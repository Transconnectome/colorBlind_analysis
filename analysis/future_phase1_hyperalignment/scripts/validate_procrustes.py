#!/usr/bin/env python3
"""
Validate Procrustes Approach
=============================

Critical question: "Procrustes는 괜찮?"

Tests:
1. Does run averaging improve between-color discriminability?
2. Are there systematic run effects?
3. Is T < p manageable with our regularization?
4. Do original Procrustes results make sense?

Author: Response to critical question
Date: 2025-12-18
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score, LeaveOneOut

sys.path.insert(0, str(Path(__file__).parent))
from hyperalignment_core import load_amplitudes


def test_averaging_improves_discriminability(subject_id, roi='V1'):
    """
    Test 1: Does averaging improve between-color structure?
    """

    print(f"\n{'='*70}")
    print(f"Test 1: Run Averaging Effect (sub-{subject_id} {roi})")
    print(f"{'='*70}")

    amplitudes = load_amplitudes(subject_id, roi)  # (6, 8, 429)
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Feature selection (top 200 voxels by F-score)
    from sklearn.feature_selection import f_classif
    colors_all = np.repeat(range(n_colors), n_runs)
    data_all = amplitudes.transpose(1, 0, 2).reshape(n_colors * n_runs, n_voxels)
    F_scores, _ = f_classif(data_all, colors_all)
    top_voxels = np.argsort(F_scores)[-200:]

    amplitudes_selected = amplitudes[:, :, top_voxels]

    # Run-wise discriminability
    discriminabilities_per_run = []
    for run_idx in range(n_runs):
        patterns = amplitudes_selected[run_idx]  # (8, 200)
        rdm = squareform(pdist(patterns, metric='correlation'))

        # Measure: mean off-diagonal distance
        mask = ~np.eye(n_colors, dtype=bool)
        mean_dist = rdm[mask].mean()
        discriminabilities_per_run.append(mean_dist)

    # Averaged discriminability
    patterns_avg = amplitudes_selected.mean(axis=0)  # (8, 200)
    rdm_avg = squareform(pdist(patterns_avg, metric='correlation'))
    discriminability_avg = rdm_avg[mask].mean()

    print(f"\nDiscriminability (mean pairwise distance):")
    print(f"  Individual runs: {np.mean(discriminabilities_per_run):.4f} ± {np.std(discriminabilities_per_run):.4f}")
    print(f"  Run-averaged:    {discriminability_avg:.4f}")

    improvement = (discriminability_avg - np.mean(discriminabilities_per_run)) / np.mean(discriminabilities_per_run) * 100

    if improvement > 5:
        print(f"\n✅ Averaging improves discriminability by {improvement:.1f}%")
        verdict = "GOOD"
    elif improvement > 0:
        print(f"\n⚠️ Averaging slightly improves discriminability by {improvement:.1f}%")
        verdict = "OK"
    else:
        print(f"\n❌ Averaging degrades discriminability by {improvement:.1f}%")
        verdict = "BAD"

    return {
        'discriminability_runs': discriminabilities_per_run,
        'discriminability_avg': discriminability_avg,
        'improvement_pct': improvement,
        'verdict': verdict
    }


def test_classification_performance(subject_id, roi='V1'):
    """
    Test 2: Classification accuracy with vs without averaging
    """

    print(f"\n{'='*70}")
    print(f"Test 2: Classification Performance (sub-{subject_id} {roi})")
    print(f"{'='*70}")

    amplitudes = load_amplitudes(subject_id, roi)
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Feature selection
    from sklearn.feature_selection import f_classif
    colors_all = np.repeat(range(n_colors), n_runs)
    data_all = amplitudes.transpose(1, 0, 2).reshape(n_colors * n_runs, n_voxels)
    F_scores, _ = f_classif(data_all, colors_all)
    top_voxels = np.argsort(F_scores)[-100:]

    amplitudes_selected = amplitudes[:, :, top_voxels]

    # Run-level classification (leave-one-run-out)
    accuracies_run_level = []
    for test_run in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != test_run]

        X_train = amplitudes_selected[train_runs].reshape(-1, amplitudes_selected.shape[2])
        y_train = np.tile(range(n_colors), len(train_runs))

        X_test = amplitudes_selected[test_run]
        y_test = range(n_colors)

        clf = LinearDiscriminantAnalysis()
        clf.fit(X_train, y_train)
        acc = clf.score(X_test, y_test)
        accuracies_run_level.append(acc)

    # Averaged classification (leave-one-out colors)
    patterns_avg = amplitudes_selected.mean(axis=0)  # (8, 100)

    loo = LeaveOneOut()
    accuracies_loo = []
    for train_idx, test_idx in loo.split(patterns_avg):
        X_train, X_test = patterns_avg[train_idx], patterns_avg[test_idx]
        y_train, y_test = train_idx, test_idx

        clf = LinearDiscriminantAnalysis()
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)
        accuracies_loo.append(pred[0] == y_test[0])

    acc_loo = np.mean(accuracies_loo)

    print(f"\nClassification accuracy:")
    print(f"  Run-level (LORO CV): {np.mean(accuracies_run_level):.3f} ± {np.std(accuracies_run_level):.3f}")
    print(f"  Averaged (LOO CV):   {acc_loo:.3f}")
    print(f"  Chance level:        {1/n_colors:.3f} (1/{n_colors})")

    if acc_loo > np.mean(accuracies_run_level):
        print(f"\n✅ Averaged patterns classify better")
        verdict = "GOOD"
    else:
        print(f"\n⚠️ Run-level classifies better (expected with more data)")
        verdict = "OK"

    if acc_loo > 1/n_colors * 1.5:
        print(f"✅ LOO accuracy significantly above chance")
    else:
        print(f"❌ LOO accuracy near chance level!")

    return {
        'acc_run_level': accuracies_run_level,
        'acc_averaged': acc_loo,
        'chance': 1/n_colors,
        'verdict': verdict
    }


def test_systematic_run_effects(subject_id, roi='V1'):
    """
    Test 3: Are there systematic run effects?
    """

    print(f"\n{'='*70}")
    print(f"Test 3: Systematic Run Effects (sub-{subject_id} {roi})")
    print(f"{'='*70}")

    amplitudes = load_amplitudes(subject_id, roi)
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Global pattern per run (average across colors)
    run_patterns = amplitudes.mean(axis=1)  # (6, 429)

    # Check if there's a linear trend across runs
    run_numbers = np.arange(n_runs)
    correlations = []

    for voxel_idx in range(n_voxels):
        voxel_timecourse = run_patterns[:, voxel_idx]
        r, p = pearsonr(run_numbers, voxel_timecourse)
        if p < 0.05:
            correlations.append(r)

    print(f"\nVoxels with significant run trend (p<0.05): {len(correlations)}/{n_voxels}")
    print(f"  Percentage: {len(correlations)/n_voxels*100:.1f}%")

    if len(correlations) > 0:
        print(f"  Mean correlation: {np.mean(correlations):.3f}")
        print(f"  Range: [{np.min(correlations):.3f}, {np.max(correlations):.3f}]")

    # Global drift
    global_signal = run_patterns.mean(axis=1)
    r_global, p_global = pearsonr(run_numbers, global_signal)
    print(f"\nGlobal signal trend:")
    print(f"  Correlation with run number: r={r_global:.3f}, p={p_global:.3f}")

    if p_global < 0.05 and abs(r_global) > 0.5:
        print(f"\n❌ Strong systematic run effect detected!")
        print(f"   → Should model or remove run effects")
        verdict = "BAD"
    elif len(correlations) / n_voxels > 0.1:
        print(f"\n⚠️ Moderate run effects in {len(correlations)/n_voxels*100:.0f}% of voxels")
        print(f"   → Consider run effect removal")
        verdict = "CAUTION"
    else:
        print(f"\n✅ No strong systematic run effects")
        verdict = "GOOD"

    return {
        'n_voxels_with_trend': len(correlations),
        'pct_voxels_with_trend': len(correlations)/n_voxels*100,
        'global_trend_r': r_global,
        'global_trend_p': p_global,
        'verdict': verdict
    }


def test_procrustes_T_vs_p(subject_id, roi='V1'):
    """
    Test 4: Is T < p manageable?
    """

    print(f"\n{'='*70}")
    print(f"Test 4: T vs p in Procrustes (sub-{subject_id} {roi})")
    print(f"{'='*70}")

    amplitudes = load_amplitudes(subject_id, roi)
    patterns_avg = amplitudes.mean(axis=0)  # (8, 429)

    T, p = patterns_avg.shape

    print(f"\nDimensions:")
    print(f"  T (colors): {T}")
    print(f"  p (voxels): {p}")
    print(f"  T/p ratio: {T/p*100:.1f}%")

    # Check rank
    U, S, Vt = np.linalg.svd(patterns_avg, full_matrices=False)
    effective_rank = np.sum(S > 1e-10)

    print(f"\nSingular values:")
    print(f"  Effective rank: {effective_rank}/{min(T, p)}")
    print(f"  Top 5 singular values: {S[:5]}")

    # Simulate Procrustes cross-covariance
    # M = Y.T @ X where Y, X are (8, 429)
    X = patterns_avg
    Y = patterns_avg + np.random.randn(*patterns_avg.shape) * 0.1  # Noisy version

    M = Y.T @ X  # (429, 429)
    U_m, S_m, Vt_m = np.linalg.svd(M, full_matrices=False)

    print(f"\nCross-covariance M = Y.T @ X:")
    print(f"  Shape: {M.shape}")
    print(f"  Rank: {np.sum(S_m > 1e-10)}/{min(M.shape)}")
    print(f"  Largest singular values: {S_m[:8]}")
    print(f"  Smallest 5 singular values: {S_m[-5:]}")

    # With regularization
    lambda_reg = 0.01
    M_reg = M + lambda_reg * np.eye(M.shape[0])
    U_r, S_r, Vt_r = np.linalg.svd(M_reg, full_matrices=False)

    print(f"\nWith regularization (λ={lambda_reg}):")
    print(f"  Smallest 5 singular values: {S_r[-5:]}")
    print(f"  Condition number: {S_r[0]/S_r[-1]:.2e}")

    if T/p < 0.05:
        print(f"\n❌ T/p = {T/p*100:.1f}% is very low (< 5%)")
        print(f"   → Rotation severely underdetermined")
        print(f"   → Need stronger regularization or feature selection")
        verdict = "PROBLEMATIC"
    elif T/p < 0.1:
        print(f"\n⚠️ T/p = {T/p*100:.1f}% is low (< 10%)")
        print(f"   → Rotation underdetermined but manageable")
        print(f"   → Regularization helps")
        verdict = "CAUTION"
    else:
        print(f"\n✅ T/p = {T/p*100:.1f}% is acceptable (≥ 10%)")
        verdict = "OK"

    return {
        'T': T,
        'p': p,
        'T_over_p': T/p,
        'effective_rank': effective_rank,
        'verdict': verdict
    }


def run_all_tests(subjects, roi='V1'):
    """
    Run all validation tests for all subjects.
    """

    print("\n" + "="*70)
    print(" COMPREHENSIVE PROCRUSTES VALIDATION")
    print("="*70)
    print(f"\n📍 ROI: {roi}")
    print(f"📍 Subjects: {len(subjects)}")

    all_results = {}

    for sub_id in subjects:
        print(f"\n" + "="*70)
        print(f" Subject {sub_id}")
        print("="*70)

        try:
            results = {}

            # Test 1
            results['averaging'] = test_averaging_improves_discriminability(sub_id, roi)

            # Test 2
            results['classification'] = test_classification_performance(sub_id, roi)

            # Test 3
            results['run_effects'] = test_systematic_run_effects(sub_id, roi)

            # Test 4
            results['T_vs_p'] = test_procrustes_T_vs_p(sub_id, roi)

            all_results[f'sub-{sub_id}'] = results

        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Overall summary
    print("\n" + "="*70)
    print(" OVERALL SUMMARY")
    print("="*70)

    print("\nSubject    Averaging  Classification  Run Effects  T vs p    Overall")
    print("-" * 80)

    for sub_id, results in all_results.items():
        avg_verdict = results['averaging']['verdict']
        cls_verdict = results['classification']['verdict']
        run_verdict = results['run_effects']['verdict']
        tvp_verdict = results['T_vs_p']['verdict']

        # Overall assessment
        if all(v in ['GOOD', 'OK'] for v in [avg_verdict, cls_verdict, run_verdict, tvp_verdict]):
            overall = "✅ VALID"
        elif 'BAD' in [avg_verdict, cls_verdict, run_verdict] or tvp_verdict == 'PROBLEMATIC':
            overall = "❌ INVALID"
        else:
            overall = "⚠️ CAUTION"

        print(f"{sub_id:10s} {avg_verdict:10s} {cls_verdict:14s} {run_verdict:11s} {tvp_verdict:9s} {overall}")

    # Final recommendation
    print("\n" + "="*70)
    print(" FINAL RECOMMENDATION: Is Procrustes Valid?")
    print("="*70)

    all_verdicts = []
    for results in all_results.values():
        all_verdicts.extend([
            results['averaging']['verdict'],
            results['classification']['verdict'],
            results['run_effects']['verdict'],
            results['T_vs_p']['verdict']
        ])

    n_good = all_verdicts.count('GOOD')
    n_ok = all_verdicts.count('OK')
    n_caution = all_verdicts.count('CAUTION')
    n_bad = all_verdicts.count('BAD')
    n_problematic = all_verdicts.count('PROBLEMATIC')

    print(f"\nTest results summary:")
    print(f"  GOOD: {n_good}")
    print(f"  OK: {n_ok}")
    print(f"  CAUTION: {n_caution}")
    print(f"  BAD: {n_bad}")
    print(f"  PROBLEMATIC: {n_problematic}")

    if n_bad + n_problematic > len(all_verdicts) * 0.3:
        print(f"\n❌ PROCRUSTES IS PROBLEMATIC")
        print(f"   → Too many failed tests ({n_bad + n_problematic}/{len(all_verdicts)})")
        print(f"   → Consider alternatives (SRM, RSA)")
    elif n_caution > len(all_verdicts) * 0.5:
        print(f"\n⚠️ PROCRUSTES IS ACCEPTABLE WITH CAUTION")
        print(f"   → Some issues but manageable")
        print(f"   → Apply recommended improvements")
    else:
        print(f"\n✅ PROCRUSTES IS VALID")
        print(f"   → Most tests passed")
        print(f"   → Can use with confidence")

    return all_results


if __name__ == '__main__':
    HC_SUBJECTS = ['02', '03', '05', '06', '07']

    results = run_all_tests(HC_SUBJECTS, roi='V1')
