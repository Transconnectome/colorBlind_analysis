# 🧠 ROI Construction Guide - Wang Atlas Based

**목적:** Wang (2015) atlas에서 V1, V2, V3, hV4 ROI 추출 및 검증
**타겟 공간:** MNI152NLin2009cAsym:res-2 (97×115×97 voxels)
**기준:** config.get_func_img_path(1) - 첫 번째 run의 BOLD 이미지

---

## 📋 Overview

### ROI 제작 프로세스
```
Wang Atlas (native space)
  ↓
1. Probability threshold (>50%)
  ↓
2. Left/Right hemisphere 합치기
  ↓
3. Ventral/Dorsal 합치기
  ↓
4. Resample to res-2 BOLD space (nearest neighbor)
  ↓
5. Brain mask intersection (optional)
  ↓
6. Subject MNI ROI intersection (optional)
  ↓
Final ROI mask (MNI152NLin2009cAsym:res-2)
```

---

## 🎯 Wang Atlas ROI Mapping

### ROI 구성 (from roi_build.py line 14-19)
```python
WANG_ROI_MAP = {
    'V1':  ['perc_VTPM_vol_roi1_', 'perc_VTPM_vol_roi2_'],  # V1v + V1d
    'V2':  ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_'],  # V2v + V2d
    'V3':  ['perc_VTPM_vol_roi5_', 'perc_VTPM_vol_roi6_'],  # V3v + V3d
    'hV4': ['perc_VTPM_vol_roi7_'],                          # hV4 only
}
```

### Hemisphere 합치기 (Left + Right)
```python
HEMISPHERES = ('lh', 'rh')
```

**예시: V1 ROI**
- `perc_VTPM_vol_roi1_lh.nii.gz` (V1 ventral left)
- `perc_VTPM_vol_roi1_rh.nii.gz` (V1 ventral right)
- `perc_VTPM_vol_roi2_lh.nii.gz` (V1 dorsal left)
- `perc_VTPM_vol_roi2_rh.nii.gz` (V1 dorsal right)
→ **4개 파일 모두 합쳐서 V1 mask 생성**

---

## 🔧 Implementation Details

### 1. Probability Threshold
**코드:** roi_build.py line 110
```python
part_mask = part_data > 50  # 50% 확률 이상만 포함
```

**설명:**
- Wang atlas는 probabilistic atlas (0-100% 확률 값)
- 50% 이상 voxel만 ROI에 포함
- **조정 가능:** 더 많은 voxel 필요 시 → threshold 낮추기 (예: 25%)

**임계값 효과:**
| Threshold | V2 예상 voxel 수 | 특성 |
|-----------|-----------------|------|
| 75% | ~150 | 매우 확실한 voxel만 (보수적) |
| **50%** | **~310** | **균형잡힌 기본값 (권장)** ✅ |
| 25% | ~500 | 더 많은 voxel 포함 (노이즈 증가 가능) |

---

### 2. Left/Right & Ventral/Dorsal 합치기
**코드:** roi_build.py lines 96-112
```python
roi_mask = None
for hemi in HEMISPHERES:  # 'lh', 'rh'
    for part in roi_parts:  # e.g., ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_']
        roi_file = f'ProbAtlas_v4/subj_vol_all/{part}{hemi}.nii.gz'
        part_img = nib.load(roi_file)
        part_data = part_img.get_fdata()
        part_mask = part_data > 50

        # 논리합 (OR) 연산으로 합치기
        roi_mask = part_mask if roi_mask is None else np.logical_or(roi_mask, part_mask)
```

**결과:**
- V2 = (V2v_lh OR V2v_rh) OR (V2d_lh OR V2d_rh)
- 모든 하위 영역이 하나의 통합된 V2 mask로 합쳐짐

---

### 3. Resample to res-2 BOLD Space (CRITICAL!)
**코드:** roi_build.py lines 119-124
```python
ref_img = nib.load(config.get_func_img_path(1))  # Run-1 BOLD (res-2)

roi_resampled = image.resample_img(
    roi_nii,
    target_affine=ref_img.affine,      # BOLD의 affine matrix
    target_shape=ref_img.shape[:3],    # BOLD의 shape (97, 115, 97)
    interpolation='nearest'            # 가장 가까운 voxel 사용 (mask이므로)
)
```

**왜 중요한가:**
- ✅ **Wang atlas → MNI152NLin2009cAsym:res-2로 강제 변환**
- ✅ **모든 이미지가 동일한 격자(grid)에 정렬됨**
- ✅ **BOLD 이미지와 완벽히 일치** (voxel-to-voxel 대응)
- ✅ **interpolation='nearest'** → 확률 값이 아닌 binary mask 유지

**결과 확인:**
```bash
# Reference BOLD 이미지
fslinfo sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
# dim1 = 97, dim2 = 115, dim3 = 97, dim4 = 246 (timepoints)

# 생성된 ROI mask
fslinfo derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz
# dim1 = 97, dim2 = 115, dim3 = 97, dim4 = 1 (static mask)
# ✅ 공간 차원 완벽히 일치!
```

---

### 4. Brain Mask Intersection (Optional)
**코드:** roi_build.py lines 127-143
```python
if os.path.exists(brain_mask_path):
    brain_img = nib.load(brain_mask_path)
    brain_resampled = image.resample_img(
        brain_img,
        target_affine=roi_resampled.affine,
        target_shape=roi_resampled.shape[:3],
        interpolation='nearest'
    )
    roi_bool = roi_resampled.get_fdata().astype(bool)
    brain_bool = brain_resampled.get_fdata().astype(bool)
    combined = np.logical_and(roi_bool, brain_bool)  # AND 연산
    roi_resampled = nib.Nifti1Image(combined.astype(np.int16), ...)
```

**목적:**
- Wang atlas가 뇌 밖 영역 포함할 수 있음 (resampling artifact)
- Brain mask와 교집합 → 실제 뇌 영역만 보존
- **EPI 이미지 범위 내로 제한**

**Brain mask 경로 (from roi_build.py line 29-37):**
```
output/pilot/sub-01/anat/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz
```

**영향:**
- ✅ Brain mask 있음: ROI ∩ Brain → 노이즈 제거
- ⚠️ Brain mask 없음: ROI만 사용 → 일부 out-of-brain voxel 포함 가능

---

### 5. Subject MNI ROI Intersection (Optional)
**코드:** roi_build.py lines 145-169
```python
subj_roi_img, subj_roi_path = _load_subject_mni_roi(config, roi_name, status)
if subj_roi_img is not None:
    subj_resampled = image.resample_img(...)
    atlas_bool = roi_resampled.get_fdata().astype(bool)
    subj_bool = subj_resampled.get_fdata().astype(bool)
    combined = np.logical_and(atlas_bool, subj_bool)  # AND 연산
    if combined.any():
        roi_resampled = nib.Nifti1Image(combined.astype(np.int16), ...)
```

**목적:**
- Subject-specific functional localization 있을 경우
- Atlas mask와 교집합 → 더 정확한 ROI
- **개인 맞춤 ROI (최적이지만 optional)**

**Subject ROI 탐색 경로 (line 41-71):**
```
output/pilot/sub-01/anat/
  → *space-mni*.nii.gz 중
  → roi_name (e.g., 'v2') 포함된 파일
```

**영향:**
- ✅ Subject ROI 있음: Atlas ∩ Subject → 가장 정확
- ✅ Subject ROI 없음: Atlas만 사용 → 여전히 작동 가능
- ⚠️ 교집합 비어있음: Atlas만 유지 (경고 메시지)

---

## 🚀 실행 방법

### Method 1: Python Script 직접 실행
```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

# conda 환경 활성화
conda activate nilearn

# ROI 생성
python roi_build.py
```

### Method 2: Python Import 사용
```python
from config import cfg
from roi_build import build_wang_rois

# Wang atlas ROI 생성
created_rois = build_wang_rois(cfg)

# 결과 확인
for roi_name, roi_path in created_rois.items():
    print(f"{roi_name}: {roi_path}")
```

### Method 3: SLURM Script 사용 (권장)
```bash
# sbatch 파일 생성
cat > build_rois.sbatch << 'EOF'
#!/bin/bash
#SBATCH --job-name=build_rois
#SBATCH --nodelist=node2
#SBATCH --time=00:10:00
#SBATCH --mem=8G
#SBATCH --output=logs/build_rois_%j.out
#SBATCH --error=logs/build_rois_%j.err

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind

python roi_build.py

echo "ROI construction complete!"
ls -lh derivatives/sub-P01/roi/
EOF

# 실행
sbatch build_rois.sbatch
```

---

## ✅ 검증 및 품질 관리

### 1. Voxel Count 확인
```bash
# 각 ROI의 voxel 수 확인
for roi in V1 V2 V3 hV4; do
    echo "=== ${roi} ==="
    fslstats derivatives/sub-P01/roi/sub-P01_${roi}_mask.nii.gz -V
done
```

**예상 Voxel 수 (threshold=50%, from previous results):**
| ROI | 예상 voxel 수 | 상태 |
|-----|--------------|------|
| V1 | 190-250 | ✅ 충분 |
| **V2** | **280-350** | ✅ **최적** (이전 310) |
| V3 | 180-230 | ✅ 충분 |
| hV4 | 100-150 | ⚠️ 적지만 작동 가능 |

**문제 해결:**
- ❌ Voxel 수 < 50: Threshold 낮추기 (50 → 25%)
- ❌ Voxel 수 > 1000: Threshold 높이기 (50 → 75%)
- ⚠️ Voxel 수 적당하지만 성능 낮음: Subject ROI intersection 추가

---

### 2. Zero-Value Voxel 확인
```python
import nibabel as nib
import numpy as np

# ROI mask 로드
roi_img = nib.load('derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz')
roi_data = roi_img.get_fdata()

# BOLD 이미지 로드 (run-1)
bold_img = nib.load('/storage/.../sub-01_task-rsvp_run-1_*_res-2_desc-preproc_bold.nii.gz')
bold_data = bold_img.get_fdata()

# ROI 내부의 BOLD 활성화 확인
roi_mask_bool = roi_data > 0
bold_mean = bold_data.mean(axis=-1)  # Temporal average

# ROI 내부의 zero-value voxel 비율
roi_voxels = bold_mean[roi_mask_bool]
zero_voxels = np.sum(roi_voxels == 0)
total_voxels = len(roi_voxels)

zero_ratio = zero_voxels / total_voxels
print(f"Zero-value voxels: {zero_voxels}/{total_voxels} ({zero_ratio*100:.1f}%)")

# 기준
if zero_ratio < 0.05:  # < 5%
    print("✅ ROI quality EXCELLENT")
elif zero_ratio < 0.20:  # < 20%
    print("✅ ROI quality GOOD")
else:
    print("⚠️ ROI quality WARNING - too many zero voxels")
```

**해석:**
- ✅ Zero ratio < 5%: 거의 모든 voxel 활성화 → 최적
- ✅ Zero ratio < 20%: 대부분 voxel 활성화 → 양호
- ⚠️ Zero ratio > 20%: Brain mask intersection 필요

---

### 3. EPI Overlap 확인
```python
# EPI brain mask와 ROI 교집합 확인
epi_mask = bold_data.mean(axis=-1) > 0  # Non-zero timepoints
roi_mask = roi_data > 0

overlap = np.logical_and(roi_mask, epi_mask)
overlap_ratio = overlap.sum() / roi_mask.sum()

print(f"EPI overlap: {overlap.sum()}/{roi_mask.sum()} ({overlap_ratio*100:.1f}%)")

# 기준
if overlap_ratio > 0.95:  # > 95%
    print("✅ EPI coverage EXCELLENT")
elif overlap_ratio > 0.80:  # > 80%
    print("✅ EPI coverage GOOD")
else:
    print("❌ EPI coverage POOR - brain mask intersection REQUIRED")
```

**해석:**
- ✅ Overlap > 95%: Brain mask intersection 불필요
- ⚠️ Overlap 80-95%: Brain mask intersection 권장
- ❌ Overlap < 80%: Brain mask intersection 필수

---

### 4. Visual Inspection (강력 권장!)
```python
from nilearn import plotting
import matplotlib.pyplot as plt

# Overlay plot
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for idx, roi in enumerate(['V1', 'V2', 'V3', 'hV4']):
    roi_path = f'derivatives/sub-P01/roi/sub-P01_{roi}_mask.nii.gz'
    bold_path = '/storage/.../sub-01_task-rsvp_run-1_*_res-2_desc-preproc_bold.nii.gz'

    # Mean BOLD를 background로 사용
    from nilearn.image import mean_img
    mean_bold = mean_img(bold_path)

    ax = axes[idx // 2, idx % 2]
    plotting.plot_roi(
        roi_path,
        bg_img=mean_bold,
        title=f'{roi} ROI Overlay',
        cut_coords=(-10, -80, 0),  # Occipital cortex
        display_mode='ortho',
        axes=ax,
        cmap='Reds',
        alpha=0.7
    )

plt.tight_layout()
plt.savefig('derivatives/sub-P01/roi/roi_overlay_check.png', dpi=150)
print("✅ ROI overlay visualization saved")
```

**체크포인트:**
- ✅ ROI가 후두엽(occipital cortex)에 위치
- ✅ ROI가 좌우 대칭
- ✅ ROI 경계가 명확
- ❌ ROI가 뇌 밖으로 튀어나옴 → Brain mask 필요
- ❌ ROI가 비정상적으로 작거나 큼 → Threshold 조정

---

## 🔧 문제 해결

### Problem 1: Wang Atlas 파일을 찾을 수 없음
```
[WARN] File not found: ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi3_lh.nii.gz
```

**해결책:**
```bash
# Wang atlas 존재 확인
ls ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi*.nii.gz | head

# 없으면 다운로드 또는 복사 필요
# Wang et al. (2015) atlas: https://osf.io/bw9ec/
```

---

### Problem 2: Voxel 수가 너무 적음 (<50)
```
V4: 15 voxels (너무 적음!)
```

**해결책:**
```python
# roi_build.py line 110 수정
part_mask = part_data > 25  # 50 → 25로 낮춤 (더 많은 voxel 포함)
```

---

### Problem 3: Voxel 수가 너무 많음 (>1000)
```
V2: 1200 voxels (노이즈 너무 많음!)
```

**해결책:**
```python
# roi_build.py line 110 수정
part_mask = part_data > 75  # 50 → 75로 높임 (확실한 voxel만)
```

---

### Problem 4: ROI와 BOLD 공간 불일치
```
ValueError: Shapes do not match
```

**확인:**
```bash
# BOLD shape
fslinfo /storage/.../sub-01_task-rsvp_run-1_*_res-2_desc-preproc_bold.nii.gz | grep dim

# ROI shape
fslinfo derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz | grep dim

# Affine matrix 확인
fslhd sub-01_V2_mask.nii.gz | grep -A4 "qto_xyz"
```

**해결책:**
- config.get_func_img_path(1)가 올바른 BOLD 이미지를 가리키는지 확인
- resample_img의 target_affine, target_shape 확인

---

## 📊 최적 설정 (From Previous Success)

### 권장 파라미터
```python
# Wang atlas threshold
THRESHOLD = 50  # 50% 확률 이상

# Brain mask intersection
USE_BRAIN_MASK = True  # 권장

# Subject ROI intersection
USE_SUBJECT_ROI = False  # Optional (없어도 작동)

# Expected voxel counts (threshold=50%)
EXPECTED_VOXELS = {
    'V1': 220,   # 190-250 범위
    'V2': 310,   # 280-350 범위 (BEST for classification)
    'V3': 200,   # 180-230 범위
    'hV4': 120,  # 100-150 범위
}
```

### 최적 ROI 선택 (From FIR_MODIFICATIONS_SUMMARY.md)
**V2가 가장 성공적:**
- ✅ ~310 voxels (적당한 크기)
- ✅ 100% classification accuracy
- ✅ <30° reconstruction error
- ✅ Best signal-to-noise ratio

**ROI 우선순위:**
1. **V2** (1순위 - 가장 안정적) 🏆
2. **V1** (2순위 - 높은 정확도)
3. **V3** (3순위 - 양호)
4. **hV4** (4순위 - voxel 적지만 작동)

---

## 🎯 Quick Start - Step by Step

### Step 1: 서버 접속 및 환경 준비
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
conda activate nilearn
```

### Step 2: Wang Atlas 확인
```bash
# Atlas 파일 존재 확인
ls ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi*.nii.gz | wc -l
# 예상: 28개 파일 (7 ROI × 2 hemisphere × 2 ventral/dorsal)
```

### Step 3: Reference BOLD 이미지 확인
```bash
# config.get_func_img_path(1) 경로 확인
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz

# Shape 확인
fslinfo /storage/.../sub-01_task-rsvp_run-1_*_res-2_desc-preproc_bold.nii.gz | grep dim
# 예상: dim1=97, dim2=115, dim3=97, dim4=246
```

### Step 4: ROI 생성 실행
```bash
# 직접 실행
python roi_build.py

# 또는 sbatch
sbatch build_rois.sbatch
```

### Step 5: 결과 확인
```bash
# 생성된 ROI 목록
ls -lh derivatives/sub-P01/roi/

# Voxel 수 확인
for roi in V1 V2 V3 hV4; do
    echo "=== ${roi} ==="
    fslstats derivatives/sub-P01/roi/sub-P01_${roi}_mask.nii.gz -V
done
```

### Step 6: 품질 검증 (Python)
```python
import nibabel as nib
import numpy as np

# V2 ROI 검증 (가장 중요)
roi = nib.load('derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz')
roi_data = roi.get_fdata()

# Voxel 수
n_voxels = (roi_data > 0).sum()
print(f"V2 voxel count: {n_voxels}")

# 예상 범위
if 280 <= n_voxels <= 350:
    print("✅ V2 voxel count OPTIMAL")
elif 150 <= n_voxels < 280:
    print("⚠️ V2 voxel count LOW but acceptable")
else:
    print("❌ V2 voxel count OUT OF RANGE - adjust threshold")
```

---

## 📚 References

### ROI Build Script
- **File:** `roi_build.py`
- **Key functions:**
  - `build_wang_rois()`: Wang atlas ROI 생성
  - `build_structural_rois()`: Structural ROI 생성 (optional)
  - `build_all_rois()`: 모든 ROI 한번에 생성

### Wang (2015) Atlas
- **Paper:** Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015). *Cerebral Cortex*
- **Location:** `ProbAtlas_v4/subj_vol_all/`
- **Format:** Probabilistic atlas (0-100% values)

### Previous Results
- **Document:** `FIR_MODIFICATIONS_SUMMARY.md`
- **V2 success:** 310 voxels, 100% classification, <30° reconstruction

---

**작성일:** 2025-11-09
**상태:** Ready to execute
**다음 단계:** ROI 생성 후 fir_reconstruction.py 실행

**ROI 제작이 성공의 절반입니다! 차근차근 검증하면서 진행하세요! 💪**
