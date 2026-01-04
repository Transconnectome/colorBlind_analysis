# Group-Level Analysis Options: Usage Guide
# 그룹 수준 분석 옵션: 사용 가이드

**Date:** 2025-12-17
**Author:** Claude Code

---

## 개요 (Overview)

Phase 1 분석에서 HC 피험자 간 낮은 일관성을 발견했습니다. 이를 해결하기 위한 세 가지 분석 옵션을 구현했습니다.

세 가지 스크립트가 모두 **상세한 한국어 주석**으로 작성되었습니다.

---

## 📋 스크립트 목록

| 옵션 | 스크립트 | 우선순위 | 목적 |
|------|---------|---------|------|
| **Option 1** | `option1_within_subject_reliability.py` | ⭐⭐⭐ 최우선 | 피험자 내 신뢰도 평가 (진단) |
| **Option 2** | `option2_srm_analysis.py` | ⭐⭐⭐ 최우선 | SRM으로 공유 구조 찾기 |
| **Option 3** | `option3_supersubject.py` | ⭐⭐ 기준선 | Brouwer & Heeger 방법 |

---

## Option 1: Within-Subject Reliability (피험자 내 신뢰도)

### 목적
개별 피험자의 RDM이 얼마나 안정적인지 평가. **다른 모든 분석 전에 필수로 실행해야 함.**

### 왜 중요한가?
- **r > 0.7**: 개별 RDM 안정적 → 피험자 간 차이는 실제 신호 → Option 2/3 진행 가능
- **r < 0.5**: 개별 RDM 불안정 → 노이즈 문제 → 데이터 품질 개선 필요

### 사용법

```bash
# 기본 사용 (baseline81, 모든 ROI)
python analysis/group_level/option1_within_subject_reliability.py \
    --timestamp baseline81_deob_determin \
    --subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4

# 특정 ROI만
python analysis/group_level/option1_within_subject_reliability.py \
    --timestamp baseline81_deob_determin \
    --subjects 01 02 03 05 06 07 \
    --rois hV4

# Odd-even split 방법 사용
python analysis/group_level/option1_within_subject_reliability.py \
    --timestamp baseline81_deob_determin \
    --subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --split-method odd-even
```

### 파라미터

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--timestamp` | 분석 timestamp | baseline81_deob_determin |
| `--dataset` | 데이터셋 이름 | deoblique_v2 |
| `--subjects` | 피험자 ID 리스트 | 01 02 03 05 06 07 |
| `--rois` | ROI 리스트 | V1 V2 V3 hV4 |
| `--split-method` | Split 방법 (first-second or odd-even) | first-second |
| `--output-dir` | 출력 디렉토리 | analysis/group_level/option1_results/{timestamp} |

### 출력

```
analysis/group_level/option1_results/baseline81_deob_determin/
├── reliability_results.csv              # 전체 결과 (피험자 × ROI)
├── summary_statistics.txt               # 요약 통계
├── interpretation_guide.txt             # 해석 가이드
├── reliability_heatmap.png              # 히트맵 (피험자 × ROI)
├── reliability_boxplot.png              # ROI별 분포
├── raw_vs_corrected.png                 # Raw vs. Spearman-Brown corrected
├── rdm_comparison_sub-01.png            # RDM 비교 예시
└── sub-{ID}/                            # 피험자별 RDM 데이터
    └── {ROI}/
        ├── rdm_half1.npy
        └── rdm_half2.npy
```

### 실행 시간
약 **2-3시간** (전체 데이터 로드 + RDM 계산)

---

## Option 2: Shared Response Model (SRM)

### 목적
피험자 간 공유된 신경 표상 구조를 찾아내고, 기능적 정렬 수행.

### 왜 사용하는가?
- **유일하게 색상 fMRI에서 검증된 방법** (Bannert & Bartels 2025)
- 해부학적 차이를 넘어 기능적 대응 찾기
- 게재에 가장 안전

### 사용법

```bash
# 필수 설치: BrainIAK
pip install brainiak

# HC만 분석 (공유 구조 찾기)
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --k-features 20

# CVD 포함 분석
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2 V3 hV4 \
    --k-features 20

# k_features 조정 (공유 차원 수)
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois hV4 \
    --k-features 30 \
    --n-iter 15
```

### 파라미터

| 파라미터 | 설명 | 기본값 | 권장 범위 |
|---------|------|--------|----------|
| `--timestamp` | 분석 timestamp | baseline81_deob_determin | - |
| `--dataset` | 데이터셋 이름 | deoblique_v2 | - |
| `--hc-subjects` | HC 피험자 ID | 01 02 03 05 06 07 | - |
| `--cvd-subjects` | CVD 피험자 ID (선택) | [] | - |
| `--rois` | ROI 리스트 | V1 V2 V3 hV4 | - |
| `--k-features` | 공유 잠재 차원 수 | 20 | 10-50 |
| `--n-iter` | SRM iteration 수 | 10 | 10-20 |
| `--output-dir` | 출력 디렉토리 | analysis/group_level/option2_results/{timestamp} | - |

### k_features 선택 가이드

| k_features | 효과 | 추천 시나리오 |
|------------|------|--------------|
| 10-15 | 매우 낮은 차원, 공유 구조 강하게 제약 | 작은 ROI, 강한 정규화 원할 때 |
| 20-30 | **권장 범위** (Bannert & Bartels) | 일반적인 분석 |
| 40-50 | 높은 차원, 더 세밀한 구조 포착 | 큰 ROI, 복잡한 표상 |
| > 50 | 과적합 위험 | 권장하지 않음 |

### 출력

```
analysis/group_level/option2_results/baseline81_deob_determin/
├── srm_analysis_summary.txt             # 전체 요약
└── {ROI}/
    ├── srm_results.npz                  # 공유 반응, 변환 행렬, RDM 유사도
    ├── rdm_similarity_shared_space.png  # 공유 공간에서 RDM 유사도 히트맵
    ├── shared_rdms_grid.png             # 각 피험자의 공유 공간 RDM
    └── cvd_reconstruction_error.png     # CVD vs. HC 재구성 오류 (CVD 있을 때)
```

### 실행 시간
약 **2-3일** (SRM 학습 + 변환 + 시각화)

### 해석 가이드

**공유 공간 RDM 유사도**:
- **> 0.5**: SRM이 공유 구조를 성공적으로 찾음 ✅
- **0.3-0.5**: 부분적인 공유 구조 존재 ⚠️
- **< 0.3**: 공유 구조 약함, k_features 조정 또는 다른 방법 고려 ❌

**CVD 재구성 오류 (z-score)**:
- **z > 2**: CVD가 HC 공유 구조에서 유의미하게 벗어남 → 색각 결핍 효과
- **|z| < 2**: CVD가 HC 분포 내 → 공유 구조에서 큰 차이 없음

---

## Option 3: Supersubject Method

### 목적
Brouwer & Heeger (2009) 방법으로 모든 HC 데이터를 하나로 합쳐서 그룹 수준 모델 구성.

### 왜 사용하는가?
- **고전적 기준선**: 원본 논문 방법과 직접 비교
- **간단한 구현**: SRM보다 훨씬 간단
- **그룹 수준 파라미터**: 채널 bandwidth, gain 등 도출 가능

### 사용법

```bash
# HC만 분석
python analysis/group_level/option3_supersubject.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4

# CVD 포함 분석
python analysis/group_level/option3_supersubject.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2 V3 hV4
```

### 파라미터

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--timestamp` | 분석 timestamp | baseline81_deob_determin |
| `--dataset` | 데이터셋 이름 | deoblique_v2 |
| `--hc-subjects` | HC 피험자 ID | 01 02 03 05 06 07 |
| `--cvd-subjects` | CVD 피험자 ID (선택) | [] |
| `--rois` | ROI 리스트 | V1 V2 V3 hV4 |
| `--output-dir` | 출력 디렉토리 | analysis/group_level/option3_results/{timestamp} |

### 출력

```
analysis/group_level/option3_results/baseline81_deob_determin/
├── supersubject_summary.txt             # 전체 요약
└── {ROI}/
    ├── supersubject_results.npz         # Supersubject RDM, HC 유사도
    ├── supersubject_rdm.png             # Supersubject RDM
    ├── hc_supersubject_similarities.png # HC-Supersubject 유사도
    ├── rdm_comparison_grid.png          # RDM 비교 (Supersubject + 개별 HC)
    └── cvd_comparison.png               # CVD vs. HC 비교 (CVD 있을 때)
```

### 실행 시간
약 **1일** (데이터 concatenation + RDM 계산 + 시각화)

### 해석 가이드

**HC-Supersubject 유사도**:
- **> 0.5**: 개별 피험자가 그룹 평균과 유사 → Supersubject 방법 합리적 ✅
- **0.3-0.5**: 부분적 일관성 → 개인차 존재하지만 그룹 경향 있음 ⚠️
- **< 0.3**: 개별 피험자가 그룹 평균과 다름 → 개인차 크고, pooling이 신호 희석 ❌

**CVD z-score**:
- **z < -2**: CVD가 HC supersubject와 유의미하게 다름
- **|z| < 2**: CVD가 HC 분포 내

---

## 🎯 권장 실행 순서

### Step 1: Within-Subject Reliability (필수 진단) ⭐⭐⭐

```bash
python analysis/group_level/option1_within_subject_reliability.py \
    --timestamp baseline81_deob_determin \
    --subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4
```

**결과 확인**:
- `reliability_results.csv`에서 각 피험자, 각 ROI의 reliability 확인
- `interpretation_guide.txt`에서 해석 가이드 확인

**의사 결정**:
- **평균 r > 0.7**: ✅ Option 2 (SRM) 또는 Option 3 (Supersubject) 진행
- **평균 r = 0.5-0.7**: ⚠️ 신중하게 진행, 더 많은 스무딩 고려
- **평균 r < 0.5**: ❌ 데이터 품질 개선 필요 (전처리 재검토)

---

### Step 2A: Shared Response Model (SRM) - 최우선 권장 ⭐⭐⭐

**조건**: Within-subject reliability r > 0.5

```bash
# BrainIAK 설치
pip install brainiak

# HC 분석
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --k-features 20 \
    --n-iter 10

# CVD 포함
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2 V3 hV4 \
    --k-features 20 \
    --n-iter 10
```

**결과 확인**:
- `srm_analysis_summary.txt`에서 공유 공간 RDM 유사도 확인
- `rdm_similarity_shared_space.png`에서 시각적으로 확인

**k_features 튜닝** (필요시):
- 초기 결과가 좋지 않다면 (mean similarity < 0.3), k_features를 조정:
  - k=10, 15, 20, 25, 30 등 여러 값 시도
  - 각 값에 대해 mean RDM similarity 확인
  - 가장 높은 similarity를 주는 k 선택

---

### Step 2B: Supersubject Method - 고전적 기준선 ⭐⭐

**조건**: 비교 목적 또는 SRM이 너무 복잡할 때

```bash
# HC 분석
python analysis/group_level/option3_supersubject.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4

# CVD 포함
python analysis/group_level/option3_supersubject.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2 V3 hV4
```

**결과 확인**:
- `supersubject_summary.txt`에서 HC-Supersubject 유사도 확인
- `hc_supersubject_similarities.png`에서 시각적으로 확인

---

## 📊 결과 비교 및 논문 작성

### 논문 구성 권장사항

**주요 분석 #1: SRM** (Highest priority)
- "Following Bannert & Bartels (2025), we used Shared Response Model (SRM)..."
- 공유 공간에서 RDM 유사도 보고
- CVD와 HC 비교 (재구성 오류, z-score)

**주요 분석 #2: Supersubject** (Classical baseline)
- "Following Brouwer & Heeger (2009), we created a group 'supersubject'..."
- HC-Supersubject 유사도 보고
- SRM 결과와 비교

**보충 분석: Within-Subject Reliability**
- "To ensure data quality, we first assessed within-subject reliability..."
- Split-half reliability 보고
- 개별 RDM이 안정적임을 확인

**논문 Discussion**:
- SRM vs. Supersubject 비교
- 왜 기능적 정렬(SRM)이 해부학적 정렬(Supersubject)보다 나은지
- 개인차의 의미 (adaptive coding, neural variability)
- CVD에서 관찰된 차이의 해석

---

## ⚠️ 주의사항

### 1. 데이터 경로
모든 스크립트는 `derivatives/BH2009_{dataset}/{timestamp}` 경로를 사용합니다.
- baseline81: `derivatives/BH2009_deoblique_v2/baseline81_deob_determin/`
- baseline32: `derivatives/BH2009_deoblique_v2/baseline32_deob_determin/`

### 2. 복셀 수 불일치
피험자마다 선택된 복셀 수가 다를 수 있습니다.
- **Option 1**: 각 피험자 개별 복셀 사용 (문제없음)
- **Option 2 (SRM)**: 복셀 수 달라도 OK (각 피험자별 변환 행렬)
- **Option 3 (Supersubject)**: 최소 복셀 수에 맞춰 자름

### 3. 메모리 사용량
- **Option 1**: 중간 (피험자별 순차 처리)
- **Option 2**: 높음 (SRM 학습, 모든 피험자 동시 로드)
- **Option 3**: 중간 (Supersubject 생성 시 concatenation)

큰 ROI (V1)나 많은 피험자의 경우 메모리 부족 가능성 있음.

### 4. BrainIAK 설치
Option 2 (SRM)는 BrainIAK 필요:
```bash
pip install brainiak
```

설치 실패 시:
```bash
# Conda 환경에서
conda install -c brainiak -c defaults -c conda-forge brainiak
```

---

## 🔧 문제 해결 (Troubleshooting)

### 1. "No results for sub-XX ROI" 오류
**원인**: 해당 피험자/ROI 조합의 데이터가 없음
**해결**: `--subjects` 또는 `--rois`에서 해당 항목 제외

### 2. "BrainIAK not found" 오류
**원인**: BrainIAK 미설치
**해결**: `pip install brainiak` 또는 conda 설치

### 3. Memory Error
**원인**: 메모리 부족
**해결**:
- ROI를 하나씩 분석
- 작은 ROI (hV4)부터 시작
- k_features 줄이기 (Option 2)

### 4. 매우 낮은 reliability (< 0.3)
**원인**: 데이터 품질 문제 또는 전처리 부적절
**해결**:
- 더 많은 스무딩 시도 (8mm)
- Confound regression 재검토
- SNR 확인

### 5. SRM에서 낮은 RDM similarity (< 0.3)
**원인**: k_features 부적절 또는 공유 구조 약함
**해결**:
- k_features 조정 (10, 15, 20, 25, 30 시도)
- n_iter 증가 (15-20)
- 특정 ROI만 시도 (hV4)

---

## 📚 참고 문헌

**Within-Subject Reliability**:
- Nunnally, J. C., & Bernstein, I. H. (1994). Psychometric theory.

**Shared Response Model**:
- Chen et al. (2015). A Reduced-Dimension fMRI Shared Response Model. NIPS.
- Haxby et al. (2011). A common, high-dimensional model of the representational space in human ventral temporal cortex. Neuron.
- **Bannert & Bartels (2025)**. Decoding color across observers using SRM. Journal of Neuroscience.

**Supersubject**:
- **Brouwer & Heeger (2009)**. Decoding and reconstructing color from responses in human visual cortex. Journal of Neuroscience.
- **Brouwer & Heeger (2013)**. Categorical clustering of the neural representation of color. Journal of Neuroscience.

**RSA & Individual Differences**:
- Kriegeskorte et al. (2008). Representational similarity analysis. Frontiers in Systems Neuroscience.
- Op de Beeck et al. (2019). Factors determining where category-selective areas emerge in visual cortex. Trends in Cognitive Sciences.

---

## 💡 추가 팁

### 병렬 실행
여러 ROI를 동시에 분석하려면 각 ROI에 대해 별도 터미널에서 실행:
```bash
# Terminal 1
python analysis/group_level/option2_srm_analysis.py --rois V1 ... &

# Terminal 2
python analysis/group_level/option2_srm_analysis.py --rois V2 ... &

# Terminal 3
python analysis/group_level/option2_srm_analysis.py --rois V3 ... &

# Terminal 4
python analysis/group_level/option2_srm_analysis.py --rois hV4 ... &
```

### 빠른 테스트
전체 분석 전에 하나의 ROI로 빠른 테스트:
```bash
# hV4만 (가장 작은 ROI)
python analysis/group_level/option1_within_subject_reliability.py \
    --rois hV4 \
    --timestamp baseline81_deob_determin
```

### 로그 저장
출력을 파일로 저장:
```bash
python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --hc-subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --k-features 20 \
    2>&1 | tee srm_analysis_log.txt
```

---

## 📞 문의

이 스크립트들에 대한 질문이나 문제가 있으면:
1. 먼저 이 가이드의 "문제 해결" 섹션 확인
2. 스크립트 내 상세한 주석 확인 (모두 한국어로 작성됨)
3. 출력 디렉토리의 `interpretation_guide.txt` 또는 `*_summary.txt` 확인

---

**Good luck with your analysis! 분석 성공을 기원합니다!** 🎉
