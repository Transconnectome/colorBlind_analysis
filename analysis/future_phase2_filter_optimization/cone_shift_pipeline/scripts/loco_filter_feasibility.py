#!/usr/bin/env python3
"""
LOCO-primary filter design feasibility check.
Preliminary analysis for Phase 2 filter optimization.
"""

import numpy as np
from scipy.stats import spearmanr

# ============================================================
# 1. LOCO VULNERABILITY PROFILES (ridge_gcv per-color voxel_corr)
# ============================================================
# Colors: c0=red, c1=orange, c2=yellow, c3=green, c4=cyan, c5=blue, c6=purple, c7=magenta
color_names = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

loco = {
    'sub-08': {
        'cvd_type': 'deutan',
        'V1': np.array([0.1269, -0.1779, -0.4375, -0.0236, 0.4578, 0.1945, -0.4988, -0.1339]),
        'V2': np.array([0.5575, -0.5751, -0.6934, -0.3997, -0.2108, -0.2480, -0.4787, 0.1190]),
        'hV4': np.array([0.5730, -0.6368, -0.7331, -0.3057, 0.2499, -0.2506, -0.7588, -0.3343]),
    },
    'sub-09': {
        'cvd_type': 'protan',
        'V1': np.array([0.1198, -0.0004, -0.2441, -0.0816, 0.1811, 0.1121, -0.0092, -0.2415]),
        'V2': np.array([0.1441, 0.1007, -0.1177, 0.1577, 0.0159, -0.2015, -0.0733, -0.2209]),
        'hV4': np.array([0.0226, 0.5956, 0.3221, 0.1473, -0.4505, -0.2555, -0.0902, -0.5746]),
    },
    'sub-10': {
        'cvd_type': 'normal',
        'V1': np.array([0.0699, 0.1806, 0.0273, -0.0976, 0.0987, 0.1978, 0.0039, -0.1211]),
        'V2': np.array([-0.1762, -0.2021, -0.1777, -0.1865, -0.2456, -0.3608, -0.4253, -0.2829]),
        'hV4': np.array([-0.0057, 0.1603, 0.0691, 0.2925, 0.5084, 0.1826, -0.0279, -0.0846]),
    },
}

# JND HYPO pairs for sub-08 (deutan)
jnd_hypo_pairs = {
    'orange-yellow': {'ratio': 3.36, 'colors': [1, 2]},
    'yellow-green': {'ratio': 3.41, 'colors': [2, 3]},
    'yellow-purple': {'ratio': 2.95, 'colors': [2, 6]},
}
jnd_hyper_pairs = {
    'red-orange': {'ratio': 0.53, 'colors': [0, 1]},
    'red-cyan': {'ratio': 0.50, 'colors': [0, 4]},
}

# 2-Component and R+C delta_theta
dt_2comp = {
    'sub-08': np.array([0.54, -5.26, -9.94, -13.75, -17.24, -24.46, 17.53, 14.52]),
    'sub-09': np.array([-15.11, -19.62, -22.58, -24.44, -25.56, -21.93, 25.62, -0.36]),
}
dt_rc = {
    'sub-08': np.array([1.15, 2.83, 2.03, -0.49, -4.79, -4.55, 14.13, -1.91]),
    'sub-09': np.array([-4.96, -1.51, 0.06, -0.32, -2.20, -4.86, 11.51, 5.37]),
}

print("=" * 80)
print("1. LOCO VULNERABILITY ANALYSIS")
print("=" * 80)

for subj in ['sub-08', 'sub-09', 'sub-10']:
    cvd_type = loco[subj]['cvd_type']
    print(f"\n--- {subj} ({cvd_type}) ---")
    for roi in ['V1', 'V2', 'hV4']:
        v = loco[subj][roi]
        vuln_colors = [color_names[i] for i in range(8) if v[i] < -0.1]
        pres_colors = [color_names[i] for i in range(8) if v[i] > 0.1]
        print(f"  {roi}: range=[{v.min():.3f}, {v.max():.3f}], "
              f"mean={v.mean():.3f}, std={v.std():.3f}")
        print(f"       Vulnerable (<-0.1): {vuln_colors}")
        print(f"       Preserved  (>+0.1): {pres_colors}")

# ============================================================
# 2. CROSS-ROI CONSISTENCY (within subject)
# ============================================================
print("\n" + "=" * 80)
print("2. CROSS-ROI SPEARMAN CORRELATIONS (vulnerability profile consistency)")
print("=" * 80)

for subj in ['sub-08', 'sub-09', 'sub-10']:
    cvd_type = loco[subj]['cvd_type']
    print(f"\n--- {subj} ({cvd_type}) ---")
    for r1, r2 in [('V1', 'V2'), ('V1', 'hV4'), ('V2', 'hV4')]:
        rho, p = spearmanr(loco[subj][r1], loco[subj][r2])
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 't' if p < 0.1 else 'NS'
        print(f"  {r1} vs {r2}: rho={rho:.3f}, p={p:.4f} {sig}")

# ============================================================
# 3. LOCO->JND CONCORDANCE (sub-08 only, detailed)
# ============================================================
print("\n" + "=" * 80)
print("3. LOCO->JND CONCORDANCE (sub-08)")
print("=" * 80)

v08_hv4 = loco['sub-08']['hV4']
print("\nHYPO pairs (CVD worse than HC):")
for pair_name, info in jnd_hypo_pairs.items():
    c1, c2 = info['colors']
    vuln_involved = [f"{color_names[c]}={v08_hv4[c]:.3f}" for c in info['colors']]
    any_neg = any(v08_hv4[c] < 0 for c in info['colors'])
    vuln_str = ', '.join(vuln_involved)
    ratio = info['ratio']
    contains = 'YES' if any_neg else 'NO'
    print(f"  {pair_name} (ratio={ratio:.2f}x): "
          f"hV4 LOCO = [{vuln_str}], "
          f"contains_vulnerable={contains}")

print("\nHYPER pairs (CVD better than HC):")
for pair_name, info in jnd_hyper_pairs.items():
    c1, c2 = info['colors']
    vuln_involved = [f"{color_names[c]}={v08_hv4[c]:.3f}" for c in info['colors']]
    all_pos = all(v08_hv4[c] > 0 for c in info['colors'])
    vuln_str = ', '.join(vuln_involved)
    ratio = info['ratio']
    preserved = 'YES' if all_pos else 'NO'
    print(f"  {pair_name} (ratio={ratio:.2f}x): "
          f"hV4 LOCO = [{vuln_str}], "
          f"both_preserved={preserved}")

# ============================================================
# 4. FOURIER DECOMPOSITION OF DELTA_THETA
# ============================================================
print("\n" + "=" * 80)
print("4. FOURIER DECOMPOSITION OF MODEL DELTA_THETA")
print("=" * 80)

hue_approx = np.array([25, 65, 100, 160, 210, 270, 310, 345])
hue_rad = np.deg2rad(hue_approx)

for subj in ['sub-08', 'sub-09']:
    for model_name, dt_dict in [('2-Component', dt_2comp), ('R+C', dt_rc)]:
        dt = dt_dict[subj]
        A = np.column_stack([
            np.ones(8),
            np.sin(hue_rad), np.cos(hue_rad),
            np.sin(2*hue_rad), np.cos(2*hue_rad),
        ])
        coeffs, residuals, _, _ = np.linalg.lstsq(A, dt, rcond=None)
        dt_fit = A @ coeffs
        r2 = 1 - np.sum((dt - dt_fit)**2) / np.sum((dt - dt.mean())**2) if np.var(dt) > 0 else 0

        print(f"\n{subj} {model_name}:")
        print(f"  Original:  {np.array2string(dt, precision=1, separator=', ')}")
        print(f"  Fourier:   {np.array2string(dt_fit, precision=1, separator=', ')}")
        print(f"  Residual:  {np.array2string(dt - dt_fit, precision=1, separator=', ')}")
        print(f"  R2 = {r2:.3f} (5 params fit to 8 points)")
        print(f"  Coeffs: c0={coeffs[0]:.2f}, a1={coeffs[1]:.2f}, b1={coeffs[2]:.2f}, "
              f"a2={coeffs[3]:.2f}, b2={coeffs[4]:.2f}")
        max_res = np.max(np.abs(dt - dt_fit))
        print(f"  Max residual: {max_res:.2f} deg")

# ============================================================
# 5. VULNERABILITY PATTERN -> NEEDED FILTER DIRECTION
# ============================================================
print("\n" + "=" * 80)
print("5. FILTER DIRECTION ANALYSIS")
print("=" * 80)

for subj in ['sub-08', 'sub-09']:
    cvd_type = loco[subj]['cvd_type']
    print(f"\n--- {subj} ({cvd_type}) ---")
    v = loco[subj]['hV4']

    need_improve = [(i, color_names[i], v[i]) for i in range(8) if v[i] < -0.1]
    already_good = [(i, color_names[i], v[i]) for i in range(8) if v[i] > 0.1]

    print("  Colors needing improvement (LOCO < -0.1):")
    for i, name, val in sorted(need_improve, key=lambda x: x[2]):
        print(f"    c{i} {name}: vuln={val:.3f}")
    print("  Colors already good (LOCO > +0.1):")
    for i, name, val in sorted(already_good, key=lambda x: -x[2]):
        print(f"    c{i} {name}: vuln={val:.3f}")

    dt = dt_2comp[subj]
    need_idx = [x[0] for x in need_improve]
    good_idx = [x[0] for x in already_good]

    if need_idx and good_idx:
        mean_shift_vulnerable = np.mean(np.abs(dt[need_idx]))
        mean_shift_good = np.mean(np.abs(dt[good_idx]))
        ratio = mean_shift_vulnerable / mean_shift_good
        print(f"  2-Component mean |dtheta|: vulnerable={mean_shift_vulnerable:.1f} deg, "
              f"preserved={mean_shift_good:.1f} deg, ratio={ratio:.2f}x")

# ============================================================
# 6. CROSS-SUBJECT LOCO PROFILE COMPARISON
# ============================================================
print("\n" + "=" * 80)
print("6. CROSS-SUBJECT LOCO COMPARISON")
print("=" * 80)

for roi in ['V1', 'V2', 'hV4']:
    rho_08_09, _ = spearmanr(loco['sub-08'][roi], loco['sub-09'][roi])
    rho_08_10, _ = spearmanr(loco['sub-08'][roi], loco['sub-10'][roi])
    rho_09_10, _ = spearmanr(loco['sub-09'][roi], loco['sub-10'][roi])
    print(f"{roi}: sub-08 vs sub-09 rho={rho_08_09:.3f}, "
          f"sub-08 vs sub-10 rho={rho_08_10:.3f}, "
          f"sub-09 vs sub-10 rho={rho_09_10:.3f}")

# ============================================================
# 7. LOCO IMPROVEMENT POTENTIAL (how much room?)
# ============================================================
print("\n" + "=" * 80)
print("7. LOCO IMPROVEMENT POTENTIAL")
print("=" * 80)

for roi in ['V1', 'V2', 'hV4']:
    v10 = loco['sub-10'][roi]
    print(f"\nsub-10 (normal) {roi}: mean={v10.mean():.3f}, min={v10.min():.3f}, max={v10.max():.3f}")

    for subj in ['sub-08', 'sub-09']:
        v_cvd = loco[subj][roi]
        gap = v10.mean() - v_cvd.mean()
        per_color_gap = v10 - v_cvd
        worst_gap_idx = np.argmax(per_color_gap)
        worst_name = color_names[worst_gap_idx]
        worst_val = per_color_gap[worst_gap_idx]
        print(f"  vs {subj}: mean_gap={gap:.3f}, "
              f"worst_color=c{worst_gap_idx}({worst_name}) gap={worst_val:.3f}")

# ============================================================
# 8. FILTER LOSS FUNCTION ANALYSIS
# ============================================================
print("\n" + "=" * 80)
print("8. LOSS FUNCTION FEASIBILITY")
print("=" * 80)

print("\nR+C model LOCO fit quality:")
print("  sub-08 V1: rho=0.643 p=0.047* (baseline rho=0.476)")
print("  sub-08 V2: rho=0.571 p=0.077t (baseline rho=0.333)")
print("  sub-08 V4: rho=0.262 p=0.265 NS (baseline rho=0.357)")
print("  sub-09 V1: rho=0.357 p=0.197 NS")
print("  sub-09 V2: rho=-0.500 p=0.901 NS")
print("  sub-09 V4: rho=-0.357 p=0.822 NS")

print("\nLegacy shift_at_both LOCO fit:")
print("  sub-08 hV4: dlambda=8.64nm, r=0.690, p=0.036*")
print("  sub-09 hV4: dlambda=25.20nm, r=0.833, p=0.009***")

print("\nKey insight: sub-09 hV4 IS significant under shift_at_both but NS under W-fixed")
print("This means hV4 signal exists but W-fixed with K=3, alpha=1.0 is too constrained")
print("-> Filter for sub-09 should use shift_at_both or increase model flexibility")

# ============================================================
# 9. SUMMARY: FEASIBILITY VERDICT
# ============================================================
print("\n" + "=" * 80)
print("9. FEASIBILITY SUMMARY")
print("=" * 80)

print("""
SUB-08 (deutan) FEASIBILITY: HIGH
  Signal: LOCO V1 p=0.047*, V2 p=0.077t, hV4 shift_at_both p=0.036*
  Behavior: JND concordance 100% (3/3 HYPO pairs match LOCO vulnerable colors)
  Target colors: c1(orange), c2(yellow), c6(purple) -> consistent across V1/V2/hV4
  Fourier fit: check R2 above
  Risk: hV4 W-fixed NS -> may need shift_at_both approach
  
SUB-09 (protan) FEASIBILITY: MODERATE
  Signal: LOCO W-fixed ALL NS, BUT hV4 shift_at_both p=0.009***
  DRDM: 2-Component p=0.007***, R+C p=0.026*
  Target colors: c4(cyan), c5(blue), c7(magenta) in hV4
  Risk: W-fixed approach fails -> must use shift_at_both for filter
  Risk: No JND data for validation
  Risk: V1/V2 profiles weak -> cross-ROI validation limited
  
SUB-10 (control) FEASIBILITY: N/A (specificity check only)
  Expected: filter should have NO effect -> no-harm constraint test
""")
