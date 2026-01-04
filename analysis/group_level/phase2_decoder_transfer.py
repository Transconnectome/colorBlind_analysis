#!/usr/bin/env python3
"""
phase2_decoder_transfer.py
==========================

Phase 2B: HC→CVD Decoder Transfer

**핵심 질문**: HC로 학습한 decoder가 CVD에 적용 가능한가?

**방법**:
1. HC 6명 전체 데이터로 group decoder 학습
   - Voxel selection: HC common voxels (Phase 1A 결과 사용 가능)
   - W matrix 학습: pooled HC data
2. CVD 3명에게 같은 decoder 적용
   - 같은 voxel 위치
   - 같은 W matrix (재학습 없음!)
3. CVD individual decoder와 비교

**주요 지표**:
- ΔACC_CVD = ACC_HC_decoder - ACC_CVD_individual
  - < 15%: HC decoder 적용 가능 → 필터 설계 feasible
  - 15-30%: 보통
  - > 30%: HC decoder 실패 → 다른 mapping

- Per-color error: 어느 색상이 문제?
  - 특히 red-green axis (90° vs 270°) 확인

Usage:
    python analysis/group_level/phase2_decoder_transfer.py \
        --roi V1 \
        --timestamp baseline32_deob_determin \
        --hc-subjects 01 02 03 05 06 07 \
        --cvd-subjects 08 09 10

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
    create_basis_functions, circular_diff_deg
)

# Import ColorDecoder from Phase 1C
# (또는 여기서 다시 정의)
class ColorDecoder:
    """
    6-channel forward encoding model

    **핵심**: Training에서 학습한 W matrix를 그대로 사용하여
    새로운 subject의 데이터에 적용
    """
    def __init__(self, n_channels=6):
        self.n_channels = n_channels
        self.W = None
        self.basis = create_basis_functions(n_channels)

    def _get_channel_responses(self, hues):
        hues_int = np.round(hues).astype(int) % 360
        return self.basis[hues_int, :]

    def train(self, amplitudes_train, hues_train):
        """W = pinv(C) @ amplitudes"""
        C_train = self._get_channel_responses(hues_train)
        self.W = np.linalg.pinv(C_train.T) @ amplitudes_train.T
        return self.W

    def predict(self, amplitudes_test):
        """Hue reconstruction"""
        if self.W is None:
            raise RuntimeError("Model not trained!")
        C_pred = amplitudes_test @ self.W.T
        hues_pred = np.zeros(len(C_pred))
        for i, c_pred in enumerate(C_pred):
            corrs = np.dot(self.basis, c_pred)
            hues_pred[i] = np.argmax(corrs)
        return hues_pred

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Phase 2B: HC→CVD Transfer')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline32_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--cvd-subjects', type=str, nargs='+',
                        default=['08', '09', '10'])
    parser.add_argument('--use-common-voxels', action='store_true',
                        help='Use common voxels from Phase 1A')
    parser.add_argument('--scenario', type=str, default=None,
                        choices=['A_all_subjects', 'B_sufficient_voxels'],
                        help='Phase 1A scenario to use (A or B)')
    parser.add_argument('--output-dir', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """피험자의 amplitudes_z 로드"""
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")
    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'
    amplitudes = np.load(amp_file)
    hues = np.array([LABEL2HUE_DEG[f'color_{i+1}'] for i in range(N_COLORS)])
    return amplitudes, hues, result_dir

def load_common_voxels(roi, timestamp, scenario='B_sufficient_voxels'):
    """
    Phase 1A 결과에서 common voxels 로드

    Args:
        roi: ROI name
        timestamp: Analysis timestamp
        scenario: 'A_all_subjects' or 'B_sufficient_voxels'

    Returns:
        common_voxels: (n_voxels,) array 또는 None (파일 없거나 빈 배열)
    """
    voxel_file = Path(f'derivatives/group_level/{timestamp}/{roi}/voxel_overlap/{scenario}/common_voxels_indices.npy')
    if not voxel_file.exists():
        return None

    common_voxels = np.load(voxel_file)

    # 빈 배열이면 None 반환
    if len(common_voxels) == 0:
        print(f"  ⚠️  Common voxels file exists but is empty (0 voxels)")
        return None

    print(f"  ✓ Loaded {len(common_voxels)} common voxels from Phase 1A ({scenario})")
    return common_voxels

# ============================================================================
# HC Group Decoder
# ============================================================================

def train_hc_group_decoder(hc_data_dict, hues_dict, voxel_indices=None, n_channels=6):
    """
    HC 전체로 group decoder 학습

    **절차**:
    1. 모든 HC의 데이터 pooling
    2. 선택된 voxels에서만 사용 (common voxels 또는 전체)
    3. 6-channel model 학습

    Returns:
        decoder: Trained ColorDecoder
        voxel_indices: Used voxel indices
    """
    print(f"\n{'='*80}")
    print(f"Training HC Group Decoder")
    print(f"{'='*80}")

    # Determine voxel selection
    if voxel_indices is None:
        # Use minimum voxels across all HC
        n_voxels_list = [hc_data_dict[sub].shape[2] for sub in hc_data_dict]
        min_voxels = min(n_voxels_list)
        voxel_indices = np.arange(min_voxels, dtype=int)
        print(f"  No voxel selection specified, using first {min_voxels} voxels")
    else:
        # 정수 타입 확인 및 변환
        voxel_indices = np.asarray(voxel_indices, dtype=int)
        print(f"  Using {len(voxel_indices)} pre-selected voxels")

    # Pool all HC data
    amplitudes_list = []
    hues_list = []

    for sub_id in hc_data_dict:
        amp = hc_data_dict[sub_id]  # (n_runs, n_colors, n_voxels)
        n_runs = amp.shape[0]

        # Select voxels
        amp_selected = amp[:, :, voxel_indices]

        # Flatten
        amp_flat = amp_selected.reshape(-1, len(voxel_indices))
        amplitudes_list.append(amp_flat)

        # Hues
        hues = hues_dict[sub_id]
        hues_repeated = np.tile(hues, n_runs)
        hues_list.append(hues_repeated)

    # Stack
    amplitudes_pooled = np.vstack(amplitudes_list)
    hues_pooled = np.concatenate(hues_list)

    print(f"  Pooled training data: {amplitudes_pooled.shape[0]} samples from {len(hc_data_dict)} HC subjects")

    # Train decoder
    decoder = ColorDecoder(n_channels=n_channels)
    decoder.train(amplitudes_pooled, hues_pooled)

    print(f"  ✓ HC group decoder trained (W: {decoder.W.T.shape})")

    return decoder, voxel_indices

# ============================================================================
# CVD Testing
# ============================================================================

def test_decoder_on_cvd(decoder, cvd_amp, cvd_hues, voxel_indices):
    """
    HC decoder를 CVD 데이터에 적용

    **중요**: 같은 voxel 위치, 같은 W matrix 사용!

    Args:
        decoder: Trained ColorDecoder (from HC)
        cvd_amp: (n_runs, n_colors, n_voxels) CVD amplitudes
        cvd_hues: (n_colors,) stimulus hues
        voxel_indices: Which voxels to use

    Returns:
        results: Dict with accuracy, MSE, etc.
    """
    n_runs, n_colors, n_voxels = cvd_amp.shape

    # Select same voxels
    # Check if voxel indices are valid
    max_idx = np.max(voxel_indices)
    if max_idx >= n_voxels:
        print(f"    ⚠️  Warning: Some voxel indices ({max_idx}) exceed CVD voxel count ({n_voxels})")
        print(f"    Using only valid voxels (intersection)")
        voxel_indices = voxel_indices[voxel_indices < n_voxels]

    cvd_amp_selected = cvd_amp[:, :, voxel_indices]

    # Flatten
    cvd_amp_flat = cvd_amp_selected.reshape(-1, len(voxel_indices))
    cvd_hues_repeated = np.tile(cvd_hues, n_runs)

    # Predict using HC decoder
    hues_pred = decoder.predict(cvd_amp_flat)

    # Evaluate
    stimulus_hues = np.array(list(LABEL2HUE_DEG.values()))

    labels_true = []
    labels_pred = []

    for true_hue, pred_hue in zip(cvd_hues_repeated, hues_pred):
        true_label = np.argmin(circular_diff_deg(true_hue, stimulus_hues))
        pred_label = np.argmin(circular_diff_deg(pred_hue, stimulus_hues))
        labels_true.append(true_label)
        labels_pred.append(pred_label)

    labels_true = np.array(labels_true)
    labels_pred = np.array(labels_pred)

    acc = accuracy_score(labels_true, labels_pred)

    # Reconstruction error
    errors = circular_diff_deg(cvd_hues_repeated, hues_pred)
    mse = np.mean(errors ** 2)
    mae = np.mean(errors)

    # Per-color errors
    per_color_errors = {}
    for color_idx in range(n_colors):
        color_mask = labels_true == color_idx
        if color_mask.sum() > 0:
            per_color_errors[color_idx] = np.mean(errors[color_mask])

    results = {
        'acc_hc_decoder': acc,
        'mse_hc_decoder': mse,
        'mae_hc_decoder': mae,
        'labels_true': labels_true,
        'labels_pred': labels_pred,
        'hues_true': cvd_hues_repeated,
        'hues_pred': hues_pred,
        'per_color_errors': per_color_errors,
    }

    return results

def test_cvd_individual_decoder(cvd_amp, cvd_hues, voxel_indices, n_channels=6):
    """
    CVD 개인 decoder 학습 및 테스트 (baseline)

    Leave-one-run-out within CVD subject
    """
    n_runs, n_colors, n_voxels = cvd_amp.shape

    # Select voxels
    valid_voxels = voxel_indices[voxel_indices < n_voxels]
    cvd_amp_selected = cvd_amp[:, :, valid_voxels]

    # LORO
    accs = []
    mses = []

    for run_idx in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != run_idx]

        # Train
        amp_train = cvd_amp_selected[train_runs, :, :].reshape(-1, len(valid_voxels))
        hues_train = np.tile(cvd_hues, len(train_runs))

        decoder = ColorDecoder(n_channels=n_channels)
        decoder.train(amp_train, hues_train)

        # Test
        amp_test = cvd_amp_selected[run_idx, :, :].reshape(-1, len(valid_voxels))
        hues_test = cvd_hues

        hues_pred = decoder.predict(amp_test)

        # Evaluate
        stimulus_hues = np.array(list(LABEL2HUE_DEG.values()))
        labels_true = []
        labels_pred = []
        for true_hue, pred_hue in zip(hues_test, hues_pred):
            true_label = np.argmin(circular_diff_deg(true_hue, stimulus_hues))
            pred_label = np.argmin(circular_diff_deg(pred_hue, stimulus_hues))
            labels_true.append(true_label)
            labels_pred.append(pred_label)

        acc = accuracy_score(labels_true, labels_pred)
        errors = circular_diff_deg(hues_test, hues_pred)
        mse = np.mean(errors ** 2)

        accs.append(acc)
        mses.append(mse)

    results = {
        'acc_cvd_individual': np.mean(accs),
        'mse_cvd_individual': np.mean(mses),
    }

    return results

# ============================================================================
# Visualization
# ============================================================================

def plot_transfer_summary(all_cvd_results, output_dir):
    """HC→CVD transfer 결과 요약"""
    cvd_subjects = list(all_cvd_results.keys())

    acc_hc = [all_cvd_results[sub]['acc_hc_decoder'] for sub in cvd_subjects]
    acc_cvd = [all_cvd_results[sub]['acc_cvd_individual'] for sub in cvd_subjects]
    delta_acc = [all_cvd_results[sub]['delta_acc'] for sub in cvd_subjects]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Accuracy comparison
    ax = axes[0]
    x = np.arange(len(cvd_subjects))
    width = 0.35

    ax.bar(x - width/2, acc_cvd, width, label='CVD Individual', alpha=0.8, color='steelblue')
    ax.bar(x + width/2, acc_hc, width, label='HC Group Decoder', alpha=0.8, color='coral')

    ax.set_ylabel('Classification Accuracy', fontsize=12)
    ax.set_xlabel('CVD Subject', fontsize=12)
    ax.set_title('CVD Individual vs HC Group Decoder', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in cvd_subjects])
    ax.axhline(0.125, color='gray', linestyle='--', label='Chance')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # ΔACC
    ax = axes[1]
    colors = ['green' if abs(d) < 0.15 else 'orange' if abs(d) < 0.30 else 'red'
             for d in delta_acc]
    ax.bar(range(len(cvd_subjects)), delta_acc, color=colors, alpha=0.8)
    ax.set_ylabel('ΔACC (HC - CVD Individual)', fontsize=12)
    ax.set_xlabel('CVD Subject', fontsize=12)
    ax.set_title('Decoder Transfer Performance\n(Near zero = Good transfer)', fontweight='bold')
    ax.set_xticks(range(len(cvd_subjects)))
    ax.set_xticklabels([f'sub-{s}' for s in cvd_subjects])
    ax.axhline(0, color='black', linestyle='-', linewidth=1)
    ax.axhline(0.15, color='green', linestyle='--', alpha=0.5, label='Good (<15%)')
    ax.axhline(-0.15, color='green', linestyle='--', alpha=0.5)
    ax.axhline(0.30, color='orange', linestyle='--', alpha=0.5, label='Moderate (15-30%)')
    ax.axhline(-0.30, color='orange', linestyle='--', alpha=0.5)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'transfer_summary.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Transfer summary: {fig_path}")

def plot_per_color_errors(all_cvd_results, output_dir):
    """색상별 오차 분석 (특히 red-green axis)"""
    cvd_subjects = list(all_cvd_results.keys())
    n_colors = 8

    fig, ax = plt.subplots(figsize=(10, 6))

    color_labels = [f'C{i+1}' for i in range(n_colors)]
    x = np.arange(n_colors)
    width = 0.25

    for idx, sub in enumerate(cvd_subjects):
        per_color_err = all_cvd_results[sub]['per_color_errors']
        errors = [per_color_err.get(i, 0) for i in range(n_colors)]

        ax.bar(x + idx * width, errors, width, label=f'sub-{sub}', alpha=0.8)

    ax.set_ylabel('Mean Absolute Error (degrees)', fontsize=12)
    ax.set_xlabel('Color', fontsize=12)
    ax.set_title('Per-Color Reconstruction Error (HC Decoder on CVD)\nRed-Green axis: C3 (90°) vs C7 (270°)',
                fontweight='bold', pad=15)
    ax.set_xticks(x + width)
    ax.set_xticklabels(color_labels)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Highlight red-green axis
    ax.axvspan(2 - 0.5, 2 + 0.5, alpha=0.1, color='green', label='Green (90°)')
    ax.axvspan(6 - 0.5, 6 + 0.5, alpha=0.1, color='red', label='Red (270°)')

    plt.tight_layout()
    fig_path = output_dir / 'per_color_errors.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Per-color errors: {fig_path}")

# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Phase 2B: HC→CVD Decoder Transfer")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"HC subjects: {', '.join(args.hc_subjects)}")
    print(f"CVD subjects: {', '.join(args.cvd_subjects)}")
    if args.scenario:
        print(f"Scenario: {args.scenario}")
    print()

    # Output directory
    if args.output_dir is None:
        base_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/decoder_transfer")
        if args.scenario:
            output_dir = base_dir / args.scenario
        else:
            output_dir = base_dir
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'hc_group_decoder').mkdir(exist_ok=True)
    print(f"Output: {output_dir}\n")

    # ========================================================================
    # Load HC data
    # ========================================================================
    print(f"Loading HC data...")
    hc_data_dict = {}
    hc_hues_dict = {}

    for subject_id in args.hc_subjects:
        try:
            amplitudes, hues, _ = load_subject_amplitudes(
                subject_id, args.roi, args.timestamp, args.dataset
            )
            hc_data_dict[subject_id] = amplitudes
            hc_hues_dict[subject_id] = hues
            print(f"  HC sub-{subject_id}: {amplitudes.shape}")
        except Exception as e:
            print(f"  ✗ HC sub-{subject_id}: {e}")

    print(f"\n✅ Loaded {len(hc_data_dict)} HC subjects\n")

    # ========================================================================
    # Load CVD data
    # ========================================================================
    print(f"Loading CVD data...")
    cvd_data_dict = {}
    cvd_hues_dict = {}

    for subject_id in args.cvd_subjects:
        try:
            amplitudes, hues, _ = load_subject_amplitudes(
                subject_id, args.roi, args.timestamp, args.dataset
            )
            cvd_data_dict[subject_id] = amplitudes
            cvd_hues_dict[subject_id] = hues
            print(f"  CVD sub-{subject_id}: {amplitudes.shape}")
        except Exception as e:
            print(f"  ✗ CVD sub-{subject_id}: {e}")

    print(f"\n✅ Loaded {len(cvd_data_dict)} CVD subjects\n")

    # ========================================================================
    # Voxel selection (common voxels from Phase 1A if available)
    # ========================================================================
    voxel_indices = None
    if args.use_common_voxels:
        if args.scenario:
            print(f"Loading common voxels from Phase 1A ({args.scenario})...")
            voxel_indices = load_common_voxels(args.roi, args.timestamp, args.scenario)
        else:
            print(f"Loading common voxels from Phase 1A...")
            # Try B first, then A
            voxel_indices = load_common_voxels(args.roi, args.timestamp, 'B_sufficient_voxels')
            if voxel_indices is None:
                voxel_indices = load_common_voxels(args.roi, args.timestamp, 'A_all_subjects')

        if voxel_indices is None:
            print(f"  ⚠️  No common voxels found, using all voxels\n")

    # ========================================================================
    # Train HC group decoder
    # ========================================================================
    hc_decoder, voxel_indices = train_hc_group_decoder(
        hc_data_dict, hc_hues_dict,
        voxel_indices=voxel_indices,
        n_channels=6
    )

    # Save HC decoder
    np.save(output_dir / 'hc_group_decoder' / 'w_matrix.npy', hc_decoder.W.T)
    np.save(output_dir / 'hc_group_decoder' / 'voxel_indices.npy', voxel_indices)
    print(f"  ✓ HC decoder saved\n")

    # ========================================================================
    # Test on CVD subjects
    # ========================================================================
    print(f"{'='*80}")
    print(f"Testing HC Decoder on CVD Subjects")
    print(f"{'='*80}\n")

    all_cvd_results = {}

    for cvd_sub in cvd_data_dict:
        print(f"CVD sub-{cvd_sub}:")

        cvd_amp = cvd_data_dict[cvd_sub]
        cvd_hues = cvd_hues_dict[cvd_sub]

        # Test with HC decoder
        results_hc = test_decoder_on_cvd(hc_decoder, cvd_amp, cvd_hues, voxel_indices)
        print(f"  HC decoder: ACC={results_hc['acc_hc_decoder']:.3f}, MSE={results_hc['mse_hc_decoder']:.2f}°²")

        # Test with CVD individual decoder
        results_cvd = test_cvd_individual_decoder(cvd_amp, cvd_hues, voxel_indices)
        print(f"  CVD individual: ACC={results_cvd['acc_cvd_individual']:.3f}, MSE={results_cvd['mse_cvd_individual']:.2f}°²")

        # Compute delta
        delta_acc = results_hc['acc_hc_decoder'] - results_cvd['acc_cvd_individual']
        delta_mse = results_hc['mse_hc_decoder'] - results_cvd['mse_cvd_individual']

        print(f"  ΔACC: {delta_acc:.3f} (HC - CVD)")
        print(f"  ΔMSE: {delta_mse:.2f}°²\n")

        all_cvd_results[cvd_sub] = {
            **results_hc,
            **results_cvd,
            'delta_acc': delta_acc,
            'delta_mse': delta_mse,
        }

    # ========================================================================
    # Summary
    # ========================================================================
    print(f"{'='*80}")
    print(f"Summary Statistics")
    print(f"{'='*80}\n")

    mean_delta_acc = np.mean([all_cvd_results[sub]['delta_acc'] for sub in cvd_data_dict])
    mean_delta_mse = np.mean([all_cvd_results[sub]['delta_mse'] for sub in cvd_data_dict])

    print(f"Mean ΔACC (HC decoder - CVD individual): {mean_delta_acc:.3f}")
    print(f"Mean ΔMSE: {mean_delta_mse:.2f}°²\n")

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"Saving results...")

    results_df = pd.DataFrame([{
        'cvd_subject': sub,
        'acc_hc_decoder': all_cvd_results[sub]['acc_hc_decoder'],
        'acc_cvd_individual': all_cvd_results[sub]['acc_cvd_individual'],
        'delta_acc': all_cvd_results[sub]['delta_acc'],
        'mse_hc_decoder': all_cvd_results[sub]['mse_hc_decoder'],
        'mse_cvd_individual': all_cvd_results[sub]['mse_cvd_individual'],
        'delta_mse': all_cvd_results[sub]['delta_mse'],
    } for sub in cvd_data_dict])

    results_df.to_csv(output_dir / 'transfer_results.csv', index=False)
    print(f"  ✓ transfer_results.csv")

    # Summary text
    with open(output_dir / 'transfer_summary.txt', 'w') as f:
        f.write(f"Phase 2B: HC→CVD Decoder Transfer\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"ROI: {args.roi}\n")
        f.write(f"HC subjects: {', '.join(list(hc_data_dict.keys()))}\n")
        f.write(f"CVD subjects: {', '.join(list(cvd_data_dict.keys()))}\n")
        f.write(f"Voxels used: {len(voxel_indices)}\n\n")
        f.write(f"Results:\n")
        f.write(f"  Mean ΔACC: {mean_delta_acc:.3f}\n")
        f.write(f"  Mean ΔMSE: {mean_delta_mse:.2f}°²\n\n")
        f.write(f"Interpretation:\n")
        if abs(mean_delta_acc) < 0.15:
            f.write(f"  ✅ HC decoder works on CVD - Same mapping!\n")
            f.write(f"  → Filter design is FEASIBLE\n")
        elif abs(mean_delta_acc) < 0.30:
            f.write(f"  ⚠️  Moderate transfer - Some differences\n")
            f.write(f"  → Filter may need adjustment\n")
        else:
            f.write(f"  ❌ Poor transfer - Different mappings\n")
            f.write(f"  → CVD-specific filter needed\n")

    print(f"  ✓ transfer_summary.txt\n")

    # ========================================================================
    # Visualization
    # ========================================================================
    print(f"Creating visualizations...")
    plot_transfer_summary(all_cvd_results, output_dir)
    plot_per_color_errors(all_cvd_results, output_dir)

    # ========================================================================
    # Final summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Phase 2B Complete!")
    print(f"{'='*80}")
    print(f"Results: {output_dir}")
    print(f"\nKey finding: Mean ΔACC = {mean_delta_acc:.3f}")

    if abs(mean_delta_acc) < 0.15:
        print(f"\n✅ HC decoder transfers to CVD - SAME MAPPING!")
        print(f"   → Color filter design is feasible")
        print(f"   → Use HC W matrix as target for filter optimization")
    elif abs(mean_delta_acc) < 0.30:
        print(f"\n⚠️  Moderate transfer - Mapping partially shared")
        print(f"   → Filter design possible but may need tuning")
    else:
        print(f"\n❌ Poor transfer - DIFFERENT MAPPINGS")
        print(f"   → CVD uses different neural→color mapping")
        print(f"   → Need CVD-specific approach")

if __name__ == '__main__':
    main()
