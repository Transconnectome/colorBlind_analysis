#!/usr/bin/env python
"""Test RGB to HSV conversion for color stimuli"""

import numpy as np

# PsychoPy RGB values (-1 to 1)
COLOR_RGB = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    'color_3': [-0.98, -0.80,  0.96],  # yellow
    'color_4': [ 0.60, -0.56,  0.52],  # greenish
    'color_5': [ 1.00, -0.48, -0.56],  # cyan
    'color_6': [ 0.90,  0.24, -0.90],  # blue
    'color_7': [-0.24,  0.20, -0.72],  # violet
    'color_8': [-0.90, -0.20, -0.70],  # pinkish
}

# Lab hue (original - from IRB)
LABEL2HUE_LAB = {
    'color_1': 178.5695366901941,
    'color_2': 310.7676279123204,
    'color_3': 316.10116190386,
    'color_4': 333.8636890033205,
    'color_5': 54.5026811654645,
    'color_6': 68.44990693644588,
    'color_7': 130.78364209927355,
    'color_8': 153.7216350869142,
}

def rgb_to_hsv_deg(rgb01):
    """Convert RGB [0,1] to HSV hue in degrees"""
    r, g, b = rgb01
    mx, mn = max(rgb01), min(rgb01)
    diff = mx - mn
    if diff == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360
    s = 0.0 if mx == 0 else diff / mx
    v = mx
    return h, s, v

print("="*70)
print("RGB → HSV Conversion Test")
print("="*70)
print(f"{'Color':<10} {'RGB (Psychopy)':<25} {'Lab Hue':<12} {'HSV Hue':<12} {'Diff':<8}")
print("-"*70)

for i in range(1, 9):
    label = f'color_{i}'
    rgb_pm1 = COLOR_RGB[label]
    rgb01 = [np.clip((x + 1) / 2, 0.0, 1.0) for x in rgb_pm1]
    h, s, v = rgb_to_hsv_deg(rgb01)
    lab_hue = LABEL2HUE_LAB[label]

    # Circular difference
    diff = abs(h - lab_hue)
    if diff > 180:
        diff = 360 - diff

    rgb_str = f"[{rgb_pm1[0]:.2f}, {rgb_pm1[1]:.2f}, {rgb_pm1[2]:.2f}]"
    print(f"{label:<10} {rgb_str:<25} {lab_hue:>8.1f}°  {h:>8.1f}°  {diff:>6.1f}°")

print("="*70)
print("\nIssue: Lab hue ≠ HSV hue!")
print("Lab hue is perceptually uniform (better for color science)")
print("HSV hue is RGB-based (not perceptually uniform)")
