# Dimensionality Analysis (RT-5 Resolution)

> **Research Question**: Is CVD genuinely reduced-dimensional, or is K-sensitivity a model artifact?
> **Framework**: Pospisil & Pillow (2024) eigenspectrum geometry + MEME estimator

---

## Analyses

### 1. Eigenspectrum Decay (`analyze_eigenspectrum_decay.py`)

**Purpose**: Test whether signal eigenvalues follow broken power law (α_early ≠ α_late)

**Method**:
- Compute PCA eigenvalues from Procrustes-aligned data (48 samples × n_voxels)
- Fit power law λᵢ = c · i^(-α) to early modes (i=1-10) vs late modes (i=10-50)
- Compare HC vs CVD: Welch t-test for α_early, α_late

**Expected Patterns** (Pospisil 2024):
- α_early ≈ 0.5-0.7 (shallow decay, dominant modes)
- α_late ≈ 1.0-1.5 (steeper decay, noise-dominated)
- If CVD dimensionality reduced: α_CVD > α_HC

**Output**: `results/dimensionality/eigenspectrum/`
- `eigenspectrum_results.json` — α values, p-values per ROI
- `fig_eigenspectrum_decay.pdf` — 2×4 subplot (HC/CVD × V1/V2/V3/hV4)

### 2. MEME Estimator (`fit_meme_eigenspectrum.py`)

**Purpose**: Estimate unbiased dimensionality k* to validate manual SRM k=3-4

**Method**:
- Compute sample eigenvalues (biased in high-dimensional regime)
- Apply Marchenko-Pastur correction for downward bias
- Eigenmoment matching to recover true signal eigenspectrum
- Estimate rank k* = #{eigenvalues > noise floor}

**Validation**:
- Compare k* to manual SRM k (V1=4, V2=4, V3=3, hV4=3)
- If MEME k* ≈ manual k → current choice optimal
- If MEME k* < manual k → SRM over-parameterized

**Output**: `results/dimensionality/meme/`
- `meme_results.json` — k* estimates, HC vs CVD comparison
- `fig_meme_vs_pca.pdf` — MEME (debiased) vs PCA (biased) eigenvalues

---

## Expected Outcomes

| Scenario | MEME | Eigenspectrum | Interpretation | RT-5 Resolution |
|----------|------|---------------|----------------|-----------------|
| **Biological** | k*_CVD < k*_HC | α_CVD > α_HC | Genuine dimensionality reduction | Option (B) |
| **Methodological** | k*_CVD ≈ k*_HC | α_CVD ≈ α_HC | Bias-variance tradeoff | Option (A) |
| **Mixed** | k*_CVD < k*_HC | α_CVD ≈ α_HC | Dimensionality + noise | Needs simulation |

---

## Connection to Main Results

**Section 4b** (Basis Channel Ablation):
- HC-CVD gap: FE-6 d=1.36 → FE-K d=0.63 (−54% reduction)
- Is this because CVD truly has fewer dimensions?

**Section 5a** (Permutation Test):
- V1/V2 LOCO null ~0.10-0.13 (not zero)
- Eigenspectrum shows this comes from late-mode covariance

**RT-5** (CVD Failure = Data):
- Current vulnerability: "N=3 CVD cannot distinguish (A) model selection vs (B) biological"
- **MEME + Eigenspectrum provide triangulated answer**

**Phase 2** (Filter Design):
- If biological: Filter operates in lower-dimensional space (R³ not R⁴)
- If methodological: Filter uses same dimensionality, different tuning

---

## Usage

```bash
# Run both analyses sequentially
sbatch sbatch/run_dimensionality.sbatch

# Or run individually
python scripts/dimensionality/analyze_eigenspectrum_decay.py \
    --baseline_dir /path/to/C010 \
    --output_dir results/dimensionality/eigenspectrum

python scripts/dimensionality/fit_meme_eigenspectrum.py \
    --baseline_dir /path/to/C010 \
    --output_dir results/dimensionality/meme
```

---

## References

- Pospisil, D. A., & Pillow, J. W. (2024). The eigenspectrum of neural population activity reveals broken power law structure. *bioRxiv*.
- Li, P., et al. (2014). Improved estimation of eigenvalues and eigenvectors of covariance matrices using their sample estimates. *IEEE Transactions on Information Theory*.
- Kong, W., & Valiant, G. (2017). Spectrum estimation from samples. *Annals of Statistics*.
