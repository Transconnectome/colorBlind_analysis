# FIR GLM Preprocessing Parameter Testing

## Overview

문헌 기반으로 선택된 6가지 전처리 조합을 체계적으로 테스트합니다.

---

## Preprocessing Configurations (Literature-based)

| Config | Name | Smoothing | High-pass | Drift | Rationale |
|--------|------|-----------|-----------|-------|-----------|
| **1** | baseline | 0 mm | None | linear | Current baseline - minimal preprocessing |
| **2** | spm_default | 4 mm | 1/128s | linear | SPM standard (Friston et al.) |
| **3** | conservative_mvpa | 6 mm | 1/128s | linear | Conservative MVPA (Op de Beeck 2010) |
| **4** | nosmooth_mvpa | 0 mm | 1/128s | linear | MVPA recommendation (Mumford et al. 2012) |
| **5** | poly_drift | 4 mm | None | poly2 | Polynomial drift alternative |
| **6** | minimal | 0 mm | None | None | Motion correction only |

### 문헌 근거:

**Smoothing:**
- Kriegeskorte et al. (2006): "Minimal or no smoothing for MVPA"
- Op de Beeck (2010): "0-6mm for high-resolution pattern analysis"

**High-pass filtering:**
- Mumford et al. (2012): "1/128s recommended for event-related designs"
- Lindquist et al. (2019): "High-pass may remove slow HRF components"

**Drift modeling:**
- FIR GLM: Drift removal is critical (no HRF shape assumption)
- Linear detrend (nilearn default) vs. Polynomial (order 2)

---

## What Gets Tested

**Parameters:**
- 6 preprocessing configs
- 3 strategies: flatten, average, delay4
- 2 PCA variants: with/without PCA (n=6)
- 4 subjects: 01, 02, 03, 04
- 4 ROIs: V1, V2, V3, hV4

**Total analyses:** 6 × 3 × 2 × 4 × 4 = **576 analyses**

**Per subject:** 6 × 3 × 2 × 4 = **144 analyses**

**Strategy selection rationale:**
- `flatten`: Best if temporal info matters (from previous testing)
- `average`: Simplest baseline
- `delay4`: Single timepoint at HRF peak (6.0s)

---

## Step 1: Upload Files

```bash
# From local machine
scp fir_per_run_preprocessing.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_preprocessing.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analyze_fir_preprocessing_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

---

## Step 2: Run Analysis

```bash
# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch run_fir_preprocessing.sbatch
```

**Expected runtime:**
- Per subject: ~1-1.5 hours (144 analyses)
- All 4 subjects (parallel): ~1-1.5 hours

---

## Step 3: Monitor Progress

```bash
# Check job status
squeue -u haba6030

# Watch output
tail -f logs/fir_preproc_*.out

# Check for errors
tail -f logs/fir_preproc_*.err
```

---

## Step 4: Analyze Results

```bash
# Check timestamp
ls derivatives/fir_preprocessing/sub-01/

# Run analysis (replace with your timestamp)
python analyze_fir_preprocessing_results.py --timestamp 20250120_143022
```

**Output:**
```
derivatives/fir_preprocessing/summary/TIMESTAMP/
├── all_results.csv                      # Full results table
├── best_per_strategy.csv                # Best config per strategy
├── parameter_effects.txt                # Statistical summary
├── config_comparison_heatmap.png        # Config × ROI × Strategy
├── parameter_effects.png                # Individual parameter effects
└── strategy_config_interaction.png      # Strategy × Config interaction
```

---

## Step 5: Download Results

```bash
# From local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/fir_preprocessing/summary/TIMESTAMP ./fir_preprocessing_results/
```

---

## What to Look For

### 1. Best Overall Config
- Which config gives highest accuracy?
- Is it consistent across subjects/ROIs?

### 2. Smoothing Effect
- Does smoothing help or hurt?
- 0 mm (no smoothing) vs. 4-6 mm
- Expected: Minimal smoothing better for MVPA

### 3. High-pass Filtering Effect
- None vs. 1/128s
- Does filtering improve drift removal?
- Does it remove useful slow HRF components?

### 4. Drift Model Effect
- Linear detrend vs. Polynomial (order 2) vs. None
- Critical for FIR GLM
- Expected: Some drift removal necessary

### 5. PCA Interaction
- Does PCA help with certain preprocessing?
- PCA might be more helpful with noisy (minimal preprocessing) data

### 6. Strategy × Config Interaction
- Do different strategies benefit from different preprocessing?
- E.g., `flatten` might need less smoothing than `average`

---

## Expected Findings (Hypotheses)

Based on literature:

1. **Smoothing:**
   - Minimal (0-4mm) likely best for MVPA
   - Too much smoothing (6mm) may blur fine-grained patterns

2. **High-pass filtering:**
   - 1/128s should help remove slow drift
   - But might hurt if it removes slow HRF components

3. **Best config candidates:**
   - Config 1 (baseline) or Config 4 (nosmooth_mvpa)
   - Both have no/minimal smoothing
   - Config 4 adds high-pass for drift removal

4. **Worst config:**
   - Config 6 (minimal) - no drift removal at all
   - FIR GLM very sensitive to drift

---

## Troubleshooting

### Job fails
```bash
# Check error log
cat logs/fir_preproc_JOBID_ARRAYID.err

# Common issues:
# - ROI mask not found
# - Memory (should be OK with 16G)
# - Smoothing with nilearn (check version)
```

### Test single analysis
```bash
conda activate nilearn

python fir_per_run_preprocessing.py \
    --subject 01 \
    --roi V1 \
    --strategy flatten \
    --config 2 \
    --timestamp test_run
```

### No results in analysis
```bash
# Check what was created
find derivatives/fir_preprocessing -name "summary.json" | head

# Check timestamp
ls derivatives/fir_preprocessing/sub-01/
```

---

## Next Steps After Results

1. **Identify best config:**
   - Use best config for final analysis pipeline

2. **Compare with baseline:**
   - Is there significant improvement over Config 1?
   - Cost-benefit: Is added complexity worth it?

3. **ROI-specific tuning:**
   - Do different ROIs need different preprocessing?
   - E.g., V1 vs. hV4

4. **Update main pipeline:**
   - Incorporate best preprocessing into final FIR reconstruction pipeline

---

## File Structure

```
derivatives/fir_preprocessing/
├── sub-01/
│   ├── TIMESTAMP_V1_flatten_cfg1/
│   ├── TIMESTAMP_V1_flatten_cfg1_pca6/
│   ├── TIMESTAMP_V1_flatten_cfg2/
│   ├── ... (144 total per subject)
│   └── TIMESTAMP_hV4_delay4_cfg6_pca6/
├── sub-02/
├── sub-03/
├── sub-04/
└── summary/
    └── TIMESTAMP/
        ├── all_results.csv
        ├── best_per_strategy.csv
        ├── parameter_effects.txt
        └── *.png (visualizations)
```

---

## References

1. **Kriegeskorte et al. (2006).** Information-based functional brain mapping. *PNAS*, 103(10), 3863-3868.
   - MVPA methodology, minimal smoothing

2. **Op de Beeck (2010).** Against hyperacuity in brain reading. *Trends in Cognitive Sciences*, 14(5), 196-205.
   - Smoothing recommendations for pattern analysis

3. **Mumford et al. (2012).** Deconvolving BOLD activation in event-related designs. *NeuroImage*, 59(3), 2636-2643.
   - FIR GLM methodology, preprocessing recommendations

4. **Lindquist et al. (2019).** Modeling the hemodynamic response function. *NeuroImage*, 200, 521-539.
   - HRF modeling, filtering effects

5. **Friston et al. (SPM)** - Standard SPM preprocessing pipeline (4mm smoothing, 128s high-pass)

---

*See also: `logs/session_20250120_fir_only.md` for FIR-only methodology*
