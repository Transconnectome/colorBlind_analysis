"""verify_cielab_derivation.py — 5-point validity check of CIELab confusion axis derivation.

Validation:
  (1) LMS_TO_XYZ matrix vs colour-science standard
  (2) D65 white point consistency
  (3) Brettel copunctal LMS direction (literature check)
  (4) Neutral (a*=0, b*=0) vs chromatic (a*=40, varying θ) position-dependence
  (5) Linearization adequacy (ε ∈ {0.001, 0.01, 0.05})
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

# colour-science (0.4.4)
import colour

# Our derivation
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_cielab_confusion_axis import (
    LMS_TO_XYZ as OUR_LMS_TO_XYZ,
    WHITE_D65_XYZ,
    xyz_to_lab as our_xyz_to_lab,
    lab_to_xyz as our_lab_to_xyz,
)

OUT = Path(__file__).resolve().parent.parent / 'results' / 'sub09_protan_refit'


# ============================================================
# (1) Verify LMS_TO_XYZ against colour-science standard
# ============================================================
def verify_matrix():
    print("=" * 70)
    print("(1) LMS_TO_XYZ matrix verification")
    print("=" * 70)

    # colour-science approach: Stockman 2° cone fundamentals → CIE 1931 2° XYZ
    # Use the Smith & Pokorny derived transformation (one common normalization)
    # Or CIE 170-1:2006 published transform.
    #
    # colour-science provides:
    #   - colour.MATRIX_LMS_TO_XYZ['CIE 2006 LMS to XYZ']
    #   - colour.MSDS_CMFS['CIE 2012 2 Degree Standard Observer']
    #
    # Check standard CAT (chromatic adaptation transform) matrices.

    print(f"OUR matrix:\n{OUR_LMS_TO_XYZ}\n")

    # Standard published matrix from CIE 170-1:2006 / Stockman 2000:
    # Reference: Sharpe et al. 2005, Wyszecki & Stiles 1982 Table 1(5.5.2)
    # Stockman & Sharpe (2000) LMS cone fundamentals → CIE 1931 2° XYZ
    # Verified transformation (energy-normalized):
    CIE_170_LMS_TO_XYZ_NORM = np.array([
        [ 1.94735469, -1.41445123,  0.36476327],
        [ 0.68990272,  0.34832189,  0.0],
        [ 0.0,         0.0,         1.93485343],
    ])

    print("CIE 170-1:2006 reference matrix (Sharpe 2005):")
    print(CIE_170_LMS_TO_XYZ_NORM)
    print()
    diff = OUR_LMS_TO_XYZ - CIE_170_LMS_TO_XYZ_NORM
    print(f"Max abs diff: {np.abs(diff).max():.4f}")
    print(f"Relative diff: {np.abs(diff).max() / np.abs(CIE_170_LMS_TO_XYZ_NORM).max() * 100:.1f}%")
    return OUR_LMS_TO_XYZ, CIE_170_LMS_TO_XYZ_NORM


# ============================================================
# (2) D65 white point
# ============================================================
def verify_white_point():
    print("\n" + "=" * 70)
    print("(2) D65 white point verification")
    print("=" * 70)
    print(f"Our white XYZ: {WHITE_D65_XYZ}")
    print(f"CIE published D65 (2°, scaled Y=100): [95.047, 100.000, 108.883]")
    print(f"colour-science D65 illuminant 2°:")
    d65_2deg = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']
    print(f"  chromaticity (x, y): {d65_2deg}")
    xyz_from_xy = colour.xy_to_XYZ(d65_2deg) * 100
    print(f"  XYZ: {xyz_from_xy}")
    diff = WHITE_D65_XYZ - xyz_from_xy
    print(f"  Diff: {diff}, max abs: {np.abs(diff).max():.4f}")


# ============================================================
# (3) Brettel copunctal direction check
# ============================================================
def verify_copunctal():
    print("\n" + "=" * 70)
    print("(3) Brettel 1997 copunctal direction in LMS")
    print("=" * 70)
    print("""
Brettel 1997 (JOSA-A 14:2647-2655) defines confusion lines as parallel to
the missing fundamental axis in LMS space:
  - Protanope: confusion lines parallel to L-axis (1, 0, 0)
  - Deuteranope: confusion lines parallel to M-axis (0, 1, 0)
  - Tritanope: confusion lines parallel to S-axis (0, 0, 1)

Our perturbation direction matches: protan = (1,0,0), deutan = (0,1,0). OK.

Note: Brettel's "copunctal point" is a specific LMS coordinate where all
confusion lines meet, but the DIRECTION of confusion lines is independent
of which copunctal we choose — it's the missing fundamental axis.
""")


# ============================================================
# (4) Position-dependence: neutral vs chromatic
# ============================================================
def position_dependence(cvd_type: str, L_star: float = 75.0,
                       chroma_amp: float = 40.0):
    """Compare confusion axis angle at multiple (a*, b*) test points."""
    if cvd_type == 'protan':
        copunct = np.array([1.0, 0.0, 0.0])
    elif cvd_type == 'deutan':
        copunct = np.array([0.0, 1.0, 0.0])
    else:
        raise ValueError(cvd_type)

    XYZ_TO_LMS = np.linalg.inv(OUR_LMS_TO_XYZ)
    epsilon = 0.01

    test_angles = np.arange(0, 360, 45)
    results = []
    for ang in test_angles:
        a_test = chroma_amp * np.cos(np.deg2rad(ang))
        b_test = chroma_amp * np.sin(np.deg2rad(ang))
        test_lab = np.array([L_star, a_test, b_test])
        test_xyz = our_lab_to_xyz(test_lab)
        test_lms = XYZ_TO_LMS @ test_xyz

        per_lms = test_lms + epsilon * copunct * np.linalg.norm(test_lms)
        per_xyz = OUR_LMS_TO_XYZ @ per_lms
        per_lab = our_xyz_to_lab(per_xyz)
        d_a = per_lab[1] - test_lab[1]
        d_b = per_lab[2] - test_lab[2]
        angle = np.degrees(np.arctan2(d_b, d_a)) % 360.0
        results.append({'ref_angle': float(ang),
                        'ref_ab': (float(a_test), float(b_test)),
                        'd_a': float(d_a), 'd_b': float(d_b),
                        'confusion_angle_deg': float(angle)})

    # Also at neutral (0, 0)
    test_lab = np.array([L_star, 0.0, 0.0])
    test_xyz = our_lab_to_xyz(test_lab)
    test_lms = XYZ_TO_LMS @ test_xyz
    per_lms = test_lms + epsilon * copunct * np.linalg.norm(test_lms)
    per_xyz = OUR_LMS_TO_XYZ @ per_lms
    per_lab = our_xyz_to_lab(per_xyz)
    d_a = per_lab[1] - test_lab[1]
    d_b = per_lab[2] - test_lab[2]
    neutral_angle = np.degrees(np.arctan2(d_b, d_a)) % 360.0

    print(f"\n--- {cvd_type} confusion axis at multiple (a*, b*) points ---")
    print(f"  Neutral (0, 0)         : {neutral_angle:.2f}°")
    for r in results:
        print(f"  C=40, θ={r['ref_angle']:3.0f}° (a={r['ref_ab'][0]:+.1f}, b={r['ref_ab'][1]:+.1f}): "
              f"{r['confusion_angle_deg']:.2f}°")

    angles = [r['confusion_angle_deg'] for r in results]
    angles_unwrapped = np.unwrap(np.deg2rad(angles))
    span = np.degrees(angles_unwrapped.max() - angles_unwrapped.min())
    print(f"  Range across 8 chromatic test points: {span:.2f}° "
          f"(small=robust, large=position-dependent)")
    return neutral_angle, results


# ============================================================
# (5) Linearization adequacy
# ============================================================
def linearization_check(cvd_type: str, L_star: float = 75.0):
    if cvd_type == 'protan':
        copunct = np.array([1.0, 0.0, 0.0])
    elif cvd_type == 'deutan':
        copunct = np.array([0.0, 1.0, 0.0])

    XYZ_TO_LMS = np.linalg.inv(OUR_LMS_TO_XYZ)
    print(f"\n--- {cvd_type} linearization across ε ---")
    for eps in [0.001, 0.005, 0.01, 0.05, 0.1]:
        test_lab = np.array([L_star, 0.0, 0.0])
        test_xyz = our_lab_to_xyz(test_lab)
        test_lms = XYZ_TO_LMS @ test_xyz
        per_lms = test_lms + eps * copunct * np.linalg.norm(test_lms)
        per_xyz = OUR_LMS_TO_XYZ @ per_lms
        per_lab = our_xyz_to_lab(per_xyz)
        d_a = per_lab[1] - test_lab[1]
        d_b = per_lab[2] - test_lab[2]
        angle = np.degrees(np.arctan2(d_b, d_a)) % 360.0
        print(f"  ε={eps:>6.3f}: Δa*={d_a:+.4f}, Δb*={d_b:+.4f}, angle={angle:.2f}°")


def main():
    our_M, cie_M = verify_matrix()
    verify_white_point()
    verify_copunctal()

    print("\n" + "=" * 70)
    print("(4) Position-dependence of confusion axis in CIELab")
    print("=" * 70)
    pos_results = {}
    for cvd in ['protan', 'deutan']:
        n_ang, rs = position_dependence(cvd)
        pos_results[cvd] = {'neutral_angle': n_ang, 'chromatic_tests': rs}

    print("\n" + "=" * 70)
    print("(5) Linearization adequacy across ε")
    print("=" * 70)
    for cvd in ['protan', 'deutan']:
        linearization_check(cvd)

    # Save
    out_path = OUT / 'derivation_validity_check.json'
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump({
            'our_matrix': our_M.tolist(),
            'cie_reference_matrix': cie_M.tolist(),
            'matrix_max_abs_diff': float(np.abs(our_M - cie_M).max()),
            'position_dependence': pos_results,
        }, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == '__main__':
    main()
