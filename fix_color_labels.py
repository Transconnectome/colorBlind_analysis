"""
fix_color_labels.py
------------------
Generate correct LABEL2HUE_DEG_TEST from COLOR_LAB and verify usage

Test subjects (sub-01, 02, 03, 04) should use REGULAR 45° spacing
Pilot subject (sub-P01) uses IRREGULAR spacing from measured data

Date: 2025-11-17
"""

import numpy as np
import pandas as pd

# COLOR_LAB from experiment (Test subjects: sub-01~04)
COLOR_LAB = {
    'color_1': [75, -40.0, 0.0],       # 0도: Red
    'color_2': [75, -28.28, -28.28],   # 45도: Orange (a=b)
    'color_3': [75, 0.0, -40.0],       # 90도: Yellow
    'color_4': [75, 28.28, -28.28],    # 135도: Greenish
    'color_5': [75, 40.0, 0.0],        # 180도: Cyan
    'color_6': [75, 28.28, 28.28],     # 225도: Blue
    'color_7': [75, 0.0, 40.0],        # 270도: Violet (청색)
    'color_8': [75, -28.28, 28.28],    # 315도: Pinkish (Magenta)
    'blank': [75, 0.0, 0.0]            # L*=75, a*=0, b*=0 : Neutral Gray
}

# PILOT subject measured values (sub-P01)
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.142053052572436,
    'color_2': 287.979026187069735,
    'color_3': 305.226546308759566,
    'color_4': 330.204721787408289,
    'color_5': 35.269500805260478,
    'color_6': 73.365061454288877,
    'color_7': 125.585145639335096,
    'color_8': 143.909094545652778,
}

def lab_to_hue(L, a, b):
    """Calculate hue angle from Lab coordinates"""
    hue_rad = np.arctan2(b, a)
    hue_deg = np.degrees(hue_rad)
    # Normalize to 0-360
    if hue_deg < 0:
        hue_deg += 360
    return hue_deg

def generate_test_hues():
    """Generate LABEL2HUE_DEG_TEST from COLOR_LAB"""

    print("\n" + "="*80)
    print("GENERATING LABEL2HUE_DEG_TEST from COLOR_LAB")
    print("="*80)

    LABEL2HUE_DEG_TEST = {}

    print("\nColor | L    | a      | b      | Calculated Hue")
    print("-" * 60)

    for key, (L, a, b) in COLOR_LAB.items():
        if key != 'blank':
            hue = lab_to_hue(L, a, b)
            LABEL2HUE_DEG_TEST[key] = hue
            print(f"{key:<9} | {L:>4} | {a:>6.2f} | {b:>6.2f} | {hue:>8.2f}°")

    print("\n" + "="*80)
    print("GENERATED LABEL2HUE_DEG_TEST (for test subjects sub-01~04):")
    print("="*80)
    print("\nLABEL2HUE_DEG_TEST = {")
    for key in sorted(LABEL2HUE_DEG_TEST.keys()):
        print(f"    '{key}': {LABEL2HUE_DEG_TEST[key]},")
    print("}\n")

    return LABEL2HUE_DEG_TEST

def compare_pilot_vs_test():
    """Compare pilot vs test hue values"""

    test_hues = generate_test_hues()

    print("\n" + "="*80)
    print("COMPARISON: PILOT vs TEST Hue Values")
    print("="*80)
    print("\n{:<10} {:>15} {:>15} {:>15}".format(
        "Color", "PILOT (P01)", "TEST (01~04)", "Difference"
    ))
    print("-" * 60)

    for key in sorted(test_hues.keys()):
        pilot = LABEL2HUE_DEG_PILOT[key]
        test = test_hues[key]
        diff = test - pilot

        # Handle wrap-around
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        print(f"{key:<10} {pilot:>14.2f}° {test:>14.2f}° {diff:>14.2f}°")

    print("\n" + "="*80)
    print("CRITICAL ERROR IDENTIFIED")
    print("="*80)
    print("""
The current analysis scripts use LABEL2HUE_DEG_PILOT for ALL subjects!

CORRECT usage should be:
  - sub-P01 (pilot):     Use LABEL2HUE_DEG_PILOT (irregular spacing)
  - sub-01~04 (test):    Use LABEL2HUE_DEG_TEST (regular 45° spacing)

IMPACT:
  - All circular color space plots are WRONG for sub-01~04
  - Color reconstruction is using WRONG ground truth hues
  - Results need to be regenerated with correct labels
    """)

def create_subject_aware_code():
    """Generate code snippet for subject-aware hue selection"""

    print("\n" + "="*80)
    print("CORRECTED CODE SNIPPET")
    print("="*80)

    code = '''
# Color hue definitions (Lab hue angles in degrees)

# TEST subjects (sub-01, 02, 03, 04): Regular 45° spacing
LABEL2HUE_DEG_TEST = {
    'color_1': 180.0,   # Red
    'color_2': 225.0,   # Orange
    'color_3': 270.0,   # Yellow
    'color_4': 315.0,   # Greenish
    'color_5': 0.0,     # Cyan
    'color_6': 45.0,    # Blue
    'color_7': 90.0,    # Violet
    'color_8': 135.0,   # Pinkish
}

# PILOT subject (sub-P01): Measured irregular spacing
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.14,
    'color_2': 287.98,
    'color_3': 305.23,
    'color_4': 330.20,
    'color_5': 35.27,
    'color_6': 73.37,
    'color_7': 125.59,
    'color_8': 143.91,
}

def get_label2hue_for_subject(subject_id):
    """
    Return appropriate LABEL2HUE_DEG based on subject

    Parameters:
    -----------
    subject_id : str
        Subject ID (e.g., '01', '02', 'P01')

    Returns:
    --------
    dict : LABEL2HUE_DEG_TEST or LABEL2HUE_DEG_PILOT
    """
    if subject_id.startswith('P'):
        return LABEL2HUE_DEG_PILOT
    else:
        return LABEL2HUE_DEG_TEST

# Usage in analysis script:
# LABEL2HUE_DEG = get_label2hue_for_subject(SUBJECT_ID)
#
# Then use LABEL2HUE_DEG throughout instead of hardcoded LABEL2HUE_DEG_PILOT
'''

    print(code)

    # Save to file
    with open('corrected_color_labels.py', 'w') as f:
        f.write(code)

    print("\n✓ Saved to: corrected_color_labels.py")

def main():
    """Main function"""

    # Generate test hues
    test_hues = generate_test_hues()

    # Compare
    compare_pilot_vs_test()

    # Create corrected code
    create_subject_aware_code()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF REQUIRED FIXES")
    print("="*80)
    print("""
1. ✅ GENERATED: LABEL2HUE_DEG_TEST from COLOR_LAB

2. ⚠️  IDENTIFIED: Current analysis uses PILOT values for ALL subjects

3. 📝 REQUIRED ACTIONS:

   a) Update analysis scripts:
      - Add LABEL2HUE_DEG_TEST definition
      - Add get_label2hue_for_subject() function
      - Replace all LABEL2HUE_DEG_PILOT references with dynamic selection

   b) Re-run analysis for sub-01, 02, 03, 04:
      - All results are currently INCORRECT
      - Circular color space plots show WRONG positions
      - Reconstruction uses WRONG ground truth

   c) Keep pilot (sub-P01) results:
      - These are correct (uses measured values)

4. 📊 IMPACT:
   - Classification accuracy: Likely UNAFFECTED (uses voxel patterns)
   - Reconstruction error: WILL CHANGE (different ground truth hues)
   - Circular plots: WILL CHANGE (different color positions)
   - Novel color error: WILL CHANGE (different target positions)

5. 🔧 NEXT STEPS:
   - Review and approve corrected_color_labels.py
   - Update PERSUB_fir_reconstruction_universal_hrf.py
   - Re-run analysis for sub-01~04
   - Regenerate all plots and compilations
    """)

if __name__ == "__main__":
    main()
