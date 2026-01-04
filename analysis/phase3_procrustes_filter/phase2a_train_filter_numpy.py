#!/usr/bin/env python3
"""
Phase 2A: 필터 학습 (NumPy/SciPy 버전)

선형 변환 학습: F = Y @ A + b
3요소 손실 함수: Magnitude + Baseline + RDM
"""

import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import minimize

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
ALPHA = 0.01  # A 정규화
BETA = 0.01   # b 정규화
MAX_ITER = 1000


def magnitude_loss(F, H):
    """L_mag: 색별 L2 norm 매칭"""
    norm_F = np.linalg.norm(F, axis=1)  # (8,)
    norm_H = np.linalg.norm(H, axis=1)  # (8,)
    return np.mean((norm_F - norm_H)**2)


def baseline_loss(F, H):
    """L_base: 색별 평균 매칭"""
    mean_F = np.mean(F, axis=1)  # (8,)
    mean_H = np.mean(H, axis=1)  # (8,)
    return np.mean((mean_F - mean_H)**2)


def rdm_loss(F, H):
    """L_rdm: 평균-중심화 RDM 매칭"""

    def compute_rdm(patterns):
        """patterns: (8, n_voxels) → RDM: (8, 8)"""
        n_colors = patterns.shape[0]

        # 평균 중심화
        patterns_centered = patterns - patterns.mean(axis=1, keepdims=True)

        # RDM 계산
        rdm = np.zeros((n_colors, n_colors))
        for i in range(n_colors):
            for j in range(n_colors):
                if i == j:
                    rdm[i, j] = 0.0
                else:
                    vi = patterns_centered[i]
                    vj = patterns_centered[j]

                    # Pearson correlation
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


def three_component_loss(params, Y, H, weights, n_voxels, alpha=ALPHA, beta=BETA):
    """
    완전 손실 함수 (정규화 포함)

    Parameters:
    -----------
    params : np.ndarray
        Flattened parameters [A_flat, b]
    Y, H : np.ndarray (8, n_voxels)
        CVD 패턴, HC 패턴
    weights : tuple
        (lambda_mag, lambda_base, lambda_rdm)
    n_voxels : int
        복셀 수

    Returns:
    --------
    loss : float
    """
    lambda_mag, lambda_base, lambda_rdm = weights

    # 파라미터 복원
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]

    A = A_flat.reshape(n_voxels, n_voxels)

    # Forward: F = Y @ A + b
    F = Y @ A + b[np.newaxis, :]  # Broadcasting b

    # 3가지 손실 계산
    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_rdm = rdm_loss(F, H)

    # 가중 합
    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_rdm * l_rdm

    # 정규화 (작은 변형 유도)
    I = np.eye(n_voxels)
    reg_A = alpha * np.linalg.norm(A - I, ord='fro')**2
    reg_b = beta * np.linalg.norm(b)**2

    loss = loss + reg_A + reg_b

    return loss


def compute_loss_components(params, Y, H, weights, n_voxels):
    """개별 손실 계산 (로깅용)"""
    lambda_mag, lambda_base, lambda_rdm = weights

    # 파라미터 복원
    A_flat = params[:n_voxels**2]
    b = params[n_voxels**2:]

    A = A_flat.reshape(n_voxels, n_voxels)

    # Forward
    F = Y @ A + b[np.newaxis, :]

    # 손실 계산
    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_rdm = rdm_loss(F, H)

    total = lambda_mag * l_mag + lambda_base * l_base + lambda_rdm * l_rdm

    return {
        'magnitude': l_mag,
        'baseline': l_base,
        'rdm': l_rdm,
        'total': total
    }


def train_transformation(Y, H, weights, subject_id, roi, max_iter=MAX_ITER):
    """
    변환 학습

    Returns:
    --------
    A : np.ndarray (n_voxels, n_voxels)
    b : np.ndarray (n_voxels,)
    history : list of dict
    """
    print(f"\n{'='*70}")
    print(f"Training: sub-{subject_id} {roi}")
    print(f"Weights: λ_mag={weights[0]}, λ_base={weights[1]}, λ_rdm={weights[2]}")
    print(f"{'='*70}")

    n_voxels = Y.shape[1]

    # 초기화: 항등 변환
    A_init = np.eye(n_voxels).flatten()
    b_init = np.zeros(n_voxels)
    params_init = np.concatenate([A_init, b_init])

    # 최적화 (L-BFGS-B)
    print(f"\nStarting optimization...")
    print(f"  Initial parameters: {len(params_init)} dims")

    history = []
    iteration_count = [0]  # Closure를 위한 리스트

    def callback(xk):
        """각 iteration에서 호출"""
        iteration_count[0] += 1
        if iteration_count[0] % 100 == 0:
            components = compute_loss_components(xk, Y, H, weights, n_voxels)
            history.append(components)
            print(f"Iter {iteration_count[0]:4d}: Loss={components['total']:.6f} "
                  f"(mag={components['magnitude']:.6f}, "
                  f"base={components['baseline']:.6f}, "
                  f"rdm={components['rdm']:.6f})")

    result = minimize(
        three_component_loss,
        params_init,
        args=(Y, H, weights, n_voxels, ALPHA, BETA),
        method='L-BFGS-B',
        callback=callback,
        options={'maxiter': max_iter, 'disp': True}
    )

    # 최종 파라미터
    A_flat = result.x[:n_voxels**2]
    b_final = result.x[n_voxels**2:]
    A_final = A_flat.reshape(n_voxels, n_voxels)

    # 최종 손실 기록
    final_components = compute_loss_components(result.x, Y, H, weights, n_voxels)
    history.append(final_components)

    print(f"\nOptimization complete!")
    print(f"  Iterations: {result.nit}")
    print(f"  Final loss: {final_components['total']:.6f}")
    print(f"    Magnitude: {final_components['magnitude']:.6f}")
    print(f"    Baseline: {final_components['baseline']:.6f}")
    print(f"    RDM: {final_components['rdm']:.6f}")

    return A_final, b_final, history


def save_model(A, b, history, subject_id, roi, weights):
    """모델 및 결과 저장"""
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # A, b 저장
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
            'max_iterations': MAX_ITER,
            'alpha': ALPHA,
            'beta': BETA
        },
        'final_loss': history[-1],
        'n_iterations': len(history),
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
    if len(history) < 2:
        print("  Warning: Not enough history for plotting")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    iterations = range(len(history))

    # Total loss
    axes[0, 0].plot(iterations, [h['total'] for h in history], 'k-', linewidth=2)
    axes[0, 0].set_xlabel('Iteration (×100)')
    axes[0, 0].set_ylabel('Total Loss')
    axes[0, 0].set_title('Total Loss')
    axes[0, 0].grid(True, alpha=0.3)

    # Magnitude loss
    axes[0, 1].plot(iterations, [h['magnitude'] for h in history], 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Iteration (×100)')
    axes[0, 1].set_ylabel('Magnitude Loss')
    axes[0, 1].set_title('Magnitude Loss')
    axes[0, 1].grid(True, alpha=0.3)

    # Baseline loss
    axes[1, 0].plot(iterations, [h['baseline'] for h in history], 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Iteration (×100)')
    axes[1, 0].set_ylabel('Baseline Loss')
    axes[1, 0].set_title('Baseline Loss')
    axes[1, 0].grid(True, alpha=0.3)

    # RDM loss
    axes[1, 1].plot(iterations, [h['rdm'] for h in history], 'b-', linewidth=2)
    axes[1, 1].set_xlabel('Iteration (×100)')
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
    print("Phase 2A: Training Filters (NumPy/SciPy)")
    print("=" * 70)
    print(f"\nHyperparameters:")
    print(f"  Max iterations: {MAX_ITER}")
    print(f"  Regularization: α={ALPHA}, β={BETA}")

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

            # 복셀 수 맞추기
            min_voxels = min(Y.shape[1], H.shape[1])
            Y = Y[:, :min_voxels]
            H = H[:, :min_voxels]

            print(f"\nLoaded patterns: Y={Y.shape}, H={H.shape}")

            # 가중치
            weights = SUBJECT_WEIGHTS[subject_id]

            # 학습
            A, b, history = train_transformation(Y, H, weights, subject_id, roi)

            # 저장
            save_model(A, b, history, subject_id, roi, weights)

            # 결과 기록
            all_results.append({
                'subject': subject_id,
                'roi': roi,
                'final_loss': history[-1]['total'],
                'magnitude_loss': history[-1]['magnitude'],
                'baseline_loss': history[-1]['baseline'],
                'rdm_loss': history[-1]['rdm'],
                'n_iterations': len(history)
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
