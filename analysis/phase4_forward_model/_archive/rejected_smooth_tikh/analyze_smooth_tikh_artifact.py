#!/usr/bin/env python3
"""
analyze_smooth_tikh_artifact.py — Aggregate artifact validation results.

Reads sub-{ID}_artifact.json files and permutation test results.
Produces comparison tables for ridge_gcv vs smooth_tikh on:
  - voxel_corr, rdm_pearson, rdm_spearman, id_accuracy
  - HC vs CVD breakdown
  - Per-subject id_accuracy comparison
  - Artifact diagnosis with paired t-tests

Usage:
    python analyze_smooth_tikh_artifact.py
    python analyze_smooth_tikh_artifact.py --result_dir ../results/smooth_tikh_artifact
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy import stats

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
HC = [f'{i:02d}' for i in range(1, 8)]
CVD = [f'{i:02d}' for i in range(8, 11)]
ALL = HC + CVD

MODELS = ['ridge_gcv', 'smooth_tikh']
METRICS = ['mean_voxel_corr', 'rdm_pearson', 'rdm_spearman', 'id_accuracy']


def load_data(result_dir):
    """Load all subject artifact JSON files."""
    data = {}
    for subj in ALL:
        path = Path(result_dir) / f'sub-{subj}_artifact.json'
        if path.exists():
            with open(path) as f:
                data[subj] = json.load(f)
    return data


def main():
    parser = argparse.ArgumentParser(
        description='Aggregate smooth_tikh artifact results')
    parser.add_argument('--result_dir', type=str,
                        default=str(Path(__file__).parent.parent
                                    / 'results' / 'smooth_tikh_artifact'))
    args = parser.parse_args()

    data = load_data(args.result_dir)
    print(f'Loaded {len(data)} subjects from {args.result_dir}\n')

    if not data:
        print('No data found. Check result_dir path.')
        return

    # ==================================================================
    # TABLE 1: Full comparison — all metrics, all subjects
    # ==================================================================
    print('=' * 100)
    print('TABLE 1: ridge_gcv vs smooth_tikh — All subjects mean (SD)')
    print('=' * 100)

    for metric in METRICS:
        print(f'\n  --- {metric} ---')
        header = f'  {"Model":>12}'
        for roi in ROIS:
            header += f'  {ROI_DISPLAY[roi]:>16}'
        print(header)
        print(f'  {"-"*80}')

        for model in MODELS:
            line = f'  {model:>12}'
            for roi in ROIS:
                vals = []
                for subj in ALL:
                    if (subj in data and roi in data[subj]
                            and model in data[subj][roi]):
                        vals.append(data[subj][roi][model][metric])
                if vals:
                    m = np.mean(vals)
                    sd = np.std(vals, ddof=1) if len(vals) > 1 else 0.0
                    line += f'  {m:>+7.4f} ({sd:.3f})'
                else:
                    line += f'  {"N/A":>16}'
            print(line)

    # ==================================================================
    # TABLE 2: Paired delta (smooth_tikh - ridge_gcv)
    # ==================================================================
    print(f'\n{"="*100}')
    print('TABLE 2: Delta (smooth_tikh - ridge_gcv) — paired per-subject')
    print('=' * 100)

    delta_metrics = ['voxel_corr', 'rdm_pearson', 'id_accuracy']
    header = f'  {"Metric":>14}'
    for roi in ROIS:
        header += f'  {ROI_DISPLAY[roi]:>22}'
    print(header)
    print(f'  {"-"*104}')

    for metric in delta_metrics:
        line = f'  {metric:>14}'
        for roi in ROIS:
            d_vals = []
            for subj in ALL:
                if (subj in data and roi in data[subj]
                        and 'delta' in data[subj][roi]):
                    d_vals.append(data[subj][roi]['delta'][metric])
            if d_vals:
                m = np.mean(d_vals)
                sd = np.std(d_vals, ddof=1) if len(d_vals) > 1 else 0.0
                # Paired t-test
                t_val, p_val = stats.ttest_1samp(d_vals, 0)
                sig = '*' if p_val < 0.05 else ''
                line += f'  {m:>+.4f}({sd:.3f}) p={p_val:.3f}{sig}'
            else:
                line += f'  {"N/A":>22}'
        print(line)

    # ==================================================================
    # TABLE 3: HC vs CVD breakdown
    # ==================================================================
    print(f'\n{"="*100}')
    print('TABLE 3: HC vs CVD breakdown')
    print('=' * 100)

    for group_name, group_subjs in [('HC', HC), ('CVD', CVD)]:
        print(f'\n  === {group_name} (n={len(group_subjs)}) ===')

        for metric in METRICS:
            print(f'\n  {metric}:')
            header = f'  {"Model":>12}'
            for roi in ROIS:
                header += f'  {ROI_DISPLAY[roi]:>8}'
            print(header)
            print(f'  {"-"*48}')

            for model in MODELS:
                line = f'  {model:>12}'
                for roi in ROIS:
                    vals = []
                    for subj in group_subjs:
                        if (subj in data and roi in data[subj]
                                and model in data[subj][roi]):
                            vals.append(data[subj][roi][model][metric])
                    if vals:
                        line += f'  {np.mean(vals):>+8.4f}'
                    else:
                        line += f'  {"N/A":>8}'
                print(line)

    # ==================================================================
    # TABLE 4: Per-subject id_accuracy
    # ==================================================================
    print(f'\n{"="*100}')
    print('TABLE 4: Per-subject id_accuracy (ridge / smooth / delta)')
    print('=' * 100)

    header = f'  {"Subject":>8}  {"Group":>5}'
    for roi in ROIS:
        header += f'  {ROI_DISPLAY[roi]:>22}'
    print(header)
    print(f'  {"-"*110}')

    for subj in ALL:
        group = 'HC' if subj in HC else 'CVD'
        line = f'  sub-{subj:>3}  {group:>5}'
        for roi in ROIS:
            if subj in data and roi in data[subj]:
                r_id = data[subj][roi].get('ridge_gcv', {}).get(
                    'id_accuracy', float('nan'))
                s_id = data[subj][roi].get('smooth_tikh', {}).get(
                    'id_accuracy', float('nan'))
                delta = s_id - r_id
                arrow = 'v' if delta < 0 else ('^' if delta > 0 else '=')
                line += f'  {r_id:.3f}/{s_id:.3f}({delta:+.3f}{arrow})'
            else:
                line += f'  {"N/A":>22}'
        print(line)

    # ==================================================================
    # TABLE 5: Per-subject rdm_pearson
    # ==================================================================
    print(f'\n{"="*100}')
    print('TABLE 5: Per-subject rdm_pearson (ridge / smooth / delta)')
    print('=' * 100)

    header = f'  {"Subject":>8}  {"Group":>5}'
    for roi in ROIS:
        header += f'  {ROI_DISPLAY[roi]:>22}'
    print(header)
    print(f'  {"-"*110}')

    for subj in ALL:
        group = 'HC' if subj in HC else 'CVD'
        line = f'  sub-{subj:>3}  {group:>5}'
        for roi in ROIS:
            if subj in data and roi in data[subj]:
                r_rdm = data[subj][roi].get('ridge_gcv', {}).get(
                    'rdm_pearson', float('nan'))
                s_rdm = data[subj][roi].get('smooth_tikh', {}).get(
                    'rdm_pearson', float('nan'))
                delta = s_rdm - r_rdm
                arrow = 'v' if delta < 0 else ('^' if delta > 0 else '=')
                line += f'  {r_rdm:.3f}/{s_rdm:.3f}({delta:+.3f}{arrow})'
            else:
                line += f'  {"N/A":>22}'
        print(line)

    # ==================================================================
    # ARTIFACT DIAGNOSIS
    # ==================================================================
    print(f'\n{"="*100}')
    print('ARTIFACT DIAGNOSIS')
    print('=' * 100)

    for roi in ROIS:
        roi_disp = ROI_DISPLAY[roi]
        print(f'\n  {roi_disp}:')

        d_vc, d_rdm, d_id = [], [], []
        flags = 0
        for subj in ALL:
            if subj in data and roi in data[subj] and 'delta' in data[subj][roi]:
                d = data[subj][roi]['delta']
                d_vc.append(d['voxel_corr'])
                d_rdm.append(d['rdm_pearson'])
                d_id.append(d['id_accuracy'])
                if d.get('artifact_flag'):
                    flags += 1

        if not d_vc:
            print('    No data')
            continue

        print(f'    d(voxel_corr):  {np.mean(d_vc):+.4f} +/- '
              f'{np.std(d_vc, ddof=1):.4f}')
        print(f'    d(rdm_pearson): {np.mean(d_rdm):+.4f} +/- '
              f'{np.std(d_rdm, ddof=1):.4f}')
        print(f'    d(id_accuracy): {np.mean(d_id):+.4f} +/- '
              f'{np.std(d_id, ddof=1):.4f}')
        print(f'    Artifact flags: {flags}/{len(d_vc)} subjects')

        # Paired t-tests on deltas
        if len(d_rdm) > 1:
            t_rdm, p_rdm = stats.ttest_1samp(d_rdm, 0)
            t_id, p_id = stats.ttest_1samp(d_id, 0)
            print(f'    d(rdm) t-test: t={t_rdm:.3f}, p={p_rdm:.4f}')
            print(f'    d(id)  t-test: t={t_id:.3f}, p={p_id:.4f}')

        # Verdict
        mean_d_vc = np.mean(d_vc)
        mean_d_rdm = np.mean(d_rdm)
        mean_d_id = np.mean(d_id)

        if mean_d_vc > 0 and mean_d_rdm < -0.05:
            verdict = ('ARTIFACT CONFIRMED: voxel_corr UP but '
                       'rdm_pearson DOWN (same as Section 18)')
        elif mean_d_vc > 0 and mean_d_id < -0.05:
            verdict = ('ARTIFACT CONFIRMED: voxel_corr UP but '
                       'id_accuracy DOWN')
        elif mean_d_rdm < 0 and mean_d_id < 0:
            verdict = ('WARNING: both discriminability metrics slightly worse; '
                       'smooth_tikh gains may be illusory')
        elif mean_d_vc <= 0:
            verdict = 'NO BENEFIT: voxel_corr does not improve'
        else:
            verdict = ('CLEAN: smooth_tikh improves voxel_corr without '
                       'sacrificing color-discriminative structure')
        print(f'    VERDICT: {verdict}')

    # ==================================================================
    # Load permutation results if available
    # ==================================================================
    perm_path = Path(args.result_dir) / 'permutation_test_smooth_tikh.json'
    if perm_path.exists():
        print(f'\n{"="*100}')
        print('PERMUTATION TEST RESULTS (smooth_tikh)')
        print('=' * 100)

        with open(perm_path) as f:
            perm = json.load(f)

        # Compare with ridge_gcv permutation test
        ridge_perm_path = (Path(args.result_dir).parent
                           / 'loco_reinforcement' / 'permutation_test.json')
        ridge_perm = None
        if ridge_perm_path.exists():
            with open(ridge_perm_path) as f:
                ridge_perm = json.load(f)

        header = f'  {"ROI":>6}  {"Model":>12}  {"Observed":>10}  ' \
                 f'{"Null_mean":>10}  {"p_perm":>8}  {"Sig":>4}'
        print(header)
        print(f'  {"-"*60}')

        for roi_disp in ['V1', 'V2', 'V3', 'hV4']:
            # smooth_tikh
            if roi_disp in perm.get('results', {}):
                res = perm['results'][roi_disp]
                sig = '*' if res['p_perm'] < 0.05 else ''
                print(f'  {roi_disp:>6}  {"smooth_tikh":>12}  '
                      f'{res["observed"]:>10.4f}  '
                      f'{res["null_mean"]:>10.4f}  '
                      f'{res["p_perm"]:>8.4f}  {sig:>4}')

            # ridge_gcv for comparison
            if ridge_perm:
                r_key = roi_disp
                if r_key in ridge_perm.get('results', {}):
                    res_r = ridge_perm['results'][r_key]
                    sig_r = '*' if res_r['p_perm'] < 0.05 else ''
                    print(f'  {roi_disp:>6}  {"ridge_gcv":>12}  '
                          f'{res_r["observed"]:>10.4f}  '
                          f'{res_r["null_mean"]:>10.4f}  '
                          f'{res_r["p_perm"]:>8.4f}  {sig_r:>4}')

    # ==================================================================
    # FINAL SUMMARY
    # ==================================================================
    print(f'\n{"="*100}')
    print('FINAL SUMMARY')
    print('=' * 100)

    print('\n  Decision criteria:')
    print('    1. If smooth_tikh has higher voxel_corr BUT lower rdm_pearson or')
    print('       id_accuracy -> Section 18 artifact CONFIRMED, reject smooth_tikh')
    print('    2. If permutation p > 0.05 for smooth_tikh -> no evidence smooth_tikh')
    print('       captures color-specific signal above covariance baseline')
    print('    3. If both pass -> smooth_tikh is a genuine improvement, adopt it')

    print('\nDone.')


if __name__ == '__main__':
    main()
