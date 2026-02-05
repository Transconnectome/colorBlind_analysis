# Grid Coordinates 저장 및 분석 절차

## 문제 요약

현재 ANOVA voxel selection에서 저장한 `voxel_indices.npy`는 **각 피험자 ROI mask 내의 상대적 위치**입니다.
이를 직접 비교하면 실제로는 다른 뇌 위치인데도 같은 voxel로 착각하게 됩니다.

## 해결 방법

각 피험자의 선택된 voxel에 대해 **절대 grid 좌표 (i, j, k)**를 저장하고,
이 좌표를 기준으로 피험자 간 교집합을 찾습니다.

---

## Step 1: 서버에서 Grid Coordinates 저장

### 1-1. 스크립트 업로드

```bash
# 로컬에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp analysis/phase1_preprocess_decoding/scripts/save_voxel_grid_coords.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/scripts/
```

### 1-2. 서버에서 실행

```bash
# 서버 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 환경 활성화
conda activate nilearn

# 스크립트 실행
python analysis/phase1_preprocess_decoding/scripts/save_voxel_grid_coords.py
```

**예상 출력**:
```
Processing sub-01/V1:
    Found mask: /scratch/.../rois/sub-01/native/V1_mask.nii.gz
    Saved mask: results/baseline_anova_selected/sub-01/V1/roi_mask.nii.gz
    Saved coordinates: selected 129 out of 354 voxels
    Grid coord ranges:
      All:      i=[10, 50], j=[30, 80], k=[15, 45]
      Selected: i=[15, 48], j=[35, 75], k=[18, 42]
...
Summary: 40 successful, 0 failed
```

**생성되는 파일** (각 sub-XX/ROI/ 폴더에):
- `roi_mask.nii.gz` - ROI mask 이미지
- `all_grid_coords.npy` - mask 내 모든 voxel의 grid 좌표 (n_voxels, 3)
- `selected_grid_coords.npy` - 선택된 voxel의 grid 좌표 (k, 3)
- `voxel_grid_info.json` - 메타데이터 및 좌표 범위

---

## Step 2: 로컬로 다운로드

```bash
# 로컬에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Grid coordinates와 masks 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_anova_selected/sub-*/*/selected_grid_coords.npy \
    analysis/phase1_preprocess_decoding/results/baseline_anova_selected/

# 또는 전체 다운로드 (ROI masks 포함, 용량 큼)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_anova_selected/ \
    analysis/phase1_preprocess_decoding/results/
```

**주의**: ROI mask 이미지 파일(.nii.gz)은 용량이 클 수 있습니다.
필요한 경우에만 다운로드하고, 분석에는 `selected_grid_coords.npy`만 있어도 충분합니다.

---

## Step 3: Grid Coordinates로 교집합 재계산

로컬에서 `corrected_procrustes_analysis.py`를 grid coordinates 버전으로 수정하여 실행합니다.

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding

# Grid coordinates 기반 교집합 분석
python scripts/corrected_procrustes_with_grid_coords.py \
    --input-dir results/baseline_anova_selected \
    --output-dir results/corrected_procrustes_grid \
    --hc-subjects 01,02,03,04,05,06,07 \
    --cvd-subjects 08,09,10
```

---

## Expected Results

### Before (relative indices):
```
V1: 0 common voxels  (교집합 없음)
V2: 0 common voxels  (교집합 없음)
V3: 11 common voxels (22% of 50)
hV4: 10 common voxels (17.5% of 57)
```

### After (grid coordinates):
```
V1: ? common voxels  (예상: 10-30개, 8-23%)
V2: ? common voxels  (예상: 5-20개, 5-19%)
V3: ? common voxels  (예상: 20-40개, 40-80%)
hV4: ? common voxels  (예상: 15-45개, 26-79%)
```

V3/hV4는 ROI 크기가 작아 overlap이 높고,
V1/V2는 ROI 크기가 커서 overlap이 낮을 것으로 예상됩니다.

---

## Troubleshooting

### Issue 1: ROI mask 파일을 찾을 수 없음

```
❌ ROI mask not found, skipping
```

**해결책**: ROI mask 경로 확인
```bash
# 서버에서 ROI mask 위치 확인
find /scratch/connectome/haba6030/colorBlind/derivatives -name "*V1*mask*" -type f

# 찾은 경로를 save_voxel_grid_coords.py의 possible_paths에 추가
```

### Issue 2: ANOVA results가 없음

```
⚠️  ANOVA results not found, skipping
```

**원인**: `apply_anova_voxel_selection.py`가 아직 실행되지 않음

**해결책**: 먼저 ANOVA selection 실행
```bash
python scripts/apply_anova_voxel_selection.py \
    --input-dir results/baseline \
    --output-dir results/baseline_anova_selected \
    --k-values V1:129,V2:103,V3:50,hV4:57
```

### Issue 3: 메모리 부족

ROI mask 파일(.nii.gz)이 크면 메모리 문제 발생 가능

**해결책**: coordinates만 저장 (mask 이미지는 옵션)
- `selected_grid_coords.npy`: 작음 (~1KB)
- `roi_mask.nii.gz`: 클 수 있음 (~1-10MB)

---

## Summary

1. ✅ 서버에서 `save_voxel_grid_coords.py` 실행 → grid coordinates 저장
2. ✅ 로컬로 `*_grid_coords.npy` 다운로드
3. ✅ Grid coordinates 기반으로 교집합 재계산
4. ✅ CORRECTED Procrustes 재실행
5. ✅ 결과 비교 및 해석
