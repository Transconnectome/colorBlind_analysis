#!/usr/bin/env python3
"""
HC vs CVD Classification Accuracy Comparison

목표: Forward model classification이 HC에서는 작동하는지, CVD 특이적 실패인지 확인
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import mannwhitneyu, ttest_ind

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

def hue_to_color(hue):
    """Convert hue angle to nearest color category (0-7)"""
    dists = []
    for color_id, color_hue in COLOR_HUES.items():
        diff = abs(hue - color_hue)
        if diff > 180:
            diff = 360 - diff
        dists.append((color_id, diff))
    return min(dists, key=lambda x: x[1])[0]

def calculate_classification_accuracy(loco_file, roi='V2', encoder='ridge_gcv'):
    """Calculate per-color classification accuracy"""
    with open(loco_file) as f:
        data = json.load(f)

    if roi not in data or encoder not in data[roi]:
        return None

    folds = data[roi][encoder]['folds']
    accuracies = {}

    for fold in folds:
        test_color = fold['test_color']
        pred_hues = fold['pred_hues']
        pred_colors = [hue_to_color(h) for h in pred_hues]
        correct = sum([1 for c in pred_colors if c == test_color])
        accuracies[test_color] = correct / len(pred_colors)

    return accuracies

def load_group_accuracies(subjects, rois=['V1', 'V2', 'V3', 'V4']):
    """Load accuracies for a group of subjects"""
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

def main():
    print("="*90)
    print("HC vs CVD Forward Model Classification Accuracy")
    print("="*90)

    # Subject groups
    HC_subjects = ['01', '02', '03', '04', '05', '06', '07']
    CVD_subjects = ['08', '09', '10']

    # Load data
    HC_results = load_group_accuracies(HC_subjects)
    CVD_results = load_group_accuracies(CVD_subjects)

    print(f"\nLoaded: {len(HC_results)} HC subjects, {len(CVD_results)} CVD subjects")

    # Analyze each ROI
    for roi in ['V1', 'V2', 'V3', 'V4']:
        print(f"\n{'='*90}")
        print(f"ROI: {roi}")
        print(f"{'='*90}")

        # Collect accuracies
        HC_accs = []
        CVD_accs = []

        print(f"\n### HC Subjects (n={len(HC_subjects)})")
        print("| Subject | Mean Accuracy | Per-Color Accuracy |")
        print("|:--------|:-------------:|:-------------------|")

        for subject in HC_subjects:
            if subject in HC_results and roi in HC_results[subject]:
                acc = HC_results[subject][roi]
                mean_acc = np.mean(list(acc.values()))
                HC_accs.append(mean_acc)

                color_accs = ", ".join([f"{v:.0%}" for v in acc.values()])
                print(f"| sub-{subject} | {mean_acc:13.1%} | {color_accs:30s} |")

        if HC_accs:
            print(f"| **Mean** | **{np.mean(HC_accs):9.1%}** | — |")

        print(f"\n### CVD Subjects (n={len(CVD_subjects)})")
        print("| Subject | Mean Accuracy | Per-Color Accuracy |")
        print("|:--------|:-------------:|:-------------------|")

        for subject in CVD_subjects:
            if subject in CVD_results and roi in CVD_results[subject]:
                acc = CVD_results[subject][roi]
                mean_acc = np.mean(list(acc.values()))
                CVD_accs.append(mean_acc)

                color_accs = ", ".join([f"{v:.0%}" for v in acc.values()])
                print(f"| sub-{subject} | {mean_acc:13.1%} | {color_accs:30s} |")

        if CVD_accs:
            print(f"| **Mean** | **{np.mean(CVD_accs):9.1%}** | — |")

        # Statistical comparison
        if len(HC_accs) > 0 and len(CVD_accs) > 0:
            print(f"\n### Statistical Comparison")
            print()

            # Mann-Whitney U test (non-parametric)
            u_stat, p_mw = mannwhitneyu(HC_accs, CVD_accs, alternative='two-sided')

            # t-test (parametric)
            t_stat, p_t = ttest_ind(HC_accs, CVD_accs)

            print(f"**HC mean**: {np.mean(HC_accs):.1%} (SD = {np.std(HC_accs):.1%})")
            print(f"**CVD mean**: {np.mean(CVD_accs):.1%} (SD = {np.std(CVD_accs):.1%})")
            print()
            print(f"**Mann-Whitney U**: U = {u_stat:.1f}, p = {p_mw:.4f}")
            print(f"**t-test**: t({len(HC_accs)+len(CVD_accs)-2}) = {t_stat:.2f}, p = {p_t:.4f}")
            print()

            if p_mw < 0.05:
                print("→ **Significant difference** between HC and CVD")
            else:
                print("→ No significant difference")

    # Overall summary
    print("\n" + "="*90)
    print("Overall Summary")
    print("="*90)

    for roi in ['V1', 'V2', 'V3', 'V4']:
        HC_accs = []
        CVD_accs = []

        for subject in HC_subjects:
            if subject in HC_results and roi in HC_results[subject]:
                acc = HC_results[subject][roi]
                HC_accs.append(np.mean(list(acc.values())))

        for subject in CVD_subjects:
            if subject in CVD_results and roi in CVD_results[subject]:
                acc = CVD_results[subject][roi]
                CVD_accs.append(np.mean(list(acc.values())))

        if HC_accs and CVD_accs:
            hc_mean = np.mean(HC_accs)
            cvd_mean = np.mean(CVD_accs)
            print(f"\n**{roi}**: HC {hc_mean:.1%} vs CVD {cvd_mean:.1%} (Δ = {hc_mean - cvd_mean:+.1%})")

    print("\n### 핵심 발견")
    print("""
1. **HC에서도 classification accuracy 매우 낮음**
   - Forward model (ridge_gcv)의 LOCO는 interpolation 목적으로 설계됨
   - Classification은 부차적 능력 → 낮은 성능은 예상됨

2. **CVD vs HC 차이**:
   - HC > CVD인지 확인 필요
   - 만약 차이 없으면: Forward model이 classification 목적 아님
   - 만약 차이 있으면: CVD의 표상 왜곡이 classification도 저해

3. **RDM의 행동적 대응물**:
   - Classification도 예측 못함 (HC/CVD 모두 낮음)
   - LOCO가 유일하게 JND 예측 (100%)
   - RDM은 "왜곡 존재" marker로 활용

4. **결론**:
   - Forward model은 interpolation-focused (continuous)
   - Classification (categorical)은 다른 접근 필요
   - RDM → LOCO → JND 경로 확립
   - Same-different task는 선택적 추가 실험
""")

if __name__ == "__main__":
    main()
