#!/usr/bin/env python3
"""
compare_metrics.py — Compare cosine vs spearman ΔRDM fitting results.

Usage:
    python scripts/compare_metrics.py \
        --cosine_dir results/sim_cosine \
        --spearman_dir results/sim_spearman \
        --output summary_metric_comparison.json
"""

import argparse
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

def load_results(base_dir, subjects, models):
    """Load all result.json and validation_v4.json files."""
    results = {}
    for subj in subjects:
        results[subj] = {}
        for model in models:
            key = f'{subj}_{model}'
            result_path = Path(base_dir) / f'sub-{subj}_{model}_delta_rdm' / 'result.json'
            valid_path = Path(base_dir) / f'sub-{subj}_{model}_delta_rdm' / 'validation_v4.json'

            if result_path.exists():
                with open(result_path) as f:
                    results[subj][f'{model}_fit'] = json.load(f)
            if valid_path.exists():
                with open(valid_path) as f:
                    results[subj][f'{model}_valid'] = json.load(f)
    return results

def compare_metrics(cosine_results, spearman_results, subjects, models):
    """Compare key metrics between cosine and spearman."""
    comparison = {
        'subjects': {},
        'summary': {}
    }

    for subj in subjects:
        comparison['subjects'][subj] = {}

        for model in models:
            fit_key = f'{model}_fit'
            valid_key = f'{model}_valid'

            cos_fit = cosine_results[subj].get(fit_key, {})
            spear_fit = spearman_results[subj].get(fit_key, {})
            cos_valid = cosine_results[subj].get(valid_key, {})
            spear_valid = spearman_results[subj].get(valid_key, {})

            if not cos_fit or not spear_fit:
                continue

            # Extract key metrics
            phase_a_cos = cos_fit.get('phase_a', {})
            phase_a_spear = spear_fit.get('phase_a', {})

            comparison['subjects'][subj][model] = {
                'best_params': {
                    'cosine': phase_a_cos.get('best_params', []),
                    'spearman': phase_a_spear.get('best_params', []),
                    'delta': float(np.sum(np.abs(
                        np.array(phase_a_cos.get('best_params', [0])) -
                        np.array(phase_a_spear.get('best_params', [0]))
                    ))),
                },
                'best_loss': {
                    'cosine': phase_a_cos.get('best_loss', 0),
                    'spearman': phase_a_spear.get('best_loss', 0),
                },
                'improvement': {
                    'cosine': phase_a_cos.get('improvement', 0),
                    'spearman': phase_a_spear.get('improvement', 0),
                },
                'label_perm_p': {
                    'cosine': phase_a_cos.get('label_perm_p', 1),
                    'spearman': phase_a_spear.get('label_perm_p', 1),
                },
                'v4_loco_rho': {
                    'cosine': cos_valid.get('v4_loco', {}).get('spearman_rho', 0) if cos_valid else 0,
                    'spearman': spear_valid.get('v4_loco', {}).get('spearman_rho', 0) if spear_valid else 0,
                },
                'v4_loco_p': {
                    'cosine': cos_valid.get('v4_loco', {}).get('label_perm_p', 1) if cos_valid else 1,
                    'spearman': spear_valid.get('v4_loco', {}).get('label_perm_p', 1) if spear_valid else 1,
                },
            }

    # Summary statistics
    all_param_deltas = []
    better_metric = {'cosine': 0, 'spearman': 0, 'tie': 0}

    for subj in subjects:
        for model in models:
            if model not in comparison['subjects'][subj]:
                continue
            comp = comparison['subjects'][subj][model]

            # Parameter difference
            all_param_deltas.append(comp['best_params']['delta'])

            # Which metric produced better V4 LOCO?
            cos_rho = comp['v4_loco_rho']['cosine']
            spear_rho = comp['v4_loco_rho']['spearman']
            if abs(spear_rho) > abs(cos_rho) + 0.05:
                better_metric['spearman'] += 1
            elif abs(cos_rho) > abs(spear_rho) + 0.05:
                better_metric['cosine'] += 1
            else:
                better_metric['tie'] += 1

    comparison['summary'] = {
        'mean_param_delta': float(np.mean(all_param_deltas)) if all_param_deltas else 0,
        'max_param_delta': float(np.max(all_param_deltas)) if all_param_deltas else 0,
        'v4_loco_better': better_metric,
        'n_comparisons': len(all_param_deltas),
    }

    return comparison

def print_summary(comparison):
    """Print human-readable summary."""
    print('\n' + '='*70)
    print('ΔRDM LOSS: COSINE vs SPEARMAN METRIC COMPARISON')
    print('='*70)

    summary = comparison['summary']
    print(f"\nTotal comparisons: {summary['n_comparisons']}")
    print(f"Mean parameter difference: {summary['mean_param_delta']:.2f}")
    print(f"Max parameter difference: {summary['max_param_delta']:.2f}")
    print(f"\nV4 LOCO performance (|ρ| > baseline + 0.05):")
    for metric, count in summary['v4_loco_better'].items():
        print(f"  {metric:10s}: {count:2d}")

    print('\n' + '-'*70)
    print('PER-SUBJECT RESULTS')
    print('-'*70)

    for subj, models_dict in comparison['subjects'].items():
        print(f"\nsub-{subj}:")
        for model, metrics in models_dict.items():
            print(f"  {model}:")

            # Best params
            cos_p = metrics['best_params']['cosine']
            spear_p = metrics['best_params']['spearman']
            delta_p = metrics['best_params']['delta']
            print(f"    δθ best:  cos={cos_p}  spear={spear_p}  (Δ={delta_p:.2f})")

            # p-values
            cos_pval = metrics['label_perm_p']['cosine']
            spear_pval = metrics['label_perm_p']['spearman']
            sig_cos = '*' if cos_pval < 0.05 else ''
            sig_spear = '*' if spear_pval < 0.05 else ''
            print(f"    ΔRDM p:   cos={cos_pval:.4f}{sig_cos}  spear={spear_pval:.4f}{sig_spear}")

            # V4 LOCO
            cos_rho = metrics['v4_loco_rho']['cosine']
            spear_rho = metrics['v4_loco_rho']['spearman']
            cos_loco_p = metrics['v4_loco_p']['cosine']
            spear_loco_p = metrics['v4_loco_p']['spearman']
            sig_cos_loco = '*' if cos_loco_p < 0.05 else ''
            sig_spear_loco = '*' if spear_loco_p < 0.05 else ''
            print(f"    V4 ρ:     cos={cos_rho:+.3f}(p={cos_loco_p:.4f}{sig_cos_loco})  "
                  f"spear={spear_rho:+.3f}(p={spear_loco_p:.4f}{sig_spear_loco})")

def main():
    parser = argparse.ArgumentParser(
        description='Compare cosine vs spearman ΔRDM fitting results')
    parser.add_argument('--cosine_dir', type=str, required=True)
    parser.add_argument('--spearman_dir', type=str, required=True)
    parser.add_argument('--output', type=str, default='summary_metric_comparison.json')
    parser.add_argument('--subjects', nargs='+', default=['08', '09', '10'])
    parser.add_argument('--models', nargs='+',
                        default=['cone_1way', 'cone_3way', 'fourier'])
    args = parser.parse_args()

    print('Loading results...')
    cosine_results = load_results(args.cosine_dir, args.subjects, args.models)
    spearman_results = load_results(args.spearman_dir, args.subjects, args.models)

    print('Comparing metrics...')
    comparison = compare_metrics(cosine_results, spearman_results,
                                  args.subjects, args.models)

    # Save JSON
    with open(args.output, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f'\nSaved: {args.output}')

    # Print summary
    print_summary(comparison)

if __name__ == '__main__':
    main()
