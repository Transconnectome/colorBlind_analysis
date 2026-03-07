#!/usr/bin/env python3
"""
phase1_cross_subject_loso.py
=============================

Phase 1C: Cross-Subject Decoding (Leave-One-Subject-Out)

HC 피험자들의 decoder가 다른 HC에게 일반화되는지 테스트합니다.

**핵심 질문**: HC 간에 공통 color encoding system이 존재하는가?

**방법**:
1. Leave-One-Subject-Out (LOSO) cross-validation
   - 5명 HC로 학습 → 1명 HC로 테스트 (6 folds)
2. 각 fold에서:
   - Training: 5명의 데이터를 pooling하여 6-channel decoder 학습
   - Testing: 남은 1명의 데이터로 reconstruction/classification 평가
3. Baseline 비교: 개인 내(within-subject) decoding과 비교

**주요 지표**:
- ΔACC = ACC_within - ACC_cross_subject
  - < 10%: 강한 일반화 (공통 시스템 존재)
  - 10-20%: 보통
  - > 20%: 약한 일반화 (개인 특이적)

- ΔMSE = MSE_cross - MSE_within (circular reconstruction error)
  - 낮을수록 좋음

**중요**:
- 같은 voxel 위치 사용 (union of training subjects' voxels)
- 같은 W matrix 사용 (training data로 학습한 것)

Usage:
    python analysis/group_level/phase1_cross_subject_loso.py \
        --roi V1 \
        --timestamp baseline32_deob_determin \
        --subjects 01 02 03 05 06 07

Author: Claude Code
Date: 2025-12-16
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
import glob
from sklearn.metrics import confusion_matrix, accuracy_score

# Import existing utilities
from utils_color_decoding import (
    LABEL2HUE_DEG, N_COLORS,
    create_basis_functions, diag_linear_predict,
    circular_diff_deg, evaluate_reconstruction,
    visualize_circular_color_space, get_stimulus_color_rgb
)

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Phase 1C: Cross-Subject LOSO')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline32_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--n-channels', type=int, default=6,
                        help='Number of channels in encoding model (default: 6)')
    parser.add_argument('--output-dir', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    피험자의 amplitudes_z 로드

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels) array
        hues: (n_colors,) stimulus hue values in degrees
        result_dir: Path to result directory
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'
    amplitudes = np.load(amp_file)

    # Stimulus hue values (8 colors)
    hues = np.array([LABEL2HUE_DEG[f'color_{i+1}'] for i in range(N_COLORS)])

    return amplitudes, hues, result_dir

# ============================================================================
# 6-Channel Forward Encoding Model
# ============================================================================

class ColorDecoder:
    """
    6-channel forward encoding model (Brouwer & Heeger 2009)

    **모델 원리**:
    1. 6개의 channel이 색상환을 60° 간격으로 커버 (0°, 60°, 120°, 180°, 240°, 300°)
    2. 각 channel은 특정 색상에서 최대 반응 (Gaussian-like tuning curve)
    3. 학습: Neural response = Channel responses × Weights
       → W = pinv(C) @ Amplitudes
    4. 테스트: Channel responses 추정 → 색상 reconstruction

    **지표**:
    - W matrix: (n_voxels, n_channels) 각 voxel의 channel weights
    - Classification Accuracy: 8개 색상 중 정확히 맞춘 비율 (chance = 12.5%)
    - Reconstruction Error (MSE): 실제 hue와 예측 hue의 circular distance
      MSE = mean(circular_diff(true_hue, pred_hue)^2)
    """

    def __init__(self, n_channels=6):
        self.n_channels = n_channels
        self.W = None  # Weight matrix (n_voxels, n_channels)
        self.basis = create_basis_functions(n_channels)  # (360, n_channels)

    def _get_channel_responses(self, hues):
        """
        Stimulus hue → Channel responses 변환

        Args:
            hues: (n_samples,) hue values in degrees

        Returns:
            C: (n_samples, n_channels) channel responses
        """
        hues_int = np.round(hues).astype(int) % 360
        C = self.basis[hues_int, :]  # Look up basis functions
        return C

    def train(self, amplitudes_train, hues_train):
        """
        Encoding model 학습

        **학습 과정**:
        1. Stimulus hue → Channel responses (C_train)
        2. W = pinv(C_train) @ amplitudes_train
           - pinv: Moore-Penrose pseudoinverse (최소자승 해)

        Args:
            amplitudes_train: (n_samples, n_voxels) z-scored neural responses
            hues_train: (n_samples,) stimulus hues

        Returns:
            W: (n_voxels, n_channels) weight matrix
        """
        # Channel responses for training stimuli
        C_train = self._get_channel_responses(hues_train)  # (n_samples, n_channels)

        # Learn weights: W = pinv(C) @ amplitudes
        # C: (n_samples, n_channels)
        # amplitudes: (n_samples, n_voxels)
        # W: (n_voxels, n_channels) - transposed for easier interpretation
        self.W = np.linalg.pinv(C_train.T) @ amplitudes_train.T

        return self.W

    def predict(self, amplitudes_test):
        """
        Neural response → Hue reconstruction

        **Reconstruction 과정**:
        1. C_pred = amplitudes @ W (predicted channel responses)
        2. Hue 찾기: argmax_h { correlation(C_pred, basis[h]) }
           - 360° 모든 hue에 대해 channel profile과 비교

        Args:
            amplitudes_test: (n_samples, n_voxels) test neural responses

        Returns:
            hues_pred: (n_samples,) reconstructed hues in degrees
        """
        if self.W is None:
            raise RuntimeError("Model not trained yet!")

        # Predict channel responses: C_pred = amplitudes @ W
        C_pred = amplitudes_test @ self.W.T  # (n_samples, n_channels)

        # Reconstruct hue from channel profile
        hues_pred = np.zeros(len(C_pred))

        for i, c_pred in enumerate(C_pred):
            # Find best matching hue (0-359°)
            # Correlation between predicted channel response and each hue's basis
            corrs = np.dot(self.basis, c_pred)  # (360,)
            hues_pred[i] = np.argmax(corrs)

        return hues_pred

# ============================================================================
# LOSO Cross-Validation
# ============================================================================

def run_loso_fold(train_subjects, test_subject, data_dict, hues_dict, n_channels=6):
    """
    단일 LOSO fold 실행

    **절차**:
    1. Training subjects의 voxel union 구하기
    2. Training data pooling (모든 runs, 모든 subjects)
    3. Decoder 학습
    4. Test subject에 같은 voxel 위치에서 테스트

    Args:
        train_subjects: List of training subject IDs
        test_subject: Test subject ID
        data_dict: Dict[subject_id -> amplitudes]
        hues_dict: Dict[subject_id -> hues]

    Returns:
        results: Dict with performance metrics
    """
    print(f"\n  Fold: Train on {train_subjects} → Test on {test_subject}")

    # ========================================================================
    # 1. Voxel selection: Union of training subjects
    # ========================================================================
    # 모든 training subjects의 voxel 수 확인
    n_voxels_list = [data_dict[sub].shape[2] for sub in train_subjects]
    min_voxels = min(n_voxels_list)

    # 간단히 minimum voxel 수 사용 (모든 subjects에 존재하는 voxels)
    # 실제로는 MNI 좌표 기반 매칭이 필요하지만, 같은 ROI mask 사용 시 index 일치
    selected_voxels = np.arange(min_voxels)
    n_selected = len(selected_voxels)

    print(f"    Selected voxels: {n_selected} (minimum across training subjects)")

    # ========================================================================
    # 2. Pool training data
    # ========================================================================
    train_amplitudes_list = []
    train_hues_list = []

    for sub in train_subjects:
        amp = data_dict[sub]  # (n_runs, n_colors, n_voxels)
        n_runs, n_colors, n_voxels = amp.shape

        # Select voxels
        amp_selected = amp[:, :, selected_voxels]

        # Reshape: (n_runs, n_colors, n_voxels) → (n_runs * n_colors, n_voxels)
        amp_flat = amp_selected.reshape(-1, n_selected)

        train_amplitudes_list.append(amp_flat)

        # Corresponding hues (repeated for each run)
        hues = hues_dict[sub]
        hues_repeated = np.tile(hues, n_runs)
        train_hues_list.append(hues_repeated)

    # Stack all training data
    amplitudes_train = np.vstack(train_amplitudes_list)  # (n_total_samples, n_voxels)
    hues_train = np.concatenate(train_hues_list)  # (n_total_samples,)

    print(f"    Training samples: {len(amplitudes_train)} (pooled from {len(train_subjects)} subjects)")

    # ========================================================================
    # 3. Train decoder
    # ========================================================================
    decoder = ColorDecoder(n_channels=n_channels)
    decoder.train(amplitudes_train, hues_train)

    print(f"    ✓ Decoder trained (W matrix: {decoder.W.T.shape})")

    # ========================================================================
    # 4. Test on held-out subject
    # ========================================================================
    test_amp = data_dict[test_subject][:, :, selected_voxels]  # (n_runs, n_colors, n_voxels)
    test_hues = hues_dict[test_subject]

    n_runs_test, n_colors_test, _ = test_amp.shape

    # Reshape
    test_amp_flat = test_amp.reshape(-1, n_selected)
    test_hues_repeated = np.tile(test_hues, n_runs_test)

    # Predict
    hues_pred = decoder.predict(test_amp_flat)

    # ========================================================================
    # 5. Evaluate
    # ========================================================================
    # Classification accuracy (8-way)
    # 예측 hue를 가장 가까운 stimulus color로 매핑
    stimulus_hues = np.array(list(LABEL2HUE_DEG.values()))

    labels_true = []
    labels_pred = []

    for i, (true_hue, pred_hue) in enumerate(zip(test_hues_repeated, hues_pred)):
        # Find closest stimulus color
        true_label = np.argmin(circular_diff_deg(true_hue, stimulus_hues))
        pred_label = np.argmin(circular_diff_deg(pred_hue, stimulus_hues))

        labels_true.append(true_label)
        labels_pred.append(pred_label)

    labels_true = np.array(labels_true)
    labels_pred = np.array(labels_pred)

    acc_cross = accuracy_score(labels_true, labels_pred)

    # Reconstruction error (circular MSE)
    errors = circular_diff_deg(test_hues_repeated, hues_pred)
    mse_cross = np.mean(errors ** 2)
    mae_cross = np.mean(errors)

    print(f"    Cross-subject ACC: {acc_cross:.3f}")
    print(f"    Cross-subject MSE: {mse_cross:.2f}°²")
    print(f"    Cross-subject MAE: {mae_cross:.2f}°")

    # ========================================================================
    # 6. Within-subject baseline (train/test on same subject)
    # ========================================================================
    # Leave-one-run-out within test subject
    within_accs = []
    within_mses = []

    for run_idx in range(n_runs_test):
        # Train on all runs except run_idx
        train_runs = [r for r in range(n_runs_test) if r != run_idx]
        test_run = run_idx

        # Training data (within-subject)
        amp_train_within = test_amp[train_runs, :, :].reshape(-1, n_selected)
        hues_train_within = np.tile(test_hues, len(train_runs))

        # Test data
        amp_test_within = test_amp[test_run, :, :].reshape(-1, n_selected)
        hues_test_within = test_hues

        # Train and predict
        decoder_within = ColorDecoder(n_channels=n_channels)
        decoder_within.train(amp_train_within, hues_train_within)
        hues_pred_within = decoder_within.predict(amp_test_within)

        # Evaluate
        labels_true_within = []
        labels_pred_within = []
        for true_hue, pred_hue in zip(hues_test_within, hues_pred_within):
            true_label = np.argmin(circular_diff_deg(true_hue, stimulus_hues))
            pred_label = np.argmin(circular_diff_deg(pred_hue, stimulus_hues))
            labels_true_within.append(true_label)
            labels_pred_within.append(pred_label)

        acc_within = accuracy_score(labels_true_within, labels_pred_within)
        errors_within = circular_diff_deg(hues_test_within, hues_pred_within)
        mse_within = np.mean(errors_within ** 2)

        within_accs.append(acc_within)
        within_mses.append(mse_within)

    acc_within = np.mean(within_accs)
    mse_within = np.mean(within_mses)

    # Compute ΔACC and ΔMSE
    delta_acc = acc_within - acc_cross
    delta_mse = mse_cross - mse_within

    print(f"    Within-subject ACC: {acc_within:.3f}")
    print(f"    Within-subject MSE: {mse_within:.2f}°²")
    print(f"    ΔACC: {delta_acc:.3f} (within - cross)")
    print(f"    ΔMSE: {delta_mse:.2f}°² (cross - within)")

    # ========================================================================
    # Return results
    # ========================================================================
    results = {
        'test_subject': test_subject,
        'train_subjects': train_subjects,
        'n_voxels': n_selected,
        'n_train_samples': len(amplitudes_train),
        'n_test_samples': len(test_amp_flat),
        'acc_cross': acc_cross,
        'acc_within': acc_within,
        'delta_acc': delta_acc,
        'mse_cross': mse_cross,
        'mse_within': mse_within,
        'delta_mse': delta_mse,
        'mae_cross': mae_cross,
        'W_matrix': decoder.W.T,  # Save W matrix for this fold
        'labels_true': labels_true,
        'labels_pred': labels_pred,
        'hues_true': test_hues_repeated,
        'hues_pred': hues_pred,
    }

    return results

# ============================================================================
# Visualization
# ============================================================================

def plot_loso_summary(all_results, output_dir):
    """LOSO 결과 요약 plot"""
    subjects = [r['test_subject'] for r in all_results]
    acc_cross = [r['acc_cross'] for r in all_results]
    acc_within = [r['acc_within'] for r in all_results]
    delta_acc = [r['delta_acc'] for r in all_results]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Accuracy comparison
    ax = axes[0]
    x = np.arange(len(subjects))
    width = 0.35

    ax.bar(x - width/2, acc_within, width, label='Within-subject', alpha=0.8, color='steelblue')
    ax.bar(x + width/2, acc_cross, width, label='Cross-subject', alpha=0.8, color='coral')

    ax.set_ylabel('Classification Accuracy', fontsize=12)
    ax.set_xlabel('Test Subject', fontsize=12)
    ax.set_title('Within-Subject vs Cross-Subject Decoding', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.axhline(0.125, color='gray', linestyle='--', label='Chance (12.5%)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # ΔACC
    ax = axes[1]
    colors = ['green' if d < 0.1 else 'orange' if d < 0.2 else 'red' for d in delta_acc]
    ax.bar(range(len(subjects)), delta_acc, color=colors, alpha=0.8)
    ax.set_ylabel('ΔACC (Within - Cross)', fontsize=12)
    ax.set_xlabel('Test Subject', fontsize=12)
    ax.set_title('Generalization Performance\n(Lower = Better generalization)', fontweight='bold')
    ax.set_xticks(range(len(subjects)))
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.axhline(0.1, color='green', linestyle='--', alpha=0.5, label='Good (<10%)')
    ax.axhline(0.2, color='orange', linestyle='--', alpha=0.5, label='Moderate (10-20%)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'loso_summary.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ LOSO summary: {fig_path}")

def plot_confusion_matrices(all_results, output_dir):
    """각 fold의 confusion matrix"""
    n_folds = len(all_results)
    n_cols = 3
    n_rows = (n_folds + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 5 * n_rows))
    axes = axes.flatten()

    for idx, results in enumerate(all_results):
        ax = axes[idx]

        cm = confusion_matrix(results['labels_true'], results['labels_pred'],
                             labels=range(N_COLORS))
        cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

        im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1, aspect='auto')

        color_labels = [f'C{i+1}' for i in range(N_COLORS)]
        ax.set_xticks(range(N_COLORS))
        ax.set_yticks(range(N_COLORS))
        ax.set_xticklabels(color_labels, fontsize=8)
        ax.set_yticklabels(color_labels, fontsize=8)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')
        ax.set_title(f"sub-{results['test_subject']}\nACC={results['acc_cross']:.2f}",
                    fontweight='bold')

        plt.colorbar(im, ax=ax, fraction=0.046)

    for idx in range(n_folds, len(axes)):
        axes[idx].axis('off')

    plt.suptitle('Cross-Subject Decoding: Confusion Matrices',
                fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()

    fig_path = output_dir / 'confusion_matrices.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Confusion matrices: {fig_path}")

# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Phase 1C: Cross-Subject Decoding (LOSO)")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Subjects: {', '.join(args.subjects)}")
    print(f"N channels: {args.n_channels}\n")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/cross_subject")
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'w_matrices').mkdir(exist_ok=True)
    print(f"Output: {output_dir}\n")

    # ========================================================================
    # Load all subjects' data
    # ========================================================================
    print(f"Loading amplitudes from all subjects...")
    data_dict = {}
    hues_dict = {}

    for subject_id in args.subjects:
        try:
            amplitudes, hues, _ = load_subject_amplitudes(
                subject_id, args.roi, args.timestamp, args.dataset
            )
            data_dict[subject_id] = amplitudes
            hues_dict[subject_id] = hues
            print(f"  sub-{subject_id}: {amplitudes.shape}")
        except Exception as e:
            print(f"  ✗ sub-{subject_id}: {e}")

    subjects = list(data_dict.keys())
    print(f"\n✅ Loaded {len(subjects)} subjects\n")

    # ========================================================================
    # Run LOSO cross-validation
    # ========================================================================
    print(f"{'='*80}")
    print(f"Running LOSO cross-validation ({len(subjects)} folds)...")
    print(f"{'='*80}")

    all_results = []

    for test_subject in subjects:
        train_subjects = [s for s in subjects if s != test_subject]

        results = run_loso_fold(
            train_subjects, test_subject,
            data_dict, hues_dict,
            n_channels=args.n_channels
        )

        all_results.append(results)

        # Save W matrix for this fold
        np.save(output_dir / 'w_matrices' / f'fold_test_{test_subject}.npy',
               results['W_matrix'])

    # ========================================================================
    # Summary statistics
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"LOSO Summary Statistics")
    print(f"{'='*80}")

    acc_cross_all = [r['acc_cross'] for r in all_results]
    acc_within_all = [r['acc_within'] for r in all_results]
    delta_acc_all = [r['delta_acc'] for r in all_results]
    mse_cross_all = [r['mse_cross'] for r in all_results]
    mse_within_all = [r['mse_within'] for r in all_results]
    delta_mse_all = [r['delta_mse'] for r in all_results]

    print(f"\nCross-Subject Decoding:")
    print(f"  ACC: {np.mean(acc_cross_all):.3f} ± {np.std(acc_cross_all):.3f}")
    print(f"  MSE: {np.mean(mse_cross_all):.2f} ± {np.std(mse_cross_all):.2f}°²")

    print(f"\nWithin-Subject Decoding:")
    print(f"  ACC: {np.mean(acc_within_all):.3f} ± {np.std(acc_within_all):.3f}")
    print(f"  MSE: {np.mean(mse_within_all):.2f} ± {np.std(mse_within_all):.2f}°²")

    print(f"\nGeneralization (ΔACC = Within - Cross):")
    print(f"  Mean ΔACC: {np.mean(delta_acc_all):.3f} ± {np.std(delta_acc_all):.3f}")
    print(f"  Mean ΔMSE: {np.mean(delta_mse_all):.2f} ± {np.std(delta_mse_all):.2f}°²")

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Saving results...")
    print(f"{'='*80}")

    # Per-fold results
    results_df = pd.DataFrame([{
        'test_subject': r['test_subject'],
        'train_subjects': ','.join(r['train_subjects']),
        'n_voxels': r['n_voxels'],
        'acc_cross': r['acc_cross'],
        'acc_within': r['acc_within'],
        'delta_acc': r['delta_acc'],
        'mse_cross': r['mse_cross'],
        'mse_within': r['mse_within'],
        'delta_mse': r['delta_mse'],
    } for r in all_results])

    results_df.to_csv(output_dir / 'loso_performance.csv', index=False)
    print(f"  ✓ loso_performance.csv")

    # Summary statistics
    with open(output_dir / 'loso_summary.txt', 'w') as f:
        f.write(f"Phase 1C: Cross-Subject Decoding (LOSO)\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"ROI: {args.roi}\n")
        f.write(f"Timestamp: {args.timestamp}\n")
        f.write(f"Subjects: {', '.join(subjects)}\n")
        f.write(f"N channels: {args.n_channels}\n\n")
        f.write(f"Cross-Subject Decoding:\n")
        f.write(f"  ACC: {np.mean(acc_cross_all):.3f} ± {np.std(acc_cross_all):.3f}\n")
        f.write(f"  MSE: {np.mean(mse_cross_all):.2f} ± {np.std(mse_cross_all):.2f}°²\n\n")
        f.write(f"Within-Subject Decoding:\n")
        f.write(f"  ACC: {np.mean(acc_within_all):.3f} ± {np.std(acc_within_all):.3f}\n")
        f.write(f"  MSE: {np.mean(mse_within_all):.2f} ± {np.std(mse_within_all):.2f}°²\n\n")
        f.write(f"Generalization:\n")
        f.write(f"  Mean ΔACC: {np.mean(delta_acc_all):.3f} ± {np.std(delta_acc_all):.3f}\n")
        f.write(f"  Mean ΔMSE: {np.mean(delta_mse_all):.2f} ± {np.std(delta_mse_all):.2f}°²\n\n")
        f.write(f"Interpretation:\n")
        if np.mean(delta_acc_all) < 0.1:
            f.write(f"  ✅ STRONG generalization - HC share common encoding\n")
        elif np.mean(delta_acc_all) < 0.2:
            f.write(f"  ⚠️  MODERATE generalization - Some subject variability\n")
        else:
            f.write(f"  ❌ WEAK generalization - Subject-specific encoding\n")

    print(f"  ✓ loso_summary.txt")
    print(f"  ✓ W matrices saved in w_matrices/")

    # ========================================================================
    # Visualization
    # ========================================================================
    print(f"\nCreating visualizations...")
    plot_loso_summary(all_results, output_dir)
    plot_confusion_matrices(all_results, output_dir)

    # ========================================================================
    # Final summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Phase 1C Complete!")
    print(f"{'='*80}")
    print(f"Results: {output_dir}")
    print(f"\nKey findings:")
    print(f"  Mean ΔACC: {np.mean(delta_acc_all):.3f}")

    if np.mean(delta_acc_all) < 0.1:
        print(f"\n✅ STRONG generalization - HC share common encoding system")
        print(f"   → Proceed to Phase 3 (Group GLM) and Phase 2B (HC→CVD)")
    elif np.mean(delta_acc_all) < 0.2:
        print(f"\n⚠️  MODERATE generalization - Some HC consistency")
        print(f"   → Phase 3 and 2B feasible but may show limitations")
    else:
        print(f"\n❌ WEAK generalization - Subject-specific encoding")
        print(f"   → Group-level modeling may be challenging")

if __name__ == '__main__':
    main()
