# Hyperalignment 기반 Prediction Model 개발 계획

**프로젝트 시작일**: 2025-12-28
**목표**: HC common space 기반 novel color prediction model 개발 및 CVD 개별 필터 최적화를 위한 데이터 증강

---

## 📋 Executive Summary

### 프로젝트 목표

본 프로젝트는 **CVD 개별 필터 최적화를 위한 360° 연속 색 공간 예측 모델**을 개발합니다. 기존 8색 제한을 넘어 임의의 hue 각도에서 HC-like 뇌 반응을 예측함으로써, 왜곡된 색 지각을 보정하는 개인화된 필터 제작을 가능하게 합니다.

### 핵심 방법론 (3 Phases)

**Phase 1: Trial-aligned GPA (HC common space 구축)** ✅ **먼저 수행**

**근거**: 기존 분석 결과 (V1/V2)
- Procrustes stability: 0.91/0.88 (매우 높음) ✅
- RDM correlation: 0.26/0.24 (낮음) ❌
- **해석**: 좌표계는 다르지만 구조는 같음 → **Common space에서 봐야 함!**

**방법**:
- Trial-wise voxel patterns (LS-S GLM, ~384 trials)
- Generalized Procrustes Analysis (직교 변환 R_s)
- CVD 배제 (HC-only 학습, 왜곡 보존)

**Phase 2: Continuous Hue Interpolation Model (360° 예측)**

**목표**: 8색 사이의 연속적인 hue 각도 예측 (0-360°, circular)

**용어 정의**:
- ✅ **Interpolation**: 360° circular space 내 dense sampling (1° 간격)
- ❌ **Extrapolation 아님**: 범위 "밖"이 없음 (circular)
- 🔬 **Novel hues**: 측정한 8색 사이의 각도 (예: 22.5°, 67.5°)

**구조 (회의 결과 반영)**:
- **Phase 2.1**: Population Encoder (HC common)
- **Phase 2.2**: Individual Encoder (HC verification)
- **Phase 2.3**: Regularization Comparison (None, Ridge, Lasso)
- **Phase 2+ (Optional)**: MLP Encoder (if linear insufficient)

**검증 전략 (In-Silico Only)**:
- Direct: LOCO CV (8색 중 1개 hold-out → 45° 간격 interpolation)
- Indirect: RDM smoothness, inter-encoder consistency

**Phase 3: CVD Filter Optimization via 360° Search**

**목표**: Optimization-based CVD individual filter discovery across 360° hue space

**핵심 방법**:
- For each θ_orig: optimize θ_display
- Dual constraint: voxel matching + reconstruction
- Phase 2 encoder 없으면 불가능!

**구조 (회의 결과 반영)**:
- **Phase 3.1**: CVD Individual Encoder (Mandatory)
- **Phase 3.2**: Loss Function Ablation (4-way: Loss1/Loss2/Equal/Optuna)
- **Phase 3.3**: Filter Validation (In-Silico Only)

**평가 (In-Silico)**:
- Filter quality (smoothness < 2.0°/deg)
- Performance (error ≤ baseline 32°)
- Inter-CVD stability (consistency < 10°)
- Ablation winner identification
- ⚠️ Empirical validation 보류 (추가 실험 필요)

---

## 🎯 연구 목표 및 질문 (Research Goals and Questions)

### 전체 연구 목표 (Overall Research Goal)

**Investigating neural representation of color inputs for healthy controls (HC) and color vision deficiency (CVD) individuals**

**정상인(HC)과 색각 이상자(CVD)의 색 입력에 대한 신경 표상 조사**

This project aims to understand how CVD brains represent color information differently from HC brains, and leverage these insights to develop personalized neural-guided display filters.

**본 프로젝트는 CVD 뇌가 정상인 뇌와 다르게 색 정보를 표상하는 방식을 이해하고, 이러한 통찰을 활용하여 개인화된 신경 기반 디스플레이 필터를 개발하는 것을 목표로 합니다.**

---

### 주요 연구 질문 (Primary Research Questions)

Based on the program paper (docs/program_paper/main.tex), we address three primary research questions:

**프로그램 논문(docs/program_paper/main.tex)을 기반으로 세 가지 주요 연구 질문을 다룹니다:**

#### RQ1: Neural Color Discrimination Despite Retinal Deficits
**Can individuals with CVD distinguish colors neurally despite retinal deficits?**

**망막 결함에도 불구하고 색맹자가 신경 수준에서 색을 구별할 수 있는가?**

- ✅ **Status**: Answered affirmatively (Phase 1 baseline analysis complete)
  - **상태**: 긍정적으로 답변됨 (Phase 1 기준 분석 완료)
- **Evidence**: All CVD participants showed successful color decoding (V1: 76%, V2: 71%), RDM structural preservation >90%
  - **근거**: 모든 CVD 참가자가 성공적 색 디코딩 (V1: 76%, V2: 71%), RDM 구조 보존 >90%
- **Implication**: Preserved neural geometry provides target representations for filter design
  - **함의**: 보존된 신경 기하학이 필터 설계를 위한 목표 표상 제공

#### RQ2: Inter-Individual Heterogeneity in CVD
**Does CVD show inter-individual heterogeneity necessitating personalized approaches?**

**색맹이 개인화된 접근을 필요로 하는 개인 간 이질성을 보이는가?**

- ✅ **Status**: Confirmed through three-dimensional analysis (Phase 1 complete)
  - **상태**: 3차원 분석을 통해 확인됨 (Phase 1 완료)
- **Evidence**: CVD is heterogeneous → the three CVD participants show distinct 3-D distortion profiles (e.g. sub-08 deutan vs sub-09 protan differ on every axis)
  - **근거**: CVD는 이질적 → 3인이 서로 다른 3차원 왜곡 프로파일 (예: sub-08 deutan vs sub-09 protan은 모든 축에서 상이)
  - Magnitude: L2 norm ratios 0.66-1.21 (±30% variation)
  - Sign/Baseline: Directional biases -0.41 to +0.32
  - Structure: RDM differences 0.118-0.505
- **Implication**: One-size-fits-all filters inadequate; individual neural profiling necessary
  - **함의**: 획일적 필터 부적합; 개인별 신경 프로파일링 필요

#### RQ3: Neural-Guided Personalized Filter Design (✅ Feasibility Demonstrated)
**Can three-dimensional neural profiles inform individual-specific display filter design?**

**3차원 신경 프로파일이 개인별 맞춤형 디스플레이 필터 설계에 활용될 수 있는가?**

- ✅ **Status**: Feasibility demonstrated through retrospective validation
  - **상태**: 회고적 검증을 통해 가능성 입증
- **Evidence**: Subject-specific linear transformations achieved:
  - **근거**: 개인별 선형 변환 달성:
  - 97.2% Procrustes disparity reduction (CVD → HC-like patterns)
  - RDM correlation ≥0.999 with HC reference
  - Individual loss weight optimization ($\lambda_{\text{mag}}$, $\lambda_{\text{base}}$, $\lambda_{\text{struct}}$)
- ⚠️ **Limitation**: Retrospective only; prospective behavioral validation pending
  - ⚠️ **한계**: 회고적 검증만; 전향적 행동 검증 미실시
- **Next steps**: This project (Phases 1-3) extends feasibility to continuous 360° hue space
  - **다음 단계**: 본 프로젝트(Phase 1-3)는 가능성을 연속 360° 색조 공간으로 확장

---

### 본 프로젝트의 목표 (This Project's Objective)

Building on RQ3 feasibility findings, this project develops a **360° continuous hue prediction model** to enable optimization-based CVD filter design across the full color spectrum (not just 8 measured colors).

**RQ3 가능성 발견을 기반으로, 본 프로젝트는 전체 색 스펙트럼(측정된 8색뿐만 아니라)에 걸쳐 최적화 기반 CVD 필터 설계를 가능하게 하는 360° 연속 색조 예측 모델을 개발합니다.**

**Core innovation**: Phase 2 encoder enables **dense angular sampling** (1° spacing) → Phase 3 filter optimization can search across **360 possible display colors** for each original color, dramatically expanding the solution space from 8 discrete mappings to continuous transformations.

**핵심 혁신**: Phase 2 인코더가 **조밀한 각도 샘플링**(1° 간격) 가능 → Phase 3 필터 최적화가 각 원색에 대해 **360개 가능한 디스플레이 색상**을 탐색할 수 있어, 해공간을 8개 이산 매핑에서 연속 변환으로 극적으로 확장.

---

## 🎯 연구 배경 및 동기

### CVD 필터 제작의 핵심 요구사항

**문제**:
- 기존 8색만으로는 360° 색 공간에서 필터 최적화 불가능
- CVD는 **연속적인** 색 지각 왜곡을 가짐 (8개 점만 아님)
- 개인별 맞춤 필터 학습에 충분한 샘플 부족

**해결 방안**:
1. **HC common space 구축** → 좌표계 차이 제거
2. **360° continuous encoder** → 임의의 hue 예측
3. **HC-like targets** → CVD 필터 regularization

### 기존 접근의 한계

**1. 8색 제한**
- 분석: 8개 discrete colors (0°, 45°, 90°, ...)
- 문제: 8개 점만으로 연속 색 공간 변환 정의 불가능
- CVD 필터: 특정 8색만 보정, 중간 색은?

**2. 좌표계 차이 (Procrustes 한계)**
- 기존: 8색 평균 Procrustes (대응점 8개)
- 결과: HC 간 variability 남음 (RDM corr 0.26)
- 문제: Common W 불안정

**3. 검증 제한**
- 8색만 측정 → interpolation 품질 직접 검증 어려움
- Extrapolation은 불가능 (360° circular)

### 새로운 접근의 강점

**1. Trial-aligned GPA (Phase 1)**
- 대응점 증가: 8 → ~384 trials
- 좌표계 정렬 강화
- HC common space 안정화

**2. Continuous Hue Encoder (Phase 2)**
- 360° circular interpolation
- Channel-based model (6 basis channels)
- Dense angular sampling (1° 또는 더 촘촘히)

**3. HC-like Target Regularization (Phase 3)**
- 360° targets → CVD 필터 학습
- Regularization → 안정성 향상
- 8색 성능 유지하면서 일반화

---

## 🔬 방법론 개요

### Phase 1: Hyperalignment for HC Common Space

**목표**: HC 5명의 trial-wise voxel patterns를 공통 표현 공간으로 정렬

**방법**: Hyperalignment using trial-aligned GPA (Generalized Procrustes Analysis)
```
Trial-wise beta (LS-S) → Full voxel space GPA (NO PCA) → HC common space
→ X_common + 직교 변환 R_s
```

**핵심 설계**:
- **Input**: 각 HC의 trial-wise patterns (~384 trials, n_voxels)
- **Alignment**: Regularized GPA (직교 변환만, magnitude 보존)
- **CVD 처리**: 학습 배제, 고정된 X_common에 투사만
- **⚠️ NO PCA**: Full voxel space 유지 (geographic features 보존)

**산출물**:
- HC common space: X_common ∈ ℝ^(n_trials × n_voxels)
- 직교 변환: R_s ∈ SO(n_voxels) (각 HC)
- Alignment quality metrics (2-tier)

**평가 (2-Tier)**:
- Tier-1 (Trial-level): Inter-subject correlation, LOSO decoding
- Tier-2 (Color-level): Procrustes disparity (8색 평균), Run-split stability

---

### Phase 2: Continuous Hue Interpolation Model (360° encoder)

**목표**: 360° circular hue space에서 임의의 각도 θ에 대한 voxel pattern 예측

**용어 정의 (명확히)**:
```
Measured:    8 hues (0°, 45°, 90°, ..., 315°)
Interpolate: Dense angles (1° 간격, 0-359°)
Circular:    0°와 359° 사이도 interpolation (wrap-around)
```

**❌ 이것이 아님**:
- Extrapolation (범위 밖 없음, circular)
- Saturation/luminance 변화 (고정)
- Natural images (단색만)

**✅ 이것이 맞음**:
- **360° circular hue interpolation**
- **Trained hue range 내 dense sampling**
- **Channel-based continuous model**

**모델 구조 (Linear Baseline)**:
```python
# Channel-based encoding
θ (hue angle) → C(θ) (6 channels) → W_enc → ŷ(θ) (voxel pattern)

# Channel response function
C_i(θ) = cos²((θ - θ_i) / σ)  if |θ - θ_i| < 90°, else 0
Centers: 0°, 60°, 120°, 180°, 240°, 300°
```

---

#### **Phase 2.1: Population Encoder (HC Common)**

**목표**: HC common space에서 집단 수준 channel encoder 학습

**학습 (Linear Model)**:
```python
# HC common space에서
Color_patterns_8 = trials_to_color_avg(X_common)  # (8, k)
Channel_responses_8 = compute_channels(angles_8)   # (8, 6)
W_enc_population = lstsq(Channel_responses_8, Color_patterns_8)  # (6, k)

# 360° 예측
θ_dense = np.arange(0, 360, 1)
C_dense = compute_channels(θ_dense)  # (360, 6)
predictions_360 = C_dense @ W_enc_population     # (360, k)
```

**평가**:
- LOCO CV error (8색 중 1개 hold-out)
- RDM smoothness
- Population-level metrics

---

#### **Phase 2.2: Individual Encoder (HC Verification)**

**목표**: HC 개개인별 channel encoder 학습 및 population 대비 검증

**학습**:
```python
# 각 HC subject s에 대해
for subject_s in HC_subjects:
    X_s_common = apply_rotation(X_s, R_s)  # Phase 1 정렬 결과 사용
    Color_patterns_s = trials_to_color_avg(X_s_common)  # (8, k)
    W_enc_s = lstsq(Channel_responses_8, Color_patterns_s)  # Individual encoder
```

**비교 분석**:
- Individual vs Population prediction error
- Inter-individual variability
- **검증**: Individual이 크게 우수하면 population 불안정 신호

---

#### **Phase 2.3: Regularization Comparison**

**목표**: Regularization이 일반화 성능에 미치는 영향 비교

**실험 설계** (3가지 방법):

**1. None (OLS)**:
```python
W_enc = lstsq(C, Y)  # No regularization
```

**2. Ridge Regression**:
```python
# Cross-validation으로 α 선택
alphas = np.logspace(-3, 3, 10)
W_enc_ridge = RidgeCV(alphas=alphas).fit(C, Y).coef_
```

**3. Lasso Regression**:
```python
# Cross-validation으로 α 선택
alphas = np.logspace(-3, 3, 10)
W_enc_lasso = LassoCV(alphas=alphas).fit(C, Y).coef_
```

**비교 지표**:
- LOCO CV reconstruction error
- Filter smoothness (360° 예측 품질)
- Overfitting 정도 (train vs validation error gap)

**예상 결과**:
- Ridge: 일반화 우수 (예상 최적)
- Lasso: Sparse solution (voxel selection 효과)
- None: Overfitting 가능성 (데이터 부족 시)

---

### Phase 2+ (Optional): MLP Encoder

**목표**: Linear 모델이 불충분할 경우 비선형 encoder 도입

**실행 조건** (다음 중 하나 이상):
- Linear LOCO CV error > 50° (unacceptable)
- RDM smoothness < 0.5 (불연속적 예측)
- Strong non-linearity evidence (residual analysis)

**모델 구조**:
```python
# Simple 2-layer MLP
class MLPEncoder(nn.Module):
    def __init__(self, n_channels=6, n_voxels=k, hidden=32):
        self.fc1 = nn.Linear(n_channels, hidden)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden, n_voxels)

    def forward(self, C):
        h = self.relu(self.fc1(C))
        return self.fc2(h)

# Loss: MSE + L2 regularization
loss = MSE(predictions, targets) + λ * ||θ||²
```

**검증**:
- MLP vs Linear performance gain
- Overfitting 모니터링 (early stopping)
- Interpretability trade-off 고려

**⚠️ 주의사항**:
- Linear 먼저 철저히 검증
- MLP는 데이터 부족 시 overfitting 위험
- Phase 3 filter optimization 복잡도 증가

---

**검증 전략 (공통, In-Silico Only)**:

**Direct Validation** (LOCO CV):
```python
# 8색 중 1개 hold-out
for held_out_color in colors_8:
    W_enc_7 = train_on_7_colors()
    predicted = W_enc_7.predict(held_out_angle)
    error = angular_distance(predicted, actual)

# 기준: mean(error) < 60° (chance: 90°)
```

**Indirect Validation** (품질 지표):
1. **RDM Smoothness**: 인접 각도 간 거리 연속성
2. **Inter-Encoder Consistency**: HC 5명 예측 일치도
3. **Channel Plausibility**: 이론적 peak 위치 확인

**⚠️ 현재는 In-Silico Validation만 수행** (Empirical validation은 추가 실험 필요)

---

### Phase 3: CVD Filter Optimization via 360° Search

**목표**: Optimization-based CVD individual filter discovery across 360° hue space

**핵심 아이디어**:
```
For each original color θ_orig:
    Find optimal display color θ_display such that:
    - CVD's brain response to θ_display matches HC's response to θ_orig
    - Decoding θ_display gives θ_orig back (reconstruction)
```

**⚠️ CRITICAL**: CVD Individual Encoder는 **필수** (Population만으로는 개인차 캡처 불가)

---

#### **Phase 3.1: CVD Individual Encoder (Mandatory)**

**목표**: 각 CVD subject별 channel encoder 학습

**5-Step Process**:
1. **CVD projection**: CVD → HC common space (Procrustes)
2. **CVD encoder**: CVD individual encoder 학습 (8 measured colors)
   ```python
   # CVD subject c별로
   X_cvd_common = apply_procrustes(X_cvd, X_hc_common)
   Color_patterns_cvd = trials_to_color_avg(X_cvd_common)  # (8, k)
   W_enc_cvd = lstsq(Channel_responses_8, Color_patterns_cvd)  # (6, k)
   ```
3. **Regularization**: Phase 2.3과 동일한 방법 비교 (None, Ridge, Lasso)

**평가**:
- CVD individual encoder 품질 (LOCO CV)
- HC와의 차이 분석 (representational dissimilarity)

---

#### **Phase 3.2: Loss Function Ablation (4-way)**

**목표**: Dual loss function의 각 component 기여도 분석

**방법** (Optimization-based):
```python
# Phase 2 encoder 활용한 dual-constraint optimization

For θ_orig in [0°, 1°, ..., 359°]:
    θ_display = argmin_θ [
        # Loss 1: Voxel pattern matching
        α * ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²

        # Loss 2: Reconstruction accuracy
        + β * ||Decode(Ŷ_cvd(θ)) - θ_orig||²
    ]

    Filter[θ_orig] = θ_display  # Lookup table

where:
  Ŷ_hc(θ_orig) = C(θ_orig) @ W_enc_population  (Phase 2.1 encoder 사용!)
  Ŷ_cvd(θ) = C(θ) @ W_enc_cvd  (Phase 3.1 CVD encoder 사용!)
```

**실험 설계 (4가지 시나리오)**:

**Scenario 1: Loss 1 only (Voxel Matching)**
```python
α = 1.0, β = 0.0
# 뇌 반응 패턴만 일치
```
- **예상**: 강한 regularization, 하지만 reconstruction 불안정
- **검증**: Voxel correlation, filter smoothness

**Scenario 2: Loss 2 only (Reconstruction)**
```python
α = 0.0, β = 1.0
# 색 복원만 고려
```
- **예상**: Reconstruction 우수, 하지만 뇌 반응 불일치 가능
- **검증**: Reconstruction error, decoding accuracy

**Scenario 3: Equal Weight (Balanced)**
```python
α = 0.5, β = 0.5
# 동등한 중요도
```
- **예상**: Trade-off, 균형잡힌 성능
- **검증**: 종합 평가 (voxel + reconstruction)

**Scenario 4: Optuna Optimization (Data-Driven)**
```python
# Hyperparameter search
α, β = optuna.minimize(
    objective=lambda trial:
        validate_filter(
            alpha=trial.suggest_float('alpha', 0.0, 1.0),
            beta=1.0 - alpha  # α + β = 1.0 constraint
        ),
    n_trials=50
)
```
- **탐색 공간**: α ∈ [0, 1], β = 1 - α
- **목표 함수**: LOCO CV 성능 (voxel correlation + reconstruction error)
- **예상**: 데이터 기반 최적 균형점 발견

**비교 지표** (4 scenarios across):
1. **Voxel Matching**: Pattern correlation (CVD filtered vs HC original)
2. **Reconstruction Error**: Angular distance (decoded vs target)
3. **Filter Smoothness**: Gradient magnitude (°/degree)
4. **Inter-CVD Stability**: Filter consistency across CVD subjects

---

#### **Phase 3.3: Filter Validation (In-Silico Only)**

**Tier 1 (In-Silico)** - Current data only:
1. **Filter Quality**: Smoothness < 2.0°/deg
2. **Performance**: Reconstruction error ≤ baseline (32°)
3. **Stability**: Inter-CVD consistency < 10°
4. **Ablation Winner**: Best scenario identification
5. ⚠️ **Limitation**: Circular logic (encoder validates itself)

**Tier 2 (Empirical)** - ⚠️ **추가 실험 필요 (현재 보류)**:
1. Measure CVD responses to **filtered stimuli** (not just predicted)
2. Compare actual CVD(filtered) vs HC(original) patterns
3. **Gold standard**: Pattern correlation > 0.70
4. Timeline: 2-4 weeks additional scanning

**⚠️ 현재는 In-Silico만 수행**

---

**핵심 장점**:
- ✅ **360° 전체 각도 적용** (Phase 2 encoder 없으면 불가능!)
- ✅ **개인화된 filter** (각 CVD의 실제 반응 패턴 기반)
- ✅ **Dual constraint ablation** (각 loss component 기여도 분석)
- ✅ **이론적 타당성** (CVD 뇌를 HC처럼 만드는 게 목표)
- ✅ **Data-driven optimization** (Optuna로 최적 α, β 탐색)

---

## 📊 Feasibility 점검 계획

### 초기 분석 (Week 1-2)

#### 1️⃣ 데이터 준비성 확인
**체크리스트**:
- [ ] Trial-wise beta 추출 가능성 (LSA/LS-S)
- [ ] 자극 순서 동일성 검증
- [ ] Run별 trial 수 및 timing 정보 확인
- [ ] 현재 8색 beta와의 일치도 비교

**예상 이슈**:
- Single-trial GLM의 SNR 저하 → Regularization 필요
- Trial overlap/HRF 겹침 → FIR deconvolution 고려

#### 2️⃣ Hyperalignment 파일럿 테스트
**실험**:
- HC 2명으로 toy example
- 기존 8색 평균 beta로 GPA 수행
- Trial-wise vs color-averaged 비교

**평가 지표**:
- Procrustes disparity (기존 vs hyperalignment)
- Split-half stability (정렬 전/후)
- Common W decoding accuracy

#### 3️⃣ Channel-based Interpolation 검증
**실험**:
- LOCO CV (1-2색 hold-out)
- 채널 응답 기반 예측 vs 직접 voxel interpolation 비교

**평가 지표**:
- Reconstruction error (degrees)
- Voxel-wise correlation
- 예측 패턴의 RDM similarity

---

## 📅 단계별 실행 계획

### Phase 0: Preparation (Week 1)
- [x] 프로젝트 구조 설정
- [ ] 기존 데이터 구조 분석
- [ ] Trial-wise GLM 설계 (LS-S with confounds)
- [ ] Split-half reliability check implementation

### Phase 1: Hyperalignment Implementation (Week 2-3)
- [ ] Trial-wise beta 추출 (LS-S)
- [ ] Split-half reliability check (gate-keeper)
- [ ] HC-only hyperalignment using GPA (full voxel space, NO PCA)
- [ ] Alignment quality 평가 (2-tier)
- [ ] Common W 재학습 및 성능 비교

### Phase 2: Prediction Model Development (Week 3-4)
**Phase 2.1: Population Encoder**
- [ ] Channel response function 정의 (연속 θ)
- [ ] Population encoder 학습 (HC common space)
- [ ] LOCO CV 검증
- [ ] RDM smoothness 평가

**Phase 2.2: Individual Encoder (HC Verification)**
- [ ] HC individual encoders 학습 (각 subject별)
- [ ] Population vs Individual 성능 비교
- [ ] Inter-individual variability 분석

**Phase 2.3: Regularization Comparison**
- [ ] None (OLS) baseline
- [ ] Ridge regression (CV for α)
- [ ] Lasso regression (CV for α)
- [ ] 성능 비교 (LOCO CV, overfitting)

**Phase 2+ (Optional): MLP Encoder**
- [ ] Linear 성능 평가 → MLP 필요성 판단
- [ ] MLP architecture 설계 (2-layer)
- [ ] Hyperparameter tuning (hidden size, λ)
- [ ] Linear vs MLP 성능 비교

### Phase 3: CVD Filter Optimization (Week 5-6)
**Phase 3.1: CVD Individual Encoder (Mandatory)**
- [ ] CVD → HC common space projection (Procrustes)
- [ ] CVD individual encoder 학습 (8 measured colors, 3 subjects)
- [ ] Regularization 비교 (None, Ridge, Lasso)
- [ ] CVD vs HC representational difference 분석

**Phase 3.2: Loss Function Ablation (4-way)**
- [ ] Scenario 1: Loss 1 only (α=1.0, β=0.0)
- [ ] Scenario 2: Loss 2 only (α=0.0, β=1.0)
- [ ] Scenario 3: Equal weight (α=0.5, β=0.5)
- [ ] Scenario 4: Optuna optimization (α, β search)
- [ ] 4-way 성능 비교 (voxel matching, reconstruction, smoothness, stability)

**Phase 3.3: Filter Validation (In-Silico Only)**
- [ ] Filter quality 평가 (smoothness < 2.0°/deg)
- [ ] Performance 평가 (error ≤ baseline 32°)
- [ ] Inter-CVD stability (consistency < 10°)
- [ ] Best scenario identification
- [ ] ⚠️ Empirical validation 보류 (추가 실험 필요)

---

## 🔍 주요 기술적 도전 과제

### 1. Sample Size vs Dimensionality
**문제**:
- HC 5명, trial-wise로 해도 ~1920 trials total (384 × 5)
- Voxel 수는 수백 (V1: 429, V2: 279)
- Full voxel space = high noise sensitivity

**해결 방안**:
- ⚠️ **NO PCA** (geographic features 보존 위해)
- **Regularized GPA** (Ridge: R = argmin ||XR - Y||² + α||R - I||²)
- **Voxel selection** (Low-SNR voxels 제거)
- **Spatial smoothing** (6-8mm 사전 적용)
- Cross-validation으로 일반화 성능 감시

### 2. Trial-wise SNR
**문제**:
- Single-trial GLM은 noise 큼
- Beta 추정 불안정

**해결 방안**:
- Spatial smoothing (6-8mm)
- Temporal regularization (AR model)
- Robust regression (M-estimator)

### 3. Novel Color Validation
**문제**:
- 8색 외 실제 측정 데이터 없음
- Interpolation 품질 검증 어려움

**해결 방안**:
- LOCO CV로 내삽 가능성 입증
- RDM consistency 확인
- 논문에서는 "interpolation within trained range"로 표현

### 4. CVD Heterogeneity
**문제**:
- CVD 3명, 개인차 큼
- Common model이 모두에게 적합하지 않을 수 있음

**해결 방안**:
- CVD별 adaptation layer (A,b)
- Hybrid approach: common structure + individual correction
- CVD-specific validation

---

## 📈 성공 지표 (Success Criteria)

### Phase 1 (Hyperalignment)
✅ **필수**:
- Procrustes disparity < 0.10 (HC common space)
- Split-half stability > 0.80
- Common W decoding accuracy ≥ 기존 Procrustes 방식

⭐ **우수**:
- Disparity < 0.05
- LORO-CV reconstruction error 감소 > 5°

### Phase 2 (Prediction Model)

**Phase 2.1: Population Encoder**
✅ **필수**:
- LOCO CV reconstruction error < 50° (chance: 90°)
- Predicted pattern의 RDM correlation > 0.5

⭐ **우수**:
- LOCO error < 40°
- RDM smoothness > 0.7

**Phase 2.2: Individual Encoder (HC Verification)**
✅ **필수**:
- Individual encoder LOCO CV error < 50°
- Population vs Individual 차이 분석 완료

⭐ **우수**:
- Individual과 Population 차이 < 10° (일관성)
- 또는 Individual이 크게 우수 → regularization 필요 신호

**Phase 2.3: Regularization Comparison**
✅ **필수**:
- 3가지 방법 (None, Ridge, Lasso) 모두 평가
- LOCO CV로 일반화 성능 비교

⭐ **우수**:
- Ridge가 overfitting 감소 > 5°
- 최적 regularization 방법 식별

**Phase 2+ (Optional): MLP Encoder**
⚠️ **실행 조건**:
- Linear LOCO CV error > 50° (unacceptable)
- 또는 RDM smoothness < 0.5

✅ **성공 시**:
- MLP LOCO error < Linear error - 10° (유의미한 개선)

### Phase 3 (CVD Filter Optimization)

**Phase 3.1: CVD Individual Encoder**
✅ **필수**:
- CVD 3명 모두 individual encoder 학습 완료
- LOCO CV error < 70° (CVD는 왜곡되어 있으므로 HC보다 높아질 수 있음)

⭐ **우수**:
- CVD encoder error < 60°
- CVD vs HC representational dissimilarity 정량화

**Phase 3.2: Loss Function Ablation**
✅ **필수**:
- 4가지 시나리오 모두 평가 (Loss1, Loss2, Equal, Optuna)
- 각 시나리오별 4가지 지표 측정 (voxel, reconstruction, smoothness, stability)

⭐ **우수**:
- Optuna가 최적 α, β 발견 (validation 기준)
- 또는 특정 loss가 지배적 → 단순화 가능

**Phase 3.3: Filter Validation (In-Silico)**
✅ **필수**:
- Filter smoothness < 2.0°/deg
- Reconstruction error ≤ baseline (32°)
- Inter-CVD consistency < 10°

⭐ **우수**:
- Filter smoothness < 1.5°/deg (매우 부드러움)
- Reconstruction error < 25° (baseline 대비 개선)
- 모든 ablation scenarios에서 일관된 성능

⚠️ **Empirical Validation (현재 보류)**:
- In-silico 완료 후 필요성 재평가
- 추가 실험 2-4주 소요

---

## 🗂️ 문서 구조

```
prediction_model/
├── MASTER_PLAN.md                        (본 문서)
├── docs/
│   ├── PHASE1_HYPERALIGNMENT.md          (Hyperalignment 상세 계획)
│   ├── PHASE2_PREDICTION_MODEL.md        (Continuous Hue Interpolation)
│   ├── PHASE3_CVD_FILTER_OPTIMIZATION.md (Filter Optimization)
│   └── PROGRESS_LOG.md                   (진행 상황 기록)
├── scripts/
│   ├── 00_check_data_structure.py        (Trial order consistency check)
│   ├── 01_reliability_comparison.py      (Step 1.2: Baseline vs trial-wise reliability)
│   ├── 02_trial_wise_glm.py              (LS-S beta 추출)
│   ├── 03_trial_aligned_gpa.py           (Trial-aligned GPA, NO PCA)
│   ├── 04_evaluate_alignment.py          (2-tier evaluation)
│   ├── 05_channel_encoder_population.py  (Phase 2.1: Population encoder)
│   ├── 06_channel_encoder_individual.py  (Phase 2.2: Individual encoder, HC)
│   ├── 07_regularization_comparison.py   (Phase 2.3: None/Ridge/Lasso)
│   ├── 08_mlp_encoder.py                 (Phase 2+: Optional MLP)
│   ├── 09_loco_cv.py                     (LOCO validation)
│   ├── 10_continuous_interpolation.py    (360° predictions)
│   ├── 11_cvd_projection.py              (Phase 3.1: CVD → common space)
│   ├── 12_cvd_encoder.py                 (Phase 3.1: CVD individual encoder)
│   ├── 13_filter_optimization.py         (Phase 3.2: 360° filter search)
│   ├── 14_loss_ablation.py               (Phase 3.2: 4-way ablation)
│   └── 15_filter_validation.py           (Phase 3.3: In-silico validation)
└── results/
    ├── alignment_quality/                (정렬 품질 결과)
    ├── prediction_validation/            (예측 검증 결과)
    └── filter_validation/                (필터 검증 결과)
```

---

## 📚 참고 문헌 및 선행 연구

### Hyperalignment & Shared Spaces
- Gower (1975). Generalized procrustes analysis. *Psychometrika*.
- Haxby et al. (2011). A common, high-dimensional model of the representational space. *Neuron*.
- Chen et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Guntupalli et al. (2016). A model of representational spaces in the inferior temporal cortex. *Cerebral Cortex*.

### Color Encoding
- Brouwer & Heeger (2009). Decoding and reconstructing color. *J. Neurosci*.
- Bannert & Bartels (2018). Human V4 activity patterns. *J. Neurosci*.
- Bannert & Bartels (2025). Shared response model for color. *J. Neurosci*. ⭐

### Procrustes & Alignment
- Gower (1975). Generalized procrustes analysis. *Psychometrika*.
- 본 프로젝트 기존 결과 (`docs/PROCRUSTES_ANALYSIS_GUIDE.md`)

---

## 🤝 역할 분담 (제안)

### 데이터 분석
- Trial-wise GLM 구현 및 검증 (LS-S)
- Split-half reliability check
- Hyperalignment 파라미터 튜닝
- 결과 시각화

### 모델 개발
- Channel encoder 설계
- Continuous hue interpolation model 학습
- Cross-validation 프레임워크

### CVD Filter 최적화
- CVD projection to common space
- Filter optimization (360° grid search)
- 2-tier validation (in-silico + empirical)

---

## 📌 다음 액션 아이템

### Immediate (이번 주)
1. 기존 데이터에서 trial timing 정보 추출
2. 자극 순서 동일성 검증 (`00_check_data_structure.py`)
3. Single-trial GLM 문헌 조사 (LS-S)
4. Split-half reliability check 구현

### Short-term (다음 주)
1. Pilot test: HC 2명으로 hyperalignment (trial-aligned GPA, NO PCA)
2. LOCO CV 프레임워크 구현
3. Channel response function 정의

### Medium-term (2-3주 후)
1. Full hyperalignment (HC 5명, trial-aligned GPA, full voxel space)
2. Common continuous hue interpolation model
3. CVD projection 및 filter optimization
4. Tier 1 (in-silico) validation

---

**최종 업데이트**: 2025-12-28
**다음 리뷰**: Phase 0 완료 후 (예상: 2025-01-04)
