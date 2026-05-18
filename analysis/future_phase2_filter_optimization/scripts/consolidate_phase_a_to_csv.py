"""consolidate_phase_a_to_csv.py — Phase B consolidation.

Reads scalar Phase-A fit summaries (results/fits/phase_a*/sub-XX_<ROI>_<model>.json,
results/fits/canonical*/, smooth sweep files, and *_summary.json) and writes
two CSVs:
  - results/phase_a_summary.csv          (one row per subject × ROI × model)
  - results/smooth_sweep_summary.csv     (one row per subject × ROI × ε)

Schema (phase_a_summary.csv):
  source_file, subject, roi, model_class, best_bs, best_bc, perm_p, spearman_r,
  l_fit, l_vuln, l_rank, l_rdm, l_smooth, method, n_evaluations, elapsed_s

Schema (smooth_sweep_summary.csv):
  source_file, subject, roi, epsilon, alpha, beta, delta, plus any extra
  scalar metrics present

Usage:
  python scripts/consolidate_phase_a_to_csv.py [--dry-run]
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

FILENAME_PHASEA = re.compile(r'sub-(?P<subj>\d+)_(?P<roi>V\d+)_(?P<model>[a-zA-Z0-9_]+?)(?:_landscape)?\.json$')
FILENAME_SMOOTH = re.compile(r'sub-(?P<subj>\d+)_(?P<roi>V\d+)_smooth(?P<eps>[\d.]+)\.json$')


def extract_scalar(d, key, default=np.nan):
    """Pull scalar from nested dict; supports best_loss.<key> or top-level."""
    v = d.get(key)
    if v is None and 'best_loss' in d and isinstance(d['best_loss'], dict):
        v = d['best_loss'].get(key)
    if v is None or isinstance(v, (list, dict)):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def build_phase_a_row(path: Path) -> dict | None:
    name = path.name
    m = FILENAME_PHASEA.search(name)
    if not m:
        return None
    try:
        d = json.load(open(path))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    # Skip if it's clearly a landscape file (has 'cells')
    if 'cells' in d and isinstance(d['cells'], list):
        return None
    row = {
        'source_file': str(path.relative_to(ROOT)),
        'subject': m.group('subj'),
        'roi': m.group('roi'),
        'model_class': m.group('model'),
    }
    # best_params: [bs, bc] or {bs, bc}
    bp = d.get('best_params')
    if isinstance(bp, list) and len(bp) >= 2:
        row['best_bs'] = float(bp[0])
        row['best_bc'] = float(bp[1])
    elif isinstance(bp, dict):
        row['best_bs'] = float(bp.get('bs', np.nan)) if bp.get('bs') is not None else np.nan
        row['best_bc'] = float(bp.get('bc', np.nan)) if bp.get('bc') is not None else np.nan
    # Permutation
    perm = d.get('permutation')
    if isinstance(perm, dict):
        row['perm_p'] = perm.get('p_value', perm.get('p'))
    else:
        row['perm_p'] = extract_scalar(d, 'phase_a_perm_p', np.nan)
    # Scalar metrics from best_loss or top
    for k in ['spearman_r', 'l_fit', 'l_vuln', 'l_rank', 'l_rdm', 'l_smooth',
              'l_vuln_raw', 'l_rank_raw', 'pearson_r', 'rdm_cosine']:
        row[k] = extract_scalar(d, k, np.nan)
    # Run metadata
    row['method'] = d.get('method')
    row['n_evaluations'] = d.get('n_evaluations')
    row['elapsed_s'] = d.get('elapsed_s', d.get('elapsed_sec'))
    return row


def build_smooth_row(path: Path) -> dict | None:
    name = path.name
    m = FILENAME_SMOOTH.search(name)
    if not m:
        return None
    try:
        d = json.load(open(path))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    row = {
        'source_file': str(path.relative_to(ROOT)),
        'subject': m.group('subj'),
        'roi': m.group('roi'),
        'epsilon': float(m.group('eps')),
    }
    for k in ['alpha', 'beta', 'delta', 'best_bs', 'best_bc', 'spearman_r',
              'l_fit', 'l_vuln', 'l_smooth', 'perm_p']:
        v = d.get(k)
        if isinstance(v, (int, float)):
            row[k] = float(v)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    # Collect Phase-A fit files
    phase_a_paths = []
    for pattern in [
        'results/fits/phase_a*/*.json',
        'results/fits/canonical*/*.json',
        'results/fits/preimage/*.json',  # also scalars in these
        'results/old_formula/*_summary.json',
    ]:
        phase_a_paths.extend(sorted(ROOT.glob(pattern)))

    phase_a_rows = []
    used = 0
    for p in phase_a_paths:
        # Skip pure manifest files
        if p.name in ('step2c_manifest.json',):
            continue
        row = build_phase_a_row(p)
        if row:
            phase_a_rows.append(row)
            used += 1

    df_pa = pd.DataFrame(phase_a_rows)
    print(f'Phase-A: {used}/{len(phase_a_paths)} files → {len(df_pa)} rows × {len(df_pa.columns)} cols')
    if not df_pa.empty:
        print('  Sample:')
        print(df_pa[['subject', 'roi', 'model_class', 'best_bs', 'best_bc', 'perm_p', 'spearman_r']].head(8).to_string())

    # Smooth sweep
    smooth_paths = sorted(ROOT.glob('results/old_formula/*smooth*.json'))
    smooth_rows = []
    for p in smooth_paths:
        row = build_smooth_row(p)
        if row:
            smooth_rows.append(row)
    df_sm = pd.DataFrame(smooth_rows)
    print(f'\nSmooth sweep: {len(df_sm)}/{len(smooth_paths)} files → {len(df_sm)} rows × {len(df_sm.columns)} cols')

    if args.dry_run:
        print('\n--dry-run; not writing.')
        return

    out_pa = ROOT / 'results' / 'phase_a_summary.csv'
    df_pa.to_csv(out_pa, index=False)
    print(f'\nWrote {out_pa} ({os.path.getsize(out_pa)/1e3:.1f} KB)')

    out_sm = ROOT / 'results' / 'smooth_sweep_summary.csv'
    df_sm.to_csv(out_sm, index=False)
    print(f'Wrote {out_sm} ({os.path.getsize(out_sm)/1e3:.1f} KB)')

    # Report total reduction
    orig = sum(os.path.getsize(p) for p in phase_a_paths + smooth_paths)
    new = os.path.getsize(out_pa) + os.path.getsize(out_sm)
    print(f'\nOriginal: {orig/1e6:.2f} MB → CSV: {new/1e3:.1f} KB ({100*(1-new/orig):.1f}% reduction)')


if __name__ == '__main__':
    main()
