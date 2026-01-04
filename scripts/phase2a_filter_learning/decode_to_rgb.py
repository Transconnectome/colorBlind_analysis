#!/usr/bin/env python3
"""
방법 2: RGB Color Space로 역변환

필터링된 brain pattern을 실제 RGB 색상으로 디코딩하여
CVD 피험자가 어떤 색으로 지각할지 예측
"""

import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# 경로 설정
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
MODEL_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
OUTPUT_DIR = BASE_DIR / "results/filters/analysis/rgb_decoding"

# 8개 색상의 RGB 값 (0-1 normalized)
# HSV space에서 균등하게 나눈 circular colors
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

RGB_COLORS = {
    'Red':        [1.0, 0.0, 0.0],    # Hue 0°
    'Orange':     [1.0, 0.5, 0.0],    # Hue 45°
    'Yellow':     [1.0, 1.0, 0.0],    # Hue 90°
    'Chartreuse': [0.5, 1.0, 0.0],    # Hue 135°
    'Green':      [0.0, 1.0, 0.0],    # Hue 180°
    'Cyan':       [0.0, 1.0, 1.0],    # Hue 225°
    'Blue':       [0.0, 0.0, 1.0],    # Hue 270°
    'Magenta':    [1.0, 0.0, 1.0],    # Hue 315°
}

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']


def train_rgb_encoder(hc_pattern, rgb_values):
    """
    HC pattern을 사용하여 RGB → fMRI 인코딩 모델 학습

    Args:
        hc_pattern: (8, n_voxels) - HC mean pattern
        rgb_values: (8, 3) - RGB values for 8 colors

    Returns:
        model: Ridge regression model (RGB → fMRI)
        scaler: StandardScaler for fMRI patterns
    """
    # Ridge regression: RGB → fMRI
    # X: (8, 3) RGB
    # y: (8, n_voxels) fMRI

    # Standardize fMRI patterns (per voxel)
    scaler = StandardScaler()
    hc_pattern_scaled = scaler.fit_transform(hc_pattern.T).T  # (8, n_voxels)

    # Train Ridge regression
    model = Ridge(alpha=1.0)  # L2 regularization
    model.fit(rgb_values, hc_pattern_scaled)

    return model, scaler


def decode_to_rgb(fmri_pattern, model, scaler):
    """
    fMRI pattern을 RGB 색상으로 디코딩

    Args:
        fmri_pattern: (8, n_voxels) - fMRI pattern to decode
        model: trained Ridge model
        scaler: trained StandardScaler

    Returns:
        rgb_decoded: (8, 3) - decoded RGB colors
    """
    # Standardize input
    fmri_scaled = scaler.transform(fmri_pattern.T).T  # (8, n_voxels)

    # Decode using pseudo-inverse
    # model: y = X @ W + b
    # inverse: X = (y - b) @ W^+

    W = model.coef_  # (n_voxels, 3)
    b = model.intercept_  # (3,)

    # Pseudo-inverse
    W_pinv = np.linalg.pinv(W)  # (3, n_voxels)

    # Decode
    rgb_decoded = (fmri_scaled - b[np.newaxis, :]) @ W_pinv.T  # (8, 3)

    # Clip to [0, 1]
    rgb_decoded = np.clip(rgb_decoded, 0, 1)

    return rgb_decoded


def rgb_to_hex(rgb):
    """RGB (0-1) to hex color string"""
    r, g, b = [int(x * 255) for x in rgb]
    return f'#{r:02x}{g:02x}{b:02x}'


def compute_color_shift(rgb_before, rgb_after):
    """
    RGB 색상 변화 계산

    Returns:
        shift_distance: Euclidean distance in RGB space
        shift_hue: Hue shift in degrees
    """
    # Euclidean distance
    shift_distance = np.linalg.norm(rgb_after - rgb_before)

    # Hue shift (convert RGB → HSV)
    def rgb_to_hsv(rgb):
        r, g, b = rgb
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        if delta == 0:
            h = 0
        elif max_c == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_c == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

        return h

    hue_before = rgb_to_hsv(rgb_before)
    hue_after = rgb_to_hsv(rgb_after)

    # Angular difference (shortest path on circle)
    shift_hue = hue_after - hue_before
    if shift_hue > 180:
        shift_hue -= 360
    elif shift_hue < -180:
        shift_hue += 360

    return shift_distance, shift_hue


def analyze_subject_roi(subject_id, roi):
    """피험자-ROI별 RGB 디코딩 분석"""

    print(f"\n{'='*70}")
    print(f"RGB Decoding: sub-{subject_id} {roi}")
    print(f"{'='*70}")

    # 1. 데이터 로드
    hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

    # 2. 필터 로드
    model_dir = MODEL_DIR / f"sub-{subject_id}" / roi
    A = np.load(model_dir / "A_matrix.npy")
    b = np.load(model_dir / "b_vector.npy")

    # 3. Voxel alignment
    n_voxels = min(hc_pattern.shape[1], cvd_pattern.shape[1])
    hc_pattern = hc_pattern[:, :n_voxels]
    cvd_pattern = cvd_pattern[:, :n_voxels]

    # 4. 필터 적용
    filtered_pattern = cvd_pattern @ A + b[np.newaxis, :]

    # 5. RGB 값 준비
    rgb_true = np.array([RGB_COLORS[color] for color in COLOR_NAMES])  # (8, 3)

    # 6. RGB 인코더 학습 (HC pattern 사용)
    print("\nTraining RGB encoder (HC pattern)...")
    encoder, scaler = train_rgb_encoder(hc_pattern, rgb_true)
    print(f"  Encoder R² score: {encoder.score(rgb_true, scaler.transform(hc_pattern.T).T):.3f}")

    # 7. Before/After 디코딩
    print("\nDecoding CVD patterns to RGB...")
    rgb_before = decode_to_rgb(cvd_pattern, encoder, scaler)
    rgb_after = decode_to_rgb(filtered_pattern, encoder, scaler)

    # 8. 분석
    results = []
    for i, color_name in enumerate(COLOR_NAMES):
        true_rgb = rgb_true[i]
        before_rgb = rgb_before[i]
        after_rgb = rgb_after[i]

        # Shift 계산
        shift_dist_before, shift_hue_before = compute_color_shift(true_rgb, before_rgb)
        shift_dist_after, shift_hue_after = compute_color_shift(true_rgb, after_rgb)

        # Improvement
        improvement = shift_dist_before - shift_dist_after
        improvement_pct = (improvement / shift_dist_before) * 100 if shift_dist_before > 0 else 0

        results.append({
            'color': color_name,
            'true_r': true_rgb[0],
            'true_g': true_rgb[1],
            'true_b': true_rgb[2],
            'before_r': before_rgb[0],
            'before_g': before_rgb[1],
            'before_b': before_rgb[2],
            'after_r': after_rgb[0],
            'after_g': after_rgb[1],
            'after_b': after_rgb[2],
            'shift_dist_before': shift_dist_before,
            'shift_dist_after': shift_dist_after,
            'shift_hue_before': shift_hue_before,
            'shift_hue_after': shift_hue_after,
            'improvement': improvement,
            'improvement_pct': improvement_pct
        })

    df = pd.DataFrame(results)

    # 9. 출력
    print(f"\n{'Color':<12} {'True RGB':>20} {'Before RGB':>20} {'After RGB':>20} {'Shift Before':>12} {'Shift After':>12} {'Improv%':>10}")
    print("-" * 120)
    for _, row in df.iterrows():
        true_str = f"({row['true_r']:.2f},{row['true_g']:.2f},{row['true_b']:.2f})"
        before_str = f"({row['before_r']:.2f},{row['before_g']:.2f},{row['before_b']:.2f})"
        after_str = f"({row['after_r']:.2f},{row['after_g']:.2f},{row['after_b']:.2f})"

        print(f"{row['color']:<12} {true_str:>20} {before_str:>20} {after_str:>20} "
              f"{row['shift_dist_before']:>12.3f} {row['shift_dist_after']:>12.3f} {row['improvement_pct']:>10.1f}%")

    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Mean RGB shift before: {df['shift_dist_before'].mean():.3f}")
    print(f"  Mean RGB shift after:  {df['shift_dist_after'].mean():.3f}")
    print(f"  Mean improvement:      {df['improvement_pct'].mean():.1f}%")

    return df


def visualize_rgb_shifts(df, subject_id, roi, output_dir):
    """RGB 변화 시각화"""

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. RGB distance shifts
    ax = axes[0]
    x = np.arange(len(COLOR_NAMES))
    ax.bar(x - 0.2, df['shift_dist_before'], width=0.4, alpha=0.7, label='Before', color='red')
    ax.bar(x + 0.2, df['shift_dist_after'], width=0.4, alpha=0.7, label='After', color='green')
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('RGB Distance from True')
    ax.set_title(f'RGB Color Shift\nsub-{subject_id} {roi}')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 2. Color swatches - Before
    ax = axes[1]
    ax.set_xlim(0, 3)
    ax.set_ylim(0, len(COLOR_NAMES))
    ax.set_xticks([0.5, 1.5, 2.5])
    ax.set_xticklabels(['True', 'CVD Before', 'CVD After'])
    ax.set_yticks(np.arange(len(COLOR_NAMES)) + 0.5)
    ax.set_yticklabels(COLOR_NAMES)
    ax.set_title('Color Swatches')

    for i, row in df.iterrows():
        # True color
        true_rgb = [row['true_r'], row['true_g'], row['true_b']]
        rect = mpatches.Rectangle((0, i), 1, 1, facecolor=true_rgb, edgecolor='black')
        ax.add_patch(rect)

        # Before filtering
        before_rgb = [row['before_r'], row['before_g'], row['before_b']]
        rect = mpatches.Rectangle((1, i), 1, 1, facecolor=before_rgb, edgecolor='black')
        ax.add_patch(rect)

        # After filtering
        after_rgb = [row['after_r'], row['after_g'], row['after_b']]
        rect = mpatches.Rectangle((2, i), 1, 1, facecolor=after_rgb, edgecolor='black')
        ax.add_patch(rect)

    ax.set_aspect('equal')
    ax.invert_yaxis()

    # 3. Hue shifts
    ax = axes[2]
    ax.scatter(df['shift_hue_before'], x, alpha=0.7, s=100, label='Before', color='red')
    ax.scatter(df['shift_hue_after'], x, alpha=0.7, s=100, label='After', color='green')
    ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
    ax.set_yticks(x)
    ax.set_yticklabels(COLOR_NAMES)
    ax.set_xlabel('Hue Shift (degrees)')
    ax.set_title('Hue Shift from True Color')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()

    # 저장
    output_file = output_dir / f"sub-{subject_id}_{roi}_rgb_decoding.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: {output_file}")
    plt.close()


def main():
    """메인 실행"""

    print("=" * 70)
    print("RGB Color Decoding Analysis")
    print("Method 2: Decode filtered brain patterns to RGB colors")
    print("=" * 70)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    for subject in CVD_SUBJECTS:
        for roi in ROIS:
            # 분석
            df = analyze_subject_roi(subject, roi)
            df['subject'] = subject
            df['roi'] = roi
            all_results.append(df)

            # 시각화
            subject_output_dir = OUTPUT_DIR / f"sub-{subject}"
            subject_output_dir.mkdir(exist_ok=True)
            visualize_rgb_shifts(df, subject, roi, subject_output_dir)

            # CSV 저장
            csv_file = subject_output_dir / f"sub-{subject}_{roi}_rgb_decoding.csv"
            df.to_csv(csv_file, index=False)
            print(f"CSV saved: {csv_file}")

    # 전체 결과 통합
    all_df = pd.concat(all_results, ignore_index=True)
    all_csv = OUTPUT_DIR / "all_rgb_decoding.csv"
    all_df.to_csv(all_csv, index=False)

    # 전체 요약
    print("\n" + "=" * 70)
    print("Overall Summary (all subjects, all ROIs)")
    print("=" * 70)
    print(f"\nMean RGB shift before: {all_df['shift_dist_before'].mean():.3f}")
    print(f"Mean RGB shift after:  {all_df['shift_dist_after'].mean():.3f}")
    print(f"Mean improvement:      {all_df['improvement_pct'].mean():.1f}%")

    # 색상별 평균
    print("\nPer-color average improvement:")
    color_summary = all_df.groupby('color')['improvement_pct'].mean().sort_values(ascending=False)
    for color, improvement in color_summary.items():
        print(f"  {color:<12}: {improvement:>6.1f}%")

    print(f"\nAll results saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
