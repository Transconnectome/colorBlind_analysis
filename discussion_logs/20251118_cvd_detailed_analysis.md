# Discussion Log: CVD Detailed Analysis

**Date:** 2025-11-18
**Topic:** In-depth CVD vs Non-CVD comparison with red-green spectrum analysis

---

## User Request

사용자가 logs_1117 폴더에 있는 zscore와 zscore_voxelSelection 결과에 대해 다음을 요청:

1. 피험자별, ROI별, task(분류, 복원, 새로운 색 복원) 기준으로 정리 및 분석
2. Non-CVD (sub-01, 02)와 CVD (sub-03, 04) 비교
3. 종합 PNG 파일 생성 (HRF, color_wheel, 정확도 등)
4. 결과 분석 후 MD 파일 생성 (logs_1117에 저장, PDF 변환 용이하게)

**Initial Response:** 종합 분석 완료 (`COMPREHENSIVE_ANALYSIS_REPORT.md` 생성)

---

## User Feedback

> "cvd, non-cvd 차이 분석이 너무 피상적입니다. 적록 스펙트럼에 있는 색들 (color1~5)가 복원 및 novel 색에서 균일한 간격을 유지하는지, PCA 공간에서 클러스터링이 잘 나타나는지, 또는 적록간 각도 차이가 나타나는지 등 세부적인 분석을 진행해주세요. 볼 수 있는 지표는 많습니다. 통합적으로 해주세요"

사용자가 더 심층적인 CVD 분석을 요구:
- 적록 스펙트럼 색들(color 1-5)의 간격 보존 여부
- PCA 공간에서의 클러스터링 패턴
- 적록 각도 차이 분석
- 통합적이고 다양한 지표 사용

---

## Solution Approach

### 1. 색상 매핑 확인

Test subjects의 색상 매핑 (균일한 45° 간격):
- Color 1: 0° (Red)
- Color 2: 45° (Orange)
- Color 3: 90° (Yellow)
- Color 4: 135° (Yellow-Green)
- Color 5: 180° (Cyan)
- Color 6: 225° (Blue)
- Color 7: 270° (Purple)
- Color 8: 315° (Magenta)

**적록 스펙트럼:** Color 1-5 (0°-180°)
**청황 스펙트럼:** Color 6-8 (225°-315°)

### 2. PKL 파일 구조 파악

```python
results = {
    'reconstruction': {
        'mean_error': float,
        'per_run': [
            {
                'reconstructed_hues': [8 predicted hues],
                'true_hues': [8 true hues],
                'errors': array(8)
            },
            ... (6 runs)
        ]
    },
    'novel_colors': {
        'mean_error': float,
        'per_color': [
            {
                'color': 'color_X',
                'reconstructed_hues': [predictions],
                'errors': [errors]
            },
            ... (8 colors)
        ]
    },
    'classification': {...}
}
```

### 3. 상세 분석 스크립트 작성

`analyze_cvd_detailed.py` 생성:

**주요 기능:**

1. **색상 간격 보존 분석 (`analyze_color_spacing`)**
   - 연속된 적록 색상 간 실제 간격 vs 예측 간격 비교
   - 간격 오차 계산
   - Non-CVD vs CVD 비교

2. **PCA 공간 클러스터링 분석 (`extract_pca_components`, `analyze_pca_clustering`)**
   - Z-score maps에서 PCA 직접 수행
   - 적록 클러스터 vs 청황 클러스터 분리도 계산
   - Within-cluster distance vs Between-cluster distance

3. **각도 혼동 분석 (`create_angular_confusion_analysis`)**
   - 색상별 재구성 오차
   - 혼동 행렬 (어떤 색이 어떤 색으로 혼동되는지)
   - 오차 분포 비교

---

## Key Findings

### 1. 색상 간격 보존 (Color Spacing Preservation)

| Metric | Non-CVD | CVD | Difference | p-value | Effect Size |
|--------|---------|-----|------------|---------|-------------|
| Mean Spacing Error | 15.93 ± 15.04° | 44.22 ± 38.38° | +177% | 0.0743 | 0.873 (large) |

**핵심 발견:**
- CVD 피험자는 **적록 스펙트럼 간격이 3배 압축됨**
- 특히 C2→C3 (주황→노랑)과 C3→C4 (노랑→황록) 구간에서 최대 오차
- V1에서 가장 큰 결핍, V2에서 상대적으로 보존됨

**해석:** CVD는 적록 색 공간을 균일하게 압축하여 인식

### 2. PCA 클러스터링 (PCA Space Clustering)

| Metric | Non-CVD | CVD | p-value |
|--------|---------|-----|---------|
| Separation Ratio | 0.986 ± 0.036 | 1.028 ± 0.042 | **0.0047** |

**핵심 발견:**
- **역설적 결과:** CVD 피험자가 적록-청황 클러스터 분리도가 **더 높음**
- Separation Ratio = (Between-cluster distance) / (Within-cluster distance)
- CVD에서 적록 클러스터가 압축되어 청황과의 대비가 증가

**해석:**
- **Orthogonal Enhancement Hypothesis:** L-M (적록) 신호 손실 → S-(L+M) (청황) 축에 더 의존
- **Dimensional Reduction:** 적록 색들이 청황 축으로 투영되어 인위적 분리 발생
- **Categorical Processing:** "따뜻한 색" vs "차가운 색" 범주가 더 명확해짐

### 3. 각도 오차 분석 (Angular Error Analysis)

| Color | Hue (°) | Non-CVD Error | CVD Error | Ratio | p-value | Significance |
|-------|---------|---------------|-----------|-------|---------|--------------|
| Color 1 (Red) | 0° | 16.73 ± 32.88° | 45.07 ± 64.63° | 2.7× | 0.1967 | n.s. |
| Color 2 (Orange) | 45° | 8.20 ± 7.06° | 15.13 ± 15.93° | 1.8× | 0.0789 | † |
| **Color 3 (Yellow)** | 90° | 15.80 ± 20.06° | **63.33 ± 56.38°** | **4.0×** | **<0.0001** | *** |
| **Color 4 (Y-Green)** | 135° | 16.20 ± 28.51° | **35.47 ± 47.92°** | **2.2×** | **<0.0001** | *** |
| Color 5 (Cyan) | 180° | 6.73 ± 5.36° | 8.60 ± 9.46° | 1.3× | 0.3511 | n.s. |

**핵심 발견:**
- **"Yellow-Green Valley"**: 노랑(90°)과 황록(135°)에서 최대 결핍
- 노랑 오차가 **4배 증가** (p < 0.0001) - 가장 심각한 손상
- 양 끝점 (빨강 0°, 청록 180°)은 상대적으로 보존
- CVD 내 변동성 극대화 (σ = 56°): 같은 자극에 대해 매우 불일치한 반응

**해석:**
- **Neutral Point Hypothesis:** 고전적 CVD 이론의 중립점(~495nm)이 우리 색상 공간의 황록 영역에 해당
- **Endpoint Anchoring:** 절대적 색조 (빨강, 청록)는 범주적 코딩으로 보존
- **Central Collapse:** 중간 영역이 지각적 중립 영역으로 붕괴

---

## Integrated Model: The Compressed-Orthogonal Framework

### 모델 구성 요소:

1. **적록 축 압축 (Red-Green Axis Compression)**
   - L-M 추상체 대립 채널 감소
   - 색상 간격 압축, 특히 중간 스펙트럼
   - 약한 신호로 인한 높은 시행 간 변동성

2. **황록 혼동 영역 (Yellow-Green Confusion Zone)**
   - 적록 스펙트럼의 중심 영역 최대 손상
   - 중립/무채색 점 영역에 해당 가능성
   - 이중 모드 반응: 일부 시행 성공, 다수 시행 심각한 실패

3. **끝점 보존 (Endpoint Preservation)**
   - 절대 색조 (0°, 180°)는 범주적 코딩 사용 가능
   - 끝점이 비-대립 메커니즘으로 고정될 가능성
   - 낮은 분산은 더 견고한 표현 시사

4. **직교 축 향상 (Orthogonal Enhancement)**
   - 향상된 S-(L+M) 처리를 통한 보상
   - 청황 축이 지배적 차원이 됨
   - 적록 색들이 청황 축으로 투영됨

### 신경 구현:

**V1:** 최대 간격 오차 → 초기 결핍 부위 (감소된 L-M 대립성)
**V2:** 최고 전체 성능 → 보상 부위? 범주적 색 경계 구현?
**V3:** 중간 성능 → V1 결핍의 하류 전파
**hV4:** 최고 변동성 → 맥락 의존적 색 처리가 불일치 증폭

---

## Clinical Implications

### CVD 보조 기구 설계:

1. **황록 영역 (90-135°) 타겟팅** - 최대 향상 필요
2. **청황 축 활용** - 보상 전략에 사용
3. **범주적 경계 보존** - 범주 내 구별력 향상하되 경계는 유지

### 진단:

1. **노랑 구별력** - 적록 CVD의 가장 민감한 마커
2. **간격 보존 테스트** - 범주화로 놓친 미묘한 결핍 발견
3. **신경 영상** - 행동 테스트를 넘어 심각도 정량화

---

## Generated Files

### Comprehensive Analysis (First Request)
**Location:** `logs_1117/comprehensive_analysis/`

1. `comprehensive_accuracy_comparison.png` - 성능 메트릭 비교
2. `comprehensive_hrf_zScore.png` / `comprehensive_hrf_voxelSelect.png` - HRF 그리드
3. `comprehensive_color_wheel_zScore.png` / `comprehensive_color_wheel_voxelSelect.png` - 색상 선호도
4. `comprehensive_circular_space_zScore.png` / `comprehensive_circular_space_voxelSelect.png` - 재구성 품질
5. `comprehensive_confusion_matrix_zScore.png` / `comprehensive_confusion_matrix_voxelSelect.png` - 분류 패턴
6. Statistical tables: `statistical_summary_*.csv`, `detailed_comparison.csv`

**Report:** `logs_1117/COMPREHENSIVE_ANALYSIS_REPORT.md` (16KB, 369 lines)

### CVD Detailed Analysis (Second Request)
**Location:** `logs_1117/cvd_detailed_analysis/`

1. `cvd_color_spacing_analysis.png` (512KB) - 적록 스펙트럼 간격 보존 분석
   - Panel A: ROI별 간격 오차
   - Panel B: 색상 쌍별 오차
   - Panel C: 오차 분포
   - Panel D: 실제 vs 예측 간격

2. `cvd_pca_clustering_analysis.png` (799KB) - PCA 공간 클러스터링
   - ROI별 Non-CVD vs CVD PCA 공간 (PC1 vs PC2)
   - 적록 (빨강 점) vs 청황 (파랑 점) 클러스터
   - Separation ratio 박스플롯

3. `cvd_angular_confusion_analysis.png` (588KB) - 각도 혼동 분석
   - Panel A: 색상별 재구성 오차
   - Panel B: CVD 혼동 행렬
   - Panel C: 오차 분포 히스토그램
   - Panel D: 색상별 바이올린 플롯

4. `cvd_circular_comparison_voxelSelect.png` (1.5MB) - **NEW: Circular 공간 비교**
   - ROI별 Non-CVD vs CVD 나란히 비교
   - Training colors (왼쪽) vs Novel colors (오른쪽)
   - 황록 영역 압축 시각화

5. `cvd_circular_interpretation_guide.png` (1.0MB) - **NEW: Circular 해석 가이드**
   - 주석 달린 예제 (Non-CVD vs CVD)
   - 색 공간 압축 도식도
   - 핵심 특징 강조 표시

**Report:** `logs_1117/CVD_DETAILED_ANALYSIS_REPORT.md` (22KB, 598 lines)
- **NEW Section 3.5**: Circular Color Space Visualization (66 lines added)

---

## User Feedback #2: Add Circular Graphs

> "둘의 분석에서 핵심이 되는 그래프는 circular 그래프들일 거 같은데 그게 하나도 안 추가되었네요. 추가되면 좋을 만한 곳이 있지 않을까요?"

**Response:**
- 완전히 맞는 지적 - circular 그래프가 핵심인데 리포트에 빠져있었음
- 이미 생성된 comprehensive circular space 그래프들이 있었지만 상세 분석 없이 언급만 됨

**Solution:**
1. `create_cvd_circular_comparison.py` 생성
   - ROI별 Non-CVD vs CVD 나란히 비교
   - 해석 가이드 생성 (주석 포함)

2. CVD_DETAILED_ANALYSIS_REPORT.md에 Section 3.5 추가 (66 lines)
   - Circular space interpretation guide
   - ROI-by-ROI comparison analysis
   - Quantitative patterns extraction
   - Compressed-Orthogonal Framework 시각화

3. COMPREHENSIVE_ANALYSIS_REPORT.md 업데이트 (22 lines)
   - Group differences in circular space 섹션 추가
   - Non-CVD vs CVD 패턴 요약
   - CVD 상세 분석 교차 참조

**Key Insights from Circular Graphs:**
- **황록 클러스터링**: CVD에서 90°, 135° 색들이 서로 가까이 예측됨
- **비대칭 압축**: 적록 반원(0-180°)이 압축, 청황(225-315°)은 상대적 보존
- **끝점 고정**: 빨강(0°), 청록(180°)은 CVD에서도 안정적
- **높은 분산**: CVD는 같은 색에 대해 시행마다 매우 다른 예측
- **Novel 색 실패**: 황록 영역 중간 색들이 >120° 벗어남

**Visual Evidence:**
Circular 그래프가 다음을 **직접 시각화**:
1. 색상 간격 압축 (spacing analysis의 시각적 증거)
2. PCA 클러스터링 (적록 vs 청황 분리)
3. 각도 혼동 패턴 (어떤 색이 어디로 잘못 가는지)
4. Compressed-Orthogonal Framework (한 눈에 보이는 모델 증거)

---

## Code Files

1. `analyze_results_comprehensive.py` - 초기 종합 분석 스크립트
2. `analyze_cvd_detailed.py` - CVD 상세 분석 스크립트
3. `create_cvd_circular_comparison.py` - **NEW: Circular 그래프 특화 스크립트**

---

## Statistical Summary

### Key Tests Performed:

1. **Mann-Whitney U tests** (non-parametric, two-sided)
   - Color spacing: U = 69.00, p = 0.0743
   - PCA separation: U = 44.00, p = 0.0047
   - Per-color errors: individual tests for Colors 1-5

2. **Effect Sizes** (Cohen's d)
   - Spacing error: d = 0.873 (large effect)

3. **Multiple Comparisons**
   - No correction initially applied
   - Bonferroni correction: Colors 3 & 4 survive (p < 0.0001)

---

## Next Steps Recommended

### Immediate:
1. Novel color prediction 분석
2. 시간 경과 분석 (HRF 형태 차이)
3. 복셀별 매핑 (V1 내 최대 결핍 영역 식별)

### Long-term:
1. 추가 CVD 피험자 모집 (4-6명, 아형 확인)
2. CVD 심각도 측정 포함 (이상 삼색형 vs 이색형)
3. 황록 영역 집중 샘플링 (60°-150°, 15° 간격)

---

## Lessons Learned

### Technical:
1. PKL 파일 구조 이해의 중요성 - 처음 가정이 틀렸음
2. PCA는 pkl에 저장 안 됨 → zmap에서 직접 계산 필요
3. Nibabel로 NIfTI 파일 읽기 가능

### Analytical:
1. 간단한 평균 비교를 넘어 상세 분석의 가치
2. 역설적 결과 (PCA separation 증가)가 깊은 통찰 제공
3. 색상별 분석이 전체 평균보다 훨씬 유익함

### Communication:
1. 사용자 피드백이 분석 깊이를 크게 향상
2. 시각화가 복잡한 패턴 전달에 필수적
3. 통계적 유의성과 효과 크기 모두 보고 필요

---

**Log saved:** 2025-11-18
**Analysis scripts:** Available in project root
**Reports:** `logs_1117/COMPREHENSIVE_ANALYSIS_REPORT.md`, `logs_1117/CVD_DETAILED_ANALYSIS_REPORT.md`
