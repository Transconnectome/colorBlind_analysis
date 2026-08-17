# Population Organization Analysis (Bannert Validation)

> **Research Question**: Does CVD dimensionality reduction manifest in voxel-space organization?
> **Framework**: Bannert & Bartels (2025) KDE+softmax voxel preference mapping

---

## Analysis

### Voxel Color Preference Mapping (`map_voxel_color_preference.py`)

**Purpose**: Visualize which voxels prefer which colors, test HC vs CVD reorganization

**Method** (Bannert & Bartels 2025):
1. For each voxel, identify preferred color (max response across 8 colors)
2. Apply KDE to response strength distribution per color
3. Softmax normalization → % deviation from uniform (12.5% for 8 colors)
4. Statistical test: HC vs CVD preference distribution differences

**Caveat**: Our data lacks retinotopic coordinates → use voxel response magnitude as 1D proxy

**Expected Patterns**:
- **No reorganization**: Preference peaks similar (HC ≈ CVD)
- **Reorganization**: Shifted peaks (e.g., CVD red-preference → orange/yellow)

**Output**: `results/population_organization/voxel_preference/`
- `preference_results.json` — Per-color preference %, HC vs CVD p-values
- `fig_preference_polar.pdf` — 8 polar plots (one per color)
- `fig_preference_distribution.pdf` — Bar plots (voxel count per color)

---

## Expected Outcomes

### Scenario A: No Reorganization (Most Likely)

```
| Color  | HC Peak (% dev) | CVD Peak (% dev) | p     |
|--------|-----------------|------------------|-------|
| Red    | +15.2           | +12.8            | 0.41  |
| Orange | +8.1            | +9.2             | 0.67  |
| Yellow | -3.2            | -2.1             | 0.73  |
| Green  | +11.4           | +10.9            | 0.89  |

→ All p > 0.3 (no significant shifts)
```

**Interpretation**:
- CVD retains HC-like voxel organization
- Dimensionality reduction is **representational** (stimulus-space), not **organizational** (voxel-space)
- Phase 3 cross-decoding success (10/12) explained: same population geometry

**Phase 2 Implications**:
- Filter T_psi operates in **stimulus-space only**: θ → θ'
- NO need for voxel-space transformation V: Y_CVD → Y_HC
- Validates current PLAN.md architecture

### Scenario B: Reorganization (Cortical Plasticity)

```
| Color  | HC Peak | CVD Peak | Shift  | p     | Effect |
|--------|---------|----------|--------|-------|--------|
| Red    | +15.2   | +5.8     | **-9.4** | **0.023** | L-cone loss |
| Green  | +11.4   | +18.7    | **+7.3** | **0.031** | Compensatory |

→ Significant red/green redistribution
```

**Interpretation**:
- CVD shows developmental cortical reorganization
- Shifted voxel preferences → chronic retinal deficit reshaped population tuning
- Cross-decoding still succeeds because geometry is "similar enough" (not identical)

**Phase 2 Implications**:
- **Two-stage filter required**:
  1. Stimulus transformation: T_psi(θ)
  2. Voxel remapping: V @ Y_CVD
- Combined: W_HC @ C(T_psi(θ)) ≈ V @ Y_CVD
- More complex than current design

---

## Connection to Main Results

**Phase 3** (Cross-Decoding):
- HC-trained LDA generalizes to CVD (10/12 pairs p<0.05)
- **If Scenario A**: Explained by intact voxel geometry
- **If Scenario B**: Partial reorganization still preserves shared structure

**Bannert & Bartels (2025)**:
- Key finding: "Retinotopic color biases shared across observers"
- **If CVD preference ≈ HC**: Bannert's finding robust to retinal deficit
- **If CVD preference ≠ HC**: Retinal input reshapes cortical organization

**Section 11** (Eigenspectrum):
- If dimensionality reduced (k*_CVD < k*_HC) BUT voxel organization intact
- → Supports **information loss without remapping** (clean dissociation)

**RT-5** (CVD Failure = Data):
- If voxel organization intact: "CVD LOCO failure = distorted input to normal cortex"
- If reorganization: "CVD LOCO failure = distorted input + reorganized cortex"

---

## Usage

```bash
# Run analysis
sbatch sbatch/run_population_org.sbatch

# Or run directly
python scripts/population_organization/map_voxel_color_preference.py \
    --baseline_dir /path/to/C010 \
    --output_dir results/population_organization/voxel_preference \
    --bandwidth_method scott
```

---

## Validation Checklist

After analysis completion:

- [ ] Polar plots show clear color-specific peaks (not uniform)
- [ ] HC maps show distinct spatial clustering per color
- [ ] CVD vs HC comparison: are peaks shifted or similar?
- [ ] If shifted: which colors show reorganization? (red/green expected for deutan)
- [ ] If similar: confirms stimulus-level distortion only

---

## References

- Bannert, M. M., & Bartels, A. (2025). Shared response modeling reveals retinotopic organization of color preference in human visual cortex. *Nature Communications*, 16(1), 1-15.
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
