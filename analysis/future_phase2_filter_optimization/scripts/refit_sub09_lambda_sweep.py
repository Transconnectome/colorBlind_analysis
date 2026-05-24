"""Δλ sensitivity sweep for sub-09 R+C fit at L2 behav γ.

Tests whether g recovers to physiological zone (1 ≤ g ≤ 2) when Δλ assumption
is increased toward severe-protanomaly range (Machado 2009: ~20 nm).

Δλ tested: 10.0 (DPS, current S5), 15.0, 17.5, 19.5 (Gen-4 unified V1@α=1.0), 22.0.
Per-Δλ outputs: g*, factor (2-g), compensation magnitude M, L2 loss.

Verdict: if g* at Δλ=19.5 ∈ [1, 2] (physiological), then DPS=10 underestimate
hypothesis confirmed.
"""
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g
from s5_all_paths_fit import build_loss_callables
from neural_loss import load_amplitudes, load_hc_pool, ROI_K


def sweep_for_roi(subject, family, roi, lambdas, loss_keys=('L2_behav_gamma',)):
    print(f"\n=== {subject} {roi} ({family}) Δλ sweep ===")
    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)
    K = ROI_K[roi]
    losses = build_loss_callables(subject, cvd_amp, hc_amps, K, sigma=21.0)

    rows = []
    for lkey in loss_keys:
        L = losses[lkey]
        print(f"  -- loss = {lkey} --")
        for dlam in lambdas:
            fit = fit_rc_g(dlam, family, L)
            g = fit['g_best']
            factor = 2.0 - g
            M = max(0.0, g - 1.0) * dlam
            overshoot_pct = max(0.0, g - 2.0) * 100.0
            dt = forward_rc(dlam, g, family)
            norm_dt = float(np.linalg.norm(dt))
            rows.append({
                'roi': roi, 'loss': lkey,
                'delta_lambda_nm': dlam,
                'g_best': g, 'factor_2_minus_g': round(factor, 3),
                'loss_best': fit['loss_best'],
                'M_comp_nm': round(M, 2),
                'overshoot_pct': round(overshoot_pct, 1),
                'boundary_high': fit['boundary_high'],
                'norm_delta_theta_deg': round(norm_dt, 2),
                'physiological_zone': bool(1.0 <= g <= 2.0),
            })
            flag = ('✓ physiological' if 1.0 <= g <= 2.0
                    else ('⚠ boundary' if fit['boundary_high']
                          else f'✗ over-shoot ({overshoot_pct:.0f}%)'))
            print(f"    Δλ={dlam:5.1f}  g*={g:.2f}  factor={factor:+.2f}  "
                  f"M={M:5.1f}  loss={fit['loss_best']:.4f}  ‖δθ‖={norm_dt:5.1f}°  {flag}")
    return rows


def main():
    LAMBDAS = [10.0, 15.0, 17.5, 19.5, 22.0]

    print("=" * 70)
    print("Δλ sensitivity sweep — sub-09 protan R+C @ L2 behav γ (K=6, σ=21)")
    print("Question: does fit g* recover to physiological zone [1, 2] at larger Δλ?")
    print("=" * 70)

    all_rows = []
    LOSSES = ('L2_behav_gamma', 'L4_RDM_corr', 'L3_LOCO', 'L8_modality_5050')
    for roi in ['V1', 'V4']:
        all_rows.extend(sweep_for_roi('sub-09', 'protan', roi, LAMBDAS, loss_keys=LOSSES))

    out = SCRIPT_DIR.parent / 'results' / 's5_all_paths' / 'sub-09_lambda_sweep_RC_L2.json'
    out.write_text(json.dumps({
        'subject': 'sub-09', 'family': 'protan',
        'loss_target': 'L2_behav_gamma',
        'sigma': 21.0,
        'lambdas_nm': LAMBDAS,
        'rows': all_rows,
        'notes': [
            'g grid [0, 3] step 0.05; factor = 2-g',
            'physiological zone: 1<=g<=2 (1=retinal-raw, 2=full-comp)',
            'g>2 = over-shoot (Tregillus framework violation)',
            'Δλ=10 = DPS_lit (current S5 PRIMARY)',
            'Δλ=19.5 = severe protanomaly per Machado 2009 (near dichromat boundary)',
        ],
    }, indent=2))
    print(f"\nSaved {out}")


if __name__ == '__main__':
    main()
