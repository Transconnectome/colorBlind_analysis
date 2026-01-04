# Project Reorganization Plan

## Current Issues
1. 루트 디렉토리에 너무 많은 파일들 (80+ files)
2. 문서, 스크립트, 결과가 혼재
3. Outdated 파일들이 정리되지 않음
4. GitHub에 올리기 부적합한 구조

## Proposed Structure

```
colorBlind_analysis/
├── README.md                          # 새로 작성
├── CLAUDE.md                          # 유지 (개발 가이드)
├── environment.yml                    # Conda environment spec
│
├── analysis/                          # Main analysis code
│   ├── __init__.py
│   ├── preprocessing/
│   │   ├── fir_reconstruction_BH2009_system_clean.py
│   │   └── grid_search_preprocessing.py
│   ├── feature_selection/
│   │   ├── feature_selection_anova.py
│   │   ├── feature_selection_rfe.py
│   │   └── feature_selection_pca.py
│   ├── group_level/
│   │   ├── group_level_analysis_comprehensive.py
│   │   ├── group_level_common_voxels.py
│   │   └── group_level_pca_analysis.py
│   └── utils/
│       └── utils_color_decoding.py
│
├── scripts/                           # Phase-specific scripts
│   ├── phase1_baseline/              # Baseline analysis
│   ├── phase2a_filter_learning/      # Linear filter (현재 진행중)
│   │   ├── phase2a_train_single.py
│   │   ├── phase2a_train_filter.py
│   │   ├── apply_filter_with_reconstruction.py
│   │   └── visualize_rdm_*.py
│   └── diagnostics/                  # QC and diagnosis
│       ├── diagnose_qc_results.py
│       ├── check_roi_quality_comparison.py
│       └── visualize_qc.py
│
├── slurm_jobs/                       # SLURM batch scripts
│   ├── preprocessing/
│   │   ├── run_fmriprep_*.sbatch
│   │   └── run_roi_pipeline_*.sbatch
│   ├── analysis/
│   │   └── run_procrustes_*.sbatch
│   └── qc/
│       ├── qc_runwise.sh
│       └── run_qc_all_subjects_array.sbatch
│
├── docs/                             # Documentation
│   ├── README.md                     # Docs index
│   ├── guides/                       # User guides
│   │   ├── GUIDE_to_fMRIprep.md
│   │   ├── GUIDE_to_classify_reconstruct.md
│   │   ├── GROUP_ANALYSIS_COMPLETE_GUIDE.md
│   │   └── QUICK_START_*.md
│   ├── methods/                      # Methodology docs
│   │   ├── PHASE1_RESULTS_ANALYSIS.md
│   │   ├── PHASE2A_FILTER_METHODS.md
│   │   ├── PROCRUSTES_ANALYSIS_GUIDE.md
│   │   └── ROBUSTNESS_VALIDATION_METHODS.md
│   ├── technical/                    # Technical reports
│   │   ├── FMRIPREP_VERSION_COMPARISON.md
│   │   ├── PREPROCESSING_METHOD_UPDATE.md
│   │   ├── MNI_DIAGNOSIS_FINAL_REPORT.md
│   │   └── NATIVE_ROI_RESULTS_DIAGNOSIS.md
│   ├── paper/                        # Paper manuscript
│   │   ├── main_kr.tex
│   │   ├── main_kr.pdf
│   │   └── figures/
│   └── archive/                      # Outdated/legacy docs
│       ├── trial_options/
│       └── OHBM_abstract/
│
├── results/                          # Analysis results (gitignored)
├── derivatives/                      # Processed data (gitignored)
├── logs/                             # Log files (gitignored)
│
├── materials/                        # Stimuli and atlases
├── papers/                           # Reference papers
│
└── archive/                          # Outdated code & experiments
    ├── backup/
    ├── prepfigs/
    ├── preps/
    └── old_scripts/                  # 루트에서 이동한 outdated scripts
```

## Files to Move

### 1. Analysis Scripts → analysis/
- `fir_reconstruction_BH2009_system_clean.py` → analysis/preprocessing/
- `grid_search_preprocessing.py` → analysis/preprocessing/
- `feature_selection_*.py` (3 files) → analysis/feature_selection/
- `group_level_*.py` (4 files) → analysis/group_level/
- `utils_color_decoding.py` → analysis/utils/

### 2. Diagnostic Scripts → scripts/diagnostics/
- `diagnose_*.py` (4 files)
- `check_roi_quality_comparison.py`
- `visualize_qc.py`
- `generate_detailed_qc_visualizations.py`
- `TRACE_FMRIPREP_STAGES.py`

### 3. SLURM Jobs → slurm_jobs/
- `run_*.sbatch` (모든 sbatch 파일)
- `run_*.sh` (모든 shell 스크립트)
- `qc_runwise*.sh`

### 4. Documentation → docs/
#### docs/guides/
- `QC_EXECUTION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `QUICK_START_*.md`
- `PROCRUSTES_RECONSTRUCTION_QUICKSTART.md`

#### docs/methods/
- (현재 docs/에 있는 PHASE*, PROCRUSTES 등 유지)

#### docs/technical/
- `FMRIPREP_VERSION_COMPARISON*.md`
- `COMPREHENSIVE_PREPROCESSING_ANALYSIS_FINAL.md`
- `MNI_DIAGNOSIS_*.md`
- `NATIVE_ROI_*.md`

#### docs/archive/
- `OHBM_abstract/` (이미 지난 초록)
- 모든 outdated comparison 문서들

### 5. Root Documentation → Keep Only Essential
**Keep:**
- `README.md` (새로 작성)
- `CLAUDE.md` (개발 가이드)
- `LICENSE` (필요시)
- `.gitignore`

**Move to docs/:**
- `BASELINE_RESULTS_SUMMARY.md` → docs/results/
- `CVD_ANALYSIS_FINAL.md` → docs/results/
- `EXECUTIVE_SUMMARY_1PAGE.md` → docs/
- `FINAL_REPORT_WITH_VISUALIZATION.md` → docs/results/
- `STATISTICAL_SUMMARY.txt` → docs/results/

### 6. Outdated/Delete
**Move to archive/old_scripts/:**
- `compare_baseline_vs_permutation_bestK.py` (삭제됨)
- `create_summary_csvs.py` (삭제됨)
- `summarize_permutation_with_hitrate.py` (삭제됨)
- `verify_bestk_permutation.py` (삭제됨)
- `create_permuted_amplitudes.py` (outdated)

**Delete permanently:**
- `advanced_qc_section.md` (incomplete)
- `.DS_Store` files
- Temporary QC files (`qc_runwise_sub-*.tsv`)

## Git Cleanup

```bash
# Remove deleted files from git
git rm compare_baseline_vs_permutation_bestK.py
git rm create_summary_csvs.py
git rm summarize_permutation_with_hitrate.py
git rm verify_bestk_permutation.py
git rm backup/fMRIprep/sbatch_fmriprep_storage.sub
git rm docs/GUIDE_to_fMRIprep.md  # 이미 CLAUDE.md에 통합
git rm docs/REPORT_ROI_Oblique_Issues.md  # outdated

# Clean temporary files
find . -name ".DS_Store" -delete
rm qc_runwise_sub-*.tsv
```

## Implementation Order

1. **Phase 1: Create new directories**
   ```bash
   mkdir -p analysis/{preprocessing,feature_selection,group_level,utils}
   mkdir -p scripts/{phase1_baseline,phase2a_filter_learning,diagnostics}
   mkdir -p slurm_jobs/{preprocessing,analysis,qc}
   mkdir -p docs/{guides,methods,technical,results,archive,paper}
   ```

2. **Phase 2: Move analysis code**
   - Move core analysis scripts to analysis/
   - Update imports in moved files

3. **Phase 3: Move scripts**
   - Organize scripts/ by phase
   - Move diagnostic scripts

4. **Phase 4: Move SLURM jobs**
   - Organize all batch scripts

5. **Phase 5: Reorganize docs**
   - Categorize documentation
   - Move outdated to archive

6. **Phase 6: Git cleanup**
   - Remove deleted files
   - Clean temporary files

7. **Phase 7: Create README.md**
   - Project overview
   - Paper summary
   - 3-phase future directions

8. **Phase 8: Update .gitignore**
   - Add results/, derivatives/, logs/
   - Add temporary files patterns
