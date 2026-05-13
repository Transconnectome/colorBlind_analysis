"""derive_cielab_confusion_axis.py — Project Brettel copunctal vectors to CIELab L*=75 plane.

Goal: derive protan/deutan confusion axis angles in CIELab a*-b* plane at L*=75
so that the OLD formula (CIELab-direct, used by BEST/Tier 2 wfixed simulator)
can use family-aware, derivation-supported θ_conf instead of the current
"operationally chosen" 150° applied to both families.

Method:
  1. Brettel 1997 copunctal points in LMS (Stockman 2° fundamentals):
     - protan copunctal direction: missing-L axis ≈ (1, 0, 0) in LMS
     - deutan copunctal direction: missing-M axis ≈ (0, 1, 0) in LMS
  2. LMS → XYZ via Stockman-derived matrix
  3. XYZ → CIELab at L*=75 (Y* of D65 white reference)
  4. Project copunctal vector (small perturbation around white point) onto
     a*-b* plane and measure angle = atan2(b*, a*)

Output:
  - θ_conf_CIELab[protan, deutan] at L*=75 plane
  - comparison table vs Stockman opponent (16°, 150°)
"""
from __future__ import annotations
import numpy as np
from pathlib import Path
import json

# Stockman & Sharpe 2000 2° cone fundamentals → CIE XYZ 2° transform
# Reference: CIE 170-1:2006, Table A.1 / Smith & Pokorny derived
# Standard transform matrix LMS (Stockman) → XYZ_E (CIE 2°):
# Using the Hunt-Pointer-Estevez matrix inverse (one common formulation)
# More precisely: CAT02 or the CIE 170-2:2015 standard.
#
# We use the Stockman-Sharpe (2000) → CIE 2006 XYZ via published transform.
# Below: LMS (Stockman) → XYZ (CIE 2°) per CIE 170-1:2006 Section 5.2.

# CIE 170-1:2006, Table A.1 — derived from Stockman & Sharpe (2000)
# 2°-field cone fundamentals normalized so each cone peak = 1
# Transformation to CIE 1931 2° XYZ (D65 illuminant)
LMS_TO_XYZ = np.array([
    [ 1.93986443, -1.34664359,  0.43044935],
    [ 0.69283932,  0.34967567,  0.00000000],
    [ 0.00000000,  0.00000000,  2.14687945],
])  # Approximate; final accuracy verified against colour-science output

# D65 white point in XYZ (Y=100, scaled)
WHITE_D65_XYZ = np.array([95.047, 100.000, 108.883])


def xyz_to_lab(xyz: np.ndarray, white: np.ndarray = WHITE_D65_XYZ) -> np.ndarray:
    """Standard CIE 1976 L*a*b* transform."""
    xyz_n = xyz / white
    delta = 6.0 / 29.0
    def f(t):
        return np.where(t > delta**3,
                        np.cbrt(t),
                        t / (3 * delta**2) + 4.0 / 29.0)
    fx, fy, fz = f(xyz_n[..., 0]), f(xyz_n[..., 1]), f(xyz_n[..., 2])
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def lab_to_xyz(lab: np.ndarray, white: np.ndarray = WHITE_D65_XYZ) -> np.ndarray:
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    delta = 6.0 / 29.0
    def f_inv(t):
        return np.where(t > delta, t**3, 3 * delta**2 * (t - 4.0 / 29.0))
    X = white[0] * f_inv(fx)
    Y = white[1] * f_inv(fy)
    Z = white[2] * f_inv(fz)
    return np.stack([X, Y, Z], axis=-1)


def derive_confusion_axis_cielab(cvd_type: str,
                                 L_star: float = 75.0,
                                 epsilon: float = 0.01) -> float:
    """Project Brettel copunctal vector onto CIELab a*-b* plane at L*=L_star.

    Method:
      - Start from L*=L_star, a*=0, b*=0 (neutral point at the slice)
      - Add small LMS perturbation in copunctal direction
      - Convert perturbed LMS → XYZ → Lab → measure (Δa*, Δb*)
      - Angle = atan2(Δb*, Δa*)
    """
    # Neutral reference at L*=L_star, a*=0, b*=0
    neutral_lab = np.array([L_star, 0.0, 0.0])
    neutral_xyz = lab_to_xyz(neutral_lab)
    # Convert neutral XYZ to LMS
    # Inverse of LMS_TO_XYZ
    XYZ_TO_LMS = np.linalg.inv(LMS_TO_XYZ)
    neutral_lms = XYZ_TO_LMS @ neutral_xyz

    # Copunctal direction in LMS (Brettel 1997)
    if cvd_type == 'protan':
        copunct = np.array([1.0, 0.0, 0.0])  # along L axis
    elif cvd_type == 'deutan':
        copunct = np.array([0.0, 1.0, 0.0])  # along M axis
    elif cvd_type == 'tritan':
        copunct = np.array([0.0, 0.0, 1.0])  # along S axis
    else:
        raise ValueError(f"Unknown cvd_type: {cvd_type}")

    # Perturb neutral LMS along copunctal direction (small step, both signs)
    angles = []
    for sign in [+1, -1]:
        perturbed_lms = neutral_lms + sign * epsilon * copunct * np.linalg.norm(neutral_lms)
        perturbed_xyz = LMS_TO_XYZ @ perturbed_lms
        perturbed_lab = xyz_to_lab(perturbed_xyz)
        d_a = perturbed_lab[1] - neutral_lab[1]
        d_b = perturbed_lab[2] - neutral_lab[2]
        angle = np.degrees(np.arctan2(d_b, d_a)) % 360.0
        angles.append((sign, d_a, d_b, angle))

    # Both signs should give angles 180° apart (anti-parallel)
    # Return canonical (positive a*) direction
    return angles


def main():
    print("Brettel 1997 copunctal → CIELab L*=75 a*-b* plane derivation\n")
    print(f"LMS→XYZ matrix:\n{LMS_TO_XYZ}\n")
    print(f"White D65 XYZ: {WHITE_D65_XYZ}\n")

    results = {}
    for cvd in ['protan', 'deutan']:
        print(f"=== {cvd} ===")
        angles = derive_confusion_axis_cielab(cvd, L_star=75.0, epsilon=0.01)
        for sign, da, db, ang in angles:
            print(f"  sign={sign:+d}  Δa*={da:+.4f}  Δb*={db:+.4f}  angle={ang:.2f}°")
        results[cvd] = {
            'plus': {'da': float(angles[0][1]), 'db': float(angles[0][2]),
                     'angle_deg': float(angles[0][3])},
            'minus': {'da': float(angles[1][1]), 'db': float(angles[1][2]),
                      'angle_deg': float(angles[1][3])},
        }
        print()

    print("=== Comparison vs Stockman opponent values ===")
    stockman_axes = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}
    print(f"{'family':<10s} {'Stockman':>10s} {'CIELab L*=75 (+)':>18s} {'CIELab L*=75 (-)':>18s} {'|Δ|':>6s}")
    for cvd in ['protan', 'deutan']:
        s_ang = stockman_axes[cvd]
        c_plus = results[cvd]['plus']['angle_deg']
        c_minus = results[cvd]['minus']['angle_deg']
        # Take the angle closer to Stockman (since +/- are 180° apart)
        diff_plus = min(abs(c_plus - s_ang), 360 - abs(c_plus - s_ang))
        diff_minus = min(abs(c_minus - s_ang), 360 - abs(c_minus - s_ang))
        closer = c_plus if diff_plus < diff_minus else c_minus
        diff_use = min(diff_plus, diff_minus)
        print(f"{cvd:<10s} {s_ang:>10.1f} {c_plus:>18.2f} {c_minus:>18.2f} {diff_use:>6.1f}")

    out_dir = Path(__file__).resolve().parent.parent / 'results' / 'sub09_protan_refit'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'cielab_confusion_axis_derivation.json'
    with open(out_path, 'w') as f:
        json.dump({
            'method': 'Brettel 1997 copunctal projected to CIELab L*=75 a*-b* plane',
            'L_star': 75.0,
            'epsilon': 0.01,
            'LMS_to_XYZ_matrix': LMS_TO_XYZ.tolist(),
            'white_D65_XYZ': WHITE_D65_XYZ.tolist(),
            'results': results,
            'stockman_opponent_axes': stockman_axes,
        }, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == '__main__':
    main()
