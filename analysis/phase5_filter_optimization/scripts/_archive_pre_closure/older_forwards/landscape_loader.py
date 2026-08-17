"""landscape_loader.py — drop-in helpers for parquet-backed landscape access.

Replaces per-file JSON loading in c3_alternative_losses, c3_loss_to_p2amax, etc.
Same dict-of-grids output format as `c3_alternative_losses.load_landscape`.

Usage:
    from landscape_loader import load_landscape_pq

    # Old:
    grid = load_landscape(ROOT / 'results/old_formula/sub-08_V4_V4ccc_landscape.json')

    # New:
    grid = load_landscape_pq(subject='08', roi='V4', variant='V4ccc')

The parquet file is `results/landscapes_consolidated.parquet`, built by
`scripts/consolidate_landscapes_to_parquet.py`.
"""
from __future__ import annotations
from pathlib import Path
from functools import lru_cache

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / 'results' / 'landscapes_consolidated.parquet'


@lru_cache(maxsize=1)
def _load_full() -> pd.DataFrame:
    if not PARQUET.exists():
        raise FileNotFoundError(
            f'{PARQUET} not found. Run scripts/consolidate_landscapes_to_parquet.py first.'
        )
    return pd.read_parquet(PARQUET)


def list_variants(subject: str | None = None, roi: str | None = None) -> pd.Series:
    """Return distinct (subject, roi, variant) combinations available."""
    df = _load_full()
    if subject is not None:
        df = df[df['subject'] == str(subject)]
    if roi is not None:
        df = df[df['roi'] == roi]
    return df.groupby(['subject', 'roi', 'variant']).size().sort_index()


def load_landscape_pq(subject: str, roi: str, variant: str) -> dict:
    """Load one landscape as dict-of-2D-grids.

    Returns same structure as c3_alternative_losses.load_landscape():
      {
        'bs_grid': 1D array of unique bs values,
        'bc_grid': 1D array of unique bc values,
        '<scalar_key>': 2D array (N_bs, N_bc) for each scalar metric,
      }

    Vector keys (vuln_sim_c1..c8, delta_theta_c1..c8) are returned as separate
    2D grids per color.
    """
    df = _load_full()
    sub = df[(df['subject'] == str(subject)) & (df['roi'] == roi) & (df['variant'] == variant)]
    if sub.empty:
        raise KeyError(f'No landscape for subject={subject!r}, roi={roi!r}, variant={variant!r}. '
                       f'Available: {list_variants(subject, roi).index.tolist()}')

    bs_vals = sorted(sub['bs'].unique())
    bc_vals = sorted(sub['bc'].unique())
    bs_arr = np.array(bs_vals); bc_arr = np.array(bc_vals)
    N_bs, N_bc = len(bs_arr), len(bc_arr)
    bs_step = bs_arr[1] - bs_arr[0] if N_bs > 1 else 1.0
    bc_step = bc_arr[1] - bc_arr[0] if N_bc > 1 else 1.0

    # All numeric scalar columns (not source_file/subject/roi/variant/bs/bc)
    skip = {'source_file', 'subject', 'roi', 'variant', 'bs', 'bc'}
    cols = [c for c in sub.columns if c not in skip]

    grids = {}
    for c in cols:
        grids[c] = np.full((N_bs, N_bc), np.nan)

    for _, row in sub.iterrows():
        i = int(round((float(row['bs']) - bs_arr[0]) / bs_step))
        j = int(round((float(row['bc']) - bc_arr[0]) / bc_step))
        for c in cols:
            v = row[c]
            if pd.notna(v):
                grids[c][i, j] = v

    grids['bs_grid'] = bs_arr
    grids['bc_grid'] = bc_arr
    return grids


def smoke_test():
    """Quick verification — load V4ccc and check argmin matches expected."""
    g = load_landscape_pq('08', 'V4', 'V4ccc')
    print(f"Loaded: bs_grid {g['bs_grid'].shape}, bc_grid {g['bc_grid'].shape}")
    print(f"Available metrics: {[k for k in g if k not in ('bs_grid','bc_grid')]}")
    if 'l_ccc' in g:
        L = np.where(np.isnan(g['l_ccc']), 1e6, g['l_ccc'])
        idx = np.unravel_index(np.nanargmin(L), L.shape)
        print(f"argmin l_ccc: ({g['bs_grid'][idx[0]]:.0f}, {g['bc_grid'][idx[1]]:.0f})  l={L[idx]:.4f}")


if __name__ == '__main__':
    print('Available landscapes:')
    print(list_variants().to_string())
    print()
    smoke_test()
