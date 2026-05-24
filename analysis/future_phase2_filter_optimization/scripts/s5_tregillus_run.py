"""s5_tregillus_run.py — Tregillus-faithful R+C re-run of S5 pipeline.

Identical scaffolding to s5_all_paths_fit.py except R+C forward uses
rc_opponent_1dof.forward_rc_opp (opponent R-G channel gain) instead of
rc_1dof.forward_rc (uniform linear scaling).

2-Comp results are NOT re-computed — they are the same regardless of R+C
forward variant. (Re-fitting them would just re-produce S5 numbers.)

Outputs:
  results/s5_tregillus/{subject}_{roi}_sigma21.json  — R+C-only Tregillus fits
  results/s5_tregillus/summary.json                  — flat summary table
"""
from __future__ import annotations
import sys
import json
import time
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_opponent_1dof import forward_rc_opp, fit_rc_opp_g
from s5_all_paths_fit import (
    DELTA_LAMBDA_SOURCES,
    build_loss_callables,
)
from neural_loss import load_amplitudes, load_hc_pool, ROI_K
from behav_loss import SIGMA_HC

OUT_DIR = SCRIPT_DIR.parent / "results" / "s5_tregillus"


def fit_one_subject_roi(subject: str, roi: str,
                         sigma: float = SIGMA_HC) -> dict:
    info = DELTA_LAMBDA_SOURCES.get(subject)
    if info is None:
        raise ValueError(f"No Δλ sources for {subject}")
    cvd_family = info['family']
    K = ROI_K[roi]

    print(f"\n>>> Tregillus R+C fit {subject} ROI={roi} (K={K}, σ={sigma})")
    t0 = time.time()

    # Data + losses
    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)
    losses = build_loss_callables(subject, cvd_amp, hc_amps, K, sigma=sigma)

    results = {
        'subject': subject,
        'roi': roi,
        'cvd_family': cvd_family,
        'K': K,
        'sigma': sigma,
        'n_hc_used': len(hc_amps),
        'forward_model': 'rc_opponent_1dof (Tregillus R-G gain)',
        'g_grid': {'min': -2.0, 'max': 2.0, 'step': 0.05, 'n_points': 81},
        'fits': [],
    }

    # R+C only — 3 Δλ × 8 loss = 24 fits per cell
    for dl_label, dl_value in info['sources'].items():
        for loss_name, loss_fn in losses.items():
            t_fit = time.time()
            rc = fit_rc_opp_g(dl_value, cvd_family, loss_fn)
            g_best = rc['g_best']
            delta = forward_rc_opp(dl_value, g_best, cvd_family)
            fit_record = {
                'model': 'R+C_opp',
                'delta_lambda_source': dl_label,
                'delta_lambda_nm': dl_value,
                'loss_target': loss_name,
                'g_best': g_best,
                'loss_best': rc['loss_best'],
                'loss_at_g0': rc['loss_at_g0'],
                'boundary_low': rc['boundary_low'],
                'boundary_high': rc['boundary_high'],
                'misspecified': rc['misspecified'],
                'in_tregillus_zone': bool(-1.0 <= g_best <= 0.0),
                'delta_theta_at_best': delta.tolist(),
                'delta_theta_rms_deg': float(np.sqrt(np.mean(delta ** 2))),
                'delta_theta_max_abs_deg': float(np.max(np.abs(delta))),
                'fit_time_s': round(time.time() - t_fit, 2),
            }
            results['fits'].append(fit_record)

    results['total_time_s'] = round(time.time() - t0, 2)
    print(f"    {subject} {roi} done in {results['total_time_s']:.1f}s "
          f"({len(results['fits'])} fits)")
    return results


def main(rois=('V4', 'V1'), subjects=('sub-08', 'sub-09')):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print(f"S5-Tregillus R+C fit — {len(subjects)} subj × {len(rois)} ROI "
          f"× 3 Δλ × 8 loss = {len(subjects) * len(rois) * 24} fits")
    print(f"  σ = {SIGMA_HC}°, g grid [-2, +2] step 0.05 (81 pts)")
    print("=" * 78)

    all_results = {}
    summary_rows = []
    for subject in subjects:
        for roi in rois:
            key = f"{subject}_{roi}_sigma{int(SIGMA_HC)}"
            r = fit_one_subject_roi(subject, roi, sigma=SIGMA_HC)
            all_results[key] = r
            out_path = OUT_DIR / f"{key}.json"
            with open(out_path, 'w') as f:
                json.dump(r, f, indent=2, default=str)
            print(f"    Saved: {out_path}")
            for fit in r['fits']:
                summary_rows.append({
                    'subject': r['subject'], 'roi': r['roi'],
                    'sigma': r['sigma'], 'cvd_family': r['cvd_family'],
                    'model': fit['model'],
                    'delta_lambda_source': fit['delta_lambda_source'],
                    'delta_lambda_nm': fit['delta_lambda_nm'],
                    'loss_target': fit['loss_target'],
                    'g_best': fit['g_best'],
                    'loss_best': fit['loss_best'],
                    'loss_at_g0': fit['loss_at_g0'],
                    'boundary_low': fit['boundary_low'],
                    'boundary_high': fit['boundary_high'],
                    'misspecified': fit['misspecified'],
                    'in_tregillus_zone': fit['in_tregillus_zone'],
                    'delta_theta_rms_deg': fit['delta_theta_rms_deg'],
                    'delta_theta_max_abs_deg': fit['delta_theta_max_abs_deg'],
                })

    with open(OUT_DIR / "summary.json", 'w') as f:
        json.dump(summary_rows, f, indent=2, default=str)
    print(f"\nSaved master summary: {OUT_DIR / 'summary.json'}")
    print(f"  Total fits: {len(summary_rows)}")
    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--rois', nargs='+', default=['V4', 'V1'])
    parser.add_argument('--subjects', nargs='+',
                        default=['sub-08', 'sub-09'])
    args = parser.parse_args()
    main(rois=tuple(args.rois), subjects=tuple(args.subjects))
