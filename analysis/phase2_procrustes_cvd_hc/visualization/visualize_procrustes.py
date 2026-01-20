#!/usr/bin/env python3
"""
Procrustes Analysis Visualization
==================================

실제 데이터를 사용해서 Procrustes stability를 시각화합니다.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import procrustes
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from pathlib import Path
import glob

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'  # macOS
plt.rcParams['axes.unicode_minus'] = False

def load_subject_amplitudes(subject_id, roi, timestamp='baseline81_deob_determin',
                            dataset='deoblique_v2'):
    """피험자 amplitudes 로드"""
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    amplitudes = np.load(amp_file)
    return amplitudes

def compute_rdm(amplitudes):
    """RDM 계산"""
    n_runs, n_colors, n_voxels = amplitudes.shape
    mean_pattern = amplitudes.mean(axis=0)  # (n_colors, n_voxels)
    rdm = 1 - np.corrcoef(mean_pattern)
    return rdm

def compute_split_half_metrics(amplitudes):
    """Split-half metrics 계산"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split
    half1_idx = list(range(n_runs // 2))
    half2_idx = list(range(n_runs // 2, n_runs))

    half1 = amplitudes[half1_idx].mean(axis=0)  # (n_colors, n_voxels)
    half2 = amplitudes[half2_idx].mean(axis=0)

    # RDM correlation
    rdm1 = compute_rdm(amplitudes[half1_idx])
    rdm2 = compute_rdm(amplitudes[half2_idx])
    triu_idx = np.triu_indices(n_colors, k=1)
    rdm_corr, _ = spearmanr(rdm1[triu_idx], rdm2[triu_idx])

    # Procrustes
    mtx1, mtx2, disparity = procrustes(half1, half2)
    procrustes_stab = 1 - disparity

    return {
        'half1': half1,
        'half2': half2,
        'rdm1': rdm1,
        'rdm2': rdm2,
        'rdm_correlation': rdm_corr,
        'procrustes_stability': procrustes_stab,
        'procrustes_disparity': disparity,
        'procrustes_mtx1': mtx1,
        'procrustes_mtx2': mtx2,
    }

def visualize_procrustes_concept():
    """Procrustes 개념 시각화 (2D toy example)"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Toy data: 8 colors in 2D
    np.random.seed(42)
    colors_half1 = np.array([
        [1.0, 0.5],   # Red
        [0.9, 0.7],   # Orange
        [0.5, 1.0],   # Yellow
        [0.0, 0.8],   # Green
        [-0.5, 0.5],  # Cyan
        [-0.8, 0.0],  # Blue
        [-0.5, -0.5], # Purple
        [0.0, -0.8],  # Magenta
    ])

    # Rotation + noise
    theta = np.pi / 4  # 45 degrees
    rotation = np.array([[np.cos(theta), -np.sin(theta)],
                        [np.sin(theta), np.cos(theta)]])
    colors_half2 = colors_half1 @ rotation.T + np.random.randn(8, 2) * 0.1

    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    color_vals = ['red', 'orange', 'gold', 'green', 'cyan', 'blue', 'purple', 'magenta']

    # 1. Half 1 original
    ax = axes[0, 0]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(colors_half1[i, 0], colors_half1[i, 1],
                  s=200, c=c, edgecolors='black', linewidth=2, alpha=0.7)
        ax.text(colors_half1[i, 0], colors_half1[i, 1] + 0.15, name,
               ha='center', fontsize=9)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Half 1: 원본 패턴\n(첫 3 runs)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Voxel dimension 1')
    ax.set_ylabel('Voxel dimension 2')

    # 2. Half 2 rotated
    ax = axes[0, 1]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(colors_half2[i, 0], colors_half2[i, 1],
                  s=200, c=c, edgecolors='black', linewidth=2, alpha=0.7)
        ax.text(colors_half2[i, 0], colors_half2[i, 1] + 0.15, name,
               ha='center', fontsize=9)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Half 2: 회전된 패턴\n(나머지 3 runs)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Voxel dimension 1')
    ax.set_ylabel('Voxel dimension 2')

    # 3. Overlay before alignment
    ax = axes[0, 2]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(colors_half1[i, 0], colors_half1[i, 1],
                  s=200, c=c, edgecolors='blue', linewidth=2, alpha=0.5,
                  marker='o', label='Half 1' if i == 0 else '')
        ax.scatter(colors_half2[i, 0], colors_half2[i, 1],
                  s=200, c=c, edgecolors='red', linewidth=2, alpha=0.5,
                  marker='s', label='Half 2' if i == 0 else '')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title('정렬 전: 직접 비교\n→ 일치하지 않음', fontsize=12, fontweight='bold')
    ax.set_xlabel('Voxel dimension 1')
    ax.set_ylabel('Voxel dimension 2')

    # Procrustes alignment
    mtx1, mtx2_aligned, disparity = procrustes(colors_half1, colors_half2)

    # 4. After alignment
    ax = axes[1, 0]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(mtx1[i, 0], mtx1[i, 1],
                  s=200, c=c, edgecolors='blue', linewidth=2, alpha=0.5,
                  marker='o', label='Half 1' if i == 0 else '')
        ax.scatter(mtx2_aligned[i, 0], mtx2_aligned[i, 1],
                  s=200, c=c, edgecolors='red', linewidth=2, alpha=0.5,
                  marker='s', label='Half 2' if i == 0 else '')
        # Connection line
        ax.plot([mtx1[i, 0], mtx2_aligned[i, 0]],
               [mtx1[i, 1], mtx2_aligned[i, 1]],
               'k--', alpha=0.3, linewidth=1)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    stability = 1 - disparity
    ax.set_title(f'Procrustes 정렬 후\nStability = {stability:.3f}',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('Aligned dimension 1')
    ax.set_ylabel('Aligned dimension 2')

    # 5. Distance comparison
    ax = axes[1, 1]
    # Before alignment distances
    dists_before = []
    for i in range(len(colors_half1)):
        dist = np.linalg.norm(colors_half1[i] - colors_half2[i])
        dists_before.append(dist)

    # After alignment distances
    dists_after = []
    for i in range(len(mtx1)):
        dist = np.linalg.norm(mtx1[i] - mtx2_aligned[i])
        dists_after.append(dist)

    x = np.arange(len(color_names))
    width = 0.35
    ax.bar(x - width/2, dists_before, width, label='정렬 전', alpha=0.7, color='lightcoral')
    ax.bar(x + width/2, dists_after, width, label='정렬 후', alpha=0.7, color='lightblue')
    ax.set_xticks(x)
    ax.set_xticklabels(color_names, rotation=45, ha='right')
    ax.set_ylabel('Euclidean distance')
    ax.set_title('Color별 Half 1 vs Half 2 거리', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Summary metrics
    ax = axes[1, 2]
    ax.axis('off')

    # Calculate RDM correlation
    rdm1 = 1 - np.corrcoef(colors_half1)
    rdm2 = 1 - np.corrcoef(colors_half2)
    triu_idx = np.triu_indices(8, k=1)
    rdm_corr, _ = spearmanr(rdm1[triu_idx], rdm2[triu_idx])

    summary_text = f"""
    📊 요약 통계

    🔵 Procrustes Stability: {stability:.3f}
       → Pattern geometry 보존도
       → 1에 가까울수록 좋음

    📏 Disparity: {disparity:.3f}
       → 최적 정렬 후 남은 차이
       → 0에 가까울수록 좋음

    🔗 RDM Correlation: {rdm_corr:.3f}
       → 직접 비교 (정렬 없이)
       → 낮을 수 있음 (회전 때문)

    ✅ 해석:
    Procrustes 높음 ({stability:.2f})
    + RDM corr 낮음 ({rdm_corr:.2f})
    = 좌표계만 다름, 구조는 같음
    → SRM 필요!
    """

    ax.text(0.1, 0.5, summary_text, fontsize=11,
           verticalalignment='center', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig

def visualize_real_data_procrustes(subject_id='02', roi='V1'):
    """실제 데이터의 Procrustes 분석 시각화"""

    # Load data
    amplitudes = load_subject_amplitudes(subject_id, roi)
    metrics = compute_split_half_metrics(amplitudes)

    # PCA for visualization
    pca = PCA(n_components=2)
    half1_2d = pca.fit_transform(metrics['half1'])
    half2_2d = pca.transform(metrics['half2'])

    # Procrustes on 2D
    mtx1_2d, mtx2_2d_aligned, _ = procrustes(half1_2d, half2_2d)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    color_vals = ['red', 'orange', 'gold', 'green', 'cyan', 'blue', 'purple', 'magenta']

    # 1. Half 1 in PCA space
    ax = axes[0, 0]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(half1_2d[i, 0], half1_2d[i, 1],
                  s=200, c=c, edgecolors='black', linewidth=2, alpha=0.7)
        ax.text(half1_2d[i, 0], half1_2d[i, 1] + 0.3, name,
               ha='center', fontsize=9)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'Half 1 (sub-{subject_id} {roi})\nPCA 2D projection',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')

    # 2. Half 2 in PCA space
    ax = axes[0, 1]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(half2_2d[i, 0], half2_2d[i, 1],
                  s=200, c=c, edgecolors='black', linewidth=2, alpha=0.7)
        ax.text(half2_2d[i, 0], half2_2d[i, 1] + 0.3, name,
               ha='center', fontsize=9)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'Half 2 (sub-{subject_id} {roi})\nPCA 2D projection',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')

    # 3. Overlay before alignment
    ax = axes[0, 2]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(half1_2d[i, 0], half1_2d[i, 1],
                  s=200, c=c, edgecolors='blue', linewidth=2, alpha=0.5,
                  marker='o', label='Half 1' if i == 0 else '')
        ax.scatter(half2_2d[i, 0], half2_2d[i, 1],
                  s=200, c=c, edgecolors='red', linewidth=2, alpha=0.5,
                  marker='s', label='Half 2' if i == 0 else '')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title('정렬 전 비교', fontsize=12, fontweight='bold')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')

    # 4. After Procrustes alignment
    ax = axes[1, 0]
    for i, (name, c) in enumerate(zip(color_names, color_vals)):
        ax.scatter(mtx1_2d[i, 0], mtx1_2d[i, 1],
                  s=200, c=c, edgecolors='blue', linewidth=2, alpha=0.5,
                  marker='o', label='Half 1' if i == 0 else '')
        ax.scatter(mtx2_2d_aligned[i, 0], mtx2_2d_aligned[i, 1],
                  s=200, c=c, edgecolors='red', linewidth=2, alpha=0.5,
                  marker='s', label='Half 2' if i == 0 else '')
        ax.plot([mtx1_2d[i, 0], mtx2_2d_aligned[i, 0]],
               [mtx1_2d[i, 1], mtx2_2d_aligned[i, 1]],
               'k--', alpha=0.3, linewidth=1)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title(f'Procrustes 정렬 후\nStability = {metrics["procrustes_stability"]:.3f}',
                fontsize=12, fontweight='bold')
    ax.set_xlabel('Aligned PC1')
    ax.set_ylabel('Aligned PC2')

    # 5. RDM comparison
    ax = axes[1, 1]
    rdm_concat = np.hstack([metrics['rdm1'], metrics['rdm2']])
    im = ax.imshow(rdm_concat, cmap='RdYlBu_r', vmin=0, vmax=2)
    ax.axvline(7.5, color='black', linewidth=2)
    ax.set_xticks([3.5, 11.5])
    ax.set_xticklabels(['Half 1', 'Half 2'])
    ax.set_yticks(range(8))
    ax.set_yticklabels(color_names)
    ax.set_title('RDM 비교 (1-correlation)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax)

    # 6. Summary
    ax = axes[1, 2]
    ax.axis('off')

    summary_text = f"""
    📊 실제 데이터 분석 결과
    Subject: sub-{subject_id}
    ROI: {roi}
    Voxels: {amplitudes.shape[2]}

    🔵 Procrustes Stability:
       {metrics['procrustes_stability']:.3f}

    📏 Disparity:
       {metrics['procrustes_disparity']:.3f}

    🔗 RDM Correlation:
       {metrics['rdm_correlation']:.3f}

    ✅ 해석:
    """

    if metrics['procrustes_stability'] > 0.8:
        summary_text += "\n    매우 안정적인 패턴!\n    → 일관된 색 표상"
    elif metrics['procrustes_stability'] > 0.6:
        summary_text += "\n    적당히 안정적\n    → 개선 여지 있음"
    else:
        summary_text += "\n    불안정한 패턴\n    → 복셀 수 부족?"

    if metrics['procrustes_stability'] > 0.7 and metrics['rdm_correlation'] < 0.3:
        summary_text += "\n\n    좌표계 차이 문제\n    → SRM 강력 추천!"

    ax.text(0.1, 0.5, summary_text, fontsize=10,
           verticalalignment='center', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.tight_layout()
    return fig

def visualize_roi_comparison():
    """ROI별 Procrustes stability 비교"""

    import pandas as pd

    # Load results
    df = pd.read_csv('results/group_level/option1b_pattern_consistency/summary_results.csv')

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    rois = ['V1', 'V2', 'V3', 'hV4']
    subjects = ['02', '03', '05', '06', '07']

    # 1. Procrustes stability by ROI
    ax = axes[0, 0]
    data_by_roi = []
    for roi in rois:
        roi_data = df[df['roi'] == roi]['procrustes_stability'].values
        data_by_roi.append(roi_data)

    bp = ax.boxplot(data_by_roi, labels=rois, patch_artist=True, widths=0.6)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)

    # Overlay points
    for i, roi in enumerate(rois):
        roi_data = df[df['roi'] == roi]['procrustes_stability'].values
        x = np.random.normal(i+1, 0.04, size=len(roi_data))
        ax.scatter(x, roi_data, color='darkblue', s=50, alpha=0.6, zorder=3)

    ax.axhline(0.8, color='green', linestyle='--', linewidth=2, alpha=0.5, label='High (>0.8)')
    ax.axhline(0.6, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Moderate (>0.6)')
    ax.set_ylabel('Procrustes Stability', fontsize=12)
    ax.set_title('ROI별 Procrustes Stability', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 2. RDM correlation by ROI
    ax = axes[0, 1]
    data_by_roi = []
    for roi in rois:
        roi_data = df[df['roi'] == roi]['rdm_correlation'].values
        data_by_roi.append(roi_data)

    bp = ax.boxplot(data_by_roi, labels=rois, patch_artist=True, widths=0.6)
    for patch in bp['boxes']:
        patch.set_facecolor('lightcoral')
        patch.set_alpha(0.7)

    for i, roi in enumerate(rois):
        roi_data = df[df['roi'] == roi]['rdm_correlation'].values
        x = np.random.normal(i+1, 0.04, size=len(roi_data))
        ax.scatter(x, roi_data, color='darkred', s=50, alpha=0.6, zorder=3)

    ax.axhline(0.5, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Good (>0.5)')
    ax.axhline(0.3, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Moderate (>0.3)')
    ax.axhline(0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    ax.set_ylabel('RDM Correlation', fontsize=12)
    ax.set_title('ROI별 RDM Correlation', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 3. Procrustes vs RDM scatter
    ax = axes[1, 0]
    colors_roi = {'V1': 'red', 'V2': 'orange', 'V3': 'green', 'hV4': 'blue'}

    for roi in rois:
        roi_df = df[df['roi'] == roi]
        ax.scatter(roi_df['rdm_correlation'], roi_df['procrustes_stability'],
                  s=100, alpha=0.6, label=roi, color=colors_roi[roi])

    ax.axhline(0.8, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(0.3, color='gray', linestyle='--', alpha=0.3)
    ax.set_xlabel('RDM Correlation', fontsize=12)
    ax.set_ylabel('Procrustes Stability', fontsize=12)
    ax.set_title('Procrustes vs RDM Correlation', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add quadrant labels
    ax.text(0.5, 0.85, 'High Procrustes\nLow RDM\n→ SRM 필요',
           ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    ax.text(-0.2, 0.5, 'Low both\n→ 불안정',
           ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

    # 4. Summary table
    ax = axes[1, 1]
    ax.axis('off')

    summary_data = []
    for roi in rois:
        roi_df = df[df['roi'] == roi]
        summary_data.append([
            roi,
            f"{roi_df['procrustes_stability'].mean():.3f}",
            f"{roi_df['rdm_correlation'].mean():.3f}",
            f"{roi_df['n_voxels'].iloc[0]:.0f}",
        ])

    table = ax.table(cellText=summary_data,
                    colLabels=['ROI', 'Procrustes', 'RDM Corr', 'Voxels'],
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0.3, 1, 0.6])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)

    # Color code
    for i in range(1, len(summary_data) + 1):
        procrustes_val = float(summary_data[i-1][1])
        if procrustes_val > 0.8:
            color = 'lightgreen'
        elif procrustes_val > 0.6:
            color = 'lightyellow'
        else:
            color = 'lightcoral'
        table[(i, 1)].set_facecolor(color)

    ax.text(0.5, 0.1, '✅ Green: Procrustes > 0.8 (매우 좋음)\n⚠️ Yellow: 0.6-0.8 (보통)\n❌ Red: < 0.6 (낮음)',
           ha='center', fontsize=10,
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    return fig

def main():
    """메인 실행"""
    output_dir = Path('results/group_level/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Procrustes Analysis Visualization")
    print("=" * 80)

    # 1. Concept visualization
    print("\n1. Creating concept visualization...")
    fig1 = visualize_procrustes_concept()
    fig1.savefig(output_dir / 'procrustes_concept.png', dpi=300, bbox_inches='tight')
    print(f"   Saved: {output_dir / 'procrustes_concept.png'}")

    # 2. Real data visualization
    print("\n2. Creating real data visualization...")
    try:
        fig2 = visualize_real_data_procrustes(subject_id='02', roi='V1')
        fig2.savefig(output_dir / 'procrustes_real_data_sub02_V1.png', dpi=300, bbox_inches='tight')
        print(f"   Saved: {output_dir / 'procrustes_real_data_sub02_V1.png'}")
    except Exception as e:
        print(f"   ⚠️  Could not load real data: {e}")
        print("      (Run this on the server or with downloaded data)")

    # 3. ROI comparison
    print("\n3. Creating ROI comparison...")
    try:
        fig3 = visualize_roi_comparison()
        fig3.savefig(output_dir / 'procrustes_roi_comparison.png', dpi=300, bbox_inches='tight')
        print(f"   Saved: {output_dir / 'procrustes_roi_comparison.png'}")
    except Exception as e:
        print(f"   ⚠️  Could not create ROI comparison: {e}")

    print("\n" + "=" * 80)
    print("✅ Visualization complete!")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 80)

    plt.show()

if __name__ == '__main__':
    main()
