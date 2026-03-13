#!/usr/bin/env python3
"""
loco_fek_retry.py — LOCO with per-ROI optimal K (FE-K) instead of FE-6.

Tests whether the Phase 3 HC-CVD MAE gap (hV4 p=0.017, d=1.69)
survives when using per-ROI optimal K determined from forward model.

Rationale: FE-6 is overparameterized (K=6, 8 stimuli → df=1).
Per-ROI optimal K dramatically reduces HC-CVD gap in voxel_corr.
This script checks if the same holds for MAE.

Usage:
    python loco_fek_retry.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir ./results/loco_fek_retry \
        --subject 01 \
        --alignment procrustes
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from datetime import datetime

# Import from existing loco_baseline
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from loco_baseline import (
    load_amplitudes, create_basis_functions,
    HUE_ANGLES, circular_diff_deg,
    get_subject_group
)

# Per-ROI optimal K from forward model (HC LOCO validation)
OPTIMAL_K = {'V1': 2, 'V2': 3, 'V3': 8, 'V4': 3}
ROIS = ['V1', 'V2', 'V3', 'V4']


class LOCOForwardEncodingK:
    """ForwardEncoding with configurable n_channels."""

    def __init__(self, n_channels):
        self.n_channels = n_channels
        self.weights = None
        self.predict_basis = None

    def fit(self, X, y_labels):
        basis_full = create_basis_functions(n_channels=self.n_channels)
        self.predict_basis = basis_full
        hues = np.array([HUE_ANGLES[int(l)] for l in y_labels])
        C = basis_full[hues]
        # OLS (same as loco_baseline default alpha=0)
        self.weights = np.linalg.pinv(C) @ X

    def predict(self, X):
        if self.weights is None:
            raise RuntimeError("Not fitted")
        channel_responses = self.weights @ X.T
        n_samples = X.shape[0]
        y_pred = np.zeros(n_samples)
        for i in range(n_samples):
            pred_resp = channel_responses[:, i]
            corrs = np.array([
                np.corrcoef(pred_resp, self.predict_basis[h])[0, 1]
                for h in range(360)
            ])
            corrs = np.nan_to_num(corrs, nan=-1.0)
            y_pred[i] = np.argmax(corrs)
        return y_pred


def loco_cv_k(amplitudes, n_channels):
    """LOCO with specified n_channels."""
    n_runs, n_colors, n_voxels = amplitudes.shape
    all_hues = np.array(HUE_ANGLES)
    fold_results = []

    for test_color in range(n_colors):
        train_colors = np.array([c for c in range(n_colors) if c != test_color])
        test_hue = all_hues[test_color]

        X_train = amplitudes[:, train_colors, :].reshape(-1, n_voxels)
        X_test = amplitudes[:, test_color, :]
        y_train = np.tile(train_colors, n_runs)

        model = LOCOForwardEncodingK(n_channels=n_channels)
        model.fit(X_train, y_train)
        pred_hues = model.predict(X_test)

        errors = np.abs(circular_diff_deg(pred_hues, test_hue))
        adjacent_correct = np.mean(errors <= 45)

        # Also compute voxel_corr for this fold
        C_test = model.predict_basis[int(test_hue)]
        pred_pattern = C_test @ model.weights  # (n_voxels,)
        actual_mean = X_test.mean(axis=0)
        vc = np.corrcoef(pred_pattern, actual_mean)[0, 1]

        fold_results.append({
            'test_color': int(test_color),
            'test_hue': float(test_hue),
            'mae': float(np.mean(errors)),
            'adjacent_acc': float(adjacent_correct),
            'voxel_corr': float(vc),
            'errors_per_run': errors.tolist(),
            'pred_hues': pred_hues.tolist()
        })

    return fold_results


def main():
    parser = argparse.ArgumentParser(
        description="LOCO with per-ROI optimal K (FE-K retry)")
    parser.add_argument('--baseline_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--alignment', type=str, default='procrustes')
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    subject = args.subject
    group = get_subject_group(subject)
    print(f"\nLOCO FE-K Retry: sub-{subject} ({group})")
    print(f"Per-ROI optimal K: {OPTIMAL_K}")

    results = {}
    for roi in ROIS:
        k_opt = OPTIMAL_K[roi]
        print(f"\n--- {roi} (FE-{k_opt}) ---")

        try:
            amp = load_amplitudes(args.baseline_dir, subject, roi, args.alignment)
            print(f"  Loaded: {amp.shape}")
        except FileNotFoundError as e:
            print(f"  SKIP: {e}")
            continue

        # FE-K (per-ROI optimal)
        folds_k = loco_cv_k(amp, n_channels=k_opt)
        mae_k = np.mean([f['mae'] for f in folds_k])
        vc_k = np.mean([f['voxel_corr'] for f in folds_k])
        adj_k = np.mean([f['adjacent_acc'] for f in folds_k])

        # FE-6 (standard baseline)
        folds_6 = loco_cv_k(amp, n_channels=6)
        mae_6 = np.mean([f['mae'] for f in folds_6])
        vc_6 = np.mean([f['voxel_corr'] for f in folds_6])
        adj_6 = np.mean([f['adjacent_acc'] for f in folds_6])

        print(f"  FE-6:  MAE={mae_6:.1f}°  voxel_corr={vc_6:+.3f}  adj_acc={adj_6:.3f}")
        print(f"  FE-{k_opt}:  MAE={mae_k:.1f}°  voxel_corr={vc_k:+.3f}  adj_acc={adj_k:.3f}")
        print(f"  Delta: MAE={mae_k-mae_6:+.1f}°  voxel_corr={vc_k-vc_6:+.3f}")

        results[roi] = {
            'n_channels_optimal': k_opt,
            'n_voxels': int(amp.shape[2]),
            'fe6': {
                'n_channels': 6,
                'overall_mae': float(mae_6),
                'overall_voxel_corr': float(vc_6),
                'overall_adj_acc': float(adj_6),
                'fold_results': folds_6
            },
            'fek': {
                'n_channels': k_opt,
                'overall_mae': float(mae_k),
                'overall_voxel_corr': float(vc_k),
                'overall_adj_acc': float(adj_k),
                'fold_results': folds_k
            },
            'delta_mae': float(mae_k - mae_6),
            'delta_voxel_corr': float(vc_k - vc_6)
        }

    # Save
    out_file = output_path / f"sub-{subject}_loco_fek.json"
    save_data = {
        'subject': subject,
        'group': group,
        'alignment': args.alignment,
        'optimal_k': OPTIMAL_K,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'results': results
    }
    with open(out_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f"\nSaved: {out_file}")


if __name__ == '__main__':
    main()
