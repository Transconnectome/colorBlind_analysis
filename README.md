# Color Vision Deficiency fMRI Decoding Project

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Decoding and correcting color perception in color vision deficiency (CVD) using fMRI-based forward encoding models**

## Table of Contents

- [Overview](#overview)
- [Research Questions](#research-questions)
- [Current Status](#current-status)
- [Paper & Publications](#paper--publications)
- [Project Phases](#project-phases)
  - [Phase 1: Baseline Analysis ✅](#phase-1-baseline-analysis-)
  - [Phase 2A: Linear Filter Learning 🔄](#phase-2a-linear-filter-learning-)
  - [Phase 2B: Forward Encoding Model 📋](#phase-2b-forward-encoding-model-)
  - [Phase 3: Inverse Transformation 🎯](#phase-3-inverse-transformation-)
  - [Phase 4: Deep Learning Filter 🚀](#phase-4-deep-learning-filter-)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Data](#data)
- [Contributors](#contributors)
- [References](#references)

---

## Research Questions

### Primary Questions (연구 질문)

#### RQ1: Neural Color Discrimination Despite Retinal Deficits
**Can individuals with CVD distinguish colors neurally despite retinal deficits, as measured by fMRI decoding accuracy in visual cortex?**

**망막 결함에도 불구하고 색맹자가 신경 수준에서 색을 구별할 수 있는가? (fMRI 디코딩 정확도 측정)**

- ✅ **Answer**: Yes! All CVD participants showed successful color decoding
  - **답변**: 예! 모든 색맹 참가자가 성공적인 색 디코딩을 보임
  - Classification accuracy: V1 (76%), V2 (71%), V3 (69%), hV4 (68%)
  - Reconstruction error: 32-48° (random baseline: 90°)
  - **Supporting evidence**: RDM structural preservation >90% in V1-V2
  - **근거**: V1-V2에서 RDM 구조적 보존 >90%

#### RQ2: Inter-Individual Heterogeneity in CVD
**Does CVD show inter-individual heterogeneity in neural color representations, necessitating personalized approaches?**

**색맹은 신경 색 표상에서 개인 간 이질성을 보이는가? 개인화된 접근이 필요한가?**

- ✅ **Answer**: Yes, substantial individual heterogeneity even within same CVD type
  - **답변**: 예, 동일한 색맹 유형 내에서도 상당한 개인차 존재
  - **Three-dimensional characterization** (3차원 특성화):
    - **Magnitude** (크기): L2 norm ratios 0.66-1.21 (±30% variation)
    - **Sign/Baseline** (부호/기준선): Directional biases -0.41 to +0.32
    - **Structure** (구조): RDM differences 0.118-0.505
  - **Key finding**: Identical genotype (deuteranopia) → Opposite neural phenotypes (Sub-08 vs Sub-09)
  - **핵심 발견**: 동일 유전형(녹색맹) → 정반대 신경 표현형 (Sub-08 vs Sub-09)

#### RQ3: Neural-Guided Personalized Filter Design
**Can three-dimensional neural profiles (magnitude, sign, structure) inform individual-specific display filter design?**

**3차원 신경 프로파일(크기, 부호, 구조)이 개인별 맞춤형 디스플레이 필터 설계에 활용될 수 있는가?**

- ✅ **Feasibility demonstrated** (가능성 입증 완료): Subject-specific linear transformations successfully mapped CVD → HC-like patterns
  - **결과**: 개인별 선형 변환이 색맹 패턴을 정상인 유사 패턴으로 성공적 매핑
  - **Geometric alignment**: 97.2% Procrustes disparity reduction
  - **기하학적 정렬**: 97.2% Procrustes 불일치도 감소
  - **Structural recovery**: RDM correlation ≥0.999 with HC
  - **구조적 복원**: HC와 RDM 상관 ≥0.999
  - **Individual optimization**: Loss weights ($\lambda_{\text{mag}}$, $\lambda_{\text{base}}$, $\lambda_{\text{struct}}$) tailored to each CVD profile
  - **개인 최적화**: 각 색맹 프로파일에 맞춘 손실 가중치 조정
  - ⚠️ **Limitation**: Retrospective validation only; prospective behavioral testing pending
  - ⚠️ **한계**: 회고적 검증만 완료; 전향적 행동 검증 미실시

---

### Next Research Questions (이후 연구 질문)

These questions address methodological foundations for the 3-phase neural-guided filter development pipeline (MASTER_PLAN.md).

**이 질문들은 3단계 신경 기반 필터 개발 파이프라인(MASTER_PLAN.md)의 방법론적 기반을 다룹니다.**

#### SRQ1: Shared Decoder Validation
**Can a common color channel-to-voxel decoder (W matrix) be successfully applied across HC and CVD participants after alignment?**

**정렬 후 정상인과 색맹 참가자 간에 공통 색 채널-복셀 디코더(W 행렬)를 성공적으로 적용할 수 있는가?**

- ✅ **Answer**: Yes, after Procrustes alignment
  - **답변**: 예, Procrustes 정렬 후 가능
  - HC common W applied to aligned CVD: 5-10° reconstruction error (matches HC performance)
  - CVD without alignment: 84-96° error (chance level)
  - **Implication**: Linear transformation (Procrustes) sufficient for decoder sharing
  - **함의**: 선형 변환(Procrustes)만으로 디코더 공유 가능

#### SRQ2: Hyperalignment for Common Space
**Can trial-aligned Generalized Procrustes Analysis (GPA) create a stable HC common space for robust encoder learning?**

**시행별 정렬 일반화 Procrustes 분석(GPA)이 견고한 인코더 학습을 위한 안정적인 HC 공통 공간을 생성할 수 있는가?**

- 🔄 **In progress** (Phase 1 of MASTER_PLAN.md)
  - **진행 중** (MASTER_PLAN.md의 Phase 1)
  - **Goal**: Align HC participants' trial-wise voxel patterns (~384 trials/subject) into shared representational space
  - **목표**: HC 참가자의 시행별 복셀 패턴(~384 trials/subject)을 공유 표현 공간으로 정렬
  - **Method**: Trial-aligned GPA with full voxel space (NO PCA) to preserve geographic features
  - **방법**: 지리적 특징 보존을 위한 전체 복셀 공간 GPA (PCA 사용 안 함)
  - **Success criteria**: Procrustes disparity <0.10, split-half stability >0.80
  - **성공 기준**: Procrustes 불일치도 <0.10, 분할-반복 안정성 >0.80

#### SRQ3: Continuous Hue Interpolation
**Can a channel-based forward encoding model predict brain responses for any hue angle in 360° circular space, interpolating between 8 measured colors?**

**채널 기반 순방향 인코딩 모델이 8개 측정 색상 사이를 보간하여 360° 원형 공간의 임의 색조 각도에 대한 뇌 반응을 예측할 수 있는가?**

- 📋 **Planned** (Phase 2 of MASTER_PLAN.md)
  - **계획 중** (MASTER_PLAN.md의 Phase 2)
  - **Goal**: Develop continuous hue encoder (0-360°) using 6 half-wave rectified basis channels
  - **목표**: 6개 반파 정류 기저 채널을 사용한 연속 색조 인코더(0-360°) 개발
  - **Validation strategy** (검증 전략):
    - **Direct**: Leave-One-Color-Out (LOCO) CV - train on 7 colors, predict held-out 8th
    - **직접**: LOCO CV - 7색 학습, 8번째 색 예측
    - **Indirect**: RDM smoothness, inter-encoder consistency across HC subjects
    - **간접**: RDM 부드러움, HC 참가자 간 인코더 일관성
  - **Success criteria**: LOCO error <50° (chance: 90°, baseline: 32°)
  - **성공 기준**: LOCO 오차 <50° (우연 수준: 90°, 기준선: 32°)

#### SRQ4: CVD Filter Optimization via 360° Search
**Can optimization-based filter discovery across continuous hue space find display colors that make CVD brain responses match HC responses for original colors?**

**연속 색조 공간에서 최적화 기반 필터 탐색이 색맹 뇌 반응을 원래 색상에 대한 정상인 반응과 일치시키는 디스플레이 색상을 찾을 수 있는가?**

- 🎯 **Planned** (Phase 3 of MASTER_PLAN.md)
  - **계획 중** (MASTER_PLAN.md의 Phase 3)
  - **Goal**: For each original color θ_orig, optimize display color θ_display using dual-constraint loss
  - **목표**: 각 원래 색상 θ_orig에 대해 이중 제약 손실을 사용하여 디스플레이 색상 θ_display 최적화
  - **Dual constraints** (이중 제약):
    - **Loss 1 (Voxel matching)**: ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||² - brain pattern alignment
    - **손실 1 (복셀 매칭)**: 뇌 패턴 정렬
    - **Loss 2 (Reconstruction)**: ||Decode(Ŷ_cvd(θ)) - θ_orig||² - perceptual accuracy
    - **손실 2 (재구성)**: 지각 정확도
  - **Ablation study** (절제 연구): 4 scenarios (Loss1 only, Loss2 only, Equal weight, Optuna optimization)
  - **Success criteria** (성공 기준):
    - Filter smoothness <2.0°/deg (필터 부드러움)
    - Reconstruction error ≤baseline 32° (재구성 오차)
    - Inter-CVD consistency <10° (색맹 간 일관성)
  - ⚠️ **Current scope**: In-silico validation only; empirical validation with actual filtered stimuli deferred
  - ⚠️ **현재 범위**: 실리코 검증만; 실제 필터링된 자극 실증 검증은 추후

---

### Methodology

- **Participants**: 10 subjects (7 HC, 3 CVD: 2 deuteranopia, 1 protanomaly)
- **Paradigm**: Rapid serial visual presentation (RSVP) of 8 isoluminant colors
- **ROIs**: V1, V2, V3, hV4 (defined using Wang et al. 2015 probabilistic atlas)
- **Analysis**: Forward encoding models (Brouwer & Heeger, 2009)
- **Preprocessing**: fMRIPrep v23.2.1 with careful quality control


---

## Current Status

### Completed ✅

- **Preprocessing pipeline**: Optimized fMRIPrep workflow with fieldmap correction
- **ROI definition**: Native-space probabilistic atlas transformation
- **Phase 1 analysis**: Baseline decoding and Procrustes analysis
  - Individual-level classification (6 HC, 3 CVD)
  - HC super-participant construction
  - CVD-HC comparison with significance testing

### In Progress 🔄

- **Phase 2A**: Linear filter learning
  - Subject-specific transformation matrices
  - RDM-based loss optimization
  - Filter validation on held-out runs

### Planned 📋

- **Phase 2B**: Forward encoding model development
- **Phase 3**: Inverse transformation (brain → stimulus space)
- **Phase 4**: Deep learning end-to-end filter
- **Psychophysical validation**: Behavioral testing with corrected images

---

## Paper & Publications

### Current Manuscript

**Title**: *Development of a Personalized Color Vision Correction Display Filter for Individuals with Color Vision Deficiency Using fMRI-Based Neural Responses and Deep Learning*

**Authors**: Jinil Kim, Minkue Cho, Jungwoo Seo, Jiook Cha

**Status**: In preparation (Korean version completed)

**Location**: `docs/paper/main_kr.tex` (LaTeX), `docs/paper/main_kr.pdf` (compiled)

### Structure

1. **Introduction**
   - Color vision deficiency prevalence and impact
   - Limitations of current correction approaches
   - Forward encoding models in neuroscience

2. **Methods**
   - Participants and data acquisition
   - Preprocessing pipeline (fMRIPrep)
   - ROI definition and feature selection
   - Forward encoding model (Brouwer & Heeger, 2009)
   - Procrustes analysis for CVD-HC comparison

3. **Results**
   - Baseline decoding accuracy (Phase 1)
   - CVD-HC representational differences
   - Filter learning performance (Phase 2A)

4. **Discussion**
   - Neural basis of CVD color perception
   - Implications for personalized correction
   - Future directions

### Conference Abstracts

- **OHBM 2024**: Submitted (see `docs/archive/OHBM_abstract/`)

---

## Project Phases

### Phase 1: Baseline Analysis ✅

**Goal**: Establish baseline decoding performance and quantify CVD-HC differences

**Methods**:
- Forward encoding model with channel response functions
- Leave-one-run-out cross-validation
- Procrustes analysis for pattern comparison
- Permutation testing for significance

**Key Results**:
- **HC super-participant**: Mean accuracy 72% across ROIs (significantly above chance)
- **CVD individuals**: Comparable decoding accuracy (68-76%)
- **CVD-HC differences**: Significant in all CVD subjects (T = 0.10-0.18, p < 0.001)

**Documents**:
- `docs/methods/PHASE1_RESULTS_ANALYSIS.md`
- `docs/results/BASELINE_RESULTS_SUMMARY.md`

---

### Phase 2A: Linear Filter Learning 🔄

**Goal**: Learn linear transformations to map CVD patterns to HC-like patterns

**Hypothesis**: A personalized linear filter F can transform CVD brain patterns Y to match HC patterns H:

```
F = Y @ A + b
```

where A is a transformation matrix and b is a bias vector.

**Loss Function**:
```python
L_total = λ_rdm * L_rdm + λ_proc * L_procrustes + λ_reg * L_regularization
```

- **L_rdm**: RDM (Representational Dissimilarity Matrix) similarity loss
- **L_procrustes**: Procrustes disparity loss
- **L_regularization**: Identity preservation + smoothness

**Methods**:
- Subject-specific filter optimization
- PyTorch-based gradient descent
- Train on 7 runs, validate on 1 held-out run
- Metrics: RDM correlation, Procrustes disparity, reconstruction accuracy

**Implementation**:
- `scripts/phase2a_filter_learning/phase2a_train_filter.py`
- `scripts/phase2a_filter_learning/apply_filter_with_reconstruction.py`

**Expected Outcomes**:
- Reduced Procrustes disparity (T → 0)
- Increased RDM similarity (r → 1.0)
- Validation for stimulus-space correction feasibility

**Documents**:
- `docs/methods/PHASE2A_FILTER_METHODS.md`
- `docs/methods/FILTER_APPLICATION_METHOD.md`

**Status**: Training infrastructure complete, optimization in progress

---

## Future Directions: 3-Phase Neural-Guided Filter Development

### Overall Pipeline

![Overall Pipeline](prediction_model/docs/overall.png)

Our future work follows a systematic 3-phase approach to develop personalized, neural-guided color correction filters:

1. **Phase 1**: Hyperalignment - Create common neural space across individuals
2. **Phase 2**: Forward Model - Learn continuous hue → brain response mapping
3. **Phase 3**: Filter Optimization - Find optimal display colors via 360° search

---

### Phase 1: Hyperalignment for HC Common Space 📋

![Phase 1 Pipeline](prediction_model/docs/phase1.png)

**Goal**: Align HC participants' brain responses into a common representational space

**Motivation**: Current analysis shows HC individuals have similar color structures (high Procrustes stability: 0.91/0.88) but use different coordinate systems (low RDM correlation: 0.26/0.24). Hyperalignment creates a shared space for stable encoder learning.

**Method**: Trial-aligned Generalized Procrustes Analysis (GPA)

**Implementation**:

1. **Extract trial-wise patterns** using Least Squares-Separate (LS-S) GLM
   - Input: 384 trials per subject (8 colors × 8 trials × 6 runs)
   - Output: Single-trial voxel patterns

2. **Perform hyperalignment** across HC participants
   - Optimize orthogonal transformations to align trial responses
   - Preserve within-subject geometry while maximizing between-subject alignment

3. **Validate alignment quality** (2-tier strategy)
   - **Tier 1 (Trial-level)**: Inter-subject correlation (ISC), LOSO decoding
   - **Tier 2 (Color-level)**: Procrustes disparity, RDM correlation, run-split stability

4. **Relearn common encoder** in aligned space
   - Fit shared weight matrix W across all HC data
   - Compare reconstruction accuracy to baseline

**Success Criteria**:
- Trial-level ISC > 0.30
- LOSO decoding > 25% (chance: 12.5%)
- Procrustes disparity < 0.08 (baseline: 0.089)
- RDM correlation > 0.30 (baseline: 0.26)

**Expected Outcome**: Stable common space enabling robust encoder learning for Phase 2

**Documents**: `prediction_model/docs/PHASE1_HYPERALIGNMENT.md`

---

### Phase 2: Continuous Hue Interpolation Model 📋

![Phase 2 Pipeline](prediction_model/docs/phase2.png)

**Goal**: Develop a continuous hue encoder that predicts brain responses for any color in 360° space

**Motivation**: Our experiment measured responses to only 8 discrete colors (45° spacing). To optimize CVD filters across all possible display colors, we need a model that interpolates between measured points.

**Method**: Channel-based forward encoding (Brouwer & Heeger 2009)

**Hypothesis**: *Circular basis functions spanning 360° hue space enable interpolation between measured colors*

**Implementation**:

1. **Define channel response functions**
   ```python
   # 8 color-selective channels (45° spacing)
   def channel_response(stimulus_hue, channel_center, bandwidth=60):
       return exp(-((stimulus_hue - channel_center)**2) / (2 * bandwidth**2))
   ```

2. **Train encoder in HC common space** (from Phase 1)
   ```
   Y_predicted = C(θ) @ W_enc
   ```
   where C(θ) is the channel activation vector for hue angle θ

3. **Validate interpolation** (2-tier)
   - **Direct**: Leave-One-Color-Out (LOCO) cross-validation
     - Train on 7 colors, predict held-out 8th color
     - Success: reconstruction error < 60° (chance: 90°, baseline: 32°)

   - **Indirect**: Quality metrics for unmeasured angles
     - RDM smoothness (gradual change across hues)
     - Inter-encoder consistency (similar predictions across voxels)

4. **Compare common vs individual encoders**
   - Assess whether personalized encoders improve predictions

**Phase 3 Dependency**: This encoder enables filter optimization across 360° hue space (not just 8 measured colors!)

**Expected Outcome**: Validated continuous encoder: `Ŷ_hc(θ) = C(θ) @ W_enc` for any θ ∈ [0°, 360°]

**Documents**: `prediction_model/docs/PHASE2_PREDICTION_MODEL.md`

---

### Phase 3: CVD Filter Optimization via 360° Search 🎯

![Phase 3 Pipeline](prediction_model/docs/phase3.png)

**Goal**: For each original color, find the optimal display color that makes CVD brain responses match HC responses

**Core Innovation**: Optimization-based filter discovery (not direct voxel transformation)

**Method**: Dual-constraint optimization across continuous hue space

**Mathematical Framework**:

For each original color θ_orig, solve:

```python
θ_display = argmin_θ [
    Loss_voxel:  ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²  # Brain pattern matching
    + λ * Loss_decode: ||Decode(Ŷ_cvd(θ)) - θ_orig||²  # Reconstruction accuracy
]
```

where:
- **Ŷ_hc(θ_orig)**: HC target pattern (from Phase 2 encoder)
- **Ŷ_cvd(θ)**: CVD predicted pattern for display color θ
- **Decode()**: Inverse mapping from voxel pattern → perceived color

**Why this works**:
1. ✅ **360° optimization**: Phase 2 encoder predicts responses for any display color
2. ✅ **Personalized**: Uses individual CVD's actual response patterns
3. ✅ **Dual objectives**: Matches both neural geometry AND perceptual accuracy
4. ✅ **Theoretically grounded**: CVD brain → HC brain alignment

**Implementation**:

1. **Collect CVD data**
   - Measure responses to 8 colors (existing data: sub-08, 09, 10)
   - Project CVD data into HC common space (from Phase 1)

2. **Learn CVD encoder**
   - Option A: Individual CVD encoder
   - Option B: Apply HC common encoder to CVD data

3. **Run optimization** for each θ_orig ∈ [0°, 360°]
   - Grid search or gradient-based optimization
   - Constrain search to perceptually valid range

4. **Generate lookup table**
   - Original color → Display color mapping
   - Option: Fit parametric function (e.g., polynomial) for smoothness

5. **Validate filter**
   - **In silico**: Apply filter to training data, check brain pattern alignment
   - **Psychophysical**: Behavioral color discrimination with filtered stimuli
   - **fMRI validation**: Scan CVD with filtered images, verify HC-like responses

**Success Criteria**:
- Voxel pattern similarity: Procrustes disparity reduction > 50%
- Reconstruction accuracy: Error reduction > 30%
- Perceptual validation: Improved discrimination in Farnsworth-Munsell 100 Hue test

**Expected Outcome**:
- Personalized color lookup tables for each CVD subject
- Proof-of-concept real-time image filter
- Data for psychophysical validation study

**Documents**: `prediction_model/docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`

---

## Legacy Plans (For Reference)

<details>
<summary><b>Original Phase 2B-4 Plans (Click to expand)</b></summary>

These were the original phase plans, now superseded by the 3-phase neural-guided approach above.

### Original Phase 2B: Forward Encoding Model

**Goal**: Learn the explicit mapping from stimulus space → brain space

**Documents**: `docs/methods/NEXT_STEPS_FORWARD_MODEL.md`

### Original Phase 3: Inverse Transformation

**Goal**: Compute stimulus-level color corrections from brain-space differences

**Method**: Regularized least squares inversion of forward model

### Original Phase 4: Deep Learning Filter

**Goal**: End-to-end neural network for optimal CVD color correction

**Architecture**: U-Net style encoder-decoder with multi-objective loss

**Timeline**: Long-term goal (Year 2-3)

</details>

---

## Installation

### Requirements

- Python 3.8+
- Conda (recommended)
- SLURM cluster (for large-scale analysis)

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/yourusername/colorBlind_analysis.git
   cd colorBlind_analysis
   ```

2. **Create conda environment**
   ```bash
   conda env create -f environment.yml
   conda activate nilearn
   ```

3. **Verify installation**
   ```bash
   python -c "import nilearn, nibabel, sklearn; print('Success!')"
   ```

---

## Usage

### Quick Start

See `docs/guides/QUICK_START_*.md` for phase-specific tutorials.

### Example: Running Phase 1 Baseline Analysis

```bash
# 1. Preprocess fMRI data (on SLURM cluster)
sbatch slurm_jobs/preprocessing/run_fmriprep_v2.sbatch

# 2. Extract ROI data and run forward encoding model
conda activate nilearn
python analysis/preprocessing/fir_reconstruction_BH2009_system_clean.py \
    --subject 02 \
    --roi V1 \
    --dataset deoblique_v2

# 3. Analyze results
python scripts/diagnostics/diagnose_qc_results.py
```

### Example: Phase 2A Filter Learning

```bash
# Train filter for CVD subject
python scripts/phase2a_filter_learning/phase2a_train_filter.py \
    --cvd_subject 08 \
    --roi V1 \
    --lambda_rdm 1.0 \
    --lambda_proc 0.5

# Apply filter and visualize results
python scripts/phase2a_filter_learning/apply_filter_with_reconstruction.py \
    --cvd_subject 08 \
    --roi V1
```

---

## Project Structure

```
colorBlind_analysis/
├── README.md                          # This file
├── CLAUDE.md                          # Development guide for Claude Code
├── REORGANIZATION_PLAN.md             # Reorganization plan document
├── .gitignore                         # Git ignore rules
│
├── analysis/                          # Core analysis code (organized by research phases)
│   ├── phase0_preprocessing/         # Preprocessing & ROI extraction (RQ setup)
│   │   ├── fir_reconstruction_BH2009_system_clean.py
│   │   ├── grid_search_preprocessing.py
│   │   └── README.md                 # FIR GLM, forward encoding model
│   │
│   ├── phase1_baseline_decoding/     # RQ1: Neural color discrimination in CVD
│   │   ├── phase1_baseline32_*.py
│   │   ├── phase1_cross_subject_loso.py
│   │   ├── phase1_rsa.py
│   │   └── README.md                 # Classification, reconstruction, RSA
│   │
│   ├── phase2_procrustes_cvd_hc/     # RQ2: Individual heterogeneity (3D characterization)
│   │   ├── option2b_procrustes_alignment.py    # SRQ1: Shared decoder validation
│   │   ├── option2d_procrustes_cvd_comparison.py
│   │   ├── reconstruction_with_procrustes*.py
│   │   ├── visualize_*disparity*.py
│   │   └── README.md                 # Procrustes analysis, magnitude/sign/structure
│   │
│   ├── phase3_procrustes_filter/     # RQ3: Neural-guided personalized filter design
│   │   └── README.md                 # Current filter work (retrospective validation)
│   │                                 # Main code in scripts/phase2a_filter_learning/
│   │
│   ├── future_phase1_hyperalignment/ # SRQ2: HC common space via trial-aligned GPA
│   │   └── README.md                 # Planned: Trial-wise pattern extraction & hyperalignment
│   │
│   ├── future_phase2_forward_model/  # SRQ3: Continuous hue interpolation (0-360°)
│   │   └── README.md                 # Planned: Channel-based encoder, LOCO validation
│   │
│   ├── future_phase3_filter_optimization/  # SRQ4: 360° filter search
│   │   └── README.md                 # Planned: Dual-constraint optimization, LUT generation
│   │
│   ├── feature_selection/            # Feature selection methods
│   │   ├── feature_selection_anova.py
│   │   ├── feature_selection_rfe.py
│   │   └── feature_selection_pca.py
│   │
│   ├── group_level/                  # Legacy group-level analysis scripts
│   ├── utils/                        # Shared utilities
│   └── visualization/                # Visualization tools
│
├── scripts/                           # Phase-specific analysis scripts
│   ├── phase2a_filter_learning/      # Phase 3 (RQ3) filter optimization scripts
│   │   ├── phase2a_train_filter.py
│   │   ├── apply_filter_with_reconstruction.py
│   │   ├── visualize_rdm_*.py
│   │   └── ... (28 files total)
│   │
│   ├── diagnostics/                  # QC and diagnosis scripts
│   │   ├── diagnose_qc_results.py
│   │   ├── check_roi_quality_comparison.py
│   │   └── ... (10 files total)
│   │
│   └── phase1_baseline/              # (Empty - for future baseline scripts)
│
├── slurm_jobs/                        # SLURM batch scripts for server execution
│   ├── preprocessing/                # fMRIPrep, ROI extraction jobs
│   │   └── run_fmriprep*.sbatch (19 files)
│   ├── analysis/                     # Analysis jobs
│   │   └── run_procrustes*.sbatch
│   └── qc/                           # Quality control jobs
│       └── qc_runwise*.sh (4 files)
│
├── docs/                              # Documentation
│   ├── guides/                       # User guides (6 files)
│   │   ├── QC_EXECUTION_GUIDE.md
│   │   ├── QUICK_REFERENCE.md
│   │   └── PROCRUSTES_RECONSTRUCTION_QUICKSTART.md
│   │
│   ├── methods/                      # Methodology documents (existing)
│   │   ├── PHASE1_RESULTS_ANALYSIS.md
│   │   ├── PHASE2A_FILTER_METHODS.md
│   │   ├── PROCRUSTES_ANALYSIS_GUIDE.md
│   │   └── ROBUSTNESS_VALIDATION_METHODS.md
│   │
│   ├── technical/                    # Technical reports (1+ files)
│   │   ├── FMRIPREP_VERSION_COMPARISON.md
│   │   └── MNI_DIAGNOSIS_FINAL_REPORT.md
│   │
│   ├── results/                      # Results summaries (5 files)
│   │   ├── BASELINE_RESULTS_SUMMARY.md
│   │   ├── CVD_ANALYSIS_FINAL.md
│   │   └── FINAL_REPORT_WITH_VISUALIZATION.md
│   │
│   ├── paper/                        # Manuscript (Korean version)
│   │   ├── main_kr.tex
│   │   ├── main_kr.pdf
│   │   └── figures/
│   │
│   └── archive/                      # Outdated/legacy documents
│       ├── trial_options/
│       └── OHBM_abstract/
│
├── prediction_model_workspace/        # ⚠️ ACTIVE WORKSPACE (Experimental)
│   ├── README.md                     # Workspace usage rules
│   ├── MASTER_PLAN.md                # 3-phase development plan
│   ├── docs/                         # Detailed documentation (work-in-progress)
│   │   ├── PHASE1_HYPERALIGNMENT.md
│   │   ├── PHASE2_PREDICTION_MODEL.md
│   │   ├── PHASE3_CVD_FILTER_OPTIMIZATION.md
│   │   ├── overall.png, phase1-3.png  # Pipeline diagrams
│   │   └── PROGRESS_LOG.md           # Development log
│   ├── scripts/                      # Experimental scripts
│   ├── final/                        # Completed code (ready for analysis/)
│   │   ├── phase1/                   # → ../analysis/phase1_hyperalignment/
│   │   ├── phase2/                   # → ../analysis/phase2_forward_model/
│   │   └── phase3/                   # → ../analysis/phase3_filter_optimization/
│   └── results/                      # Intermediate results (gitignored)
│
├── materials/                         # Stimuli and atlases
├── papers/                            # Reference papers
│
├── results/                           # Analysis outputs (gitignored)
├── derivatives/                       # Processed fMRI data (gitignored)
└── logs/                              # Log files (gitignored)
```

### Key Directories

**analysis/** - Organized by research phases (RQ1→RQ2→RQ3→Future SRQ1-4)
- Each phase has its own README explaining methods, results, and connections
- Phase 0-3: Completed research questions
- Future Phase 1-3: Planned (currently in development in `prediction_model_workspace/`)

**prediction_model_workspace/** - ⚠️ **ACTIVE EXPERIMENTAL WORKSPACE**
- **Role**: Development and experimentation for Future Phase 1-3
- **NOT final analysis**: Work-in-progress scripts, intermediate results
- **Migration rule**: Completed phases move from `workspace/final/phase*/` → `analysis/phase*/`
- **Documentation**: Full details in `prediction_model_workspace/README.md`

**scripts/** - Executable analysis scripts organized by function
**slurm_jobs/** - Server batch scripts for preprocessing and analysis
**docs/** - Comprehensive documentation organized by type

### Important Notes

**⚠️ For collaborators working on Future Phases 1-3:**
- Primary workspace: `prediction_model_workspace/`
- Track progress: `prediction_model_workspace/docs/PROGRESS_LOG.md`
- Final code staging: `prediction_model_workspace/final/phase*/`
- Do NOT directly modify `analysis/future_phase*/` (minimal planning READMEs only)

**When a Future Phase is completed:**
1. Finalize code in `workspace/final/phase*/`
2. Copy to `analysis/future_phase*/`
3. Rename `analysis/future_phase*` → `analysis/phase*` (remove "future_" prefix)
4. Update README with final results

See individual phase READMEs in `analysis/phase*/README.md` for detailed methodology.

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
│   │   └── ... (8 runs total)
│   └── fmap/
│       └── sub-01_fieldmap.nii.gz
└── ... (sub-02 through sub-10)
```

### Stimulus Information

- **Colors**: 8 isoluminant colors equally spaced in CIELAB (L*=70)
- **Presentation**: RSVP at 2 Hz (500ms/stimulus)
- **Runs**: 8 runs × 60 trials/color = 480 trials per color
- **Duration**: ~25 min per run

See `materials/` for stimulus generation code.

---

## References

### Key Papers

1. **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
   - Foundation for our forward encoding model approach

2. **Haxby, J. V., Connolly, A. C., & Guntupalli, J. S. (2014).** Decoding neural representational spaces using multivariate pattern analysis. *Annual Review of Neuroscience*, 37, 435-456.
   - Theoretical framework for MVPA

### Additional References

- See `docs/paper/main_kr.tex` for complete bibliography
- Key papers available in `papers/` directory

---

**Last Updated**: 2026-01-04
