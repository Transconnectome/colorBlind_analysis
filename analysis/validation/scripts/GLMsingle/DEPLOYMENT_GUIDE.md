# GLMsingle + Whitening Deployment Guide

**Created**: 2026-02-05
**Status**: Ready for server deployment

---

## Quick Start

### 1. Upload Code to Server

```bash
# On local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Upload GLMsingle directory (efficient single command)
scp -r GLMsingle haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

### 2. Setup on Server

```bash
# SSH to server
ssh haba6030@node2

# Navigate to directory
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/GLMsingle

# Create logs directory
mkdir -p logs

# Make scripts executable
chmod +x *.py
chmod +x sbatch/*.sbatch

# Activate environment
conda activate nilearn

# Install GLMsingle (MUST install from GitHub, not PyPI)
pip install git+https://github.com/cvnlab/GLMsingle.git

# Verify installation
python -c "from glmsingle.glmsingle import GLM_single; print('✓ GLMsingle installed')"
```

### 3. Interactive Test (Single Subject-ROI)

```bash
# Test Step 1: GLMsingle with residuals
python 01_glmsingle_with_residuals.py --subject 01 --roi V1 --config full

# Check outputs
ls -lh results/*/sub-01_V1/
# Expected: betas_single_trial.npy, residuals_1st_level.npy, R2_voxelwise.npy

# Test Step 2: Noise covariance
python 02_estimate_noise_covariance.py --subject 01 --roi V1

# Check outputs
ls -lh results/*/sub-01_V1/
# Expected: noise_covariance.npy, whitening_matrix.npy

# Test Step 3: Whitened amplitudes
python 03_glmsingle_whitened_amplitudes.py --subject 01 --roi V1

# Check outputs
ls -lh results/*/sub-01_V1/
# Expected: amplitudes_z_glmsingle.npy, amplitudes_z_whitened.npy

# Test Step 4: Evaluation
python 04_evaluate_glmsingle_vs_fir.py --subject 01 --roi V1 --save-figures

# Check results
cat results/*/sub-01_V1/comparison_vs_fir.json
```

### 4. Monitor Resource Usage

```bash
# Profile Step 1 (most expensive)
/usr/bin/time -v python 01_glmsingle_with_residuals.py --subject 01 --roi V1 > profile.log 2>&1

# Check profile
grep "Maximum resident set size" profile.log  # Peak memory
grep "Elapsed (wall clock)" profile.log        # Runtime
grep "Percent of CPU" profile.log              # CPU utilization

# Expected for V1 (~400 voxels):
# - Peak memory: 18-24 GB
# - Runtime: 25-35 minutes
# - CPU: 350-400% (4 cores)
```

### 5. Launch Pilot Test

```bash
# Edit paths in sbatch script if needed
nano sbatch/run_glmsingle_pilot.sbatch

# Submit pilot (12 jobs: 4 ROIs × 3 methods)
sbatch sbatch/run_glmsingle_pilot.sbatch

# Monitor jobs
squeue -u haba6030
watch -n 10 'squeue -u haba6030'

# Check logs (live)
tail -f logs/glmsingle_pilot_*.out

# Check for errors
grep -i "error\|fail" logs/glmsingle_pilot_*.err
```

### 6. Launch Full Analysis (After Pilot Success)

```bash
# Submit full analysis (40 jobs: 10 subjects × 4 ROIs)
sbatch sbatch/run_glmsingle_full.sbatch

# Expected runtime: 6-8 hours (6 concurrent jobs)
# Monitor progress
watch -n 30 'squeue -u haba6030 | tail -20'

# Check completed jobs
ls -d /scratch/connectome/haba6030/colorBlind/derivatives/GLMsingle_full/*/
```

---

## Verification Checklist

### Before Deployment

- [ ] All Python scripts uploaded to server
- [ ] Utils module uploaded (glmsingle_interface.py, etc.)
- [ ] SLURM scripts uploaded (run_glmsingle_pilot.sbatch, run_glmsingle_full.sbatch)
- [ ] Logs directory created
- [ ] GLMsingle package installed (`pip install glmsingle`)
- [ ] Paths verified in scripts (EVENT_DIR, FMRIPREP_DIR, DERIVATIVES_DIR)

### After Interactive Test

- [ ] Step 1 produces betas + residuals
- [ ] Residuals have mean ≈ 0, shape (6, 240, n_voxels)
- [ ] Step 2 produces covariance + whitening matrix
- [ ] Shrinkage parameter 0.05-0.30 (in whitening_metadata.json)
- [ ] Correlation reduction > 20% (in whitening_metadata.json)
- [ ] Step 3 produces GLMsingle + whitened amplitudes
- [ ] Step 4 shows improvement > 5% over baseline
- [ ] Memory usage < 24 GB peak
- [ ] Runtime < 60 minutes total

### After Pilot Test (12 jobs)

- [ ] All 12 jobs completed successfully
- [ ] No OOM errors in logs
- [ ] Each subject-ROI directory contains all expected files
- [ ] comparison_vs_fir.json shows improvements
- [ ] comparison_figure.png generated
- [ ] Total storage < 7 GB

### After Full Analysis (40 jobs)

- [ ] All 40 jobs completed successfully
- [ ] Total storage ~22 GB
- [ ] Aggregate results show consistent improvements
- [ ] Ready to integrate with Phase 2 Procrustes

---

## Expected File Sizes

**Per subject-ROI**:
```
betas_single_trial.npy         ~70 MB  (6, 288, 400) float32
residuals_1st_level.npy       ~460 MB  (6, 240, 400) float32
noise_covariance.npy            ~1 MB  (400, 400) float64
whitening_matrix.npy            ~1 MB  (400, 400) float64
amplitudes_z_glmsingle.npy     ~20 KB  (6, 8, 400) float32
amplitudes_z_whitened.npy      ~20 KB  (6, 8, 400) float32
R2_voxelwise.npy                ~2 KB  (400,) float32
glmsingle_diagnostics.json      ~1 KB
whitening_metadata.json         ~1 KB
comparison_vs_fir.json          ~1 KB
comparison_figure.png          ~50 KB

Total per subject-ROI:        ~530 MB
```

**Total for 40 pairs**: ~21 GB

---

## Troubleshooting

### Issue: "GLMsingle not installed"

**Important**: GLMsingle is NOT on PyPI. Must install from GitHub.

```bash
conda activate nilearn

# CORRECT: Install from GitHub
pip install git+https://github.com/cvnlab/GLMsingle.git

# WRONG: This will fail
# pip install glmsingle

# Verify installation
python -c "from glmsingle.glmsingle import GLM_single; print('✓ GLMsingle installed')"

# If git is not available, install it first:
# conda install git
```

### Issue: "Event file not found"

Check paths in script:
```python
EVENT_DIR = Path('/storage/connectome/haba6030/bids_editted')
```

Verify files exist:
```bash
ls /storage/connectome/haba6030/bids_editted/sub-01/func/*events.tsv
```

### Issue: "BOLD file not found"

Check paths:
```python
FMRIPREP_DIR = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')
```

Verify files exist:
```bash
ls /storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-01/func/*bold.nii.gz
```

### Issue: "Invalid QoS" or "Invalid partition"

Edit SLURM script:
```bash
#SBATCH --qos=shared              # For node2
#SBATCH --nodelist=node2
# Do NOT include --partition
```

### Issue: "Memory error / OOM"

Reduce concurrent jobs:
```bash
#SBATCH --array=1-40%3  # Instead of %6
```

Or increase memory:
```bash
#SBATCH --mem=32G  # Instead of 24G
```

Or use block-diagonal whitening:
```bash
python 02_estimate_noise_covariance.py --subject 01 --roi V1 --block-size 100
```

### Issue: "No improvement over baseline"

Possible causes:
1. **FIR baseline already very good**: Check baseline R²
2. **ROI too small**: Need >100 voxels for reliable covariance
3. **Low SNR data**: Check R² from Step 1
4. **Wrong ROI mask**: Verify mask covers V1/V2/V3/V4

Check diagnostics:
```bash
# GLMsingle quality
cat results/*/sub-01_V1/glmsingle_diagnostics.json | grep r2_mean

# Whitening quality
cat results/*/sub-01_V1/whitening_metadata.json | grep correlation_reduction

# Comparison
cat results/*/sub-01_V1/comparison_vs_fir.json
```

---

## Performance Optimization

### CPU Optimization

GLMsingle is CPU-intensive. Use:
```bash
#SBATCH --cpus-per-task=4  # 4 cores
#SBATCH --mem=24G          # 6 GB per core
```

### Memory Optimization

For large ROIs (>1000 voxels), use block-diagonal:
```bash
python 02_estimate_noise_covariance.py --block-size 100
```

### Storage Optimization

Don't save whitened single-trial betas (large):
```bash
# Default: no --save-whitened-betas flag
python 03_glmsingle_whitened_amplitudes.py --subject 01 --roi V1
# Saves only amplitudes (~20 KB) not betas (~70 MB)
```

After analysis complete, can delete residuals:
```bash
# Free ~460 MB per subject-ROI
find results/ -name "residuals_1st_level.npy" -delete
```

---

## Integration with Existing Pipeline

### Replace FIR Baseline

Once validated (improvement >50%), replace FIR calls:

**Old** (phase1):
```python
amplitudes = run_fir_reconstruction(subject, roi)
```

**New** (GLMsingle + Whitening):
```python
amplitudes = load_glmsingle_whitened_amplitudes(subject, roi)
```

### Phase 2 Procrustes

Compatible format: `(n_runs, n_colors, n_voxels)`

```python
# Load whitened amplitudes
amps_whitened = np.load(f'results/{timestamp}/sub-{ID}_{ROI}/amplitudes_z_whitened.npy')

# Use in Procrustes
procrustes_results = run_procrustes_analysis(amps_whitened, ...)
```

### Phase 3 Filter Learning

Higher quality input → Better filter learning:

```python
# CVD subject
amps_cvd_whitened = load_glmsingle_whitened_amplitudes('08', 'V1')

# HC target
amps_hc_whitened = load_glmsingle_whitened_amplitudes('01', 'V1')

# Train filter with higher quality data
filter_learned = train_cvd_filter(amps_cvd_whitened, amps_hc_whitened)
```

---

## Next Steps After Deployment

1. **Validate improvements** (Step 4 results)
   - If total improvement >50%: ✅✅ Adopt for all analyses
   - If improvement 30-50%: ✅ Adopt with caution
   - If improvement <30%: ⚠️ Review diagnostics

2. **Aggregate results** across all 40 pairs
   ```bash
   python aggregate_glmsingle_results.py  # TODO: Create this script
   ```

3. **Integrate with Phase 2** (Procrustes)
   - Update baseline to use whitened amplitudes
   - Re-run CVD vs HC comparison
   - Expected: Higher disparity due to better signal

4. **Integrate with Future Phase 3** (Filter learning)
   - Higher quality CVD representations
   - Better HC target space
   - Improved filter optimization

5. **Publish methodology** (if improvement >100%)
   - Document combined GLMsingle + Whitening approach
   - Share code on GitHub
   - Write methods section for paper

---

## Contact & Support

**Local development**: `/Users/jinilkim/.../GLMsingle/`
**Server deployment**: `/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/GLMsingle/`

For issues:
1. Check logs: `logs/glmsingle_*.{out,err}`
2. Check diagnostics: `results/*/sub-{ID}_{ROI}/*.json`
3. Review README.md for troubleshooting
4. Contact: haba6030@node2
