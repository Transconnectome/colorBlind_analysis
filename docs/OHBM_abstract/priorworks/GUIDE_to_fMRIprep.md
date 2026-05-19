# GUIDE_to_fMRIprep.md

This file provides guidance to Claude Code (claude.ai/code) for below.
- File structures
- BIDS file information
- Settings for fMRIprep in this project.
- fMRIprep outcome diagnosis
- Make ROI files for participants

## 1. File Structures & BIDS file information

**Subject Groups:**
- **HC subjects (all)**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07 (7 subjects)
- **CVD subjects (all)**: sub-08, sub-09, sub-10 (3 subjects)

**Analyzable Subjects (as of 2025-12-12):**
- **HC (analyzable)**: sub-01, sub-02, sub-03, sub-05, sub-06, sub-07 (6 subjects)
- **CVD (analyzable)**: sub-08, sub-09, sub-10 (3 subjects)
- **Excluded from current analysis**: sub-04 (No BOLD signal at V1 atlas location - to be recovered in future)

**Note on sub-04**: ROI alignment diagnostic (Job 67066+) revealed V1 atlas location has zero BOLD signal across all timepoints, unlike sub-03/09/10 where signal exists but was excluded by functional brain mask. See `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md` for details.

**Data Paths (After Deoblique Preprocessing):**
```bash
INPUT_DIR=/storage/connectome/haba6030/colorBlind_data_deoblique
OUTPUT_DIR_V1=/storage/connectome/haba6030/fmriprep_out_deoblique      # Original (fieldmap not applied)
OUTPUT_DIR_V2=/storage/connectome/haba6030/fmriprep_out_deoblique_v2   # Improved (fieldmap applied)
WORK_DIR_V1=/storage/connectome/haba6030/fmriprep_work_deoblique_batch2
WORK_DIR_V2_B1=/storage/connectome/haba6030/fmriprep_work_deoblique_v2_batch1  # Sub-01~05
WORK_DIR_V2_B2=/storage/connectome/haba6030/fmriprep_work_deoblique_v2_batch2  # Sub-06~10
```

- **Event/Stimulus files**: `/storage/connectome/haba6030/colorBlind_data_deoblique/sub-{ID}/func/`

- **fMRIPrep outputs (v2 - RECOMMENDED)**: `/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-{ID}/func/`
  - ✅ **Fieldmap applied** (B0FieldIdentifier present)
  - ✅ Better registration (DOF 9, BBR forced, dummy scans removed)
  - ✅ All 10 subjects (01-10)
  - BOLD files: `sub-{ID}_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz`
  - Confounds: `sub-{ID}_task-rsvp_run-X_desc-confounds_timeseries.tsv`

- **Analysis outputs**: `/scratch/connectome/haba6030/colorBlind/derivatives/`

**IMPORTANT**:
- **All analysis MUST use `fmriprep_out_deoblique_v2`** (improved version with fieldmap) for now

### ✅ 1.1. Fieldmap Status (Updated 2025-12-10)

**All subjects have proper IntendedFor fields in their fieldmap JSON files:**
- Both `phasediff.json` and `magnitude1.json` properly configured

**Note**: BIDS conversion via dcm2niix successfully generated IntendedFor fields. No manual JSON editing required.

---

## 2. fMRIprep settings
- Objective: 향후 reconstruction & classification 작업을 우수하게 수행하도록 전처리
  1. ROI별 Wang Atlas 적용 시 의도한 부위의 voxel을 최대한, 그리고 해당 ROI voxel만을 포함하도록 corregistration
  2. 모든 피험자의 공통 뇌 반응 확인을 위한 2nd level GLM 예정. 이를 위해 MNI space 2mm로 일치
  3. 참가자 별 다른 설정 (oblique 등)을 해소하여 동일한 조건에서 분석될 수 있도록 함. 
  4. 그 외 일반적인 MRI 데이터 전처리 과정에 부합하도록 fMRIprep setting.

- Related to fMRIprep setting
  1. 해결된 문장은 (1) 문제 상황 (2) 해결 방법 (3) 원인 및 해결 원리 형식으로 짧게 정리
  2. 대화 로그 중 fMRIprep으로 인한 데이터 품질 문제의 경우 아래의 새로 기록. 
  3. 본 파일 외의 별도의 마크다운 파일 생성은 최대한 지양

### 2.1. ⚠️ Fieldmap Application Issue (v1)

**Issue discovered (2025-12-10)**:
- IntendedFor 필드는 존재하지만 **fieldmap이 실제로 적용되지 않음**
- Output JSON에 `B0FieldIdentifier` 없음
- 원인: `--skip-bids-validation` + `--bold2t1w-dof 6` (too restrictive)

**Solution**: Improved fMRIPrep v2 실행 중: 본 설정으로 문제 해결 시 이 프로젝트의 설정으로 고정
- Output: `/storage/connectome/haba6030/fmriprep_out_deoblique_v2`
- Subjects: **All 10 subjects (01-10)**
  - Batch 1: Sub-01~05
  - Batch 2: Sub-06~10
- Key improvements:
  - ✅ `--bold2t1w-dof 9` (affine instead of rigid)
  - ✅ `--force-bbr` (force high-quality registration)
  - ✅ Removed `--skip-bids-validation` (enable fieldmap validation)
  - ✅ `--dummy-scans 4` (remove unstable initial volumes)

**Verification command** (to check if fieldmaps are being used in v2):
```bash
# Check B0FieldIdentifier in output JSON (most reliable)
cat /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-{ID}/func/sub-{ID}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.json | grep -i "B0Field"

# Expected output (if fieldmap applied):
"B0FieldIdentifier": "auto_00000"
```
## 3. Make ROI files & Outcome Diagnosis
## 3.1. ROI 마스크 제작

**목적**: 각 참가자 별 ROI (V1, V2, V3, hV4) mask 제작

### ROI Construction
ROIs are built from Wang (2015) atlas using mappings defined in `roi_build.py`:
- V1: roi1 (V1v) + roi2 (V1d)
- V2: roi3 (V2v) + roi4 (V2d)
- V3: roi5 (V3v) + roi6 (V3d)
- hV4: roi7

- Match affine with reference anatomical & functional data to `MNI152NLin2009cAsym`

### Code guide
아래 코드는 다음과 같은 여러 세팅들을 시도한 결과로 ROI mask를 제작함. 
시도의 경우 아래와 같은 설정의 조합을 reconstruction, classification 결과값을 기준으로 비교하였음.
```
Threshold for probability maps: [0.1, 0.3, 0.5]
Interpolation method: Nearest, Linear
Binarization options: T/F
Brain mask intersection: None, Func, Anat
GM probseg intersection: Gray matter probability (> 35%)
```

여러 선택지를 시도한 후, 실제 roi_pipeline 폴더에 roi 마스크를 저장할 때는 
roi_pipeline_selected_1202used.py 파일을 활용
현재 최적은 아래와 같다. 

```
Threshold for probability maps: 0.5
Interpolation method: Nearest
Binarization options: True
Brain mask intersection: None
GM probseg intersection: Gray matter probability (> 35%)
Brain mask intersection: Func
```

### 스크립트 실행
roi_pipeline_selected_1202used.py을 run_roi_pipeline_selectedOnly.sbatch로 실행. 

## 3.2. ROI 마스크 점검 (전처리 적용 전 필수 절차)

**목적**: 전처리 적용 전에 ROI mask와 functional data의 공간적 호환성을 확인합니다.

### 1. 진단 스크립트 실행

```bash
# 서버에 파일 업로드
scp diagnose_roi_mask_issue.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_roi_diagnosis.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 서버에서 실행
cd /scratch/connectome/haba6030/colorBlind
chmod +x run_roi_diagnosis.sh
sbatch run_roi_diagnosis.sh

# 결과 다운로드 (로컬에서)
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/roi_mask_diagnostic_report.txt ./logs/
```

### 2. 점검 항목

진단 스크립트 (`diagnose_roi_mask_issue.py`)는 모든 피험자에 대해 다음을 확인합니다:

1. **Functional reference 품질**
   - Shape: (97, 115, 97) 확인
   - Affine diagonal: [2, 2, 2, 1] 확인
   - Posterior signal coverage (z>30): 후두엽 signal 비율
   - Z-axis range: EPI signal이 존재하는 slice 범위

2. **Functional brain mask**
   - Voxel 수 및 coverage
   - Posterior voxels (z>30) 비율
   - Affine match with functional reference

3. **GM probability segmentation**
   - Voxels > 0.35 threshold (현재 설정)
   - Voxels > 0.20 threshold (대안 평가)
   - Affine/shape match with functional reference
   - Resampling 전후 품질 변화

4. **ROI overlap with functional mask** (핵심 지표)
   - Wang atlas의 각 ROI (V1, V2, V3, hV4)를 functional 공간으로 resample
   - Functional brain mask와의 overlap 비율 계산
   - 정상: >50% overlap
   - 경고: <50% overlap
   - 치명적: 0% overlap

5. **실제 overlay 사진** (핵심 지표)
   - Derivatives에 생성된 overlay png 파일에서 뇌영역을 해당 mask가 잘 포함하고 있는지 확인. 

### 3. 출력 결과

진단 보고서 (`roi_mask_diagnostic_report.txt`)는 다음을 포함합니다:

- 피험자별 상세 진단 결과
- 정상 vs 문제 피험자 비교 테이블
- ROI overlap 비교 테이블
- 평균값 기반 결론

보고서는 `logs/` 디렉토리에 보관하여 추후 참조합니다. 
