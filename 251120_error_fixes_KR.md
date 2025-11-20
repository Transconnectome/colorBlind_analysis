# 에러 수정 및 디버깅 강화

## 발생한 문제

### 1. R² = NaN 에러
```
R² Distribution Analysis
Mean:   nan
Median: nan (will be used as threshold)
```

### 2. Zero-size array 에러
```python
ValueError: zero-size array to reduction operation minimum which has no identity
```

## 원인 분석

문제의 근본 원인은 **ROI mask에서 voxel이 하나도 추출되지 않았기 때문**입니다.

가능한 원인:
1. ROI mask 파일이 존재하지 않음
2. ROI mask 파일이 비어있음 (all zeros)
3. ROI mask와 functional data의 공간 불일치
4. 잘못된 파일 경로

## 적용한 수정 사항

### 1. ROI Mask 로딩 단계 강화 (Line 307-340)

```python
# 더 자세한 경로 출력
print(f"  Attempting to load ROI mask from:")
print(f"  {roi_path}")

# 파일 존재 여부 확인
if not os.path.exists(roi_path):
    print(f"\n❌ ERROR: ROI mask file not found!")
    print(f"  Expected path: {roi_path}")

    # 사용 가능한 대체 파일 제안
    if os.path.exists(alt_dir):
        print(f"\n  Available files in {alt_dir}:")
        for root, dirs, files in os.walk(alt_dir):
            for file in files:
                if ROI_NAME in file and file.endswith('.nii.gz'):
                    print(f"    {os.path.join(root, file)}")

    sys.exit(1)
```

### 2. Voxel 개수 확인 추가 (Line 323-338)

```python
roi_mask = roi_img.get_fdata() > 0
n_voxels_total = np.sum(roi_mask)

print(f"  ROI: {ROI_NAME}")
print(f"  ROI mask path: {roi_path}")
print(f"  ROI mask shape: {roi_img.shape}")
print(f"  Total voxels in mask: {n_voxels_total}")

# Safety check
if n_voxels_total == 0:
    print(f"\n❌ ERROR: No voxels found in ROI mask!")
    print(f"  This could mean:")
    print(f"  1. ROI mask file is empty/all zeros")
    print(f"  2. ROI mask file is corrupted")
    print(f"  3. Wrong ROI name or path")
    sys.exit(1)
```

### 3. Masker Transform 검증 (Line 372-378)

```python
func_data = masker.transform(func_img)

# Safety check for masker output
if func_data.shape[1] == 0:
    print(f"\n❌ ERROR: Masker extracted 0 voxels from run {run}!")
    print(f"  Functional image shape: {func_img.shape}")
    print(f"  Masked data shape: {func_data.shape}")
    print(f"  This means the ROI mask and functional data don't align properly.")
    sys.exit(1)

# 더 자세한 출력
print(f"  Run {run}: {func_data.shape[0]} scans, {func_data.shape[1]} voxels, {len(events)} events")
```

### 4. HRF Correlation 계산 보호 (Line 646-696)

```python
# Safety check
if n_voxels_selected == 0:
    print(f"\n⚠️  WARNING: No voxels selected (R² threshold too high?)")
    print(f"  Skipping HRF variability analysis...")
    hrf_correlations = np.array([])
    hrf_rmse = np.array([])
    hrf_nrmse = np.array([])
    high_corr = 0
    very_high_corr = 0
else:
    # Correlation 계산
    for i in range(n_voxels_selected):
        try:
            hrf_correlations[i] = np.corrcoef(HRF_selected[i], ROI_HRF)[0, 1]
        except:
            hrf_correlations[i] = np.nan

    # Remove NaN values
    valid_mask = ~np.isnan(hrf_correlations)
    hrf_correlations = hrf_correlations[valid_mask]

    if len(hrf_correlations) > 0:
        print(f"\n  Correlation with ROI HRF:")
        print(f"    Mean: {np.mean(hrf_correlations):.4f}")
        ...
    else:
        print(f"\n  ⚠️  No valid correlations computed")
```

## 디버깅 방법

### 1. 수동으로 ROI mask 확인

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

# Subject 01-04의 ROI mask 확인
ls -lh derivatives/sub-01/roi_pipeline/

# Pilot P01의 ROI mask 확인
ls -lh derivatives/pilot/sub-01/roi_pipeline_*/

# Mask 파일이 비어있는지 확인
python3 << EOF
import nibabel as nib
import numpy as np

mask_path = "derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
mask = nib.load(mask_path)
data = mask.get_fdata()

print(f"Mask shape: {data.shape}")
print(f"Non-zero voxels: {np.sum(data > 0)}")
print(f"Min: {data.min()}, Max: {data.max()}")
EOF
```

### 2. 로그 파일 확인

수정된 코드를 실행하면 더 자세한 정보가 출력됩니다:

```bash
# 실행
sbatch run_BH2009.sbatch

# 로그 확인
tail -f logs/BH2009_*.out

# 에러 확인
tail -f logs/BH2009_*.err
```

**예상 출력 (성공 시):**
```
[1/9] Loading ROI mask
  Attempting to load ROI mask from:
  derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz
  ROI: V1
  ROI mask path: derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz
  ROI mask shape: (97, 115, 97)
  Total voxels in mask: 1234

[2/9] Loading functional data (6 runs)
  Run 1: 146 scans, 1234 voxels, 72 events
  Run 2: 146 scans, 1234 voxels, 72 events
  ...
```

**예상 출력 (실패 시 - 파일 없음):**
```
[1/9] Loading ROI mask
  Attempting to load ROI mask from:
  derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz

❌ ERROR: ROI mask file not found!
  Expected path: derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz

  Please check:
  1. ROI masks have been created with roi_pipeline
  2. Path structure matches expected format
  3. ROI name 'V1' is correct

  Available files in derivatives/sub-01:
    derivatives/sub-01/some_other_dir/V1_mask.nii.gz
```

**예상 출력 (실패 시 - 빈 mask):**
```
[1/9] Loading ROI mask
  Attempting to load ROI mask from:
  derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz
  ROI: V1
  ROI mask path: derivatives/sub-01/roi_pipeline/V1_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz
  ROI mask shape: (97, 115, 97)
  Total voxels in mask: 0

❌ ERROR: No voxels found in ROI mask!
  This could mean:
  1. ROI mask file is empty/all zeros
  2. ROI mask file is corrupted
  3. Wrong ROI name or path

Please check the ROI mask file and try again.
```

## 해결 방법

### Case 1: ROI mask 파일이 없는 경우

```bash
# roi_pipeline_comprehensive.py를 먼저 실행
python roi_pipeline_comprehensive.py --subject 01 --roi V1

# 또는 모든 ROI에 대해
for roi in V1 V2 V3 hV4; do
    python roi_pipeline_comprehensive.py --subject 01 --roi $roi
done
```

### Case 2: ROI mask가 비어있는 경우

ROI mask 생성 시 threshold가 너무 높을 수 있습니다. `roi_pipeline_comprehensive.py`의 threshold를 낮춰보세요:

```python
# roi_pipeline_comprehensive.py 수정
threshold = 30  # 기존 50에서 30으로 낮춤
```

### Case 3: 경로가 잘못된 경우

실제 파일 구조를 확인하고 코드의 경로를 수정:

```python
# fir_reconstruction_BH2009.py에서 수정
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_ACTUAL_TIMESTAMP/{ROI_NAME}_mask_ACTUAL_FILENAME.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/ACTUAL_DIR/{ROI_NAME}_mask_ACTUAL_FILENAME.nii.gz"
```

## 테스트 방법

1. **로컬에서 경로 확인**
   ```bash
   # 서버에 SSH 접속
   ssh haba6030@node2
   cd /scratch/connectome/haba6030/colorBlind

   # ROI mask 파일 확인
   find derivatives -name "*V1*mask*.nii.gz" -type f
   ```

2. **단일 subject/ROI로 먼저 테스트**
   ```bash
   # V1만 테스트
   python fir_reconstruction_BH2009.py --subject 01 --roi V1 --use-pca --n-components 6
   ```

3. **성공하면 전체 실행**
   ```bash
   sbatch run_BH2009.sbatch
   ```

## 업데이트된 파일

- **`fir_reconstruction_BH2009.py`**: 에러 핸들링 및 디버깅 강화
- **`251120_error_fixes_KR.md`**: 이 문서

이제 훨씬 더 자세한 에러 메시지가 출력되어 문제를 쉽게 파악할 수 있습니다!
