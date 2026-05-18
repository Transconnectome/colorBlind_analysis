"""consolidate_landscapes_to_parquet.py — Phase A consolidation.

Reads all landscape JSONs from results/old_formula/, results/axis_3way/,
results/CANDIDATE/tier2_v4ccc_srm_rdm/ and writes a single parquet.

Schema (per row = one (subject, roi, variant, bs, bc) cell):
  - source_file: provenance
  - subject: '08' / '09' / 'HC' (from filename)
  - roi: 'V1' / 'V2' / 'V4'
  - variant: descriptive tag from filename (V4ccc / Stockman150 / 4term / wfixed / ...)
  - bs, bc: 2-comp params
  - vuln_sim_c1..c8: per-color simulated vuln (flattened from 8-vec)
  - delta_theta_c1..c8: per-color δθ (flattened from 8-vec)
  - l_*: any loss-component scalars present in source JSON (NaN if missing)
  - Other metric scalars: spearman_r, pearson_r, ccc, rdm_cosine, etc.

Usage:
  python scripts/consolidate_landscapes_to_parquet.py [--dry-run]
"""
from __future__ import annotations
import json
import os
import re
import sys
import argparse
import glob
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results' / 'landscapes_consolidated.parquet'

SCALAR_KEYS = {
    'l_fit', 'l_vuln', 'l_rank', 'l_rdm', 'l_smooth', 'l_ccc', 'l_topk',
    'l_pearson', 'l_vuln_raw', 'l_rank_raw', 'l_smooth_raw',
    'l_vuln_with_offset', 'l_vuln_with_offset_raw', 'offset_squared',
    'L_combined', 'tikh',
    'spearman_r', 'pearson_r', 'ccc', 'rdm_cosine',
    'sim_mean', 'sim_std', 'obs_mean', 'obs_std',
}
VECTOR_KEYS = {'vuln_sim', 'delta_theta'}  # 8-vec each

FILENAME_RE = re.compile(
    r'sub-(?P<subj>\d+|HC)_(?P<roi>V\d+)_(?P<variant>.+?)_landscape\.json$'
)


def parse_filename(name: str) -> tuple[str, str, str]:
    m = FILENAME_RE.search(name)
    if m:
        return m.group('subj'), m.group('roi'), m.group('variant')
    # Fallback for non-standard names
    return 'unknown', 'unknown', name.replace('.json', '')


def cells_from_json(d):
    if isinstance(d, list):
        return d
    if isinstance(d, dict) and 'cells' in d and isinstance(d['cells'], list):
        return d['cells']
    return None


def build_rows(path: Path):
    name = path.name
    subj, roi, variant = parse_filename(name)
    try:
        d = json.load(open(path))
    except Exception as e:
        print(f'  ERR load {name}: {e}', file=sys.stderr)
        return []
    cells = cells_from_json(d)
    if not cells:
        return []
    rows = []
    for c in cells:
        if not isinstance(c, dict):
            continue
        row = {
            'source_file': name,
            'subject': subj,
            'roi': roi,
            'variant': variant,
            'bs': c.get('bs'),
            'bc': c.get('bc'),
        }
        for k in VECTOR_KEYS:
            v = c.get(k)
            if isinstance(v, list) and len(v) == 8:
                for i, x in enumerate(v):
                    row[f'{k}_c{i+1}'] = float(x) if x is not None else np.nan
            else:
                for i in range(8):
                    row[f'{k}_c{i+1}'] = np.nan
        for k in SCALAR_KEYS:
            v = c.get(k)
            row[k] = float(v) if v is not None and not isinstance(v, list) else np.nan
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--out', default=str(OUT))
    args = ap.parse_args()

    sources = []
    for pattern in [
        'results/old_formula/*landscape*.json',
        'results/axis_3way/*landscape*.json',
        'results/CANDIDATE/tier2_v4ccc_srm_rdm/*landscape*.json',
    ]:
        sources.extend(sorted(ROOT.glob(pattern)))

    print(f'Found {len(sources)} landscape JSONs')

    all_rows = []
    n_files_used = 0
    for p in sources:
        rows = build_rows(p)
        if rows:
            all_rows.extend(rows)
            n_files_used += 1
        else:
            print(f'  SKIP (not landscape): {p.name}')

    df = pd.DataFrame(all_rows)
    print(f'\nConsolidated: {n_files_used}/{len(sources)} files → {len(df)} rows × {len(df.columns)} cols')
    print(f'\nSubject × ROI × variant distinct rows:')
    grp = df.groupby(['subject', 'roi', 'variant']).size()
    print(grp.head(20))
    print(f'\nColumns: {list(df.columns)}')

    if args.dry_run:
        print('\n--dry-run; not writing.')
        return

    df.to_parquet(args.out, index=False, compression='snappy')
    sz = os.path.getsize(args.out)
    print(f'\nWrote {args.out} ({sz/1e6:.2f} MB)')
    # Original total
    orig_total = sum(os.path.getsize(p) for p in sources)
    print(f'Original total JSON: {orig_total/1e6:.2f} MB → reduction {100*(1 - sz/orig_total):.1f}%')


if __name__ == '__main__':
    main()
