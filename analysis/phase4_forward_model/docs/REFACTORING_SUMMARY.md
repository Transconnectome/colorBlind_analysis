# Project Structure Refactoring Summary

> **Date**: 2026-03-13
> **Type**: Gradual refactoring (new analyses only)
> **Status**: ✅ Complete, ready for server execution

---

## Changes Made

### 1. Folder Structure (NEW)

```diff
future_phase1_forward_model/
├── scripts/
│   ├── (30+ existing files)                     # UNCHANGED ✓
+   ├── dimensionality/                          # NEW
+   │   ├── README.md
+   │   ├── analyze_eigenspectrum_decay.py
+   │   └── fit_meme_eigenspectrum.py
+   └── population_organization/                 # NEW
+       ├── README.md
+       └── map_voxel_color_preference.py
+
+├── sbatch/                                      # NEW
+   ├── run_dimensionality.sbatch                # Master (eigen + MEME)
+   ├── run_eigenspectrum_decay.sbatch           # Individual
+   ├── run_meme_estimator.sbatch                # Individual
+   └── run_voxel_preference.sbatch              # Individual
+
└── results/
+   ├── dimensionality/                          # NEW
+   │   ├── eigenspectrum/
+   │   └── meme/
+   └── population_organization/                 # NEW
+       └── voxel_preference/
```

### 2. Scripts Moved

| Old Location | New Location | Purpose |
|--------------|-------------|---------|
| `scripts/analyze_eigenspectrum_decay.py` | `scripts/dimensionality/` | Pospisil broken power law |
| `scripts/fit_meme_eigenspectrum.py` | `scripts/dimensionality/` | MEME k* estimator |
| `scripts/map_voxel_color_preference.py` | `scripts/population_organization/` | Bannert KDE preference |
| `run_*.sbatch` (3 files) | `sbatch/` | SLURM batch scripts |

### 3. Documentation Added

**New README files:**
- `scripts/dimensionality/README.md` — Research Q: Is CVD reduced-dimensional?
- `scripts/population_organization/README.md` — Research Q: Voxel-space intact?

**Updated existing docs:**
- `PLAN.md` — Section 13: Project Structure (gradual refactoring plan)
- `RESULTS.md` — Sections 11-14: Eigenspectrum, MEME, Voxel preference, Discussion
- `phase3_decoder_comparing/README.md` — Related Literature section
- `LITERATURE_INTEGRATION_PLAN.md` — Updated upload/run/download commands

### 4. Master Batch Script Created

**`sbatch/run_dimensionality.sbatch`** — Runs both analyses sequentially:
1. Eigenspectrum decay (α_early vs α_late)
2. MEME estimator (k* vs manual SRM k)

**Advantages:**
- Single job submission for both dimensionality analyses
- Sequential execution (MEME can use eigenspectrum results)
- Error handling (stops if eigenspectrum fails)
- Clear progress reporting

---

## Rationale

### Why Structured Folders?

**Problem**: 30+ scripts in flat `scripts/` directory → hard to find literature-driven analyses

**Solution**: Organize by **research question**, not chronology

| Folder | Research Question | Framework |
|--------|------------------|-----------|
| `dimensionality/` | Is CVD reduced-dimensional? | Pospisil & Pillow (2024) |
| `population_organization/` | Does reduction show in voxel space? | Bannert & Bartels (2025) |

### Why Gradual Refactoring?

**Safety**: Existing baseline scripts (30+ files) untouched → zero risk to working code

**Clarity**: New analyses clearly separated by purpose → easier to locate

**Migration path**: Future reorganization planned (move baseline to `0_baseline/`, failures to `archive/`)

---

## Research Question Hierarchy

```
Level 1: Dimensionality (RT-5 Resolution)
├── Q: Is CVD genuinely reduced-dimensional?
├── Evidence: Eigenspectrum α_CVD vs α_HC
├── Evidence: MEME k*_CVD vs k*_HC
└── Outcome: Biological (B) vs Methodological (A)

Level 2: Organization (Bannert Validation)
├── Q: Does dimensionality reduction manifest in voxel space?
├── Evidence: Voxel preference maps (HC vs CVD)
├── Outcome: Intact geometry vs Reorganization
└── Informs: Phase 2 filter architecture
```

**Connection**: If Level 1 shows biological dimensionality reduction BUT Level 2 shows intact voxel geometry → **clean dissociation** (information loss without cortical remapping)

---

## Execution (Server)

### Upload (Single Command)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase1_forward_model

scp -r scripts/dimensionality scripts/population_organization sbatch \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/
```

### Run (Recommended)

```bash
ssh haba6030@node3
cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

sbatch sbatch/run_dimensionality.sbatch      # Eigenspectrum + MEME (2h)
sbatch sbatch/run_voxel_preference.sbatch    # Voxel preference (1h)
```

### Download (Two Commands)

```bash
scp -r haba6030@node3:/scratch/.../results/dimensionality ./results/
scp -r haba6030@node3:/scratch/.../results/population_organization ./results/
```

---

## Validation Checklist

After download, verify:

### Dimensionality Results
- [ ] `results/dimensionality/eigenspectrum/eigenspectrum_results.json` exists
- [ ] `results/dimensionality/meme/meme_results.json` exists
- [ ] Eigenspectrum: α_early ≈ 0.5-0.7, α_late ≈ 1.0-1.5 (broken power law?)
- [ ] MEME: k* estimates per ROI, HC vs CVD comparison
- [ ] PDFs generated: `fig_eigenspectrum_decay.pdf`, `fig_meme_vs_pca.pdf`

### Population Organization Results
- [ ] `results/population_organization/voxel_preference/preference_results.json` exists
- [ ] Polar plots: 8 colors × 4 ROI showing % deviation from uniform
- [ ] Bar plots: voxel count distribution per color
- [ ] HC vs CVD p-values per color-ROI combination

### Documentation Updates
- [ ] Fill in "TO BE FILLED" sections in `RESULTS.md` (Sections 11-13)
- [ ] Update `PLAN.md` status (mark dimensionality analyses as complete)
- [ ] Create summary document with key findings for each analysis

---

## Next Steps After Completion

1. **Analyze results** against expected patterns (see LITERATURE_INTEGRATION_PLAN.md validation)
2. **Update RESULTS.md** with actual values (replace "TO BE FILLED")
3. **Resolve RT-5** based on MEME k* comparison
4. **Decide Phase 2 filter architecture** based on voxel preference findings
5. **Commit changes** with message: "Add dimensionality/organization analyses + structured folders"

---

## Files Modified

**Created** (11 files):
- `scripts/dimensionality/README.md`
- `scripts/dimensionality/analyze_eigenspectrum_decay.py`
- `scripts/dimensionality/fit_meme_eigenspectrum.py`
- `scripts/population_organization/README.md`
- `scripts/population_organization/map_voxel_color_preference.py`
- `sbatch/run_dimensionality.sbatch` (master)
- `sbatch/run_eigenspectrum_decay.sbatch`
- `sbatch/run_meme_estimator.sbatch`
- `sbatch/run_voxel_preference.sbatch`
- `REFACTORING_SUMMARY.md` (this file)
- `LITERATURE_INTEGRATION_PLAN.md`

**Modified** (3 files):
- `PLAN.md` — Added Section 13 (project structure)
- `RESULTS.md` — Added Sections 11-14 (literature integration)
- `../phase3_decoder_comparing/README.md` — Added Related Literature section

**Unchanged**:
- All 30+ existing baseline scripts in `scripts/`
- All existing result directories
- All existing sbatch files for baseline analyses

---

## Time Investment

- Script creation: ~3 hours (3 analysis scripts)
- Documentation: ~2 hours (READMEs, RESULTS.md updates)
- Refactoring: ~30 minutes (folder structure, path updates)

**Total**: ~5.5 hours

---

## Benefits

1. **Clarity**: Research questions immediately visible from folder names
2. **Safety**: Zero disruption to existing working code
3. **Scalability**: Easy to add future literature-driven analyses (e.g., Kuriki task-dependent)
4. **Maintainability**: Structured folders easier to navigate than flat 40+ file directory
5. **Documentation**: Each folder has README explaining purpose and expected outcomes

---

**Status**: Ready for server execution (2026-03-13)
