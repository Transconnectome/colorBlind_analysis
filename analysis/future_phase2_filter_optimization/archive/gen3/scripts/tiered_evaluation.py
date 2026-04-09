#!/usr/bin/env python3
"""
tiered_evaluation.py — Multi-tiered evaluation of ΔRDM cone-shift fitting.

Tiered Criterion:
  Tier 1: Phase A ΔRDM fit quality (label_perm_p, baseline_improvement_p)
  Tier 2: V4 LOCO prediction (spearman_rho, baseline_improvement_p)
  Tier 3: Parameter stability (for cone_3way/fourier)
  Tier 4: Specificity check (sub-10 should be null)

Usage:
    python scripts/tiered_evaluation.py \
        --cosine_dir results/sim_cosine \
        --spearman_dir results/sim_spearman \
        --output results/tiered_evaluation.json
"""

import argparse
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

# Tier thresholds
TIER1_THRESHOLDS = {
    'label_perm_p_max': 0.05,
    'baseline_improvement_p_max': 0.10,  # Stricter than 0.05
    'improvement_min': 0.05,  # Minimum improvement over baseline
}

TIER2_THRESHOLDS = {
    'v4_rho_min': 0.5,
    'v4_label_p_max': 0.05,
    'v4_baseline_improvement_p_max': 0.10,
    'v4_delta_rho_min': 0.3,  # Minimum improvement over baseline
}

TIER3_THRESHOLDS = {
    'de_success_required': True,  # For cone_3way/fourier
}


def load_result_pair(base_dir, subj, model):
    """Load result.json and validation_v4.json."""
    result_path = Path(base_dir) / f'sub-{subj}_{model}_delta_rdm' / 'result.json'
    valid_path = Path(base_dir) / f'sub-{subj}_{model}_delta_rdm' / 'validation_v4.json'

    result, valid = None, None
    if result_path.exists():
        with open(result_path) as f:
            result = json.load(f)
    if valid_path.exists():
        with open(valid_path) as f:
            valid = json.load(f)
    return result, valid


def evaluate_tier1(result):
    """Tier 1: Phase A ΔRDM fit quality."""
    if not result:
        return {'pass': False, 'reason': 'No result file', 'details': {}}

    phase_a = result.get('phase_a', {})
    label_p = phase_a.get('label_perm_p', 1.0)
    baseline_imp_p = phase_a.get('baseline_improvement_p', 1.0)
    improvement = phase_a.get('improvement', 0.0)

    checks = {
        'label_perm_p': label_p,
        'baseline_improvement_p': baseline_imp_p,
        'improvement': improvement,
    }

    # Pass criteria (ALL must pass)
    pass_label = label_p <= TIER1_THRESHOLDS['label_perm_p_max']
    pass_baseline_p = baseline_imp_p <= TIER1_THRESHOLDS['baseline_improvement_p_max']
    pass_improvement = improvement >= TIER1_THRESHOLDS['improvement_min']

    all_pass = pass_label and pass_baseline_p and pass_improvement

    reasons = []
    if not pass_label:
        reasons.append(f"label_perm_p={label_p:.4f} > {TIER1_THRESHOLDS['label_perm_p_max']}")
    if not pass_baseline_p:
        reasons.append(f"baseline_improvement_p={baseline_imp_p:.4f} > {TIER1_THRESHOLDS['baseline_improvement_p_max']}")
    if not pass_improvement:
        reasons.append(f"improvement={improvement:.4f} < {TIER1_THRESHOLDS['improvement_min']}")

    return {
        'pass': all_pass,
        'reason': ' AND '.join(reasons) if reasons else 'PASS',
        'details': checks,
    }


def evaluate_tier2(valid):
    """Tier 2: V4 LOCO prediction quality."""
    if not valid:
        return {'pass': False, 'reason': 'No validation file', 'details': {}}

    v4 = valid.get('v4_loco', {})
    rho = v4.get('spearman_rho', 0.0)
    label_p = v4.get('label_perm_p', 1.0)
    baseline_imp_p = v4.get('baseline_improvement_p', 1.0)
    delta_rho = v4.get('delta_rho', 0.0)

    checks = {
        'spearman_rho': rho,
        'label_perm_p': label_p,
        'baseline_improvement_p': baseline_imp_p,
        'delta_rho': delta_rho,
    }

    # Pass criteria (emphasis on baseline improvement)
    pass_rho = abs(rho) >= TIER2_THRESHOLDS['v4_rho_min']
    pass_label_p = label_p <= TIER2_THRESHOLDS['v4_label_p_max']
    pass_baseline_p = baseline_imp_p <= TIER2_THRESHOLDS['v4_baseline_improvement_p_max']
    pass_delta = delta_rho >= TIER2_THRESHOLDS['v4_delta_rho_min']

    # Require at least: high rho + significant label_p + baseline improvement
    all_pass = pass_rho and pass_label_p and (pass_baseline_p or pass_delta)

    reasons = []
    if not pass_rho:
        reasons.append(f"|rho|={abs(rho):.3f} < {TIER2_THRESHOLDS['v4_rho_min']}")
    if not pass_label_p:
        reasons.append(f"label_p={label_p:.4f} > {TIER2_THRESHOLDS['v4_label_p_max']}")
    if not (pass_baseline_p or pass_delta):
        reasons.append(f"baseline_imp_p={baseline_imp_p:.4f} AND delta_rho={delta_rho:.3f} both weak")

    return {
        'pass': all_pass,
        'reason': ' AND '.join(reasons) if reasons else 'PASS',
        'details': checks,
    }


def evaluate_tier3(result):
    """Tier 3: Parameter stability (for multi-parameter models)."""
    if not result:
        return {'pass': False, 'reason': 'No result file', 'details': {}}

    model = result.get('model', '')
    if model == 'cone_1way':
        # Single parameter, no stability concern
        return {'pass': True, 'reason': 'cone_1way (single param)', 'details': {}}

    phase_a = result.get('phase_a', {})
    coarse = phase_a.get('coarse_grid', {})

    if model in ['cone_3way', 'fourier']:
        # Check differential_evolution success
        de_success = coarse.get('success', False)
        n_fev = coarse.get('n_fev', 0)

        checks = {
            'optimizer': 'differential_evolution',
            'success': de_success,
            'n_fev': n_fev,
        }

        if TIER3_THRESHOLDS['de_success_required'] and not de_success:
            return {
                'pass': False,
                'reason': f"DE convergence failed (n_fev={n_fev})",
                'details': checks,
            }

        return {
            'pass': True,
            'reason': f"DE converged (n_fev={n_fev})",
            'details': checks,
        }

    return {'pass': True, 'reason': 'No stability check defined', 'details': {}}


def evaluate_tier4_specificity(all_results, metric):
    """Tier 4: Specificity check (sub-10 should be null)."""
    sub10_results = {}

    for model in ['cone_1way', 'cone_3way', 'fourier']:
        result, valid = all_results.get(('10', model, metric), (None, None))
        if not valid:
            continue

        v4 = valid.get('v4_loco', {})
        rho = v4.get('spearman_rho', 0.0)
        label_p = v4.get('label_perm_p', 1.0)

        # Sub-10 should be NS
        is_specific = label_p > 0.05 or abs(rho) < 0.3

        sub10_results[model] = {
            'rho': rho,
            'label_p': label_p,
            'is_specific': is_specific,
        }

    n_total = len(sub10_results)
    n_specific = sum(1 for v in sub10_results.values() if v['is_specific'])

    return {
        'sub10_results': sub10_results,
        'n_specific': n_specific,
        'n_total': n_total,
        'specificity_rate': n_specific / n_total if n_total > 0 else 0,
    }


def tiered_evaluate(base_dir, subjects, models, metric):
    """Evaluate all cases with tiered criteria."""
    results = {}
    all_data = {}

    for subj in subjects:
        results[subj] = {}
        for model in models:
            result, valid = load_result_pair(base_dir, subj, model)
            all_data[(subj, model, metric)] = (result, valid)

            tier1 = evaluate_tier1(result)
            tier2 = evaluate_tier2(valid)
            tier3 = evaluate_tier3(result)

            # Overall verdict
            overall_pass = tier1['pass'] and tier2['pass'] and tier3['pass']
            overall_grade = 'PASS' if overall_pass else 'HOLD'

            # Flag sub-10 false positives
            if subj == '10' and tier2['pass']:
                overall_grade = 'FALSE_POSITIVE'

            results[subj][model] = {
                'tier1_phase_a': tier1,
                'tier2_v4_loco': tier2,
                'tier3_stability': tier3,
                'overall_grade': overall_grade,
                'best_params': result.get('phase_a', {}).get('best_params', []) if result else [],
            }

    # Tier 4: Specificity
    tier4 = evaluate_tier4_specificity(all_data, metric)

    return results, tier4


def print_tiered_summary(cosine_results, spearman_results, tier4_cosine, tier4_spearman):
    """Print human-readable tiered evaluation."""
    print('\n' + '='*80)
    print('TIERED EVALUATION: ΔRDM CONE-SHIFT FITTING')
    print('='*80)

    for metric_name, results, tier4 in [('COSINE', cosine_results, tier4_cosine),
                                          ('SPEARMAN', spearman_results, tier4_spearman)]:
        print(f'\n{"#"*80}')
        print(f'### {metric_name} METRIC ###')
        print(f'{"#"*80}')

        # Collect by grade
        by_grade = defaultdict(list)
        for subj, models_dict in results.items():
            for model, eval_dict in models_dict.items():
                grade = eval_dict['overall_grade']
                by_grade[grade].append((subj, model, eval_dict))

        # Print PASS cases
        print(f'\n{"="*70}')
        print(f'✅ PASS (All Tiers): {len(by_grade["PASS"])} cases')
        print(f'{"="*70}')
        for subj, model, eval_dict in sorted(by_grade['PASS']):
            params = eval_dict['best_params']
            tier2 = eval_dict['tier2_v4_loco']['details']
            rho = tier2['spearman_rho']
            label_p = tier2['label_perm_p']
            baseline_p = tier2['baseline_improvement_p']
            delta_rho = tier2['delta_rho']

            print(f'\nsub-{subj} {model}:')
            print(f'  δθ: {params}')
            print(f'  V4 ρ={rho:+.3f}** (p={label_p:.4f})')
            print(f'  Baseline improvement: Δρ={delta_rho:+.3f} (p={baseline_p:.4f})')

        # Print HOLD cases
        print(f'\n{"="*70}')
        print(f'⚠️  HOLD (Failed Tiers): {len(by_grade["HOLD"])} cases')
        print(f'{"="*70}')
        for subj, model, eval_dict in sorted(by_grade['HOLD']):
            failed_tiers = []
            if not eval_dict['tier1_phase_a']['pass']:
                failed_tiers.append(f"T1({eval_dict['tier1_phase_a']['reason']})")
            if not eval_dict['tier2_v4_loco']['pass']:
                failed_tiers.append(f"T2({eval_dict['tier2_v4_loco']['reason']})")
            if not eval_dict['tier3_stability']['pass']:
                failed_tiers.append(f"T3({eval_dict['tier3_stability']['reason']})")

            print(f'\nsub-{subj} {model}: {" | ".join(failed_tiers)}')

        # Print FALSE_POSITIVE cases
        if 'FALSE_POSITIVE' in by_grade:
            print(f'\n{"="*70}')
            print(f'❌ FALSE POSITIVE (sub-10 specificity): {len(by_grade["FALSE_POSITIVE"])} cases')
            print(f'{"="*70}')
            for subj, model, eval_dict in sorted(by_grade['FALSE_POSITIVE']):
                tier2 = eval_dict['tier2_v4_loco']['details']
                rho = tier2['spearman_rho']
                label_p = tier2['label_perm_p']
                print(f'sub-{subj} {model}: ρ={rho:+.3f} (p={label_p:.4f}) ← Should be null!')

        # Tier 4: Specificity summary
        print(f'\n{"="*70}')
        print(f'Tier 4: Specificity Check (sub-10 should be NS)')
        print(f'{"="*70}')
        print(f'Specificity rate: {tier4["n_specific"]}/{tier4["n_total"]} = '
              f'{tier4["specificity_rate"]:.2%}')
        for model, stats in tier4['sub10_results'].items():
            status = '✓' if stats['is_specific'] else '✗'
            print(f'  {status} {model}: ρ={stats["rho"]:+.3f} (p={stats["label_p"]:.4f})')


def main():
    parser = argparse.ArgumentParser(description='Tiered evaluation of ΔRDM fitting')
    parser.add_argument('--cosine_dir', type=str, required=True)
    parser.add_argument('--spearman_dir', type=str, required=True)
    parser.add_argument('--output', type=str, default='results/tiered_evaluation.json')
    parser.add_argument('--subjects', nargs='+', default=['08', '09', '10'])
    parser.add_argument('--models', nargs='+',
                        default=['cone_1way', 'cone_3way', 'fourier'])
    args = parser.parse_args()

    print('Running tiered evaluation...')
    cosine_results, tier4_cosine = tiered_evaluate(
        args.cosine_dir, args.subjects, args.models, 'cosine')
    spearman_results, tier4_spearman = tiered_evaluate(
        args.spearman_dir, args.subjects, args.models, 'spearman')

    # Save
    output = {
        'thresholds': {
            'tier1': TIER1_THRESHOLDS,
            'tier2': TIER2_THRESHOLDS,
            'tier3': TIER3_THRESHOLDS,
        },
        'cosine': {
            'results': cosine_results,
            'tier4_specificity': tier4_cosine,
        },
        'spearman': {
            'results': spearman_results,
            'tier4_specificity': tier4_spearman,
        },
    }

    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved: {args.output}')

    # Print summary
    print_tiered_summary(cosine_results, spearman_results,
                         tier4_cosine, tier4_spearman)


if __name__ == '__main__':
    main()
