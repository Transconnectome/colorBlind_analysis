#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_feature_selection_individual.py
-----------------------------------
Individual-level feature selection methods: ANOVA, RFE, PCA

Applies to single subject-ROI combination.
Compares baseline (no selection) vs. each feature selection method.

Usage:
    python run_feature_selection_individual.py --subject 01 --roi V1 \
        --baseline-dir derivatives/BH2009_deoblique/20251210_123456/sub-01/sm0_hpNo_moNo_ccNo_drNo_stFa/V1

Output:
    derivatives/feature_selection/sub-XX/ROI/
    ├── anova_results.npz
    ├── rfe_results.npz
    ├── pca_results.npz
    └── comparison_summary.csv
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.feature_selection import f_classif, RFE
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Import utils
try:
    from utils_color_decoding import (
        evaluate_reconstruction,
        diag_linear_predict,
        compute_voxel_snr,
        visualize_circular_color_space
    )
except ImportError:
    print("ERROR: Cannot import utils_color_decoding.py")
    print("Make sure utils_color_decoding.py is in the same directory")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description='Individual-level feature selection')
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (01-10)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--baseline-dir', type=str, required=True,
                        help='Baseline analysis directory containing amplitudes_z.npy')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: auto-generated)')
    parser.add_argument('--n-features-anova', type=int, default=100,
                        help='Number of features to select for ANOVA (default: 100)')
    parser.add_argument('--n-features-rfe', type=int, default=100,
                        help='Number of features to select for RFE (default: 100)')
    parser.add_argument('--n-components-pca', type=int, default=6,
                        help='Number of PCA components (default: 6)')
    return parser.parse_args()


def load_baseline_data(baseline_dir):
    """Load baseline amplitudes_z.npy"""
    baseline_dir = Path(baseline_dir)
    amp_file = baseline_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"Baseline data not found: {amp_file}")

    amplitudes_z = np.load(amp_file)  # (n_runs, n_colors, n_voxels)
    print(f"  Loaded baseline amplitudes: {amplitudes_z.shape}")

    return amplitudes_z


def anova_selection(X, y, n_features):
    """ANOVA F-test based feature selection"""
    print(f"\n[1/3] ANOVA-based Feature Selection")
    print(f"  Selecting top {n_features} features...")

    # Compute F-scores
    f_scores, p_values = f_classif(X, y)

    # Select top features
    top_indices = np.argsort(f_scores)[::-1][:n_features]

    print(f"  Selected features: {len(top_indices)}")
    print(f"  F-score range: [{f_scores[top_indices].min():.2f}, {f_scores[top_indices].max():.2f}]")
    print(f"  Mean p-value: {p_values[top_indices].mean():.2e}")

    return top_indices, f_scores, p_values


def rfe_selection(X, y, n_features):
    """RFE (Recursive Feature Elimination) based selection"""
    print(f"\n[2/3] RFE-based Feature Selection")
    print(f"  Selecting top {n_features} features...")

    # Use Logistic Regression as base estimator
    estimator = LogisticRegression(max_iter=1000, random_state=42)

    # RFE
    selector = RFE(estimator, n_features_to_select=n_features, step=0.1)
    selector.fit(X, y)

    # Get selected features
    selected_mask = selector.support_
    selected_indices = np.where(selected_mask)[0]

    print(f"  Selected features: {len(selected_indices)}")
    print(f"  Feature ranking: min={selector.ranking_.min()}, max={selector.ranking_.max()}")

    return selected_indices, selector.ranking_


def pca_transform(X, n_components):
    """PCA dimensionality reduction"""
    print(f"\n[3/3] PCA Dimensionality Reduction")
    print(f"  Reducing to {n_components} components...")

    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X)

    var_explained = pca.explained_variance_ratio_
    cumvar = np.cumsum(var_explained)

    print(f"  Variance explained per component: {var_explained}")
    print(f"  Cumulative variance: {cumvar[-1]*100:.1f}%")

    return X_pca, pca, var_explained


def evaluate_method(amplitudes_z, selected_indices=None, method_name='Baseline'):
    """Evaluate classification and reconstruction performance"""
    print(f"\n=== Evaluating {method_name} ===")

    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Apply feature selection if provided
    if selected_indices is not None:
        amplitudes_z = amplitudes_z[:, :, selected_indices]
        print(f"  Using {len(selected_indices)} selected features")
    else:
        print(f"  Using all {n_voxels} features")

    # Classification (leave-one-run-out)
    classification_accs = []

    for test_run in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != test_run]

        X_train = amplitudes_z[train_runs].reshape(-1, amplitudes_z.shape[2])
        y_train = np.tile(np.arange(n_colors), len(train_runs))

        X_test = amplitudes_z[test_run]
        y_test = np.arange(n_colors)

        # Standardize
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Predict
        y_pred = diag_linear_predict(X_train_scaled, y_train, X_test_scaled)
        acc = np.mean(y_pred == y_test)
        classification_accs.append(acc)

    mean_classification_acc = np.mean(classification_accs)

    # Reconstruction (B&H 2009 forward model)
    reconstruction_errors, _, _ = evaluate_reconstruction(amplitudes_z)
    mean_reconstruction_error = np.mean(reconstruction_errors)

    # SNR
    snr_values = compute_voxel_snr(amplitudes_z)
    mean_snr = np.mean(snr_values)

    print(f"  Classification: {mean_classification_acc*100:.1f}%")
    print(f"  Reconstruction: {mean_reconstruction_error:.1f}°")
    print(f"  Mean SNR: {mean_snr:.2f}")

    return {
        'classification_acc': mean_classification_acc,
        'reconstruction_error': mean_reconstruction_error,
        'mean_snr': mean_snr,
        'classification_accs_per_run': classification_accs,
        'reconstruction_errors_per_run': reconstruction_errors
    }


def main():
    args = parse_args()

    print("=" * 80)
    print("Individual-level Feature Selection")
    print("=" * 80)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Baseline dir: {args.baseline_dir}")
    print()

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/feature_selection/sub-{args.subject}/{args.roi}")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # Load baseline data
    print("Loading baseline data...")
    amplitudes_z = load_baseline_data(args.baseline_dir)
    n_runs, n_colors, n_voxels = amplitudes_z.shape
    print(f"  Shape: (runs={n_runs}, colors={n_colors}, voxels={n_voxels})")
    print()

    # Prepare data for feature selection (concatenate all runs)
    X_all = amplitudes_z.reshape(-1, n_voxels)  # (n_runs * n_colors, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_runs)

    print(f"Feature selection input: X={X_all.shape}, y={y_all.shape}")
    print()

    # ========================================================================
    # Baseline (no selection)
    # ========================================================================
    print("=" * 80)
    print("[BASELINE] No Feature Selection")
    print("=" * 80)
    baseline_results = evaluate_method(amplitudes_z, selected_indices=None, method_name='Baseline')

    # ========================================================================
    # ANOVA-based selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("[METHOD 1] ANOVA-based Feature Selection")
    print("=" * 80)

    anova_indices, f_scores, p_values = anova_selection(X_all, y_all, args.n_features_anova)
    anova_results = evaluate_method(amplitudes_z, selected_indices=anova_indices, method_name='ANOVA')

    # Save ANOVA results
    np.savez(output_dir / 'anova_results.npz',
             selected_indices=anova_indices,
             f_scores=f_scores,
             p_values=p_values,
             **anova_results)

    # ========================================================================
    # RFE-based selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("[METHOD 2] RFE-based Feature Selection")
    print("=" * 80)

    rfe_indices, rfe_ranking = rfe_selection(X_all, y_all, args.n_features_rfe)
    rfe_results = evaluate_method(amplitudes_z, selected_indices=rfe_indices, method_name='RFE')

    # Save RFE results
    np.savez(output_dir / 'rfe_results.npz',
             selected_indices=rfe_indices,
             ranking=rfe_ranking,
             **rfe_results)

    # ========================================================================
    # PCA-based reduction
    # ========================================================================
    print("\n" + "=" * 80)
    print("[METHOD 3] PCA Dimensionality Reduction")
    print("=" * 80)

    # For PCA, we need to transform the data differently
    # Reshape to (n_samples, n_features) for PCA
    amplitudes_pca_list = []

    for run_idx in range(n_runs):
        X_run = amplitudes_z[run_idx]  # (n_colors, n_voxels)

        # Fit PCA on all runs except this one
        other_runs = [r for r in range(n_runs) if r != run_idx]
        X_other = amplitudes_z[other_runs].reshape(-1, n_voxels)

        pca = PCA(n_components=args.n_components_pca, random_state=42)
        pca.fit(X_other)

        # Transform current run
        X_run_pca = pca.transform(X_run)
        amplitudes_pca_list.append(X_run_pca)

    amplitudes_pca = np.array(amplitudes_pca_list)  # (n_runs, n_colors, n_components)

    # Evaluate PCA
    pca_results = evaluate_method(amplitudes_pca, selected_indices=None, method_name='PCA')

    # Fit final PCA on all data for visualization
    X_all_scaled = StandardScaler().fit_transform(X_all)
    _, final_pca, var_explained = pca_transform(X_all_scaled, args.n_components_pca)

    # Save PCA results
    np.savez(output_dir / 'pca_results.npz',
             n_components=args.n_components_pca,
             explained_variance_ratio=var_explained,
             components=final_pca.components_,
             **pca_results)

    # ========================================================================
    # Summary & Comparison
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY & COMPARISON")
    print("=" * 80)

    comparison_df = pd.DataFrame({
        'Method': ['Baseline', 'ANOVA', 'RFE', 'PCA'],
        'N_Features': [n_voxels, args.n_features_anova, args.n_features_rfe, args.n_components_pca],
        'Classification_Acc': [
            baseline_results['classification_acc'],
            anova_results['classification_acc'],
            rfe_results['classification_acc'],
            pca_results['classification_acc']
        ],
        'Reconstruction_Error': [
            baseline_results['reconstruction_error'],
            anova_results['reconstruction_error'],
            rfe_results['reconstruction_error'],
            pca_results['reconstruction_error']
        ],
        'Mean_SNR': [
            baseline_results['mean_snr'],
            anova_results['mean_snr'],
            rfe_results['mean_snr'],
            pca_results['mean_snr']
        ]
    })

    print("\n", comparison_df.to_string(index=False))

    # Save comparison
    comparison_df.to_csv(output_dir / 'comparison_summary.csv', index=False)

    # Best method
    best_class_idx = comparison_df['Classification_Acc'].argmax()
    best_recon_idx = comparison_df['Reconstruction_Error'].argmin()

    print("\n✅ Best Classification:", comparison_df.iloc[best_class_idx]['Method'],
          f"({comparison_df.iloc[best_class_idx]['Classification_Acc']*100:.1f}%)")
    print("✅ Best Reconstruction:", comparison_df.iloc[best_recon_idx]['Method'],
          f"({comparison_df.iloc[best_recon_idx]['Reconstruction_Error']:.1f}°)")

    print("\n" + "=" * 80)
    print("Individual Feature Selection Complete!")
    print("=" * 80)
    print(f"Results saved to: {output_dir}")


if __name__ == '__main__':
    main()
