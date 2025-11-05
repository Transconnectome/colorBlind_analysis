#!/usr/bin/env python
"""
Compare colors across three sources:
1. IRB document (intended design)
2. Pilot experiment (colorBlind_pilotTest.py)
3. Main experiment (colorBlind_test.py)
"""

import numpy as np
from skimage import color

print("=" * 100)
print("COLOR COMPARISON: IRB vs PILOT vs MAIN EXPERIMENT")
print("=" * 100)
print()

# ============================================================
# 1. IRB Document Lab Hue Values (Intended)
# ============================================================
IRB_LAB_HUE = {
    'color_1': 178.5695366901941,
    'color_2': 310.7676279123204,
    'color_3': 316.10116190386,
    'color_4': 333.8636890033205,
    'color_5': 54.5026811654645,
    'color_6': 68.44990693644588,
    'color_7': 130.78364209927355,
    'color_8': 153.7216350869142,
}

# ============================================================
# 2. Pilot Experiment RGB (colorBlind_pilotTest.py)
# ============================================================
PILOT_RGB = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    'color_3': [-0.98, -0.80,  0.96],  # yellow
    'color_4': [ 0.60, -0.56,  0.52],  # greenish
    'color_5': [ 1.00, -0.48, -0.56],  # cyan
    'color_6': [ 0.90,  0.24, -0.90],  # blue
    'color_7': [-0.24,  0.20, -0.72],  # violet
    'color_8': [-0.90, -0.20, -0.70],  # pinkish
}

# ============================================================
# 3. Main Experiment Lab Values (colorBlind_test.py)
# ============================================================
MAIN_LAB = {
    'color_1': [75, -40.0, 0.0],       # 0°: Red
    'color_2': [75, -28.28, -28.28],   # 45°: Orange
    'color_3': [75, 0.0, -40.0],       # 90°: Yellow
    'color_4': [75, 28.28, -28.28],    # 135°: Greenish
    'color_5': [75, 40.0, 0.0],        # 180°: Cyan
    'color_6': [75, 28.28, 28.28],     # 225°: Blue
    'color_7': [75, 0.0, 40.0],        # 270°: Violet
    'color_8': [75, -28.28, 28.28],    # 315°: Pinkish
}

# ============================================================
# Conversion Functions
# ============================================================

def psychopy_rgb_to_srgb(psychopy_rgb):
    """Convert PsychoPy RGB [-1, 1] to sRGB [0, 1]"""
    return [(x + 1.0) / 2.0 for x in psychopy_rgb]

def rgb_to_lab_hue(rgb_01):
    """Convert RGB [0,1] to Lab hue angle"""
    rgb_array = np.array(rgb_01).reshape(1, 1, 3)
    lab_array = color.rgb2lab(rgb_array)
    L, a, b = lab_array[0, 0, :]
    hue_rad = np.arctan2(b, a)
    hue_deg = np.degrees(hue_rad)
    if hue_deg < 0:
        hue_deg += 360
    return hue_deg, L, a, b

def lab_to_hue(L, a, b):
    """Compute hue angle from Lab values"""
    hue_rad = np.arctan2(b, a)
    hue_deg = np.degrees(hue_rad)
    if hue_deg < 0:
        hue_deg += 360
    return hue_deg

def lab2rgb_main(L, a, b, clip=True):
    """Lab to RGB conversion from colorBlind_test.py"""
    L, a, b = float(L), float(a), float(b)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1., 1.08883]
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)
    if clip:
        rgb = np.clip(rgb, 0, 1)
    rgb_psychopy = (rgb * 2) - 1
    return rgb_psychopy.tolist()

# ============================================================
# Compute Pilot Lab Hue
# ============================================================
print("STEP 1: Compute Lab hue from PILOT RGB values")
print("-" * 100)

pilot_lab_hue = {}
pilot_lab_full = {}
for label, psychopy_rgb in sorted(PILOT_RGB.items()):
    srgb = psychopy_rgb_to_srgb(psychopy_rgb)
    hue_deg, L, a, b = rgb_to_lab_hue(srgb)
    pilot_lab_hue[label] = hue_deg
    pilot_lab_full[label] = (L, a, b)
    print(f"{label}: RGB {psychopy_rgb} → Lab({L:.1f}, {a:.2f}, {b:.2f}) → Hue {hue_deg:.2f}°")

print()

# ============================================================
# Compute Main Lab Hue
# ============================================================
print("STEP 2: Compute Lab hue from MAIN experiment Lab values")
print("-" * 100)

main_lab_hue = {}
main_rgb = {}
for label, lab_vals in sorted(MAIN_LAB.items()):
    L, a, b = lab_vals
    hue_deg = lab_to_hue(L, a, b)
    main_lab_hue[label] = hue_deg
    rgb_psychopy = lab2rgb_main(L, a, b)
    main_rgb[label] = rgb_psychopy
    print(f"{label}: Lab({L:.1f}, {a:.2f}, {b:.2f}) → Hue {hue_deg:.2f}° → RGB {[f'{x:.3f}' for x in rgb_psychopy]}")

print()

# ============================================================
# COMPARISON TABLE
# ============================================================
print("=" * 100)
print("COMPREHENSIVE COMPARISON TABLE")
print("=" * 100)
print(f"{'Color':<10} {'IRB Hue':<12} {'Pilot Hue':<12} {'Main Hue':<12} {'IRB-Pilot':<12} {'IRB-Main':<12} {'Pilot-Main':<12}")
print("-" * 100)

max_irb_pilot = 0
max_irb_main = 0
max_pilot_main = 0
worst_irb_pilot = None
worst_irb_main = None
worst_pilot_main = None

for label in sorted(IRB_LAB_HUE.keys()):
    irb = IRB_LAB_HUE[label]
    pilot = pilot_lab_hue[label]
    main = main_lab_hue[label]

    # Circular differences
    diff_irb_pilot = min(abs(irb - pilot), 360 - abs(irb - pilot))
    diff_irb_main = min(abs(irb - main), 360 - abs(irb - main))
    diff_pilot_main = min(abs(pilot - main), 360 - abs(pilot - main))

    if diff_irb_pilot > max_irb_pilot:
        max_irb_pilot = diff_irb_pilot
        worst_irb_pilot = label
    if diff_irb_main > max_irb_main:
        max_irb_main = diff_irb_main
        worst_irb_main = label
    if diff_pilot_main > max_pilot_main:
        max_pilot_main = diff_pilot_main
        worst_pilot_main = label

    print(f"{label:<10} {irb:>8.2f}°  {pilot:>8.2f}°  {main:>8.2f}°  {diff_irb_pilot:>8.2f}°  {diff_irb_main:>8.2f}°  {diff_pilot_main:>8.2f}°")

print("=" * 100)
print()

# ============================================================
# ANALYSIS SUMMARY
# ============================================================
print("ANALYSIS SUMMARY")
print("=" * 100)
print()

print("1. IRB vs PILOT:")
print(f"   Maximum difference: {max_irb_pilot:.2f}° ({worst_irb_pilot})")
print(f"   → IRB values DO NOT match pilot experiment!")
print()

print("2. IRB vs MAIN:")
print(f"   Maximum difference: {max_irb_main:.2f}° ({worst_irb_main})")
print(f"   → IRB values DO NOT match main experiment!")
print()

print("3. PILOT vs MAIN:")
print(f"   Maximum difference: {max_pilot_main:.2f}° ({worst_pilot_main})")
if max_pilot_main < 10:
    print(f"   → Pilot and main are similar (but you should analyze MAIN data with MAIN colors!)")
else:
    print(f"   → Pilot and main are DIFFERENT experiments!")
print()

# ============================================================
# SPACING ANALYSIS
# ============================================================
print("=" * 100)
print("HUEUE SPACING ANALYSIS")
print("=" * 100)
print()

print("Main Experiment (Intended - Brouwer & Heeger 2009):")
print("   Uniformly spaced at 45° intervals: [0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]")
main_hues_sorted = sorted([(hue, label) for label, hue in main_lab_hue.items()])
print(f"   Actual: {[f'{h:.1f}°' for h, _ in main_hues_sorted]}")
print()

print("Pilot Experiment:")
pilot_hues_sorted = sorted([(hue, label) for label, hue in pilot_lab_hue.items()])
print(f"   Hues: {[f'{h:.1f}°' for h, _ in pilot_hues_sorted]}")
spacings = []
for i in range(len(pilot_hues_sorted)):
    h1 = pilot_hues_sorted[i][0]
    h2 = pilot_hues_sorted[(i+1) % len(pilot_hues_sorted)][0]
    spacing = (h2 - h1) % 360
    spacings.append(spacing)
print(f"   Spacing: {[f'{s:.1f}°' for s in spacings]}")
print(f"   Min spacing: {min(spacings):.1f}°, Max spacing: {max(spacings):.1f}°")
print()

# ============================================================
# RECOMMENDATIONS
# ============================================================
print("=" * 100)
print("RECOMMENDATIONS")
print("=" * 100)
print()

print("❗ CRITICAL: You are analyzing PILOT data (sub-01)")
print()
print("✅ ACTION REQUIRED:")
print("   Use the Lab hue values computed from PILOT RGB (colorBlind_pilotTest.py)")
print("   These are already updated in naive_analysis.py")
print()
print("📊 Lab hue values for PILOT data (already in naive_analysis.py):")
print("   LABEL2HUE_DEG = {")
for label, hue in sorted(pilot_lab_hue.items()):
    print(f"       '{label}': float({hue:.15f}),")
print("   }")
print()
print("⚠️  When you analyze MAIN experiment data in the future:")
print("   You MUST update to use MAIN experiment Lab hue values:")
print("   LABEL2HUE_DEG = {")
for label, hue in sorted(main_lab_hue.items()):
    print(f"       '{label}': float({hue:.15f}),")
print("   }")
print()

print("=" * 100)
print("RGB COMPARISON: PILOT vs MAIN")
print("=" * 100)
print(f"{'Color':<10} {'Pilot RGB':<35} {'Main RGB':<35} {'Match':<10}")
print("-" * 100)

for label in sorted(PILOT_RGB.keys()):
    pilot_rgb = PILOT_RGB[label]
    main_rgb_val = main_rgb[label]

    pilot_str = f"[{pilot_rgb[0]:>6.3f}, {pilot_rgb[1]:>6.3f}, {pilot_rgb[2]:>6.3f}]"
    main_str = f"[{main_rgb_val[0]:>6.3f}, {main_rgb_val[1]:>6.3f}, {main_rgb_val[2]:>6.3f}]"

    # Check if RGB values are similar (within 0.05)
    match = all(abs(pilot_rgb[i] - main_rgb_val[i]) < 0.05 for i in range(3))
    match_str = "✅ Yes" if match else "❌ No"

    print(f"{label:<10} {pilot_str:<35} {main_str:<35} {match_str:<10}")

print("=" * 100)
