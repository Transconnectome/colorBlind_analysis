"""
s16 — E2 SRM disparity OOS evaluation (per-candidate HC+CVD filter, user Q4 = (i))
=================================================================================
Per DECISION_CRITERIA_2026-05-26.md axis E2.

Interpretation (user Q4 answer 2026-05-26): Apply forward δθ to BOTH HC and CVD
amplitudes, retrain SRM, recompute HC baseline. Null control: filter shouldn't
move HC disparity significantly if CVD-specific.

For each candidate (Δλ, g) for R+C or (β_s, β_c) for 2-comp:
  1. Compute forward δθ(θ) for 8 colors
  2. Apply δθ to all subjects' (8, n_vox) amplitudes via circular interpolation
     (the amplitude formerly elicited by color θ is reassigned to color θ−δθ(θ),
     simulating distortion of color encoding)
  3. Train SRM on filtered HC pool (K per ROI)
  4. HC LOO disparity → mean_HC_filtered, std_HC_filtered
  5. CVD filtered projection via Procrustes → CVD_disparity
  6. post_filter_z = (CVD_disp - HC_mean) / HC_std
  7. E2 score = baseline_z (phase2) − post_filter_z (positive = reduction = good)

Candidate list: top E1 P2-pass per subject + cross-check (Cycle 6, v4)
ROIs: V1, V2, V4
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from time import time
from typing import Dict, List, Tuple

import numpy as np
from brainiak.funcalign.srm import SRM
from scipy.interpolate import interp1d

ROOT_AMPL = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals')
OUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/oos_reanalysis_v1')

HC_SUBJECTS = [f'sub-0{i}' for i in range(1, 8)]
ROI_K = {'V1': 4, 'V2': 4, 'V4': 3}

# Pre-computed baseline z-scores (phase2_SRM_across_between unfiltered)
BASELINE_Z = {
    'sub-08': {'V1': +1.788, 'V2': +2.940, 'V4': +1.416},
    'sub-09': {'V1': +5.169, 'V2': +1.358, 'V4': +2.465},
    'sub-10': {'V1': +1.060, 'V2': +1.290, 'V4': -1.793},
}

# Δλ source values (nm) per project memory
DELTA_LAMBDA = {
    'DPS_lit_sub-08': 6.0,
    'DPS_lit_sub-09': 10.0,
    'Boehm_mid': 8.0,
    'Boehm_low': 3.0,
    'JND_Lamb_sub-08': 6.5,
    'JND_Lamb_sub-09': 1.5,
}


def load_subject_mean(sid: str, roi: str) -> np.ndarray:
    """Return (n_voxels, n_colors=8)."""
    p = ROOT_AMPL / sid / roi / 'amplitudes_procrustes.npy'
    a = np.load(p)  # (6, 8, n_vox)
    return a.mean(axis=0).T  # (n_vox, 8)


def shift_amplitudes(amp: np.ndarray, delta_theta_deg: np.ndarray) -> np.ndarray:
    """
    amp: (n_vox, 8); delta_theta_deg: (8,) — shift per color in degrees.

    The amplitude at color θ_i is reassigned to the position θ_i − δθ(θ_i).
    Equivalent: amp_shifted[θ_i] = amp_original at angular position (θ_i + δθ(θ_i))
    using circular linear interpolation across 8 colors.
    """
    n_vox = amp.shape[0]
    theta_orig = np.arange(8) * 45.0  # 0, 45, ..., 315
    # We want amp_shifted at color θ_i to equal amp_original sampled at θ_i + δθ(θ_i)
    sample_at = (theta_orig + delta_theta_deg) % 360
    # Cyclic interp1d via 3-tile
    theta_ext = np.concatenate([theta_orig - 360, theta_orig, theta_orig + 360])  # (24,)
    amp_ext = np.concatenate([amp, amp, amp], axis=1)  # (n_vox, 24)
    out = np.zeros((n_vox, 8))
    for v in range(n_vox):
        f = interp1d(theta_ext, amp_ext[v], kind='linear')
        out[v] = f(sample_at)
    return out


def forward_delta_2comp(beta_s: float, beta_c: float, cvd_family: str) -> np.ndarray:
    """2-component δθ(θ) for 8 colors. cvd_family: 'protan' or 'deutan'."""
    theta_conf = 16.0 if cvd_family == 'protan' else 150.0
    theta = np.arange(8) * 45.0
    return beta_s * np.cos(np.deg2rad(theta - 90.0)) + beta_c * np.cos(np.deg2rad(theta - theta_conf))


def machado_delta(delta_lambda_nm: float, cvd_family: str) -> np.ndarray:
    """
    Approximate Machado δθ(θ) for 8 colors with Δλ shift.
    Without colour-science available everywhere we use a documented
    sinusoidal approximation aligned to the confusion axis.
    """
    theta_conf = 16.0 if cvd_family == 'protan' else 150.0
    theta = np.arange(8) * 45.0
    # Empirical scaling: ~3°/nm at peak per Machado 2009 typical curves
    amplitude = 3.0 * delta_lambda_nm
    return amplitude * np.cos(np.deg2rad(theta - theta_conf))


def forward_delta_rc(delta_lambda_nm: float, g: float, cvd_family: str) -> np.ndarray:
    """R+C: δθ = (2-g)·machado(Δλ)."""
    return (2.0 - g) * machado_delta(delta_lambda_nm, cvd_family)


def procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """X, Y: (K, T) shared-space matrices. Returns squared Procrustes distance."""
    # Center
    X_c = X - X.mean(axis=1, keepdims=True)
    Y_c = Y - Y.mean(axis=1, keepdims=True)
    X_n = X_c / (np.linalg.norm(X_c) + 1e-12)
    Y_n = Y_c / (np.linalg.norm(Y_c) + 1e-12)
    M = X_n @ Y_n.T
    u, s, vt = np.linalg.svd(M)
    return 1.0 - s.sum()


def evaluate_candidate(
    cvd_id: str,
    roi: str,
    delta_theta: np.ndarray,
    seed: int = 0,
) -> Dict:
    K = ROI_K[roi]
    cvd_family = 'deutan' if cvd_id == 'sub-08' else ('protan' if cvd_id == 'sub-09' else 'normal')

    # Load all subjects
    hc_data_orig = [load_subject_mean(h, roi) for h in HC_SUBJECTS]
    cvd_data_orig = load_subject_mean(cvd_id, roi)

    # Apply forward δθ to amplitudes
    hc_data_f = [shift_amplitudes(x, delta_theta) for x in hc_data_orig]
    cvd_data_f = shift_amplitudes(cvd_data_orig, delta_theta)

    # Train SRM on filtered HC pool
    srm = SRM(n_iter=20, features=K, rand_seed=seed)
    srm.fit(hc_data_f)
    s_shared = srm.s_

    # HC LOO disparities (held out)
    hc_disps = []
    for i in range(len(HC_SUBJECTS)):
        held = hc_data_f[i]
        # Project held-out HC via Procrustes to fixed S (using full-pool SRM)
        u, _, vt = np.linalg.svd(held @ s_shared.T, full_matrices=False)
        w_held = u @ vt
        held_shared = w_held.T @ held
        # Compute reference = mean of other HCs in shared space
        others_shared = []
        for j in range(len(HC_SUBJECTS)):
            if j == i:
                continue
            xj = hc_data_f[j]
            w_j = srm.w_[j]
            others_shared.append(w_j.T @ xj)
        ref = np.mean(others_shared, axis=0)
        hc_disps.append(procrustes_disparity(held_shared, ref))
    hc_mean = float(np.mean(hc_disps))
    hc_std = float(np.std(hc_disps, ddof=1))

    # CVD filtered disparity
    u, _, vt = np.linalg.svd(cvd_data_f @ s_shared.T, full_matrices=False)
    w_cvd = u @ vt
    cvd_shared = w_cvd.T @ cvd_data_f
    # Reference for CVD = full HC mean shared
    hc_shared_mean = np.mean([srm.w_[i].T @ hc_data_f[i] for i in range(len(HC_SUBJECTS))], axis=0)
    cvd_disp = procrustes_disparity(cvd_shared, hc_shared_mean)

    post_z = (cvd_disp - hc_mean) / (hc_std + 1e-12)
    baseline_z = BASELINE_Z.get(cvd_id, {}).get(roi, None)
    e2_reduction = (baseline_z - post_z) if baseline_z is not None else None

    return {
        'cvd_id': cvd_id,
        'roi': roi,
        'K': K,
        'hc_filtered_mean': hc_mean,
        'hc_filtered_std': hc_std,
        'cvd_filtered_disparity': float(cvd_disp),
        'post_filter_z': float(post_z),
        'baseline_z': baseline_z,
        'e2_reduction': float(e2_reduction) if e2_reduction is not None else None,
    }


# Candidate list — top E1 P2-pass per Cycle 10b lexicographic + cross-check historical
CANDIDATES = {
    'sub-08': [
        # Cycle 10b E1 top (lexicographic P2)
        ('E1_top1_triple', '2-comp', {'beta_s': 14, 'beta_c': -46}),   # γOY,YG,YP|RDMV2|noLOCO
        ('E1_top2_triple', '2-comp', {'beta_s': 50, 'beta_c': -36}),   # γOY,YG,YP|RDMV1+V4|noLOCO
        ('E1_yg_cluster', '2-comp', {'beta_s': 46, 'beta_c': -36}),    # γYG|RDMV1/V4|noLOCO
        # Cycle 6 raw best (cross-check; γOY|RDMV2|noLOCO)
        ('Cycle6_descriptive', '2-comp', {'beta_s': 6, 'beta_c': -42}),
        # v4 historical (38, -44)
        ('v4_historical', '2-comp', {'beta_s': 38, 'beta_c': -44}),
        # R+C g=2.60 (S08-B sensitivity)
        ('S08-B_RC_sensitivity', 'R+C', {'delta_lambda': 6.0, 'g': 2.60}),
        # Null
        ('null', '2-comp', {'beta_s': 0, 'beta_c': 0}),
    ],
    'sub-09': [
        # Cycle 10b E1 top (lexicographic P2; R+C over-comp restored)
        ('E1_top1_RC_g3.0', 'R+C', {'delta_lambda': 3.0, 'g': 3.00}),  # γGB|RDMV1|noLOCO Boehm_low
        ('E1_2c_alt_tight', '2-comp', {'beta_s': 2, 'beta_c': 24}),    # γGB|RDMV1|noLOCO; IQR=1.41
        ('E1_2c_no_gamma', '2-comp', {'beta_s': 0, 'beta_c': 24}),     # γ_|RDMV1|noLOCO
        # Cycle 6 R+C g=2.60 DPS_lit (historical primary; P2-fail in Cycle 10a, P2-pass adjacent in Cycle 10b)
        ('Cycle6_g2.6_DPS', 'R+C', {'delta_lambda': 10.0, 'g': 2.60}),
        # Null
        ('null', '2-comp', {'beta_s': 0, 'beta_c': 0}),
    ],
}


def compute_delta_theta(model: str, params: dict, cvd_family: str) -> np.ndarray:
    if model == '2-comp':
        return forward_delta_2comp(params['beta_s'], params['beta_c'], cvd_family)
    elif model == 'R+C':
        return forward_delta_rc(params['delta_lambda'], params['g'], cvd_family)
    else:
        raise ValueError(model)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {}
    for cvd_id, cands in CANDIDATES.items():
        cvd_family = 'deutan' if cvd_id == 'sub-08' else 'protan'
        print(f"\n========== {cvd_id} ({cvd_family}) ==========")
        print(f"{'label':22s} {'model':6s} {'params':28s} {'ROI':4s} {'pre_z':>7s} {'post_z':>7s} {'Δred':>6s} {'HC_μ':>6s} {'HC_σ':>6s} {'CVD_d':>6s}")
        results = []
        for label, model, params in cands:
            dt = compute_delta_theta(model, params, cvd_family)
            row = {'label': label, 'model': model, 'params': params, 'delta_theta_deg': dt.tolist(), 'per_roi': {}}
            for roi in ['V1', 'V2', 'V4']:
                t0 = time()
                r = evaluate_candidate(cvd_id, roi, dt)
                row['per_roi'][roi] = r
                pre = r['baseline_z']
                post = r['post_filter_z']
                red = r['e2_reduction']
                hcm = r['hc_filtered_mean']
                hcs = r['hc_filtered_std']
                cd = r['cvd_filtered_disparity']
                pstr = (f"βs={params['beta_s']:.0f},βc={params['beta_c']:.0f}" if model == '2-comp'
                        else f"Δλ={params['delta_lambda']:.1f},g={params['g']:.2f}")
                print(f"{label:22s} {model:6s} {pstr:28s} {roi:4s} {pre:+7.2f} {post:+7.2f} {red:+6.2f} {hcm:6.3f} {hcs:6.3f} {cd:6.3f}")
            results.append(row)
        all_results[cvd_id] = results

    out_path = OUT_DIR / 's16_e2_srm_disparity.json'
    with out_path.open('w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n→ {out_path}")


if __name__ == '__main__':
    main()
