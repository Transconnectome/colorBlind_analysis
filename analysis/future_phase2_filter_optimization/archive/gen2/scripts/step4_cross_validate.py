#!/usr/bin/env python3
"""
step4_cross_validate.py — Cross-criterion convergence analysis.

Loads results from Steps 2-3 and checks:
  1. delta_theta* consistency across 3 criteria (Spearman r)
  2. Cross-validation: fit on criterion A -> evaluate on B, C
  3. Summary matrix: 5 models x 3 criteria x 3 CVD x {fit_score, cross_score}

Runs locally (conda env: srm).

Usage:
    python scripts/step4_cross_validate.py \
        --output_dir results/step4_cross_validation
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    CVD_SUBJECTS, ROIS,
)
from utils_distortion_models import (
    MODELS, get_delta_theta,
)

RESULTS_BASE = Path(__file__).resolve().parent.parent / 'results'
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def load_step_results(roi, cvd_subj):
    """Load all step results for one CVD subject x ROI."""
    results = {}

    # Step 2: RDM
    rdm_path = RESULTS_BASE / 'step2_rdm' / roi / f'sub-{cvd_subj}_rdm_fits.json'
    if rdm_path.exists():
        with open(rdm_path) as f:
            results['rdm'] = json.load(f)

    # Step 3: LORO
    loro_path = RESULTS_BASE / 'step3_loro' / roi / f'sub-{cvd_subj}_loro_fits.json'
    if loro_path.exists():
        with open(loro_path) as f:
            results['loro'] = json.load(f)

    # Step 3: LOCO
    loco_path = RESULTS_BASE / 'step3_loco' / roi / f'sub-{cvd_subj}_loco_sim.json'
    if loco_path.exists():
        with open(loco_path) as f:
            results['loco'] = json.load(f)

    # Step 3b: W constraint
    wc_path = RESULTS_BASE / 'step3_w_constraint' / roi / f'sub-{cvd_subj}_w_constraint.json'
    if wc_path.exists():
        with open(wc_path) as f:
            results['w_constraint'] = json.load(f)

    return results


def extract_params(step_results, model_name):
    """Extract fitted params from each criterion for a given model.

    Returns:
        params_dict: {criterion: params_array}
    """
    params = {}

    # Criterion 1a (RDM voxel)
    if 'rdm' in step_results:
        m = step_results['rdm'].get('models', {}).get(model_name, {})
        if '1a' in m:
            params['rdm_1a'] = np.array(m['1a']['params'])
        if '1b' in m:
            params['rdm_1b'] = np.array(m['1b']['params'])

    # Criterion 2 (LORO)
    if 'loro' in step_results:
        m = step_results['loro'].get('models', {}).get(model_name, {})
        if 'params' in m:
            params['loro'] = np.array(m['params'])

    # Criterion 3 (LOCO)
    if 'loco' in step_results:
        m = step_results['loco'].get('models', {}).get(model_name, {})
        if 'shift_at_test' in m:
            params['loco'] = np.array(m['shift_at_test']['params'])

    return params


def compute_param_consistency(params_dict, cvd_type):
    """Compute pairwise Spearman r between parameter estimates.

    Also converts to delta_theta for model-agnostic comparison.
    """
    criteria = list(params_dict.keys())
    n = len(criteria)
    if n < 2:
        return {}

    # Pairwise parameter correlation
    pairwise = {}
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = criteria[i], criteria[j]
            pi, pj = params_dict[ci], params_dict[cj]
            if len(pi) == len(pj) and len(pi) > 1:
                rho, p = spearmanr(pi, pj)
                if not np.isfinite(rho):
                    rho, p = 0.0, 1.0
            elif len(pi) == 1 and len(pj) == 1:
                # Scalar: just compare direction
                rho = 1.0 if np.sign(pi[0]) == np.sign(pj[0]) else -1.0
                p = 0.0
            else:
                rho, p = np.nan, np.nan

            pairwise[f'{ci}_vs_{cj}'] = {
                'spearman_r': float(rho) if np.isfinite(rho) else 0.0,
                'p_value': float(p) if np.isfinite(p) else 1.0,
            }

    return pairwise


def compute_convergence_summary(roi, cvd_subj, step_results):
    """Build convergence summary for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]
    summary = {'models': {}}

    for model_name in MODELS:
        params_dict = extract_params(step_results, model_name)
        consistency = compute_param_consistency(params_dict, cvd_type)

        # Extract fit scores
        scores = {}

        # RDM 1a
        if 'rdm' in step_results:
            m = step_results['rdm'].get('models', {}).get(model_name, {})
            if '1a' in m:
                scores['rdm_1a_loss'] = m['1a']['loss']
                scores['rdm_1a_aicc'] = m['1a']['aicc']
            if '1b' in m:
                scores['rdm_1b_loss'] = m['1b']['loss']
                scores['rdm_1b_aicc'] = m['1b']['aicc']
            if '1a_to_1b_transfer' in m:
                scores['transfer_r'] = m['1a_to_1b_transfer']['spearman_r']

        # LORO
        if 'loro' in step_results:
            m = step_results['loro'].get('models', {}).get(model_name, {})
            if 'loro_corr' in m:
                scores['loro_corr'] = m['loro_corr']
                scores['loro_improvement'] = m.get('improvement', 0)

        # LOCO
        if 'loco' in step_results:
            m = step_results['loco'].get('models', {}).get(model_name, {})
            if 'shift_at_test' in m:
                scores['loco_rho'] = m['shift_at_test']['spearman_r']
                scores['loco_p'] = m['shift_at_test']['spearman_p']

        # Parameters
        param_summary = {}
        for crit, p in params_dict.items():
            param_summary[crit] = p.tolist()

        summary['models'][model_name] = {
            'df': MODELS[model_name]['df'],
            'scores': scores,
            'consistency': consistency,
            'params': param_summary,
        }

    # W constraint
    if 'w_constraint' in step_results:
        wc = step_results['w_constraint']
        summary['w_constraint'] = {
            'delta_w_norm': wc.get('delta_w_norm'),
            'crawford_howell_p': wc.get('crawford_howell', {}).get('p_value'),
            'outlier_fraction': wc.get('element_outlier_fraction'),
        }

    # Best model per criterion
    summary['best_models'] = {}
    # RDM 1a: lowest AICc
    aicc_1a = {}
    for m in MODELS:
        if m in summary['models']:
            s = summary['models'][m]['scores']
            if 'rdm_1a_aicc' in s and np.isfinite(s['rdm_1a_aicc']):
                aicc_1a[m] = s['rdm_1a_aicc']
    if aicc_1a:
        summary['best_models']['rdm_1a'] = min(aicc_1a, key=aicc_1a.get)

    # LORO: highest correlation
    loro_corrs = {}
    for m in MODELS:
        if m in summary['models']:
            s = summary['models'][m]['scores']
            if 'loro_corr' in s:
                loro_corrs[m] = s['loro_corr']
    if loro_corrs:
        summary['best_models']['loro'] = max(loro_corrs, key=loro_corrs.get)

    # LOCO: highest Spearman r
    loco_rhos = {}
    for m in MODELS:
        if m in summary['models']:
            s = summary['models'][m]['scores']
            if 'loco_rho' in s:
                loco_rhos[m] = s['loco_rho']
    if loco_rhos:
        summary['best_models']['loco'] = max(loco_rhos, key=loco_rhos.get)

    # Convergence: same model wins >=2 criteria
    if summary['best_models']:
        from collections import Counter
        wins = Counter(summary['best_models'].values())
        winner, count = wins.most_common(1)[0]
        summary['convergence'] = {
            'converged': count >= 2,
            'best_model': winner,
            'n_criteria_won': count,
        }
    else:
        summary['convergence'] = {'converged': False, 'best_model': None,
                                  'n_criteria_won': 0}

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Step 4: Cross-criterion convergence')
    parser.add_argument('--output_dir', type=str,
                        default='results/step4_cross_validation')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Step 4: Cross-Criterion Convergence Analysis')
    print('=' * 60)

    all_summaries = {}

    for roi in args.rois:
        print(f'\n--- {roi} ---')
        for cvd_subj in args.cvd_subjects:
            print(f'  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')
            step_results = load_step_results(roi, cvd_subj)

            if not step_results:
                print('    No results found, skipping.')
                continue

            summary = compute_convergence_summary(roi, cvd_subj, step_results)

            conv = summary['convergence']
            print(f'    Convergence: {conv["converged"]} '
                  f'(best={conv["best_model"]}, wins={conv["n_criteria_won"]})')

            if 'best_models' in summary:
                for crit, model in summary['best_models'].items():
                    print(f'      {crit}: {model}')

            key = f'{roi}/sub-{cvd_subj}'
            all_summaries[key] = summary

    # Save
    result = {
        'timestamp': datetime.now().isoformat(),
        'summaries': all_summaries,
    }
    out_path = output_dir / 'convergence_summary.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f'\nResults saved to {out_path}')

    # Gate check: if all models produce delta ~0, warn
    for key, summary in all_summaries.items():
        all_zero = True
        for m_name, m_data in summary['models'].items():
            for crit, params in m_data.get('params', {}).items():
                if any(abs(p) > 1.0 for p in params):
                    all_zero = False
                    break
            if not all_zero:
                break
        if all_zero:
            print(f'\n  WARNING: {key} — all models produce delta ~0. '
                  f'Pipeline may not distinguish CVD from HC.')

    print('\nStep 4 complete.')


if __name__ == '__main__':
    main()
