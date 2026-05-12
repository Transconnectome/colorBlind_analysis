"""phase3_old_formula_full_grid.py — full-grid OLD formula refit + §3 judgment.

Applies §3 framework (LOCO ρ argmax + behavioral validation) under OLD CIELab-
direct formula. Saves full landscape so top-N candidates can be evaluated.

Subjects: sub-08 V4 (primary), sub-08 V1, sub-09 V4 (if data available).

Output per subject: results/old_formula/sub-XX_VV_simplified_{landscape,summary}.json
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

# Reuse helpers from old_formula_refit
from old_formula_refit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, THETA_8,
    load_amplitudes, load_cvd_loco_target, create_basis_full,
    simulate_mean_hc_loco_legacy, get_shifted_design_old, dt_old,
    theta_to_name, p2a_score, SUB08_PERCEPTS,
    permutation_test_spearman,
    LOCAL_DATA, SERVER_DATA,
)

OUTDIR = _THIS_DIR.parent / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)
VARIANT_TAG = 'simplified'


# Sub-09 perceptions (from raw_behav.md). Will produce empty P2a if not used.
SUB09_PERCEPTS = {
    'c1': '연한 분홍/red',       # sub-09 protan c1 perception
    'c2': '주황/yellow-orange',
    'c3': '노랑',
    'c4': '연두/yellow-green',
    'c5': '청록/cyan',
    'c6': '하늘',
    'c7': '파랑',
    'c8': '보라/violet',
}


def evaluate_p2a_general(bs: float, bc: float, percepts: dict) -> dict:
    """P2a using generic percept dict (sub-08 or sub-09)."""
    dt = dt_old(bs, bc)
    theta_cvd = (THETA_8 + dt) % 360.0
    rows = []
    for i, (tb, tc, dti) in enumerate(zip(THETA_8, theta_cvd, dt)):
        name = theta_to_name(tc)
        # p2a_score is sub-08-specific; build generic
        rows.append({
            'c': f'c{i+1}',
            'theta_base': float(tb),
            'dt': float(dti),
            'theta_cvd': float(tc),
            'color_name': name,
            'reported': percepts[f'c{i+1}'],
        })
    return rows


def fit_subject_roi(subject_id: str, roi: str, percepts: dict | None) -> dict:
    print(f'\n=== sub-{subject_id} {roi} (OLD formula) ===')
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'Data: {data_dir}')

    hc_amps = {s: load_amplitudes(data_dir, s, roi) for s in HC_SUBJECTS}
    vuln_cvd = load_cvd_loco_target(subject_id, roi)
    print(f'CVD vuln: {np.round(vuln_cvd, 3).tolist()}')

    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)

    landscape = []
    best_l_fit = np.inf
    best_rho = -2.0
    best_by_lfit = None
    best_by_rho = None

    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            rho, _ = spearmanr(vuln_sim, vuln_cvd)
            rho = float(rho) if np.isfinite(rho) else 0.0
            l_vuln_raw = float(np.mean((vuln_sim - vuln_cvd) ** 2))
            l_vuln = l_vuln_raw / 4.0
            l_rank = (1.0 - rho) / 2.0
            l_fit = 1.0 * l_vuln + 0.5 * l_rank  # NORM'd: matches §3 weights minus δ/ε
            entry = {
                'bs': float(bs), 'bc': float(bc),
                'spearman_r': rho,
                'l_vuln': l_vuln, 'l_rank': l_rank, 'l_fit': l_fit,
                'delta_theta': dt.tolist(),
            }
            landscape.append(entry)
            if l_fit < best_l_fit:
                best_l_fit = l_fit
                best_by_lfit = entry
            if rho > best_rho:
                best_rho = rho
                best_by_rho = entry
        if (i + 1) % max(1, len(bs_range) // 5) == 0:
            print(f'  [{i+1}/{len(bs_range)} β_s] '
                  f'best ρ={best_rho:.3f} l_fit={best_l_fit:.4f}')
    elapsed = time.time() - t0
    print(f'  Done in {elapsed:.0f}s')

    # Top 10 by ρ
    by_rho = sorted(landscape, key=lambda r: -r['spearman_r'])[:10]
    # Top 10 by l_fit
    by_lfit = sorted(landscape, key=lambda r: r['l_fit'])[:10]

    print(f'\nTop 10 by Spearman ρ:')
    for r in by_rho:
        print(f'  β_s={r["bs"]:>4.0f} β_c={r["bc"]:>+5.0f}  ρ={r["spearman_r"]:.3f}  '
              f'l_fit={r["l_fit"]:.4f}')
    print(f'\nTop 10 by L_fit:')
    for r in by_lfit:
        print(f'  β_s={r["bs"]:>4.0f} β_c={r["bc"]:>+5.0f}  l_fit={r["l_fit"]:.4f}  '
              f'ρ={r["spearman_r"]:.3f}')

    # P2a evaluation for top 5 by l_fit
    if percepts:
        print(f'\nP2a evaluation (top 5 by L_fit):')
        for r in by_lfit[:5]:
            rows = evaluate_p2a_general(r['bs'], r['bc'], percepts)
            names = [row['color_name'] for row in rows]
            print(f'  β=({r["bs"]:>4.0f},{r["bc"]:>+5.0f}) ρ={r["spearman_r"]:.3f}: {names}')

    out = {
        'subject': subject_id, 'roi': roi,
        'formula': 'OLD CIELab-direct: dt = bs*cos(θ−90°) + bc*cos(θ−150°)',
        'grid_bounds': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'n_cells': len(landscape),
        'elapsed_s': elapsed,
        'best_by_l_fit': best_by_lfit,
        'best_by_rho': best_by_rho,
        'top_10_by_rho': by_rho,
        'top_10_by_l_fit': by_lfit,
    }

    # Save landscape separately (large)
    fn_base = f'sub-{subject_id}_{roi}_{VARIANT_TAG}'
    with open(OUTDIR / f'{fn_base}_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
    with open(OUTDIR / f'{fn_base}_landscape.json', 'w') as f:
        json.dump(landscape, f, indent=2)
    print(f'  → {fn_base}_summary.json + _landscape.json')
    return out


def main():
    cfg = [
        ('08', 'V4', SUB08_PERCEPTS),
        ('08', 'V1', SUB08_PERCEPTS),
        ('09', 'V4', SUB09_PERCEPTS),
        ('09', 'V1', SUB09_PERCEPTS),
    ]
    all_results = {}
    for sid, roi, percepts in cfg:
        try:
            r = fit_subject_roi(sid, roi, percepts)
            all_results[f'sub-{sid}_{roi}'] = r
        except Exception as e:
            print(f'sub-{sid} {roi} FAILED: {e}')

    # Master summary
    summary = {
        'description': 'OLD-formula full-grid refit, applying §3 judgment criteria',
        'subjects': {
            k: {
                'best_by_l_fit': v['best_by_l_fit'],
                'best_by_rho': v['best_by_rho'],
            } for k, v in all_results.items()
        }
    }
    with open(OUTDIR / f'master_summary_{VARIANT_TAG}.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nWrote master_summary.json with {len(all_results)} subjects')


if __name__ == '__main__':
    main()
