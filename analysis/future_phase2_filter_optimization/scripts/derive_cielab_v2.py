"""derive_cielab_v2.py — CIELab confusion axis using CIE 170-1:2006 reference matrix.

Replaces the approximate matrix in derive_cielab_confusion_axis.py.
Also averages over the 8 experimental stimulus hues (C*=40, L*=75) instead
of relying on neutral-only measurement, since protan exhibits ±4° position
dependence in CIELab.
"""
from __future__ import annotations
import numpy as np
import json
from pathlib import Path

# CIE 170-1:2006 Sharpe 2005 reference (Stockman & Sharpe 2000 → CIE 2° XYZ)
CIE_LMS_TO_XYZ = np.array([
    [ 1.94735469, -1.41445123,  0.36476327],
    [ 0.68990272,  0.34832189,  0.0],
    [ 0.0,         0.0,         1.93485343],
])

WHITE_D65_XYZ = np.array([95.047, 100.000, 108.883])

L_STAR = 75.0
CHROMA = 40.0
HUE_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)


def xyz_to_lab(xyz, white=WHITE_D65_XYZ):
    xyz_n = xyz / white
    delta = 6.0 / 29.0
    f = lambda t: np.where(t > delta**3, np.cbrt(t), t / (3 * delta**2) + 4.0 / 29.0)
    fx, fy, fz = f(xyz_n[..., 0]), f(xyz_n[..., 1]), f(xyz_n[..., 2])
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def lab_to_xyz(lab, white=WHITE_D65_XYZ):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    delta = 6.0 / 29.0
    fi = lambda t: np.where(t > delta, t**3, 3 * delta**2 * (t - 4.0 / 29.0))
    X = white[0] * fi(fx); Y = white[1] * fi(fy); Z = white[2] * fi(fz)
    return np.stack([X, Y, Z], axis=-1)


def confusion_angle_at(a_test, b_test, copunct, eps=0.01,
                       lms_to_xyz=CIE_LMS_TO_XYZ):
    XYZ_TO_LMS = np.linalg.inv(lms_to_xyz)
    test_lab = np.array([L_STAR, a_test, b_test])
    test_xyz = lab_to_xyz(test_lab)
    test_lms = XYZ_TO_LMS @ test_xyz
    per_lms = test_lms + eps * copunct * np.linalg.norm(test_lms)
    per_xyz = lms_to_xyz @ per_lms
    per_lab = xyz_to_lab(per_xyz)
    d_a = per_lab[1] - test_lab[1]
    d_b = per_lab[2] - test_lab[2]
    return float(np.degrees(np.arctan2(d_b, d_a)) % 360.0), float(d_a), float(d_b)


def per_family(cvd_type):
    copunct = {'protan': np.array([1.0, 0.0, 0.0]),
               'deutan': np.array([0.0, 1.0, 0.0])}[cvd_type]

    # (a) Neutral point
    ang_neutral, _, _ = confusion_angle_at(0.0, 0.0, copunct)

    # (b) 8 experimental stimulus points (C*=40, hues 0..315)
    per_hue = []
    for hue in HUE_8:
        a_t = CHROMA * np.cos(np.deg2rad(hue))
        b_t = CHROMA * np.sin(np.deg2rad(hue))
        ang, d_a, d_b = confusion_angle_at(a_t, b_t, copunct)
        per_hue.append({'hue_deg': float(hue), 'a*': a_t, 'b*': b_t,
                        'd_a': d_a, 'd_b': d_b, 'angle_deg': ang})

    # Circular mean over 8 hues
    angles_rad = np.array([np.deg2rad(p['angle_deg']) for p in per_hue])
    mean_ang = float(np.degrees(np.arctan2(np.sin(angles_rad).mean(),
                                            np.cos(angles_rad).mean())) % 360.0)
    angles = np.array([p['angle_deg'] for p in per_hue])
    span = float(angles.max() - angles.min())

    return {
        'family': cvd_type,
        'neutral_angle': ang_neutral,
        'mean_over_8_hues': mean_ang,
        'min_over_8_hues': float(angles.min()),
        'max_over_8_hues': float(angles.max()),
        'span_over_8_hues': span,
        'per_hue': per_hue,
    }


def main():
    print("=" * 70)
    print("CIELab confusion axis (CIE 170-1:2006 reference matrix, L*=75)")
    print("=" * 70)
    print(f"LMS→XYZ matrix:\n{CIE_LMS_TO_XYZ}\n")

    results = {}
    for cvd in ['protan', 'deutan']:
        r = per_family(cvd)
        results[cvd] = r
        print(f"\n--- {cvd} ---")
        print(f"  Neutral (0,0):       {r['neutral_angle']:.2f}°")
        print(f"  Mean over 8 stimuli: {r['mean_over_8_hues']:.2f}°")
        print(f"  Range over 8 stim:   [{r['min_over_8_hues']:.2f}°, "
              f"{r['max_over_8_hues']:.2f}°] (span={r['span_over_8_hues']:.2f}°)")

    print("\n" + "=" * 70)
    print("Summary: three candidate confusion axes")
    print("=" * 70)
    print(f"{'family':<10s} {'current(OLD)':>14s} {'Stockman':>10s} "
          f"{'CIELab neutral':>16s} {'CIELab 8-stim mean':>20s}")
    for cvd in ['protan', 'deutan']:
        s = {'protan': 16.0, 'deutan': 150.0}[cvd]
        c_neutral = results[cvd]['neutral_angle']
        c_mean = results[cvd]['mean_over_8_hues']
        cur = 150.0
        print(f"{cvd:<10s} {cur:>14.1f} {s:>10.1f} {c_neutral:>16.2f} {c_mean:>20.2f}")

    out_path = (Path(__file__).resolve().parent.parent
                / 'results' / 'sub09_protan_refit'
                / 'cielab_confusion_axis_v2.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump({
            'matrix_source': 'CIE 170-1:2006 / Sharpe 2005 (Stockman 2000 fundamentals)',
            'matrix': CIE_LMS_TO_XYZ.tolist(),
            'L_star': L_STAR, 'chroma': CHROMA,
            'experimental_hues_deg': HUE_8.tolist(),
            'results': results,
        }, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == '__main__':
    main()
