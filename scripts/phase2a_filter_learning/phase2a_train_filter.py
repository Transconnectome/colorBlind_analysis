#!/usr/bin/env python3
"""
Phase 2A: 필터 학습

선형 변환 학습: F = Y @ A + b
3요소 손실 함수: Magnitude + Baseline + RDM
"""

import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import json
import matplotlib.pyplot as plt
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/models"

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']  # 우선 V1, V2만
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# 피험자별 초기 가중치 (Phase 1 분석 기반)
SUBJECT_WEIGHTS = {
    '08': (0.2, 0.3, 0.5),  # (λ_mag, λ_base, λ_rdm) - Structure-dominant
    '09': (0.5, 0.3, 0.2),  # Magnitude-dominant
    '10': (0.5, 0.3, 0.2),  # Magnitude-dominant
}

# 하이퍼파라미터
LEARNING_RATE = 1e-3
MAX_EPOCHS = 1000
ALPHA = 0.01  # A 정규화
BETA = 0.01   # b 정규화
EARLY_STOP_PATIENCE = 50


class LinearTransform(nn.Module):
    """선형 변환 모델: F = Y @ A + b"""

    def __init__(self, n_voxels):
        super().__init__()
        # 항등 변환으로 초기화
        self.A = nn.Parameter(torch.eye(n_voxels, dtype=torch.float32))
        self.b = nn.Parameter(torch.zeros(n_voxels, dtype=torch.float32))

    def forward(self, Y):
        """
        Y: (8, n_voxels) - CVD 패턴
        Returns: F (8, n_voxels) - 변환된 패턴
        """
        return Y @ self.A + self.b


def magnitude_loss(F, H):
    """L_mag: 색별 L2 norm 매칭"""
    norm_F = torch.norm(F, dim=1)  # (8,)
    norm_H = torch.norm(H, dim=1)  # (8,)
    return torch.mean((norm_F - norm_H)**2)


def baseline_loss(F, H):
    """L_base: 색별 평균 매칭"""
    mean_F = torch.mean(F, dim=1)  # (8,)
    mean_H = torch.mean(H, dim=1)  # (8,)
    return torch.mean((mean_F - mean_H)**2)


def rdm_loss(F, H):
    """L_rdm: 평균-중심화 RDM 매칭"""

    def compute_rdm(patterns):
        """patterns: (8, n_voxels) → RDM: (8, 8)"""
        n_colors = patterns.shape[0]

        # 평균 중심화
        patterns_centered = patterns - patterns.mean(dim=1, keepdim=True)

        # RDM 계산
        rdm = torch.zeros(n_colors, n_colors, device=patterns.device)
        for i in range(n_colors):
            for j in range(n_colors):
                if i == j:
                    rdm[i, j] = 0.0
                else:
                    vi = patterns_centered[i]
                    vj = patterns_centered[j]

                    # Pearson correlation
                    corr = torch.dot(vi, vj) / (
                        torch.norm(vi) * torch.norm(vj) + 1e-10
                    )
                    rdm[i, j] = 1 - corr

        return rdm

    rdm_F = compute_rdm(F)
    rdm_H = compute_rdm(H)

    return torch.norm(rdm_F - rdm_H, p='fro')**2


def three_component_loss(F, H, weights, A=None, b=None, alpha=0.01, beta=0.01):
    """
    완전 손실 함수 (정규화 포함)

    Returns:
    --------
    loss : torch.Tensor (scalar)
    components : dict
    """
    lambda_mag, lambda_base, lambda_rdm = weights

    # 3가지 손실 계산
    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_rdm = rdm_loss(F, H)

    # 가중 합
    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_rdm * l_rdm

    # 정규화 (작은 변형 유도)
    if A is not None:
        n = A.shape[0]
        I = torch.eye(n, device=A.device)
        reg_A = alpha * torch.norm(A - I, p='fro')**2
        loss = loss + reg_A

    if b is not None:
        reg_b = beta * torch.norm(b)**2
        loss = loss + reg_b

    # 개별 손실 저장
    components = {
        'magnitude': l_mag.item(),
        'baseline': l_base.item(),
        'rdm': l_rdm.item(),
        'total': loss.item()
    }

    return loss, components


def train_transformation(Y, H, weights, subject_id, roi, n_epochs=MAX_EPOCHS, lr=LEARNING_RATE):
    """
    변환 학습

    Returns:
    --------
    model : LinearTransform
    history : list of dict
    """
    print(f"\n{'='*70}")
    print(f"Training: sub-{subject_id} {roi}")
    print(f"Weights: λ_mag={weights[0]}, λ_base={weights[1]}, λ_rdm={weights[2]}")
    print(f"{'='*70}")

    # Tensor 변환
    Y_tensor = torch.from_numpy(Y).float()
    H_tensor = torch.from_numpy(H).float()

    # 모델 초기화
    n_voxels = Y.shape[1]
    model = LinearTransform(n_voxels)

    # 옵티마이저
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # 학습 루프
    history = []
    best_loss = float('inf')
    patience_counter = 0

    for epoch in range(n_epochs):
        optimizer.zero_grad()

        # Forward
        F = model(Y_tensor)

        # Loss
        loss, components = three_component_loss(
            F, H_tensor, weights,
            A=model.A, b=model.b,
            alpha=ALPHA, beta=BETA
        )

        # Backward
        loss.backward()
        optimizer.step()

        # 기록
        history.append(components)

        # 로깅
        if epoch % 100 == 0:
            print(f"Epoch {epoch:4d}: Loss={components['total']:.6f} "
                  f"(mag={components['magnitude']:.6f}, "
                  f"base={components['baseline']:.6f}, "
                  f"rdm={components['rdm']:.6f})")

        # Early stopping
        current_loss = components['total']
        if current_loss < best_loss:
            best_loss = current_loss
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= EARLY_STOP_PATIENCE:
            if epoch >= 50:
                recent = [h['total'] for h in history[-EARLY_STOP_PATIENCE:]]
                if max(recent) - min(recent) < 1e-5:
                    print(f"\nConverged at epoch {epoch}")
                    break

    print(f"\nFinal loss: {history[-1]['total']:.6f}")
    print(f"  Magnitude: {history[-1]['magnitude']:.6f}")
    print(f"  Baseline: {history[-1]['baseline']:.6f}")
    print(f"  RDM: {history[-1]['rdm']:.6f}")

    return model, history


def save_model(model, history, subject_id, roi, weights):
    """모델 및 결과 저장"""
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # A, b 저장
    A = model.A.detach().cpu().numpy()
    b = model.b.detach().cpu().numpy()

    np.save(output_dir / "A_matrix.npy", A)
    np.save(output_dir / "b_vector.npy", b)

    print(f"  Saved: {output_dir / 'A_matrix.npy'}")
    print(f"  Saved: {output_dir / 'b_vector.npy'}")

    # 히스토리 저장
    history_file = output_dir / "loss_history.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    # 메타데이터
    metadata = {
        'subject': subject_id,
        'roi': roi,
        'weights': {
            'lambda_mag': weights[0],
            'lambda_base': weights[1],
            'lambda_rdm': weights[2]
        },
        'hyperparameters': {
            'learning_rate': LEARNING_RATE,
            'max_epochs': MAX_EPOCHS,
            'alpha': ALPHA,
            'beta': BETA
        },
        'final_loss': history[-1],
        'n_epochs': len(history),
        'trained_date': datetime.now().isoformat()
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # 손실 곡선 플롯
    plot_loss_curve(history, output_dir, subject_id, roi)

    # A, b 히트맵
    plot_transformation(A, b, output_dir, subject_id, roi)


def plot_loss_curve(history, output_dir, subject_id, roi):
    """손실 곡선 플롯"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    epochs = range(len(history))

    # Total loss
    axes[0, 0].plot(epochs, [h['total'] for h in history], 'k-', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Total Loss')
    axes[0, 0].set_title('Total Loss')
    axes[0, 0].grid(True, alpha=0.3)

    # Magnitude loss
    axes[0, 1].plot(epochs, [h['magnitude'] for h in history], 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Magnitude Loss')
    axes[0, 1].set_title('Magnitude Loss')
    axes[0, 1].grid(True, alpha=0.3)

    # Baseline loss
    axes[1, 0].plot(epochs, [h['baseline'] for h in history], 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Baseline Loss')
    axes[1, 0].set_title('Baseline Loss')
    axes[1, 0].grid(True, alpha=0.3)

    # RDM loss
    axes[1, 1].plot(epochs, [h['rdm'] for h in history], 'b-', linewidth=2)
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('RDM Loss')
    axes[1, 1].set_title('RDM Loss')
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle(f'sub-{subject_id} {roi} Training Loss', fontsize=14, fontweight='bold')
    plt.tight_layout()

    plot_file = output_dir / "loss_curve.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Saved: {plot_file}")


def plot_transformation(A, b, output_dir, subject_id, roi):
    """A, b 시각화"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # A diagonal (voxel-wise gain)
    diag_A = np.diag(A)
    axes[0].hist(diag_A, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    axes[0].axvline(1.0, color='red', linestyle='--', linewidth=2, label='Identity (1.0)')
    axes[0].set_xlabel('Gain', fontsize=12)
    axes[0].set_ylabel('Count', fontsize=12)
    axes[0].set_title(f'A Diagonal Distribution\n(mean={diag_A.mean():.3f}, std={diag_A.std():.3f})', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # b distribution
    axes[1].hist(b, bins=50, color='coral', alpha=0.7, edgecolor='black')
    axes[1].axvline(0.0, color='red', linestyle='--', linewidth=2, label='Zero')
    axes[1].set_xlabel('Baseline Shift', fontsize=12)
    axes[1].set_ylabel('Count', fontsize=12)
    axes[1].set_title(f'b Vector Distribution\n(mean={b.mean():.3f}, std={b.std():.3f})', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # A heatmap (sample)
    n_sample = min(100, A.shape[0])
    A_sample = A[:n_sample, :n_sample]
    im = axes[2].imshow(A_sample, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    axes[2].set_xlabel('Voxel Index', fontsize=12)
    axes[2].set_ylabel('Voxel Index', fontsize=12)
    axes[2].set_title(f'A Matrix (first {n_sample}×{n_sample})', fontsize=12)
    plt.colorbar(im, ax=axes[2])

    plt.suptitle(f'sub-{subject_id} {roi} Learned Transformation', fontsize=14, fontweight='bold')
    plt.tight_layout()

    plot_file = output_dir / "transformation_visualization.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Saved: {plot_file}")


def main():
    """메인 실행"""
    print("=" * 70)
    print("Phase 2A: Training Filters")
    print("=" * 70)
    print(f"\nHyperparameters:")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Max epochs: {MAX_EPOCHS}")
    print(f"  Regularization: α={ALPHA}, β={BETA}")
    print(f"  Early stopping patience: {EARLY_STOP_PATIENCE}")

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    for subject_id in CVD_SUBJECTS:
        for roi in ROIS:
            # 패턴 로드
            cvd_file = PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy"
            hc_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"

            if not cvd_file.exists() or not hc_file.exists():
                print(f"\nWarning: Pattern files not found for sub-{subject_id} {roi}")
                continue

            Y = np.load(cvd_file)  # (8, n_voxels)
            H = np.load(hc_file)   # (8, n_voxels)

            # 가중치
            weights = SUBJECT_WEIGHTS[subject_id]

            # 학습
            model, history = train_transformation(Y, H, weights, subject_id, roi)

            # 저장
            save_model(model, history, subject_id, roi, weights)

            # 결과 기록
            all_results.append({
                'subject': subject_id,
                'roi': roi,
                'final_loss': history[-1]['total'],
                'magnitude_loss': history[-1]['magnitude'],
                'baseline_loss': history[-1]['baseline'],
                'rdm_loss': history[-1]['rdm'],
                'n_epochs': len(history)
            })

    # 전체 요약
    print("\n" + "="*70)
    print("Training Summary")
    print("="*70)

    import pandas as pd
    results_df = pd.DataFrame(all_results)
    print(results_df.to_string(index=False))

    summary_file = OUTPUT_DIR / "training_summary.csv"
    results_df.to_csv(summary_file, index=False, float_format='%.6f')

    print(f"\nSummary saved: {summary_file}")
    print(f"Models saved in: {OUTPUT_DIR}")

    print("\n" + "="*70)
    print("Training complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. Evaluate: python phase2a_evaluate.py")
    print("2. Compare with Phase 1 metrics")
    print("3. Run ablation study (different loss options)")


if __name__ == "__main__":
    main()
