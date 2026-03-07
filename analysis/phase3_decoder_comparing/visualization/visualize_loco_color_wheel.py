#!/usr/bin/env python3
"""
LOCO Color Wheel Visualization

Visualizes true vs predicted hue angles on a color wheel for LOCO (Leave-One-Color-Out) results.
- True hues: Large dots on outer circle
- Predicted hues: Small dots on inner circle (angle = prediction, color = truth)

Shows both:
1. Per-run plots (each of 6 runs separately)
2. Average plot (all runs combined)

Uses utils_color_decoding.py for color wheel visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
import json
import sys

# Import color utilities directly (avoid nilearn dependency)
LABEL2HUE_DEG = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

COLOR_LAB = {
    'color_1': [59.90, 62.69, 3.78],
    'color_2': [64.20, 49.20, 45.58],
    'color_3': [57.27, 13.06, 41.69],
    'color_4': [69.08, -55.02, 47.38],
    'color_5': [74.61, -41.33, -4.89],
    'color_6': [69.14, -11.45, -40.91],
    'color_7': [60.68, 19.18, -54.13],
    'color_8': [60.17, 46.82, -40.31],
}

def circular_diff_deg(a, b):
    """Calculate circular difference in degrees (0-180)"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

def lab2rgb_accurate(L, a, b, clip=True):
    """CIELab to RGB conversion"""
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
    return tuple(rgb)

def get_stimulus_color_rgb(color_name):
    """Get RGB color for stimulus"""
    if color_name in COLOR_LAB:
        L, a, b = COLOR_LAB[color_name]
        return lab2rgb_accurate(L, a, b)
    else:
        return (0.5, 0.5, 0.5)

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = BASE_DIR / 'analysis' / 'phase3_decoder_comparing' / 'results' / 'loco'
OUTPUT_DIR = LOCO_DIR / 'color_wheel_plots'
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Subject groups
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'Deutan', '09': 'Protan', '10': 'Deutan'}

ROIS = ['V1', 'V2', 'V3', 'V4']
N_COLORS = 8


def create_color_wheel_plot(true_hues, pred_hues, title, output_path,
                             show_error_bars=False):
    """
    Create circular color wheel plot

    Args:
        true_hues: (n_colors,) array of true hue angles
        pred_hues: (n_colors,) or (n_runs, n_colors) array of predicted hue angles
        title: Plot title
        output_path: Path to save figure
        show_error_bars: If True and pred_hues is 2D, show error bars
    """
    fig = plt.figure(figsize=(12, 6))

    # Left: Color wheel
    ax1 = fig.add_subplot(1, 2, 1, projection='polar')
    ax1.set_theta_zero_location("E")  # 0° at right
    ax1.set_theta_direction(1)  # Anticlockwise
    ax1.set_rticks([])
    ax1.grid(alpha=0.25)

    r_true = 1.0  # Outer circle for true colors
    r_pred_base = 0.85  # Inner circle for predictions

    rng = np.random.default_rng(42)

    # Handle 1D (average) vs 2D (per-run) predictions
    if pred_hues.ndim == 1:
        # Average case: single prediction per color
        pred_hues_mean = pred_hues
        pred_hues_std = None
    else:
        # Per-run case: multiple predictions per color
        pred_hues_mean = np.mean(pred_hues, axis=0)
        pred_hues_std = np.std(pred_hues, axis=0) if show_error_bars else None

    # Plot each color
    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx + 1}'
        true_hue = true_hues[color_idx]
        true_rgb = get_stimulus_color_rgb(color_name)

        # True color at outer circle (large, solid)
        ax1.scatter([np.deg2rad(true_hue)], [r_true],
                   s=150, color=true_rgb, edgecolor='k',
                   linewidths=1.5, zorder=5, label='True' if color_idx == 0 else '')

        # Predictions at inner circle
        if pred_hues.ndim == 1:
            # Average: single dot
            pred_hue = pred_hues[color_idx]
            ax1.scatter([np.deg2rad(pred_hue)], [r_pred_base],
                       s=60, color=true_rgb, alpha=0.8,
                       edgecolor='k', linewidths=0.5, zorder=4,
                       label='Pred (avg)' if color_idx == 0 else '')
        else:
            # Per-run: multiple dots with jitter
            for run_idx in range(pred_hues.shape[0]):
                pred_hue = pred_hues[run_idx, color_idx]
                r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
                ax1.scatter([np.deg2rad(pred_hue)], [r_jit],
                           s=30, color=true_rgb, alpha=0.6,
                           zorder=3, label='Pred (runs)' if color_idx == 0 and run_idx == 0 else '')

        # Optional: Connect true to mean prediction
        if show_error_bars and pred_hues_std is not None:
            ax1.plot([np.deg2rad(true_hue), np.deg2rad(pred_hues_mean[color_idx])],
                    [r_true, r_pred_base],
                    color='gray', alpha=0.3, linewidth=0.8, zorder=2)

    ax1.set_ylim([0, 1.15])
    ax1.set_title('Color Wheel: True vs Predicted Hues',
                  fontsize=12, fontweight='bold', pad=20)

    # Add legend
    ax1.legend(loc='upper left', bbox_to_anchor=(1.15, 1.05),
              fontsize=10, frameon=True, facecolor='white', edgecolor='black')

    # Right: Statistics
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.axis('off')

    # Calculate errors
    if pred_hues.ndim == 1:
        errors = circular_diff_deg(pred_hues, true_hues)
    else:
        errors = circular_diff_deg(pred_hues_mean, true_hues)

    mean_error = np.mean(errors)

    # Summary text
    summary_text = f"""
LOCO Reconstruction Results

Overall Performance:
  Mean Error: {mean_error:.1f}°
  Chance Level: 90.0°

Per-Color Errors:
"""

    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx + 1}'
        error = errors[color_idx]
        summary_text += f"\n  {color_name}: {error:.1f}°"

    if pred_hues.ndim > 1:
        summary_text += f"\n\nNumber of runs: {pred_hues.shape[0]}"

    ax2.text(0.1, 0.5, summary_text,
            transform=ax2.transAxes,
            fontsize=10, verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path.name}")


def visualize_loco_subject(subject_id, roi, model='ForwardEncoding'):
    """
    Visualize LOCO results for one subject-ROI combination

    Creates:
    1. Per-run plots (6 individual plots)
    2. Average plot (all runs combined)

    Args:
        subject_id: Subject ID (e.g., '01', '08')
        roi: ROI name ('V1', 'V2', 'V3', 'V4')
        model: Model name (default: 'ForwardEncoding')
    """
    # Load LOCO results
    loco_file = LOCO_DIR / f'sub-{subject_id}_loco.json'
    if not loco_file.exists():
        print(f"  ✗ LOCO file not found: {loco_file}")
        return

    with open(loco_file, 'r') as f:
        data = json.load(f)

    if roi not in data['results']:
        print(f"  ✗ ROI {roi} not found in results")
        return

    if model not in data['results'][roi]:
        print(f"  ✗ Model {model} not found for {roi}")
        return

    fold_results = data['results'][roi][model]['fold_results']

    # Extract data
    n_folds = len(fold_results)  # Should be 8 (one per color)
    true_hues = np.zeros(N_COLORS)
    pred_hues_all = []  # Will be list of (n_runs,) arrays

    for fold in fold_results:
        # test_color is already an integer (0-7)
        test_color_idx = int(fold['test_color'])
        true_hues[test_color_idx] = fold['test_hue']
        pred_hues_all.append(fold['pred_hues'])  # List of predictions per run

    # Convert to numpy array: (n_folds=8, n_runs=6) then transpose to (n_runs=6, n_colors=8)
    pred_hues_array = np.array(pred_hues_all).T  # Now (6, 8)
    n_runs = pred_hues_array.shape[0]

    # Create output directory for this subject-ROI
    subject_dir = OUTPUT_DIR / f'sub-{subject_id}' / roi
    subject_dir.mkdir(exist_ok=True, parents=True)

    print(f"\n  Processing sub-{subject_id} {roi} ({model})...")

    # 1. Per-run plots
    for run_idx in range(n_runs):
        pred_hues_run = pred_hues_array[run_idx, :]  # (8,) - one run's predictions for all colors

        title = f'sub-{subject_id} {roi} | Run {run_idx + 1}/{n_runs} | {model}'
        output_path = subject_dir / f'run_{run_idx + 1:02d}.png'

        create_color_wheel_plot(
            true_hues=true_hues,
            pred_hues=pred_hues_run,
            title=title,
            output_path=output_path,
            show_error_bars=False
        )

    # 2. Average plot (all runs combined)
    title = f'sub-{subject_id} {roi} | Average across {n_runs} runs | {model}'
    output_path = subject_dir / 'average_all_runs.png'

    # Pass 2D array to show all predictions
    create_color_wheel_plot(
        true_hues=true_hues,
        pred_hues=pred_hues_array,  # (8, 6) - shows all dots
        title=title,
        output_path=output_path,
        show_error_bars=True
    )

    # 3. Summary statistics
    pred_hues_mean = np.mean(pred_hues_array, axis=0)  # Average across runs -> (8,)
    errors = circular_diff_deg(pred_hues_mean, true_hues)
    mean_error = np.mean(errors)

    print(f"    Mean error: {mean_error:.1f}°")


def visualize_group_comparison(roi, model='ForwardEncoding'):
    """
    Create group comparison figure (HC vs CVD) for one ROI

    Args:
        roi: ROI name
        model: Model name
    """
    print(f"\n  Creating group comparison for {roi}...")

    # Collect data
    hc_errors = []
    cvd_errors = {}

    for subject_id in HC_SUBJECTS + CVD_SUBJECTS:
        loco_file = LOCO_DIR / f'sub-{subject_id}_loco.json'
        if not loco_file.exists():
            continue

        with open(loco_file, 'r') as f:
            data = json.load(f)

        if roi not in data['results'] or model not in data['results'][roi]:
            continue

        fold_results = data['results'][roi][model]['fold_results']

        # Extract predictions
        true_hues = np.zeros(N_COLORS)
        pred_hues_all = []

        for fold in fold_results:
            # test_color is already an integer (0-7)
            test_color_idx = int(fold['test_color'])
            true_hues[test_color_idx] = fold['test_hue']
            pred_hues_all.append(fold['pred_hues'])

        pred_hues_array = np.array(pred_hues_all).T  # (n_runs, n_colors)
        pred_hues_mean = np.mean(pred_hues_array, axis=0)  # Average across runs
        errors = circular_diff_deg(pred_hues_mean, true_hues)
        mean_error = np.mean(errors)

        if subject_id in HC_SUBJECTS:
            hc_errors.append(mean_error)
        else:
            cvd_errors[subject_id] = mean_error

    # Create comparison plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # HC box
    bp = ax.boxplot([hc_errors], positions=[1], widths=0.6,
                     patch_artist=True, labels=['HC'])
    bp['boxes'][0].set_facecolor('steelblue')
    bp['boxes'][0].set_alpha(0.6)

    # Individual HC points
    for i, err in enumerate(hc_errors):
        ax.scatter([1 + np.random.normal(0, 0.05)], [err],
                  c='steelblue', s=60, alpha=0.8, zorder=3)

    # CVD individual points
    cvd_colors = {'08': '#FF6B6B', '09': '#FFA07A', '10': '#FFB6C1'}
    for idx, (cvd_id, err) in enumerate(cvd_errors.items()):
        x_pos = 2 + idx * 0.3
        ax.scatter([x_pos], [err], c=cvd_colors[cvd_id],
                  s=100, marker='D', edgecolor='black', linewidth=1.5,
                  label=f'sub-{cvd_id} ({CVD_TYPES[cvd_id]})', zorder=4)

    # Formatting
    ax.axhline(90, color='gray', linestyle='--', linewidth=1,
              alpha=0.5, label='Chance (90°)')
    ax.set_ylabel('Mean Absolute Error (degrees)', fontsize=12, fontweight='bold')
    ax.set_title(f'{roi} LOCO Performance: HC vs CVD ({model})',
                fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.set_xlim([0.5, 3.5])
    ax.set_xticks([1, 2.15])
    ax.set_xticklabels(['HC (n=7)', 'CVD'], fontsize=11)

    # Save
    output_path = OUTPUT_DIR / f'group_comparison_{roi}.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path.name}")
    print(f"    HC: {np.mean(hc_errors):.1f}° ± {np.std(hc_errors):.1f}°")
    print(f"    CVD: {', '.join([f'{v:.1f}°' for v in cvd_errors.values()])}")


def main():
    """Main execution"""

    print("=" * 80)
    print("LOCO Color Wheel Visualization")
    print("=" * 80)
    print(f"Input directory: {LOCO_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")

    model = 'ForwardEncoding'

    # Visualize all subjects
    all_subjects = HC_SUBJECTS + CVD_SUBJECTS

    for roi in ROIS:
        print(f"\n{'='*60}")
        print(f"ROI: {roi}")
        print(f"{'='*60}")

        for subject_id in all_subjects:
            visualize_loco_subject(subject_id, roi, model)

        # Group comparison
        visualize_group_comparison(roi, model)

    print("\n" + "=" * 80)
    print("✓ Color wheel visualization complete!")
    print(f"  Total subjects: {len(all_subjects)}")
    print(f"  Per subject: {6} run plots + 1 average plot")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == '__main__':
    main()
