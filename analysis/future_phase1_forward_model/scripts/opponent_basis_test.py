#!/usr/bin/env python3
"""
opponent_basis_test.py — Test 2D opponent-channel basis for V1/V2.

Red Team Criticism #3 neutralization experiment:
  If opponent basis LOCO passes permutation in V1/V2 → FE-6 mismatch confirmed.
  If it also fails → dissociation is real (not just basis choice).

Opponent basis design:
  8 hue angles → 2D DKL cone-opponent coordinates:
    Channel 1: L-M (red-green axis) ∝ cos(θ)
    Channel 2: S-(L+M) (blue-yellow axis) ∝ sin(θ)

  This maps the circular hue space onto the 2D cardinal opponent axes.
  The mapping assumes isoluminant hue angles where:
    θ=0° (red) → max L-M, zero S
    θ=90° (yellow-green) → zero L-M, max S
    θ=180° (cyan) → min L-M, zero S
    θ=270° (blue) → zero L-M, min S

Bases tested:
  (A) OPP-2: Raw opponent [cos(θ), sin(θ)] — 2 channels
  (B) OPP-4: Opponent + half-rectified [cos+, cos−, sin+, sin−] — 4 channels
  (C) OPP-2-rect: Half-rectified opponent [max(cos,0), max(-cos,0), max(sin,0), max(-sin,0)] — 4 channels
  (D) FE-6: Baseline for comparison

10K permutations, HC subjects, ridge_gcv.
"""

import numpy as np
import json
from pathlib import Path
from scipy import stats as sp_stats

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, HUE_ANGLES, N_RUNS, N_COLORS,
    ALPHA_GRID, load_amplitudes, create_basis_matrix,
    fit_W_ridge, gcv_select_alpha, voxel_pattern_correlation,
)

# ============================================================================
# Configuration
# ============================================================================

SERVER_BASELINE_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')
LOCAL_BASELINE_DIR = Path(__file__).resolve().parents[3] / \
    'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
BASELINE_DIR = SERVER_BASELINE_DIR if SERVER_BASELINE_DIR.exists() else LOCAL_BASELINE_DIR

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'results' / 'opponent_basis'

N_PERM = 10000
RNG_SEED = 42


# ============================================================================
# Opponent Basis Functions
# ============================================================================

def create_opponent_basis(hue_angles, basis_type='opp2'):
    """Create opponent-channel design matrix.

    Args:
        hue_angles: (n,) hue angles in degrees
        basis_type: 'opp2', 'opp4', 'opp4rect'

    Returns:
        C: (n, K) design matrix
    """
    theta = np.deg2rad(hue_angles)

    if basis_type == 'opp2':
        # Raw L-M and S-(L+M) axes
        # K=2: [cos(θ), sin(θ)]
        C = np.column_stack([np.cos(theta), np.sin(theta)])

    elif basis_type == 'opp4':
        # Opponent + quadrature: captures both linear and rectified responses
        # K=4: [cos(θ), sin(θ), cos(2θ), sin(2θ)]
        C = np.column_stack([
            np.cos(theta),
            np.sin(theta),
            np.cos(2 * theta),
            np.sin(2 * theta),
        ])

    elif basis_type == 'opp4rect':
        # Half-wave rectified opponent channels (double-opponent cells)
        # K=4: [cos+, cos−, sin+, sin−]
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        C = np.column_stack([
            np.maximum(cos_t, 0),   # L-M ON
            np.maximum(-cos_t, 0),  # M-L ON
            np.maximum(sin_t, 0),   # S ON
            np.maximum(-sin_t, 0),  # -S ON
        ])

    else:
        raise ValueError(f'Unknown opponent basis_type: {basis_type}')

    return C


# ============================================================================
# LOCO with fixed alpha
# ============================================================================

def loco_fixed_alpha(amp, C_full, alpha):
    """Run LOCO with pre-selected alpha. Returns mean voxel_corr across 8 colors."""
    corrs = []
    for tc in range(N_COLORS):
        train = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train, :].reshape(-1, amp.shape[2])
        C_train = np.tile(C_full[train], (N_RUNS, 1))
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)
        C_test = C_full[tc:tc+1]

        W = fit_W_ridge(C_train, X_train, alpha)
        Y_hat = C_test @ W
        r = voxel_pattern_correlation(Y_hat, X_test)
        corrs.append(r[0])
    return float(np.mean(corrs))


def select_alpha(amp, C_full):
    """Select best alpha via GCV on full data."""
    X_all = amp.reshape(-1, amp.shape[2])
    C_all = np.tile(C_full, (N_RUNS, 1))
    best_alpha, _ = gcv_select_alpha(C_all, X_all)
    return best_alpha


# ============================================================================
# Permutation engine
# ============================================================================

def run_perm_test(amp, C_full, n_perm, rng):
    """Run permutation test for one subject."""
    alpha = select_alpha(amp, C_full)
    observed = loco_fixed_alpha(amp, C_full, alpha)

    null_dist = np.zeros(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(N_COLORS)
        amp_perm = amp[:, perm, :]
        null_dist[i] = loco_fixed_alpha(amp_perm, C_full, alpha)

    p = float(np.mean(null_dist >= observed))
    return {
        'observed': float(observed),
        'null_mean': float(np.mean(null_dist)),
        'null_sd': float(np.std(null_dist)),
        'null_95ci': [float(np.percentile(null_dist, 2.5)),
                      float(np.percentile(null_dist, 97.5))],
        'p_perm': p,
        'alpha_used': float(alpha),
        'n_perm': n_perm,
    }


def stouffer_combine(p_vals):
    """Stouffer's method for combining p-values."""
    z_scores = []
    for p in p_vals:
        if p == 0:
            z_scores.append(3.5)
        elif p >= 1:
            z_scores.append(-3.5)
        else:
            z_scores.append(sp_stats.norm.ppf(1 - p))
    z = np.sum(z_scores) / np.sqrt(len(z_scores))
    return float(1 - sp_stats.norm.cdf(z))


# ============================================================================
# LORO for comparison
# ============================================================================

def loro_single(amp, C_full, alpha):
    """Run LORO with pre-selected alpha. Returns mean voxel_corr across runs."""
    corrs = []
    for run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != run]
        X_train = amp[train_runs].reshape(-1, amp.shape[2])
        C_train = np.tile(C_full, (len(train_runs), 1))
        X_test = amp[run]  # (8, V_s)
        C_test = C_full  # (8, K)

        W = fit_W_ridge(C_train, X_train, alpha)
        Y_hat = C_test @ W
        r = voxel_pattern_correlation(Y_hat, X_test)
        corrs.append(float(np.mean(r)))
    return float(np.mean(corrs))


# ============================================================================
# Main
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    bases = [
        ('OPP-2',     'opp2'),
        ('OPP-4',     'opp4'),
        ('OPP-4rect', 'opp4rect'),
        ('FE-6',      None),  # Use existing function
    ]

    # Focus on V1/V2 (primary targets), but include all ROIs
    test_rois = ['V1', 'V2', 'V3', 'V4']

    print(f'Opponent basis test: {N_PERM} permutations, seed={RNG_SEED}')
    print(f'Bases: {[b[0] for b in bases]}')
    print(f'ROIs: {test_rois}')
    print(f'Data: {BASELINE_DIR}')
    print()

    all_results = {}

    for basis_label, basis_type in bases:
        all_results[basis_label] = {}
        print(f'\n{"=" * 70}')
        print(f'  {basis_label}')
        print(f'{"=" * 70}')

        for roi in test_rois:
            all_results[basis_label][roi] = {}

            # Create design matrix
            if basis_type is not None:
                C_full = create_opponent_basis(HUE_ANGLES, basis_type)
            else:
                C_full = create_basis_matrix(HUE_ANGLES, 6, 'fe')

            print(f'\n--- {roi} ({basis_label}, K={C_full.shape[1]}) ---')

            # LORO (quick, no permutation)
            loro_vals = []
            loco_vals = []
            subj_results = []

            for subj in HC_SUBJECTS:
                amp = load_amplitudes(BASELINE_DIR, subj, roi)
                alpha = select_alpha(amp, C_full)

                # LORO
                r_loro = loro_single(amp, C_full, alpha)
                loro_vals.append(r_loro)

                # LOCO + permutation
                res = run_perm_test(amp, C_full, N_PERM, rng)
                res['loro'] = r_loro
                all_results[basis_label][roi][subj] = res
                subj_results.append(res)
                loco_vals.append(res['observed'])

                print(f'  sub-{subj}: LORO={r_loro:.3f}  '
                      f'LOCO={res["observed"]:.3f}  '
                      f'null={res["null_mean"]:.3f}  '
                      f'p={res["p_perm"]:.4f}')

            # Stouffer combined
            p_vals = [r['p_perm'] for r in subj_results]
            p_stouffer = stouffer_combine(p_vals)

            hc_loco = np.mean(loco_vals)
            hc_loro = np.mean(loro_vals)
            hc_null = np.mean([r['null_mean'] for r in subj_results])

            sig = '***' if p_stouffer < 0.001 else '**' if p_stouffer < 0.01 else \
                  '*' if p_stouffer < 0.05 else '†' if p_stouffer < 0.1 else ''

            print(f'  HC: LORO={hc_loro:.3f}  LOCO={hc_loco:.3f}  '
                  f'null={hc_null:.3f}  p_stouffer={p_stouffer:.4f} {sig}')

            # Store summary
            all_results[basis_label][roi]['_summary'] = {
                'hc_loro': hc_loro,
                'hc_loco': hc_loco,
                'hc_null': hc_null,
                'p_stouffer': p_stouffer,
            }

    # === CVD comparison (LOCO only, no permutation) ===
    print(f'\n\n{"=" * 70}')
    print('CVD LOCO (no permutation)')
    print(f'{"=" * 70}')

    for basis_label, basis_type in bases:
        for roi in test_rois:
            if basis_type is not None:
                C_full = create_opponent_basis(HUE_ANGLES, basis_type)
            else:
                C_full = create_basis_matrix(HUE_ANGLES, 6, 'fe')

            for subj in CVD_SUBJECTS:
                amp = load_amplitudes(BASELINE_DIR, subj, roi)
                alpha = select_alpha(amp, C_full)
                loco = loco_fixed_alpha(amp, C_full, alpha)
                all_results[basis_label][roi][subj] = {'observed': loco}

    # Save
    out_path = OUTPUT_DIR / 'opponent_basis_10K.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nResults saved to {out_path}')

    # === Summary table ===
    print(f'\n\n{"=" * 80}')
    print('SUMMARY')
    print(f'{"=" * 80}')
    print(f'{"Basis":<12} {"ROI":<5} {"LORO":>7} {"LOCO":>7} {"Null":>7} '
          f'{"Delta":>7} {"p_stouf":>8}')
    print('-' * 65)

    for basis_label, _ in bases:
        for roi in test_rois:
            s = all_results[basis_label][roi].get('_summary', {})
            if not s:
                continue
            delta = s['hc_loco'] - s['hc_null']
            sig = '***' if s['p_stouffer'] < 0.001 else '**' if s['p_stouffer'] < 0.01 else \
                  '*' if s['p_stouffer'] < 0.05 else '†' if s['p_stouffer'] < 0.1 else ''
            print(f'{basis_label:<12} {roi:<5} {s["hc_loro"]:>+7.3f} {s["hc_loco"]:>+7.3f} '
                  f'{s["hc_null"]:>+7.3f} {delta:>+7.3f} {s["p_stouffer"]:>8.4f} {sig}')
        print()

    # === HC-CVD comparison ===
    print(f'\n{"=" * 80}')
    print('HC vs CVD LOCO')
    print(f'{"=" * 80}')
    print(f'{"Basis":<12} {"ROI":<5} {"HC M":>7} {"CVD M":>7} {"d":>7}')
    print('-' * 50)

    for basis_label, _ in bases:
        for roi in ['V1', 'V2']:
            hc = [all_results[basis_label][roi][s]['observed'] for s in HC_SUBJECTS]
            cvd = [all_results[basis_label][roi][s]['observed'] for s in CVD_SUBJECTS]
            hc_m, cvd_m = np.mean(hc), np.mean(cvd)
            pooled_sd = np.sqrt((np.var(hc) * 6 + np.var(cvd) * 2) / 8)
            d = (hc_m - cvd_m) / pooled_sd if pooled_sd > 0 else 0
            print(f'{basis_label:<12} {roi:<5} {hc_m:>+7.3f} {cvd_m:>+7.3f} {d:>+7.2f}')
        print()


if __name__ == '__main__':
    main()
