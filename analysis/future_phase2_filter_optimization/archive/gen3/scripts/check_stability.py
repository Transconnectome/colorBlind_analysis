#!/usr/bin/env python3
"""
check_stability.py — Check parameter stability for cone_3way/fourier models.

For DE optimization, check:
  - Convergence status (success flag)
  - Function evaluations (n_fev)
  - Final loss value
  - Whether multiple runs would give similar results

Usage:
    python scripts/check_stability.py \
        --result_dir results/sim_cosine \
        --subject 08 \
        --model cone_3way
"""

import argparse
import json
import numpy as np
from pathlib import Path


def analyze_de_convergence(result_path):
    """Analyze DE optimization convergence."""
    with open(result_path) as f:
        result = json.load(f)

    phase_a = result.get('phase_a', {})
    coarse = phase_a.get('coarse_grid', {})
    best_params = phase_a.get('best_params', [])
    best_loss = phase_a.get('best_loss', 0)
    baseline_loss = phase_a.get('baseline_loss', 0)
    improvement = phase_a.get('improvement', 0)

    print('\n' + '='*70)
    print(f'DE Convergence Analysis: {result_path.name}')
    print('='*70)

    print(f'\nOptimizer: {coarse.get("method", "unknown")}')
    print(f'Success: {coarse.get("success", False)}')
    print(f'Iterations: {coarse.get("n_iter", 0)}')
    print(f'Function evaluations: {coarse.get("n_fev", 0)}')

    print(f'\nBest parameters: {best_params}')
    print(f'Best loss: {best_loss:.6f}')
    print(f'Baseline loss (δ=0): {baseline_loss:.6f}')
    print(f'Improvement: {improvement:+.6f}')

    print(f'\nPhase A statistics:')
    print(f'  label_perm_p: {phase_a.get("label_perm_p", 1.0):.4f}')
    print(f'  baseline_improvement_p: {phase_a.get("baseline_improvement_p", 1.0):.4f}')

    print(f'\nNull distribution:')
    print(f'  Mean: {phase_a.get("null_distribution_mean", 0):.6f}')
    print(f'  Std:  {phase_a.get("null_distribution_std", 0):.6f}')
    print(f'  Size: {phase_a.get("null_distribution_size", 0)}')

    # Assess stability
    print(f'\n{"="*70}')
    print('STABILITY ASSESSMENT:')
    print('='*70)

    issues = []

    if not coarse.get('success', False):
        issues.append('❌ DE did not converge (success=False)')

    if improvement < 0.05:
        issues.append(f'❌ Negligible improvement over baseline ({improvement:.4f})')

    if best_loss < 0:
        issues.append(f'⚠️  Negative loss ({best_loss:.4f}) suggests poor fit')

    if abs(best_loss - baseline_loss) < 0.01:
        issues.append('❌ Best ≈ baseline (optimizer stuck at δ=0?)')

    label_p = phase_a.get('label_perm_p', 1.0)
    if label_p > 0.05:
        issues.append(f'❌ Phase A not significant (p={label_p:.4f})')

    if not issues:
        print('✅ No major stability issues detected')
    else:
        for issue in issues:
            print(issue)

    # Check if parameters are at bounds (suggests optimizer hitting limits)
    model_name = result.get('model', '')
    if model_name == 'cone_3way':
        bounds = [(-60, 60), (-60, 60), (-60, 60)]
    elif model_name == 'fourier':
        bounds = [(-30, 30)] * 4
    else:
        bounds = None

    if bounds and best_params:
        print(f'\nParameter bounds check:')
        at_bounds = []
        for i, (param, (lo, hi)) in enumerate(zip(best_params, bounds)):
            if abs(param - lo) < 1 or abs(param - hi) < 1:
                at_bounds.append(f'  Param {i}: {param:.2f} near bound [{lo}, {hi}]')
        if at_bounds:
            print('⚠️  Parameters at/near bounds (may be constrained):')
            for msg in at_bounds:
                print(msg)
        else:
            print('✅ No parameters at bounds')

    return {
        'success': coarse.get('success', False),
        'n_fev': coarse.get('n_fev', 0),
        'best_loss': best_loss,
        'improvement': improvement,
        'label_p': label_p,
        'issues': issues,
    }


def main():
    parser = argparse.ArgumentParser(description='Check parameter stability')
    parser.add_argument('--result_dir', type=str, required=True)
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--model', type=str, required=True)
    args = parser.parse_args()

    result_path = (Path(args.result_dir)
                   / f'sub-{args.subject}_{args.model}_delta_rdm'
                   / 'result.json')

    if not result_path.exists():
        print(f'Error: {result_path} not found')
        return

    analyze_de_convergence(result_path)


if __name__ == '__main__':
    main()
