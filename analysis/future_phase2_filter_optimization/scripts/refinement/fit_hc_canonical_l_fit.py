"""fit_hc_canonical_l_fit.py — Run canonical L_fit on HC subjects for sanity check.

Per CLAUDE.md §2.5: Phase A canonical L_LOCO HC fit was missing. This script
fills that gap by running grid_search with the canonical L_fit
(α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth) on each HC subject (sub-01~07)
treating their own LOCO vulnerability as target. Sane loss should give
(β_s, β_c) ≈ (0, 0) for HCs.
"""
import json
import sys
import time
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2 = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))
sys.path.insert(0, str(_PHASE2.parent / 'future_phase1_forward_model' / 'scripts'))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_loco_legacy, precompute_hc_W, load_cvd_loco_target,
)
from loco_distortion_fit import grid_search, DEFAULT_WEIGHTS
from diagnostic_delta_rdm import compute_delta_rdm_obs

DATA_DIR = _PHASE2.parent / 'phase1_procrustes_decoding' / 'results' / 'full_dataset_C010'
OUT_DIR = _PHASE2 / 'results' / 'fits' / 'phase_a_2component_hc_sanity'
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROIS = ['V4', 'V1']

print(f'Data: {DATA_DIR}')
print(f'Output: {OUT_DIR}\n')

t_total = time.time()

for roi in ROIS:
    print(f'\n=== ROI: {roi} ===')

    # Load HC amplitudes
    hc_amps = {h: load_amplitudes(DATA_DIR, h, roi) for h in HC_SUBJECTS}
    print(f'  Loaded HC amps: {list(hc_amps.keys())}')

    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    hc_W_dict, _ = precompute_hc_W(hc_amps, C_original)

    # For each HC: target = own LOCO vulnerability, simulator = mean of other HCs
    for target_hc in HC_SUBJECTS:
        out_path = OUT_DIR / f'sub-{target_hc}_{roi}_2component.json'
        if out_path.exists():
            print(f'  sub-{target_hc}: SKIP (exists)')
            continue
        t0 = time.time()
        # Target = HC's own LOCO vulnerability
        try:
            vuln_target = load_cvd_loco_target(target_hc, roi)
        except FileNotFoundError as e:
            print(f'  sub-{target_hc}: SKIP (no LOCO target — {e})')
            continue
        # Simulator HC pool = other HCs (leave-target-out)
        sim_amps = {h: a for h, a in hc_amps.items() if h != target_hc}
        sim_W = {h: w for h, w in hc_W_dict.items() if h != target_hc}

        # ΔRDM observed for this HC
        cvd_amp = hc_amps[target_hc]
        try:
            delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(cvd_amp, sim_amps)
        except Exception:
            delta_rdm_obs = None

        result = grid_search(
            '2component', sim_amps, vuln_target, 'normal',
            method='shift_at_both', hc_W_dict=sim_W,
            delta_rdm_obs=delta_rdm_obs,
            weights=DEFAULT_WEIGHTS, verbose=False,
        )

        # Add baseline
        vuln_baseline, _ = simulate_mean_hc_loco_legacy(sim_amps, C_original)
        rho_baseline, _ = spearmanr(vuln_baseline, vuln_target)
        result['baseline'] = {
            'vuln_baseline': vuln_baseline.tolist(),
            'spearman_r_baseline': float(rho_baseline),
        }
        result['target_subject'] = f'sub-{target_hc}'
        result['target_role'] = 'HC'
        result['simulator_pool'] = list(sim_amps.keys())

        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2, default=lambda x: float(x) if hasattr(x, 'item') else x)
        bs, bc = result['best_params']
        norm = (bs**2 + bc**2)**0.5
        print(f'  sub-{target_hc}: best=({bs:>5.1f}, {bc:>+6.1f}), '
              f'norm={norm:>5.1f}, ρ={result["best_loss"]["spearman_r"]:.3f}, '
              f'baseline_ρ={rho_baseline:.3f}, t={time.time()-t0:.1f}s')

print(f'\nTotal: {time.time()-t_total:.1f}s')
print(f'Output: {OUT_DIR}')
