# Native Space ROI Validation Pipeline

**작성일**: 2025-01-04
**목적**: MNI 정규화 품질과 무관하게 native functional space에서 ROI 피팅 및 분석 가능성 검증

---

## 개요

### 핵심 질문
**"MNI가 깨져 있어도, native functional에서는 분석이 성립하는가?"**

### 배경

일부 피험자(sub-01, 03, 04, 09, 10)에서 MNI space의 ROI와 brain mask가 0% overlap을 보였습니다. 하지만:

- **MNI 정규화는 필수 조건이 아닙니다**
- Hyperalignment, Procrustes, pattern-based 분석은 **native functional space**에서 수행 가능
- 개인 해부학적 구조에 맞춘 ROI가 더 정확할 수 있음

### 목표

1. ✅ Native BOLD 공간에서 ROI가 정상적으로 후두엽에 피팅되는지 확인
2. ✅ Decoding/beta pattern/hyperalignment 등 핵심 분석 가능성 검증
3. ✅ MNI 문제와 무관하게 연구 진행 가능 여부 판단

---

## 파이프라인 구조

### 전체 흐름

```
Wang Atlas (MNI)
    ↓
[1] MNI → T1w native (ANTs inverse warp)
    ↓
[2] T1w → BOLD native (fMRIPrep transform)
    ↓
[3] 시각적 QC (ROI overlay)
    ↓
[4] 기능적 검증 (decoding test)
    ↓
✅ 분석 진행 가능 여부 판단
```

### 주요 단계

#### Step 1: MNI ROI → T1w Native
- **Input**: Wang atlas ROI (MNI space)
- **Transform**: `*_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5`
- **Output**: ROI in T1w native space
- **Interpolation**: Linear (probabilistic values preserved)

#### Step 2: T1w ROI → BOLD Native
- **Input**: ROI in T1w native
- **Transform**: `*_from-boldref_to-T1w_mode-image_xfm.txt` (inverse)
- **Output**: ROI in native BOLD space
- **Alternative**: If using T1w-space BOLD, simple resampling

#### Step 3: 시각적 검증
- **Overlay**: ROI on native BOLD reference
- **Check points**:
  - ROI가 posterior occipital cortex에 위치하는가?
  - 소뇌/뇌간/비피질 영역으로 튀지 않는가?
  - 좌우 반구에 대칭적으로 분포하는가?

#### Step 4: 기능적 Sanity Check
- **Trial-wise response** 추출
- **tSNR** 계산
- **Color discriminability** (between/within variance ratio)
- **Simple decoding test** (Leave-one-out LDA)

---

## 사용법

### 단일 피험자 실행

```bash
# 로컬 또는 서버에서 실행
bash run_native_roi_pipeline.sh <subject_id> <roi_name> [run]

# 예시
bash run_native_roi_pipeline.sh 02 V1 1
```

### 전체 피험자 배치 실행 (SLURM)

```bash
# Array job 제출 (7 subjects × 4 ROIs = 28 jobs)
sbatch run_native_roi_pipeline.sbatch

# 특정 피험자만 실행
sbatch --array=0-3 run_native_roi_pipeline.sbatch  # sub-01, all ROIs
sbatch --array=4-7 run_native_roi_pipeline.sbatch  # sub-02, all ROIs
```

### Array Job 인덱스 매핑

```
Task ID | Subject | ROI
--------|---------|-----
0       | 01      | V1
1       | 01      | V2
2       | 01      | V3
3       | 01      | hV4
4       | 02      | V1
...     | ...     | ...
27      | 08      | hV4
```

---

## 출력 파일

### 디렉토리 구조

```
derivatives/native_space_roi/
└── sub-{ID}/
    ├── sub-{ID}_{ROI}_space-T1w.nii.gz              # T1w native ROI
    ├── sub-{ID}_{ROI}_space-bold_run-{RUN}.nii.gz   # BOLD native ROI (probabilistic)
    ├── sub-{ID}_{ROI}_space-bold_run-{RUN}_mask.nii.gz  # Binary mask (threshold > 20)
    ├── QC_sub-{ID}_{ROI}_run-{RUN}_overlay.png      # Basic overlay (FSL slicer)
    ├── QC_sub-{ID}_{ROI}_run-{RUN}_detailed.png     # Detailed multi-view overlay
    ├── QC_sub-{ID}_{ROI}_run-{RUN}_histogram.png    # Intensity distribution
    └── sanity_check_sub-{ID}_{ROI}_run-{RUN}.png    # Functional diagnostics
```

### 주요 출력물 설명

#### 1. ROI 파일

- **Probabilistic ROI** (`*_space-bold_run-*.nii.gz`):
  - Continuous values (0-100) from Wang atlas
  - 변환 과정에서 부드럽게 interpolated
  - 추가 threshold 가능

- **Binary mask** (`*_mask.nii.gz`):
  - Threshold > 20 applied
  - 분석에 직접 사용 가능

#### 2. QC 이미지

- **overlay.png**: 빠른 확인용 (FSL slicer)
- **detailed.png**: 상세 multi-view (nilearn)
- **histogram.png**: 강도 분포 및 통계

#### 3. 기능적 진단

- **tSNR**: Temporal signal-to-noise ratio
- **SNR ratio**: Between-color / Within-color variance
- **Decoding accuracy**: Leave-one-out classification

---

## 해석 가이드

### 변환 성공 기준

| 지표 | 성공 | 주의 | 실패 |
|------|------|------|------|
| Binary mask voxels | > 100 | 10-100 | 0 |
| ROI location | Posterior occipital | Parietal | Frontal/cerebellum |
| tSNR | > 40 | 20-40 | < 20 |
| Decoding accuracy | > 20% | 15-20% | < 15% (chance: 12.5%) |

### 결과 해석

#### ✅ 성공 (분석 진행 가능)

```
Binary mask: 150 voxels
ROI center: (-15.2, -85.3, -5.1) mm
tSNR: 45.3
Decoding: 28.5%
→ Native space 분석 진행
```

**의미**:
- ROI가 올바른 위치(posterior occipital cortex)에 피팅됨
- 충분한 신호 품질과 color discriminability
- Hyperalignment/Procrustes 분석 가능

#### ⚠ 부분 성공 (추가 검토 필요)

```
Binary mask: 45 voxels
ROI center: (-12.1, -78.4, -8.2) mm
tSNR: 28.7
Decoding: 18.2%
→ Manual inspection 권장
```

**의미**:
- ROI 크기가 작지만 위치는 정상
- 분석 가능하나 통계 검정력 낮을 수 있음
- Voxel threshold 조정 고려

#### ❌ 실패 (근본적 문제)

```
Binary mask: 0 voxels
→ 변환 실패 또는 registration 문제
```

**가능한 원인**:
1. EPI coverage 부족 (scan protocol 문제)
2. T1w-to-MNI registration catastrophic failure
3. Transform chain 오류

**해결 방안**:
- fMRIPrep HTML report 확인
- 원본 BOLD coverage 확인
- 다른 preprocessing 시도

---

## 필요 파일 및 의존성

### fMRIPrep 출력물

```bash
# 필수 파일
/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-{ID}/

  anat/
    sub-{ID}_desc-preproc_T1w.nii.gz
    sub-{ID}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5

  func/
    sub-{ID}_task-rsvp_run-{RUN}_desc-coreg_boldref.nii.gz
    sub-{ID}_task-rsvp_run-{RUN}_space-T1w_desc-preproc_bold.nii.gz
    sub-{ID}_task-rsvp_run-{RUN}_from-boldref_to-T1w_mode-image_xfm.txt
```

### Wang Atlas

```bash
/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4_2mm/subj_vol_all/
  perc_VTPM_vol_roi{1-7}_{lh,rh}.nii.gz
```

### 이벤트 파일

```bash
/storage/connectome/haba6030/colorBlind_data_deoblique/sub-{ID}/func/
  sub-{ID}_task-rsvp_run-{RUN}_events.tsv
```

### 소프트웨어 의존성

```bash
# 모듈
module load fsl/6.0.5
module load ants/2.3.5

# Conda 환경
conda activate nilearn

# Python 패키지
nilearn, nibabel, numpy, pandas, matplotlib, scipy, scikit-learn
```

---

## 트러블슈팅

### 문제 1: "Transform file not found"

**증상**:
```
✗ MISSING: sub-02_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5
```

**원인**: fMRIPrep 버전 또는 설정 차이

**해결**:
```bash
# 파일 존재 확인
ls /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-02/anat/*xfm*

# 대체 파일 사용
# *.mat (FLIRT) 또는 *.txt (ITK) 가능
```

### 문제 2: "Empty binary mask (0 voxels)"

**증상**:
```
Binary mask: 0 voxels (threshold > 20)
```

**원인**: Threshold가 너무 높거나 변환 실패

**해결**:
```bash
# 1. Probabilistic ROI 확인
fslstats sub-02_V1_space-bold_run-1.nii.gz -R

# 2. Threshold 조정
fslmaths sub-02_V1_space-bold_run-1.nii.gz -thr 10 -bin mask_thr10.nii.gz

# 3. Transform chain 재확인
bash check_transform_chain.sh 02 1
```

### 문제 3: ROI가 이상한 위치에 있음

**증상**:
```
ROI center: (45.2, 20.1, 35.3) mm  # Frontal lobe?
```

**원인**: Registration 실패

**해결**:
```bash
# 1. fMRIPrep HTML report 확인
# 2. T1w-to-MNI registration quality 확인
# 3. 필요시 다른 피험자 데이터와 비교
```

---

## 다음 단계

### 성공 시

1. **Individual-level analysis** in native space
   - GLM with native space BOLD
   - Decoding/reconstruction pipeline
   - 기존 `fir_reconstruction_BH2009_system_clean.py` 수정하여 native space 지원

2. **Hyperalignment/Procrustes**
   - Native space beta patterns 추출
   - Across-subject alignment (MNI 불필요!)
   - Common representational space 구축

3. **Group-level analysis**
   - Aligned native spaces에서 통계 검정
   - ROI-based searchlight
   - Connectivity analysis

### 실패 시

1. **Preprocessing 재검토**
   - 다른 fMRIPrep 설정 시도
   - Brain mask dilation
   - Liberal brain extraction

2. **Alternative ROI 정의**
   - Functional localizer 기반 ROI
   - Subject-specific ROI from retinotopy
   - Probabilistic atlas 대신 anatomical landmarks

3. **데이터 제외 고려**
   - EPI coverage 부족한 피험자
   - Individual-level analysis만 수행
   - Group analysis에서 제외

---

## 참고 문서

- `docs/FMRIPREP_BRAIN_MASK_SOLUTIONS.md`: Brain mask 문제 해결 방안
- `docs/PREPROCESSING_METHOD_UPDATE_2025-12-18.md`: fMRIPrep 설정 변경 내역
- `check_transform_chain.sh`: Transform chain 진단 스크립트
- `docs/GUIDE_to_classify_reconstruct.md`: 기존 분석 파이프라인

---

## 작성자 노트

이 파이프라인은 **MNI 정규화 문제 우회**를 위한 솔루션입니다.

**핵심 아이디어**:
- MNI space는 group comparison을 위한 **옵션**이지 **필수**가 아님
- Native space에서 분석 후 hyperalignment로 align 가능
- 개인 해부학적 구조 보존으로 더 정확한 결과 가능

**성공 조건**:
- ✅ ROI가 올바른 위치(occipital cortex)에 피팅
- ✅ 충분한 신호 품질(tSNR > 20)
- ✅ Color discriminability 존재(decoding > chance)

**성공 시 이점**:
- MNI 문제와 무관하게 연구 진행
- Sub-01, 03, 04, 09, 10 포함 가능성
- 더 정확한 individual-level 분석

---

**업데이트 내역**:
- 2025-01-04: 초기 작성 및 파이프라인 구현
