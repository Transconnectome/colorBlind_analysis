#!/usr/bin/env python3
"""Aggregate extended model results across all 10 subjects.

Loads results/validation_extended/sub-{ID}_loco.json and produces
comparison tables matching §9h-6 format.

Usage:
    python analyze_extended_models.py
    python analyze_extended_models.py --result_dir ../results/validation_extended
"""

import argparse
import json
import numpy as np
from pathlib import Path

ROIS = ['V1', 'V2', 'V3', 'V4']
HC = [f'{i:02d}' for i in range(1, 8)]
CVD = [f'{i:02d}' for i in range(8, 11)]
ALL = HC + CVD

MODELS = ['ridge_gcv', 'prior_finetune',
          'mixed_ridge_prior', 'bayes_prior',
          'smooth_tikh', 'smooth_prior']
METRICS = ['mean_voxel_corr', 'mean_R2', 'mean_mae']


def load_data(result_dir):
    """Load all subject result files."""
    data = {}
    for subj in ALL:
        path = Path(result_dir) / f'sub-{subj}_loco.json'
        if path.exists():
            with open(path) as f:
                data[subj] = json.load(f)
    return data


def main():
    parser = argparse.ArgumentParser(
        description='Aggregate extended model results')
    parser.add_argument('--result_dir', type=str,
                        default=str(Path(__file__).parent.parent
                                    / 'results' / 'validation_extended'))
    parser.add_argument('--validation_dir', type=str,
                        default=str(Path(__file__).parent.parent
                                    / 'results' / 'validation'),
                        help='Original validation dir for comparison')
    args = parser.parse_args()

    data = load_data(args.result_dir)
    print(f'Loaded {len(data)} subjects from {args.result_dir}\n')

    if len(data) == 0:
        print('No data found. Check result_dir path.')
        return

    # ==================================================================
    # TABLE 1: LOCO voxel_corr — All subjects, mean (SD)
    # ==================================================================
    print('=' * 90)
    print('TABLE 1: LOCO mean_voxel_corr — All subjects mean (SD)')
    print('=' * 90)
    header = f'{"Model":>22}'
    for roi in ROIS:
        header += f'  {"":>3}{roi:>4}{"":>9}'
    print(header)
    print('-' * 90)

    for model in MODELS:
        line = f'{model:>22}'
        for roi in ROIS:
            vals = []
            for subj in ALL:
                if (subj in data and roi in data[subj]
                        and model in data[subj][roi]):
                    vals.append(data[subj][roi][model]['mean_voxel_corr'])
            if vals:
                line += f'  {np.mean(vals):>+7.4f} ({np.std(vals,ddof=1):.3f})'
            else:
                line += f'  {"N/A":>16}'
        print(line)

    # ==================================================================
    # TABLE 2: HC vs CVD breakdown
    # ==================================================================
    print(f'\n{"="*90}')
    print('TABLE 2: LOCO mean_voxel_corr — HC vs CVD')
    print('=' * 90)

    for group_name, group_subjs in [('HC', HC), ('CVD', CVD)]:
        print(f'\n  --- {group_name} (n={len(group_subjs)}) ---')
        header = f'  {"Model":>22}'
        for roi in ROIS:
            header += f'  {roi:>8}'
        print(header)
        print(f'  {"-"*58}')

        for model in MODELS:
            line = f'  {model:>22}'
            for roi in ROIS:
                vals = []
                for subj in group_subjs:
                    if (subj in data and roi in data[subj]
                            and model in data[subj][roi]):
                        vals.append(data[subj][roi][model]['mean_voxel_corr'])
                if vals:
                    line += f'  {np.mean(vals):>+8.4f}'
                else:
                    line += f'  {"N/A":>8}'
            print(line)

    # ==================================================================
    # TABLE 3: Improvement over ridge_gcv and prior_finetune
    # ==================================================================
    print(f'\n{"="*90}')
    print('TABLE 3: Delta voxel_corr vs baselines')
    print('=' * 90)

    for baseline in ('ridge_gcv', 'prior_finetune'):
        print(f'\n  Delta vs {baseline}:')
        header = f'  {"Model":>22}'
        for roi in ROIS:
            header += f'  {roi:>8}'
        print(header)
        print(f'  {"-"*58}')

        extended = ['mixed_ridge_prior', 'bayes_prior',
                    'smooth_tikh', 'smooth_prior']
        for model in extended:
            line = f'  {model:>22}'
            for roi in ROIS:
                base_vals = []
                model_vals = []
                for subj in ALL:
                    if (subj in data and roi in data[subj]
                            and baseline in data[subj][roi]
                            and model in data[subj][roi]):
                        base_vals.append(
                            data[subj][roi][baseline]['mean_voxel_corr'])
                        model_vals.append(
                            data[subj][roi][model]['mean_voxel_corr'])
                if base_vals:
                    delta = np.mean(model_vals) - np.mean(base_vals)
                    line += f'  {delta:>+8.4f}'
                else:
                    line += f'  {"N/A":>8}'
            print(line)

    # ==================================================================
    # TABLE 4: Selected hyperparameters
    # ==================================================================
    print(f'\n{"="*90}')
    print('TABLE 4: Selected hyperparameters (per subject × ROI)')
    print('=' * 90)

    for model in ['mixed_ridge_prior', 'bayes_prior',
                   'smooth_tikh', 'smooth_prior']:
        print(f'\n  --- {model} ---')
        header = f'  {"Subject":>8}'
        for roi in ROIS:
            header += f'  {roi:>16}'
        print(header)
        print(f'  {"-"*76}')

        for subj in ALL:
            line = f'  sub-{subj:>3}'
            for roi in ROIS:
                if (subj in data and roi in data[subj]
                        and model in data[subj][roi]):
                    params = data[subj][roi][model].get('selected_params', [])
                    if params:
                        # Mode of selected params across folds
                        from collections import Counter
                        param_tuples = [tuple(p) for p in params]
                        mode = Counter(param_tuples).most_common(1)[0][0]
                        param_str = ','.join(f'{p:.2g}' for p in mode)
                        line += f'  {param_str:>16}'
                    else:
                        line += f'  {"?":>16}'
                else:
                    line += f'  {"N/A":>16}'
            print(line)

    # ==================================================================
    # TABLE 5: mixed_ridge_prior lambda ratio
    # ==================================================================
    print(f'\n{"="*90}')
    print('TABLE 5: mixed_ridge_prior lambda/(alpha+lambda) ratio')
    print('=' * 90)
    header = f'  {"Subject":>8}'
    for roi in ROIS:
        header += f'  {roi:>8}'
    print(header)
    print(f'  {"-"*44}')

    for subj in ALL:
        line = f'  sub-{subj:>3}'
        for roi in ROIS:
            if (subj in data and roi in data[subj]
                    and 'mixed_ridge_prior' in data[subj][roi]):
                ratio = data[subj][roi]['mixed_ridge_prior'].get(
                    'lambda_ratio_mean')
                if ratio is not None:
                    line += f'  {ratio:>8.3f}'
                else:
                    line += f'  {"?":>8}'
            else:
                line += f'  {"N/A":>8}'
        print(line)

    # ==================================================================
    # TABLE 6: All 3 metrics
    # ==================================================================
    print(f'\n{"="*90}')
    print('TABLE 6: All metrics — All subjects mean')
    print('=' * 90)

    for roi in ROIS:
        print(f'\n  --- {roi} ---')
        header = f'  {"Model":>22}'
        for metric in METRICS:
            short = metric.replace('mean_', '')[:10]
            header += f'  {short:>10}'
        print(header)
        print(f'  {"-"*56}')

        for model in MODELS:
            line = f'  {model:>22}'
            for metric in METRICS:
                vals = []
                for subj in ALL:
                    if (subj in data and roi in data[subj]
                            and model in data[subj][roi]):
                        vals.append(data[subj][roi][model][metric])
                if vals:
                    line += f'  {np.mean(vals):>10.4f}'
                else:
                    line += f'  {"N/A":>10}'
            print(line)

    # ==================================================================
    # DECISION RULES
    # ==================================================================
    print(f'\n{"="*90}')
    print('DECISION RULES')
    print('=' * 90)

    for roi in ROIS:
        print(f'\n  {roi}:')

        # Collect per-model means
        model_means = {}
        for model in MODELS:
            vals = []
            for subj in ALL:
                if (subj in data and roi in data[subj]
                        and model in data[subj][roi]):
                    vals.append(data[subj][roi][model]['mean_voxel_corr'])
            if vals:
                model_means[model] = np.mean(vals)

        if not model_means:
            print('    No data')
            continue

        best = max(model_means, key=model_means.get)
        ridge_val = model_means.get('ridge_gcv', float('-inf'))
        prior_val = model_means.get('prior_finetune', float('-inf'))

        print(f'    Best model: {best} (r={model_means[best]:+.4f})')
        print(f'    ridge_gcv: r={ridge_val:+.4f}')
        print(f'    prior_finetune: r={prior_val:+.4f}')

        # Decision
        for ext_model in ['mixed_ridge_prior', 'bayes_prior',
                          'smooth_tikh', 'smooth_prior']:
            if ext_model in model_means:
                d_ridge = model_means[ext_model] - ridge_val
                d_prior = model_means[ext_model] - prior_val
                status = 'BEATS both' if (d_ridge > 0 and d_prior > 0) else \
                         'beats ridge' if d_ridge > 0 else \
                         'beats prior' if d_prior > 0 else 'WORSE'
                print(f'    {ext_model:>22}: r={model_means[ext_model]:+.4f} '
                      f'(d_ridge={d_ridge:+.4f}, d_prior={d_prior:+.4f}) '
                      f'-> {status}')

    # ==================================================================
    # Comparison with original validation (if available)
    # ==================================================================
    orig_dir = Path(args.validation_dir)
    orig_data = {}
    for subj in ALL:
        path = orig_dir / f'sub-{subj}_loco.json'
        if path.exists():
            with open(path) as f:
                orig_data[subj] = json.load(f)

    if orig_data:
        print(f'\n{"="*90}')
        print('SANITY CHECK: ridge_gcv consistency with original validation')
        print('=' * 90)
        for roi in ROIS:
            orig_vals = []
            new_vals = []
            for subj in ALL:
                if (subj in orig_data and roi in orig_data[subj]
                        and 'ridge_gcv' in orig_data[subj][roi]
                        and subj in data and roi in data[subj]
                        and 'ridge_gcv' in data[subj][roi]):
                    orig_vals.append(
                        orig_data[subj][roi]['ridge_gcv']['mean_voxel_corr'])
                    new_vals.append(
                        data[subj][roi]['ridge_gcv']['mean_voxel_corr'])
            if orig_vals:
                diff = np.abs(np.array(new_vals) - np.array(orig_vals))
                max_diff = diff.max()
                status = 'MATCH' if max_diff < 0.001 else 'MISMATCH'
                print(f'  {roi}: max_diff={max_diff:.6f} -> {status}')


if __name__ == '__main__':
    main()
