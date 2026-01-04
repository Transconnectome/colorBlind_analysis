# Phase 3: CVD Filter Optimization via 360° Search

**목표**: Optimization-based CVD individual filter discovery across 360° hue space
**방법**: Dual-constraint optimization (voxel pattern matching + reconstruction accuracy)
**예상 기간**: 2주 (Week 5-6)
**담당**: 필터 최적화팀

---

## 🎯 Phase 3 목표 및 핵심 아이디어

### The Big Picture

**Phase 1-2의 산출물**:
- ✅ HC common space (hyperalignment using trial-aligned GPA)
- ✅ 360° hue encoder: `Ŷ_hc(θ) = C(θ) @ W_enc`

**Phase 3의 목표**:
> **For each original color θ_orig, find the optimal display color θ_display**
> **such that CVD's brain response to θ_display matches HC's response to θ_orig**

---

### Core Innovation: Optimization-based Filter

**기존 접근 (voxel-space filter)**:
```
문제: CVD voxel → HC voxel 변환 학습
한계: 8색 데이터만 → filter 불안정
```

**우리 접근 (color-space filter via optimization)**:
```
For each θ_orig in [0°, 360°]:
    θ_display = argmin_θ [
        Loss1: ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²  (voxel pattern matching)
        Loss2: λ * ||Decode(Ŷ_cvd(θ)) - θ_orig||²  (reconstruction accuracy)
    ]

Filter: θ_orig → θ_display (lookup table or parametric function)
```

**장점**:
1. ✅ **360° 전체 각도 적용 가능** (Phase 2 encoder 덕분)
2. ✅ **개인화된 filter** (각 CVD의 실제 반응 패턴 기반)
3. ✅ **Dual constraint** (뇌 반응 + 색 복원 모두 만족)
4. ✅ **이론적 타당성** (CVD 뇌를 HC처럼 만드는 게 목표)

---

## 📊 Step 1: CVD Data Collection & Projection

### 1.1 CVD Measured Data

**실험 데이터**:
- CVD 3명 (sub-08, 09, 10)
- 8 colors × 6 runs
- ROIs: V1, V2, V3, hV4

**데이터 형식**:
```python
# 각 CVD의 trial-wise beta (LS-S로 추출)
cvd_data = []
cvd_labels = []

for cvd_id in ['08', '09', '10']:
    trial_betas, labels = extract_trial_wise_beta_lss(cvd_id, roi_mask)
    cvd_data.append(trial_betas)  # (n_trials, n_voxels)
    cvd_labels.append(labels)

print(f"CVD data shapes:")
for i, cvd_id in enumerate(['08', '09', '10']):
    print(f"  CVD {cvd_id}: {cvd_data[i].shape}")
```

---

### 1.2 CVD → Common Space Projection

**⚠️ 주의: CVD는 학습에 참여하지 않았음!**

GPA는 HC-only로 학습했으므로, CVD는 학습된 common space에 **투사**만:

```python
def project_cvd_to_common_space(cvd_data, X_common_hc, pca_models):
    """
    CVD 데이터를 HC common space에 투사

    HC-only GPA로 학습된 공간에 CVD를 align

    Parameters
    ----------
    cvd_data : ndarray (n_trials, n_voxels)
        CVD의 trial-wise beta
    X_common_hc : ndarray (n_trials_hc, n_components)
        HC common space (from Phase 1)
    pca_models : list of PCA
        각 HC의 PCA model (voxel → feature space)

    Returns
    -------
    cvd_aligned : ndarray (n_trials_cvd, n_components)
        Common space에 투사된 CVD 데이터
    R_cvd : ndarray (n_components, n_components)
        CVD → common space 변환 행렬 (직교)
    """
    from scipy.linalg import orthogonal_procrustes

    # Step 1: CVD도 PCA로 차원 축소 (HC와 같은 방식)
    # 방법: HC의 평균 PCA를 사용하거나, CVD 독립 PCA
    # 여기서는 HC 평균 PCA 사용 (더 안정적)
    pca_mean = average_pca_models(pca_models)  # HC 평균 PCA
    cvd_reduced = pca_mean.transform(cvd_data)  # (n_trials_cvd, n_components)

    # Step 2: CVD → common space Procrustes alignment
    # Reference: HC common space의 색별 평균 패턴
    hc_color_patterns = compute_color_averaged_patterns(X_common_hc)  # (8, n_components)

    # CVD의 색별 평균 패턴
    cvd_color_patterns = compute_color_averaged_patterns_cvd(cvd_reduced, cvd_labels)

    # Procrustes: CVD 패턴을 HC 패턴에 정렬
    R_cvd, _ = orthogonal_procrustes(cvd_color_patterns, hc_color_patterns)

    # CVD 전체 trial 정렬
    cvd_aligned = cvd_reduced @ R_cvd  # (n_trials_cvd, n_components)

    return cvd_aligned, R_cvd

# CVD 투사
cvd_projected = []
R_cvd_list = []

for cvd_idx in range(3):
    cvd_aligned, R_cvd = project_cvd_to_common_space(
        cvd_data[cvd_idx],
        X_common,  # from Phase 1
        pca_models  # from Phase 1
    )
    cvd_projected.append(cvd_aligned)
    R_cvd_list.append(R_cvd)

    print(f"✅ CVD {cvd_idx+1} projected: {cvd_aligned.shape}")
```

---

## 🧪 Step 2: CVD Voxel Pattern Modeling

### 2.1 CVD Encoder (Optional vs Required?)

**옵션 A: CVD-specific encoder 학습** (권장 ⭐)

각 CVD의 8색 데이터로 individual encoder 학습:

```python
def train_cvd_encoder(cvd_data_aligned, cvd_labels, n_channels=6):
    """
    CVD의 individual encoder 학습

    HC encoder와 같은 방식이지만, CVD의 왜곡된 패턴 학습
    """
    # 색별 평균 패턴
    unique_colors = np.unique(cvd_labels)
    color_patterns = []
    color_angles = []

    for color in unique_colors:
        mask = cvd_labels == color
        color_patterns.append(cvd_data_aligned[mask].mean(axis=0))
        color_angles.append(get_angle_from_color_name(color))

    color_patterns = np.array(color_patterns)  # (8, n_features)
    color_angles = np.array(color_angles)

    # Channel responses
    C = compute_channel_responses(color_angles, n_channels)  # (8, n_channels)

    # CVD encoder: Ŷ_cvd(θ) = C(θ) @ W_enc_cvd
    W_enc_cvd = np.linalg.lstsq(C, color_patterns, rcond=None)[0]

    return W_enc_cvd

# 각 CVD encoder 학습
W_enc_cvd_list = []
for cvd_idx in range(3):
    W_cvd = train_cvd_encoder(
        cvd_projected[cvd_idx],
        cvd_labels[cvd_idx]
    )
    W_enc_cvd_list.append(W_cvd)
    print(f"✅ CVD {cvd_idx+1} encoder: {W_cvd.shape}")
```

**옵션 B: Measured patterns만 사용**

8색 measured patterns만으로 interpolation (encoder 없이):
- 장점: Overfitting 위험 없음
- 단점: 360° optimization 불가, 8색만 가능

**선택**: **옵션 A** (CVD encoder 학습) → 360° filter 가능!

---

## 🎯 Step 3: 360° Filter Optimization (5-Step Process)

### 3.1 Optimization Problem 정의

**For each original color θ_orig**:

```
Find θ_display that minimizes:

L(θ_display | θ_orig) =
    α * ||Ŷ_cvd(θ_display) - Ŷ_hc(θ_orig)||²  (voxel matching loss)
    + β * ||Decode(Ŷ_cvd(θ_display)) - θ_orig||²  (reconstruction loss)

where:
- Ŷ_hc(θ_orig) = C(θ_orig) @ W_enc_common  (Phase 2)
- Ŷ_cvd(θ_display) = C(θ_display) @ W_enc_cvd  (Step 2)
- Decode(): channel-based decoding (W_enc^T 사용)
```

**Dual constraint 의미**:
1. **Voxel matching**: CVD가 θ_display 보면 HC가 θ_orig 볼 때처럼 반응
2. **Reconstruction**: θ_display decoding 시 θ_orig 복원 (색 인식 정확도)

---

### 3.2 구현: Grid Search vs Gradient-based

#### Option A: Grid Search (1° spacing) ⭐ 권장

```python
def optimize_filter_grid_search(theta_orig, W_enc_hc, W_enc_cvd,
                                alpha=1.0, beta=0.5):
    """
    Grid search로 최적 display color 찾기

    Parameters
    ----------
    theta_orig : float
        원래 색 각도 (0-360)
    W_enc_hc : ndarray (n_channels, n_features)
        HC common encoder
    W_enc_cvd : ndarray (n_channels, n_features)
        CVD individual encoder
    alpha, beta : float
        Loss weights

    Returns
    -------
    theta_display_opt : float
        최적 display color
    loss_opt : float
        최소 loss 값
    """
    # HC target pattern
    C_orig = compute_channel_responses(theta_orig)  # (n_channels,)
    Y_hc_target = C_orig @ W_enc_hc  # (n_features,)

    # Grid search over all possible display colors
    theta_candidates = np.arange(0, 360, 1)  # 1° spacing
    losses = []

    for theta_display in theta_candidates:
        # CVD predicted pattern
        C_display = compute_channel_responses(theta_display)
        Y_cvd_pred = C_display @ W_enc_cvd

        # Loss 1: Voxel matching
        voxel_loss = np.linalg.norm(Y_cvd_pred - Y_hc_target) ** 2

        # Loss 2: Reconstruction accuracy
        # Decode Y_cvd_pred back to angle
        C_hat = Y_cvd_pred @ W_enc_cvd.T @ \
                np.linalg.inv(W_enc_cvd @ W_enc_cvd.T)
        theta_reconstructed = decode_angle_from_channels(C_hat)

        # Circular angular error
        recon_error = np.abs(theta_reconstructed - theta_orig)
        recon_error = min(recon_error, 360 - recon_error)
        recon_loss = recon_error ** 2

        # Total loss
        total_loss = alpha * voxel_loss + beta * recon_loss
        losses.append(total_loss)

    # Find minimum
    min_idx = np.argmin(losses)
    theta_display_opt = theta_candidates[min_idx]
    loss_opt = losses[min_idx]

    return theta_display_opt, loss_opt

# 예시: θ_orig = 45°에 대한 최적 display color
theta_opt, loss = optimize_filter_grid_search(
    theta_orig=45.0,
    W_enc_hc=W_enc_common,
    W_enc_cvd=W_enc_cvd_list[0],  # CVD #1
    alpha=1.0,
    beta=0.5
)

print(f"Original color: 45.0°")
print(f"Optimal display: {theta_opt:.1f}°")
print(f"Shift: {theta_opt - 45.0:.1f}°")
print(f"Loss: {loss:.4f}")
```

---

### 3.3 360° Filter Construction

```python
def construct_360_filter(W_enc_hc, W_enc_cvd, alpha=1.0, beta=0.5):
    """
    360° 전체 각도에 대한 filter 생성

    Returns
    -------
    filter_lookup : ndarray (360, 2)
        [:, 0]: original angles (0-359°)
        [:, 1]: optimal display angles
    """
    theta_orig_range = np.arange(0, 360, 1)  # 1° spacing
    theta_display_opt = np.zeros(360)

    for i, theta_orig in enumerate(theta_orig_range):
        theta_opt, _ = optimize_filter_grid_search(
            theta_orig, W_enc_hc, W_enc_cvd, alpha, beta
        )
        theta_display_opt[i] = theta_opt

        if i % 45 == 0:
            print(f"  θ_orig={theta_orig:3.0f}° → θ_display={theta_opt:3.0f}°")

    filter_lookup = np.column_stack([theta_orig_range, theta_display_opt])

    return filter_lookup

# 각 CVD의 360° filter 생성
filters_360 = []

for cvd_idx in range(3):
    print(f"\n=== CVD {cvd_idx+1} Filter Optimization ===")
    filter_table = construct_360_filter(
        W_enc_common,
        W_enc_cvd_list[cvd_idx],
        alpha=1.0,
        beta=0.5
    )
    filters_360.append(filter_table)

    # 저장
    np.save(f'results/cvd_filters/filter_360_cvd{cvd_idx+1}.npy', filter_table)

print(f"\n✅ 360° filters constructed for all CVDs")
```

---

### 3.4 Parametric Filter (Optional)

Lookup table 대신 parametric function으로 표현:

```python
def fit_parametric_filter(filter_lookup):
    """
    Lookup table → parametric function

    θ_display = f(θ_orig) = θ_orig + g(θ_orig)

    where g(θ_orig) = Σ[a_k * sin(k * θ_orig) + b_k * cos(k * θ_orig)]
    """
    from scipy.optimize import curve_fit

    theta_orig = filter_lookup[:, 0]
    theta_display = filter_lookup[:, 1]

    # Shift function
    shift = theta_display - theta_orig
    shift = np.where(shift > 180, shift - 360, shift)
    shift = np.where(shift < -180, shift + 360, shift)

    # Fourier series fit
    def fourier_shift(theta, a1, b1, a2, b2, a3, b3):
        theta_rad = np.deg2rad(theta)
        return (a1 * np.sin(theta_rad) + b1 * np.cos(theta_rad) +
                a2 * np.sin(2*theta_rad) + b2 * np.cos(2*theta_rad) +
                a3 * np.sin(3*theta_rad) + b3 * np.cos(3*theta_rad))

    params, _ = curve_fit(fourier_shift, theta_orig, shift)

    # Parametric filter
    def filter_function(theta):
        return theta + fourier_shift(theta, *params)

    return filter_function, params

# CVD #1 filter parametric 표현
filter_func, params = fit_parametric_filter(filters_360[0])

print(f"Parametric filter coefficients:")
print(f"  a1={params[0]:.4f}, b1={params[1]:.4f}")
print(f"  a2={params[2]:.4f}, b2={params[3]:.4f}")
print(f"  a3={params[4]:.4f}, b3={params[5]:.4f}")
```

---

## 📊 Step 4: Filter Validation (2-Tier Strategy)

### ⚠️ Validation Tier Overview

**Tier 1: In-Silico Validation** (Current data only)
- Uses existing 8-color measurements
- Validates optimization quality and filter properties
- **Cannot** validate actual CVD responses to filtered stimuli
- **Outcome**: Filter quality metrics, stability analysis

**Tier 2: Empirical Validation** (Future experiments required)
- Requires additional measurements with filtered stimuli
- Validates whether filtered colors actually produce intended brain responses
- **Gold standard** for filter effectiveness
- **Outcome**: Direct evidence of filter working in CVD brains

**⚠️ CRITICAL**: Tier 1 validation has **circular logic risk**:
- Filter is optimized using CVD encoder predictions
- Then validated using same encoder predictions
- **NOT** measuring actual CVD responses to filtered colors
- → Tier 2 empirical validation is essential for true confirmation

---

### 4.1 Tier 1: In-Silico Validation (Current Data)

#### 4.1.1 Hold-out Validation on Measured Colors

```python
def validate_filter_on_measured(filter_lookup, cvd_data_aligned, cvd_labels,
                                W_enc_hc, W_enc_cvd):
    """
    8색 measured data로 filter 검증

    Returns
    -------
    metrics : dict
        - voxel_matching_error: CVD filtered vs HC target
        - reconstruction_error: Decoded angle vs original
    """
    unique_colors = np.unique(cvd_labels)
    voxel_errors = []
    recon_errors = []

    for color in unique_colors:
        # Original angle
        theta_orig = get_angle_from_color_name(color)

        # Filtered display angle (from lookup table)
        theta_display = filter_lookup[int(theta_orig), 1]

        # HC target pattern
        C_orig = compute_channel_responses(theta_orig)
        Y_hc_target = C_orig @ W_enc_hc

        # CVD pattern when seeing filtered color
        mask = cvd_labels == color
        Y_cvd_actual = cvd_data_aligned[mask].mean(axis=0)

        # (Ideally should measure CVD response to θ_display,
        #  but we only have θ_orig measurements)
        # Predicted CVD pattern for filtered color
        C_display = compute_channel_responses(theta_display)
        Y_cvd_pred = C_display @ W_enc_cvd

        # Voxel matching error
        voxel_err = np.linalg.norm(Y_cvd_pred - Y_hc_target)
        voxel_errors.append(voxel_err)

        # Reconstruction error
        C_hat = Y_cvd_pred @ W_enc_cvd.T @ \
                np.linalg.inv(W_enc_cvd @ W_enc_cvd.T)
        theta_recon = decode_angle_from_channels(C_hat)
        recon_err = angular_distance(theta_recon, theta_orig)
        recon_errors.append(recon_err)

    return {
        'voxel_matching_error': np.mean(voxel_errors),
        'reconstruction_error': np.mean(recon_errors),
    }

# Validation
for cvd_idx in range(3):
    metrics = validate_filter_on_measured(
        filters_360[cvd_idx],
        cvd_projected[cvd_idx],
        cvd_labels[cvd_idx],
        W_enc_common,
        W_enc_cvd_list[cvd_idx]
    )

    print(f"\n=== CVD {cvd_idx+1} Filter Validation ===")
    print(f"Voxel matching error: {metrics['voxel_matching_error']:.4f}")
    print(f"Reconstruction error: {metrics['reconstruction_error']:.1f}°")
    print(f"  ✅ Target: < baseline (32° for V1)")
```

---

#### 4.1.2 Filter Stability Analysis

```python
def analyze_filter_stability(filters_360, cvd_ids):
    """
    Filter 안정성 분석

    1. Smoothness: 인접 각도 간 shift 변화
    2. Consistency: CVD 간 filter 유사도
    """
    # (1) Smoothness
    for cvd_idx, filter_table in enumerate(filters_360):
        shifts = filter_table[:, 1] - filter_table[:, 0]
        shifts = np.where(shifts > 180, shifts - 360, shifts)
        shifts = np.where(shifts < -180, shifts + 360, shifts)

        shift_diffs = np.abs(np.diff(shifts))
        smoothness = np.mean(shift_diffs)

        print(f"CVD {cvd_idx+1} filter smoothness: {smoothness:.2f}°/deg")
        print(f"  ✅ Target: < 2.0° (smooth transition)")

    # (2) Inter-CVD consistency
    if len(filters_360) > 1:
        shifts_all = []
        for filter_table in filters_360:
            shifts = filter_table[:, 1] - filter_table[:, 0]
            shifts = np.where(shifts > 180, shifts - 360, shifts)
            shifts = np.where(shifts < -180, shifts + 360, shifts)
            shifts_all.append(shifts)

        shifts_all = np.array(shifts_all)  # (n_cvd, 360)
        consistency = np.std(shifts_all, axis=0).mean()

        print(f"\nInter-CVD filter consistency: {consistency:.2f}°")
        print(f"  해석: CVD 간 filter 차이 (낮을수록 유사)")

# 분석
analyze_filter_stability(filters_360, ['08', '09', '10'])
```

---

### 4.2 Tier 2: Empirical Validation (Future Experiments)

**⚠️ CRITICAL LIMITATION**: Tier 1 validation cannot verify that filtered colors actually work in CVD brains because:
1. We only measured CVD responses to **original 8 colors**, not to **filtered colors**
2. Validation uses **predicted** CVD responses (from encoder), not **actual** measurements
3. Circular logic: Model validates itself

**Tier 2 Solution**: Measure actual CVD responses to optimized filtered stimuli

---

#### 4.2.1 Experimental Design

**New stimulus set**: Optimized filtered colors
```python
# For each CVD, select test colors
test_colors_orig = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 original

# Generate filtered stimuli using optimized filters
filtered_stimuli = {}
for cvd_id in ['08', '09', '10']:
    filter_table = filters_360[cvd_id]
    filtered_angles = []

    for theta_orig in test_colors_orig:
        theta_display = filter_table[int(theta_orig), 1]
        filtered_angles.append(theta_display)

    filtered_stimuli[cvd_id] = filtered_angles

# Example output:
# CVD 08 filtered stimuli: [15°, 60°, 105°, ...] (shifted from original)
```

**Experimental protocol**:
1. Present **both original and filtered colors** to each CVD
2. Measure fMRI responses (same protocol as Phase 1)
3. Extract trial-wise beta maps (LS-S)
4. Compare:
   - CVD response to **filtered** color (e.g., 15°)
   - HC response to **original** color (e.g., 0°)
   - ✅ **Success**: High correlation (> 0.70)

---

#### 4.2.2 Validation Metrics (Empirical)

```python
def empirical_filter_validation(cvd_measured_filtered, hc_measured_orig,
                                filtered_angles, orig_angles):
    """
    Empirical validation using actual measurements

    Parameters
    ----------
    cvd_measured_filtered : ndarray (n_colors, n_voxels)
        CVD actual responses to FILTERED colors
    hc_measured_orig : ndarray (n_colors, n_voxels)
        HC actual responses to ORIGINAL colors

    Returns
    -------
    correlation : float
        Pattern correlation between CVD(filtered) and HC(original)
    """
    correlations = []

    for i, (theta_filt, theta_orig) in enumerate(zip(filtered_angles, orig_angles)):
        cvd_pattern = cvd_measured_filtered[i]  # Measured, not predicted!
        hc_pattern = hc_measured_orig[i]

        corr = np.corrcoef(cvd_pattern, hc_pattern)[0, 1]
        correlations.append(corr)

        print(f"Color {theta_orig}° → {theta_filt}°: r = {corr:.3f}")

    mean_corr = np.mean(correlations)
    print(f"\n✅ Mean pattern correlation: {mean_corr:.3f}")
    print(f"   Target: > 0.70 (strong match)")

    return mean_corr

# GOLD STANDARD VALIDATION
empirical_corr = empirical_filter_validation(
    cvd_measured_filtered=cvd_new_measurements,  # NEW DATA REQUIRED
    hc_measured_orig=hc_color_patterns,
    filtered_angles=filtered_stimuli['08'],
    orig_angles=test_colors_orig
)
```

**Success Criteria (Tier 2)**:
- ✅ **필수**: Mean pattern correlation > 0.70
- ✅ **필수**: Correlation significantly higher than baseline (CVD original vs HC)
- ⭐ **우수**: Correlation > 0.80 (near-perfect match)

---

#### 4.2.3 Behavioral Validation (Optional)

**Additional validation**: Psychophysical color discrimination
```markdown
Experiment: Can CVD discriminate filtered colors as well as HC discriminate originals?

Protocol:
1. 2AFC task: "Which circle is different?"
2. HC: Original colors (e.g., 0° vs 45°)
3. CVD: Filtered colors (e.g., 15° vs 60°)
4. Measure d' (discrimination sensitivity)

Prediction:
- IF filter works: d'_cvd(filtered) ≈ d'_hc(original)
- Better than: d'_cvd(original) << d'_hc(original)
```

**Timeline**: Tier 2 validation requires 2-4 weeks additional scanning + analysis

---

## 📋 Deliverables (Phase 3 산출물)

### 코드
- [ ] `scripts/08_cvd_projection.py`: CVD → common space
- [ ] `scripts/09_cvd_encoder.py`: CVD individual encoder
- [ ] `scripts/10_filter_optimization.py`: 360° filter search
- [ ] `scripts/11_filter_validation.py`: Filter 검증

### 모델
- [ ] **CVD encoders** (CVD 3명 × ROIs)
  - Individual encoder per CVD
- [ ] **360° filters** (CVD 3명 × ROIs)
  - Lookup table: θ_orig → θ_display
  - Parametric function (optional)

### 결과
- [ ] Filter lookup tables (360 × 2)
- [ ] Voxel matching errors
- [ ] Reconstruction errors
- [ ] Filter stability metrics
- [ ] Filter visualization (shift curves)

---

## ⚠️ 예상 문제 및 해결책

### 문제 1: Filter가 identity에 가까움
**증상**: θ_display ≈ θ_orig (거의 shift 없음)

**원인**:
- Reconstruction loss β가 너무 큼 → shift 억제
- CVD encoder가 HC와 너무 유사 (왜곡 미반영)
- Optimization이 local minimum

**해결**:
1. **α/β 비율 조정**: β ↓ (0.5 → 0.2)
2. **CVD encoder 재확인**: 실제 CVD 왜곡 학습 여부 체크
3. **Multiple initializations**: Grid search 범위 확대

---

### 문제 2: Filter가 불연속 (급격한 shift 변화)
**증상**: 인접 각도 간 shift > 10°

**원인**:
- Encoder noise
- Optimization landscape 복잡
- Overfitting to 8 measured colors

**해결**:
1. **Smoothing regularization 추가**:
   ```python
   smooth_loss = np.sum((shifts[1:] - shifts[:-1])**2)
   total_loss += gamma * smooth_loss
   ```
2. **Parametric filter 사용** (Fourier series로 smooth 보장)
3. **Post-hoc smoothing** (circular Gaussian filter)

---

### 문제 3: Validation error가 baseline보다 나쁨
**증상**: Reconstruction error > 32°

**원인**:
- Phase 2 encoder 성능 부족 (Decision Point #4)
- α/β 균형 부적절
- CVD measurement noise 큼

**해결**:
1. **Decision Point #4 발동**: Phase 2 재점검
2. **α/β grid search**:
   ```python
   for alpha in [0.5, 1.0, 2.0]:
       for beta in [0.1, 0.5, 1.0]:
           ...
   ```
3. **Ensemble filter**: Multiple α/β 조합 평균

---

## 🎯 Success Criteria

**Filter Quality**:
- ✅ **필수**: Smoothness < 2.0°/deg
- ⭐ **우수**: Smoothness < 1.0°/deg

**Performance**:
- ✅ **필수**: Reconstruction error ≤ baseline (no worse than no filter)
- ⭐ **우수**: Reconstruction error < baseline - 5° (improvement)

**Stability**:
- ✅ **필수**: Inter-CVD filter consistency < 10° (같은 CVD 유형이면 유사)
- ⭐ **우수**: Consistency < 5°

---

---

## 🚀 다음 단계: Tier 2 Empirical Validation

**Current Phase 3 scope**: Tier 1 in-silico validation
- ✅ Filter optimization using current data
- ✅ Quality metrics (smoothness, consistency, reconstruction)
- ⚠️ **Limitation**: Self-validation (circular logic)

**Next phase (Tier 2)**: Empirical validation with new measurements
- 📋 Design: See Section 4.2 for detailed protocol
- 🎯 Goal: Measure actual CVD responses to optimized filtered stimuli
- ⏱️ Timeline: 2-4 weeks additional scanning + analysis
- ✅ Outcome: Gold standard evidence for filter effectiveness

**Decision Point**: After Tier 1 completion
- IF Tier 1 metrics pass thresholds → Proceed to Tier 2 experiments
- ELSE → Revisit optimization strategy or Phase 1/2 parameters

**업데이트**: 2025-12-28
