# SRM Baseline Adaptation - Implementation Checklist

**Date**: 2026-02-06
**Status**: ✅ COMPLETE

---

## ✅ Phase 1: Script Modifications (COMPLETE)

### Python Scripts

- [x] **evaluate_srm_vs_procrustes.py**
  - [x] Add `socket` import for hostname detection
  - [x] Replace `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
  - [x] Add auto-path detection (server vs local)
  - [x] Create `load_baseline_amplitudes()` function
  - [x] Update data loading (use `amplitudes_z.npy` for SRM, `amplitudes_procrustes.npy` for comparison)
  - [x] Update all "whitened" references to "baseline"
  - [x] Update docstrings

- [x] **evaluate_srm_between_subject.py**
  - [x] Add `socket` import
  - [x] Replace `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
  - [x] Add auto-path detection
  - [x] Update `load_subject_amplitudes()` to load `amplitudes_z.npy`
  - [x] Update all references to baseline data
  - [x] Update docstrings

### Batch Scripts

- [x] **sbatch/run_srm_evaluation.sbatch**
  - [x] Update job description (whitened → baseline)
  - [x] Replace `WHITENING_RESULTS_DIR` with `BASELINE_RESULTS_DIR`
  - [x] Update server path
  - [x] Update file checks (`amplitudes_whitened.npy` → `amplitudes_z.npy`)
  - [x] Update prerequisites documentation in header

---

## ✅ Phase 2: Documentation Updates (COMPLETE)

- [x] **EXECUTION_GUIDE_PHASE3_SRM.md**
  - [x] Update prerequisites (Phase 2 → Phase 1)
  - [x] Remove placeholder path update section
  - [x] Update configuration section (paths auto-detected)
  - [x] Update all "whitening" references to "baseline"
  - [x] Simplify setup instructions

---

## ✅ Phase 3: Helper Scripts Creation (COMPLETE)

- [x] **test_srm_server_interactive.sh** (Server test script)
  - [x] Check baseline data exists
  - [x] Activate conda environment (standard method)
  - [x] Verify BrainIAK
  - [x] Run single subject test (sub-01 V1)
  - [x] Monitor execution
  - [x] Show results preview
  - [x] Make executable

---

## ✅ Phase 4: Documentation Creation (COMPLETE)

- [x] **SRM_BASELINE_ADAPTATION_SUMMARY.md**
  - [x] Document all changes made
  - [x] Explain data flow comparison
  - [x] List file locations
  - [x] Provide deployment instructions
  - [x] Include troubleshooting guide
  - [x] Define success criteria

- [x] **QUICK_START_SRM.md**
  - [x] 3-step quick deployment guide
  - [x] Result checking instructions
  - [x] Troubleshooting table
  - [x] Success criteria checklist

- [x] **IMPLEMENTATION_CHECKLIST.md** (This file)
  - [x] Track all implementation tasks
  - [x] Verify completion status

---

## 📋 Pre-Deployment Verification

### File Integrity Checks

- [x] All Python scripts have correct imports
- [x] All path configurations use hostname detection
- [x] All file references updated (whitened → baseline)
- [x] Sbatch script has correct SLURM directives
- [x] All shell scripts are executable
- [x] No placeholder paths remaining

### Code Quality Checks

- [x] No syntax errors in Python scripts
- [x] Proper error handling for file not found
- [x] Clear print statements for debugging
- [x] Docstrings updated accurately
- [x] Comments reflect actual behavior

### Documentation Checks

- [x] Execution guide reflects current implementation
- [x] Quick start guide is concise and accurate
- [x] Summary document is comprehensive
- [x] All file paths are correct
- [x] Next steps are clear

---

## 🚀 Deployment Readiness

### Pre-Deployment

- [x] All files created locally
- [x] Direct scp commands prepared
- [x] Server test script ready (`test_srm_server_interactive.sh`)
- [x] Documentation complete and accurate

### Deployment Steps (To Be Done by User)

- [ ] Run scp commands to upload files
- [ ] SSH to server and verify baseline data exists
- [ ] Install BrainIAK if not already installed
- [ ] Run interactive test (`bash test_srm_server_interactive.sh`)
- [ ] If test passes, submit array job (`sbatch sbatch/run_srm_evaluation.sbatch`)

### Post-Deployment Verification (To Be Done After Job Runs)

- [ ] Check all 40 result files created
- [ ] Verify no OOM errors in logs
- [ ] Compare Procrustes baseline with Phase 1 results
- [ ] Check SRM improvements are reasonable
- [ ] Run aggregation script
- [ ] Generate visualization plots
- [ ] Download results to local machine

---

## 📊 Expected Outcomes

### Success Metrics

**Within-Subject Evaluation:**
- 40 JSON result files (10 subjects × 4 ROIs)
- 40 PNG tuning plots
- Procrustes baseline: RDM correlation 0.15-0.26
- SRM improvement: +5-15% (if beneficial)
- Best k: 30-100 (ROI-dependent)

**Between-Subject Evaluation:**
- 4 JSON result files (one per ROI)
- 4 disparity comparison plots
- 4 RDM similarity matrices
- CVD vs HC disparities with statistical test
- Effect size (Cohen's d)

### Timeline

- Deployment: ~5 minutes
- BrainIAK installation (if needed): ~10-15 minutes
- Interactive test: ~5-10 minutes
- Array job (40 tasks): ~3-4 hours
- Results aggregation: ~5 minutes
- Total: ~4-5 hours end-to-end

---

## 🔧 Modification Summary

### Files Modified (7 files)

1. `evaluate_srm_vs_procrustes.py` - Within-subject SRM evaluation
2. `evaluate_srm_between_subject.py` - Between-subject HC-CVD comparison
3. `sbatch/run_srm_evaluation.sbatch` - SLURM array job script
4. `EXECUTION_GUIDE_PHASE3_SRM.md` - Execution documentation

### Files Created (4 files)

5. `deploy_srm_to_server.sh` - Deployment automation
6. `test_srm_server_interactive.sh` - Interactive testing
7. `test_srm_baseline_local.sh` - Local testing (optional)
8. `SRM_BASELINE_ADAPTATION_SUMMARY.md` - Technical summary
9. `QUICK_START_SRM.md` - Quick reference guide
10. `IMPLEMENTATION_CHECKLIST.md` - This checklist

### Files Unchanged (2 files)

- `aggregate_srm_results.py` - Works as-is with baseline results
- `visualize_srm_comparison.py` - Works as-is with baseline results

---

## ✅ Final Status

**All implementation tasks complete!**

**Ready for deployment:**
- ✅ Code modifications complete
- ✅ Documentation updated
- ✅ Helper scripts created
- ✅ Deployment automation ready
- ✅ Testing procedures defined
- ✅ Troubleshooting guides provided

**Next action:** User runs `bash deploy_srm_to_server.sh` to begin deployment.

---

**Implementation completed**: 2026-02-06
**Implementer**: Claude Code
**Verification**: All checklist items marked complete
