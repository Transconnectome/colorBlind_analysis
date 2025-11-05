#!/usr/bin/env python
"""
Compute actual Lab hue angles from the RGB values presented in the experiment.
This ensures ground truth hue matches what participants actually saw.
"""

import numpy as np
from skimage import color

# PsychoPy RGB values (-1 to 1) as presented in colorBlind_pilotTest.py
COLOR_RGB_PSYCHOPY = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    'color_3': [-0.98, -0.80,  0.96],  # yellow
    'color_4': [ 0.60, -0.56,  0.52],  # greenish
    'color_5': [ 1.00, -0.48, -0.56],  # cyan
    'color_6': [ 0.90,  0.24, -0.90],  # blue
    'color_7': [-0.24,  0.20, -0.72],  # violet
    'color_8': [-0.90, -0.20, -0.70],  # pinkish
}

# Lab hue values currently used (from IRB)
LABEL2HUE_LAB_IRB = {
    'color_1': 178.5695366901941,
    'color_2': 310.7676279123204,
    'color_3': 316.10116190386,
    'color_4': 333.8636890033205,
    'color_5': 54.5026811654645,
    'color_6': 68.44990693644588,
    'color_7': 130.78364209927355,
    'color_8': 153.7216350869142,
}

def psychopy_rgb_to_srgb(psychopy_rgb):
    """Convert PsychoPy RGB [-1, 1] to sRGB [0, 1]"""
    return [(x + 1.0) / 2.0 for x in psychopy_rgb]

def rgb_to_lab_hue(rgb_01):
    """
    Convert RGB [0,1] to Lab hue angle in degrees.
    Uses scikit-image for accurate RGB→Lab conversion.
    """
    # RGB to Lab (scikit-image expects RGB in [0,1])
    rgb_array = np.array(rgb_01).reshape(1, 1, 3)
    lab_array = color.rgb2lab(rgb_array)

    L, a, b = lab_array[0, 0, :]

    # Compute hue angle in degrees
    hue_rad = np.arctan2(b, a)
    hue_deg = np.degrees(hue_rad)

    # Convert to [0, 360) range
    if hue_deg < 0:
        hue_deg += 360

    return hue_deg, L, a, b

print("=" * 80)
print("ACTUAL LAB HUE COMPUTATION FROM EXPERIMENT RGB VALUES")
print("=" * 80)
print()
print("Step 1: Convert PsychoPy RGB [-1,1] → sRGB [0,1]")
print("Step 2: Convert sRGB [0,1] → CIELab (L, a, b)")
print("Step 3: Compute hue angle = atan2(b, a) in degrees")
print()
print("=" * 80)

print(f"{'Color':<12} {'PsychoPy RGB':<30} {'sRGB [0,1]':<30}")
print("-" * 80)

srgb_colors = {}
for label, psychopy_rgb in sorted(COLOR_RGB_PSYCHOPY.items()):
    srgb = psychopy_rgb_to_srgb(psychopy_rgb)
    srgb_colors[label] = srgb

    psychopy_str = f"[{psychopy_rgb[0]:>6.2f}, {psychopy_rgb[1]:>6.2f}, {psychopy_rgb[2]:>6.2f}]"
    srgb_str = f"[{srgb[0]:>5.3f}, {srgb[1]:>5.3f}, {srgb[2]:>5.3f}]"
    print(f"{label:<12} {psychopy_str:<30} {srgb_str:<30}")

print()
print("=" * 80)
print(f"{'Color':<12} {'Lab (L,a,b)':<30} {'Hue (deg)':<12} {'IRB Hue':<12} {'Diff':<8}")
print("-" * 80)

computed_hues = {}
max_diff = 0
max_diff_color = None

for label, srgb in sorted(srgb_colors.items()):
    hue_deg, L, a, b = rgb_to_lab_hue(srgb)
    computed_hues[label] = hue_deg

    irb_hue = LABEL2HUE_LAB_IRB[label]
    diff = abs(hue_deg - irb_hue)
    if diff > 180:
        diff = 360 - diff

    if diff > max_diff:
        max_diff = diff
        max_diff_color = label

    lab_str = f"({L:>5.1f}, {a:>6.2f}, {b:>6.2f})"
    print(f"{label:<12} {lab_str:<30} {hue_deg:>8.2f}°  {irb_hue:>8.2f}°  {diff:>6.2f}°")

print("=" * 80)
print()

if max_diff < 0.1:
    print("✅ RESULT: IRB Lab hue values are CORRECT!")
    print(f"   Maximum difference: {max_diff:.4f}° (essentially zero)")
    print()
    print("   The Lab hue values in naive_analysis.py match the actual presented colors.")
    print("   No modification needed.")
else:
    print(f"❌ RESULT: IRB Lab hue values differ from actual presented colors!")
    print(f"   Maximum difference: {max_diff:.2f}° for {max_diff_color}")
    print()
    print("   You should update LABEL2HUE_DEG in naive_analysis.py with computed values:")
    print()
    print("LABEL2HUE_DEG = {")
    for label, hue in sorted(computed_hues.items()):
        print(f"    '{label}': float({hue:.15f}),")
    print("}")

print()
print("=" * 80)
print("ADDITIONAL INFO: Intended vs Actual Design")
print("=" * 80)

# Check if these were intended to be uniformly spaced
uniform_spacing = [0, 45, 90, 135, 180, 225, 270, 315]
print()
print("Brouwer & Heeger (2009) used 8 colors uniformly spaced at 45° intervals:")
print("  [0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]")
print()
print("Your actual Lab hue angles (sorted by value):")
sorted_hues = sorted([(hue, label) for label, hue in computed_hues.items()])
for hue, label in sorted_hues:
    print(f"  {label}: {hue:>6.2f}°")
print()
print("These are NOT uniformly spaced. The experiment used non-uniform Lab hues.")
