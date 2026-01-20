# 단계별 판단 및 실행 파이프라인 가이드

**목적**: Step 1.2 결과부터 Phase 3 완료까지의 의사결정 트리 및 실행 순서

**마지막 업데이트**: 2026-01-08

---

## 📊 현재 상태: Step 1.2 Reliability Check 실행 중

**위치**: `prediction_model_workspace/scripts/run_01_reliability_comparison.sbatch`
**작업**: 10 subjects × 4 ROIs = 40개 결과 생성 중

---

## 🔀 Step 1.2 완료 후 의사결정 플로우

### **결과 확인**

```bash
# 서버에서 aggregation 실행
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts
eval "$(conda shell.bash hook)"
conda activate nilearn

python aggregate_reliability_results.py \
    --input_dir ../results/reliability_check \
    --output_dir ../results/reliability_check

# 요약 확인
cat ../results/reliability_check/reliability_summary.txt
```

### **Decision Rules (Procrustes Stability 기준)**

40개 subject-ROI 조합 각각에 대해:

| Procrustes Stability | Decision | Action |
|---------------------|----------|--------|
| **≥ 0.80** | ✅ **PROCEED** | Step 1.3 진행 |
| **0.70 - 0.80** | ⚠️ **PROCEED_WITH_CAUTION** | Step 1.3 진행 (품질 모니터링) |
| **< 0.70** | ❌ **IMPROVE_GLM** | Preprocessing 개선 후 재실행 |

---

## 📋 Phase 1: Trial-aligned Hyperalignment (Week 2-3)

### **Step 1.3: LS-S GLM 실행** ⬅️ **다음 단계**

**조건**: Step 1.2에서 대부분 PROCEED 받은 경우

**목적**: Stimulus-wise beta 추출 (384 trials per subject-ROI)

**Input**:
- fMRIPrep BOLD files: `fmriprep_out_original_v3/sub-{ID}/func/*_bold.nii.gz`
- Events files: `bids_editted/sub-{ID}/func/*_events.tsv`
- Confounds: `*_desc-confounds_timeseries.tsv`

**Output**:
```
derivatives/trial_wise_glm/original_v3/sub-{ID}_{ROI}/
├── stimulus_wise_betas.npy    # (384, n_voxels)
├── trial_metadata.csv          # Trial info
└── quality_metrics.json        # SNR, reliability
```

**스크립트**: `02_trial_wise_glm.py` (아직 미작성)

**실행**:
```bash
# TODO: 스크립트 작성 필요
python 02_trial_wise_glm.py \
    --subject 01 \
    --roi V1 \
    --method LS-S \
    --confounds motion
```

**예상 시간**: 1-2시간 per subject-ROI

**Decision Point #1: Trial-wise SNR Check**
- **Procrustes stability < 0.50**: ❌ STOP → Smoothing 증가 (6mm → 8mm)
- **Procrustes stability ≥ 0.50**: ✅ PROCEED to Step 1.4

---

### **Step 1.4: Trial-aligned GPA (Hyperalignment)**

**조건**: Step 1.3 완료, SNR 충분

**목적**: HC 7명의 trial-wise patterns을 공통 공간으로 정렬

**Input**:
- `stimulus_wise_betas.npy` (HC 7명, 4 ROIs)
- Trial metadata

**Method**:
- Generalized Procrustes Analysis (GPA)
- HC-only learning (CVD 배제)
- Full voxel space (NO PCA)
- Regularized orthogonal transformations

**Output**:
```
results/alignment_quality/
├── X_common.npy                # (384, n_voxels) - HC common space
├── R_list.pkl                  # List of rotation matrices (7 subjects)
├── alignment_metrics.json      # ISC, LOSO, disparity
└── figures/alignment_quality.png
```

**스크립트**: `03_trial_aligned_gpa.py`

**실행**:
```bash
python 03_trial_aligned_gpa.py \
    --roi V1 \
    --hc_subjects 01 02 03 04 05 06 07 \
    --regularization 0.1
```

**Success Criteria (2-Tier)**:

**Tier-1: Trial-level**
- Inter-subject correlation (ISC) > 0.30
- LOSO decoding accuracy > 25% (chance: 12.5%)

**Tier-2: Color-level**
- Procrustes disparity < 0.08
- Run-split stability > 0.80
- RDM correlation > 0.30

**Decision Point #2: Alignment Quality**
- **Tier-1 실패**: ❌ Adjust regularization or smoothing
- **Tier-2 실패**: ⚠️ CAUTION - Proceed but monitor
- **Both pass**: ✅ PROCEED to Step 1.5

---

### **Step 1.5: Common W 재학습**

**목적**: 정렬된 HC common space에서 shared decoder 학습

**Input**:
- `X_common.npy` (aligned HC data)
- Trial labels

**Output**:
```
results/alignment_quality/
├── W_common_hyperaligned_V1.npy    # Common weights
└── loro_cv_results.json            # Reconstruction errors
```

**Evaluation**: LORO-CV reconstruction error ≤ baseline (32° for V1)

**Decision Point #3: Downstream Performance**
- **Error > baseline + 10°**: ❌ Alignment hurts performance
- **Error ≈ baseline**: ✅ No harm, proceed
- **Error < baseline**: ✅✅ Performance gain!

---

## 📋 Phase 2: Continuous Hue Interpolation (Week 3-4)

### **Step 2.1: Population Encoder**

**조건**: Phase 1 완료, HC common space 구축됨

**목적**: 360° 연속 색조 공간에서 임의 hue 예측

**Method**: Channel-based encoding (6 half-wave rectified channels)

**Input**:
- `X_common.npy` (HC common space)
- 8 measured colors (0°, 45°, ..., 315°)

**Output**:
```
results/prediction_validation/
├── W_enc_population.npy        # (6, n_voxels) encoder weights
├── predictions_360.npy         # (360, n_voxels) dense predictions
├── loco_cv_results.json        # Hold-out validation
└── figures/rdm_smoothness.png
```

**스크립트**: `05_channel_encoder_population.py`

**Success Criteria**:
- ✅ LOCO CV error < 60° (chance: 90°)
- ⭐ LOCO CV error < 45° (excellent)

---

### **Step 2.2: Individual Encoder (HC Verification)**

**목적**: Population encoder의 일반화 검증

**Method**: 각 HC subject별 개별 encoder 학습 후 population과 비교

**Decision Point #4: Population vs Individual**
- **Individual >> Population**: ⚠️ Population 불안정 → Regularization 필요
- **Individual ≈ Population**: ✅ Good generalization
- **Individual < Population**: ✅✅ Excellent! (Unlikely)

---

### **Step 2.3: Regularization Comparison**

**목적**: Overfitting 방지 및 일반화 향상

**Methods**: None (OLS), Ridge, Lasso

**Evaluation**: LOCO CV error 비교

**Best method 선택** → Phase 3에서 사용

---

### **Step 2+ (Optional): MLP Encoder**

**실행 조건**:
- Linear LOCO error > 50°, OR
- RDM smoothness < 0.5

**If skipped**: Linear encoder 사용 → Phase 3

---

## 📋 Phase 3: CVD Filter Optimization (Week 5-6)

### **Step 3.1: CVD Individual Encoder (Mandatory)**

**조건**: Phase 2 완료

**목적**: CVD 3명 각각의 channel encoder 학습

**Method**:
1. CVD → HC common space projection (Procrustes)
2. CVD individual encoder 학습 (Best regularization from Phase 2)

**Output**:
```
results/cvd_analysis/
├── W_enc_cvd_08.npy
├── W_enc_cvd_09.npy
├── W_enc_cvd_10.npy
└── cvd_vs_hc_comparison.json
```

---

### **Step 3.2: Loss Function Ablation (4-way)**

**목적**: Dual-constraint optimization의 최적 균형 찾기

**Loss Function**:
```
θ_display = argmin_θ [
    α * ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²     # Loss 1: Voxel matching
    + β * ||Decode(Ŷ_cvd(θ)) - θ_orig||²  # Loss 2: Reconstruction
]
```

**4 Scenarios**:
1. α=1.0, β=0.0 (Voxel only)
2. α=0.0, β=1.0 (Reconstruction only)
3. α=0.5, β=0.5 (Equal)
4. Optuna optimization (data-driven)

**Output**:
```
results/filter_validation/
├── filter_cvd08_scenario1.npy  # (360,) lookup table
├── filter_cvd08_scenario2.npy
├── filter_cvd08_scenario3.npy
├── filter_cvd08_scenario4.npy
└── ablation_comparison.csv
```

**Decision Point #5: Best Scenario**
- 4가지 scenario 중 best performer 선택
- Criteria: smoothness, reconstruction error, inter-CVD consistency

---

### **Step 3.3: Filter Validation (In-Silico)**

**Tier 1 Validation** (Current scope):
1. Filter smoothness < 2.0°/deg
2. Reconstruction error ≤ baseline (32°)
3. Inter-CVD consistency < 10°

**Tier 2 Validation** (Future work, 보류):
- Measure CVD responses to filtered stimuli (requires new experiment)

**Final Deliverable**:
```
results/filter_validation/
├── filter_cvd08_final.npy      # Lookup table (360°)
├── filter_cvd09_final.npy
├── filter_cvd10_final.npy
├── validation_report.pdf
└── figures/filter_visualization.png
```

---

## 🛠️ 스크립트 개발 상태

| Script | Status | Description |
|--------|--------|-------------|
| `00_check_data_structure.py` | ✅ Done | Trial order consistency check |
| `01_reliability_comparison.py` | ✅ Done | Step 1.2: Baseline vs trial-wise |
| `aggregate_reliability_results.py` | ✅ Done | Results aggregation |
| `02_trial_wise_glm.py` | ❌ TODO | Step 1.3: LS-S GLM |
| `03_trial_aligned_gpa.py` | ❌ TODO | Step 1.4: Hyperalignment |
| `04_evaluate_alignment.py` | ❌ TODO | Step 1.5: 2-tier evaluation |
| `05_channel_encoder_population.py` | ❌ TODO | Phase 2.1 |
| `06_channel_encoder_individual.py` | ❌ TODO | Phase 2.2 |
| `07_regularization_comparison.py` | ❌ TODO | Phase 2.3 |
| `08_mlp_encoder.py` | ❌ TODO | Phase 2+ (optional) |
| `09_loco_cv.py` | ❌ TODO | LOCO validation |
| `10_continuous_interpolation.py` | ❌ TODO | 360° predictions |
| `11_cvd_projection.py` | ❌ TODO | Phase 3.1: CVD encoder |
| `12_filter_optimization.py` | ❌ TODO | Phase 3.2: Optimization |
| `13_loss_ablation.py` | ❌ TODO | Phase 3.2: 4-way ablation |
| `14_filter_validation.py` | ❌ TODO | Phase 3.3: Validation |

---

## 🚨 Critical Decision Points Summary

| Point | Condition | Action if Fail | Action if Pass |
|-------|-----------|----------------|----------------|
| **DP#1** | Trial SNR < 0.50 | Increase smoothing | → Step 1.4 |
| **DP#2** | Alignment quality fail | Adjust parameters | → Step 1.5 |
| **DP#3** | Error > baseline+10° | Review alignment | → Phase 2 |
| **DP#4** | Individual >> Population | Add regularization | Continue |
| **DP#5** | Choose best scenario | - | → Validation |

---

## 📅 예상 타임라인 (1명 기준)

| Phase | Step | Duration | Cumulative |
|-------|------|----------|------------|
| Phase 1 | Step 1.2 (현재) | 2-4 hours | 2-4h |
| Phase 1 | Step 1.3 (LS-S) | 1-2 days | 1-2 days |
| Phase 1 | Step 1.4 (GPA) | 1 day | 2-3 days |
| Phase 1 | Step 1.5 (Eval) | 0.5 day | 2-4 days |
| Phase 2 | Step 2.1-2.3 | 3-5 days | 5-9 days |
| Phase 3 | Step 3.1-3.3 | 3-5 days | 8-14 days |
| **Total** | | **2-3 weeks** | |

---

## 🎯 다음 즉시 액션

1. **현재 (2026-01-08)**: Step 1.2 job 완료 대기
2. **결과 확인**: `reliability_summary.txt` 확인
3. **Decision**: 대부분 PROCEED면 → Step 1.3 스크립트 작성
4. **If IMPROVE_GLM**: Smoothing 8mm로 Step 1.2 재실행

---

## 📖 상세 문서 참조

- **전체 계획**: `MASTER_PLAN.md`
- **Phase 1 상세**: `docs/PHASE1_HYPERALIGNMENT.md`
- **Phase 2 상세**: `docs/PHASE2_PREDICTION_MODEL.md`
- **Phase 3 상세**: `docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`
- **진행 기록**: `docs/PROGRESS_LOG.md`
