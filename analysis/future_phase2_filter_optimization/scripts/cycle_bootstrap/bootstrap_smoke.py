#!/usr/bin/env python3
"""bootstrap_smoke.py — Cycle 1 smoke test for HC-subject bootstrap of LOCO ρ.

Goals:
- Verify import / data wiring (read-only) on hV4 with sub-08.
- Compute mean-HC ρ for full 7-HC and 7 LOHO leave-one-HC-out variants
  using the existing 2-component grid (single ROI, single subject, single model).
- Output a small JSON to results/cycle_bootstrap/.

Run (local, conda env: srm):
    python analysis/future_phase2_filter_optimization/scripts/cycle_bootstrap/bootstrap_smoke.py

Notes:
- This is read-only with respect to existing scripts (no modification).
- Imports loco_distortion_fit + step1_fit_loco_v2 helpers.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path bootstrapping
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent.parent
_PHASE2_SCRIPTS = _PHASE2_DIR / 'scripts'
sys.path.insert(0, str(_PHASE2_SCRIPTS))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, HUE_ANGLES,
    load_amplitudes, create_basis_matrix,
)
from step1_fit_loco_v2 import (
    precompute_hc_W,
    simulate_mean_hc_wfixed,
    load_cvd_loco_target,
    permutation_test_spearman,
)
from loco_distortion_fit import (
    FILTER_MODELS, get_shifted_design, compute_fit_loss, DEFAULT_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
LOCAL_DATA = (_PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def grid_search_loho(
    model_name: str,
    hc_amps_dict: dict,
    hc_W_dict: dict,
    cvd_vuln: np.ndarray,
    cvd_type: str,
    weights=None,
):
    """Run W-fixed grid search over the 2-component or machado_1way grid.

    Returns dict with best_params, best ρ, label_perm_p (8! exact).
    """
    info = FILTER_MODELS[model_name]
    bounds = info['bounds']
    steps = info['grid_step']
    if steps is None:
        raise ValueError(f"Grid not supported for {model_name}; use grid models")

    axes = []
    for (lo, hi), step in zip(bounds, steps):
        axes.append(np.arange(lo, hi + step * 0.5, step))
    if len(axes) == 1:
        grid = [(x,) for x in axes[0]]
    elif len(axes) == 2:
        grid = [(x, y) for x in axes[0] for y in axes[1]]
    else:
        raise ValueError("only 1D/2D grids supported")

    if weights is None:
        weights = DEFAULT_WEIGHTS

    best_loss = np.inf
    best_params = None
    best_rho = None
    best_vuln_sim = None
    for params in grid:
        params_arr = np.array(params)
        C_shifted, dt = get_shifted_design(model_name, params_arr, cvd_type)
        vuln_sim, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted)
        loss = compute_fit_loss(vuln_sim, cvd_vuln, dt, weights=weights)
        if loss['l_fit'] < best_loss:
            best_loss = loss['l_fit']
            best_params = params_arr.tolist()
            best_rho = loss['spearman_r']
            best_vuln_sim = vuln_sim.tolist()

    perm_p, _, rho_obs = permutation_test_spearman(
        np.array(best_vuln_sim), cvd_vuln, n_perm=40320)

    return {
        'best_params': best_params,
        'best_loss': float(best_loss),
        'rho': float(best_rho),
        'rho_obs_perm': float(rho_obs),
        'label_perm_p': float(perm_p),
        'vuln_sim': best_vuln_sim,
    }


def fit_with_subject_subset(
    model_name: str,
    hc_amps_full: dict,
    cvd_vuln: np.ndarray,
    cvd_type: str,
    drop_subj: str | None,
    C_original: np.ndarray,
):
    """Drop one HC (or none) and refit grid + permutation."""
    if drop_subj is None:
        amps_sub = dict(hc_amps_full)
        label = 'all7'
    else:
        amps_sub = {k: v for k, v in hc_amps_full.items() if k != drop_subj}
        label = f'drop_{drop_subj}'

    W_sub, alpha_sub = precompute_hc_W(amps_sub, C_original)
    res = grid_search_loho(model_name, amps_sub, W_sub, cvd_vuln, cvd_type)
    res['label'] = label
    res['n_hc'] = len(amps_sub)
    res['alphas'] = {k: float(v) for k, v in alpha_sub.items()}
    return res


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', default='08')
    ap.add_argument('--roi', default='V4')
    ap.add_argument('--model', default='2component',
                    choices=['2component', 'machado_1way'])
    ap.add_argument('--data_dir', default=str(LOCAL_DATA))
    ap.add_argument('--n_loho', type=int, default=2,
                    help='smoke: number of LOHO variants to try (in addition to all7)')
    ap.add_argument('--output_dir', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'smoke'))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cvd_type = CVD_TYPE[args.subject]
    print(f'[smoke] subject=sub-{args.subject} roi={args.roi} '
          f'model={args.model} cvd_type={cvd_type}')

    # ---- Load HC amps ----
    hc_amps = {}
    for s in HC_SUBJECTS:
        try:
            hc_amps[s] = load_amplitudes(args.data_dir, s, args.roi)
        except FileNotFoundError as e:
            print(f'  [warn] missing {s}: {e}')
    if not hc_amps:
        raise SystemExit('No HC amps loaded — check --data_dir')
    print(f'  HC loaded: {sorted(hc_amps.keys())}')

    # ---- Load CVD LOCO target ----
    cvd_vuln = load_cvd_loco_target(args.subject, args.roi)
    print(f'  CVD vuln (sub-{args.subject}, {args.roi}): {np.round(cvd_vuln, 3).tolist()}')

    # ---- Original design matrix ----
    C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS, basis_type='fe')

    # ---- Run all7 baseline ----
    t0 = time.time()
    res_all = fit_with_subject_subset(
        args.model, hc_amps, cvd_vuln, cvd_type,
        drop_subj=None, C_original=C_original)
    elapsed_all = time.time() - t0
    print(f'  [all7] params={res_all["best_params"]} '
          f'ρ={res_all["rho"]:.3f} p={res_all["label_perm_p"]:.4f} '
          f'({elapsed_all:.1f}s)')

    # ---- Run a few LOHO variants ----
    loho_results = []
    pick = sorted(hc_amps.keys())[:args.n_loho]
    for s in pick:
        t0 = time.time()
        res = fit_with_subject_subset(
            args.model, hc_amps, cvd_vuln, cvd_type,
            drop_subj=s, C_original=C_original)
        elapsed = time.time() - t0
        print(f'  [drop_{s}] params={res["best_params"]} '
              f'ρ={res["rho"]:.3f} p={res["label_perm_p"]:.4f} '
              f'({elapsed:.1f}s)')
        loho_results.append(res)

    # Summary
    rhos = [res_all['rho']] + [r['rho'] for r in loho_results]
    summary = {
        'subject': args.subject,
        'roi': args.roi,
        'model': args.model,
        'cvd_type': cvd_type,
        'n_hc_full': len(hc_amps),
        'all7': res_all,
        'loho': loho_results,
        'rho_summary': {
            'min': float(np.min(rhos)),
            'max': float(np.max(rhos)),
            'mean': float(np.mean(rhos)),
            'median': float(np.median(rhos)),
            'std': float(np.std(rhos, ddof=1)) if len(rhos) > 1 else 0.0,
            'spread': float(np.max(rhos) - np.min(rhos)),
        },
        'timestamp': datetime.now().isoformat(),
    }
    out = out_dir / f'smoke_sub-{args.subject}_{args.roi}_{args.model}.json'
    with open(out, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'  [saved] {out}')

    print(f'\n  ρ spread (all7 + {args.n_loho} LOHO): '
          f'{summary["rho_summary"]["min"]:.3f}…'
          f'{summary["rho_summary"]["max"]:.3f}, '
          f'std={summary["rho_summary"]["std"]:.3f}')


if __name__ == '__main__':
    main()
