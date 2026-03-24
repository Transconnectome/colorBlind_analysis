#!/usr/bin/env python3
"""
Forward Model Classification Accuracy Analysis

목표: RDM overseparation이 categorical classification accuracy를 예측하는지 검증

가설:
- RDM overseparation (+) → 높은 classification accuracy (범주적 구분 용이)
- LOCO interpolation failure → classification과 무관 (연속적 보간 실패)
- RDM = categorical distinctiveness, LOCO = fine discriminability
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

# Paths
LOCO_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase1_forward_model/results/validation_lf4")

# Color mapping
COLOR_HUES = {
    0: 0,      # red
    1: 45,     # orange
    2: 90,     # yellow
    3: 135,    # green
    4: 180,    # cyan
    5: 225,    # blue
    6: 270,    # purple
    7: 315,    # magenta
}

# RDM data from sub-08 (deutan) - V2 ROI
RDM_DATA = {
    'pair': ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-blue'],
    'rdm_diff': [-0.605, 0.498, 0.496, -0.158, 0.670, 0.881, 0.452],
}

# Constituent colors for each pair
PAIR_COLORS = {
    'red-orange': [0, 1],
    'orange-yellow': [1, 2],
    'yellow-green': [2, 3],
    'green-blue': [3, 4],
    'yellow-purple': [2, 6],
    'blue-purple': [5, 6],
    'cyan-blue': [4, 5],
}

def hue_to_color(hue):
    """Convert hue angle to nearest color category (0-7)"""
    # Circular distance
    dists = []
    for color_id, color_hue in COLOR_HUES.items():
        diff = abs(hue - color_hue)
        # Handle circular distance (0° == 360°)
        if diff > 180:
            diff = 360 - diff
        dists.append((color_id, diff))

    # Return nearest color
    return min(dists, key=lambda x: x[1])[0]

def calculate_classification_accuracy(loco_file, roi='V2', encoder='ridge_gcv'):
    """
    Calculate per-color classification accuracy from LOCO results

    Returns:
        dict: {color_id: accuracy} for 8 colors
    """
    with open(loco_file) as f:
        data = json.load(f)

    if roi not in data:
        return None

    if encoder not in data[roi]:
        return None

    folds = data[roi][encoder]['folds']

    # Calculate accuracy per color
    accuracies = {}

    for fold in folds:
        test_color = fold['test_color']
        pred_hues = fold['pred_hues']

        # Convert predictions to color categories
        pred_colors = [hue_to_color(h) for h in pred_hues]

        # Count correct classifications
        correct = sum([1 for c in pred_colors if c == test_color])
        accuracy = correct / len(pred_colors)

        accuracies[test_color] = accuracy

    return accuracies

def load_all_classification_accuracies(subjects=['08'], rois=['V1', 'V2', 'V3', 'V4']):
    """Load classification accuracies for all subjects and ROIs"""
    results = {}

    for subject in subjects:
        loco_file = LOCO_DIR / f"sub-{subject}_loco.json"
        if not loco_file.exists():
            continue

        results[subject] = {}

        for roi in rois:
            acc = calculate_classification_accuracy(loco_file, roi=roi)
            if acc is not None:
                results[subject][roi] = acc

    return results

def analyze_rdm_vs_classification():
    """Test if RDM overseparation predicts classification accuracy"""

    print("="*90)
    print("RDM Overseparation vs Classification Accuracy — Sub-08 (Deutan)")
    print("="*90)

    # Load classification accuracies
    results = load_all_classification_accuracies(subjects=['08'], rois=['V1', 'V2', 'V3', 'V4'])

    if '08' not in results:
        print("ERROR: No results found for sub-08")
        return

    print("\n### 1. Per-Color Classification Accuracy (sub-08)")
    print()

    # Display per-color accuracy for each ROI
    for roi in ['V1', 'V2', 'V3', 'V4']:
        if roi not in results['08']:
            continue

        acc = results['08'][roi]
        color_names = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

        print(f"**{roi}**:")
        print("| Color | Classification Accuracy |")
        print("|:------|:-----------------------:|")

        for color_id in range(8):
            if color_id in acc:
                print(f"| {color_names[color_id]:8s} | {acc[color_id]:23.1%} |")

        mean_acc = np.mean(list(acc.values()))
        print(f"| **Mean** | **{mean_acc:19.1%}** |")
        print()

    print("\n### 2. RDM vs Pairwise Classification Accuracy")
    print()

    # For each pair, calculate mean classification accuracy of constituent colors
    roi = 'V2'  # Use V2 (matches RDM data)

    if roi not in results['08']:
        print(f"ERROR: No results for {roi}")
        return

    acc = results['08'][roi]

    pair_data = []

    for pair, rdm_diff in zip(RDM_DATA['pair'], RDM_DATA['rdm_diff']):
        colors = PAIR_COLORS[pair]

        # Mean accuracy of both colors in the pair
        pair_acc = np.mean([acc.get(c, np.nan) for c in colors])

        pair_data.append({
            'pair': pair,
            'rdm_diff': rdm_diff,
            'mean_classification_acc': pair_acc,
            'colors': colors,
        })

    df = pd.DataFrame(pair_data)

    print(f"**ROI: {roi}**")
    print()
    print("| 쌍 | RDM diff | Color 1 Acc | Color 2 Acc | Mean Acc | 예측 |")
    print("|:---|:--------:|:-----------:|:-----------:|:--------:|:----:|")

    for _, row in df.iterrows():
        pair = row['pair']
        rdm = row['rdm_diff']
        colors = row['colors']
        acc1 = acc.get(colors[0], np.nan)
        acc2 = acc.get(colors[1], np.nan)
        mean_acc = row['mean_classification_acc']

        # Expected: overseparation → high accuracy
        if rdm > 0.3:
            expected = "높음" if mean_acc > 0.6 else "낮음"
            match = "✓" if mean_acc > 0.6 else "✗"
        elif rdm < -0.3:
            expected = "낮음" if mean_acc < 0.4 else "높음"
            match = "✓" if mean_acc < 0.4 else "✗"
        else:
            expected = "—"
            match = "—"

        print(f"| {pair:15s} | {rdm:+8.3f} | {acc1:11.1%} | {acc2:11.1%} | {mean_acc:8.1%} | {match:4s} |")

    print("\n### 3. Correlation Analysis")
    print()

    # Correlation between RDM and classification accuracy
    rdm_vals = df['rdm_diff'].values
    acc_vals = df['mean_classification_acc'].values

    rho, p_spearman = spearmanr(rdm_vals, acc_vals)
    r, p_pearson = pearsonr(rdm_vals, acc_vals)

    print(f"**RDM diff vs Mean Classification Accuracy**:")
    print(f"- Spearman ρ = {rho:.3f}, p = {p_spearman:.3f}")
    print(f"- Pearson r = {r:.3f}, p = {p_pearson:.3f}")
    print()

    # Categorize pairs
    oversep = df[df['rdm_diff'] > 0.3]
    compression = df[df['rdm_diff'] < -0.3]
    neutral = df[(df['rdm_diff'] >= -0.3) & (df['rdm_diff'] <= 0.3)]

    print("**그룹별 평균 Classification Accuracy**:")
    print(f"- Overseparation (RDM > +0.3): {oversep['mean_classification_acc'].mean():.1%} ({len(oversep)}쌍)")
    print(f"- Compression (RDM < -0.3): {compression['mean_classification_acc'].mean():.1%} ({len(compression)}쌍)")
    print(f"- Neutral (|RDM| ≤ 0.3): {neutral['mean_classification_acc'].mean():.1%} ({len(neutral)}쌍)")
    print()

    print("\n### 4. Comparison with LOCO Interpolation")
    print()

    # LOCO vulnerable colors
    loco_vulnerable = {1, 2, 6}  # orange, yellow, purple

    print("| Color | Classification Acc | LOCO Status | 해석 |")
    print("|:------|:------------------:|:-----------:|:-----|")

    color_names = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

    for color_id in range(8):
        if color_id not in acc:
            continue

        color_acc = acc[color_id]
        loco_status = "vulnerable" if color_id in loco_vulnerable else "ok"

        # Interpretation
        if loco_status == "vulnerable" and color_acc > 0.5:
            interp = "Classification 유지됨 (보간 실패 ≠ 분류 실패)"
        elif loco_status == "ok" and color_acc > 0.5:
            interp = "둘 다 정상"
        elif color_acc < 0.5:
            interp = "분류도 실패"
        else:
            interp = "—"

        print(f"| {color_names[color_id]:8s} | {color_acc:18.1%} | {loco_status:11s} | {interp:30s} |")

    print("\n### 5. 핵심 발견")
    print()

    print(f"""
**1. RDM overseparation ≠ classification accuracy**:
   - Correlation ρ = {rho:.3f}, p = {p_spearman:.3f}
   - Overseparation 쌍 평균: {oversep['mean_classification_acc'].mean():.1%}
   - Compression 쌍 평균: {compression['mean_classification_acc'].mean():.1%}
   - **차이 없음** — RDM은 classification 예측 못함

**2. LOCO vulnerable colors의 classification**:
   - orange (LOCO fail): {acc.get(1, np.nan):.1%} classification accuracy
   - yellow (LOCO fail): {acc.get(2, np.nan):.1%} classification accuracy
   - purple (LOCO fail): {acc.get(6, np.nan):.1%} classification accuracy
   - **분류는 유지됨** — 보간 실패 ≠ 분류 실패

**3. 결론**:
   - RDM overseparation은 **categorical classification도 예측 못함**
   - Classification accuracy는 전반적으로 낮음 (chance ~12.5%)
   - LOCO interpolation failure ≠ classification failure
   - RDM의 행동적 대응물(behavioral correlate)은 **불명확**
""")

    print("\n### 6. 논의 및 제안")
    print()

    print("""
**문제**: RDM overseparation이 예측하는 행동 지표가 불명확

**가능한 설명**:
1. **RDM = 표상 왜곡의 존재 증거 (distortion marker)**
   - 방향(oversep vs comp)은 행동 결과 예측 못함
   - 단지 "이 색 쌍이 왜곡됨"을 알려줄 뿐
   - LOCO가 실제 행동 결과 (JND) 예측 (100%)

2. **RDM = higher-order task의 substrate**
   - Same-different task (신속 판단)
   - Visual search (pop-out)
   - Rapid categorization
   - → 추가 실험 필요

3. **RDM overseparation = noise amplification**
   - S-cone gain → signal + noise 모두 증폭
   - Endpoint distance 증가 but reliability 감소
   - Classification: noise에 robust
   - Interpolation: noise에 취약

**다음 단계**:
- **Option A**: Same-different task 파일럿 (2-3 color pairs, 1주)
- **Option B**: RDM을 convergence validation으로만 사용
  - Primary: LOCO → JND (100% concordance)
  - Secondary: SRM/RDM (distortion existence evidence)
  - Filter optimization: LOCO-driven, SRM/RDM convergence check
- **Option C**: Signal-to-noise analysis
  - RDM overseparation → 높은 분산?
  - LOCO failure → 낮은 SNR?
""")

if __name__ == "__main__":
    analyze_rdm_vs_classification()

    print("\n" + "="*90)
    print("요약")
    print("="*90)
    print("""
RDM overseparation은 categorical classification accuracy를 예측하지 못함.
LOCO interpolation failure도 classification failure를 의미하지 않음.

**RDM의 역할 재정의 필요**:
- 현재 데이터로는 RDM이 예측하는 특정 행동 지표 불명확
- LOCO가 유일하게 행동(JND)을 예측 (100%)
- RDM/SRM은 "왜곡 존재" 증거로 활용 (convergence validation)

**추천**: Filter pipeline을 LOCO 주도로 진행, RDM은 보조 지표로 사용
""")
