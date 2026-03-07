#!/usr/bin/env python3
"""
Phase 2A: Filter Training for baseline81_deob_determin
서버에서 실행 (개별 모델)

Usage:
    python phase2a_train_single_baseline81.py --subject 08 --roi V1
    python phase2a_train_single_baseline81.py --subject 09 --roi V2
"""

import numpy as np
from pathlib import Path
import json
from scipy.optimize import minimize, approx_fprime
from scipy.stats import spearmanr
from datetime import datetime
import argparse

# 경로 설정 (서버)
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data_baseline81/patterns"
OUTPUT_DIR = BASE_DIR / "results/filters/models_baseline81/optionD"

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# 피험자별 가중치 (Phase 2A baseline32와 동일)
SUBJECT_WEIGHTS = {
    '08': (0.2, 0.3, 0.5),  # Structure-dominant
    '09': (0.5, 0.3, 0.2),  # Magnitude-dominant
    '10': (0.5, 0.3, 0.2),  # Magnitude-dominant
}

# 하이퍼파라미터
ALPHA = 0.01  # A 정규화
BETA = 0.01   # b 정규화
MAX_ITER = 1000


def magnitude_loss(F, H):
    """L_mag: 색별 L2 norm 매칭"""
    norm_F = np.linalg.norm(F, axis=1)
    norm_H = np.linalg.norm(H, axis=1)
    return np.mean((norm_F - norm_H)**2)


def baseline_loss(F, H):
    """L_base: 색별 평균 매칭"""
    mean_F = np.mean(F, axis=1)
    mean_H = np.mean(H, axis=1)
    return np.mean((mean_F - mean_H)**2)


def rdm_loss(F, H):
    """Option D: RDM-based structure loss"""
    n_colors = F.shape[0]
    rdm_F = np.zeros((n_colors, n_colors))
    rdm_H = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                corr_F, _ = spearmanr(F[i], F[j])
                corr_H, _ = spearmanr(H[i], H[j])
                rdm_F[i, j] = 1 - corr_F
                rdm_H[i, j] = 1 - corr_H

    return np.linalg.norm(rdm_F - rdm_H, ord='fro')**2


def compute_gradient(params, Y, H, weights, n_voxels):
    """Analytical gradient (magnitude + baseline) + numerical (RDM)"""
    lambda_mag, lambda_base, lambda_struct = weights

    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)

    F = Y @ A + b[np.newaxis, :]

    # 1. Magnitude loss gradient
    norm_F = np.linalg.norm(F, axis=1, keepdims=True)
    norm_H = np.linalg.norm(H, axis=1, keepdims=True)
    grad_mag_F = (2 / 8) * (norm_F - norm_H) * (F / (norm_F + 1e-10))

    # 2. Baseline loss gradient
    mean_F = np.mean(F, axis=1, keepdims=True)
    mean_H = np.mean(H, axis=1, keepdims=True)
    grad_base_F = (1 / (4 * n_voxels)) * (mean_F - mean_H) * np.ones_like(F)

    # 3. Structure loss gradient (numerical for RDM)
    def struct_loss_fn(F_flat):
        F_reshaped = F_flat.reshape(8, n_voxels)
        return rdm_loss(F_reshaped, H)

    F_flat = F.flatten()
    grad_struct_F_flat = approx_fprime(F_flat, struct_loss_fn, epsilon=1e-8)
    grad_struct_F = grad_struct_F_flat.reshape(8, n_voxels)

    # Combine
    grad_F = lambda_mag * grad_mag_F + lambda_base * grad_base_F + lambda_struct * grad_struct_F

    # Chain rule: F = Y @ A + b
    grad_A = Y.T @ grad_F
    grad_b = np.sum(grad_F, axis=0)

    # Regularization
    I = np.eye(n_voxels)
    grad_A += 2 * ALPHA * (A - I)
    grad_b += 2 * BETA * b

    grad_params = np.concatenate([grad_A.flatten(), grad_b])

    return grad_params


def three_component_loss_with_grad(params, Y, H, weights, n_voxels):
    """Loss and gradient together"""
    loss = three_component_loss(params, Y, H, weights, n_voxels)
    grad = compute_gradient(params, Y, H, weights, n_voxels)
    return loss, grad


def three_component_loss(params, Y, H, weights, n_voxels):
    """완전 손실 함수"""
    lambda_mag, lambda_base, lambda_struct = weights
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)
    F = Y @ A + b[np.newaxis, :]

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_struct = rdm_loss(F, H)

    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_struct * l_struct

    # 정규화
    I = np.eye(n_voxels)
    reg_A = ALPHA * np.linalg.norm(A - I, ord='fro')**2
    reg_b = BETA * np.linalg.norm(b)**2
    loss = loss + reg_A + reg_b

    return loss


def compute_loss_components(params, Y, H, weights, n_voxels):
    """개별 손실 계산 (출력용)"""
    lambda_mag, lambda_base, lambda_struct = weights
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)
    F = Y @ A + b[np.newaxis, :]

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_struct = rdm_loss(F, H)
    total = lambda_mag * l_mag + lambda_base * l_base + lambda_struct * l_struct

    return {
        'magnitude': float(l_mag),
        'baseline': float(l_base),
        'structure': float(l_struct),
        'total': float(total)
    }


def train_model(subject_id, roi):
    """단일 모델 학습"""
    print(f"\n{'='*70}")
    print(f"Training: sub-{subject_id} {roi} (baseline81)")
    print(f"{'='*70}")
    print(f"Start time: {datetime.now()}")

    # 1. 데이터 로드
    hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

    print(f"\nData loaded:")
    print(f"  HC shape: {hc_pattern.shape}")
    print(f"  CVD shape: {cvd_pattern.shape}")

    # 2. Voxel alignment
    n_voxels_hc = hc_pattern.shape[1]
    n_voxels_cvd = cvd_pattern.shape[1]
    n_voxels = min(n_voxels_hc, n_voxels_cvd)

    if n_voxels_hc != n_voxels_cvd:
        print(f"\n⚠️ Aligning voxels: {n_voxels_hc}, {n_voxels_cvd} -> {n_voxels}")
        hc_pattern = hc_pattern[:, :n_voxels]
        cvd_pattern = cvd_pattern[:, :n_voxels]
    else:
        print(f"\n✓ Voxel counts match: {n_voxels}")

    H = hc_pattern  # Target
    Y = cvd_pattern  # Input

    # 3. 초기화
    A_init = np.eye(n_voxels)
    b_init = np.zeros(n_voxels)
    params_init = np.concatenate([A_init.flatten(), b_init])

    print(f"\nInitialization:")
    print(f"  Parameters: {len(params_init)} ({n_voxels}x{n_voxels} + {n_voxels})")

    # 4. 가중치
    weights = SUBJECT_WEIGHTS[subject_id]
    print(f"\nWeights (mag, base, struct): {weights}")
    print(f"  λ_mag={weights[0]}, λ_base={weights[1]}, λ_struct={weights[2]}")
    print(f"Regularization: alpha={ALPHA}, beta={BETA}")

    # 5. 최적화
    print(f"\nStarting optimization...")
    print(f"  Parameters: {len(params_init)} dims")

    # 초기 loss 확인
    initial_components = compute_loss_components(params_init, Y, H, weights, n_voxels)
    print(f"  Initial loss: {initial_components['total']:.6f}")
    print(f"    Magnitude: {initial_components['magnitude']:.6f}")
    print(f"    Baseline: {initial_components['baseline']:.6f}")
    print(f"    Structure: {initial_components['structure']:.6f}")
    print(f"  Using analytical gradient (magnitude + baseline) + numerical (RDM)")

    # Callback for progress tracking
    history = []
    iteration_count = [0]

    def callback(xk):
        iteration_count[0] += 1
        if iteration_count[0] % 100 == 0:
            components = compute_loss_components(xk, Y, H, weights, n_voxels)
            history.append(components)
            print(f"Iter {iteration_count[0]:4d}: Loss={components['total']:.6f} "
                  f"(mag={components['magnitude']:.6f}, "
                  f"base={components['baseline']:.6f}, "
                  f"struct={components['structure']:.6f})")

    print(f"\nOptimizing with L-BFGS-B (max_iter={MAX_ITER})...")

    result = minimize(
        three_component_loss_with_grad,
        params_init,
        args=(Y, H, weights, n_voxels),
        method='L-BFGS-B',
        jac=True,  # gradient provided
        callback=callback,
        options={'maxiter': MAX_ITER, 'disp': True, 'ftol': 1e-9}
    )

    # Final loss components
    final_components = compute_loss_components(result.x, Y, H, weights, n_voxels)

    print(f"\nOptimization complete:")
    print(f"  Success: {result.success}")
    print(f"  Iterations: {result.nit}")
    print(f"  Final loss: {result.fun:.6e}")
    print(f"    Magnitude: {final_components['magnitude']:.6f}")
    print(f"    Baseline: {final_components['baseline']:.6f}")
    print(f"    Structure: {final_components['structure']:.6f}")

    # 6. 결과 저장
    A_opt = result.x[:n_voxels**2].reshape(n_voxels, n_voxels)
    b_opt = result.x[n_voxels**2:]

    output_subdir = OUTPUT_DIR / f"sub-{subject_id}" / roi
    output_subdir.mkdir(parents=True, exist_ok=True)

    np.save(output_subdir / "A_matrix.npy", A_opt)
    np.save(output_subdir / "b_vector.npy", b_opt)

    print(f"\nSaved filter parameters:")
    print(f"  A: {output_subdir / 'A_matrix.npy'}")
    print(f"  b: {output_subdir / 'b_vector.npy'}")
    print(f"  ||A - I||_F: {np.linalg.norm(A_opt - np.eye(n_voxels), ord='fro'):.4f}")
    print(f"  ||b||: {np.linalg.norm(b_opt):.4f}")

    # 7. 메타데이터
    metadata = {
        "subject": subject_id,
        "roi": roi,
        "preprocessing": "baseline81_deob_determin",
        "n_voxels": int(n_voxels),
        "weights": {
            "magnitude": float(weights[0]),
            "baseline": float(weights[1]),
            "structure": float(weights[2])
        },
        "hyperparameters": {
            "alpha": float(ALPHA),
            "beta": float(BETA),
            "max_iter": int(MAX_ITER)
        },
        "loss_components": {
            "initial": {
                "total": float(initial_components['total']),
                "magnitude": float(initial_components['magnitude']),
                "baseline": float(initial_components['baseline']),
                "structure": float(initial_components['structure'])
            },
            "final": {
                "total": float(final_components['total']),
                "magnitude": float(final_components['magnitude']),
                "baseline": float(final_components['baseline']),
                "structure": float(final_components['structure'])
            }
        },
        "optimization": {
            "final_loss": float(result.fun),
            "success": bool(result.success),
            "n_iterations": int(result.nit),
            "message": result.message,
            "history": history  # 100 iter마다 기록
        },
        "filter_properties": {
            "deviation_from_identity": float(np.linalg.norm(A_opt - np.eye(n_voxels), ord='fro')),
            "bias_norm": float(np.linalg.norm(b_opt))
        },
        "trained_date": datetime.now().isoformat()
    }

    with open(output_subdir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadata saved: {output_subdir / 'metadata.json'}")
    print(f"End time: {datetime.now()}")
    print(f"{'='*70}\n")

    return result


def main():
    parser = argparse.ArgumentParser(description='Train Phase 2A filter (baseline81)')
    parser.add_argument('--subject', type=str, required=True, choices=['08', '09', '10'],
                        help='Subject ID (08, 09, or 10)')
    parser.add_argument('--roi', type=str, required=True, choices=['V1', 'V2'],
                        help='ROI (V1 or V2)')

    args = parser.parse_args()

    print("=" * 70)
    print("Phase 2A Filter Training - baseline81_deob_determin")
    print("=" * 70)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Option: D (RDM-Based)")
    print("=" * 70)

    result = train_model(args.subject, args.roi)

    if result.success:
        print("\n✅ Training successful!")
    else:
        print(f"\n⚠️ Training ended: {result.message}")


if __name__ == "__main__":
    main()
