# CVD Analysis Quick Start Guide (Updated for New Directory Structure)

색약 구분 지표를 빠르게 추출하고 비교하는 방법입니다.

## ⚠️ 새로운 폴더 구조

**변경 전:**
```
derivatives/
  sub-01/
    fir_reconstruction_uni_hrf/
      zScore/20250116_143022/V2_universal_hrf/
```

**변경 후:**
```
derivatives/
  20250116_143022/          ← 날짜/시간이 최상위
    sub-01/
      fir_reconstruction_uni_hrf/
        zScore/
          V2_universal_hrf/
```

**장점:**
- ✓ 같은 날짜/시간에 실행한 모든 피험자/ROI를 한 폴더에서 볼 수 있음
- ✓ 버전 비교가 쉬움
- ✓ 실험 session별로 정리됨

---

## 1단계: 파일 업로드 (로컬 → 서버)

```bash
# 로컬에서 실행
scp visualize_Edits/fir_reconstruction_zScore.py \
    visualize_Edits/fir_reconstruction_zScore_voxelSelect.py \
    visualize_Edits/fir_reconstruction_universal_hrf.py \
    visualize_Edits/extract_colorblind_metrics.py \
    visualize_Edits/compare_subjects_cvd.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/visualize_Edits/
```

---

## 2단계: Reconstruction 실행 (새 폴더 구조로)

```bash
# 서버에 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 예시: 모든 피험자와 ROI 실행 (같은 timestamp에 저장됨)
for sub in P01 01 02 03 04; do
    for roi in V1 V2 V3 hV4; do
        python visualize_Edits/fir_reconstruction_universal_hrf.py \
            --subject $sub --roi $roi --use-pca --n-components 6
    done
done
```

**결과 폴더 구조:**
```
derivatives/
  20250116_143022/         ← 모든 결과가 이 timestamp 아래
    sub-P01/
      fir_reconstruction_uni_hrf/
        V1_universal_hrf/results.pkl
        V2_universal_hrf/results.pkl
        ...
    sub-01/
      fir_reconstruction_uni_hrf/
        V1_universal_hrf/results.pkl
        ...
```

---

## 3단계: 메트릭 추출

### Option A: 가장 최근 결과 자동 사용

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

# 모든 피험자 메트릭 추출 (최신 timestamp 자동 선택)
for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub \
        --output-dir cvd_metrics
done
```

### Option B: 특정 timestamp 지정 ⭐ 추천

```bash
# 서버에서 먼저 어떤 timestamp가 있는지 확인
ls derivatives/

# 예시 출력:
# 20250116_143022/
# 20250116_150315/
# 20250117_091043/

# 특정 timestamp의 결과만 분석
TIMESTAMP=20250116_143022

for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub \
        --timestamp $TIMESTAMP \
        --output-dir cvd_metrics_${TIMESTAMP}
done
```

**예상 출력:**
```
Extracting CVD Discrimination Metrics
================================================================================
Subject: P01
Timestamp: 20250116_143022          ← 지정된 timestamp 사용
Output directory: cvd_metrics_20250116_143022

[1/5] Extracting novel color reconstruction angles...
  Saved: cvd_metrics_20250116_143022/P01_novel_color_angles.csv
  Extracted 32 color×ROI combinations
...
```

---

## 4단계: 그룹 비교

```bash
# 서버에서
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 \
    --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics_20250116_143022 \
    --output-dir cvd_comparison_20250116_143022
```

**예상 출력:**
```
[1/4] Comparing red-green compression ratios...
  Saved: cvd_comparison_20250116_143022/red_green_compression_comparison.png

[2/4] Comparing novel color reconstruction biases...
  Saved: cvd_comparison_20250116_143022/novel_color_bias_comparison.png

[3/4] Comparing color space structure (MDS)...
  Saved: cvd_comparison_20250116_143022/color_space_structure_comparison.png

[4/4] Generating statistical comparison report...
  Saved: cvd_comparison_20250116_143022/statistical_comparison.txt
```

---

## 5단계: 결과 다운로드 (서버 → 로컬)

```bash
# 로컬에서 실행
TIMESTAMP=20250116_143022

# 메트릭과 비교 결과 모두 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_metrics_${TIMESTAMP} ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_comparison_${TIMESTAMP} ./
```

---

## 6단계: 결과 확인

### A. 통계 검정 결과 확인

```bash
# 로컬에서
cat cvd_comparison_20250116_143022/statistical_comparison.txt
```

**핵심 확인 사항:**
```
1. RED-GREEN COMPRESSION RATIO
----------------------------------------
V1:
  CVD:     mean = 0.65 ← 색약 양성 지표!
  Non-CVD: mean = 0.98
  t-test: p = 0.002 ***SIGNIFICANT*** ← p < 0.05면 유의미!

hV4:
  CVD:     mean = 0.58 ← V1보다 더 압축!
  Non-CVD: mean = 0.96
  t-test: p = 0.001 ***SIGNIFICANT***
```

### B. 시각화 확인

```bash
# 로컬에서 그림 열기
open cvd_comparison_20250116_143022/red_green_compression_comparison.png
open cvd_comparison_20250116_143022/novel_color_bias_comparison.png
open cvd_comparison_20250116_143022/color_space_structure_comparison.png
```

---

## 🎯 폴더 구조 활용법

### 여러 실험 버전 비교

```bash
# 서버에서 모든 timestamp 확인
ls -lt derivatives/ | head -10

# 각 timestamp별로 메트릭 추출
for TS in 20250116_143022 20250117_091043; do
    for sub in P01 01 02 03 04; do
        python visualize_Edits/extract_colorblind_metrics.py \
            --subject $sub \
            --timestamp $TS \
            --output-dir cvd_metrics_${TS}
    done

    # 그룹 비교
    python visualize_Edits/compare_subjects_cvd.py \
        --cvd-subjects P01 \
        --non-cvd-subjects 01 02 03 04 \
        --metrics-dir cvd_metrics_${TS} \
        --output-dir cvd_comparison_${TS}
done
```

### 버전 간 결과 비교

```bash
# 로컬에서
# Version 1 (zScore without voxel selection)
cat cvd_comparison_20250116_143022/statistical_comparison.txt

# Version 2 (zScore with voxel selection)
cat cvd_comparison_20250117_091043/statistical_comparison.txt

# 어떤 버전이 CVD 구분력이 더 높은가?
```

---

## 🔧 Troubleshooting

### 문제 1: "No results found for V1/V2/V3/hV4"

**원인:** 지정한 timestamp에 해당 ROI 결과가 없음

**해결:**
```bash
# 서버에서 해당 timestamp의 결과 확인
ls derivatives/20250116_143022/sub-01/fir_reconstruction_uni_hrf/

# 만약 V2만 있다면 V2만 분석
python visualize_Edits/extract_colorblind_metrics.py \
    --subject 01 \
    --timestamp 20250116_143022 \
    --rois V2 \
    --output-dir cvd_metrics_20250116_143022
```

### 문제 2: 모든 데이터가 "No data available"

**원인 1:** Timestamp 철자 오류
```bash
# 정확한 timestamp 확인
ls derivatives/

# 복사해서 사용
TIMESTAMP=20250116_143022  # 복사한 값
```

**원인 2:** 파일 경로 문제
```bash
# 서버에서 results.pkl 파일 확인
find derivatives/20250116_143022 -name "results.pkl"

# 예상 경로:
# derivatives/20250116_143022/sub-01/fir_reconstruction_uni_hrf/V2_universal_hrf/results.pkl
```

### 문제 3: 옛날 폴더 구조와 섞여있음

**상황:** 옛날 결과(sub-XX/fir_*/20250115_*/)와 새 결과(20250116_*/sub-XX/)가 섞임

**해결:**
```bash
# 서버에서 옛날 결과 백업
mkdir derivatives_old
mv derivatives/sub-* derivatives_old/
mv derivatives/pilot derivatives_old/

# 새 구조로 재실행
# (이제 derivatives/에는 timestamp 폴더만 있음)
```

---

## 📊 빠른 명령어 요약

```bash
# 0. 서버 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 1. Timestamp 확인
ls derivatives/

# 2. 특정 timestamp 선택
export TS=20250116_143022

# 3. 모든 피험자 메트릭 추출
for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub --timestamp $TS --output-dir cvd_metrics_${TS}
done

# 4. 그룹 비교
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics_${TS} --output-dir cvd_comparison_${TS}

# 5. 로컬로 다운로드 (로컬에서 실행)
export TS=20250116_143022
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_comparison_${TS} ./

# 6. 결과 확인 (로컬)
cat cvd_comparison_${TS}/statistical_comparison.txt
open cvd_comparison_${TS}/red_green_compression_comparison.png
```

---

## 📝 파일 업로드 체크리스트

업데이트된 파일들:
- ✅ `fir_reconstruction_zScore.py` (timestamp at top level)
- ✅ `fir_reconstruction_zScore_voxelSelect.py` (timestamp at top level)
- ✅ `fir_reconstruction_universal_hrf.py` (timestamp at top level)
- ✅ `extract_colorblind_metrics.py` (새 경로 지원 + --timestamp 옵션)
- ⬜ `compare_subjects_cvd.py` (수정 불필요, metrics_dir만 지정하면 됨)

---

**작성일:** 2025-01-16
**최종 수정:** 2025-01-16 (폴더 구조 변경 반영)
