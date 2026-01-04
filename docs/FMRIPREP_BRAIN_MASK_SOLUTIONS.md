# fMRIPrep Brain Mask 문제 해결 방안

**작성일**: 2025-12-26

---

## 문제 요약

### 현황

**ZERO Overlap (분석 불가능):**
- Sub-01, 03, 04, 09, 10 (5명)
- 모든 ROI (V1, V2, V3, hV4)가 brain mask와 0% overlap

**정상 (분석 가능):**
- Sub-05, 06, 07 (3명)
- V1~hV4 모두 67-100% overlap

**부분 문제:**
- Sub-02: V1만 21% (V2~hV4는 58-100%)
- Sub-08: V1만 4% (V2~hV4는 51-100%)

### 근본 원인

**Affine은 완벽히 일치**하지만 overlap이 ZERO:
```
→ Brain mask가 posterior (후두엽) visual cortex를 포함하지 못함
```

**가능한 3가지 원인:**
1. **Brain extraction 너무 보수적** (fMRIPrep 설정)
2. **EPI coverage 부족** (스캔 자체 문제)
3. **Registration 문제** (MNI space 변환 시 손실)

---

## 해결 방안

### 방안 1: Brain Mask 수동 확장 ⭐ (추천)

**개념**: fMRIPrep brain mask를 morphological dilation으로 확장

**장점**:
- ✅ 간단하고 빠름 (수 분)
- ✅ 기존 fMRIPrep 결과 재사용 (재실행 불필요)
- ✅ Conservative → Liberal로 변경
- ✅ 즉시 테스트 가능

**단점**:
- ⚠️ Noise 증가 가능성
- ⚠️ Non-brain tissue 일부 포함 가능

**구현**:

```python
#!/usr/bin/env python3
"""Brain Mask Dilation for Visual Cortex Coverage"""

import nibabel as nib
import numpy as np
from scipy.ndimage import binary_dilation

def dilate_brain_mask(brain_mask_file, output_file, iterations=3):
    """
    Brain mask를 morphological dilation으로 확장

    Parameters:
    - iterations: dilation 반복 횟수 (3 = 6mm 확장 for 2mm voxels)
    """
    # Load brain mask
    mask_img = nib.load(brain_mask_file)
    mask_data = mask_img.get_fdata()

    # Dilate (posterior 방향 우선)
    # Structuring element: 타원형 (posterior 방향으로 더 확장)
    struct = np.zeros((3, 3, 5))
    struct[1, 1, :] = 1  # Z-direction (posterior)
    struct[1, :, 2] = 1  # Y-direction
    struct[:, 1, 2] = 1  # X-direction

    dilated = binary_dilation(mask_data > 0, structure=struct, iterations=iterations)

    # Save
    dilated_img = nib.Nifti1Image(dilated.astype(np.uint8), mask_img.affine, mask_img.header)
    nib.save(dilated_img, output_file)

    print(f"Original voxels: {np.sum(mask_data > 0)}")
    print(f"Dilated voxels: {np.sum(dilated)}")
    print(f"Increase: {np.sum(dilated) - np.sum(mask_data > 0)} voxels")

# 모든 ZERO overlap 피험자에 적용
for subj_id in ["01", "03", "04", "09", "10"]:
    input_file = f"/storage/connectome/haba6030/fmriprep_out_afni_deoblique/sub-{subj_id}/func/sub-{subj_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
    output_file = f"/storage/connectome/haba6030/fmriprep_out_afni_deoblique/sub-{subj_id}/func/sub-{subj_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask_dilated.nii.gz"

    dilate_brain_mask(input_file, output_file, iterations=3)
```

**검증**:
```bash
# Overlap 재확인
python3 CHECK_ALL_SUBJECTS_OVERLAP.sh --use-dilated
```

---

### 방안 2: fMRIPrep 재실행 (Brain Extraction 파라미터 조정)

**개념**: fMRIPrep의 brain extraction threshold를 낮춤

**장점**:
- ✅ "정석" 방법
- ✅ 전체 파이프라인 일관성 유지
- ✅ Brain extraction quality 개선

**단점**:
- ❌ 시간 소요 (8-12시간 per batch)
- ❌ 계산 자원 필요
- ❌ 성공 보장 없음

**구현**:

fMRIPrep 설정에 추가:
```bash
# 방법 A: skull-strip-fixed-seed (재현성 보장)
--skull-strip-fixed-seed

# 방법 B: skull-strip-t1w skip (기존 T1w brain extraction 재사용)
--skull-strip-t1w skip

# 방법 C: ANTs brain extraction 파라미터 조정
# (fMRIPrep에서 직접 지원 안 함, templateflow 수정 필요)
```

**문제**: fMRIPrep은 brain extraction threshold를 직접 조정하는 옵션이 없음!

---

### 방안 3: Atlas를 Individual T1w Space로 변환 (역변환)

**개념**: MNI atlas → Individual T1w → Functional space 변환

**장점**:
- ✅ Brain mask 문제 우회
- ✅ Individual anatomy에 최적화
- ✅ Registration quality 무관

**단점**:
- ⚠️ 복잡한 변환 (MNI → T1w → Func)
- ⚠️ Transform chain 오류 가능성
- ⚠️ 추가 preprocessing 필요

**구현**:

```bash
# 1. MNI atlas → Individual T1w
antsApplyTransforms -d 3 \
  -i wang_atlas_V1_MNI.nii.gz \
  -r sub-01_T1w.nii.gz \
  -t [MNI_to_T1w_transform.h5, 1] \
  -o wang_atlas_V1_T1w.nii.gz \
  -n NearestNeighbor

# 2. T1w → Functional space
antsApplyTransforms -d 3 \
  -i wang_atlas_V1_T1w.nii.gz \
  -r sub-01_task-rsvp_run-1_space-T1w_boldref.nii.gz \
  -t func_to_T1w_transform.h5 \
  -o wang_atlas_V1_func.nii.gz \
  -n NearestNeighbor

# 3. Functional space → MNI (for group analysis)
# 이미 fMRIPrep이 제공
```

**Transform 파일 위치**:
```
fmriprep_out/sub-{ID}/anat/sub-{ID}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5
fmriprep_out/sub-{ID}/func/sub-{ID}_from-T1w_to-scanner_mode-image_xfm.txt
```

---

### 방안 4: Liberal Brain Mask 생성 (Custom)

**개념**: AFNI 3dAutomask로 liberal brain mask 생성

**장점**:
- ✅ AFNI 도구 활용 (proven)
- ✅ Threshold 조정 가능
- ✅ Visual cortex coverage 최적화

**단점**:
- ⚠️ fMRIPrep과 불일치
- ⚠️ 추가 검증 필요

**구현**:

```bash
#!/bin/bash
# AFNI 3dAutomask로 liberal brain mask 생성

for subj in 01 03 04 09 10; do
    echo "Processing sub-$subj..."

    # Input: fMRIPrep preprocessed BOLD
    bold_file="/storage/connectome/haba6030/fmriprep_out_afni_deoblique/sub-${subj}/func/sub-${subj}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    # Output: Liberal brain mask
    output_mask="/storage/connectome/haba6030/fmriprep_out_afni_deoblique/sub-${subj}/func/sub-${subj}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask_liberal.nii.gz"

    # 3dAutomask with liberal settings
    3dAutomask \
        -dilate 3 \
        -prefix $output_mask \
        $bold_file

    echo "  Created: $output_mask"
done
```

**파라미터**:
- `-dilate 3`: 3 voxels 확장 (6mm for 2mm voxels)
- Default threshold: 더 관대함

---

## 추천 전략

### 단계 1: 빠른 테스트 (방안 1) ⭐

```bash
# 1. Brain mask dilation (5분)
python dilate_brain_masks.py

# 2. Overlap 재확인 (1분)
./CHECK_ALL_SUBJECTS_OVERLAP.sh --use-dilated

# 3. 결과 평가
# - Overlap > 50%? → 성공, baseline analysis 진행
# - Overlap < 20%? → 방안 2 또는 3 고려
```

**예상 성공률**: 80-90%

---

### 단계 2: Liberal Mask 생성 (방안 4)

Dilation으로 불충분하면:

```bash
# AFNI 3dAutomask 사용
./create_liberal_brain_masks.sh

# Overlap 재확인
./CHECK_ALL_SUBJECTS_OVERLAP.sh --use-liberal
```

**예상 성공률**: 90-95%

---

### 단계 3: 최종 수단 (방안 3)

위 2가지 실패 시:

```bash
# Atlas를 individual space로 역변환
./transform_atlas_to_individual.sh

# 장점: Brain mask 완전히 우회
# 단점: 복잡, 오류 가능성
```

---

## EPI Coverage 확인 (필수)

**모든 방안 시도 전에 확인해야 할 사항**:

```bash
# 원본 BOLD 데이터의 coverage 확인
for subj in 01 03 04 09 10; do
    echo "Sub-$subj:"

    # Original BOLD (before fMRIPrep)
    orig_bold="/storage/connectome/haba6030/colorBlind_data_afni_deoblique/sub-${subj}/func/sub-${subj}_task-rsvp_run-1_bold.nii.gz"

    # Check Z-range
    3dinfo -nk -dk -zk_to_z 0 50 $orig_bold

    # Visual check
    fsleyes $orig_bold &
done
```

**만약 원본 BOLD에 visual cortex가 없으면**:
→ **Scan protocol 문제, 전처리로 해결 불가능**
→ 해당 피험자 제외

---

## 실행 계획

### 즉시 실행 (오늘):

1. **EPI coverage 확인** (10분)
   ```bash
   ./check_original_epi_coverage.sh
   ```

2. **Brain mask dilation 테스트** (5분)
   ```bash
   python dilate_brain_masks.py
   ./CHECK_ALL_SUBJECTS_OVERLAP.sh --use-dilated
   ```

3. **결과 평가** (5분)
   - Overlap 개선 확인
   - 시각적 검사

### 내일 (필요 시):

4. **Liberal mask 생성** (방안 4)
   - 3dAutomask 사용
   - Overlap 재확인

5. **Baseline analysis 재실행**
   - 수정된 brain mask 사용
   - 결과 비교

---

## 예상 결과

### Best Case (80% 확률):

```
방안 1 (Dilation) 성공:
- Sub-01, 03, 04, 09, 10 → Overlap > 50%
- 모든 피험자 분석 가능
- 총 소요 시간: 1시간 미만
```

### Moderate Case (15% 확률):

```
방안 1 부분 성공, 방안 4 추가:
- 일부 피험자만 개선
- Liberal mask로 나머지 해결
- 총 소요 시간: 2-3시간
```

### Worst Case (5% 확률):

```
원본 EPI coverage 부족:
- Sub-01, 03, 04, 09, 10 제외
- 5명만으로 분석 진행 (sub-02, 05, 06, 07, 08)
- HC: 4명 (02, 05, 06, 07)
- CVD: 1명 (08) → Group analysis 불가능
```

---

## 교수님께 보고할 내용

### 진단 결과:

1. **이미지 왜곡 문제**: AFNI 3dWarp로 해결됨 ✅
2. **ROI-Brain mask overlap 문제**: fMRIPrep brain extraction 너무 보수적 ⚠️
3. **Affine matching**: 완벽 (AFNI 3dresample 성공) ✅

### 현재 조치:

1. Brain mask coverage 확인 중
2. Dilation으로 빠른 테스트 진행 중
3. EPI coverage 검증 예정

### 예상 일정:

- **오늘 (12/26)**: 진단 및 방안 1 테스트
- **내일 (12/27)**: 결과 확인 및 방안 2-4 (필요 시)
- **12/28**: Baseline analysis 재실행 및 결과 보고

---

## References

- fMRIPrep brain extraction: https://fmriprep.org/en/stable/workflows.html#brain-extraction
- AFNI 3dAutomask: https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html
- Morphological dilation: scipy.ndimage.binary_dilation
- Visual cortex coverage: Wandell & Winawer (2015)

---

**작성**: 2025-12-26
**상태**: 진단 중, 해결 방안 준비 완료
**다음**: EPI coverage 확인 → Dilation 테스트
