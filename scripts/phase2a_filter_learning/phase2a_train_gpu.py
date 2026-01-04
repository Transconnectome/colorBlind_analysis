#!/usr/bin/env python3
"""
Phase 2A: GPU 버전 (PyTorch)

Usage:
    python phase2a_train_gpu.py --subject 08 --roi V1 --option D --gpu 0
"""

import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import argparse

# 경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

SUBJECT_WEIGHTS = {
    '08': (0.2, 0.3, 0.5),
    '09': (0.5, 0.3, 0.2),
    '10': (0.5, 0.3, 0.2),
}

# 하이퍼파라미터
LEARNING_RATE = 1e-3
MAX_EPOCHS = 1000
ALPHA = 0.01
BETA = 0.01
EARLY_STOP_PATIENCE = 50


class LinearTransform(nn.Module):
    """선형 변환 모델: F = Y @ A + b"""

    def __init__(self, n_voxels, device='cpu'):
        super().__init__()
        self.device = device

        # 항등 변환으로 초기화
        self.A = nn.Parameter(torch.eye(n_voxels, dtype=torch.float32, device=device))
        self.b = nn.Parameter(torch.zeros(n_voxels, dtype=torch.float32, device=device))

    def forward(self, Y):
        """
        Y: (8, n_voxels)
        Returns: F (8, n_voxels)
        """
        return Y @ self.A + self.b


def magnitude_loss(F, H):
    """L_mag: 색별 L2 norm 매칭"""
    norm_F = torch.norm(F, dim=1)
    norm_H = torch.norm(H, dim=1)
    return torch.mean((norm_F - norm_H)**2)


def baseline_loss(F, H):
    """L_base: 색별 평균 매칭"""
    mean_F = torch.mean(F, dim=1)
    mean_H = torch.mean(H, dim=1)
    return torch.mean((mean_F - mean_H)**2)


def angular_loss(F, H):
    """Option A: Per-color angular distance"""
    n_colors = F.shape[0]
    angles_squared = []

    for i in range(n_colors):
        f_norm = torch.norm(F[i])
        h_norm = torch.norm(H[i])

        if f_norm > 1e-10 and h_norm > 1e-10:
            f_unit = F[i] / f_norm
            h_unit = H[i] / h_norm
            cos_sim = torch.dot(f_unit, h_unit)
            cos_sim = torch.clamp(cos_sim, -1.0, 1.0)
            angle = torch.acos(cos_sim)
            angles_squared.append(angle**2)
        else:
            angles_squared.append(torch.tensor(0.0, device=F.device))

    return torch.mean(torch.stack(angles_squared))


def variance_decomposition_loss(F, H):
    """Option B: Variance decomposition"""
    n_colors = F.shape[0]
    angular_terms = []

    for i in range(n_colors):
        f_norm = torch.norm(F[i])
        h_norm = torch.norm(H[i])

        if f_norm > 1e-10 and h_norm > 1e-10:
            cos_sim = torch.dot(F[i], H[i]) / (f_norm * h_norm)
            cos_sim = torch.clamp(cos_sim, -1.0, 1.0)
            angular_term = 2 * f_norm * h_norm * (1 - cos_sim)
            angular_terms.append(angular_term)
        else:
            angular_terms.append(torch.tensor(0.0, device=F.device))

    return torch.sum(torch.stack(angular_terms))


def rdm_loss(F, H):
    """Option D: RDM-based"""
    def compute_rdm(patterns):
        n_colors = patterns.shape[0]
        patterns_centered = patterns - patterns.mean(dim=1, keepdim=True)
        rdm = torch.zeros(n_colors, n_colors, device=patterns.device)

        for i in range(n_colors):
            for j in range(n_colors):
                if i == j:
                    rdm[i, j] = 0.0
                else:
                    vi = patterns_centered[i]
                    vj = patterns_centered[j]
                    norm_i = torch.norm(vi)
                    norm_j = torch.norm(vj)

                    if norm_i > 1e-10 and norm_j > 1e-10:
                        corr = torch.dot(vi, vj) / (norm_i * norm_j)
                    else:
                        corr = torch.tensor(0.0, device=patterns.device)

                    rdm[i, j] = 1 - corr

        return rdm

    rdm_F = compute_rdm(F)
    rdm_H = compute_rdm(H)
    return torch.norm(rdm_F - rdm_H, p='fro')**2


def get_structure_loss_fn(option):
    """구조 손실 함수 선택"""
    if option == 'A':
        return angular_loss, 'Angular Distance'
    elif option == 'B':
        return variance_decomposition_loss, 'Variance Decomposition'
    elif option == 'D':
        return rdm_loss, 'RDM-Based'
    else:
        raise ValueError(f"Invalid option: {option}")


def three_component_loss(F, H, weights, model, structure_loss_fn, alpha=ALPHA, beta=BETA):
    """완전 손실 함수"""
    lambda_mag, lambda_base, lambda_struct = weights

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_struct = structure_loss_fn(F, H)

    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_struct * l_struct

    # 정규화
    n = model.A.shape[0]
    I = torch.eye(n, device=model.A.device)
    reg_A = alpha * torch.norm(model.A - I, p='fro')**2
    reg_b = beta * torch.norm(model.b)**2

    loss = loss + reg_A + reg_b

    components = {
        'magnitude': l_mag.item(),
        'baseline': l_base.item(),
        'structure': l_struct.item(),
        'total': loss.item()
    }

    return loss, components


def train_model(subject_id, roi, option='D', gpu=0, use_gpu=True):
    """GPU 학습"""
    print("=" * 70)
    print(f"Phase 2A GPU: Training sub-{subject_id} {roi}")
    print(f"Option: {option}")
    print("=" * 70)

    # GPU 설정
    if use_gpu and torch.cuda.is_available():
        device = torch.device(f'cuda:{gpu}')
        print(f"Using GPU: {gpu}")
    else:
        device = torch.device('cpu')
        print(f"Using CPU")

    # 구조 손실 함수
    structure_loss_fn, structure_name = get_structure_loss_fn(option)
    print(f"Structure Loss: {structure_name}")

    # 출력 디렉토리
    if option == 'D':
        OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/models_gpu"
    else:
        OUTPUT_DIR = BASE_DIR / f"results/group_level/phase2a_data/models_gpu_option{option}"

    # 패턴 로드
    cvd_file = PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy"
    hc_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"

    print(f"\nLoading patterns...")
    Y_np = np.load(cvd_file)
    H_np = np.load(hc_file)

    # 복셀 수 맞추기
    min_voxels = min(Y_np.shape[1], H_np.shape[1])
    Y_np = Y_np[:, :min_voxels]
    H_np = H_np[:, :min_voxels]

    # Tensor 변환
    Y = torch.from_numpy(Y_np).float().to(device)
    H = torch.from_numpy(H_np).float().to(device)

    print(f"  Y shape: {Y.shape}")
    print(f"  H shape: {H.shape}")
    print(f"  Device: {device}")

    # 가중치
    weights = SUBJECT_WEIGHTS[subject_id]
    print(f"  Weights: λ_mag={weights[0]}, λ_base={weights[1]}, λ_struct={weights[2]}")

    # 모델 초기화
    n_voxels = Y.shape[1]
    model = LinearTransform(n_voxels, device=device)

    # 옵티마이저
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print(f"\nStarting optimization...")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Max epochs: {MAX_EPOCHS}")

    # 학습 루프
    history = []
    best_loss = float('inf')
    patience_counter = 0

    for epoch in range(MAX_EPOCHS):
        optimizer.zero_grad()

        # Forward
        F = model(Y)

        # Loss
        loss, components = three_component_loss(
            F, H, weights, model, structure_loss_fn, ALPHA, BETA
        )

        # Backward
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        # 기록
        history.append(components)

        # 로깅
        if epoch % 10 == 0:
            print(f"Epoch {epoch:4d}: Loss={components['total']:.6f} "
                  f"(mag={components['magnitude']:.6f}, "
                  f"base={components['baseline']:.6f}, "
                  f"struct={components['structure']:.6f})")

        # Early stopping
        current_loss = components['total']
        if current_loss < best_loss:
            best_loss = current_loss
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= EARLY_STOP_PATIENCE:
            if epoch >= 100:
                recent = [h['total'] for h in history[-EARLY_STOP_PATIENCE:]]
                if max(recent) - min(recent) < 1e-5:
                    print(f"\nConverged at epoch {epoch}")
                    break

    print(f"\nOptimization complete!")
    print(f"  Epochs: {len(history)}")
    print(f"  Final loss: {history[-1]['total']:.6f}")
    print(f"    Magnitude: {history[-1]['magnitude']:.6f}")
    print(f"    Baseline: {history[-1]['baseline']:.6f}")
    print(f"    Structure: {history[-1]['structure']:.6f}")

    # 저장
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    A_final = model.A.detach().cpu().numpy()
    b_final = model.b.detach().cpu().numpy()

    np.save(output_dir / "A_matrix.npy", A_final)
    np.save(output_dir / "b_vector.npy", b_final)

    print(f"\nSaved:")
    print(f"  {output_dir / 'A_matrix.npy'}")
    print(f"  {output_dir / 'b_vector.npy'}")

    # 히스토리 저장
    history_file = output_dir / "loss_history.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    # 메타데이터
    metadata = {
        'subject': subject_id,
        'roi': roi,
        'structure_loss_option': f'{option} ({structure_name})',
        'weights': {
            'lambda_mag': weights[0],
            'lambda_base': weights[1],
            'lambda_struct': weights[2]
        },
        'hyperparameters': {
            'learning_rate': LEARNING_RATE,
            'max_epochs': MAX_EPOCHS,
            'alpha': ALPHA,
            'beta': BETA
        },
        'final_loss': history[-1],
        'n_epochs': len(history),
        'device': str(device),
        'trained_date': datetime.now().isoformat()
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # 손실 곡선 플롯
    if len(history) >= 2:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        epochs = range(len(history))

        ax.plot(epochs, [h['total'] for h in history], 'k-', linewidth=2, label='Total')
        ax.plot(epochs, [h['magnitude'] for h in history], 'r-', linewidth=1.5, label='Magnitude')
        ax.plot(epochs, [h['baseline'] for h in history], 'g-', linewidth=1.5, label='Baseline')
        ax.plot(epochs, [h['structure'] for h in history], 'b-', linewidth=1.5, label=f'Structure')

        ax.set_xlabel('Epoch', fontsize=12)
        ax.set_ylabel('Loss', fontsize=12)
        ax.set_title(f'sub-{subject_id} {roi} - Option {option} (GPU)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plot_file = output_dir / "loss_curve.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  {plot_file}")

    print(f"\nTraining complete!")
    return history[-1]


def main():
    parser = argparse.ArgumentParser(description='Phase 2A: GPU Training')
    parser.add_argument('--subject', type=str, required=True, choices=['08', '09', '10'])
    parser.add_argument('--roi', type=str, required=True, choices=['V1', 'V2', 'V3', 'hV4'])
    parser.add_argument('--option', type=str, default='D', choices=['A', 'B', 'D'])
    parser.add_argument('--gpu', type=int, default=0, help='GPU ID (0-7)')
    parser.add_argument('--cpu', action='store_true', help='Force CPU mode')

    args = parser.parse_args()

    train_model(args.subject, args.roi, args.option, args.gpu, not args.cpu)


if __name__ == "__main__":
    main()
