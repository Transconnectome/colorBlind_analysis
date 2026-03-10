# Future Phase 1: Group-Prior Prediction Model

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-03-08
> **대상**: Future Phase 1 Forward Model — Group-Prior 기반 Prediction Model 구축 및 검증
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4
> **목적**: HC group prior를 활용한 subject-specific prediction model W_s 학습

---

## 1. 핵심: Prediction은 Procrustes Space에서 한다

### 1a. 결론

Prediction model의 **본체**는 Procrustes voxel space에서 작동한다. SRM은 prediction 공간도 evaluation 공간도 아닌, **prior-construction helper**로만 사용된다.

핵심 목표:
1. Prediction은 Procrustes voxel space에서 한다
2. Group prior는 공통공간을 잠깐 거쳐 만든다
3. 최종적으로는 target subject용 하나의 W_s만 학습한다

### 1b. 왜 SRM은 prediction 공간으로 부적합한가

LOCO MAE 비교 (핵심 증거):

| ROI | Procrustes | SRM | Delta |
|-----|-----------|-----|-------|
| V1 | ~76° | ~80° | +4° |
| V2 | ~80° | ~85° | +5° |
| V3 | ~77° | **~99°** | **+22° (chance 90°보다 worse)** |
| hV4 | ~69° | ~72° | +3° |

4가지 이유 요약:
1. **SRM은 interpolation 구조를 파괴** — V3에서 chance보다 나쁨
2. **SRM은 stimulus → representation mapping이 아님** — voxel → latent만 학습
3. **SRM filter는 stimulus control 불가** — latent → latent, 아닌 theta → theta' 필요
4. **SRM은 cross-subject alignment에는 유효** — prior construction에만 활용

**SRM = prior-construction helper로 역할 재정의**

---

## 2. 기호 정리

각 subject *s*, ROI *r*에 대해:

| 기호 | Shape | 의미 |
|------|-------|------|
| V_s | scalar | subject s의 voxel 수 (subject마다 다름) |
| N | scalar | 조건 수 (= 8 colors, 또는 8 × 6 = 48 if run-level) |
| K | scalar | Basis channel 수 (= 6) |
| Y_s | V_s × N | Procrustes-aligned voxel response (`amplitudes_procrustes.npy`) |
| C | K × N | 색 basis matrix (half-wave rectified cosine, BH2009) |
| W_s | V_s × K | **학습 대상**: subject-specific encoding weight |
| k | scalar | SRM latent 차원 (V1=4, V2=4, V3=3, hV4=3) |
| R_s | V_s × k | SRM projection matrix (`srm.w_` from BrainIAK) |
| Z_i | k × N | HC subject i의 공통공간 response |
| A_i | k × K | HC subject i의 공통공간 encoding weight |
| A_g | k × K | **Group prior** (HC A_i의 평균) |
| W_{0,s} | V_s × K | target subject voxel space로 투사된 prior weight |

**Prediction equation**:

```
Y_hat_s = W_s @ C
```

> **Transpose 주의**: 기존 코드 (loco_baseline.py, group_prior.py)는 W ∈ R^{K×V_s} (channels × voxels) convention을 사용. 이 문서는 W_s ∈ R^{V_s×K} (voxels × channels)를 사용. 구현 시 transpose 필요.

---

## 3. 왜 직접 섞으면 안 되는가

원래 하고 싶었던 것:

```
W_mix = alpha * W_group + (1 - alpha) * W_subject
```

**이것은 안 된다.** Subject마다 voxel 수가 다르기 때문이다:

```
W_group   ∈ R^{V_g × K}
W_subject ∈ R^{V_s × K}
```

V_g ≠ V_s이므로 같은 공간의 행렬이 아니다. 덧셈 자체가 정의되지 않는다.

> **기존 `group_prior.py`의 문제**: `analysis/phase3_decoder_comparing/model_comparison_validation/scripts/group_prior.py`는 이 문제를 `amplitudes_srm.npy` (SRM 공간)에서 작업함으로써 우회한다. 즉 `W = λ·W_ind + (1-λ)·W_group`을 SRM 공간에서 수행. 하지만 이는 Procrustes 원칙을 위반 — SRM이 interpolation 구조를 파괴하므로, SRM 공간에서의 mixing은 연속 보간 품질을 보장하지 못한다.

**해결 방향**:
1. 공통공간에서 prior를 만든 뒤
2. 그 prior를 target subject voxel space로 내려보내고
3. 그 prior를 중심으로 target subject의 W_s 하나만 학습

---

## 4. 전체 알고리즘

전체는 4단계이다.

### Step A: HC 공통공간 적합

HC subject i = 1, ..., M (M = 7)에 대해, Procrustes-aligned data:

```
Y_i ∈ R^{V_i × N}
```

SRM을 적합하여 각 subject에 대한 projection matrix 획득:

```
R_i ∈ R^{V_i × k}
```

공통공간 response 계산:

```
Z_i = R_i^T @ Y_i ∈ R^{k × N}
```

즉 subject마다 다른 voxel 수(V_i)를 가진 data를 모두 같은 k-차원 공간으로 보낸다.

**Source**: BrainIAK SRM, HC-only training. k 값: V1=4, V2=4, V3=3, hV4=3.

### Step B: 공통공간에서 Group Prior 학습

각 HC subject에 대해, 공통공간에서 색 basis C로부터 latent response Z_i를 예측하는 encoding 학습:

```
A_i = argmin_A ||Z_i - A @ C||_F^2 + lambda_A * ||A||_F^2
```

여기서 A_i ∈ R^{k × K}. 즉 A_i는 공통공간에서의 encoding weight이다.

Group prior를 평균:

```
A_g = (1/M) * sum_{i=1}^{M} A_i
```

**기본값**: 단순 평균 (omega_i = 1/M).

**선택적 가중 변형**: omega_i = r_sh(i) / sum_j r_sh(j), 여기서 r_sh(i)는 subject i의 현재 ROI에 대한 split-half RDM reliability. 이는 noisy한 representation을 가진 subject의 가중치를 낮춘다.

**권고**: 단순 평균으로 시작. M=7에서 한 명의 noisy subject는 평균에 제한적 영향만 미친다. Leave-one-out 분석에서 한 subject가 A_g 품질을 과도하게 저하시킬 때만 가중 평균으로 전환.

### Step C: Target Subject 공간으로 Prior 투사

Target subject s에 대해, 동일한 공통공간 변환 R_s ∈ R^{V_s × k}를 얻었다고 하자.

Group prior를 target subject voxel space로 투사:

```
W_{0,s} = R_s @ A_g ∈ R^{V_s × K}
```

차원 확인:
- R_s: V_s × k
- A_g: k × K
- W_{0,s}: V_s × K

**이것이 핵심이다**: voxel 수가 달라도, 공통공간을 거치면 target subject용 prior W_{0,s}를 만들 수 있다.

HC subject의 경우 R_s는 SRM fitting에서 직접 얻어진다. CVD/신규 subject의 경우 SVD-based projection을 사용한다 (Phase 2 `rerun_loo_consistent.py` 참조).

### Step D: Target Subject 데이터로 Fine-Tuning

최종적으로 학습하는 것은 **하나의 행렬** W_s ∈ R^{V_s × K}:

```
W_s = argmin_W ||Y_s - W @ C||_F^2 + lambda * ||W - W_{0,s}||_F^2
```

이 식의 의미:
- **첫째 항** `||Y_s - W @ C||²`: target subject 실제 데이터에 맞추기
- **둘째 항** `lambda * ||W - W_{0,s}||²`: group prior에서 너무 멀리 벗어나지 않기

즉 **prior-centered ridge** (= fine-tuning / shrinkage)이다.

### Closed-Form 해

이 식은 해석적으로 풀 수 있다. Normal equation:

```
W_s @ (C @ C^T + lambda * I) = Y_s @ C^T + lambda * W_{0,s}
```

따라서:

```
W_s = (Y_s @ C^T + lambda * W_{0,s}) @ (C @ C^T + lambda * I)^{-1}
```

**이것이 가장 깔끔한 최종식이다.**

### lambda의 의미

lambda가 group prior와 individual information의 비율을 제어한다:

| lambda | 의미 | W_s |
|--------|------|-----|
| 0 | Pure subject-specific fit | OLS (기존 baseline과 동일) |
| 작은 값 | Individual 위주 + 약간의 prior regularization | Subject data 중심 |
| 적정 값 | Group prior와 individual data의 최적 균형 | **이것을 찾는 것이 목표** |
| → ∞ | 거의 group prior만 따름 | W_s ≈ W_{0,s} (zero-shot transfer) |

---

## 5. Validation 구조

이 모델은 반드시 **Procrustes voxel space**에서 평가한다. Prediction의 본체가 Y_hat = W_s @ C이기 때문이다.

### A. LORO: 새로운 Run Generalization

**질문**: 같은 subject에서 새로운 run에도 prediction이 유지되는가?

**절차**:
1. Target subject의 5 runs로 W_s 학습
2. Held-out 1 run의 Y_s^{test}와 비교

**Metric**: r_LORO = corr(v_pred, v_real) — held-out run의 특정 색에 대한 voxel pattern vector 간 상관

### B. LOCO: 새로운 Color Interpolation

**질문**: 훈련에 없는 색도 예측 가능한가?

**절차**:
1. Target color 제외
2. 7색으로 W_s 학습
3. Held-out color의 voxel pattern 예측

**Metric**:
- r_LOCO = corr(v_pred, v_real)
- MAE_LOCO = angular decoding error (circular mean absolute error)

이것이 현재 filter pipeline과 가장 직접적으로 연결되는 validation이다.

### C. LOSO: 새로운 Subject Transfer

**질문**: Target subject 정보가 없거나 적을 때 group prior만으로 얼마나 가능한가?

세 조건:

| 조건 | 수식 | 의미 |
|------|------|------|
| Zero-shot | W_s = W_{0,s} | Prior만으로 예측 (target subject 데이터 없음) |
| Few-shot / fine-tuned | argmin ||Y_s - WC||² + lambda·||W - W_{0,s}||² | Prior + target subject data |
| Subject-only baseline | argmin ||Y_s - WC||² | Target subject data만 (prior 없음) |

---

## 6. 추천 Metrics

Prediction model의 primary metric은 decoding accuracy가 아니라 voxel-level prediction quality이다.

| 우선순위 | Metric | 수식 | 용도 |
|---------|--------|------|------|
| **1차** | Voxel prediction correlation | corr(v_pred, v_real) | Primary quality measure |
| **2차** | Explained variance | R² = 1 - ||v - v_hat||² / ||v - v_bar||² | Variance accounted for |
| **3차** | LOCO angular MAE | MAE_LOCO | Interpolation 정확도 |
| **4차** | Predicted vs real RDM correlation | corr(RDM_pred, RDM_real) | Geometry 보존 (보조 metric) |
| **5차** | Normalized geometry fit | corr(RDM_pred, RDM_real) / RDM_ceiling | Ceiling 대비 성능 |

### Reliability-Aware Support Metrics

Reviewer가 반드시 묻는 질문: **"이 ROI의 geometry 자체가 noisy한데 모델이 못 맞춘 건가, 아니면 데이터 한계인가?"**

이에 답하려면 noise ceiling이 필요하다.

| Metric | 수식 | 용도 |
|--------|------|------|
| RDM noise ceiling | Upper: corr(RDM_single_run, RDM_group_mean). Lower: corr(RDM_LOO_mean, RDM_full_mean) | 측정 noise를 감안한 최대 달성 가능 RDM correlation |
| Normalized fit | corr(RDM_pred, RDM_real) / RDM_ceiling | 데이터 품질 대비 모델 품질 — ROI간 공정한 비교 가능 |
| Split-half geometry reliability | corr(RDM_odd_runs, RDM_even_runs) | Subject × ROI별 데이터 품질 |

**왜 중요한가**: Noise ceiling 없이는 ROI 비교가 데이터 품질과 모델 품질을 혼동한다. V4가 V1보다 좋아 보여도, 이것이 모델이 좋은 건지 V4 RDM이 더 reliable한 건지 구분할 수 없다. Normalized fit은 이 혼동을 제거한다.

**핵심 전환**: Prediction model 평가를 "absolute performance"에서 **"ceiling 대비 performance"**로 확장.

---

## 7. Encoding Basis Ablation

**질문**: 왜 6-channel cosine tuning인가? 다른 basis가 더 좋을 수 있는가?

| Model | Stimulus basis | K | 설명 |
|-------|---------------|---|------|
| FE-6 | Half-wave rectified cosine | 6 | Brouwer & Heeger (2009), 현재 기본값 |
| LF-4 | Low-frequency Fourier | 4 | cos(θ), sin(θ), cos(2θ), sin(2θ) |
| LF-6 | Low-frequency Fourier | 6 | 3차 harmonic까지 |

모든 모델의 prediction target은 동일하다: `Y_hat_s = W_s @ C` (C만 basis에 따라 다름).

**평가**: Section 6과 동일한 metrics (voxel correlation, R², LOCO MAE, RDM correlation, normalized fit)을 각 basis × 각 CV protocol에 적용.

**핵심 질문**:
- 6-channel tuning이 정말 필요한가, 아니면 4-parameter 모델로 충분한가?
- CVD distortion이 주로 low-frequency axis distortion인가?
- Fourier basis가 downstream filter 매개변수화 (T_psi가 Fourier 항을 사용)와 더 잘 맞는가?

**기대 효과**: 이 실험은 **encoding model 구조의 정당화**를 제공한다.

### 권장 2-Stage 설계

**Stage 1 — Basis screening** (고정 모델: Subject-only OLS):

|         | LORO r         | LOCO r         | LOCO MAE       |
|---------|----------------|----------------|----------------|
|         | V1  V2  V3  V4 | V1  V2  V3  V4 | V1  V2  V3  V4 |
| FE-6    |  .   .   .   . |  .   .   .   . |  .   .   .   . |
| LF-4    |  .   .   .   . |  .   .   .   . |  .   .   .   . |
| LF-6    |  .   .   .   . |  .   .   .   . |  .   .   .   . |

값: 10명 피험자의 mean ± SEM. Bold = 열별 최고값.

**Stage 2 — Full model comparison**: Stage 1에서 선정된 winning basis로 수행.
→ §8 비교 실험으로 진행.

**근거**: Full factorial (3 × 5 × 3 × 4 = 180 cells)은 N=10으로 해석이 불가능하다. 2단계로 분리하면 encoding-basis 질문을 먼저 해결한 후 모델 복잡성을 추가할 수 있다.

---

## 8. 비교 실험 설계

**Design**: 5 models × 3 CV protocols × 4 ROIs (× 3 encoding bases 선택적)

### Models

| Model | Regularization | W_s | 목적 |
|-------|---------------|-----|------|
| Subject-only OLS | lambda = 0 | OLS fit, regularization 없음 | Baseline |
| Standard Ridge | ||W||² (zero 방향 shrink) | Ridge with GCV-selected alpha | 일반적 shrinkage로 충분한지 확인 |
| Prior-only | lambda → ∞ | W_{0,s} = R_s @ A_g | Zero-shot group prior transfer |
| Prior + fine-tuning | ||W - W_{0,s}||² | Closed-form with optimal lambda | **제안 방법** |
| Standard Ridge + GCV | ||W||² with analytical alpha | GCV 선택 (기존 loco_ridge.py) | 가장 강력한 simple baseline |

> **왜 Standard Ridge가 핵심인가**: Prior-centered ridge (||W - W_{0,s}||²)가 standard ridge (||W||²)를 유의미하게 이기지 못하면, SRM-mediated prior construction은 불필요한 복잡성이다. 이 비교는 generic regularization과 prior의 기여를 분리한다.

### CV Protocols

| Protocol | Held-out | 학습 데이터 |
|----------|----------|-----------|
| LORO | 1 run | 5 runs (같은 subject, 8 colors 전체) |
| LOCO | 1 color | 6 runs × 7 colors (같은 subject) |
| LOSO | 1 subject | 전체 HC data (group prior transfer) |

### 기대 결과

- **Prior-only > Subject-only OLS**: subject data가 부족한 LOSO에서 기대
- **Prior + fine-tuning >= Standard Ridge**: 모든 조건에서 기대 (prior가 generic shrinkage 이상의 structured regularization 제공)
- **Prior + fine-tuning >> Subject-only OLS**: CVD subject에서 특히 기대 (group prior가 noisy individual estimate를 regularize)
- **Standard Ridge > Subject-only OLS**: LOCO에서 기대 (작은 training set가 regularization 혜택)

### Results Table (target)

```
                  LORO (r)    LOCO (r)    LOCO (MAE)    LOSO (r)
                  HC   CVD    HC   CVD    HC    CVD     HC   CVD
subject-only OLS   .    .     .    .     .      .      N/A   .
standard ridge     .    .     .    .     .      .      N/A   .
prior-only         .    .     .    .     .      .       .    .
prior+finetune     .    .     .    .     .      .       .    .
ridge+GCV          .    .     .    .     .      .      N/A   .
```

× 4 ROIs (V1, V2, V3, hV4)

---

## 9. Gate Criteria

ROI가 downstream filter 설계에 **사용 가능**하려면 세 가지 독립 조건을 만족해야 한다:

| Criterion | Metric | Threshold | 목적 |
|-----------|--------|-----------|------|
| Geometry reliability | Split-half RDM correlation | > 0.3 | 데이터 품질이 모델 학습에 충분한가 |
| Prediction quality | Normalized geometry fit (pred RDM corr / ceiling) | > 0.3 | 모델이 가용 구조를 포착하는가 |
| Interpolation stability | LOCO voxel correlation (prior+finetune 모델) | > 0 (chance 이상, p < 0.05 by permutation) | 미보유 색에 대한 일반화 가능한가 |

**Gate rule**: 3개 모두 만족 → PASS. Criterion 1 실패 → 데이터 자체가 noisy (모델 문제 아님). Criteria 2-3 실패 → 모델 개선 필요.

**기존 gate 대비 장점**: 이전 gate는 5개 structural metrics의 absolute threshold (MAE < 90°, trajectory r > 0.6 등)를 사용 — 데이터 품질과 모델 품질을 혼동했다. 새 gate는 이를 분리: reliability는 데이터에 대한 정보, normalized fit은 모델에 대한 정보.

즉 **reliability + predictability + interpolation** 세 조건을 동시에 본다.

### Failure Analysis Protocol

ROI가 gate를 통과하지 못할 때, *왜* 실패했는지 진단한다:

| Gate 실패 | 해석 | 진단 방법 |
|---|---|---|
| Criterion 1 (reliability < 0.3) | 데이터가 너무 noisy | 모델로 해결 불가 — 더 나은 데이터나 추가 run 필요 |
| Criterion 2 (normalized fit < 0.3) | 모델이 구조를 거의 포착하지 못함 | Per-channel encoding quality: corr(W_s[:,k] @ C[k,:], Y_s) per channel k — 어떤 basis channel이 실패하는지 식별 |
| Criterion 3 (LOCO r ≤ 0) | Interpolation 실패 | Residual 분석: (Y_s - W_s @ C)가 구조적인가 랜덤인가? 구조적 residual → 체계적 encoding 실패; 랜덤 → voxel noise가 signal 초과 |

이는 **encoding model 부적합**과 **측정 noise**를 분리한다.

---

## 10. Implementation

### 10a. Script 구성

| Script | Purpose | Status |
|--------|---------|--------|
| `step_a_fit_srm.py` | HC subjects SRM 적합 → R_i 추출 | **TODO** |
| `check_rs_stability.py` | R_s split-half 안정성 검증 (Steps B-D 이전 gate) | **TODO** |
| `step_b_group_prior.py` | 공통공간 encoding A_i 학습 → A_g 계산 | **TODO** |
| `step_c_project_prior.py` | W_{0,s} = R_s @ A_g 투사 | **TODO** |
| `step_d_finetune.py` | Prior-centered ridge → W_s 학습 | **TODO** |
| `validate_loro_loco_loso.py` | 3종 CV 평가 | **TODO** |
| `run_comparison.sbatch` | SLURM wrapper | **TODO** |

### 10b. Directory Structure

```
future_phase1_forward_model/
├── PLAN.md                          # Implementation plan (English)
├── notion.md                        # Algorithm documentation (Korean, 이 문서)
├── README.md                        # Phase overview
├── scripts/
│   ├── step_a_fit_srm.py
│   ├── check_rs_stability.py
│   ├── step_b_group_prior.py
│   ├── step_c_project_prior.py
│   ├── step_d_finetune.py
│   ├── validate_loro_loco_loso.py
│   └── run_comparison.sbatch
└── results/
    ├── srm_projections/             # R_i matrices
    ├── group_prior/                 # A_g per ROI
    ├── subject_weights/             # W_s per subject-ROI
    └── validation/                  # LORO/LOCO/LOSO results
```

### 10c. Data Dependencies

| Data | Path (server) | Shape | Source |
|------|--------------|-------|--------|
| Procrustes amplitudes | `derivatives/full_dataset_C010/{sub}/{ROI}/amplitudes_procrustes.npy` | (6, 8, V_s) | Phase 1 |
| SRM projection matrices | Step A에서 저장 | (V_s, k) per subject | Step A |
| 색 basis matrix | `create_basis_functions()` | (K, N) | `analysis/utils/utils_color_decoding.py` |

### 10d. 기존 코드 재활용

| Function | Source | 용도 |
|----------|--------|------|
| `create_basis_functions(n_channels=6)` | `analysis/utils/utils_color_decoding.py` | Basis matrix C 생성 |
| SRM fitting | `analysis/phase2_SRM_across_between/utils/srm_alignment.py` | Step A |
| `fit_W()` | `analysis/phase3_decoder_comparing/LOCO_trials/scripts/loco_ridge.py` | OLS/ridge fitting 참조 |
| SVD projection | Phase 2 `rerun_loo_consistent.py` | CVD subject R_s 획득 |

### 10e. lambda 선택

- **Nested CV**: 각 outer fold 안에서 inner loop로 lambda grid [0, 0.01, 0.1, 1, 10, 100, 1000]에서 선택
- **Alternative**: Analytical GCV (generalized cross-validation)
- ROI별, subject별 optimal lambda 보고

---

## 11. Filter Pipeline과의 연결

이 Phase에서 학습한 best W_s가 Phase 2의 **prediction engine**이 된다:

```
theta → C(theta) → W_s @ C(theta) = Y_hat_s(theta)
```

Phase 2에서 설계하는 T_psi (stimulus-space filter)는 W_s의 **upstream**에서 작동:

```
theta → T_psi(theta) → C(T_psi(theta)) → W_s @ C(T_psi(theta))
```

**SRM은 filter evaluation에 더 이상 필요하지 않다.** W_s가 Procrustes voxel space에서 prediction을 생성하므로, filter 품질은 voxel-level metric (correlation, R²)으로 직접 평가 가능하다. SRM은 cross-subject comparison에 선택적으로 사용할 수 있지만, core prediction/evaluation 경로에 포함되지 않는다.

이는 이전의 M_s bridge 접근법 대비 **근본적인 단순화**이다.

> **핵심 제약**: Prediction model W_s는 filter optimization 시작 전에 고정(frozen)된다. Filter T_ψ는 stimulus space에서만 작동하며, W_s를 수정, 재학습, 또는 fine-tune하지 않는다. 최적화 목적함수는 min_ψ L(W_s @ C(T_ψ(θ)), Y_target)이며 W_s는 고정이다.

### Filter Family Ablation (Phase 2 범위, 여기서 참조)

Filter 자체는 Phase 2에서 설계하지만, prediction model은 여러 filter family 비교를 지원해야 한다:

| Filter | Parameters | 설명 |
|--------|-----------|------|
| Identity | 0 | 보정 없음 (baseline) |
| Fourier-4 | 4 | a1·cos(θ) + b1·sin(θ) + a2·cos(2θ) + b2·sin(2θ) |
| Fourier-6 | 6 | 3차 harmonic까지 |
| GP (optional) | nonparametric | Gaussian process baseline |

핵심 질문:
- Correction이 실제로 필요한가? (Identity vs Fourier-4)
- 4-param이면 충분한가? (Fourier-4 vs Fourier-6)
- 더 flexible model이 overfit하지 않는가? (Fourier-6 vs GP)

---

## 12. 리스크 및 대응 방안

**핵심 리스크**: LOCO voxel correlation ≈ 0이 전체 ROI에서 나타나면, 연속 보간 주장이 무너지고 filter optimization에 활용할 prediction engine이 없어진다.

**발생 가능한 이유**:
- 8색 훈련이 연속 encoding에 너무 sparse할 수 있음 (특히 higher visual areas에서)
- SRM-mediated prior가 signal 대신 noise를 주입할 수 있음 (red team criticism 1)

**완화 방안**:
1. Gate criterion 3이 이를 명시적으로 포착 — filter 단계 이전에 파이프라인 정지
2. Template-matching LOCO는 이미 작동 (MAE: V1 ~76°, hV4 ~69°), 따라서 model-based 접근은 최소한 template matching 성능을 달성해야 함
3. R_s split-half stability check (실행 Step 1b)이 prior-projection 실패를 조기에 포착

**대응**: Model-based LOCO가 실패하지만 template matching이 성공하면, filter evaluation에 template-matching 기반 prediction을 사용. 이는 덜 우아하지만 (closed-form gradient 없음) 기능적이다.

---

## 13. 실행 우선순위

엄격한 순차 의존 — 각 단계가 다음 단계를 gate한다.

| Step | Script(s) | Output | Gate |
|---|---|---|---|
| 1a | `step_a_fit_srm.py` | R_i per HC subject | — |
| **1b** | **`check_rs_stability.py`** | **R_s split-half cosine similarity** | **cosine > 0.5 per ROI → 진행; 아니면 prior 접근 재설계** |
| 2a | `step_b_group_prior.py` | A_i, A_g per ROI | — |
| 2b | `step_c_project_prior.py` | W_{0,s} per subject | — |
| 3 | `step_d_finetune.py` | W_s per subject (lambda via nested CV) | — |
| **4** | **`validate_loro_loco_loso.py`** | **LORO r, LOCO r, LOCO MAE** | **LOCO r > 0 (p < 0.05) → 진행; 아니면 STOP** |
| 5 | Encoding-basis ablation (Stage 1) | Basis comparison table | Best basis 선정 |
| 6 | Full model comparison (Stage 2) | 5 models × 3 CV × 4 ROI table | Best model 식별 |
| 7 | Phase 2 filter design | T_ψ optimization | — |

**Step 1b는 red team criticism 1에서 유래** — Steps 2-4에 투자하기 전에 R_s projection의 신뢰성을 검증한다.

**Step 4가 핵심 go/no-go gate** — prediction model이 LOCO에 실패하면, downstream 전체가 차단된다.

---

## 14. Updated Pipeline Summary

```
Phase 1. Prediction Model
├── 1. Base model: forward encoding (FE-6 기본)
├── 2. Encoding basis ablation: FE-6 / LF-4 / LF-6
├── 3. Group prior + subject adaptation (Steps A-D)
├── 4. Validation: LORO / LOCO / LOSO
├── 5. Model comparison: OLS / Standard Ridge / Prior-only / Prior+finetune / Ridge+GCV
├── 6. Metrics: voxel corr, R², LOCO MAE, RDM corr, normalized fit, reliability
└── 7. Gate: reliability + predictability + interpolation

Phase 2. Filter Optimization
├── Filter families: identity / Fourier-4 / Fourier-6 / optional GP
├── Evaluation: geometry improvement, held-out validation, permutation, pairwise diagnostics
└── Individual-level analysis (Crawford & Howell per CVD subject)

Phase 3. Behavioral Validation
└── Neural correction → perceptual improvement prediction
```

**구조적 원칙**: Prediction model의 과학적 타당성을 먼저 확실히 만들고, 그 위에서 filter를 논의한다.

**기존 구조 vs 수정 구조**:

| 기존 | 수정 |
|------|------|
| prediction model → filter | prediction model (reliability-aware validation + encoding-basis ablation + group-prior adaptation) → filter-family ablation → behavioral validation |

---

## 15. 실무용 알고리즘 요약

### 학습

**HC prior construction**:
```
Z_i = R_i^T @ Y_i
A_i = argmin_A ||Z_i - A @ C||² + lambda_A * ||A||²
A_g = (1/M) * sum_i A_i
```

**Target subject prior projection**:
```
W_{0,s} = R_s @ A_g
```

**Target subject fine-tuning**:
```
W_s = argmin_W ||Y_s - W @ C||² + lambda * ||W - W_{0,s}||²
```

**Closed-form**:
```
W_s = (Y_s @ C^T + lambda * W_{0,s}) @ (C @ C^T + lambda * I)^{-1}
```

### 최종 한 줄 정리

> HC 공통공간에서 group prior A_g를 만든 뒤, 이를 target subject voxel space로 내린 W_{0,s} = R_s @ A_g를 prior로 사용하여, **하나의 subject-specific W_s**를 prior-centered ridge로 학습한다. Prediction은 끝까지 Procrustes voxel space에서 수행되며, SRM은 prior construction helper로만 사용된다.
