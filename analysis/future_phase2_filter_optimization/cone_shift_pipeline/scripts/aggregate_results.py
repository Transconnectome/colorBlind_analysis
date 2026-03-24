#!/usr/bin/env python3
"""
aggregate_results.py — Aggregate Geometry→Function simulation results.

Collects all `config.json` and `result.json` pairs produced by `run_sim.py`,
builds flat per-combination tables, reports missing jobs from the 48-condition
grid, and ranks model/metric conditions by behavioral LOCO fit.

Usage:
    python scripts/aggregate_results.py
    python scripts/aggregate_results.py \
        --results_dir ../results/sim \
        --output_dir ../results/sim_aggregate
"""

import argparse
import csv
import json
import math
from itertools import product
from pathlib import Path

import numpy as np


DEFAULT_SUBJECTS = ['08', '09']
DEFAULT_ROIS = ['V1', 'V2']
DEFAULT_MODELS = ['cone_1way', 'cone_3way', 'fourier']
DEFAULT_METRICS = ['corr', 'cosine', 'triangle', 'combination']


def load_json(path):
    with open(path) as f:
        return json.load(f)


def safe_float(value):
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def safe_mean(values):
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if not vals:
        return None
    return float(np.mean(vals))


def safe_int_mean(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(np.mean(vals))


def maybe_round(value, digits=4):
    if value is None:
        return None
    return round(float(value), digits)


def expected_combinations(subjects, rois, models, metrics):
    combos = []
    for sub, roi, model, metric in product(subjects, rois, models, metrics):
        combos.append({
            'subject': f'sub-{sub}',
            'roi': roi,
            'model': model,
            'metric': metric,
            'combo_name': f'sub-{sub}_{roi}_{model}_{metric}',
        })
    return combos


def collect_result_dirs(results_dir):
    config_paths = sorted(results_dir.rglob('config.json'))
    pairs = []
    for config_path in config_paths:
        result_path = config_path.with_name('result.json')
        if result_path.exists():
            pairs.append((config_path, result_path))
    return pairs


def flatten_result(config, result, source_dir):
    phase_a = result.get('phase_a', {})
    phase_b = result.get('phase_b', {})
    phase_c = result.get('phase_c', {})
    loco_match = phase_c.get('loco_match', {}) or {}
    per_hc_match = (((phase_c.get('per_hc') or {}).get('loco_match')) or {})
    mean_w_match = (((phase_c.get('mean_w') or {}).get('loco_match')) or {})

    row = {
        'combo_name': source_dir.name,
        'source_dir': str(source_dir),
        'subject': config.get('subject'),
        'cvd_type': config.get('cvd_type'),
        'roi': config.get('roi'),
        'model': config.get('model'),
        'metric': config.get('metric'),
        'model_df': config.get('model_df'),
        'n_hc': config.get('n_hc'),
        'n_voxels': config.get('n_voxels'),
        'n_channels': config.get('n_channels'),
        'elapsed_sec': config.get('elapsed_sec'),
        'timestamp': config.get('timestamp'),
        'best_pearson_r': safe_float(phase_a.get('best_pearson_r')),
        'rdm_perm_p': safe_float(phase_a.get('perm_p')),
        'rdm_significant': bool(phase_a.get('significant', False)),
        'best_params_json': json.dumps(phase_a.get('best_params', [])),
        'delta_theta_deg_json': json.dumps(phase_a.get('delta_theta_deg', [])),
        'synthetic_mean_norm': safe_float(phase_b.get('synthetic_mean_norm')),
        'loco_spearman_rho': safe_float(loco_match.get('spearman_rho')),
        'loco_spearman_p_raw': safe_float(loco_match.get('spearman_p_raw')),
        'loco_perm_p': safe_float(loco_match.get('perm_p')),
        'worst3_overlap': loco_match.get('worst3_overlap'),
        'per_hc_loco_spearman_rho': safe_float(per_hc_match.get('spearman_rho')),
        'per_hc_loco_perm_p': safe_float(per_hc_match.get('perm_p')),
        'per_hc_worst3_overlap': per_hc_match.get('worst3_overlap'),
        'mean_w_loco_spearman_rho': safe_float(mean_w_match.get('spearman_rho')),
        'mean_w_loco_perm_p': safe_float(mean_w_match.get('perm_p')),
        'mean_w_worst3_overlap': mean_w_match.get('worst3_overlap'),
        'worst3_synthetic_json': json.dumps(loco_match.get('worst3_synthetic', [])),
        'worst3_observed_json': json.dumps(loco_match.get('worst3_observed', [])),
        'vuln_synthetic_json': json.dumps(phase_c.get('vuln_synthetic')),
        'vuln_observed_json': json.dumps(phase_c.get('vuln_observed')),
        'has_observed_loco': phase_c.get('vuln_observed') is not None,
    }
    return row


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_group(rows, group_keys, expected_lookup):
    grouped = {}
    for row in rows:
        key = tuple(row[k] for k in group_keys)
        grouped.setdefault(key, []).append(row)

    summaries = []
    for key, group_rows in grouped.items():
        item = {k: v for k, v in zip(group_keys, key)}
        item['n_found'] = len(group_rows)
        item['n_expected'] = expected_lookup.get(key, len(group_rows))
        item['completion_rate'] = maybe_round(
            len(group_rows) / item['n_expected'] if item['n_expected'] else None, 3
        )
        item['subjects'] = ','.join(sorted({r['subject'] for r in group_rows}))
        item['rois'] = ','.join(sorted({r['roi'] for r in group_rows}))
        item['mean_loco_spearman_rho'] = maybe_round(
            safe_mean([r['loco_spearman_rho'] for r in group_rows])
        )
        item['mean_worst3_overlap'] = maybe_round(
            safe_int_mean([r['worst3_overlap'] for r in group_rows]), 3
        )
        item['mean_loco_perm_p'] = maybe_round(
            safe_mean([r['loco_perm_p'] for r in group_rows])
        )
        item['mean_rdm_pearson_r'] = maybe_round(
            safe_mean([r['best_pearson_r'] for r in group_rows])
        )
        item['mean_rdm_perm_p'] = maybe_round(
            safe_mean([r['rdm_perm_p'] for r in group_rows])
        )
        item['n_sig_loco'] = sum(
            1 for r in group_rows
            if r['loco_perm_p'] is not None and r['loco_perm_p'] < 0.05
        )
        item['n_sig_rdm'] = sum(1 for r in group_rows if r['rdm_significant'])
        item['mean_elapsed_sec'] = maybe_round(
            safe_mean([r['elapsed_sec'] for r in group_rows]), 1
        )
        summaries.append(item)

    summaries.sort(
        key=lambda x: (
            -(x['mean_loco_spearman_rho'] if x['mean_loco_spearman_rho'] is not None else -999),
            -(x['mean_worst3_overlap'] if x['mean_worst3_overlap'] is not None else -999),
            -x['n_sig_loco'],
            (x['mean_loco_perm_p'] if x['mean_loco_perm_p'] is not None else 999),
            -(x['mean_rdm_pearson_r'] if x['mean_rdm_pearson_r'] is not None else -999),
            (x['mean_rdm_perm_p'] if x['mean_rdm_perm_p'] is not None else 999),
        )
    )
    for idx, item in enumerate(summaries, start=1):
        item['rank'] = idx
    return summaries


def build_expected_lookup(expected_rows, group_keys):
    lookup = {}
    for row in expected_rows:
        key = tuple(row[k] for k in group_keys)
        lookup[key] = lookup.get(key, 0) + 1
    return lookup


def write_markdown_report(path, rows, missing, summary_by_condition, summary_by_roi):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append('# Geometry→Function Simulation Aggregate Report')
    lines.append('')
    lines.append('## Coverage')
    lines.append('')
    lines.append(f'- Completed combinations: {len(rows)}')
    lines.append(f'- Missing combinations: {len(missing)}')
    lines.append('- Ranking rule: behavioral LOCO fit first, RDM fit second')
    lines.append('  LOCO priority order = mean Spearman rho, mean worst-3 overlap, significant LOCO count, mean LOCO permutation p')
    lines.append('  RDM tie-breakers = mean Pearson r, mean RDM permutation p')
    lines.append('')

    if summary_by_condition:
        top = summary_by_condition[0]
        lines.append('## Best Overall Condition')
        lines.append('')
        lines.append(
            f"- Rank 1: `{top['model']} + {top['metric']}` "
            f"(mean LOCO rho={top['mean_loco_spearman_rho']}, "
            f"mean overlap={top['mean_worst3_overlap']}, "
            f"mean RDM r={top['mean_rdm_pearson_r']}, "
            f"{top['n_found']}/{top['n_expected']} complete)"
        )
        lines.append('')

    if summary_by_condition:
        lines.append('## Condition Ranking')
        lines.append('')
        lines.append('| Rank | Model | Metric | Found | Mean LOCO rho | Mean overlap | Sig LOCO | Mean LOCO p | Mean RDM r | Sig RDM |')
        lines.append('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
        for item in summary_by_condition:
            lines.append(
                f"| {item['rank']} | {item['model']} | {item['metric']} | "
                f"{item['n_found']}/{item['n_expected']} | "
                f"{item['mean_loco_spearman_rho']} | "
                f"{item['mean_worst3_overlap']} | "
                f"{item['n_sig_loco']} | "
                f"{item['mean_loco_perm_p']} | "
                f"{item['mean_rdm_pearson_r']} | "
                f"{item['n_sig_rdm']} |"
            )
        lines.append('')

    if summary_by_roi:
        lines.append('## ROI-Specific Ranking')
        lines.append('')
        lines.append('| Rank | ROI | Model | Metric | Found | Mean LOCO rho | Mean overlap | Mean RDM r |')
        lines.append('| --- | --- | --- | --- | ---: | ---: | ---: | ---: |')
        for item in summary_by_roi:
            lines.append(
                f"| {item['rank']} | {item['roi']} | {item['model']} | {item['metric']} | "
                f"{item['n_found']}/{item['n_expected']} | "
                f"{item['mean_loco_spearman_rho']} | "
                f"{item['mean_worst3_overlap']} | "
                f"{item['mean_rdm_pearson_r']} |"
            )
        lines.append('')

    if missing:
        lines.append('## Missing Combinations')
        lines.append('')
        for item in missing:
            lines.append(
                f"- `{item['combo_name']}` "
                f"({item['subject']} {item['roi']} {item['model']} {item['metric']})"
            )
        lines.append('')

    with open(path, 'w') as f:
        f.write('\n'.join(lines))


def print_console_summary(rows, missing, summary_by_condition):
    print('=' * 88)
    print('Geometry→Function simulation aggregate')
    print('=' * 88)
    print(f'Completed combinations: {len(rows)}')
    print(f'Missing combinations:   {len(missing)}')

    if not summary_by_condition:
        return

    print('\nTop ranked conditions (behavior-first):')
    for item in summary_by_condition[:5]:
        print(
            f"  #{item['rank']:>2}  {item['model']:<10} + {item['metric']:<11}  "
            f"LOCO rho={item['mean_loco_spearman_rho']!s:<6}  "
            f"overlap={item['mean_worst3_overlap']!s:<5}  "
            f"RDM r={item['mean_rdm_pearson_r']!s:<6}  "
            f"complete={item['n_found']}/{item['n_expected']}"
        )


def parse_args():
    script_dir = Path(__file__).resolve().parent
    pipeline_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description='Aggregate Geometry→Function simulation results'
    )
    parser.add_argument(
        '--results_dir',
        default=str(pipeline_dir / 'results' / 'sim'),
        help='Directory containing per-combination simulation outputs',
    )
    parser.add_argument(
        '--output_dir',
        default=str(pipeline_dir / 'results' / 'sim_aggregate'),
        help='Directory for aggregate CSV/JSON/Markdown outputs',
    )
    parser.add_argument('--subjects', nargs='+', default=DEFAULT_SUBJECTS)
    parser.add_argument('--rois', nargs='+', default=DEFAULT_ROIS)
    parser.add_argument('--models', nargs='+', default=DEFAULT_MODELS)
    parser.add_argument('--metrics', nargs='+', default=DEFAULT_METRICS)
    return parser.parse_args()


def main():
    args = parse_args()
    results_dir = Path(args.results_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not results_dir.exists():
        raise FileNotFoundError(f'Results directory not found: {results_dir}')

    expected_rows = expected_combinations(
        args.subjects, args.rois, args.models, args.metrics
    )
    expected_combo_names = {row['combo_name'] for row in expected_rows}

    rows = []
    for config_path, result_path in collect_result_dirs(results_dir):
        config = load_json(config_path)
        result = load_json(result_path)
        rows.append(flatten_result(config, result, config_path.parent))

    if not rows:
        raise RuntimeError(f'No completed result pairs found under {results_dir}')

    found_combo_names = {row['combo_name'] for row in rows}
    missing = [
        row for row in expected_rows
        if row['combo_name'] not in found_combo_names
    ]

    # Keep output deterministic and focused on the requested 48-combo grid.
    rows = [row for row in rows if row['combo_name'] in expected_combo_names]
    rows.sort(key=lambda x: (x['subject'], x['roi'], x['model'], x['metric']))

    condition_keys = ['model', 'metric']
    roi_keys = ['roi', 'model', 'metric']
    subject_roi_keys = ['subject', 'roi']

    summary_by_condition = summarize_group(
        rows, condition_keys, build_expected_lookup(expected_rows, condition_keys)
    )
    summary_by_roi = summarize_group(
        rows, roi_keys, build_expected_lookup(expected_rows, roi_keys)
    )
    summary_by_subject_roi = summarize_group(
        rows, subject_roi_keys, build_expected_lookup(expected_rows, subject_roi_keys)
    )

    per_combo_csv = output_dir / 'per_combination_results.csv'
    condition_csv = output_dir / 'summary_by_condition.csv'
    roi_csv = output_dir / 'summary_by_roi.csv'
    subject_roi_csv = output_dir / 'summary_by_subject_roi.csv'
    missing_json = output_dir / 'missing_combinations.json'
    summary_json = output_dir / 'aggregate_summary.json'
    report_md = output_dir / 'aggregate_report.md'

    write_csv(per_combo_csv, rows, list(rows[0].keys()))
    write_csv(condition_csv, summary_by_condition, list(summary_by_condition[0].keys()))
    write_csv(roi_csv, summary_by_roi, list(summary_by_roi[0].keys()))
    write_csv(subject_roi_csv, summary_by_subject_roi, list(summary_by_subject_roi[0].keys()))

    with open(missing_json, 'w') as f:
        json.dump(missing, f, indent=2)

    aggregate_payload = {
        'results_dir': str(results_dir),
        'output_dir': str(output_dir),
        'n_completed': len(rows),
        'n_expected': len(expected_rows),
        'n_missing': len(missing),
        'ranking_rule': {
            'primary': [
                'mean_loco_spearman_rho desc',
                'mean_worst3_overlap desc',
                'n_sig_loco desc',
                'mean_loco_perm_p asc',
            ],
            'tie_breakers': [
                'mean_rdm_pearson_r desc',
                'mean_rdm_perm_p asc',
            ],
        },
        'top_condition': summary_by_condition[0] if summary_by_condition else None,
        'summary_by_condition': summary_by_condition,
        'summary_by_roi': summary_by_roi,
        'summary_by_subject_roi': summary_by_subject_roi,
    }
    with open(summary_json, 'w') as f:
        json.dump(aggregate_payload, f, indent=2)

    write_markdown_report(
        report_md,
        rows,
        missing,
        summary_by_condition,
        summary_by_roi,
    )

    print_console_summary(rows, missing, summary_by_condition)
    print(f'\nSaved: {per_combo_csv}')
    print(f'Saved: {condition_csv}')
    print(f'Saved: {roi_csv}')
    print(f'Saved: {subject_roi_csv}')
    print(f'Saved: {missing_json}')
    print(f'Saved: {summary_json}')
    print(f'Saved: {report_md}')


if __name__ == '__main__':
    main()
