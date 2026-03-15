# Literature Integration & Eigenspectrum Analysis — Implementation Plan

> **Created**: 2026-03-13
> **Status**: Ready for server execution
> **Papers**: Bannert & Bartels (2025), Kuriki et al. (2025), Pospisil & Pillow (2024)

---

## Executive Summary

This plan integrates 3 recent papers into the colorblind fMRI project through:
1. **New analyses** (eigenspectrum decay, MEME dimensionality, voxel preference maps)
2. **Documentation updates** (literature citations in Phase 3 README, Future Phase 1 RESULTS)

**Status:**
- ✅ **Scripts created**: 3 analysis scripts + 3 sbatch files
- ✅ **Documentation updated**: Phase 3 README.md, Future Phase 1 RESULTS.md
- ⏳ **Server execution**: Awaiting SLURM jobs

---

## Files Created

### Analysis Scripts

1. **`scripts/analyze_eigenspectrum_decay.py`**
   - Computes PCA eigenvalues from Procrustes-aligned data
   - Fits broken power law (α_early vs α_late)
   - Compares HC vs CVD eigenvalue decay
   - Output: `results/eigenspectrum_decay/`

2. **`scripts/fit_meme_eigenspectrum.py`**
   - Implements eigenmoment matching estimator (Li et al. 2014)
   - Estimates unbiased dimensionality k* per ROI
   - Compares to manual SRM k values (V1=4, V2=4, V3=3, hV4=3)
   - Output: `results/meme_dimensionality/`

3. **`scripts/map_voxel_color_preference.py`**
   - KDE+softmax voxel preference mapping (Bannert & Bartels 2025)
   - Identifies which voxels prefer which colors
   - Tests HC vs CVD preference distribution differences
   - Output: `results/voxel_preference_maps/`

### SLURM Batch Files

1. **`run_eigenspectrum_decay.sbatch`**
   - Node2, 4 CPU, 16GB, 1 hour
   - Runs eigenspectrum decay analysis

2. **`run_meme_estimator.sbatch`**
   - Node2, 4 CPU, 16GB, 1 hour
   - Runs MEME dimensionality estimator

3. **`run_voxel_preference.sbatch`**
   - Node2, 4 CPU, 16GB, 1 hour
   - Runs voxel color preference mapping

### Documentation Updated

1. **`analysis/phase3_decoder_comparing/README.md`**
   - Added "Related Literature" section (after Discussion, before Limitations)
   - Integrated Bannert & Bartels (2025) — SRM cross-subject generalization
   - Integrated Kuriki et al. (2025) — task-dependent representation
   - Updated References section

2. **`analysis/future_phase1_forward_model/RESULTS.md`**
   - Added Section 11: Eigenspectrum Geometry (Pospisil & Pillow 2024)
   - Added Section 12: Unbiased Dimensionality Estimation (MEME)
   - Added Section 13: Voxel Color Preference Maps (Bannert & Bartels 2025)
   - Added Section 14: Discussion — Literature Integration
   - Connected new analyses to existing findings (V1/V2 LOCO null, RT-5 dimensionality question)

---

## Execution Steps

### Step 1: Upload Scripts to Server

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase1_forward_model

# Upload structured folders (dimensionality + population_organization + sbatch)
scp -r scripts/dimensionality scripts/population_organization sbatch \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/
```

### Step 2: Run Jobs on Server

```bash
# SSH to server
ssh haba6030@node3

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# Create logs directory if needed
mkdir -p logs

# Option A: Run all dimensionality analyses sequentially (recommended)
sbatch sbatch/run_dimensionality.sbatch      # Eigenspectrum + MEME (2 hours)
sbatch sbatch/run_voxel_preference.sbatch    # Voxel preference (1 hour)

# Option B: Run individually (if needed)
# sbatch sbatch/run_eigenspectrum_decay.sbatch
# sbatch sbatch/run_meme_estimator.sbatch
# sbatch sbatch/run_voxel_preference.sbatch

# Monitor jobs
squeue -u haba6030

# Check logs after completion
tail logs/dimensionality_*.out          # Master dimensionality log
tail logs/voxel_preference_*.out        # Voxel preference log
```

### Step 3: Download Results

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase1_forward_model

# Download structured result directories (2 commands)
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/results/dimensionality ./results/
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/results/population_organization ./results/
```

### Step 4: Update RESULTS.md with Actual Data

After downloading results, fill in the "TO BE FILLED" sections in `RESULTS.md`:
- Section 11: Eigenspectrum Geometry → Add actual α_early, α_late, p-values
- Section 12: MEME → Add actual k* estimates vs SRM k comparison
- Section 13: Voxel Preference → Add actual preference distribution findings

---

## Expected Outcomes

### Scientific Contributions

1. **First quantitative eigenspectrum comparison in HC vs CVD color representation**
   - If CVD shows steeper α → supports "reduced dimensionality" hypothesis
   - If α_early ≈ α_late → challenges Pospisil's broken power law universality in 8-color task

2. **Unbiased dimensionality estimates via MEME**
   - Validates or challenges current SRM k=3-4 choice
   - Resolves RT-5 vulnerability: K-sensitivity as (A) bias-variance tradeoff vs (B) biological dimensionality reduction

3. **Direct voxel-level color preference maps**
   - Tests cortical reorganization hypothesis (shifted preference peaks in CVD?)
   - Validates stimulus-level vs voxel-level distortion distinction

4. **Comprehensive literature integration**
   - Connects isolated findings to broader color neuroscience
   - Strengthens Discussion with mechanistic explanations (Kuriki task-dependent, Pospisil broken power law)

### Publication Figures

- **Figure 5**: Eigenspectrum decay (log-log, HC vs CVD, 4 ROI)
- **Figure 6**: MEME vs PCA dimensionality estimates
- **Figure 7**: Voxel color preference maps (polar KDE, 8 colors × 4 ROI)
- **Supplementary Table**: Literature comparison (our findings vs Bannert/Kuriki/Pospisil)

---

## Validation Checklist

After results are downloaded:

### Eigenspectrum Decay
- [ ] α_early ≈ 0.5-0.7 (consistent with Pospisil)
- [ ] α_late ≈ 1.0-1.5 (steeper than early)
- [ ] hV4 has more eigenvalues above noise floor than V1
- [ ] HC vs CVD comparison: does CVD show steeper decay?

### MEME Estimator
- [ ] MEME k* for hV4 ≈ 3-5 (validates SRM k=3)
- [ ] CVD k* ≤ HC k* (reduced dimensionality hypothesis)
- [ ] MEME eigenvalues > PCA eigenvalues (debiasing works)

### Voxel Preference Maps
- [ ] HC maps show distinct spatial clustering per color
- [ ] CVD maps: shifted peaks (red→orange for deutan) OR similar peaks (geometry intact)
- [ ] Polar plots show % deviation from uniform (12.5% baseline)

---

## Troubleshooting

### If eigenspectrum_decay fails
- Check if sub-07 hV4 (only 16 voxels) causes matrix errors
- Reduce `--n_late` from 50 to 30 if n_voxels < 50

### If MEME estimator fails
- High-dimensional regime (γ > 1) may cause instability
- Check Marchenko-Pastur correction factor validity

### If voxel_preference fails
- KDE bandwidth may be too large/small for sparse voxel counts
- Try `--bandwidth_method silverman` instead of scott

---

## Time Estimate

- **Upload**: 2 minutes
- **SLURM execution**: ~30 minutes per job (parallel)
- **Download**: 5 minutes
- **Results analysis**: 30 minutes (check figures, extract key numbers)
- **RESULTS.md update**: 30 minutes (fill in TO BE FILLED sections)

**Total**: ~2 hours from start to finish

---

## Next Steps After Completion

1. **Validate findings** against expected patterns (checklist above)
2. **Update RESULTS.md** with actual numbers and figures
3. **Commit to git** with message: "Add eigenspectrum/MEME/voxel preference analyses + literature integration"
4. **Cross-reference** with Phase 2/3 findings for consistency
5. **Prepare figures** for publication (polish eigenspectrum log-log plots, MEME overlay, polar preference maps)

---

## Questions to Answer

After analysis completion:

1. **Does CVD show reduced dimensionality?** (MEME k*_CVD < k*_HC?)
2. **Is SRM k=3-4 optimal?** (MEME k* ≈ manual k?)
3. **Does eigenspectrum show broken power law?** (α_early < α_late?)
4. **Do CVD voxel preferences shift?** (cortical reorganization vs intact geometry?)
5. **Does LOCO null (~0.10-0.13) come from late modes?** (eigenspectrum analysis)

These answers directly inform:
- **Phase 2 filter design** (dimensionality of stimulus transformation)
- **RT-5 neutralization** (K-sensitivity biological vs methodological)
- **Discussion framing** (discrimination vs interpolation dissociation mechanism)

---

**Status**: Ready for execution — proceed to Step 1 (upload scripts)
