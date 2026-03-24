#!/usr/bin/env python3
"""
Per-Color LOCO Analysis with HC CI and Confusion Pattern

Generates integration table with:
- HC mean [95% CI] per color
- CVD value and whether it falls outside HC CI
- Confusion direction (which color region is predicted?)
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

# Paths
VALIDATION_DIR = Path(__file__).parents[2] / "future_phase1_forward_model" / "results" / "validation"

# Color mapping
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
COLOR_HUES = [0, 45, 90, 135, 180, 225, 270, 315]

HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = {
    '08': 'deutan',
    '09': 'protan',
    '10': 'normal'
}

def load_loco_data(subject, roi='hV4', model='ridge_gcv'):
    """Load LOCO results for a subject"""
    file_path = VALIDATION_DIR / f"sub-{subject}_loco.json"

    if not file_path.exists():
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    return data.get(roi, {}).get(model, {})

def calculate_confusion_direction(pred_hues, true_hue):
    """
    Calculate the most common predicted hue region

    Returns:
    - median_pred: median predicted hue
    - nearest_color: nearest color name to median prediction
    - angular_error: median angular error
    """
    pred_hues = np.array(pred_hues)

    # Calculate circular median
    angles_rad = np.deg2rad(pred_hues)
    sin_mean = np.mean(np.sin(angles_rad))
    cos_mean = np.mean(np.cos(angles_rad))
    median_pred = np.rad2deg(np.arctan2(sin_mean, cos_mean)) % 360

    # Calculate angular error
    errors = np.abs(pred_hues - true_hue)
    errors = np.minimum(errors, 360 - errors)  # Circular distance
    median_error = np.median(errors)

    # Find nearest color to median prediction
    hue_diffs = np.abs(np.array(COLOR_HUES) - median_pred)
    hue_diffs = np.minimum(hue_diffs, 360 - hue_diffs)
    nearest_idx = np.argmin(hue_diffs)
    nearest_color = COLOR_NAMES[nearest_idx]

    return median_pred, nearest_color, median_error

def analyze_per_color_loco(roi='V4', model='ridge_gcv'):
    """
    Analyze per-color LOCO performance

    Returns dictionary with:
    - hc_stats: HC mean, std, CI per color
    - cvd_stats: CVD value, outside_ci, confusion per color per subject
    """
    # Load HC data
    hc_data = []
    for sub in HC_SUBJECTS:
        data = load_loco_data(sub, roi, model)
        if data and 'folds' in data:
            hc_data.append(data)

    # Calculate HC statistics per color
    hc_stats = {}
    for color_idx, color_name in enumerate(COLOR_NAMES):
        color_scores = []
        for sub_data in hc_data:
            fold = sub_data['folds'][color_idx]
            color_scores.append(fold['voxel_corr'])

        color_scores = np.array(color_scores)
        mean = np.mean(color_scores)
        std = np.std(color_scores, ddof=1)
        n = len(color_scores)

        # Bootstrap 95% CI
        n_bootstrap = 10000
        bootstrap_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(color_scores, size=n, replace=True)
            bootstrap_means.append(np.mean(sample))

        ci_lower, ci_upper = np.percentile(bootstrap_means, [2.5, 97.5])

        hc_stats[color_name] = {
            'mean': mean,
            'std': std,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'values': color_scores
        }

    # Analyze CVD subjects
    cvd_stats = {}
    for sub, cvd_type in CVD_SUBJECTS.items():
        cvd_data = load_loco_data(sub, roi, model)
        if not cvd_data or 'folds' not in cvd_data:
            continue

        cvd_stats[sub] = {
            'cvd_type': cvd_type,
            'colors': {}
        }

        for color_idx, color_name in enumerate(COLOR_NAMES):
            fold = cvd_data['folds'][color_idx]
            cvd_value = fold['voxel_corr']
            pred_hues = fold['pred_hues']
            true_hue = COLOR_HUES[color_idx]

            # Check if outside HC CI
            hc = hc_stats[color_name]
            outside_ci = cvd_value < hc['ci_lower'] or cvd_value > hc['ci_upper']

            # Calculate confusion
            median_pred, nearest_color, median_error = calculate_confusion_direction(
                pred_hues, true_hue
            )

            # Crawford-Howell test
            t_stat, p_value = crawford_howell_test(
                cvd_value, hc['values']
            )

            cvd_stats[sub]['colors'][color_name] = {
                'value': cvd_value,
                'outside_ci': outside_ci,
                'median_pred': median_pred,
                'nearest_color': nearest_color,
                'median_error': median_error,
                't': t_stat,
                'p': p_value
            }

    return hc_stats, cvd_stats

def crawford_howell_test(case_score, control_scores):
    """
    Crawford-Howell modified t-test for single case vs controls

    Parameters:
    - case_score: single value for the case
    - control_scores: array of control values

    Returns:
    - t: t-statistic
    - p: two-tailed p-value
    """
    controls = np.array(control_scores)
    n = len(controls)

    mean_c = np.mean(controls)
    std_c = np.std(controls, ddof=1)

    # Modified t-statistic
    t = (case_score - mean_c) / (std_c * np.sqrt((n + 1) / n))

    # Two-tailed p-value with df = n - 1
    p = 2 * (1 - stats.t.cdf(np.abs(t), df=n - 1))

    return t, p

def print_integration_table(hc_stats, cvd_stats, subject='08', roi='hV4'):
    """Print integration table for a specific CVD subject"""

    sub_data = cvd_stats.get(subject)
    if not sub_data:
        print(f"No data for sub-{subject}")
        return

    cvd_type = sub_data['cvd_type']

    print(f"\n## Sub-{subject} ({cvd_type.capitalize()}) — {roi} Per-Color LOCO Analysis")
    print()
    print("| Color | HC Mean [95% CI] | CVD Value | Outside CI | Confusion → | Median Error (°) | Crawford p |")
    print("|-------|:----------------:|:---------:|:----------:|:-----------:|:----------------:|:----------:|")

    for color_name in COLOR_NAMES:
        hc = hc_stats[color_name]
        cvd = sub_data['colors'][color_name]

        # Format values
        hc_mean_ci = f"{hc['mean']:+.3f} [{hc['ci_lower']:+.3f}, {hc['ci_upper']:+.3f}]"
        cvd_val = f"{cvd['value']:+.3f}"
        outside = "✓" if cvd['outside_ci'] else "—"

        # Confusion direction
        if cvd['nearest_color'] == color_name:
            confusion = "—"  # Correctly predicted region
        else:
            confusion = f"{cvd['nearest_color']} ({cvd['median_pred']:.0f}°)"

        error = f"{cvd['median_error']:.0f}"

        # Crawford p-value
        p = cvd['p']
        if p < 0.001:
            p_str = "**<0.001***"
        elif p < 0.01:
            p_str = f"**{p:.3f}***"
        elif p < 0.05:
            p_str = f"**{p:.3f}***"
        else:
            p_str = f"{p:.3f}"

        print(f"| {color_name:7s} | {hc_mean_ci:40s} | {cvd_val:9s} | {outside:10s} | {confusion:11s} | {error:16s} | {p_str:10s} |")

    print()
    print("> **Outside CI**: CVD value falls outside HC 95% bootstrap confidence interval")
    print("> **Confusion**: Median predicted hue (if different from true color region)")
    print("> **Crawford p**: Modified t-test (df=6) for single case vs HC group")

if __name__ == '__main__':
    print("="*80)
    print("Per-Color LOCO Analysis with HC CI and Confusion Pattern")
    print("="*80)

    # Analyze V4 ridge_gcv (primary model)
    hc_stats, cvd_stats = analyze_per_color_loco(roi='V4', model='ridge_gcv')

    # Print tables for each CVD subject
    for subject in ['08', '09', '10']:
        print_integration_table(hc_stats, cvd_stats, subject=subject, roi='V4')

    print("\n" + "="*80)
    print("Analysis Complete")
    print("="*80)
