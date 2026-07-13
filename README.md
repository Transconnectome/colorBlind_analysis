# Development of a Personalized Color Vision Correction Display Filter for Individuals with Color Vision Deficiency Using fMRI-Based Neural Responses

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Decoding and characterizing color perception in color vision deficiency (CVD) using fMRI-based forward encoding models and Shared Response Model (SRM) group comparison**

![overallPipeline](analysis/Overall.png)

## Table of Contents

- [Overview](#overview)
- [Research Questions](#research-questions)
- [Current Status](#current-status)
- [Project Phases](#project-phases)
  - [Phase 1: Preprocessing & Baseline Decoding ✅](#phase-1-preprocessing--baseline-decoding-)
  - [Phase 2: SRM Between-Subject Group Comparison ✅](#phase-2-srm-between-subject-group-comparison-)
  - [Phase 2b: Decoder Model Validation ✅](#phase-2b-decoder-model-validation-)
- [Future Directions](#future-directions)
  - [Future Phase 1: Forward Encoding Model (360° Hue Interpolation) ✅](#future-phase-1-forward-encoding-model-360-hue-interpolation-)
  - [Future Phase 2: CVD Filter Optimization 🎯](#future-phase-2-cvd-filter-optimization-)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Data](#data)
- [References](#references)

---

## Research Questions

### Primary Questions (연구 질문)

#### RQ1: Neural Color Discrimination Despite Retinal Deficits
**Can individuals with CVD distinguish colors neurally despite retinal deficits, as measured by fMRI decoding accuracy in visual cortex?**

**망막 결함에도 불구하고 색맹자가 신경 수준에서 색을 구별할 수 있는가? (fMRI 디코딩 정확도 측정)**

- ✅ **Answer**: Yes! All CVD participants showed successful color decoding
  - **답변**: 예! 모든 색맹 참가자가 성공적인 색 디코딩을 보임
  - Mean decoding accuracy: **0.592 ± 0.121** across 40 subject-ROI pairs (C010 + Procrustes pipeline)
  - hV4 shows strongest selectivity: **0.613 ± 0.092** (decoding), **0.541 ± 0.283** (RDM correlation)
  - RDM correlation after Procrustes: **0.381 ± 0.278** (100% positive pairs, up from 52.5% pre-alignment)
  - CVD group: **0.684 ± 0.094** (numerically higher than HC 0.552 ± 0.111)
  - **Supporting evidence**: Noise ceiling utilization 79.4% (C010 pipeline); all subjects p < 0.001 vs chance

#### RQ2: Inter-Individual Heterogeneity in CVD
**Does CVD show inter-individual heterogeneity in neural color representations, necessitating personalized approaches?**

**색맹은 신경 색 표상에서 개인 간 이질성을 보이는가? 개인화된 접근이 필요한가?**

- ✅ **Answer**: Yes, substantial individual heterogeneity confirmed via SRM group comparison
  - **답변**: 예, SRM 그룹 비교를 통해 상당한 개인차 확인
  - **SRM LOO-consistent group disparity** (HC-only SRM, LOO references):
    - V1: p=0.062 (g=1.16), V2: p=0.075 (g=1.04) — trending with large effects
    - V3/hV4: not significant
  - **Individual CVD tests** (Crawford & Howell 1998):
    - **sub-09** (protan): V1 p=0.007* — early visual cortex disruption
    - **sub-08** (deutan): V2 p=0.040* — mid-level visual processing impact
    - **sub-10** (deutan): falls within HC range — functionally normal representations
  - **LOSO color-dependency** (CVD color-specific, HC color-agnostic):
    - CVD: V2 p=0.010, V3 p=0.000, hV4 p=0.016
    - HC: p=0.21–0.36 (not significant)
  - **CVD heterogeneity**: 1.4–1.6× more dispersed than HC across all ROIs
  - **Key finding**: Identical genotype (deuteranopia) → Opposite neural phenotypes (sub-08 vs sub-10)
  - **Robustness**: Convergent validity with SRM-independent metrics (crossnobis r=0.486**, PCA r=0.742***)

#### RQ3: Neural-Guided Personalized Filter Design
**Can three-dimensional neural profiles (magnitude, sign, structure) inform individual-specific display filter design?**

**3차원 신경 프로파일(크기, 부호, 구조)이 개인별 맞춤형 디스플레이 필터 설계에 활용될 수 있는가?**

- 🔬 **In Progress** — Forward model complete, filter optimization planned
  - **결과**: Forward encoding model 완료, 필터 최적화 설계 중
  - Forward model (Future Phase 1) validated: hV4 interpolation confirmed (perm p=0.026)
  - Cool/S-axis distortion characterized as Phase 2 filter target
  - LOSO zero-shot transfer validated: group prior = viable prediction engine
  - **Next**: Stimulus-space filter optimization (Future Phase 2) using cone-shift analysis

---

### Sub-Research Questions (이후 연구 질문)

These questions address methodological foundations for the neural-guided filter development pipeline.

#### SRQ1: Shared Decoder Validation
**Can a common color decoder be successfully applied across HC and CVD participants after alignment?**

- ✅ **Answer**: Yes — alignment is essential; optimal pipeline is task-dependent
  - **LORO classification**: LDA+SRM best (acc_45 = 0.793, ICC = 0.666); resolves Procrustes LDA reliability paradox
  - **LOCO interpolation**: FE+Procrustes best (HC MAE 75.7°); ForwardEncoding is the only model with interpolation ability
  - Without alignment: ALL models perform at chance (~37–39% LORO, ~90° LOCO)
  - HC ≈ CVD performance (LDA: HC 0.805, CVD 0.859) → shared voxel-color mapping confirmed
  - Group prior: HC-mean W improves CVD LOCO by +4–8% (leakage-free nested CV)

#### SRQ3: Continuous Hue Interpolation
**Can a channel-based forward encoding model predict brain responses for any hue angle in 360° circular space?**

- ✅ **Complete** (Future Phase 1)
  - **Encoder**: Ridge regression with GCV (ridge_gcv) — direct fit, no group prior
  - **Gate result**: hV4 = PRIMARY GO (perm p=0.026, FE-3); V3 = CONDITIONAL (p=0.045); V1/V2 = FAIL
  - **Omnibus**: Stouffer Z=2.87, p=0.002 — cortex-level color interpolation confirmed
  - **Key finding**: Discrimination ≠ Interpolation — V1/V2 classify but cannot interpolate
  - **HC-CVD gap**: Cool/S-axis (blue, purple, magenta) persistent deficit; warm gap = model-specification artifact
  - **LOSO Zero-Shot**: hV4 ZS ≈ LORO (p=0.913) — group prior is a valid prediction engine for Phase 2

#### SRQ4: CVD Filter Optimization
**Can optimization-based filter discovery find display colors that make CVD brain responses match HC responses?**

- 🎯 **Planned** (Future Phase 2)
  - **Goal**: For each original color θ_orig, optimize display color θ_display via stimulus-space filter T_ψ
  - **Inputs from SRQ3**: Target color range [180°, 315°] (cool/S-axis), per-subject optimal K, distortion direction, pairwise geometry
  - **Pre-validation**: SRM pair-level analysis complete — sub-08 FDR 32 pairs, sub-09 FDR 7 pairs, sub-10 FDR 0 pairs (compensated)

---

### Methodology

- **Participants**: 10 subjects (7 HC, 3 CVD: 2 deuteranopia, 1 protanomaly)
- **Paradigm**: Rapid serial visual presentation (RSVP) of 8 isoluminant colors
- **Runs**: 6 runs per subject
- **ROIs**: V1, V2, V3, hV4 (defined using Wang et al. 2015 probabilistic atlas)
- **Space**: MNI152NLin2009cAsym, res-2
- **Preprocessing**: fMRIPrep v23.2.3 with MI-based coregistration
- **Pipeline**: C010 (2nd-level drift removal) + Procrustes alignment (validated 2026-02-09)
- **Analysis methods**:
  - Forward encoding models (Brouwer & Heeger, 2009)
  - Shared Response Model (SRM; BrainIAK) for between-subject alignment
  - Crawford & Howell (1998) modified t-test for single-case inference
  - Crossnobis distance (Walther et al., 2016) for SRM-independent validation

---

## Current Status

### Completed ✅

- **Phase 1**: C010 + Procrustes baseline decoding (validated 2026-02-09)
  - Mean decoding accuracy 0.592, RDM correlation 0.381, noise ceiling utilization 79.4%
- **Phase 2**: SRM between-subject group comparison (HC-only SRM, LOO-consistent)
  - Group: V1 p=0.062, V2 p=0.075; Individual: sub-09 V1 p=0.007*, sub-08 V2 p=0.040*
  - LOSO color-dependency: CVD V2/V3/hV4 significant, HC not significant
- **Phase 2b**: Decoder model comparison and cross-validation (21/21 validations complete)
  - Task-dependent optimality: LDA+SRM for LORO (0.793), FE+Procrustes for LOCO (75.7°)
  - Procrustes/SRM alignment essential; HC ≈ CVD; group prior validated (+4–8% CVD LOCO)
  - Negative results: decoder bottleneck not improvable (Result 7), sequential/MLP dead ends (Result 10)
- **Robustness triangulation** (A3/A4/A5):
  - A3 Variance Explained: CVD VE ≥ HC (V2 g=−1.68)
  - A4 Crossnobis RDM: SRM-independent convergent r=0.486**
  - A5 PCA-CCA replication: convergent r=0.742***

### Complete ✅ (Future Phase 1)

- **Future Phase 1**: Forward encoding model — 360° hue interpolation validated
  - hV4 = PRIMARY GO (perm p=0.026); Omnibus Z=2.87, p=0.002
  - ridge_gcv encoder confirmed; smooth_tikh rejected
  - HC-CVD gap: cool/S-axis persistent deficit; warm gap = model artifact
  - LOSO zero-shot ≈ LORO (p=0.913) — group prior validated for Phase 2
  - Track A (residual biology), Track B (CVD prediction), Track C (dimensionality) — all complete or ready

### Planned 🎯

- **Future Phase 2**: Filter optimization — stimulus-space CVD correction via cone-shift analysis

---

## Project Phases

### Phase 1: Preprocessing & Baseline Decoding ✅

**Goal**: Establish baseline decoding performance and quantify color representation quality

**Pipeline** (C010 + Procrustes, validated 2026-02-09):
- 1st-level GLM: FIR basis (8 delays, 0–12s)
- Voxel selection: Top 50% by FIR R²
- 2nd-level GLM: 8 HRF + 8 derivative + 12 per-run drift regressors
- Procrustes alignment: runs 1–5 aligned to run 0
- Forward encoding: 6 half-wave rectified channels, LORO cross-validation

**Key Results**:

| ROI | N | RDM Correlation (M ± SD) | Decoding Accuracy (M ± SD) |
|-----|---|--------------------------|---------------------------|
| V1 | 10 | 0.313 ± 0.215 | 0.560 ± 0.138 |
| V2 | 10 | 0.370 ± 0.256 | 0.581 ± 0.131 |
| V3 | 10 | 0.316 ± 0.328 | 0.613 ± 0.130 |
| hV4 | 10 | **0.541 ± 0.283** | **0.613 ± 0.092** |

**Documents**: `analysis/phase1_preprocess_decoding/README.md`, `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`

---

### Phase 2: SRM Between-Subject Group Comparison ✅

**Goal**: Quantify HC-CVD representational differences in SRM shared space

**Method**: HC-only SRM (BrainIAK) with LOO-consistent disparity analysis
- SRM trained on 7 HC subjects only; CVD projected via SVD
- LOO references: HC sub-i vs mean of other 6 HC; CVD vs same LOO references
- Three bias fixes: (1) HC-only training, (2) LOO for HC, (3) same LOO refs for CVD
- Crawford & Howell (1998) for individual CVD inference
- 10,000 permutation iterations (LOO-consistent)

**Canonical script**: `analysis/phase2_SRM_across_between/rerun_loo_consistent.py`

**Key Results**:

| ROI | HC LOO | CVD LOO | Separation | p (perm) | Hedges' g |
|-----|--------|---------|------------|----------|-----------|
| V1 | 0.453 | 0.590 | 0.137 | 0.062 | 1.16 |
| V2 | 0.486 | 0.606 | 0.120 | 0.075 | 1.04 |
| V3 | 0.540 | 0.564 | 0.023 | 0.395 | 0.18 |
| hV4 | 0.700 | 0.677 | −0.023 | 0.559 | −0.14 |

**Individual CVD** (Crawford & Howell):
- sub-09 (protan): **V1 p=0.007*** — early visual cortex
- sub-08 (deutan): **V2 p=0.040*** — mid-level processing
- sub-10 (deutan): HC range — functionally normal

**Validation** (12+ tests): LOSO stability (V2 7/7), split-half (V2 both halves sig), permutation, ICC, RDM consistency, alignment comparison, crossnobis, PCA-CCA, variance explained

**Documents**: `analysis/phase2_SRM_across_between/README.md`, `analysis/phase2_SRM_across_between/validation/`

---

### Phase 2b: Decoder Model Validation ✅

**Goal**: Validate decoder assumptions — linearity, alignment necessity, group comparability, interpolation

**Methods**: 6 models (LDA, Ridge, ForwardEncoding, KernelRidge, SVM, MLP) compared with LORO and LOCO CV

**Key Findings**:
1. **Task-dependent optimality**: LDA+SRM for LORO classification (0.793, ICC 0.666); FE+Procrustes for LOCO interpolation (75.7°)
2. **Alignment is essential**: Without it, ALL models perform at chance (~37–39% LORO, ~90° LOCO)
3. **HC ≈ CVD**: Shared voxel-color mapping confirmed (justifies filter learning)
4. **ForwardEncoding is the only model with interpolation ability** (LOCO MAE 72–83° vs 90° chance)
5. **LDA+SRM = optimal LORO pipeline**: SRM resolves LDA fold-instability (ICC 0.013 → 0.666)
6. **Group prior validated**: HC-mean W improves CVD LOCO by +4–8% (leakage-free nested CV)
7. **Cross-subject generalization**: HC→CVD = HC→HC in SRM space (no group bias)
8. **Negative results**: Decoder bottleneck not improvable (4 alt. methods all worse); sequential/MLP dead ends

**Documents**: `analysis/phase3_decoder_comparing/model_comparison_validation/`, `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`

---

## Future Directions: Neural-Guided Filter Development

### Overall Pipeline

![Overall Pipeline](analysis/Overall.png)

Our filter development follows a 2-phase approach: forward model validation (complete) → stimulus-space filter optimization (planned).

---

### Future Phase 1: Forward Encoding Model (360° Hue Interpolation) ✅

**Goal**: Validate continuous hue encoding — can we predict brain responses for colors not in the training set?

**Method**: Channel-based forward encoding `Y_s = W_s @ C(θ; K)` with ridge_gcv encoder, Leave-One-Color-Out (LOCO) cross-validation

**Key Results**:

| ROI | Optimal K | Perm p (10K) | Gate |
|-----|:---------:|:------------:|:----:|
| V1  | FE-2      | 0.170        | FAIL |
| V2  | FE-3      | 0.125        | FAIL |
| V3  | FE-8      | 0.045        | CONDITIONAL |
| hV4 | FE-3      | 0.026        | **PRIMARY GO** |

- **Omnibus**: Stouffer Z=2.87, p=0.002 — cortex-level interpolation exists
- **Discrimination ≠ Interpolation**: V1/V2 discriminate but cannot interpolate (confirmed across all basis types including opponent)
- **HC-CVD gap**: Warm-color gap = model-specification artifact (>100% reduction at optimal K); Cool/S-axis gap persists at 65% → Phase 2 filter target
- **LOSO Zero-Shot**: hV4 ZS ≈ LORO (p=0.913) — group prior validated as prediction engine
- **Track B (CVD Prediction)**: Per-subject K* adopted (sub-08 K*=8 → 6.4× LOCO improvement); anisotropic basis and hierarchical FE rejected

**Documents**: `analysis/future_phase1_forward_model/README.md`, `analysis/future_phase1_forward_model/RESULTS.md`

---

### Future Phase 2: CVD Filter Optimization 🎯

**Goal**: For each original color, find the optimal display color that makes CVD brain responses match HC responses via stimulus-space filter T_ψ

**Core Innovation**: Stimulus-space correction guided by cone-shift analysis (not direct voxel transformation)

**Mathematical Framework**:

```
T_ψ: θ → θ' = θ + ψ(θ)
where ψ(θ) = Σ_k [a_k sin(kθ) + b_k cos(kθ)]   (Fourier parameterization)
```

**Pre-Validation Complete**: SRM pair-level distortion characterized per CVD subject
- sub-08 (deutan): 32 FDR-significant pairs, split-half r=0.73–0.84, cone-shift prediction 7/7 match
- sub-09 (protan): 7 FDR pairs (V1 magenta axis), dual dissociation with sub-08
- sub-10 (deutan, compensated): 0 FDR pairs, HC-like — cortical compensation case study

**Documents**: `analysis/phase2_procrustes_cvd_hc/README.md` (CVD–HC SRM pair-level distortion; 구 `future_phase2_filter_optimization/pre_validation/notion_prevalidation.md`은 commit 58bce39에서 삭제)

---

## Legacy Plans (For Reference)

<details>
<summary><b>Original Phase Plans (Click to expand)</b></summary>

These were the original phase plans, now superseded by the SRM-based approach (Phase 2) and the forward model + filter pipeline above.

### Original Hyperalignment Plan
- Goal: Trial-aligned GPA for HC common space
- Status: Superseded by SRM (Phase 2) — archived in `analysis/archive/future_phase1_hyperalignment/`

### Original Phase 2A: Linear Filter Learning
- Goal: Learn linear transformations to map CVD patterns to HC-like patterns
- Status: Superseded by SRM group comparison approach

### Original Phase 2B: Forward Encoding Model
- Goal: Learn explicit stimulus → brain mapping
- Status: Completed as Future Phase 1 (forward encoding model)

### Original Phase 3: Inverse Transformation
- Goal: Compute stimulus-level color corrections
- Status: Evolved into Future Phase 2 stimulus-space filter optimization

### Original Phase 4: Deep Learning Filter
- Goal: End-to-end neural network for CVD color correction
- Status: Deferred — nonlinear models showed no benefit in current data/task

</details>

---

## Installation

### Requirements

- Python 3.9
- Conda (Miniconda or Anaconda)
- Git LFS (`git lfs install` — required for residual array files)
- SLURM cluster (for server-side large-scale analysis only)

### Quick Start

```bash
git clone https://github.com/haba6030/colorBlind_analysis.git
cd colorBlind_analysis
git lfs pull          # download large residual arrays tracked by LFS
```

### Environment Setup

#### Mac / Linux (full pipeline including BrainIAK SRM)

```bash
# macOS: install OpenMPI first
brew install open-mpi

# Ubuntu/Debian
sudo apt install libopenmpi-dev

conda env create -f environment_mac.yml
conda activate colorblind
```

#### Windows (native — all analysis except SRM re-training)

```bash
conda env create -f environment_windows.yml
conda activate colorblind
```

> **Windows + BrainIAK SRM**: BrainIAK is not officially supported on native Windows.
> Install [MS-MPI](https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi),
> then uncomment the `mpi4py` / `brainiak` lines in `environment_windows.yml`.
> For full compatibility, **WSL2 with Ubuntu** is strongly recommended — use `environment_mac.yml` inside WSL2.

#### Server (`node3`, `nilearn` env)

```bash
conda activate nilearn          # pre-installed on the server
# CRITICAL: always prefix BrainIAK scripts with mpirun
mpirun -np 1 python script.py  # bare 'python' crashes with PMIx error
```

### Data Layout after Clone

Preprocessed amplitude arrays are included directly in this repository:

| Path | Size | Contents |
|---|---|---|
| `analysis/phase1_procrustes_decoding/results/full_dataset_C010/` | 11 MB | Procrustes-aligned amplitudes — **primary input for all analyses** |
| `analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals/` | 186 MB | Same + 2nd-level residuals (Git LFS) |
| `data/behavior/` | 320 KB | JND and 8-AFC behavioural data |

Raw fMRI BIDS data (`data/sub-*/`) is **not** in this repository (IRB/privacy + 20 GB). Contact the PI for access.

### Verify Installation

```bash
conda activate colorblind
python -c "import nilearn, nibabel, sklearn, scipy; print('Core OK')"
# If BrainIAK installed:
mpirun -np 1 python -c "from brainiak.funcalign.srm import SRM; print('BrainIAK OK')"
```

---

## Usage

### Phase 1: Baseline Decoding

```bash
# Run forward encoding model for a single subject-ROI
conda activate nilearn
python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject 02 \
    --roi V1 \
    --dataset full_dataset_C010
```

### Phase 2: SRM Group Comparison

```bash
# Run canonical LOO-consistent SRM analysis
conda activate srm
mpirun -np 1 python analysis/phase2_SRM_across_between/rerun_loo_consistent.py
```

### Phase 2b: Decoder Comparison

```bash
# Run model comparison (LORO + LOCO)
python analysis/phase3_decoder_comparing/model_comparison_validation/scripts/run_comparison.py
```

---

## Project Structure

```
colorBlind_analysis/
├── README.md                              # This file
├── CLAUDE.md                              # Development guide for Claude Code
│
├── analysis/                              # Core analysis code
│   ├── README.md                          # Master analysis overview
│   ├── METHODS_RESULTS_SUMMARY_FOR_PAPER.md  # Exact statistics for all phases
│   ├── filter_design_plan.md              # Filter design planning
│   │
│   ├── prep_trials/                       # Registration quality comparison
│   ├── roi_masks/                         # ROI mask files
│   │
│   ├── phase1_preprocess_decoding/        # Phase 1: Baseline (C010 + Procrustes) ✅
│   │   ├── fir_reconstruction_BH2009_system_clean.py  # Main analysis script
│   │   └── results/full_dataset_C010/     # Per-subject per-ROI results
│   │
│   ├── phase2_SRM_across_between/         # Phase 2: SRM group comparison ✅
│   │   ├── rerun_loo_consistent.py        # Canonical LOO-consistent analysis
│   │   ├── validation/                    # 12+ validation tests (A3/A4/A5, 1A-2D)
│   │   └── results/
│   │
│   ├── phase3_decoder_comparing/          # Phase 2b: Decoder cross-validation ✅
│   │   ├── model_comparison_validation/   # 6-model LORO + LOCO comparison
│   │   └── results/
│   │
│   ├── phase2_procrustes_cvd_hc/          # Legacy: Procrustes-based comparison
│   ├── archive/phase3_procrustes_filter/          # Legacy: Exploratory filter learning
│   │
│   ├── archive/future_phase1_hyperalignment/      # Archived: HC hyperalignment (superseded by SRM)
│   ├── future_phase1_forward_model/       # SRQ3: 360° encoder ✅ (ridge_gcv, hV4 GO)
│   ├── future_phase2_filter_optimization/ # SRQ4: Stimulus-space filter 🎯 (planned)
│   │
│   ├── comprehensive/                     # Cross-phase analyses
│   ├── validation/                        # Cross-pipeline validation
│   └── utils/                             # Shared utilities
│
├── prediction_model_workspace/            # Legacy dev workspace (superseded)
│   ├── MASTER_PLAN.md                     # Original 3-phase plan (historical)
│   ├── docs/                              # Early documentation + pipeline diagrams
│   └── scripts/                           # Experimental scripts (migrated to analysis/)
│
├── docs/                                  # Documentation
│   ├── program_paper/                     # Manuscript (main.tex, main_kr.tex)
│   ├── methods/                           # Methodology docs
│   ├── results/                           # Result summaries
│   └── technical/                         # Technical reports
│
├── data/                                  # Local data
├── ProbAtlas_v4/                          # Wang Atlas (2015)
├── papers/                                # Reference papers
├── results/                               # Analysis outputs (gitignored)
└── derivatives/                           # Processed fMRI data (gitignored)
```

### Key Directories

**`analysis/`** — Organized by research phases (Phase 1 → Phase 2 → Phase 2b → Future Phases 1-2)
- Each phase has its own README explaining methods, results, and connections
- `METHODS_RESULTS_SUMMARY_FOR_PAPER.md`: Authoritative source for all statistics

**`prediction_model_workspace/`** — Legacy development workspace (superseded)
- Early experimental scripts and planning documents
- Active code has migrated to `analysis/future_phase1_forward_model/` and `analysis/future_phase2_filter_optimization/`

---

## Data

### Data Availability

Due to participant privacy, raw fMRI data are not publicly available. Processed results and code are provided for reproducibility.

### Data Structure (BIDS format)

```
colorBlind_data/
├── sub-01/
│   ├── anat/
│   │   └── sub-01_T1w.nii.gz
│   ├── func/
│   │   ├── sub-01_task-rsvp_run-1_bold.nii.gz
│   │   ├── sub-01_task-rsvp_run-1_events.tsv
│   │   └── ... (6 runs total)
│   └── fmap/
│       └── sub-01_fieldmap.nii.gz
└── ... (sub-02 through sub-10)
```

### Stimulus Information

- **Colors**: 8 isoluminant colors equally spaced in CIELAB (L*=70)
- **Presentation**: RSVP at 2 Hz (500ms/stimulus)
- **Runs**: 6 runs per subject
- **Duration**: ~25 min per run

See `materials/` for stimulus generation code.

---

## Contributors

- **Jin-il Kim** — Principal investigator

---

## References

### Key Papers

1. **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
   - Foundation for our forward encoding model approach

2. **Chen, P.-H. C., Chen, J., Yeshurun, Y., Hasson, U., Haxby, J., & Ramadge, P. J. (2015).** A reduced-dimension fMRI shared response model. *Advances in Neural Information Processing Systems*, 28, 460-468.
   - BrainIAK Shared Response Model (SRM) for between-subject alignment

3. **Crawford, J. R., & Howell, D. C. (1998).** Comparing an individual's test score against norms derived from small samples. *The Clinical Neuropsychologist*, 12(4), 482-486.
   - Single-case inference for individual CVD testing

4. **Walther, A., Nili, H., Ejaz, N., Alink, A., Kriegeskorte, N., & Diedrichsen, J. (2016).** Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.
   - Cross-validated Mahalanobis distance (crossnobis) for RDM computation

5. **Haxby, J. V., Connolly, A. C., & Guntupalli, J. S. (2014).** Decoding neural representational spaces using multivariate pattern analysis. *Annual Review of Neuroscience*, 37, 435-456.
   - Theoretical framework for MVPA

6. **Wang, L., Mruczek, R. E., Arcaro, M. J., & Bhatt, M. (2015).** Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
   - ROI definition atlas

### Additional References

- See `docs/program_paper/main.tex` for complete bibliography
- Key papers available in `papers/` directory

---

**Last Updated**: 2026-03-16
