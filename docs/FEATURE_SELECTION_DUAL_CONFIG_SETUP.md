# Feature Selection Dual Config Setup Guide

**Purpose**: Compare Non-Probabilistic vs Probabilistic ROI masks
**Date**: 2025-01-20

---

## Overview

이 가이드는 feature selection 방법을 비교하기 위한 dual config 설정을 설명합니다:

1. **Non-Probabilistic ROI** (이미 완료)
   - `roi_pipeline_deob_Noprob`
   - Binary masks (threshold-based)

2. **Probabilistic ROI** (새로 실행)
   - `roi_pipeline_deob_prob`
   - Probability-weighted masks

---

## 1. Current Baseline Structure

### 현재 디렉토리 구조

```
derivatives/
├── BH2009_deoblique_v2/
│   ├── baseline32/                    # Old (generic name)
│   ├── baseline32_deob/                # New (specific name)
│   ├── baseline81/
│   └── baseline81_deob/
└── BH2009_original/
    ├── baseline32/
    ├── baseline32_origin/
    ├── baseline81/
    └── baseline81_origin/
```

### ✅ 현재 구조는 이미 적합함

- Timestamp 기반으로 구분됨
- Fallback 메커니즘 있음 (baseline32_deob → baseline32)
- 분석 스크립트가 자동으로 처리

---

## 2. Probabilistic ROI용 수정사항

### 필요한 수정: ❌ **없음**

**이유:**
1. `--roi-pipeline-dir` 파라미터가 이미 존재
2. `--timestamp` 파라미터로 출력 디렉토리 구분
3. 분석 스크립트가 자동으로 처리

### 새로운 Batch 파일만 생성하면 됨

**파일명 예시:**
- `run_all_subjects_baseline32_deob_prob.sbatch`
- `run_all_subjects_baseline81_deob_prob.sbatch`

**주요 변경사항:**
```bash
# Non-Probabilistic (기존)
ROI_PIPELINE_DIR="roi_pipeline_deob_Noprob"
TIMESTAMP="baseline32_deob"

# Probabilistic (신규)
ROI_PIPELINE_DIR="roi_pipeline_deob_prob"
TIMESTAMP="baseline32_deob_prob"
```

---

## 3. Batch 파일 생성

### Baseline 32 - Probabilistic

파일: `run_all_subjects_baseline32_deob_prob.sbatch`

**주요 설정:**
```bash
#SBATCH --job-name=b32_deob_p
#SBATCH --output=logs/feature_selection/baseline32_deob_prob_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/baseline32_deob_prob_sub-%a_%j.err

DATASET="deoblique_v2"
ROI_PIPELINE_DIR="roi_pipeline_deob_prob"    # 핵심 변경
TIMESTAMP="baseline32_deob_prob"              # 핵심 변경
SMOOTH=0
STANDARDIZE=""
```

### Baseline 81 - Probabilistic

파일: `run_all_subjects_baseline81_deob_prob.sbatch`

**주요 설정:**
```bash
#SBATCH --job-name=b81_deob_p
#SBATCH --output=logs/feature_selection/baseline81_deob_prob_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/baseline81_deob_prob_sub-%a_%j.err

DATASET="deoblique_v2"
ROI_PIPELINE_DIR="roi_pipeline_deob_prob"    # 핵심 변경
TIMESTAMP="baseline81_deob_prob"              # 핵심 변경
SMOOTH=6
STANDARDIZE="--standardize"
```

---

## 4. Analysis Script 수정

### 기존 CONFIGS에 추가

```python
# In analyze_baseline_results.py

CONFIGS = {
    # ... existing configs ...

    # NEW: Probabilistic ROI configs
    'baseline32_deob_prob': {
        'dataset': 'deoblique_v2',
        'timestamp': 'baseline32_deob_prob',
        'fallback_timestamp': None,  # No fallback needed
        'config_num': 32,
        'smooth': 0,
        'standardize': 'No',
        'roi_method': 'Probabilistic'  # NEW field
    },
    'baseline81_deob_prob': {
        'dataset': 'deoblique_v2',
        'timestamp': 'baseline81_deob_prob',
        'fallback_timestamp': None,
        'config_num': 81,
        'smooth': 6,
        'standardize': 'Yes',
        'roi_method': 'Probabilistic'  # NEW field
    }
}
```

---

## 5. Comparison Matrix

### Full Comparison (4 configs × 2 ROI methods = 8 total)

| Config | Dataset | Smooth | Std | ROI Method | Timestamp |
|--------|---------|--------|-----|------------|-----------|
| 32 | deob | 0mm | No | Non-Prob | `baseline32_deob` |
| 32 | deob | 0mm | No | **Prob** | `baseline32_deob_prob` |
| 81 | deob | 6mm | Yes | Non-Prob | `baseline81_deob` |
| 81 | deob | 6mm | Yes | **Prob** | `baseline81_deob_prob` |

**Optional** (if origin works):
| 32 | origin | 0mm | No | Non-Prob | `baseline32_origin` |
| 32 | origin | 0mm | No | **Prob** | `baseline32_origin_prob` |
| 81 | origin | 6mm | Yes | Non-Prob | `baseline81_origin` |
| 81 | origin | 6mm | Yes | **Prob** | `baseline81_origin_prob` |

---

## 6. Execution Steps

### Step 1: ROI Mask 생성 확인

```bash
# Probabilistic ROI masks이 존재하는지 확인
ssh haba6030@node2
ls derivatives/sub-*/roi_pipeline_deob_prob/*_mask_*.nii.gz | wc -l
# Expected: 9 subjects × 4 ROIs = 36 files

# 없으면 생성 필요
# (ROI pipeline script 실행)
```

### Step 2: Batch 파일 업로드

```bash
# 로컬에서
scp run_all_subjects_baseline32_deob_prob.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_all_subjects_baseline81_deob_prob.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 3: 실행

```bash
# 서버에서
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Probabilistic ROI 실행
sbatch run_all_subjects_baseline32_deob_prob.sbatch
sbatch run_all_subjects_baseline81_deob_prob.sbatch

# 상태 확인
squeue -u haba6030
```

### Step 4: 결과 다운로드

```bash
# 로컬에서
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline32_deob_prob ./derivatives/BH2009_deoblique_v2/
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline81_deob_prob ./derivatives/BH2009_deoblique_v2/
```

### Step 5: 분석

```bash
# analyze_baseline_results.py 수정 (CONFIGS 추가)
# 그 다음
./run_baseline_analysis.sh
```

---

## 7. Expected Output Structure

```
derivatives/
└── BH2009_deoblique_v2/
    ├── baseline32_deob/           # Non-Probabilistic
    │   └── sm0.0_*_sub-01_V1_*masknone_gmFalse_subjFalse/
    │       └── analysis_summary.json
    │
    ├── baseline32_deob_prob/      # Probabilistic (NEW)
    │   └── sm0.0_*_sub-01_V1_*[prob_config]/
    │       └── analysis_summary.json
    │
    ├── baseline81_deob/
    │   └── sm6.0_*_sub-01_V1_*masknone_gmFalse_subjFalse/
    │
    └── baseline81_deob_prob/      # Probabilistic (NEW)
        └── sm6.0_*_sub-01_V1_*[prob_config]/
```

---

## 8. Validation Checklist

### Before Running

- [ ] Probabilistic ROI masks exist for all subjects
- [ ] ROI config string matches actual files
- [ ] Batch files have correct parameters
- [ ] Log directory exists: `logs/feature_selection/`

### After Running

- [ ] All 9 subjects × 4 ROIs completed
- [ ] analysis_summary.json files exist
- [ ] Classification accuracy computed
- [ ] Reconstruction error computed
- [ ] No empty result directories

### Analysis

- [ ] CONFIGS updated in analyze_baseline_results.py
- [ ] CSV generated successfully
- [ ] Visualization created
- [ ] Comparison table shows Prob vs Non-Prob

---

## 9. Comparison Analysis

### Metrics to Compare

1. **Classification Accuracy**
   - Non-Prob vs Prob
   - By ROI (V1, V2, V3, hV4)
   - By subject

2. **Voxel Selection**
   - Number of voxels selected
   - Mean R² of selected voxels
   - Selection ratio

3. **Signal Quality**
   - Mean SNR
   - HRF correlation
   - Response amplitude

### Expected Questions

1. Does probabilistic ROI improve performance?
2. Which ROI method selects better voxels?
3. Is the effect consistent across subjects?
4. Does the effect vary by visual area?

---

## 10. Potential Issues & Solutions

### Issue 1: ROI Config String Mismatch

**Problem**: Probabilistic ROI masks have different naming convention

**Solution**: Check actual filenames
```bash
ls derivatives/sub-01/roi_pipeline_deob_prob/V1_mask_*.nii.gz
```

Update default roi_config in Python script if needed:
```python
parser.add_argument('--roi-config', type=str,
                    default='thr50_intnearest_binTrue_masknone_gmFalse_subjFalse')
```

### Issue 2: Empty Result Directories

**Problem**: Job starts but no analysis_summary.json created

**Solution**: Check error logs
```bash
cat logs/feature_selection/baseline32_deob_prob_sub-0_*.err
```

Common causes:
- ROI mask not found
- fMRIPrep data missing
- Python environment issue

### Issue 3: Analysis Script Can't Find Results

**Problem**: find_result_dir() returns None

**Solution**: Check pattern matching
```python
# Debug
import glob
pattern = "derivatives/BH2009_deoblique_v2/baseline32_deob_prob/sm*_sub-01_V1_*"
matches = glob.glob(pattern)
print(f"Found {len(matches)} matches")
```

---

## 11. Summary

### ✅ No Code Changes Needed

현재 구조가 이미 dual config를 지원합니다:
- ✅ `--roi-pipeline-dir` parameter
- ✅ `--timestamp` parameter
- ✅ Flexible output structure
- ✅ Analysis script handles multiple configs

### 📝 Only Need

1. **Create new batch files** (2 files)
   - `run_all_subjects_baseline32_deob_prob.sbatch`
   - `run_all_subjects_baseline81_deob_prob.sbatch`

2. **Update analysis CONFIGS** (minor edit)
   - Add 2 new entries to CONFIGS dict

3. **Generate probabilistic ROI masks** (if not exist)
   - Run ROI pipeline with probabilistic settings

### 🚀 Ready to Go

Framework is ready for feature selection comparison!

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: ✅ **READY FOR EXECUTION**
