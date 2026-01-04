#!/usr/bin/env python3
"""
Phase 2A: Hypernetwork 버전

Hypernetwork가 피험자 특성에서 A, b를 생성
Meta-learning approach for personalized transformations

Architecture:
    subject_features → HyperNet → (A, b) → F = Y @ A + b
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

#경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
METRICS_DIR = BASE_DIR / "results/group_level/phase2a_data/metrics"

SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']

# 하이퍼파라미터
LEARNING_RATE = 1e-3
MAX_EPOCHS = 1000
ALPHA = 0.01
BETA = 0.01


class HyperNetwork(nn.Module):
    """
    Hypernetwork: 피험자 특성 → 변환 파라미터 (A, b)

    Input: subject_features (embedding)
    Output: A (n × n), b (n,)
    """

    def __init__(self, n_voxels, feature_dim=16, hidden_dim=64, device='cpu'):
        super().__init__()
        self.n_voxels = n_voxels
        self.feature_dim = feature_dim
        self.device = device

        # Subject embedding (learnable)
        self.subject_embeddings = nn.Embedding(3, feature_dim)  # 3 subjects

        # HyperNet for A matrix
        self.A_net = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_voxels * n_voxels)
        )

        # HyperNet for b vector
        self.b_net = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, n_voxels)
        )

        # Identity 초기화
        self._initialize_identity()

    def _initialize_identity(self):
        """A를 identity에 가깝게, b를 0에 가깝게 초기화"""
        # A_net의 마지막 layer를 작은 값으로
        nn.init.normal_(self.A_net[-1].weight, mean=0.0, std=0.01)
        nn.init.zeros_(self.A_net[-1].bias)

        # b_net의 마지막 layer를 0으로
        nn.init.zeros_(self.b_net[-1].weight)
        nn.init.zeros_(self.b_net[-1].bias)

    def forward(self, subject_idx):
        """
        subject_idx: 0, 1, or 2 (for sub-08, 09, 10)
        Returns: A (n × n), b (n,)
        """
        # Subject embedding
        subject_idx_tensor = torch.tensor([subject_idx], dtype=torch.long, device=self.device)
        features = self.subject_embeddings(subject_idx_tensor)  # (1, feature_dim)

        # Generate A
        A_flat = self.A_net(features)  # (1, n*n)
        A = A_flat.view(self.n_voxels, self.n_voxels)

        # Add identity (residual connection)
        I = torch.eye(self.n_voxels, device=self.device)
        A = I + A  # A ≈ I + small perturbation

        # Generate b
        b = self.b_net(features).squeeze(0)  # (n,)

        return A, b


class HyperTransform(nn.Module):
    """Complete transformation with HyperNet"""

    def __init__(self, n_voxels, feature_dim=16, hidden_dim=64, device='cpu'):
        super().__init__()
        self.hypernet = HyperNetwork(n_voxels, feature_dim, hidden_dim, device)

    def forward(self, Y, subject_idx):
        """
        Y: (8, n_voxels) - CVD pattern
        subject_idx: 0, 1, or 2
        Returns: F (8, n_voxels) - transformed pattern
        """
        A, b = self.hypernet(subject_idx)
        F = Y @ A + b
        return F, A, b


def magnitude_loss(F, H):
    norm_F = torch.norm(F, dim=1)
    norm_H = torch.norm(H, dim=1)
    return torch.mean((norm_F - norm_H)**2)


def baseline_loss(F, H):
    mean_F = torch.mean(F, dim=1)
    mean_H = torch.mean(H, dim=1)
    return torch.mean((mean_F - mean_H)**2)


def rdm_loss(F, H):
    """RDM-based structure loss"""
    def compute_rdm(patterns):
        n_colors = patterns.shape[0]
        patterns_centered = patterns - patterns.mean(dim=1, keepdim=True)
        rdm = torch.zeros(n_colors, n_colors, device=patterns.device)

        for i in range(n_colors):
            for j in range(n_colors):
                if i != j:
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


def train_hypernetwork(gpu=0, use_gpu=True):
    """Hypernetwork 학습 - 모든 피험자 동시에"""
    print("=" * 70)
    print("Phase 2A: Hypernetwork Training")
    print("=" * 70)

    # GPU 설정
    if use_gpu and torch.cuda.is_available():
        device = torch.device(f'cuda:{gpu}')
        print(f"Using GPU: {gpu}")
    else:
        device = torch.device('cpu')
        print(f"Using CPU")

    OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/models_hypernet"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드 (모든 피험자)
    print("\nLoading data...")
    data = {}

    for roi in ROIS:
        # HC pattern
        hc_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"
        H_np = np.load(hc_file)
        H = torch.from_numpy(H_np).float().to(device)

        # CVD patterns
        Y_dict = {}
        for subj in SUBJECTS:
            cvd_file = PATTERN_DIR / f"sub-{subj}" / f"{roi}_pattern.npy"
            Y_np = np.load(cvd_file)

            # 복셀 수 맞추기
            min_voxels = min(Y_np.shape[1], H_np.shape[1])
            Y_np = Y_np[:, :min_voxels]
            H_truncated = H[:, :min_voxels]

            Y = torch.from_numpy(Y_np).float().to(device)
            Y_dict[subj] = Y

        data[roi] = {
            'H': H_truncated,
            'Y': Y_dict,
            'n_voxels': min_voxels
        }

        print(f"  {roi}: {min_voxels} voxels")

    # 피험자별 가중치 (평균 사용)
    subject_weights = {
        '08': (0.2, 0.3, 0.5),
        '09': (0.5, 0.3, 0.2),
        '10': (0.5, 0.3, 0.2),
    }

    # ROI별 모델 학습
    all_results = {}

    for roi in ROIS:
        print(f"\n{'='*70}")
        print(f"Training HyperNet for {roi}")
        print(f"{'='*70}")

        n_voxels = data[roi]['n_voxels']
        H = data[roi]['H']
        Y_dict = data[roi]['Y']

        # HyperNetwork 초기화
        model = HyperTransform(n_voxels, feature_dim=16, hidden_dim=64, device=device)
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

        # 학습 루프
        history = {subj: [] for subj in SUBJECTS}
        best_loss = {subj: float('inf') for subj in SUBJECTS}

        for epoch in range(MAX_EPOCHS):
            epoch_loss = 0.0

            # 각 피험자에 대해 학습
            for subj_idx, subj in enumerate(SUBJECTS):
                optimizer.zero_grad()

                Y = Y_dict[subj]
                weights = subject_weights[subj]
                lambda_mag, lambda_base, lambda_rdm = weights

                # Forward
                F, A, b = model(Y, subj_idx)

                # Loss
                l_mag = magnitude_loss(F, H)
                l_base = baseline_loss(F, H)
                l_rdm = rdm_loss(F, H)

                loss = lambda_mag * l_mag + lambda_base * l_base + lambda_rdm * l_rdm

                # 정규화
                I = torch.eye(n_voxels, device=device)
                reg_A = ALPHA * torch.norm(A - I, p='fro')**2
                reg_b = BETA * torch.norm(b)**2
                loss = loss + reg_A + reg_b

                # Backward
                loss.backward()

                # 기록
                components = {
                    'magnitude': l_mag.item(),
                    'baseline': l_base.item(),
                    'structure': l_rdm.item(),
                    'total': loss.item()
                }
                history[subj].append(components)
                epoch_loss += loss.item()

                # Update
                if subj_idx == len(SUBJECTS) - 1:  # 마지막 피험자 후 update
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()

            # 로깅
            if epoch % 10 == 0:
                avg_loss = epoch_loss / len(SUBJECTS)
                print(f"Epoch {epoch:4d}: Avg Loss={avg_loss:.6f}")
                for subj in SUBJECTS:
                    comp = history[subj][-1]
                    print(f"  Sub-{subj}: {comp['total']:.6f} "
                          f"(mag={comp['magnitude']:.6f}, base={comp['baseline']:.6f}, "
                          f"struct={comp['structure']:.6f})")

        print(f"\nTraining complete for {roi}!")

        # 각 피험자별 A, b 저장
        for subj_idx, subj in enumerate(SUBJECTS):
            with torch.no_grad():
                Y = Y_dict[subj]
                F, A, b = model(Y, subj_idx)

                A_np = A.cpu().numpy()
                b_np = b.cpu().numpy()

                output_dir = OUTPUT_DIR / f"sub-{subj}" / roi
                output_dir.mkdir(parents=True, exist_ok=True)

                np.save(output_dir / "A_matrix.npy", A_np)
                np.save(output_dir / "b_vector.npy", b_np)

                # 히스토리
                history_file = output_dir / "loss_history.json"
                with open(history_file, 'w') as f:
                    json.dump(history[subj], f, indent=2)

                # 메타데이터
                metadata = {
                    'subject': subj,
                    'roi': roi,
                    'model_type': 'HyperNetwork',
                    'final_loss': history[subj][-1],
                    'n_epochs': len(history[subj]),
                    'hypernet_features': 16,
                    'trained_date': datetime.now().isoformat()
                }

                metadata_file = output_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                print(f"  Saved sub-{subj}: {output_dir}")

    print(f"\n{'='*70}")
    print("HyperNetwork training complete!")
    print(f"{'='*70}")
    print(f"\nResults saved in: {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(description='Phase 2A: HyperNetwork Training')
    parser.add_argument('--gpu', type=int, default=0, help='GPU ID')
    parser.add_argument('--cpu', action='store_true', help='Force CPU mode')

    args = parser.parse_args()

    train_hypernetwork(args.gpu, not args.cpu)


if __name__ == "__main__":
    main()
