# Phase 2: Continuous Hue Interpolation Model

**목표**: 360° circular hue space 내 연속 색에 대한 voxel 반응 예측 모델 개발
**방법**: Channel-based encoder (Brouwer & Heeger, 2009)
**예상 기간**: 1-2주 (Week 3-4)
**담당**: 모델 개발팀

---

## 🎯 Phase 2 목표 및 Phase 3 연계

### Why This Phase Matters?

**Phase 1의 결과물**:
- ✅ HC common space (hyperalignment using trial-aligned GPA)
- ✅ 좌표계 정렬된 HC 데이터

**Phase 2의 역할**:
> **🔬 Hypothesis: Continuous hue interpolation within circular color space**
>
> **We hypothesize that**:
> - Channel-based encoding allows **interpolation** between measured hues (8 colors at 45° spacing)
> - This hypothesis is **directly testable** only at measured angles (via LOCO CV)
> - Predictions for intermediate angles (e.g., 22.5°, 30°) rely on **indirect validation** (smoothness, consistency, plausibility)
>
> **Phase 3 Dependency**:
> - Phase 3 optimization framework **requires** this encoder to predict voxel responses for arbitrary display colors
> - Without this encoder: filter optimization limited to 8 discrete colors only

**Phase 3 연계**:
```
Phase 2 Encoder를 사용하여:
For each original color θ_orig:
    θ_display = argmin_θ [
        ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²  ← Phase 2 encoder로 Ŷ_hc(θ_orig) 예측!
        + λ ||Decode(Ŷ_cvd(θ)) - θ_orig||²
    ]
```
→ **Encoder가 없으면 8색에만 filter 적용 가능, encoder 있으면 360° 전체 최적화 가능!**

---

### Primary Objectives

1. **Channel response function 정의** (circular 360° space)
2. **HC common space에서 공용 encoder 학습**
3. **2-tier validation**:
   - Direct: LOCO CV (45° spacing interpolation)
   - Indirect: RDM smoothness, Inter-encoder consistency
4. **Common vs Individual encoder 비교**

---

### Success Criteria

**Direct Validation (LOCO CV)**:
- ✅ **필수**: Reconstruction error < 60° (chance: 90°, baseline: 32°)
- ⭐ **우수**: Error < 45°

**Indirect Validation (Quality Metrics)**:
- ✅ **필수**: RDM correlation > 0.50
- ✅ **필수**: Smoothness (연속성): adjacent angle diff < 0.1
- ⭐ **우수**: Inter-encoder consistency (5 HC) > 0.70

**Common vs Individual**:
- ✅ **필수**: Δ < 15° (common이 individual 대비 크게 나쁘지 않음)
- ⭐ **우수**: Δ < 10° (comparable)

---

### ⚠️ Recommended Validation Strategy

**Problem**: With only 8 measured colors (45° spacing), we have **limited ground truth** for validating continuous interpolation.

**Recommendation**: **Start with denser measurements before committing to full 360° predictions**

**Validation Grid Progression**:
```markdown
Stage 1 (Current): 8 colors at 45° spacing
↓ LOCO CV validation
Stage 2 (Recommended): 16 colors at 22.5° spacing
↓ Better interpolation validation (narrower gaps)
Stage 3 (Optional): 32 colors at 11.25° spacing
↓ High-confidence interpolation
Stage 4 (Full): 360° at 1° spacing (for Phase 3 optimization)
```

**Rationale**:
- ✅ **16-32 colors** allows **direct validation** of interpolation quality at intermediate angles
- ✅ Reduces reliance on **indirect metrics** (smoothness, consistency)
- ✅ Provides empirical evidence for interpolation hypothesis
- ❌ **360° predictions without additional measurements** = **extrapolation beyond validation scope**

**Action for Phase 2**:
1. Implement encoder with current 8-color data
2. Pass LOCO CV thresholds (error < 60°)
3. ⭐ **Recommend additional data collection** (16 or 32 colors) before Phase 3
4. If no additional data: Proceed with strong caveats on intermediate angle predictions

---

## 📐 Step 1: Channel Response Function 정의

### 1.1 이론적 배경

**Brouwer & Heeger (2009) 모델**:
```
Voxel response = Σ(channel_i × weight_i)

Channel_i(θ) = cos^2((θ - θ_i) / σ)  if |θ - θ_i| < 90°
                0                      otherwise
```

**파라미터**:
- n_channels: 6 (기본) 또는 8, 16 (고해상도)
- channel centers: 0°, 60°, 120°, 180°, 240°, 300° (6개)
- bandwidth σ: ~30° (추정치, 데이터로 최적화 가능)

### 1.2 구현

```python
import numpy as np

def compute_channel_responses(theta, n_channels=6, bandwidth=30):
    """
    연속 색 각도에 대한 channel responses

    Parameters
    ----------
    theta : float or array
        색 각도 (degrees, 0-360)
    n_channels : int
        채널 수 (기본 6)
    bandwidth : float
        채널 bandwidth (degrees)

    Returns
    -------
    responses : ndarray (n_channels,) or (len(theta), n_channels)
        각 채널의 반응 값
    """
    # Channel centers (균등 분포)
    centers = np.linspace(0, 360, n_channels, endpoint=False)

    # theta를 array로
    theta = np.atleast_1d(theta)

    responses = np.zeros((len(theta), n_channels))

    for i, center in enumerate(centers):
        # Angular distance (circular)
        diff = np.abs(theta - center)
        diff = np.minimum(diff, 360 - diff)

        # Half-wave cosine^2
        response = np.cos(np.deg2rad(diff / bandwidth)) ** 2
        response[diff > 90] = 0  # Half-wave rectification

        responses[:, i] = response

    return responses.squeeze()

# 예시: 8색 + 연속 색
color_angles_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315])
channel_8 = compute_channel_responses(color_angles_8)
print(f"8색 channel responses: {channel_8.shape}")  # (8, 6)

# 연속 색 (1° 간격)
theta_continuous = np.arange(0, 360, 1)
channel_continuous = compute_channel_responses(theta_continuous)
print(f"연속 색 channel responses: {channel_continuous.shape}")  # (360, 6)
```

### 1.3 시각화

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# (A) Channel tuning curves
ax = axes[0]
for i in range(6):
    ax.plot(theta_continuous, channel_continuous[:, i],
            label=f'Ch {i+1} ({i*60}°)')
ax.set_xlabel('Color Angle (degrees)')
ax.set_ylabel('Channel Response')
ax.set_title('(A) Channel Tuning Curves')
ax.legend()
ax.grid(True, alpha=0.3)

# (B) 8색에 대한 channel responses (heatmap)
ax = axes[1]
im = ax.imshow(channel_8.T, aspect='auto', cmap='hot')
ax.set_xticks(range(8))
ax.set_xticklabels([f'{ang}°' for ang in color_angles_8])
ax.set_yticks(range(6))
ax.set_yticklabels([f'Ch {i+1}' for i in range(6)])
ax.set_xlabel('Color Angle')
ax.set_ylabel('Channel')
ax.set_title('(B) Channel Responses for 8 Colors')
plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.savefig('results/prediction_validation/channel_responses.png', dpi=300)
```

---

## 🧠 Step 2: Encoder 학습

### 2.1 Common Encoder (HC common space)

**모델 구조**:
```
θ → C(θ) → W_enc → ŷ(θ)

C(θ): (n_channels,) channel responses
W_enc: (n_channels, n_features) encoding matrix
ŷ(θ): (n_features,) predicted voxel pattern in common space
```

**학습**:
```python
def train_encoder_common(hc_data_aligned, trial_labels, n_channels=6):
    """
    HC common space에서 encoder 학습

    Parameters
    ----------
    hc_data_aligned : list of ndarray
        각 HC의 정렬된 trial-wise 데이터
    trial_labels : list of arrays
        각 trial의 색 레이블
    n_channels : int
        채널 수

    Returns
    -------
    W_enc : ndarray (n_channels, n_features)
        Encoding matrix
    """
    # 모든 HC 데이터 결합
    all_trials = np.vstack(hc_data_aligned)
    all_labels = np.concatenate(trial_labels)

    # 색별 평균 패턴
    unique_colors = np.unique(all_labels)
    color_patterns = []
    color_angles = []

    for color in unique_colors:
        mask = all_labels == color
        color_patterns.append(all_trials[mask].mean(axis=0))
        color_angles.append(get_angle_from_color_name(color))

    color_patterns = np.array(color_patterns)  # (8, n_features)
    color_angles = np.array(color_angles)      # (8,)

    # Channel responses
    C = compute_channel_responses(color_angles, n_channels)  # (8, n_channels)

    # Encoder: Y = C @ W_enc
    # W_enc = (C^T C)^{-1} C^T Y
    W_enc = np.linalg.lstsq(C, color_patterns, rcond=None)[0]
    # (n_channels, n_features)

    return W_enc, color_angles, color_patterns

# 학습
W_enc_common, angles_8, patterns_8 = train_encoder_common(
    hc_data_aligned, trial_labels
)

print(f"Common encoder shape: {W_enc_common.shape}")
# 예: (6, 50) for 6 channels, 50 features
```

### 2.2 Individual Encoders

```python
def train_encoder_individual(subj_data_aligned, trial_labels, n_channels=6):
    """개별 subject의 encoder 학습"""
    unique_colors = np.unique(trial_labels)
    color_patterns = []
    color_angles = []

    for color in unique_colors:
        mask = trial_labels == color
        color_patterns.append(subj_data_aligned[mask].mean(axis=0))
        color_angles.append(get_angle_from_color_name(color))

    color_patterns = np.array(color_patterns)
    color_angles = np.array(color_angles)

    C = compute_channel_responses(color_angles, n_channels)
    W_enc_ind = np.linalg.lstsq(C, color_patterns, rcond=None)[0]

    return W_enc_ind

# 각 HC별 encoder
W_enc_individual = []
for s_idx in range(len(hc_subjects)):
    W_ind = train_encoder_individual(
        hc_data_aligned[s_idx],
        trial_labels[s_idx]
    )
    W_enc_individual.append(W_ind)
```

---

## 🔍 Step 3: LOCO Cross-Validation

### 3.1 Leave-One-Color-Out 검증

```python
def loco_cv(hc_data_aligned, trial_labels, n_channels=6):
    """
    Leave-One-Color-Out cross-validation

    각 색을 한 번씩 hold-out하고,
    나머지 7색으로 encoder 학습,
    hold-out 색 예측

    Returns
    -------
    reconstruction_errors : dict
        {color: mean_error_degrees}
    """
    unique_colors = np.unique(np.concatenate(trial_labels))
    errors_by_color = {}

    for held_out_color in unique_colors:
        print(f"\nHold-out: {held_out_color}")

        # Training data (7 colors)
        train_data = []
        train_labels = []
        test_data = []
        test_labels = []

        for s_idx in range(len(hc_data_aligned)):
            mask = np.array(trial_labels[s_idx]) != held_out_color
            train_data.append(hc_data_aligned[s_idx][mask])
            train_labels.append(np.array(trial_labels[s_idx])[mask])

            mask_test = np.array(trial_labels[s_idx]) == held_out_color
            test_data.append(hc_data_aligned[s_idx][mask_test])

        # Encoder 학습 (7 colors)
        W_enc_7 = train_encoder_common(train_data, train_labels, n_channels)

        # Held-out color 예측
        held_out_angle = get_angle_from_color_name(held_out_color)
        C_test = compute_channel_responses(held_out_angle, n_channels)  # (n_channels,)
        predicted_pattern = C_test @ W_enc_7  # (n_features,)

        # 실제 패턴 (test data 평균)
        actual_pattern = np.vstack(test_data).mean(axis=0)

        # Decode back to angle
        # Method 1: Channel-based decoding
        C_hat = predicted_pattern @ W_enc_7.T @ \
                np.linalg.inv(W_enc_7 @ W_enc_7.T)
        predicted_angle = decode_angle_from_channels(C_hat)

        # Angular error
        error = np.abs(predicted_angle - held_out_angle)
        error = min(error, 360 - error)  # Circular

        errors_by_color[held_out_color] = error
        print(f"  Predicted: {predicted_angle:.1f}°, Actual: {held_out_angle:.1f}°")
        print(f"  Error: {error:.1f}°")

    return errors_by_color

# 실행
errors_loco = loco_cv(hc_data_aligned, trial_labels)

print(f"\n=== LOCO CV Results ===")
print(f"Mean error: {np.mean(list(errors_loco.values())):.1f}°")
print(f"Std error:  {np.std(list(errors_loco.values())):.1f}°")
print(f"Chance level: 90.0°")
```

### 3.2 시각화

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# (A) LOCO errors by color
ax = axes[0]
colors = list(errors_loco.keys())
errors = list(errors_loco.values())
bars = ax.bar(range(8), errors)
ax.axhline(90, color='red', linestyle='--', label='Chance')
ax.axhline(np.mean(errors), color='blue', linestyle='--', label='Mean')
ax.set_xticks(range(8))
ax.set_xticklabels([f'{c}' for c in colors], rotation=45)
ax.set_ylabel('Reconstruction Error (degrees)')
ax.set_title('(A) LOCO CV Errors by Color')
ax.legend()

# (B) Common vs Individual encoder
ax = axes[1]
# Individual errors (각 subject별)
individual_errors = []
for s_idx in range(len(hc_subjects)):
    errors_ind = loco_cv_individual(hc_data_aligned[s_idx],
                                    trial_labels[s_idx])
    individual_errors.append(np.mean(list(errors_ind.values())))

common_error = np.mean(list(errors_loco.values()))

ax.boxplot([individual_errors, [common_error]*len(hc_subjects)],
           labels=['Individual', 'Common'])
ax.set_ylabel('Mean Reconstruction Error (degrees)')
ax.set_title('(B) Common vs Individual Encoder')

plt.tight_layout()
plt.savefig('results/prediction_validation/loco_cv_results.png', dpi=300)
```

---

## 🎨 Step 4: Continuous Hue Interpolation (360°)

### 4.1 용어 명확화: Interpolation vs Extrapolation

**중요한 개념적 구분**:

```markdown
✅ **Interpolation** (우리 케이스):
- 360° circular hue space 내에서 dense sampling
- 8개 measured colors 사이의 각도들 예측
- 예: 22.5°, 67.5°, 112.5° (45° 간격 사이)
- 범위 "밖"이 없음 (circular)

❌ **Extrapolation** (아님):
- 측정 범위 "밖"으로 확장
- 선형 공간에서만 의미 있음 (예: 0-100 → 150 예측)
- 360° circular space에는 "밖"이 없음!

📝 **표현 가이드**:
✅ "Continuous hue interpolation within 360° circular space"
✅ "Dense angular sampling based on 8 trained hues"
✅ "Predicting intermediate hues between measured colors"
❌ "Novel color prediction" (애매함)
❌ "Extrapolation to unseen colors"
```

---

### 4.2 연속 색 공간 예측

```python
def predict_continuous_hues(W_enc, theta_range=np.arange(0, 360, 1)):
    """
    360° circular hue space 내 연속 각도에 대한 voxel patterns 예측

    ⚠️ Interpolation within circular space (not extrapolation)

    Parameters
    ----------
    W_enc : ndarray (n_channels, n_features)
        Encoder matrix (learned from 8 measured hues)
    theta_range : array
        예측할 색 각도 (degrees, 0-360)
        Default: 1° spacing for dense interpolation

    Returns
    -------
    predicted_patterns : ndarray (len(theta_range), n_features)
        각 각도의 예측 voxel pattern (HC common space)
    """
    # Channel responses for continuous hues
    C_continuous = compute_channel_responses(theta_range)  # (360, n_channels)

    # Predicted voxel patterns
    predicted_patterns = C_continuous @ W_enc  # (360, n_features)

    return predicted_patterns

# 예측 실행
theta_range = np.arange(0, 360, 1)  # 1° spacing
patterns_360 = predict_continuous_hues(W_enc_common, theta_range)

print(f"✅ Continuous hue interpolation:")
print(f"  Input: 8 measured colors (45° spacing)")
print(f"  Output: {patterns_360.shape[0]} interpolated patterns (1° spacing)")
print(f"  Feature space: {patterns_360.shape[1]} dimensions")

# RDM 계산 (연속 색 공간)
rdm_continuous = compute_rdm(patterns_360)  # (360, 360)

# 8색 위치 표시
measured_indices = [int(ang) for ang in angles_8]
```

---

### 4.3 Indirect Validation (품질 지표)

**Why Indirect?**
> Direct validation은 LOCO CV로 45° 간격만 검증 가능.
> 중간 각도 (예: 22.5°, 30°)는 ground truth가 없음.
> → **Indirect metrics**로 interpolation 품질 평가

---

#### (1) RDM Consistency & Smoothness

```python
def evaluate_rdm_quality(patterns_continuous, patterns_measured, measured_indices):
    """
    RDM 기반 품질 평가

    Returns
    -------
    metrics : dict
        - rdm_correlation: 측정된 8색 위치에서 RDM 유사도
        - rdm_smoothness: 연속 RDM의 smoothness
    """
    from scipy.stats import spearmanr

    # (1) 8색 위치에서 RDM 비교
    predicted_8 = patterns_continuous[measured_indices]
    rdm_predicted = compute_rdm(predicted_8)
    rdm_actual = compute_rdm(patterns_measured)

    rdm_corr = spearmanr(
        rdm_predicted[np.triu_indices(8, k=1)],
        rdm_actual[np.triu_indices(8, k=1)]
    ).correlation

    # (2) RDM Smoothness (연속성)
    # 인접 각도 간 RDM 행 차이
    rdm_full = compute_rdm(patterns_continuous)  # (360, 360)
    rdm_diffs = np.diff(rdm_full, axis=0)  # (359, 360)
    smoothness = np.mean(np.abs(rdm_diffs))

    metrics = {
        'rdm_correlation': rdm_corr,
        'rdm_smoothness': smoothness,
    }

    return metrics

# 평가
rdm_metrics = evaluate_rdm_quality(patterns_360, patterns_8, measured_indices)

print(f"\n=== RDM Quality Metrics ===")
print(f"RDM correlation (8 colors): {rdm_metrics['rdm_correlation']:.3f}")
print(f"  ✅ Target: > 0.50")
print(f"RDM smoothness: {rdm_metrics['rdm_smoothness']:.4f}")
print(f"  ✅ Target: < 0.10 (lower = smoother)")
```

---

#### (2) Inter-Encoder Consistency (5 HC)

```python
def inter_encoder_consistency(W_enc_list, theta_test=None):
    """
    5명 HC의 individual encoder 간 일치도

    같은 색 각도를 예측했을 때 패턴이 얼마나 유사한가?

    Parameters
    ----------
    W_enc_list : list of ndarray
        각 HC의 individual encoder (5개)
    theta_test : array, optional
        테스트할 각도들 (default: 8색 + 중간 각도들)

    Returns
    -------
    consistency : float
        Pairwise pattern correlation 평균
    """
    if theta_test is None:
        # 8색 + 중간 각도 (22.5°, 67.5°, ...)
        theta_test = np.concatenate([
            angles_8,
            angles_8 + 22.5
        ])

    # 각 encoder로 예측
    predictions = []
    for W_enc in W_enc_list:
        C_test = compute_channel_responses(theta_test)
        patterns = C_test @ W_enc
        predictions.append(patterns)

    # Pairwise correlation
    correlations = []
    for i in range(len(predictions)):
        for j in range(i+1, len(predictions)):
            corr = np.corrcoef(
                predictions[i].ravel(),
                predictions[j].ravel()
            )[0, 1]
            correlations.append(corr)

    return np.mean(correlations)

# 평가
consistency = inter_encoder_consistency(W_enc_individual)

print(f"\n=== Inter-Encoder Consistency ===")
print(f"5 HC encoders consistency: {consistency:.3f}")
print(f"  ✅ Target: > 0.70")
print(f"  해석: 높을수록 HC 간 예측 일치 → 안정적 interpolation")
```

---

#### (3) Channel Theoretical Plausibility

```python
def check_channel_plausibility(W_enc, n_channels=6):
    """
    Encoder weights가 channel 이론과 일치하는지 확인

    예상: 각 voxel이 특정 channel에 선택적으로 반응
    → W_enc의 각 column (voxel)이 특정 channel에 peak

    Returns
    -------
    plausibility_score : float
        0-1, 높을수록 이론적으로 타당
    """
    # W_enc: (n_channels, n_features)
    # 각 feature (voxel)의 preferred channel
    preferred_channels = np.argmax(np.abs(W_enc), axis=0)

    # 각 channel이 최소 1개 이상의 voxel을 가지는가?
    unique_channels = len(np.unique(preferred_channels))
    coverage = unique_channels / n_channels

    # Weight distribution의 selectivity
    # High selectivity = 각 voxel이 1-2개 channel에만 강하게 반응
    W_norm = W_enc / (np.linalg.norm(W_enc, axis=0, keepdims=True) + 1e-10)
    selectivity = np.mean(np.max(np.abs(W_norm), axis=0))

    plausibility_score = (coverage + selectivity) / 2

    return plausibility_score, {
        'coverage': coverage,
        'selectivity': selectivity,
    }

# 평가
plausibility, details = check_channel_plausibility(W_enc_common)

print(f"\n=== Channel Theoretical Plausibility ===")
print(f"Overall plausibility: {plausibility:.3f}")
print(f"  Channel coverage: {details['coverage']:.3f} (all 6 channels used?)")
print(f"  Weight selectivity: {details['selectivity']:.3f} (voxels selective?)")
print(f"  ✅ Target: > 0.60")
```

---

## 📊 Deliverables (Phase 2 산출물)

### 코드
- [ ] `scripts/04_channel_encoder.py`: Encoder 학습 및 예측
- [ ] `scripts/05_loco_cv.py`: LOCO cross-validation
- [ ] `scripts/06_continuous_interpolation.py`: 360° hue interpolation
- [ ] `scripts/07_indirect_validation.py`: 품질 지표 평가

### 모델
- [ ] **Common encoder** (W_enc_common)
  - HC common space에서 학습
  - Phase 3 optimization의 핵심 기반
- [ ] **Individual encoders** (각 HC × 5)
  - Consistency 평가용
- [ ] **Channel response functions**
  - 6 channels, bandwidth optimized

### 결과

**Direct Validation**:
- [ ] LOCO CV errors (8 colors, 45° spacing)
- [ ] Common vs individual comparison

**Indirect Validation**:
- [ ] RDM correlation & smoothness
- [ ] Inter-encoder consistency (5 HC)
- [ ] Channel theoretical plausibility

**360° Predictions**:
- [ ] Continuous hue patterns (1° spacing)
- [ ] RDM heatmap (360×360)

### 시각화
- [ ] Channel tuning curves (6 channels)
- [ ] LOCO CV results (error by color)
- [ ] 2-tier validation summary
- [ ] Continuous color space visualization

---

## 🔗 Phase 3 연계: Optimization Framework 준비

**Phase 2 산출물이 Phase 3에서 사용되는 방식**:

```python
# Phase 3에서의 활용:

# (1) HC encoder로 임의의 각도에 대한 "expected HC response" 예측
Ŷ_hc(θ_orig) = C(θ_orig) @ W_enc_common  # Phase 2 encoder 사용!

# (2) CVD filter optimization
for θ_orig in [0°, 1°, 2°, ..., 359°]:
    # 목표: CVD가 어떤 색 θ_display를 보면 HC가 θ_orig 볼 때처럼 반응할까?

    θ_display = argmin_θ [
        # Loss 1: Voxel pattern matching
        ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²

        # Loss 2: Reconstruction accuracy
        + λ * ||Decode(Ŷ_cvd(θ)) - θ_orig||²
    ]

    # Filter: θ_orig → θ_display
    Filter[θ_orig] = θ_display
```

**핵심**:
- ✅ Phase 2 encoder 없으면: 8색에만 filter 적용 가능
- ⭐ Phase 2 encoder 있으면: **360° 전체 각도에 대해 최적 display 색 찾기 가능!**

---

## ⚠️ 예상 문제 및 해결책

### 문제 1: LOCO 성능이 chance level
**증상**: Reconstruction error > 80°

**원인**:
- 7색으로는 학습 부족 (underfitting)
- Channel bandwidth 부적절
- Common space 정렬 실패 (Phase 1 문제)

**해결**:
1. **Regularization** (ridge regression):
   ```python
   W_enc = np.linalg.lstsq(C.T @ C + λ*I, C.T @ Y, rcond=None)[0]
   ```
2. **Bandwidth 최적화** (grid search: 20°, 30°, 40°)
3. **Decision Point 발동**: Phase 1 재점검
4. **Channel 수 조정** (6 → 8 → 4 시도)

---

### 문제 2: Individual vs common 차이 큼
**증상**: Individual이 common보다 30° 이상 좋음

**원인**:
- HC 간 variability가 실제로 큼
- Common space 정렬이 불완전
- Individual이 overfitting

**해결**:
1. **Phase 1 Decision Point #2 발동**: Alignment + Downstream 분리
2. **Hybrid model**:
   - Common encoder를 prior로
   - Individual encoder는 fine-tuning으로
   ```python
   W_ind = W_common + α * ΔW_subject
   ```
3. **Phase 3에서 유연하게 선택**:
   - CVD filter 학습 시 common/individual 중 성능 좋은 것 사용

---

### 문제 3: 연속 색 예측이 불연속 (Smoothness 낮음)
**증상**: 인접 각도 간 급격한 변화, RDM smoothness > 0.15

**원인**:
- Channel bandwidth 너무 좁음
- Noise in encoder weights
- Channel 수 부족

**해결**:
1. **Bandwidth 증가** (30° → 40°)
2. **Gaussian Process Regression**:
   ```python
   from sklearn.gaussian_process import GaussianProcessRegressor
   gp = GaussianProcessRegressor(kernel=...)
   gp.fit(angles_8, patterns_8)
   patterns_360 = gp.predict(theta_range)
   ```
3. **Post-hoc smoothing** (circular Gaussian filter)
4. **Spline interpolation** (circular 1D spline)

---

## 🚧 Decision Points

### Decision Point #4: LOCO Error > 70°

**조건**: LOCO CV mean error > 70° (chance: 90°)

**판단**: Encoder 성능 불충분

**분기**:
- **Option A**: Phase 1 재점검 → GPA 파라미터 조정
- **Option B**: Channel 구조 변경 (n_channels, bandwidth)
- **Option C**: Phase 3에서 8색만 사용 (360° optimization 포기)

**판단 시점**: LOCO CV 완료 후

---

### Decision Point #5: Indirect Validation 실패

**조건**: RDM smoothness > 0.15 OR Inter-encoder consistency < 0.50

**판단**: Interpolation 품질 낮음 (중간 각도 신뢰도 낮음)

**분기**:
- **Option A**: Smoothing 강화 (Gaussian Process)
- **Option B**: Phase 3에서 조심스럽게 사용:
  - Filter optimization 시 regularization 강화
  - Validation 강조 (filtered colors로 실제 측정)
- **Option C**: 8색 + LOCO-validated 45° midpoints만 사용 (16 colors)
- **Option D (⭐ Recommended)**: **Additional data collection before Phase 3**:
  - Measure 16 colors (22.5° spacing) or 32 colors (11.25° spacing)
  - Re-train encoder with denser measurements
  - Direct validation of interpolation at finer scales
  - **Higher confidence** for Phase 3 optimization

**판단 시점**: Indirect validation 완료 후

---

**다음 단계**: **Phase 3 (CVD Filter Optimization via 360° Search)**

**업데이트**: 2025-12-28
