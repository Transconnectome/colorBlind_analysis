# File Cleanup Recommendations — 2026-02-19

**Status**: Preliminary scan
**Total potential cleanup**: ~806 MB + 62 cache directories + consolidation opportunities

---

## Priority 1: Large Archived Data (HIGH — 806 MB)

### 1.1 Phase 1 Past Results (779 MB) ⚠️ **LARGEST**
**Path**: `analysis/phase1_preprocess_decoding/results/past/`

**Content**: Grid search factorial results from early preprocessing trials

**Recommendation**:
- **Action**: Archive to external storage or compress to `.tar.gz`
- **Justification**: Phase 1 validations complete (11/11 done); current pipeline uses `full_dataset_C010` (method3_header_mi)
- **Risk**: Low — results superseded by current C010 dataset
- **Commands**:
  ```bash
  # Option 1: Compress in place
  cd analysis/phase1_preprocess_decoding/results
  tar -czf past_grid_factorial_archive_2026-02-19.tar.gz past/
  # Verify integrity before removal
  tar -tzf past_grid_factorial_archive_2026-02-19.tar.gz > /dev/null && echo "Archive OK"

  # Option 2: Move to external archive location (recommended)
  # Define ARCHIVE_DIR first, then:
  # mv analysis/phase1_preprocess_decoding/results/past/ $ARCHIVE_DIR/
  ```

### 1.2 Phase 2 SRM pastData (21 MB)
**Path**: `analysis/phase2_SRM_across_between/results/pastData/`

**Content**: Outdated SRM alignment results (before LOO-consistent analysis)

**Recommendation**:
- **Action**: Archive or remove
- **Justification**: Current results in `results/loo_consistent/` supersede these (HC-only SRM + LOO refs)
- **Risk**: Low — methodology improved (three bias fixes applied)
- **Commands**:
  ```bash
  cd analysis/phase2_SRM_across_between/results
  tar -czf pastData_archive_2026-02-19.tar.gz pastData/
  ```

### 1.3 Validation pastData (5.5 MB)
**Path**: `analysis/validation/results/pastData/`

**Content**: Old noise ceiling and validation runs

**Recommendation**:
- **Action**: Archive
- **Justification**: Validations re-run with sub-01 (2026-02-17); 39 valid tests now canonical
- **Risk**: Low — superseded by current validation results
- **Commands**:
  ```bash
  cd analysis/validation/results
  tar -czf pastData_validation_archive_2026-02-19.tar.gz pastData/
  ```

### 1.4 Phase 1 Scripts Past (196 KB)
**Path**: `analysis/phase1_preprocess_decoding/scripts/past/`

**Content**: Deprecated preprocessing scripts

**Recommendation**:
- **Action**: Keep but document
- **Justification**: Small size; useful for reference if method questions arise
- **Risk**: Very low
- **Action**: Add README.md explaining deprecation

---

## Priority 2: Python Cache Files (MEDIUM — 62 items)

**Pattern**: `__pycache__/` directories, `*.pyc` files

**Recommendation**:
- **Action**: Remove all (regenerated automatically)
- **Justification**: No version control value; bloats repository
- **Risk**: None — Python recreates on next import
- **Commands**:
  ```bash
  # Preview
  find analysis -type d -name "__pycache__" -o -name "*.pyc"

  # Remove
  find analysis -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
  find analysis -type f -name "*.pyc" -delete
  ```

**Git Ignore**: Verify `.gitignore` includes:
```
__pycache__/
*.pyc
*.pyo
*.pyd
```

---

## Priority 3: Duplicate/Redundant Summary Files (LOW — Documentation Overlap)

### 3.1 Phase 2 SRM Summaries
**Location**: `analysis/phase2_SRM_across_between/`

**Files**:
- `ALL_ROIS_RESULTS_SUMMARY.md` (12 KB)
- `SRM_ANALYSIS_SUMMARY.md` (12 KB)
- `C010_BETWEEN_SUBJECT_RESULTS.md` (10 KB)
- `README.md` (29 KB)

**Analysis**:
```bash
# Check content similarity
diff ALL_ROIS_RESULTS_SUMMARY.md SRM_ANALYSIS_SUMMARY.md
```

**Recommendation**:
- **Action**: Consolidate into single `PHASE2_SRM_RESULTS.md` if substantial overlap exists
- **Justification**: Avoid maintaining multiple similar documents
- **Risk**: Low — can merge content
- **Decision**: DEFER to manual review (need to check if files serve distinct purposes)

### 3.2 Filter Pre-Validation Summaries
**Location**: `analysis/future_phase3_filter_optimization/pre_validation/`

**Files** (all created 2026-02-19):
- `VALIDATION_RESULTS_SUMMARY.md`
- `FDR_CORRECTION_SUMMARY.md`
- `CRITICISM_2_ANALYSIS.md`
- `UPDATED_FILTER_STRATEGY.md`
- `PROJECT_STATUS_2026-02-19.md`
- `QUICK_REFERENCE.md`

**Recommendation**:
- **Action**: Keep all (distinct purposes)
- **Justification**:
  - VALIDATION_RESULTS_SUMMARY = high-level overview
  - FDR_CORRECTION_SUMMARY = method-specific detail
  - CRITICISM_2_ANALYSIS = SRM circularity analysis
  - UPDATED_FILTER_STRATEGY = filter design specification
  - PROJECT_STATUS_2026-02-19 = bilingual comprehensive status
  - QUICK_REFERENCE = lookup table
- **Risk**: None — complementary, not redundant

---

## Priority 4: Figure Files (INFO ONLY — 3,017 files)

**Total**: 3,017 `.png`, `.jpg`, `.pdf` files

**Recommendation**:
- **Action**: No immediate cleanup
- **Justification**: Most are analysis results (RDM plots, z-score matrices, validation figures)
- **Future action**: Consider:
  1. Move publication figures to dedicated `manuscript/figures/` directory
  2. Archive intermediate debugging plots (e.g., per-run RDMs)
  3. Compress large PDFs if space becomes issue
- **Risk**: Low — figures are git-ignored if large

---

## Priority 5: Results Directory Proliferation (24 directories)

**Pattern**: 24 `results/` subdirectories across analysis phases

**Examples**:
- `analysis/phase1_preprocess_decoding/results/`
- `analysis/phase2_SRM_across_between/results/`
- `analysis/phase2_decoder_comparing/results/`
- `analysis/validation/results/`
- `analysis/future_phase3_filter_optimization/pre_validation/results/`

**Recommendation**:
- **Action**: Document structure, no consolidation
- **Justification**: Phase-specific results are appropriately isolated
- **Future**: Consider top-level `results/` symlink tree for cross-phase navigation
- **Risk**: None — current structure follows phase organization

---

## Recommended Actions (Ordered by Impact)

### Immediate (Safe, High-Reward)
1. **Remove Python cache** (62 items, no risk)
   ```bash
   find analysis -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find analysis -type f -name "*.pyc" -delete
   ```

2. **Compress phase1 past results** (779 MB → ~50-100 MB estimated)
   ```bash
   cd analysis/phase1_preprocess_decoding/results
   tar -czf past_grid_factorial_archive_2026-02-19.tar.gz past/
   # After verification:
   # rm -rf past/
   ```

### Short-term (Review Required)
3. **Review phase2 SRM summary overlap**
   - Manually compare `ALL_ROIS_RESULTS_SUMMARY.md` vs `SRM_ANALYSIS_SUMMARY.md`
   - Merge if >80% content overlap

4. **Archive validation pastData** (5.5 MB)
   ```bash
   cd analysis/validation/results
   tar -czf pastData_validation_archive_2026-02-19.tar.gz pastData/
   ```

5. **Archive phase2 SRM pastData** (21 MB)
   ```bash
   cd analysis/phase2_SRM_across_between/results
   tar -czf pastData_archive_2026-02-19.tar.gz pastData/
   ```

### Long-term (Optional)
6. **Create manuscript figures directory**
   ```bash
   mkdir -p manuscript/figures
   # Selectively copy publication-ready figures
   ```

7. **Document deprecated scripts**
   - Add `analysis/phase1_preprocess_decoding/scripts/past/README.md`
   - Explain why scripts superseded

---

## Estimated Space Savings

| Action | Size Reduction | Risk | Effort |
|--------|---------------|------|--------|
| Remove Python cache | ~10-50 MB | None | 1 min |
| Compress phase1 past | ~650-700 MB | Low | 5 min |
| Archive validation pastData | ~5 MB | Low | 2 min |
| Archive phase2 SRM pastData | ~20 MB | Low | 2 min |
| **Total** | **~685-775 MB** | **Low** | **10 min** |

---

## Git Repository Impact

**Current status**: `.gitignore` should already exclude:
- Large data files (`*.nii.gz`, `*.npy`)
- Results directories (`derivatives/`, `results/full_dataset*`)
- Cache files (`__pycache__/`)

**Verify**:
```bash
git status --ignored
```

**Action**: No git changes needed (all cleanup targets already ignored or in tracked docs)

---

## Next Steps

1. ✅ **Done**: Daily summary created (`results/daily/2026-02-19.md`)
2. ✅ **Done**: Cleanup scan completed (this document)
3. ⏳ **Pending**: User approval for archive/removal actions
4. ⏳ **Pending**: Execute priority 1 cleanup (Python cache + phase1 archive)

---

*Generated as part of daily-checkin cleanup analysis*
