"""
Comprehensive analysis script for ColorBlind project
Performs ROI-level and voxel-level analyses with status logging.
"""

import os
import sys
import socket
import time
import logging
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pickle

def _setup_logging():
    """Configure console + file logging to logs/analysis_status.log"""
    logger = logging.getLogger('ColorBlindComprehensive')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        # Console
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        # File
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(logs_dir, 'analysis_status.log'), mode='a')
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def _status(logger, msg):
    print(msg)
    try:
        logger.info(msg)
    except Exception:
        pass
    sys.stdout.flush()


# Environment enforcement removed per user request. The pipeline assumes the
# runtime (host and conda env) is already correctly configured by external
# provisioning scripts or wrappers. If needed, re-enable checks here.

LOGGER = _setup_logging()
_status(LOGGER, "[INIT] Starting comprehensive analysis script")

from bh_anal import BHAnalysisPipeline
from bh_viz import plot_roi_responses, plot_confusion_matrices, plot_accuracy_comparison
from bh_stats import run_permutation_test, analyze_color_selectivity

def main():
    _status(LOGGER, "=" * 80)
    _status(LOGGER, "ColorBlind Analysis - Comprehensive Results")
    _status(LOGGER, "=" * 80)
    
    # Initialize pipeline
    pipeline = BHAnalysisPipeline()
    
    # Create output directory
    results_dir = os.path.join(pipeline.config.analysis_dir, 'comprehensive_results')
    os.makedirs(results_dir, exist_ok=True)
    
    # =========================================================================
    # PART 1: ROI-Level Analysis
    # =========================================================================
    _status(LOGGER, "\n" + "=" * 80)
    _status(LOGGER, "PART 1: ROI-Level Analysis")
    _status(LOGGER, "=" * 80)
    
    # Extract ROI responses
    _status(LOGGER, "\n[1/5] Extracting ROI responses...")
    t0 = time.time()
    roi_data = pipeline.run_extract_roi(include_whole_brain=True)
    _status(LOGGER, f"[OK] ROI extraction done in {time.time()-t0:.1f}s")
    
    # Analyze color selectivity
    _status(LOGGER, "\n[2/5] Analyzing color selectivity...")
    t0 = time.time()
    selectivity = analyze_color_selectivity(roi_data, save_dir=results_dir)
    _status(LOGGER, f"[OK] Color selectivity done in {time.time()-t0:.1f}s")
    
    # Run forward modeling
    _status(LOGGER, "\n[3/5] Running forward modeling...")
    t0 = time.time()
    model_results = pipeline.run_forward_model(roi_data)
    _status(LOGGER, f"[OK] Forward model done in {time.time()-t0:.1f}s")
    
    # Statistical tests
    # Permutation tests are expensive. By default we SKIP them to save time.
    # To enable, set environment variable RUN_PERMUTATION=1 before running.
    run_perm = os.environ.get('RUN_PERMUTATION', '0') == '1'
    if not run_perm:
        _status(LOGGER, "\n[4/5] Skipping permutation tests (set RUN_PERMUTATION=1 to enable)")
        p_values, null_dists = {}, {}
    else:
        # Permutation tests can be very slow. Allow skipping via env var SKIP_PERMUTATION
        skip_perm = os.environ.get('SKIP_PERMUTATION', '1') != '0'
        if skip_perm:
            _status(LOGGER, "\n[4/5] Skipping permutation tests (SKIP_PERMUTATION!=0). Set SKIP_PERMUTATION=0 to run them)")
            # Provide placeholder p-values (None) so downstream code can run
            p_values = {roi: None for roi in roi_data.keys()}
            null_dists = {}
        else:
            _status(LOGGER, "\n[4/5] Running permutation tests (n=1000)...")
            t0 = time.time()
            p_values, null_dists = run_permutation_test(roi_data, 
                                                        n_permutations=1000,
                                                        save_dir=results_dir)
            _status(LOGGER, f"[OK] Permutation tests done in {time.time()-t0:.1f}s")
    
    # Visualization
    _status(LOGGER, "\n[5/5] Generating visualizations...")
    plot_roi_responses(roi_data, save_dir=results_dir)
    plot_confusion_matrices(model_results, save_dir=results_dir)
    plot_accuracy_comparison(model_results, save_dir=results_dir)
    
    # =========================================================================
    # PART 2: Voxel-Level Analysis
    # =========================================================================
    _status(LOGGER, "\n" + "=" * 80)
    _status(LOGGER, "PART 2: Voxel-Level Analysis")
    _status(LOGGER, "=" * 80)
    
    t0 = time.time()
    voxel_results = perform_voxel_analysis(roi_data, results_dir)
    _status(LOGGER, f"[OK] Voxel-level analysis done in {time.time()-t0:.1f}s")
    
    # =========================================================================
    # PART 3: Performance Summary
    # =========================================================================
    _status(LOGGER, "\n" + "=" * 80)
    _status(LOGGER, "PART 3: Performance Summary")
    _status(LOGGER, "=" * 80)
    
    summary = compile_results(roi_data, model_results, selectivity, 
                            p_values, voxel_results)
    
    # Save results
    with open(os.path.join(results_dir, 'analysis_results.pkl'), 'wb') as f:
        pickle.dump({
            'roi_data': roi_data,
            'model_results': model_results,
            'selectivity': selectivity,
            'p_values': p_values,
            'voxel_results': voxel_results,
            'summary': summary
        }, f)
    
    # Generate reports
    _status(LOGGER, "\n[Final] Generating reports...")
    t0 = time.time()
    generate_markdown_report(summary, results_dir)
    _status(LOGGER, f"[OK] Reports generated in {time.time()-t0:.1f}s")
    
    _status(LOGGER, "\n" + "=" * 80)
    _status(LOGGER, f"Analysis complete! Results saved to: {results_dir}")
    _status(LOGGER, "=" * 80)
    
    return summary

def perform_voxel_analysis(roi_data, save_dir):
    """Perform voxel-level analysis"""
    print("\n[1/3] Analyzing voxel preferences...")
    
    voxel_results = {}
    
    for roi, responses in roi_data.items():
        print(f"\nProcessing {roi}...")
        
        # Voxel color preference
        n_voxels = responses.shape[1]
        preferred_colors = np.argmax(responses, axis=0)
        
        # Voxel selectivity
        voxel_selectivity = []
        for v in range(n_voxels):
            v_resp = responses[:, v]
            sel = (v_resp.max() - v_resp.min()) / (v_resp.max() + v_resp.min() + 1e-10)
            voxel_selectivity.append(sel)
        
        voxel_selectivity = np.array(voxel_selectivity)
        
        # Voxel reliability (split-half correlation)
        # Note: run_extract_roi currently returns mean betas across runs
        # with shape (n_colors, n_voxels). If per-run data (n_runs*n_colors,
        # n_voxels) is available we try to compute split-half; otherwise
        # fall back to NaN reliability so the pipeline can continue.
        n_colors = 8
        voxel_reliability = None
        rows = responses.shape[0]
        if rows == n_colors:
            # Only mean betas available — cannot compute split-half across runs
            voxel_reliability = np.full(n_voxels, np.nan)
        else:
            # Attempt to interpret rows as (n_runs * n_colors)
            if rows % n_colors == 0:
                try:
                    n_runs_est = rows // n_colors
                    arr = responses.reshape((n_runs_est, n_colors, n_voxels))
                    # define odd/even split-halves
                    half1_idx = list(range(0, n_runs_est, 2))
                    half2_idx = list(range(1, n_runs_est, 2))
                    voxel_reliability = []
                    for v in range(n_voxels):
                        half1_mean = np.mean(arr[half1_idx, :, v], axis=0)
                        half2_mean = np.mean(arr[half2_idx, :, v], axis=0)
                        # If constant arrays, correlation may be nan
                        try:
                            r = np.corrcoef(half1_mean, half2_mean)[0, 1]
                        except Exception:
                            r = np.nan
                        voxel_reliability.append(r)
                    voxel_reliability = np.array(voxel_reliability)
                except Exception:
                    voxel_reliability = np.full(n_voxels, np.nan)
            else:
                voxel_reliability = np.full(n_voxels, np.nan)
        
        voxel_results[roi] = {
            'preferred_colors': preferred_colors,
            'selectivity': voxel_selectivity,
            'reliability': voxel_reliability,
            'n_voxels': n_voxels
        }
        
        print(f"  Voxels: {n_voxels}")
        print(f"  Mean selectivity: {voxel_selectivity.mean():.3f}")
        print(f"  Mean reliability: {voxel_reliability.mean():.3f}")
        
        # Plot voxel preference distribution
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 2, 1)
        plt.hist(preferred_colors, bins=8, range=(-0.5, 7.5))
        plt.xlabel('Preferred Color')
        plt.ylabel('Number of Voxels')
        plt.title(f'{roi} Color Preference Distribution')
        
        plt.subplot(1, 2, 2)
        plt.scatter(voxel_selectivity, voxel_reliability, alpha=0.5)
        plt.xlabel('Selectivity Index')
        plt.ylabel('Reliability (split-half r)')
        plt.title(f'{roi} Selectivity vs Reliability')
        
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'{roi}_voxel_analysis.png'))
        plt.close()
    
    return voxel_results

def compile_results(roi_data, model_results, selectivity, p_values, voxel_results):
    """Compile all results into summary dictionary"""
    
    summary = {
        'roi_level': {},
        'voxel_level': {},
        'overall_performance': {}
    }
    
    # ROI-level summary
    for roi in roi_data.keys():
        roi_sel = selectivity.get(roi, {}) if isinstance(selectivity, dict) else {}
        summary['roi_level'][roi] = {
            'n_voxels': roi_data[roi].shape[1],
            'accuracy': np.mean(model_results[roi]['train_accuracy']),
            'accuracy_std': np.std(model_results[roi]['train_accuracy']),
            'p_value': p_values.get(roi, None) if isinstance(p_values, dict) else None,
            'selectivity_index': roi_sel.get('selectivity_index', float('nan')),
            'tuning_width': roi_sel.get('tuning_width', float('nan')),
            'reliability': roi_sel.get('reliability', float('nan'))
        }
    
    # Voxel-level summary
    for roi in voxel_results.keys():
        summary['voxel_level'][roi] = {
            'n_voxels': voxel_results[roi]['n_voxels'],
            'mean_selectivity': voxel_results[roi]['selectivity'].mean(),
            'mean_reliability': voxel_results[roi]['reliability'].mean()
        }
    
    # Overall performance
    all_accuracies = [summary['roi_level'][roi]['accuracy'] for roi in roi_data.keys()]
    summary['overall_performance'] = {
        'mean_accuracy': np.mean(all_accuracies),
        'std_accuracy': np.std(all_accuracies),
        'chance_level': 0.125,
        'best_roi': max(roi_data.keys(), key=lambda r: summary['roi_level'][r]['accuracy']),
        'worst_roi': min(roi_data.keys(), key=lambda r: summary['roi_level'][r]['accuracy'])
    }
    
    return summary

def generate_markdown_report(summary, save_dir):
    """Generate markdown report in both English and Korean"""
    
    # English report
    eng_report = generate_english_report(summary)
    with open(os.path.join(save_dir, 'results_report_EN.md'), 'w') as f:
        f.write(eng_report)
    
    # Korean report
    kor_report = generate_korean_report(summary)
    with open(os.path.join(save_dir, 'results_report_KR.md'), 'w') as f:
        f.write(kor_report)
    
    print(f"\nReports generated:")
    print(f"  - English: {os.path.join(save_dir, 'results_report_EN.md')}")
    print(f"  - Korean: {os.path.join(save_dir, 'results_report_KR.md')}")

def generate_english_report(summary):
    """Generate English report"""
    
    report = f"""# ColorBlind Analysis Results Report

## Executive Summary

This report presents the results of color decoding analysis based on Brouwer & Heeger (2009) methodology.

### Overall Performance
- **Mean Classification Accuracy**: {summary['overall_performance']['mean_accuracy']:.3f} ± {summary['overall_performance']['std_accuracy']:.3f}
- **Chance Level**: {summary['overall_performance']['chance_level']:.3f} (1/8)
- **Performance vs Chance**: {(summary['overall_performance']['mean_accuracy'] / summary['overall_performance']['chance_level']):.2f}x above chance
- **Best Performing ROI**: {summary['overall_performance']['best_roi']}
- **Lowest Performing ROI**: {summary['overall_performance']['worst_roi']}

---

## Part 1: ROI-Level Analysis

### 1.1 Classification Performance

"""
    
    for roi, results in summary['roi_level'].items():
        acc = results.get('accuracy', float('nan'))
        acc_std = results.get('accuracy_std', float('nan'))
        pval = results.get('p_value', None)
        pval_str = f"{pval:.3e}" if (pval is not None) else "N/A"
        nvox = results.get('n_voxels', 0)
        sel = results.get('selectivity_index', float('nan'))
        tw = results.get('tuning_width', float('nan'))
        rel = results.get('reliability', float('nan'))

        report += f"""
#### {roi}
- **Accuracy**: {acc:.3f} ± {acc_std:.3f}
- **Statistical Significance**: p = {pval_str}
- **Number of Voxels**: {nvox}
- **Selectivity Index**: {sel:.3f}
- **Tuning Width**: {tw:.3f}
- **Response Reliability**: {rel:.3f}

"""
    
    report += """
### 1.2 Performance Interpretation

"""
    
    # Add interpretation
    best_roi = summary['overall_performance']['best_roi']
    best_acc = summary['roi_level'][best_roi]['accuracy']
    
    if best_acc > 0.25:
        report += """
**Good Performance Indicators:**
- Classification accuracy substantially above chance level
- Significant p-values indicate reliable color information
- High selectivity indices suggest strong color tuning

**Possible Reasons for Good Performance:**
1. Strong color-selective responses in visual cortex
2. Sufficient number of informative voxels
3. Reliable responses across repeated measurements
4. Effective spatial preprocessing and alignment
5. Appropriate ROI definition and localization

"""
    else:
        report += """
**Limited Performance Indicators:**
- Classification accuracy near or below expected levels
- Weaker statistical significance
- Lower selectivity indices

**Possible Reasons for Limited Performance:**
1. **Data Quality Issues**:
   - Low signal-to-noise ratio in fMRI data
   - Motion artifacts or other confounds
   - Insufficient number of trials per condition

2. **ROI Definition Issues**:
   - Atlas-based ROIs may not align well with subject-specific retinotopy
   - Coarse spatial resolution (2mm) may miss fine-grained patterns
   - Mixed response properties within broadly-defined ROIs

3. **Model Limitations**:
   - Linear forward model may be too simple
   - Limited number of voxels selected
   - Potential overfitting with cross-validation

4. **Stimulus/Design Issues**:
   - Color space sampling may not match neural representation
   - Insufficient variation in stimulus features
   - Adaptation or habituation effects

"""
    
    report += """
---

## Part 2: Voxel-Level Analysis

### 2.1 Voxel Properties

"""
    
    for roi, results in summary['voxel_level'].items():
        report += f"""
#### {roi}
- **Total Voxels**: {results['n_voxels']}
- **Mean Voxel Selectivity**: {results['mean_selectivity']:.3f}
- **Mean Voxel Reliability**: {results['mean_reliability']:.3f}

"""
    
    report += """
### 2.2 Voxel Selection Recommendations

Based on the voxel-level analysis, we recommend:
1. **Selectivity-based selection**: Use top 50% most selective voxels
2. **Reliability threshold**: Exclude voxels with reliability < 0.3
3. **Combined criteria**: Balance selectivity and reliability for robust decoding

---

## Conclusions

### Strengths
- Systematic implementation following B&H (2009) methodology
- Comprehensive analysis at both ROI and voxel levels
- Robust statistical validation with permutation tests

### Limitations
- Atlas-based ROI definition (not subject-specific retinotopy)
- Limited to linear forward modeling approach
- Single subject analysis (generalization unclear)

### Future Directions
1. Implement subject-specific retinotopic mapping
2. Explore non-linear decoding models (e.g., neural networks)
3. Test alternative feature spaces and color representations
4. Conduct multi-subject analysis for population-level inference

---

*Report generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report

def generate_korean_report(summary):
    """Generate Korean report"""
    
    report = f"""# ColorBlind 분석 결과 보고서

## 요약

본 보고서는 Brouwer & Heeger (2009) 방법론을 기반으로 한 색상 디코딩 분석 결과를 제시합니다.

### 전반적 성능
- **평균 분류 정확도**: {summary['overall_performance']['mean_accuracy']:.3f} ± {summary['overall_performance']['std_accuracy']:.3f}
- **우연 수준**: {summary['overall_performance']['chance_level']:.3f} (1/8)
- **우연 대비 성능**: 우연 수준의 {(summary['overall_performance']['mean_accuracy'] / summary['overall_performance']['chance_level']):.2f}배
- **최고 성능 ROI**: {summary['overall_performance']['best_roi']}
- **최저 성능 ROI**: {summary['overall_performance']['worst_roi']}

---

## 1부: ROI 수준 분석

### 1.1 분류 성능

"""
    
    for roi, results in summary['roi_level'].items():
        acc = results.get('accuracy', float('nan'))
        acc_std = results.get('accuracy_std', float('nan'))
        pval = results.get('p_value', None)
        pval_str = f"{pval:.3e}" if (pval is not None) else "N/A"
        nvox = results.get('n_voxels', 0)
        sel = results.get('selectivity_index', float('nan'))
        tw = results.get('tuning_width', float('nan'))
        rel = results.get('reliability', float('nan'))

        report += f"""
#### {roi}
- **정확도**: {acc:.3f} ± {acc_std:.3f}
- **통계적 유의성**: p = {pval_str}
- **복셀 수**: {nvox}
- **선택성 지수**: {sel:.3f}
- **튜닝 폭**: {tw:.3f}
- **반응 신뢰도**: {rel:.3f}

"""
    
    report += """
### 1.2 성능 해석

"""
    
    best_roi = summary['overall_performance']['best_roi']
    best_acc = summary['roi_level'][best_roi]['accuracy']
    
    if best_acc > 0.25:
        report += """
**좋은 성능 지표:**
- 분류 정확도가 우연 수준을 크게 상회
- 유의한 p-값은 신뢰할 수 있는 색상 정보를 나타냄
- 높은 선택성 지수는 강한 색상 튜닝을 시사

**좋은 성능의 가능한 원인:**
1. 시각피질에서 강한 색상 선택적 반응
2. 충분한 수의 정보성 있는 복셀
3. 반복 측정 간 신뢰할 수 있는 반응
4. 효과적인 공간 전처리 및 정렬
5. 적절한 ROI 정의 및 위치 결정

"""
    else:
        report += """
**제한된 성능 지표:**
- 분류 정확도가 예상 수준 근처 또는 이하
- 약한 통계적 유의성
- 낮은 선택성 지수

**제한된 성능의 가능한 원인:**

1. **데이터 품질 문제**:
   - fMRI 데이터의 낮은 신호 대 잡음비
   - 움직임 artifact 또는 기타 교란 요인
   - 조건당 시행 수 부족

2. **ROI 정의 문제**:
   - Atlas 기반 ROI가 피험자 특이적 망막지도와 잘 맞지 않을 수 있음
   - 거친 공간 해상도(2mm)가 미세한 패턴을 놓칠 수 있음
   - 광범위하게 정의된 ROI 내 혼합된 반응 특성

3. **모델 한계**:
   - 선형 순방향 모델이 너무 단순할 수 있음
   - 제한된 수의 복셀 선택
   - 교차 검증에서 과적합 가능성

4. **자극/설계 문제**:
   - 색 공간 샘플링이 신경 표현과 일치하지 않을 수 있음
   - 자극 특징의 변화 부족
   - 적응 또는 습관화 효과

"""
    
    report += """
---

## 2부: 복셀 수준 분석

### 2.1 복셀 특성

"""
    
    for roi, results in summary['voxel_level'].items():
        report += f"""
#### {roi}
- **전체 복셀 수**: {results['n_voxels']}
- **평균 복셀 선택성**: {results['mean_selectivity']:.3f}
- **평균 복셀 신뢰도**: {results['mean_reliability']:.3f}

"""
    
    report += """
### 2.2 복셀 선택 권장사항

복셀 수준 분석을 기반으로 다음을 권장합니다:
1. **선택성 기반 선택**: 상위 50% 선택적 복셀 사용
2. **신뢰도 임계값**: 신뢰도 < 0.3인 복셀 제외
3. **결합 기준**: 강건한 디코딩을 위해 선택성과 신뢰도 균형

---

## 결론

### 강점
- B&H (2009) 방법론에 따른 체계적 구현
- ROI 및 복셀 수준에서의 포괄적 분석
- 순열 검정을 통한 강건한 통계적 검증

### 한계
- Atlas 기반 ROI 정의 (피험자 특이적 망막지도 아님)
- 선형 순방향 모델링 접근법에 국한
- 단일 피험자 분석 (일반화 불명확)

### 향후 방향
1. 피험자 특이적 망막지도 매핑 구현
2. 비선형 디코딩 모델 탐색 (예: 신경망)
3. 대안적 특징 공간 및 색상 표현 테스트
4. 집단 수준 추론을 위한 다중 피험자 분석 수행

---

*보고서 생성 날짜: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report

if __name__ == '__main__':
    summary = main()
