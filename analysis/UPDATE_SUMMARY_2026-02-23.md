# METHODS_RESULTS_SUMMARY Update Summary (2026-02-23)

## Changes Made

### 1. Added Result 9: LOCO Ensemble Rollout Validation (Line 1038)

**Location**: Inserted after Result 8 "Implications: Ensemble Encoding Rollout" section

**Content**:
- Comprehensive validation of LOCO decoding across all 3 alignments (raw, Procrustes, SRM)
- Confirmed ForwardEncoding baseline performance across alignment methods
- Documented non-linear model (MLP, SVM, Hybrid) failure in LOCO context
- Established that raw space performs at chance (~90°) for all models
- Demonstrated Procrustes superiority over SRM (7/8 comparisons)
- Provided rationale for why non-linear models fail (insufficient training samples)
- Cross-referenced to Result 8 (FE_Ensemble) and LORO results
- Documented pending work (FE_Ensemble × raw/SRM, LORO validation)

**Key Tables**:
1. Alignment Comparison (HC and CVD groups, ForwardEncoding baseline)
2. Non-Linear Model Performance (Procrustes, HC and CVD groups)
3. Relative degradation compared to ForwardEncoding baseline
4. LORO vs LOCO comparison

### 2. Updated Pending Validations Table (Line ~1352)

**Changes**:
- Split "Ensemble rollout: LOCO + LORO" into two separate rows
- Marked LOCO as **DONE** with reference to Result 9
- Kept LORO as **In progress** with note about server jobs
- Updated status descriptions for clarity

**Before**:
```
| **Ensemble rollout: LOCO + LORO (raw, procrustes, SRM)** | Phase 2b | **Not started** | **Fatal** | Re-run all FE and hybrid models...
```

**After**:
```
| ~~Ensemble rollout: LOCO (raw, procrustes, SRM)~~ | Phase 2b | **DONE** | ~~Fatal~~ | Result 9: LOCO complete all 3 alignments...
| **Ensemble rollout: LORO (raw, procrustes, SRM)** | Phase 2b | **In progress** | **Fatal** | Re-run LORO with FE_Ensemble...
```

### 3. Updated TODO Section (Line ~1367)

**Changes**:
- Marked LOCO ensemble as complete
- Updated immediate priorities to focus on LORO validation
- Clarified that LOCO validation is done (Result 9)

**Modified text**:
- Changed "Re-run all ForwardEncoding-based models" to separate LOCO (done) from LORO (in progress)
- Added explicit reference to Result 9 for LOCO completion
- Noted server jobs are currently running for LORO

## Data Sources Used

1. **LOCO Ensemble Summary**: `/Users/jinilkim/.../results/LOCO_ENSEMBLE_SUMMARY_2026-02-23.md`
   - Group-level MAE comparisons (FE_Ensemble vs baseline)
   - Individual subject improvements
   - Ensemble variant failures (Ridge, GaussML)
   - Non-linear model performance

2. **LOCO Ensemble Results**: `/Users/jinilkim/.../results/loco_ensemble/{raw,procrustes,srm}/`
   - Config files confirmed 3 alignments tested
   - Models: ForwardEncoding, MLP, SVM, HybridMLP, HybridSVR
   - Note: FE_Ensemble results from separate directory (loco_decoding_comparison)

## Key Findings Documented

1. **Alignment necessity**: Raw space at chance (~90°) for all models
2. **Procrustes superiority**: Best performance in 7/8 group-ROI comparisons
3. **SRM viability**: Near-Procrustes performance (within 1-3°)
4. **Non-linear failure**: MLP/SVM 19-46° worse than ForwardEncoding
5. **Interpolation advantage**: ForwardEncoding +37° penalty in LOCO vs SVM's +98°
6. **FE_Ensemble confirmed**: −8.3° improvement in HC V1 (from Result 8)

## Cross-References Added

- Result 8 (FE_Ensemble improvements)
- Result 1 (LORO Systematic Results Matrix)
- Comparison of LORO vs LOCO performance degradation

## Status Tracking

- **LOCO ensemble**: ✅ DONE (Result 9)
- **LORO ensemble**: 🔄 In progress (server jobs running)
- **Group analyses**: ⏳ Pending LORO completion
- **Phase 3 filter**: ⏳ Awaiting decoder validation completion

---

*Generated: 2026-02-23*
*File modified: `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`*
