#!/usr/bin/env python3
"""
cone_shift_validation.py — Step 1 + Step 2: Cone shift validation.

Step 1: Build CIELab ↔ opponent lookup, compute θ_equiv for each CVD color.
Step 2: Compare shifted opponent RDM with SRM CVD RDM (Mantel-style).

Runs locally (conda env: srm).

Usage:
    cd analysis/phase4_forward_model
    python scripts/cone_shift_validation.py
"""

import json
import sys
import numpy as np
from pathlib import Path
from itertools import combinations
from scipy.stats import spearmanr, pearsonr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stockman_cone_shift import (
    load_stockman_fundamentals, compute_xyz_to_lms_matrix,
    compute_shifted_hue_angles, lab_to_xyz, lms_to_opponent,
    opponent_to_hue_angle, _compute_spectral_shift_lms,
    shift_cone_sensitivity,
    COLOR_LAB, HUE_ANGLES_DEG, CVD_TYPE, D65_XYZ,
    L_STAR, CHROMA,
)

# Paths
BASE = Path(__file__).resolve().parent.parent
CONE_SHIFT_JSON = BASE / 'results' / 'cone_shift' / 'cone_shift_results.json'
SRM_RESULTS_JSON = (BASE.parent / 'phase5_filter_optimization' /
                    'pre_validation' / 'results' /
                    'filter_pre_validation_results.json')
OUTPUT_DIR = BASE / 'results' / 'cone_shift'

COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8
PAIR_INDICES = list(combinations(range(N_COLORS), 2))
PAIR_LABELS = [f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}" for i, j in PAIR_INDICES]


# ============================================================================
# Step 1: CIELab ↔ Opponent Lookup + θ_equiv
# ============================================================================

def build_cielab_to_opponent_lookup(wavelengths, L, M, S, resolution=1):
    """Build lookup table: CIELab hue angle → opponent hue angle.

    Computes opponent hue for CIELab angles at `resolution` degree intervals.
    Uses L*=60, chroma=40 (same as experimental stimuli).

    Returns:
        cielab_angles: (N,) CIELab angles
        opponent_angles: (N,) corresponding opponent angles
    """
    M_xyz2lms = compute_xyz_to_lms_matrix(wavelengths, L, M, S)

    cielab_angles = np.arange(0, 360, resolution, dtype=float)
    n = len(cielab_angles)

    # Build CIELab coordinates for each angle
    lab_coords = np.zeros((n, 3))
    for i, h in enumerate(cielab_angles):
        h_rad = np.deg2rad(h)
        lab_coords[i] = [L_STAR, CHROMA * np.cos(h_rad), CHROMA * np.sin(h_rad)]

    # CIELab → XYZ → LMS → opponent → hue angle
    xyz = lab_to_xyz(lab_coords)
    lms = _compute_spectral_shift_lms(
        wavelengths, L, M, S, M_xyz2lms, xyz
    )
    rg, by = lms_to_opponent(lms)
    opponent_angles = opponent_to_hue_angle(rg, by)

    return cielab_angles, opponent_angles


def opponent_to_cielab_inverse(target_opp_angle, cielab_angles, opponent_angles):
    """Inverse lookup: given opponent angle, find closest CIELab angle.

    Uses circular distance for matching.

    Args:
        target_opp_angle: scalar, opponent angle in degrees
        cielab_angles: (N,) lookup CIELab angles
        opponent_angles: (N,) lookup opponent angles

    Returns:
        best_cielab: closest CIELab angle
        min_dist: circular distance to nearest match
    """
    # Circular distance between target and each opponent angle
    diff = opponent_angles - target_opp_angle
    circ_dist = np.abs((diff + 180) % 360 - 180)
    best_idx = np.argmin(circ_dist)
    return float(cielab_angles[best_idx]), float(circ_dist[best_idx])


def compute_theta_equiv(wavelengths, L, M, S, delta_lambda, cvd_type,
                        cielab_angles, opponent_angles):
    """Compute θ_equiv: CIELab angle that produces the shifted opponent angle
    in a normal eye.

    For each of 8 colors:
      1. Get shifted opponent angle (from cone shift model)
      2. Inverse lookup: what CIELab angle would produce this in normal eye?
      3. That's θ_equiv — "what CVD perceives this color as"

    Returns:
        theta_equiv: (8,) CIELab-equivalent angles
        lookup_errors: (8,) circular distance of nearest match (quality check)
        opp_normal: (8,) normal opponent angles
        opp_shifted: (8,) shifted opponent angles
    """
    opp_normal, opp_shifted, delta_theta = compute_shifted_hue_angles(
        wavelengths, L, M, S, delta_lambda, cvd_type
    )

    theta_equiv = np.zeros(N_COLORS)
    lookup_errors = np.zeros(N_COLORS)

    for i in range(N_COLORS):
        theta_equiv[i], lookup_errors[i] = opponent_to_cielab_inverse(
            opp_shifted[i], cielab_angles, opponent_angles
        )

    return theta_equiv, lookup_errors, opp_normal, opp_shifted


# ============================================================================
# Step 2: RDM Comparison
# ============================================================================

def circular_distance(a, b):
    """Circular distance in degrees, [0, 180]."""
    d = np.abs(a - b)
    return np.minimum(d, 360 - d)


def compute_angular_rdm(angles):
    """Compute 8×8 angular distance matrix from hue angles."""
    n = len(angles)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            rdm[i, j] = circular_distance(angles[i], angles[j])
    return rdm


def rdm_upper_tri(rdm):
    """Extract upper triangle as 1D vector (28 values for 8×8)."""
    idx = np.triu_indices_from(rdm, k=1)
    return rdm[idx]


def mantel_test(rdm1_vec, rdm2_vec):
    """Mantel test: Spearman + Pearson correlation between RDM vectors."""
    rho, p_rho = spearmanr(rdm1_vec, rdm2_vec)
    r, p_r = pearsonr(rdm1_vec, rdm2_vec)
    return {
        'spearman_r': float(rho), 'spearman_p': float(p_rho),
        'pearson_r': float(r), 'pearson_p': float(p_r),
    }


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 70)
    print("Cone Shift Validation: Step 1 (θ_equiv) + Step 2 (RDM comparison)")
    print("=" * 70)

    # Load data
    with open(CONE_SHIFT_JSON) as f:
        cone_shift = json.load(f)
    with open(SRM_RESULTS_JSON) as f:
        srm_data = json.load(f)

    b1 = srm_data['results']['hV4']['B1_permutation']
    hc_pair_dists = b1['hc_pair_distances']
    cvd_pair_dists = b1['cvd_pair_distances']

    # Load cone fundamentals
    wavelengths, L, M, S = load_stockman_fundamentals()

    # ================================================================
    # Step 1: Build lookup + compute θ_equiv
    # ================================================================
    print("\n[Step 1] Building CIELab ↔ opponent lookup (1° resolution)...")
    cielab_angles, opponent_angles = build_cielab_to_opponent_lookup(
        wavelengths, L, M, S, resolution=1
    )

    # Show the mapping for 8 experimental colors
    print("\n  CIELab → Opponent mapping (normal eye, 8 experimental colors):")
    print(f"  {'CIELab':>8s}  {'Opponent':>8s}  {'Color':>8s}")
    for i in range(N_COLORS):
        cl = HUE_ANGLES_DEG[i]
        # Find opponent angle for this CIELab angle
        idx = int(cl) % 360
        op = opponent_angles[idx]
        print(f"  {cl:8.0f}°  {op:8.1f}°  {COLOR_NAMES[i]:>8s}")

    # Check if mapping is monotonic
    diffs = np.diff(opponent_angles)
    sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
    print(f"\n  Mapping monotonicity: {sign_changes} direction changes in 360° sweep")
    print(f"  (0 = monotonic, >0 = non-monotonic → inverse is multi-valued)")

    # Compute θ_equiv for each CVD subject
    all_results = {}

    for cvd_subj in ['sub-08', 'sub-09', 'sub-10']:
        cvd_type = cone_shift[cvd_subj]['cvd_type']
        dl = cone_shift[cvd_subj]['best_delta_lambda_nm']

        print(f"\n{'=' * 70}")
        print(f"[{cvd_subj}] type={cvd_type}, Δλ*={dl}nm")
        print(f"{'=' * 70}")

        effective_type = cvd_type if cvd_type in ('deutan', 'protan') else 'deutan'
        theta_equiv, errors, opp_n, opp_s = compute_theta_equiv(
            wavelengths, L, M, S, dl, effective_type,
            cielab_angles, opponent_angles
        )

        print(f"\n  θ_equiv (CVD가 지각하는 등가 CIELab 각도):")
        print(f"  {'Color':>8s}  {'CIELab':>8s}  {'Opp_N':>8s}  {'Opp_S':>8s}  "
              f"{'δθ_opp':>8s}  {'θ_equiv':>8s}  {'Δ_CIELab':>10s}  {'err':>5s}")
        for i in range(N_COLORS):
            delta_cielab = theta_equiv[i] - HUE_ANGLES_DEG[i]
            delta_cielab = (delta_cielab + 180) % 360 - 180
            delta_opp = opp_s[i] - opp_n[i]
            delta_opp = (delta_opp + 180) % 360 - 180
            print(f"  {COLOR_NAMES[i]:>8s}  {HUE_ANGLES_DEG[i]:8.0f}°  "
                  f"{opp_n[i]:8.1f}°  {opp_s[i]:8.1f}°  {delta_opp:+8.1f}°  "
                  f"{theta_equiv[i]:8.1f}°  {delta_cielab:+10.1f}°  {errors[i]:5.1f}°")

        # Sanity check: is the color order preserved?
        order_original = np.argsort(HUE_ANGLES_DEG)
        order_equiv = np.argsort(theta_equiv)
        order_preserved = np.array_equal(order_original, order_equiv)
        print(f"\n  Color order preserved: {order_preserved}")
        if not order_preserved:
            print(f"    Original order: {[COLOR_NAMES[i] for i in order_original]}")
            print(f"    θ_equiv order:  {[COLOR_NAMES[i] for i in order_equiv]}")

        # ================================================================
        # Step 2: RDM comparison
        # ================================================================
        print(f"\n  --- RDM Comparison ---")

        # RDM 1: Normal opponent angular distance
        rdm_opp_normal = compute_angular_rdm(opp_n)
        vec_opp_normal = rdm_upper_tri(rdm_opp_normal)

        # RDM 2: Shifted opponent angular distance
        rdm_opp_shifted = compute_angular_rdm(opp_s)
        vec_opp_shifted = rdm_upper_tri(rdm_opp_shifted)

        # RDM 3: θ_equiv CIELab angular distance
        rdm_equiv = compute_angular_rdm(theta_equiv)
        vec_equiv = rdm_upper_tri(rdm_equiv)

        # RDM 4: Normal CIELab angular distance (ideal circular)
        rdm_cielab = compute_angular_rdm(HUE_ANGLES_DEG)
        vec_cielab = rdm_upper_tri(rdm_cielab)

        # SRM RDM: HC mean pair distances
        hc_dists_all = np.array([hc_pair_dists[f'sub-{s:02d}']
                                 for s in range(1, 8)])
        vec_hc_mean = hc_dists_all.mean(axis=0)

        # SRM RDM: CVD pair distances
        vec_cvd = np.array(cvd_pair_dists[cvd_subj])

        # CVD-HC raw gap
        vec_gap = vec_cvd - vec_hc_mean

        # Comparisons
        print(f"\n  [A] Opponent RDM vs SRM RDM:")
        r1 = mantel_test(vec_opp_normal, vec_cvd)
        r2 = mantel_test(vec_opp_shifted, vec_cvd)
        r3 = mantel_test(vec_opp_normal, vec_hc_mean)
        print(f"    Normal_Opp  vs CVD_SRM:  rho={r1['spearman_r']:+.3f} (p={r1['spearman_p']:.3f})")
        print(f"    Shifted_Opp vs CVD_SRM:  rho={r2['spearman_r']:+.3f} (p={r2['spearman_p']:.3f})")
        print(f"    Normal_Opp  vs HC_SRM:   rho={r3['spearman_r']:+.3f} (p={r3['spearman_p']:.3f})")
        print(f"    Δ(Shifted-Normal vs CVD): {r2['spearman_r'] - r1['spearman_r']:+.3f}")

        print(f"\n  [B] θ_equiv CIELab RDM vs SRM RDM:")
        r4 = mantel_test(vec_cielab, vec_cvd)
        r5 = mantel_test(vec_equiv, vec_cvd)
        r6 = mantel_test(vec_cielab, vec_hc_mean)
        print(f"    Ideal_CIELab vs CVD_SRM: rho={r4['spearman_r']:+.3f} (p={r4['spearman_p']:.3f})")
        print(f"    θ_equiv      vs CVD_SRM: rho={r5['spearman_r']:+.3f} (p={r5['spearman_p']:.3f})")
        print(f"    Ideal_CIELab vs HC_SRM:  rho={r6['spearman_r']:+.3f} (p={r6['spearman_p']:.3f})")
        print(f"    Δ(θ_equiv-Ideal vs CVD): {r5['spearman_r'] - r4['spearman_r']:+.3f}")

        print(f"\n  [C] Predicted Δdist vs Raw CVD-HC gap:")
        delta_dist_opp = vec_opp_shifted - vec_opp_normal
        r7 = mantel_test(delta_dist_opp, vec_gap)
        print(f"    Δdist_opp vs (CVD-HC)_raw:  rho={r7['spearman_r']:+.3f} (p={r7['spearman_p']:.3f})")
        print(f"                                r_p={r7['pearson_r']:+.3f} (p={r7['pearson_p']:.3f})")

        delta_dist_equiv = vec_equiv - vec_cielab
        r8 = mantel_test(delta_dist_equiv, vec_gap)
        print(f"    Δdist_equiv vs (CVD-HC)_raw: rho={r8['spearman_r']:+.3f} (p={r8['spearman_p']:.3f})")
        print(f"                                 r_p={r8['pearson_r']:+.3f} (p={r8['pearson_p']:.3f})")

        all_results[cvd_subj] = {
            'cvd_type': cvd_type,
            'delta_lambda_nm': dl,
            'theta_equiv_deg': theta_equiv.tolist(),
            'lookup_errors_deg': errors.tolist(),
            'delta_cielab_deg': [
                float((theta_equiv[i] - HUE_ANGLES_DEG[i] + 180) % 360 - 180)
                for i in range(N_COLORS)
            ],
            'color_order_preserved': bool(order_preserved),
            'rdm_comparison': {
                'normal_opp_vs_cvd_srm': r1,
                'shifted_opp_vs_cvd_srm': r2,
                'normal_opp_vs_hc_srm': r3,
                'ideal_cielab_vs_cvd_srm': r4,
                'theta_equiv_vs_cvd_srm': r5,
                'ideal_cielab_vs_hc_srm': r6,
                'delta_dist_opp_vs_gap': r7,
                'delta_dist_equiv_vs_gap': r8,
            },
        }

    # Save
    out_path = OUTPUT_DIR / 'cone_shift_validation_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n{'=' * 70}")
    print(f"Results saved to {out_path}")


if __name__ == '__main__':
    main()
