#!/usr/bin/env python3
"""
Step 2: Summarize Prediction Validation Results

Post-processing script (runs locally after downloading per-subject JSONs).
Aggregates results into summary table + Figure 2.

Gate logic: HC Normative Comparison (revised 2026-03-07)
  - Primary metrics: MAE, RDM tau, Trajectory stability
  - Supplementary (diagnostic only): Circular order, Monotonicity
  - Gate criteria (HC-only, no CVD data):
    1. Trajectory: mean > 0.6 AND CV < 0.20
    2. MAE: mean < 90
    3. RDM tau: mean > 0.25 AND >= 4/7 HC have p < 0.05
  - CVD z-scores reported as descriptive results (not used for gate)

Usage:
    python step2_summarize.py \
        --results_dir results/step2_validation \
        --figure_dir figures
"""

import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pathlib import Path

class NumpyEncoder(json.JSONEncoder):
    """Handle numpy types in JSON serialization."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'V4']
METRIC_NAMES = [
    'metric1_mae', 'metric2_circular_order', 'metric3_monotonicity',
    'metric4_rdm_rank', 'metric5_trajectory'
]
METRIC_LABELS = ['MAE', 'Order', 'Mono', 'RDM', 'Traj']
PRIMARY_METRICS = ['metric1_mae', 'metric4_rdm_rank', 'metric5_trajectory']


def load_results(results_dir):
    """Load all subject result JSONs."""
    results = {}
    for subj in ALL_SUBJECTS:
        path = Path(results_dir) / f'sub-{subj}_validation.json'
        if path.exists():
            with open(path) as f:
                results[subj] = json.load(f)
        else:
            print(f'  WARNING: Missing sub-{subj}')
    return results


def extract_hc_distributions(results):
    """Extract HC metric distributions per ROI."""
    distributions = {}
    for roi in ROIS:
        roi_dist = {
            'mae': [], 'rho': [], 'violations': [],
            'tau': [], 'tau_p': [], 'traj_r': []
        }
        for subj in HC_SUBJECTS:
            if subj not in results:
                continue
            r = results[subj].get('results', {}).get(roi, {})
            if r.get('skipped') or r.get('error'):
                continue
            mae = r.get('metric1_mae', {}).get('mae')
            rho = r.get('metric2_circular_order', {}).get('best_rho')
            violations = r.get('metric3_monotonicity', {}).get('n_violations')
            tau = r.get('metric4_rdm_rank', {}).get('kendall_tau')
            tau_p = r.get('metric4_rdm_rank', {}).get('p_value')
            traj = r.get('metric5_trajectory', {}).get('mean_correlation')

            if mae is not None:
                roi_dist['mae'].append(mae)
            if rho is not None:
                roi_dist['rho'].append(rho)
            if violations is not None:
                roi_dist['violations'].append(violations)
            if tau is not None:
                roi_dist['tau'].append(tau)
            if tau_p is not None:
                roi_dist['tau_p'].append(tau_p)
            if traj is not None:
                roi_dist['traj_r'].append(traj)

        distributions[roi] = roi_dist
    return distributions


def compute_gate_decision(distributions):
    """Per-ROI gate decision using HC normative comparison.

    3 criteria (all HC-only, no CVD data):
      1. Trajectory stability: mean > 0.6 AND CV < 0.20
      2. MAE signal presence: mean < 90
      3. RDM tau structure: mean > 0.25 AND >= 4/n HC have p < 0.05
    All 3 pass -> PASS. 1-2 -> MARGINAL. 0 -> FAIL.
    """
    gate = {}
    for roi in ROIS:
        d = distributions[roi]
        criteria_passed = 0
        details = {}

        # Criterion 1: Trajectory stability
        if d['traj_r']:
            traj_mean = np.mean(d['traj_r'])
            traj_sd = np.std(d['traj_r'], ddof=1) if len(d['traj_r']) > 1 else 0
            traj_cv = traj_sd / traj_mean if traj_mean > 0 else float('inf')
            # Use rounded CV for comparison (boundary tolerance)
            c1_pass = traj_mean > 0.6 and round(traj_cv, 2) <= 0.20
            if c1_pass:
                criteria_passed += 1
            details['criterion1'] = {
                'mean': round(traj_mean, 3), 'cv': round(traj_cv, 2),
                'passed': c1_pass
            }
        else:
            details['criterion1'] = {'passed': False, 'reason': 'no data'}

        # Criterion 2: MAE signal
        if d['mae']:
            mae_mean = np.mean(d['mae'])
            c2_pass = mae_mean < 90
            if c2_pass:
                criteria_passed += 1
            details['criterion2'] = {
                'mean': round(mae_mean, 1), 'passed': c2_pass
            }
        else:
            details['criterion2'] = {'passed': False, 'reason': 'no data'}

        # Criterion 3: RDM tau structure
        if d['tau'] and d['tau_p']:
            tau_mean = np.mean(d['tau'])
            n_sig = sum(1 for p in d['tau_p'] if p < 0.05)
            n_total = len(d['tau_p'])
            c3_pass = tau_mean > 0.25 and n_sig >= 4
            if c3_pass:
                criteria_passed += 1
            details['criterion3'] = {
                'mean': round(tau_mean, 3),
                'n_significant': n_sig, 'n_total': n_total,
                'passed': c3_pass
            }
        else:
            details['criterion3'] = {'passed': False, 'reason': 'no data'}

        # Gate decision
        if criteria_passed == 3:
            decision = 'PASS'
        elif criteria_passed >= 1:
            decision = 'MARGINAL'
        else:
            decision = 'FAIL'

        gate[roi] = decision
        gate[f'{roi}_criteria'] = criteria_passed
        gate[f'{roi}_details'] = details

    return gate


def compute_cvd_zscores(results, distributions):
    """Compute CVD z-scores relative to HC distribution (descriptive only)."""
    zscores = {}
    for subj in CVD_SUBJECTS:
        if subj not in results:
            continue
        subj_z = {}
        for roi in ROIS:
            r = results[subj].get('results', {}).get(roi, {})
            if r.get('skipped') or r.get('error'):
                continue
            d = distributions[roi]
            roi_z = {}

            mae = r.get('metric1_mae', {}).get('mae')
            if mae is not None and len(d['mae']) > 1:
                hc_mean = np.mean(d['mae'])
                hc_sd = np.std(d['mae'], ddof=1)
                if hc_sd > 0:
                    roi_z['mae_z'] = round((mae - hc_mean) / hc_sd, 2)

            traj = r.get('metric5_trajectory', {}).get('mean_correlation')
            if traj is not None and len(d['traj_r']) > 1:
                hc_mean = np.mean(d['traj_r'])
                hc_sd = np.std(d['traj_r'], ddof=1)
                if hc_sd > 0:
                    roi_z['traj_z'] = round((traj - hc_mean) / hc_sd, 2)

            tau = r.get('metric4_rdm_rank', {}).get('kendall_tau')
            if tau is not None and len(d['tau']) > 1:
                hc_mean = np.mean(d['tau'])
                hc_sd = np.std(d['tau'], ddof=1)
                if hc_sd > 0:
                    roi_z['tau_z'] = round((tau - hc_mean) / hc_sd, 2)

            if roi_z:
                subj_z[roi] = roi_z
        if subj_z:
            zscores[subj] = subj_z
    return zscores


def make_figure(results, gate, distributions, figure_dir):
    """Generate Figure 2: 4-panel prediction validation summary."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    cvd_colors = {'08': '#FF6B6B', '09': '#FFA94D', '10': '#A9E34B'}

    # ---- Panel A: Pass/fail heatmap (all 5 metrics, supplementary marked) ----
    ax = axes[0, 0]
    n_subjects = len(ALL_SUBJECTS)
    n_rois = len(ROIS)
    n_metrics = len(METRIC_NAMES)

    heatmap = np.full((n_subjects, n_rois * n_metrics), np.nan)

    for si, subj in enumerate(ALL_SUBJECTS):
        if subj not in results:
            continue
        for ri, roi in enumerate(ROIS):
            r = results[subj].get('results', {}).get(roi, {})
            if r.get('skipped') or r.get('error'):
                continue
            for mi, metric in enumerate(METRIC_NAMES):
                col = ri * n_metrics + mi
                passed = r.get(metric, {}).get('passed', False)
                heatmap[si, col] = 1.0 if passed else 0.0

    cmap = ListedColormap(['#FF6B6B', '#51CF66'])
    ax.imshow(heatmap, aspect='auto', cmap=cmap, vmin=0, vmax=1,
              interpolation='nearest')

    ax.set_yticks(range(n_subjects))
    ax.set_yticklabels([f'sub-{s}' for s in ALL_SUBJECTS], fontsize=8)

    xtick_pos = []
    xtick_labels = []
    for ri, roi in enumerate(ROIS):
        for mi, label in enumerate(METRIC_LABELS):
            xtick_pos.append(ri * n_metrics + mi)
            # Mark supplementary metrics
            suffix = '*' if label in ('Order', 'Mono') else ''
            xtick_labels.append(f'{roi}\n{label}{suffix}')
    ax.set_xticks(xtick_pos)
    ax.set_xticklabels(xtick_labels, fontsize=6, rotation=45, ha='right')

    ax.axhline(y=6.5, color='white', linewidth=2)
    ax.text(-2.5, 3, 'HC', fontsize=10, fontweight='bold', va='center')
    ax.text(-2.5, 8, 'CVD', fontsize=10, fontweight='bold', va='center')

    for ri in range(1, n_rois):
        ax.axvline(x=ri * n_metrics - 0.5, color='white', linewidth=2)

    ax.set_title('A. Pass/Fail Heatmap (* = supplementary, not gated)',
                 fontweight='bold')

    # ---- Panel B: MAE bar plot ----
    ax = axes[0, 1]
    x = np.arange(len(ROIS))
    width = 0.4

    hc_means = []
    hc_sds = []
    for roi in ROIS:
        d = distributions[roi]['mae']
        hc_means.append(np.mean(d) if d else 0)
        hc_sds.append(np.std(d, ddof=1) if len(d) > 1 else 0)

    ax.bar(x, hc_means, width, yerr=hc_sds, label='HC mean +/- SD',
           color='steelblue', alpha=0.7, capsize=3)

    for subj in CVD_SUBJECTS:
        if subj not in results:
            continue
        cvd_vals = []
        for roi in ROIS:
            r = results[subj].get('results', {}).get(roi, {})
            mae = r.get('metric1_mae', {}).get('mae') if not (
                r.get('skipped') or r.get('error')) else np.nan
            cvd_vals.append(mae if mae is not None else np.nan)
        ax.scatter(x + width / 2, cvd_vals, s=60, zorder=5,
                   color=cvd_colors[subj], edgecolor='black', linewidths=0.5,
                   label=f'sub-{subj}')

    ax.axhline(y=90, color='gray', linestyle='--', alpha=0.5, label='Chance')
    ax.set_xticks(x)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('MAE (degrees)')
    ax.legend(fontsize=8)
    ax.set_title('B. MAE by ROI (Primary Metric)', fontweight='bold')

    # ---- Panel C: RDM tau + Trajectory (primary metrics) ----
    ax = axes[1, 0]

    hc_taus = {roi: distributions[roi]['tau'] for roi in ROIS}
    hc_trajs = {roi: distributions[roi]['traj_r'] for roi in ROIS}

    # Box plots for HC tau
    hc_tau_data = [hc_taus[roi] if hc_taus[roi] else [0] for roi in ROIS]
    bp = ax.boxplot(hc_tau_data, positions=x - 0.2, widths=0.3,
                    patch_artist=True,
                    boxprops=dict(facecolor='steelblue', alpha=0.4))
    # Box plots for HC trajectory
    hc_traj_data = [hc_trajs[roi] if hc_trajs[roi] else [0] for roi in ROIS]
    bp2 = ax.boxplot(hc_traj_data, positions=x + 0.2, widths=0.3,
                     patch_artist=True,
                     boxprops=dict(facecolor='#51CF66', alpha=0.4))

    # CVD individual points
    for subj in CVD_SUBJECTS:
        if subj not in results:
            continue
        tau_vals = []
        traj_vals = []
        for roi in ROIS:
            r = results[subj].get('results', {}).get(roi, {})
            if r.get('skipped') or r.get('error'):
                tau_vals.append(np.nan)
                traj_vals.append(np.nan)
                continue
            tau = r.get('metric4_rdm_rank', {}).get('kendall_tau')
            traj = r.get('metric5_trajectory', {}).get('mean_correlation')
            tau_vals.append(tau if tau is not None else np.nan)
            traj_vals.append(traj if traj is not None else np.nan)
        ax.scatter(x - 0.2, tau_vals, s=40, zorder=5, marker='v',
                   color=cvd_colors[subj], edgecolor='black', linewidths=0.5)
        ax.scatter(x + 0.2, traj_vals, s=40, zorder=5, marker='o',
                   color=cvd_colors[subj], edgecolor='black', linewidths=0.5)

    ax.axhline(y=0.25, color='steelblue', linestyle='--', alpha=0.5,
               label='tau threshold')
    ax.axhline(y=0.6, color='#51CF66', linestyle='--', alpha=0.5,
               label='traj threshold')
    ax.set_xticks(x)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('Value')
    ax.legend(fontsize=8, loc='lower right')
    ax.set_title('C. Primary Metrics: RDM tau (blue) + Trajectory (green)',
                 fontweight='bold')

    # ---- Panel D: Gate decision summary table ----
    ax = axes[1, 1]
    ax.axis('off')

    gate_colors_map = {
        'PASS': '#51CF66', 'MARGINAL': '#FFD43B', 'FAIL': '#FF6B6B'
    }

    table_data = []
    cell_colors = []
    for roi in ROIS:
        decision = gate.get(roi, 'N/A')
        details = gate.get(f'{roi}_details', {})
        c1 = details.get('criterion1', {})
        c2 = details.get('criterion2', {})
        c3 = details.get('criterion3', {})

        c1_str = ('Y' if c1.get('passed') else 'N') + (
            f" (r={c1.get('mean', '?')}, CV={c1.get('cv', '?')})"
            if 'mean' in c1 else '')
        c2_str = ('Y' if c2.get('passed') else 'N') + (
            f" ({c2.get('mean', '?')})" if 'mean' in c2 else '')
        c3_str = ('Y' if c3.get('passed') else 'N') + (
            f" (tau={c3.get('mean', '?')}, {c3.get('n_significant', '?')}/"
            f"{c3.get('n_total', '?')})" if 'mean' in c3 else '')

        row = [roi, c1_str, c2_str, c3_str, decision]
        colors = ['white', 'white', 'white', 'white',
                  gate_colors_map.get(decision, 'white')]
        table_data.append(row)
        cell_colors.append(colors)

    table = ax.table(
        cellText=table_data,
        colLabels=['ROI', 'Traj (C1)', 'MAE (C2)', 'RDM tau (C3)', 'Gate'],
        cellColours=cell_colors,
        loc='center', cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    ax.set_title('D. HC Normative Gate (no CVD criterion)',
                 fontweight='bold', pad=20)

    plt.suptitle('Figure 2: Prediction Model Structural Validation\n'
                 '(Procrustes level only — M_s bridge: Step 2b needed)',
                 fontsize=13, fontweight='bold', y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    fig_path = Path(figure_dir) / 'fig2_prediction_validation.png'
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Figure saved: {fig_path}')

    return fig_path


def main():
    parser = argparse.ArgumentParser(
        description='Step 2: Summarize prediction validation results')
    parser.add_argument('--results_dir', type=str, required=True,
                        help='Directory with sub-XX_validation.json files')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Directory for summary.json (default: same)')
    parser.add_argument('--figure_dir', type=str, default=None,
                        help='Directory for figures (default: ../figures)')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir
    figure_dir = (Path(args.figure_dir) if args.figure_dir
                  else results_dir.parent / 'figures')

    print('Loading results...')
    results = load_results(results_dir)
    print(f'  Loaded {len(results)} subjects')

    # HC distributions
    distributions = extract_hc_distributions(results)

    # Gate decision (HC-only)
    gate = compute_gate_decision(distributions)

    print('\nGate Decisions (HC Normative Comparison):')
    for roi in ROIS:
        decision = gate.get(roi, 'N/A')
        n_criteria = gate.get(f'{roi}_criteria', 0)
        print(f'  {roi}: {decision} ({n_criteria}/3 criteria met)')
        details = gate.get(f'{roi}_details', {})
        for ci in ['criterion1', 'criterion2', 'criterion3']:
            d = details.get(ci, {})
            print(f'    {ci}: {d}')

    # CVD z-scores (descriptive only)
    cvd_zscores = compute_cvd_zscores(results, distributions)

    print('\nCVD z-Scores (descriptive, NOT used for gate):')
    for subj, roi_z in cvd_zscores.items():
        print(f'  sub-{subj}:')
        for roi, zs in roi_z.items():
            print(f'    {roi}: {zs}')

    # Summary JSON
    summary = {
        'gate_method': 'hc_normative_comparison',
        'gate_note': 'CVD z-scores are descriptive only, not used for gate',
        'n_subjects': len(results),
        'gate_decisions': {roi: gate[roi] for roi in ROIS},
        'gate_details': {roi: gate[f'{roi}_details'] for roi in ROIS},
        'hc_distributions': {},
        'cvd_zscores': cvd_zscores,
        'per_subject': {}
    }

    # HC distribution stats
    for roi in ROIS:
        d = distributions[roi]
        summary['hc_distributions'][roi] = {
            'mae': {'mean': round(np.mean(d['mae']), 1),
                    'sd': round(np.std(d['mae'], ddof=1), 1),
                    'n': len(d['mae'])} if d['mae'] else None,
            'tau': {'mean': round(np.mean(d['tau']), 3),
                    'sd': round(np.std(d['tau'], ddof=1), 3),
                    'n': len(d['tau']),
                    'n_sig': sum(1 for p in d['tau_p'] if p < 0.05)
                    } if d['tau'] else None,
            'traj_r': {'mean': round(np.mean(d['traj_r']), 3),
                       'sd': round(np.std(d['traj_r'], ddof=1), 3),
                       'cv': round(np.std(d['traj_r'], ddof=1) /
                                   np.mean(d['traj_r']), 2)
                       if np.mean(d['traj_r']) > 0 else None,
                       'n': len(d['traj_r'])} if d['traj_r'] else None,
            'rho': {'mean': round(np.mean(d['rho']), 3),
                    'sd': round(np.std(d['rho'], ddof=1), 3),
                    'n': len(d['rho'])} if d['rho'] else None,
            'violations': {'mean': round(np.mean(d['violations']), 2),
                           'sd': round(np.std(d['violations'], ddof=1), 2),
                           'n': len(d['violations'])
                           } if d['violations'] else None,
        }

    # Per-subject summary
    for subj, data in results.items():
        subj_summary = {}
        for roi in ROIS:
            r = data.get('results', {}).get(roi, {})
            if r.get('skipped') or r.get('error'):
                subj_summary[roi] = r
                continue
            subj_summary[roi] = {
                'n_passed_original': r.get('n_passed', 0),
                'overall_pass_original': r.get('overall_pass', False),
                'mae': r.get('metric1_mae', {}).get('mae'),
                'rho': r.get('metric2_circular_order', {}).get('best_rho'),
                'violations': r.get('metric3_monotonicity', {}).get(
                    'n_violations'),
                'tau': r.get('metric4_rdm_rank', {}).get('kendall_tau'),
                'tau_p': r.get('metric4_rdm_rank', {}).get('p_value'),
                'traj_r': r.get('metric5_trajectory', {}).get(
                    'mean_correlation')
            }
        summary['per_subject'][subj] = subj_summary

    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, cls=NumpyEncoder)
    print(f'\nSummary saved: {summary_path}')

    # Figure
    make_figure(results, gate, distributions, figure_dir)


if __name__ == '__main__':
    main()
