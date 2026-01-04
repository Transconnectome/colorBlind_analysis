#!/usr/bin/env python3
"""
Phase 2A: 단일 모델 학습

Usage:
    python phase2a_train_single.py --subject 08 --roi V1 --option D  # Recommended
    python phase2a_train_single.py --subject 09 --roi V2 --option A  # Alternative

Options:
    A: Angular Distance (Simple, interpretable)
    D: RDM-Based (Recommended, captures color-pair relationships)

Note: Option B (Variance Decomposition) deprecated due to poor performance
"""

import numpy as np
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')  # 서버에서 GUI 없이 실행
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import minimize, approx_fprime
import argparse

# 경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# 피험자별 가중치
SUBJECT_WEIGHTS = {
    '08': (0.2, 0.3, 0.5),  # Structure-dominant
    '09': (0.5, 0.3, 0.2),  # Magnitude-dominant
    '10': (0.5, 0.3, 0.2),  # Magnitude-dominant
}

# 하이퍼파라미터
ALPHA = 0.01
BETA = 0.01
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


def angular_loss(F, H):
    """
    Option A: Per-color angular distance
    Measures angle between each color's voxel pattern
    """
    n_colors = F.shape[0]
    angles_squared = []

    for i in range(n_colors):
        f_norm_val = np.linalg.norm(F[i])
        h_norm_val = np.linalg.norm(H[i])

        if f_norm_val > 1e-10 and h_norm_val > 1e-10:
            f_unit = F[i] / f_norm_val
            h_unit = H[i] / h_norm_val
            cos_sim = np.dot(f_unit, h_unit)
            cos_sim = np.clip(cos_sim, -1.0, 1.0)
            angle = np.arccos(cos_sim)
            angles_squared.append(angle**2)
        else:
            angles_squared.append(0.0)

    return np.mean(angles_squared)


def variance_decomposition_loss(F, H):
    """
    Option B: Angular component from variance decomposition
    Total² = Magnitude² + Angular²

    DEPRECATED: Empirical results showed 10-100x worse performance than Options A/D.
    Excluded from candidate methods.
    """
    raise DeprecationWarning("Option B is deprecated due to poor empirical performance (0/6 wins, 10-100x worse loss)")

    n_colors = F.shape[0]
    angular_terms = []

    for i in range(n_colors):
        f_norm = np.linalg.norm(F[i])
        h_norm = np.linalg.norm(H[i])

        if f_norm > 1e-10 and h_norm > 1e-10:
            cos_sim = np.dot(F[i], H[i]) / (f_norm * h_norm)
            cos_sim = np.clip(cos_sim, -1.0, 1.0)
            angular_term = 2 * f_norm * h_norm * (1 - cos_sim)
            angular_terms.append(angular_term)
        else:
            angular_terms.append(0.0)

    return np.sum(angular_terms)


def rdm_loss(F, H):
    """
    Option D: RDM-based structure loss
    Captures color-pair relationships
    """
    def compute_rdm(patterns):
        n_colors = patterns.shape[0]
        patterns_centered = patterns - patterns.mean(axis=1, keepdims=True)
        rdm = np.zeros((n_colors, n_colors))

        for i in range(n_colors):
            for j in range(n_colors):
                if i == j:
                    rdm[i, j] = 0.0
                else:
                    vi = patterns_centered[i]
                    vj = patterns_centered[j]
                    norm_i = np.linalg.norm(vi)
                    norm_j = np.linalg.norm(vj)

                    if norm_i > 1e-10 and norm_j > 1e-10:
                        corr = np.dot(vi, vj) / (norm_i * norm_j)
                    else:
                        corr = 0.0

                    rdm[i, j] = 1 - corr

        return rdm

    rdm_F = compute_rdm(F)
    rdm_H = compute_rdm(H)
    return np.linalg.norm(rdm_F - rdm_H, ord='fro')**2


def get_structure_loss_fn(option):
    """구조 손실 함수 선택

    Available options:
    - A: Angular Distance (Simple, interpretable)
    - D: RDM-Based (Recommended, captures color-pair relationships)

    Deprecated:
    - B: Variance Decomposition (10-100x worse performance, excluded)
    """
    if option == 'A':
        return angular_loss, 'Angular Distance'
    elif option == 'B':
        raise ValueError("Option B (Variance Decomposition) is deprecated due to poor performance. Use A or D instead.")
    elif option == 'D':
        return rdm_loss, 'RDM-Based'
    else:
        raise ValueError(f"Invalid option: {option}. Must be A or D (B is deprecated)")


def compute_gradient(params, Y, H, weights, n_voxels, structure_loss_fn):
    """
    Compute analytical gradient of loss w.r.t. parameters

    Gradient components:
    - Magnitude & Baseline: Analytical (exact)
    - Structure (RDM): Numerical approximation (for complexity)

    Returns:
        grad: (n_params,) gradient vector
    """
    lambda_mag, lambda_base, lambda_struct = weights

    # Unpack parameters
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)

    # Forward pass
    F = Y @ A + b[np.newaxis, :]  # (8, n_voxels)

    # ========================================
    # Gradient w.r.t F (∂L/∂F)
    # ========================================
    grad_F = np.zeros_like(F)  # (8, n_voxels)

    # 1. Magnitude loss gradient
    # L_mag = (1/8) * Σ(||F[i]|| - ||H[i]||)²
    # ∂L_mag/∂F[i] = (1/4) * (||F[i]|| - ||H[i]||) * F[i] / ||F[i]||
    norm_F = np.linalg.norm(F, axis=1, keepdims=True)  # (8, 1)
    norm_H = np.linalg.norm(H, axis=1, keepdims=True)  # (8, 1)
    grad_mag_F = (1/4) * (norm_F - norm_H) * F / (norm_F + 1e-10)  # (8, n_voxels)

    # 2. Baseline loss gradient
    # L_base = (1/8) * Σ(mean(F[i]) - mean(H[i]))²
    # ∂L_base/∂F[i] = (1/(4*n)) * (mean(F[i]) - mean(H[i])) * ones
    mean_F = np.mean(F, axis=1, keepdims=True)  # (8, 1)
    mean_H = np.mean(H, axis=1, keepdims=True)  # (8, 1)
    grad_base_F = (1 / (4 * n_voxels)) * (mean_F - mean_H) * np.ones_like(F)

    # 3. Structure loss gradient (numerical for RDM complexity)
    # Use numerical approximation only for structure component
    def struct_loss_fn(F_flat):
        F_reshaped = F_flat.reshape(8, n_voxels)
        return structure_loss_fn(F_reshaped, H)

    F_flat = F.flatten()
    grad_struct_F_flat = approx_fprime(F_flat, struct_loss_fn, epsilon=1e-8)
    grad_struct_F = grad_struct_F_flat.reshape(8, n_voxels)

    # Combine weighted gradients
    grad_F = lambda_mag * grad_mag_F + lambda_base * grad_base_F + lambda_struct * grad_struct_F

    # ========================================
    # Chain rule: F = Y @ A + b
    # ========================================
    # ∂L/∂A = Y^T @ (∂L/∂F)
    grad_A = Y.T @ grad_F  # (n_voxels, n_voxels)

    # ∂L/∂b = Σ(∂L/∂F)
    grad_b = np.sum(grad_F, axis=0)  # (n_voxels,)

    # ========================================
    # Add regularization gradients
    # ========================================
    I = np.eye(n_voxels)
    grad_A += 2 * ALPHA * (A - I)
    grad_b += 2 * BETA * b

    # Concatenate to match parameter format
    grad_params = np.concatenate([grad_A.flatten(), grad_b])

    return grad_params


def three_component_loss_with_grad(params, Y, H, weights, n_voxels, structure_loss_fn):
    """
    Compute loss AND gradient together (efficient for L-BFGS-B)

    Returns:
        loss: scalar
        grad: (n_params,) gradient vector
    """
    loss = three_component_loss(params, Y, H, weights, n_voxels, structure_loss_fn)
    grad = compute_gradient(params, Y, H, weights, n_voxels, structure_loss_fn)
    return loss, grad


def three_component_loss(params, Y, H, weights, n_voxels, structure_loss_fn):
    """완전 손실 함수"""
    lambda_mag, lambda_base, lambda_struct = weights
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)
    F = Y @ A + b[np.newaxis, :]

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_struct = structure_loss_fn(F, H)

    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_struct * l_struct

    # 정규화
    I = np.eye(n_voxels)
    reg_A = ALPHA * np.linalg.norm(A - I, ord='fro')**2
    reg_b = BETA * np.linalg.norm(b)**2
    loss = loss + reg_A + reg_b

    return loss


def compute_loss_components(params, Y, H, weights, n_voxels, structure_loss_fn):
    """개별 손실 계산"""
    lambda_mag, lambda_base, lambda_struct = weights
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]
    A = A_flat.reshape(n_voxels, n_voxels)
    F = Y @ A + b[np.newaxis, :]

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_struct = structure_loss_fn(F, H)
    total = lambda_mag * l_mag + lambda_base * l_base + lambda_struct * l_struct

    return {
        'magnitude': float(l_mag),
        'baseline': float(l_base),
        'structure': float(l_struct),
        'total': float(total)
    }


def train_model(subject_id, roi, option='D'):
    """모델 학습"""
    print("=" * 70)
    print(f"Phase 2A: Training sub-{subject_id} {roi}")
    print(f"Option: {option}")
    print("=" * 70)

    # 구조 손실 함수 선택
    structure_loss_fn, structure_name = get_structure_loss_fn(option)
    print(f"Structure Loss: {structure_name}")

    # 출력 디렉토리 설정
    OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_models"

    # 패턴 로드
    cvd_file = PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy"
    hc_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"

    print(f"\nLoading patterns...")
    print(f"  CVD: {cvd_file}")
    print(f"  HC: {hc_file}")

    Y = np.load(cvd_file)
    H = np.load(hc_file)

    # 복셀 수 맞추기
    min_voxels = min(Y.shape[1], H.shape[1])
    Y = Y[:, :min_voxels]
    H = H[:, :min_voxels]

    print(f"  Y shape: {Y.shape}")
    print(f"  H shape: {H.shape}")

    # 가중치
    weights = SUBJECT_WEIGHTS[subject_id]
    print(f"  Weights: λ_mag={weights[0]}, λ_base={weights[1]}, λ_struct={weights[2]}")

    # 초기화
    n_voxels = Y.shape[1]
    A_init = np.eye(n_voxels).flatten()
    b_init = np.zeros(n_voxels)
    params_init = np.concatenate([A_init, b_init])

    print(f"\nStarting optimization...")
    print(f"  Parameters: {len(params_init)} dims")

    # 초기 loss 확인
    initial_components = compute_loss_components(params_init, Y, H, weights, n_voxels, structure_loss_fn)
    print(f"  Initial loss: {initial_components['total']:.6f}")
    print(f"    Magnitude: {initial_components['magnitude']:.6f}")
    print(f"    Baseline: {initial_components['baseline']:.6f}")
    print(f"    Structure: {initial_components['structure']:.6f}")

    # 최적화
    history = []
    iteration_count = [0]

    def callback(xk):
        iteration_count[0] += 1
        if iteration_count[0] % 100 == 0:
            components = compute_loss_components(xk, Y, H, weights, n_voxels, structure_loss_fn)
            history.append(components)
            print(f"Iter {iteration_count[0]:4d}: Loss={components['total']:.6f} "
                  f"(mag={components['magnitude']:.6f}, "
                  f"base={components['baseline']:.6f}, "
                  f"struct={components['structure']:.6f})")

    # Use analytical gradient for massive speedup
    print("  Using analytical gradient (magnitude + baseline) + numerical (RDM)")

    result = minimize(
        three_component_loss_with_grad,
        params_init,
        args=(Y, H, weights, n_voxels, structure_loss_fn),
        method='L-BFGS-B',
        jac=True,  # Gradient is returned by function
        callback=callback,
        options={
            'maxiter': MAX_ITER,
            'disp': True,
            'ftol': 1e-9,       # Function tolerance
            'gtol': 1e-5,       # Gradient tolerance (convergence when ||grad|| < gtol)
            'maxfun': 1000000,  # Maximum function evaluations
            'maxls': 50         # Maximum line search steps per iteration
        }
    )

    # 최종 파라미터
    A_flat = result.x[:n_voxels**2]
    b_final = result.x[n_voxels**2:]
    A_final = A_flat.reshape(n_voxels, n_voxels)

    final_components = compute_loss_components(result.x, Y, H, weights, n_voxels, structure_loss_fn)
    history.append(final_components)

    print(f"\nOptimization complete!")
    print(f"  Iterations: {result.nit}")
    print(f"  Function evaluations: {result.nfev}")
    print(f"  Status: {result.status}")
    print(f"  Message: {result.message}")
    print(f"  Success: {result.success}")
    print(f"  Final loss: {final_components['total']:.6f}")
    print(f"    Magnitude: {final_components['magnitude']:.6f}")
    print(f"    Baseline: {final_components['baseline']:.6f}")
    print(f"    Structure: {final_components['structure']:.6f}")

    # Gradient norm 확인
    if hasattr(result, 'jac'):
        grad_norm = np.linalg.norm(result.jac)
        print(f"  Final gradient norm: {grad_norm:.2e}")

    # 저장
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi
    output_dir.mkdir(parents=True, exist_ok=True)

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
            'max_iterations': MAX_ITER,
            'alpha': ALPHA,
            'beta': BETA
        },
        'final_loss': final_components,
        'n_iterations': len(history),
        'trained_date': datetime.now().isoformat()
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # 손실 곡선 플롯
    if len(history) >= 2:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        iterations = range(len(history))

        ax.plot(iterations, [h['total'] for h in history], 'k-', linewidth=2, label='Total')
        ax.plot(iterations, [h['magnitude'] for h in history], 'r-', linewidth=1.5, label='Magnitude')
        ax.plot(iterations, [h['baseline'] for h in history], 'g-', linewidth=1.5, label='Baseline')
        ax.plot(iterations, [h['structure'] for h in history], 'b-', linewidth=1.5, label=f'Structure ({structure_name})')

        ax.set_xlabel('Iteration (×100)', fontsize=12)
        ax.set_ylabel('Loss', fontsize=12)
        ax.set_title(f'sub-{subject_id} {roi} - Option {option}', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plot_file = output_dir / "loss_curve.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  {plot_file}")

    print(f"\nTraining complete for sub-{subject_id} {roi} (Option {option})!")

    return final_components


def main():
    parser = argparse.ArgumentParser(description='Phase 2A: Single Model Training')
    parser.add_argument('--subject', type=str, required=True, choices=['08', '09', '10'],
                        help='Subject ID (08, 09, or 10)')
    parser.add_argument('--roi', type=str, required=True, choices=['V1', 'V2', 'V3', 'hV4'],
                        help='ROI name')
    parser.add_argument('--option', type=str, default='D', choices=['A', 'B', 'D'],
                        help='Structure loss option: A (Angular), B (Variance), D (RDM)')

    args = parser.parse_args()

    train_model(args.subject, args.roi, args.option)


if __name__ == "__main__":
    main()
