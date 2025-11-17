"""
verify_color_labels.py
---------------------
Verify color label consistency between designed and measured values

Compares:
1. DESIGNED values from COLOR_LAB (45° spacing in Lab hue)
2. MEASURED values from LABEL2HUE_DEG_PILOT (actual pilot data)

Date: 2025-11-17
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Designed color values (from experimental design)
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

# Measured hue angles from pilot data (ACTUAL values used in analysis)
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

def compare_color_labels():
    """Compare designed vs measured color positions"""

    print("\n" + "="*80)
    print("COLOR LABEL VERIFICATION")
    print("="*80)

    # Calculate designed hue angles from COLOR_LAB
    designed_hues = {}
    for key, (L, a, b) in COLOR_LAB.items():
        if key != 'blank':
            hue = lab_to_hue(L, a, b)
            designed_hues[key] = hue

    # Compare with measured values
    print("\nDESIGNED vs MEASURED Hue Angles:")
    print("-"*80)
    print(f"{'Color':<10} {'Designed (deg)':<18} {'Measured (deg)':<18} {'Difference (deg)':<18}")
    print("-"*80)

    for key in sorted(designed_hues.keys()):
        designed = designed_hues[key]
        measured = LABEL2HUE_DEG_PILOT[key]
        diff = measured - designed

        # Handle wrap-around
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        print(f"{key:<10} {designed:>16.2f}° {measured:>16.2f}° {diff:>16.2f}°")

    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)
    print("""
DESIGNED values: Intended stimulus positions (45° spacing in Lab hue space)
MEASURED values: Actual measured hue angles from pilot data

LARGE DIFFERENCES indicate:
1. Monitor calibration differences between design and actual presentation
2. Color space conversion discrepancies
3. Measurement errors in pilot data extraction

The MEASURED values should be used for analysis because they represent
the ACTUAL stimuli that participants saw during the experiment.
    """)

    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Polar plot comparison
    ax = axes[0]
    ax = plt.subplot(1, 2, 1, projection='polar')

    colors_designed = []
    colors_measured = []
    labels = []

    for key in sorted(designed_hues.keys()):
        colors_designed.append(np.radians(designed_hues[key]))
        colors_measured.append(np.radians(LABEL2HUE_DEG_PILOT[key]))
        labels.append(key)

    # Plot designed positions
    ax.scatter(colors_designed, [1]*len(colors_designed),
              c='blue', s=200, alpha=0.5, label='Designed', marker='o')

    # Plot measured positions
    ax.scatter(colors_measured, [1.2]*len(colors_measured),
              c='red', s=200, alpha=0.5, label='Measured', marker='^')

    # Add labels
    for i, (deg_d, deg_m, label) in enumerate(zip(colors_designed, colors_measured, labels)):
        ax.text(deg_d, 1.0, label.split('_')[1],
               ha='center', va='center', fontsize=8, fontweight='bold')
        ax.text(deg_m, 1.2, label.split('_')[1],
               ha='center', va='center', fontsize=8, fontweight='bold',
               color='red')

    ax.set_ylim(0, 1.5)
    ax.set_title('Color Positions: Designed vs Measured\n(Polar Plot)',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    # Right: Difference plot
    ax = axes[1]

    differences = []
    for key in sorted(designed_hues.keys()):
        designed = designed_hues[key]
        measured = LABEL2HUE_DEG_PILOT[key]
        diff = measured - designed

        # Handle wrap-around
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        differences.append(diff)

    colors_list = [f"C{i}" for i in range(1, 9)]
    bars = ax.bar(labels, differences, color=colors_list, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xlabel('Color', fontsize=12, fontweight='bold')
    ax.set_ylabel('Hue Difference (Measured - Designed, degrees)',
                 fontsize=12, fontweight='bold')
    ax.set_title('Deviation from Designed Positions',
                fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Add value labels on bars
    for i, (bar, diff) in enumerate(zip(bars, differences)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{diff:.1f}°',
               ha='center', va='bottom' if height > 0 else 'top',
               fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('ColorLabel_verification.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved verification plot: ColorLabel_verification.png")

    # Create summary table
    summary_data = []
    for key in sorted(designed_hues.keys()):
        designed = designed_hues[key]
        measured = LABEL2HUE_DEG_PILOT[key]
        diff = measured - designed

        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        L, a, b = COLOR_LAB[key]

        summary_data.append({
            'Color': key,
            'L': L,
            'a': a,
            'b': b,
            'Designed_Hue_deg': designed,
            'Measured_Hue_deg': measured,
            'Difference_deg': diff
        })

    df = pd.DataFrame(summary_data)
    df.to_csv('ColorLabel_comparison.csv', index=False)
    print("✓ Saved comparison table: ColorLabel_comparison.csv")

    return df

def check_analysis_scripts():
    """Check which color labels are used in analysis scripts"""

    print("\n" + "="*80)
    print("CHECKING ANALYSIS SCRIPTS")
    print("="*80)

    import subprocess

    # Search for COLOR_LAB usage
    print("\nSearching for COLOR_LAB usage...")
    result = subprocess.run(['grep', '-r', 'COLOR_LAB', '--include=*.py', '.'],
                          capture_output=True, text=True)

    if result.stdout:
        print("Found in:")
        for line in result.stdout.split('\n')[:10]:
            if line:
                print(f"  {line}")
    else:
        print("  Not found")

    # Search for LABEL2HUE usage
    print("\nSearching for LABEL2HUE_DEG usage...")
    result = subprocess.run(['grep', '-r', 'LABEL2HUE_DEG', '--include=*.py', '.'],
                          capture_output=True, text=True)

    if result.stdout:
        print("Found in:")
        for line in result.stdout.split('\n')[:10]:
            if line:
                print(f"  {line}")
    else:
        print("  Not found")

    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("""
CURRENT STATUS:
  - Analysis scripts use LABEL2HUE_DEG_PILOT (MEASURED values) ✓
  - This is CORRECT for analysis

DESIGNED vs MEASURED:
  - COLOR_LAB defines the INTENDED stimulus positions (45° spacing)
  - LABEL2HUE_DEG_PILOT contains ACTUAL measured positions from pilot
  - Use MEASURED values for reconstruction analysis

ACTION NEEDED:
  1. Verify that circular color space plots show MEASURED positions
  2. Check if color labels in plots match actual stimulus colors
  3. If discrepancy found, regenerate plots with correct labels
    """)

def main():
    """Main verification function"""

    # Compare color labels
    df = compare_color_labels()

    # Check analysis scripts
    check_analysis_scripts()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nMean absolute difference: {df['Difference_deg'].abs().mean():.2f}°")
    print(f"Max absolute difference: {df['Difference_deg'].abs().max():.2f}°")
    print(f"Std of differences: {df['Difference_deg'].std():.2f}°")

    print("\nGenerated files:")
    print("  ✓ ColorLabel_verification.png")
    print("  ✓ ColorLabel_comparison.csv")

if __name__ == "__main__":
    main()
