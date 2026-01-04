# Phase 1: Hyperalignment for HC Common Space

**목표**: HC 5명의 뇌 반응을 공통 표현 공간으로 정렬
**방법**: Hyperalignment using trial-aligned GPA (Generalized Procrustes Analysis)
**예상 기간**: 2주 (Week 2-3)
**담당**: 데이터 분석팀

---

## 🎯 Phase 1 목표 및 근거

### Why Hyperalignment First?

**기존 분석 결과 (V1/V2)**:
- ✅ **Procrustes stability**: 0.91/0.88 (매우 높음) → 구조는 같음
- ❌ **RDM correlation**: 0.26/0.24 (낮음) → 좌표계가 다름

**해석**:
> HC들이 같은 색 구조를 표현하지만 서로 다른 좌표계를 사용함
> → **Common space에서 봐야 안정적인 encoder 학습 가능!**

### Primary Objectives
1. Trial-wise voxel 패턴 추출 (LS-S GLM)
2. HC-only hyperalignment 수행 (trial-aligned GPA)
3. 정렬 품질 평가 (2-tier strategy)
4. Common W 재학습 및 성능 비교

### Success Criteria

**Tier-1: Trial-level Metrics**
- Inter-subject correlation (trial-wise) > 0.30
- LOSO (Leave-One-Subject-Out) decoding > 25% (chance: 12.5%)

**Tier-2: Color-level Metrics**
- Procrustes disparity < 0.08 (baseline: 0.089)
- Run-split stability > 0.80 (baseline: 0.91)
- RDM between-subject correlation > 0.30 (baseline: 0.26)

**Downstream Performance**
- Common W reconstruction error ≤ baseline (32° for V1)

---

## 📊 Step 1: 데이터 구조 분석 및 Trial-wise 추출

### 1.1 현재 데이터 구조 확인

**필요 정보**:
```python
# 각 subject의 실험 구조
- n_runs: 6
- n_colors: 8 (+ gray)
- trials_per_color_per_run: 8
- total_trials: 6 × 8 × 8 = 384 (색 trial만)
- TR: ?
- trial_duration: ?
- ITI: ?
```

**확인 항목**:
- [ ] Events/stimulus files 위치 및 형식
- [ ] Run별 자극 순서 동일성
- [ ] Timing 정보 (onset, duration)
- [ ] Bold preprocessing outputs

**실행 코드**:
```python
import pandas as pd
from pathlib import Path

# Subject 02 예시
subject_id = '02'
base_path = Path('/storage/connectome/haba6030/colorBlind_data_deoblique')
events_path = base_path / f'sub-{subject_id}' / 'func'

# Run 1-6의 events 파일 로드
for run_id in range(1, 7):
    events_file = events_path / f'sub-{subject_id}_task-rsvp_run-{run_id}_events.tsv'
    df = pd.read_csv(events_file, sep='\t')
    print(f"Run {run_id}:")
    print(f"  Trials: {len(df)}")
    print(f"  Unique colors: {df['trial_type'].unique()}")
    print(f"  Onset range: {df['onset'].min():.1f} - {df['onset'].max():.1f}s")
    print()
```

---

### 1.2 Trial-wise Beta 추출 방법 선택

#### 옵션 A: Least Squares All (LSA)
**장점**:
- 구현 간단 (모든 trial을 별도 regressor로)
- SPM/nilearn 기본 지원

**단점**:
- Trial 간 HRF 겹침으로 beta 상관관계 높음
- 순차 효과 (serial correlation) 문제

**적합성**: Trial spacing이 충분하면 (>12s) 괜찮음

#### 옵션 B: Least Squares Separate (LS-S) ⭐ **권장**
**장점**:
- 각 trial을 한 번에 하나씩 추정
- Beta 간 독립성 향상
- 더 정확한 pattern 추정

**단점**:
- 계산량 많음 (trial 수만큼 GLM 반복)
- 구현 복잡

**적합성**: Hyperalignment에 최적 (독립적 패턴 필요)

#### 옵션 C: FIR Deconvolution
**장점**:
- HRF shape 가정 불필요
- Time-resolved response 추출

**단점**:
- 계산량 매우 많음
- 추정 파라미터 수 증가 → SNR 저하

**적합성**: 추후 고려 (Phase 1에서는 과도)

---

### 1.3 LS-S 구현 전략 (개선된 버전)

**핵심 아이디어**:
각 trial t에 대해:
1. Trial t를 "target" regressor로
2. 나머지 trials를 **명시적으로 분리된** nuisance regressors로
3. Confounds (motion, physio) 추가
4. GLM 수행 → target beta만 저장

**⚠️ 중요**: 단순히 "다른 모든 trial"로 묶지 말고, 명시적으로 분리!

**Improved Design**:
```python
def extract_trial_wise_beta_lss(subject_id, roi_mask, confounds_strategy='motion'):
    """
    LS-S 방식으로 trial-wise beta 추출 (improved version)

    Parameters
    ----------
    subject_id : str
        피험자 ID (예: '02')
    roi_mask : niimg
        ROI mask (예: V1)
    confounds_strategy : str
        'motion': 6 motion params only
        'compcor': motion + aCompCor
        'full': motion + aCompCor + physio

    Returns
    -------
    trial_betas : ndarray (n_trials, n_voxels)
        각 trial의 voxel-wise beta 추정치
    trial_labels : list
        각 trial의 색 레이블
    reliability_scores : dict
        Split-half reliability (run-split)
    """
    from nilearn.glm.first_level import FirstLevelModel
    from nilearn.masking import apply_mask

    all_betas = []
    all_labels = []
    all_runs = []

    # Run별 처리
    for run_id in range(1, 7):
        # BOLD 데이터 로드
        bold_path = get_bold_path(subject_id, run_id)
        bold_img = nib.load(bold_path)

        # Events 로드
        events = load_events(subject_id, run_id)
        color_trials = events[events['trial_type'] != 'gray']

        # Confounds 로드
        confounds = load_confounds(subject_id, run_id, strategy=confounds_strategy)

        # 각 trial에 대해 LS-S
        for trial_idx, trial in color_trials.iterrows():
            # Design matrix 구성 (개선된 버전)
            design_events = make_lss_design_improved(events, trial_idx)

            # GLM fit (with confounds!)
            glm = FirstLevelModel(
                t_r=TR,
                high_pass=0.01,  # 100s high-pass filter
                drift_model='cosine',
                minimize_memory=False
            )
            glm.fit(bold_img, events=design_events, confounds=confounds)

            # Target trial의 beta만 추출
            beta_map = glm.compute_contrast('target')
            beta_values = apply_mask(beta_map, roi_mask)

            all_betas.append(beta_values)
            all_labels.append(trial['trial_type'])
            all_runs.append(run_id)

    trial_betas = np.array(all_betas)

    # ⚠️ CRITICAL: Split-half reliability 측정
    reliability = compute_split_half_reliability(
        trial_betas, all_labels, all_runs
    )

    return trial_betas, all_labels, reliability


def make_lss_design_improved(events, target_idx):
    """
    LS-S용 design matrix 생성 (명시적 nuisance 분리)

    ⚠️ 핵심 개선: Nuisance를 명시적으로 분리
    """
    design_events = events.copy()
    target_color = events.loc[target_idx, 'trial_type']

    # (1) Target trial
    design_events.loc[target_idx, 'trial_type'] = 'target'

    # (2) Nuisance: 같은 색 다른 trials
    same_color_mask = (design_events['trial_type'] == target_color) & \
                      (design_events.index != target_idx)
    design_events.loc[same_color_mask, 'trial_type'] = 'nuisance_same_color'

    # (3) Nuisance: 다른 색 trials (색별로 묶음)
    other_colors = design_events['trial_type'].unique()
    other_colors = [c for c in other_colors if c not in [target_color, 'target', 'nuisance_same_color', 'gray']]

    for color in other_colors:
        color_mask = design_events['trial_type'] == color
        design_events.loc[color_mask, 'trial_type'] = f'nuisance_{color}'

    # (4) Gray trials (별도 처리)
    gray_mask = design_events['trial_type'] == 'gray'
    if gray_mask.any():
        design_events.loc[gray_mask, 'trial_type'] = 'nuisance_gray'

    return design_events


def load_confounds(subject_id, run_id, strategy='motion'):
    """
    Confounds 로드 (motion, CompCor, physio)

    Parameters
    ----------
    strategy : str
        'motion': 6 motion params만
        'compcor': motion + 5 aCompCor components
        'full': motion + aCompCor + physio (if available)
    """
    confounds_file = get_confounds_path(subject_id, run_id)
    confounds_df = pd.read_csv(confounds_file, sep='\t')

    if strategy == 'motion':
        # 6 motion parameters
        motion_cols = ['trans_x', 'trans_y', 'trans_z',
                      'rot_x', 'rot_y', 'rot_z']
        confounds = confounds_df[motion_cols]

    elif strategy == 'compcor':
        # Motion + aCompCor (top 5)
        motion_cols = ['trans_x', 'trans_y', 'trans_z',
                      'rot_x', 'rot_y', 'rot_z']
        acomp_cols = [col for col in confounds_df.columns
                     if col.startswith('a_comp_cor_')][:5]
        confounds = confounds_df[motion_cols + acomp_cols]

    elif strategy == 'full':
        # Motion + aCompCor + physio (cardiac, respiratory)
        # Implementation depends on available confounds
        pass

    return confounds
```

---

### 1.4 ⚠️ CRITICAL: Split-Half Reliability Check

**Why This Matters**:
> LS-S가 noisy하면 GPA가 "좌표계 정렬"이 아니라 "노이즈 평균화"
> → Garbage in, garbage out!

**측정 방법**:
```python
def compute_split_half_reliability(trial_betas, trial_labels, trial_runs):
    """
    Run-split으로 trial-wise beta reliability 측정

    각 색별로:
    - Half 1: runs [1, 3, 5] trials
    - Half 2: runs [2, 4, 6] trials
    - 색별 평균 패턴의 correlation 계산

    Returns
    -------
    reliability : dict
        {color: correlation} for each color
        mean_reliability: 평균
    """
    trial_betas = np.array(trial_betas)
    trial_labels = np.array(trial_labels)
    trial_runs = np.array(trial_runs)

    unique_colors = np.unique(trial_labels)
    reliabilities = {}

    for color in unique_colors:
        color_mask = trial_labels == color

        # Split by runs (odd vs even)
        half1_mask = color_mask & np.isin(trial_runs, [1, 3, 5])
        half2_mask = color_mask & np.isin(trial_runs, [2, 4, 6])

        # 각 half의 평균 패턴
        pattern_half1 = trial_betas[half1_mask].mean(axis=0)
        pattern_half2 = trial_betas[half2_mask].mean(axis=0)

        # Correlation (또는 Procrustes stability)
        corr = np.corrcoef(pattern_half1, pattern_half2)[0, 1]
        reliabilities[color] = corr

    reliabilities['mean'] = np.mean(list(reliabilities.values()))

    return reliabilities


# 실행 예시
trial_betas, labels, reliability = extract_trial_wise_beta_lss('02', roi_mask)

print("\n=== Split-Half Reliability ===")
for color, r in reliability.items():
    if color != 'mean':
        print(f"  {color}: r = {r:.3f}")
print(f"\n  Mean: {reliability['mean']:.3f}")

# ⚠️ DECISION RULE
if reliability['mean'] < 0.3:
    print("\n❌ WARNING: Low reliability! GPA may fail.")
    print("   → Recommendation: Improve GLM (smoothing, AR1, confounds)")
    print("   → Or switch to color-averaged GPA")
elif reliability['mean'] < 0.4:
    print("\n⚠️ CAUTION: Moderate reliability. Monitor GPA quality closely.")
else:
    print("\n✅ Good reliability. Proceed to GPA.")
```

**Decision Rule**:
```
IF mean_reliability < 0.3:
    STOP Phase 1
    → Improve GLM:
      - Increase spatial smoothing (6mm → 8mm)
      - Try AR1 whitening
      - Add more confounds
      - Check preprocessing quality

ELIF mean_reliability < 0.4:
    PROCEED with caution
    → Monitor GPA quality metrics closely
    → Consider hybrid approach

ELSE:
    PROCEED to GPA
```

---

## 🔧 Step 2: Hyperalignment 구현 (Trial-aligned GPA)

### 2.1 GPA vs SRM: 어떤 방법을 선택할까?

**핵심 차이**:

| 특성 | GPA (Generalized Procrustes) | SRM (Shared Response Model) |
|------|------------------------------|----------------------------|
| 변환 | 직교 변환 R_s | 비직교 로딩 W_s |
| Magnitude | **보존** ✅ | 변경 가능 ⚠️ |
| 해석 | 좌표계 회전 | 차원 압축 + 회전 |
| Downstream | CVD magnitude 분석 가능 | Magnitude 정보 손실 |

**우리 프로젝트에서의 선택**: **GPA** ✅

**이유**:
- Phase 3에서 CVD의 magnitude 변화 (voxel 활성 강도)를 분석해야 함
- SRM의 비직교 변환은 magnitude를 임의로 변경 가능 → CVD 효과 왜곡
- GPA는 직교 변환 R_s로 magnitude 보존 → CVD 왜곡 그대로 유지

---

### 2.2 라이브러리 선택

#### 옵션 A: BrainIAK SRM (선택적 사용)
**장점**:
- 검증된 구현체, 최적화됨
- 빠른 프로토타이핑 가능

**단점**:
- SRM = 비직교 변환 (magnitude 변경 가능)
- 우리 요구사항(GPA)과 불일치

**사용 조건**:
- Orthogonal 옵션 확인 필요
- 또는 비교 목적으로만 사용

```bash
conda activate nilearn
pip install brainiak
```

#### 옵션 B: Custom GPA Implementation ⭐ **권장**
**장점**:
- **직교 변환 R_s 보장** (scipy.linalg.orthogonal_procrustes 사용)
- Magnitude 보존 명시적
- Procrustes 결과와 직접 비교 가능
- 우리 데이터 특성에 최적화

**구현**:
```python
def generalized_procrustes(data_list, n_iter=20, use_regularization=True, alpha=0.1):
    """
    Trial-aligned Generalized Procrustes Analysis (HC-only)

    ⚠️ NO PCA: Full voxel space GPA to preserve geographic features

    직교 변환 R_s를 사용하여 magnitude 보존 (CVD magnitude 분석 위해 필수)

    Parameters
    ----------
    data_list : list of ndarray
        각 HC subject의 (n_trials, n_voxels) trial-wise beta 데이터
        ⚠️ HC만 포함! CVD는 학습에서 배제
        ⚠️ NO PCA preprocessing! Full voxel space
    n_iter : int
        GPA 반복 횟수 (default: 20)
    use_regularization : bool
        Ridge regularization 사용 여부 (SNR 향상)
    alpha : float
        Regularization strength (if use_regularization=True)

    Returns
    -------
    X_common : ndarray (n_trials, n_voxels)
        공통 표현 공간 (HC 평균) - FULL VOXEL SPACE
    R_list : list of ndarray (n_voxels, n_voxels)
        각 HC의 직교 변환 행렬
    """
    from scipy.linalg import orthogonal_procrustes
    import numpy as np

    n_subjects = len(data_list)
    n_trials, n_voxels = data_list[0].shape

    print(f"✅ GPA 시작:")
    print(f"  Subjects: {n_subjects}")
    print(f"  Trials: {n_trials}")
    print(f"  Voxels: {n_voxels} (FULL SPACE, NO PCA)")
    print(f"  Regularization: {alpha if use_regularization else 'None'}")

    # ⚠️ Optional: Voxel-wise normalization (subject-specific scaling 제거)
    # Geographic features는 보존하되, scale 차이만 제거
    data_normalized = []
    for data in data_list:
        # Z-score per voxel (across trials)
        # 이것도 magnitude를 변경하므로 선택적
        # 권장: 정렬 후 magnitude 분석은 원본 데이터로
        data_norm = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-10)
        data_normalized.append(data_norm)

    # Step 1: 초기 reference (첫 번째 HC)
    X_common = data_normalized[0].copy()

    # Step 2: 반복 정렬 (iterative GPA)
    R_list = [None] * n_subjects

    for iter_idx in range(n_iter):
        aligned_data = []

        # 각 HC를 현재 reference에 정렬
        for s_idx, X_s in enumerate(data_normalized):
            if use_regularization:
                # Regularized Procrustes (stability 향상)
                # R_s = argmin ||X_s @ R - X_common||² + alpha ||R - I||²
                R_s = regularized_procrustes(X_s, X_common, alpha)
            else:
                # Standard orthogonal Procrustes
                R_s, _ = orthogonal_procrustes(X_s, X_common)

            X_s_aligned = X_s @ R_s  # (n_trials, n_voxels)

            aligned_data.append(X_s_aligned)
            R_list[s_idx] = R_s

        # Reference 업데이트 (HC 평균)
        X_common_new = np.mean(aligned_data, axis=0)

        # 수렴 확인
        if iter_idx > 0:
            change = np.linalg.norm(X_common_new - X_common)
            if change < 1e-6:
                print(f"✅ GPA 수렴: iteration {iter_idx+1}, change={change:.2e}")
                break

        X_common = X_common_new

    if iter_idx == n_iter - 1:
        print(f"⚠️ GPA 최대 iteration 도달 (수렴 안 됨)")

    return X_common, R_list


def regularized_procrustes(X, Y, alpha=0.1):
    """
    Regularized orthogonal Procrustes

    R = argmin ||X @ R - Y||² + alpha ||R - I||²

    더 안정적인 정렬 (특히 high-dimensional space)
    """
    from scipy.linalg import orthogonal_procrustes

    # Standard Procrustes
    R_standard, _ = orthogonal_procrustes(X, Y)

    # Regularization: R을 identity에 가깝게
    # 간단한 구현: weighted average
    I = np.eye(R_standard.shape[0])
    R_regularized = (R_standard + alpha * I) / (1 + alpha)

    # Re-orthogonalize (SVD)
    U, _, Vt = np.linalg.svd(R_regularized)
    R_ortho = U @ Vt

    return R_ortho
```

---

### 2.2.1 ⚠️ Why NO PCA?

**Geographic Features Preservation**:
- PCA mixes voxels → 공간적 패턴 손실
- 예: V1의 retinotopic organization이 PCA에서 섞임
- CVD magnitude 분석 시 원래 voxel 위치가 중요

**Magnitude Preservation**:
- PCA + scaling은 magnitude를 왜곡
- Full voxel space GPA = 직교 변환만 → magnitude 명확히 보존

**Trade-off**:
- ❌ PCA 없으면: 계산량 증가, noise 영향 증가
- ✅ PCA 없으면: Geographic features 보존, magnitude 명확

**해결책**:
1. **Regularization**: Ridge-regularized Procrustes (noise 억제)
2. **Spatial smoothing**: ROI 내에서 사전 smoothing (6-8mm)
3. **Voxel selection**: Low-SNR voxels 제거 (optional)

---

### 2.3 HC-only Learning: Why Exclude CVD?

**핵심 원리**:
```
HC common space = HC 뇌 반응의 "정상" 통계
CVD projection = CVD를 이 공간에 투사만 (학습 배제)
```

**CVD 배제 이유**:

1. **Common space 오염 방지**
   - GPA는 모든 subject를 평균하여 reference 생성
   - CVD가 포함되면 왜곡된 패턴이 평균에 섞임
   - 결과: HC도 CVD도 아닌 애매한 공간

2. **CVD 왜곡 보존**
   - CVD는 색 구조가 왜곡됨 (예: protan은 red-green 혼동)
   - 학습에 포함 시 GPA가 이 왜곡을 "보정"하려 함
   - 우리 목표: CVD 왜곡을 **그대로 관찰**해야 함

3. **Filter 학습 시 명확한 target**
   - Phase 3: CVD → HC-like 변환 학습
   - HC common space가 순수하면 명확한 목표 제공

**수학적 표현**:
```
GPA 학습: HC만
  X_common = mean(X_hc1 @ R_1, X_hc2 @ R_2, ..., X_hc5 @ R_5)

CVD 투사: 학습된 공간에 투사만
  X_cvd_projected = X_cvd @ R_cvd
  (R_cvd는 X_cvd를 X_common에 정렬하는 변환)
```

---

### 2.4 GPA 실행 (HC-only)

**데이터 준비**:
```python
# ⚠️ HC만 사용: sub-02, 03, 05, 06, 07 (CVD 배제!)
hc_subjects = ['02', '03', '05', '06', '07']
roi_name = 'V1'

# ROI mask 로드
roi_mask = load_roi_mask('V1')

# 각 HC의 trial-wise beta 추출 (LS-S)
hc_data = []
trial_labels = []

for subj_id in hc_subjects:
    trial_betas, labels = extract_trial_wise_beta_lss(subj_id, roi_mask)
    hc_data.append(trial_betas)
    trial_labels.append(labels)

    print(f"✅ Subject {subj_id}: {trial_betas.shape}")

# 예상 출력:
# ✅ Subject 02: (384, 429)  # 384 trials, 429 voxels (V1)
# ✅ Subject 03: (384, 429)
# ...
```

**GPA 실행 (Full Voxel Space - NO PCA)**:
```python
# Hyperalignment using trial-aligned GPA (전체 voxel space 사용)
# ⚠️ NO PCA: Geographic features 보존 위해 전체 voxel 사용

X_common, R_list = generalized_procrustes(
    data_list=hc_data,
    n_iter=20,
    use_regularization=True,  # Ridge-regularized Procrustes for stability
    alpha=0.1                  # Regularization strength
)

print(f"\n✅ GPA 완료:")
print(f"  Common space shape: {X_common.shape}")  # (384, 429) - FULL VOXELS
print(f"  Transformations: {len(R_list)} subjects")
print(f"  R_s shape: {R_list[0].shape}")  # (429, 429) - 직교 행렬

# 결과 저장
results = {
    'X_common': X_common,            # (384, 429) - Full voxel space
    'R_list': R_list,                # List of (429, 429) orthogonal matrices
    'subjects': hc_subjects,
    'roi': roi_name,
    'trial_labels': trial_labels,
    'n_voxels': X_common.shape[1],   # 429 voxels for V1
}

np.savez(f'results/alignment_quality/gpa_{roi_name}_fullvox.npz',
         **results)
```

---

## 📈 Step 3: 정렬 품질 평가 (2-Tier Strategy)

### 3.1 평가 전략 개요

**2-Tier 접근**:

**Tier-1: Trial-level Metrics** (직접 평가)
- Trial-wise 패턴의 정렬 품질 직접 측정
- 지표: Inter-subject correlation, LOSO decoding

**Tier-2: Color-level Metrics** (간접 평가)
- Trial → 색별 평균 후 기존 지표와 비교
- 지표: Procrustes disparity, Run-split stability, RDM similarity

---

### 3.2 Tier-1: Trial-level Metrics

#### (1) Inter-subject Correlation (Trial-wise)
각 trial에서 HC 간 패턴 유사도:

```python
def trial_inter_subject_correlation(hc_data_aligned, trial_labels):
    """
    Trial-level inter-subject correlation

    각 색의 trial들에서 HC 간 평균 correlation 계산
    """
    from scipy.stats import pearsonr

    unique_colors = np.unique(trial_labels[0])
    correlations = []

    for color in unique_colors:
        # 각 색의 trial indices
        color_indices = [np.where(np.array(labels) == color)[0]
                        for labels in trial_labels]

        # 각 trial에서 subject 간 correlation
        n_trials_per_color = len(color_indices[0])

        for trial_idx in range(n_trials_per_color):
            # 이 trial의 모든 HC 패턴
            trial_patterns = []
            for s_idx in range(len(hc_data_aligned)):
                pattern = hc_data_aligned[s_idx][color_indices[s_idx][trial_idx]]
                trial_patterns.append(pattern)

            # Pairwise correlation
            for i in range(len(trial_patterns)):
                for j in range(i+1, len(trial_patterns)):
                    corr, _ = pearsonr(trial_patterns[i], trial_patterns[j])
                    correlations.append(corr)

    return np.mean(correlations)

# Before vs After
hc_data_original = hc_data  # Original (각 subject 독립)
hc_data_aligned = [hc_data[i] @ R_list[i] for i in range(len(hc_subjects))]

corr_before = trial_inter_subject_correlation(hc_data_original, trial_labels)
corr_after = trial_inter_subject_correlation(hc_data_aligned, trial_labels)

print(f"Trial-level inter-subject correlation:")
print(f"  Before GPA: {corr_before:.3f}")
print(f"  After GPA:  {corr_after:.3f}")
print(f"  ✅ Target: > 0.30")
```

#### (2) LOSO (Leave-One-Subject-Out) Decoding
공통 공간에서 색 분류:

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import accuracy_score

def loso_decoding_trial_level(hc_data_aligned, trial_labels):
    """
    LOSO CV: 한 subject를 test로, 나머지로 학습
    """
    accuracies = []

    for test_idx in range(len(hc_subjects)):
        # Train: 나머지 HC들
        train_data = []
        train_labels = []
        for s_idx in range(len(hc_subjects)):
            if s_idx != test_idx:
                train_data.append(hc_data_aligned[s_idx])
                train_labels.extend(trial_labels[s_idx])

        train_data = np.vstack(train_data)
        train_labels = np.array(train_labels)

        # Test: 한 명
        test_data = hc_data_aligned[test_idx]
        test_labels = np.array(trial_labels[test_idx])

        # LDA 분류
        clf = LinearDiscriminantAnalysis()
        clf.fit(train_data, train_labels)
        predictions = clf.predict(test_data)

        acc = accuracy_score(test_labels, predictions)
        accuracies.append(acc)

        print(f"  Subject {hc_subjects[test_idx]}: {acc:.1%}")

    return np.array(accuracies)

# 평가
loso_acc = loso_decoding_trial_level(hc_data_aligned, trial_labels)

print(f"\nLOSO Decoding Accuracy:")
print(f"  Mean: {loso_acc.mean():.1%} (chance: 12.5%)")
print(f"  ✅ Target: > 25%")
```

---

### 3.3 Tier-2: Color-level Metrics

#### (1) Procrustes Disparity
기존 Procrustes 정렬과 비교:
```python
from scipy.spatial import procrustes

# 색별 평균 패턴으로 변환
def trials_to_color_patterns(trial_betas, trial_labels):
    """Trial-wise → 8 colors 평균"""
    unique_colors = np.unique(trial_labels)
    color_patterns = []
    for color in unique_colors:
        mask = np.array(trial_labels) == color
        color_patterns.append(trial_betas[mask].mean(axis=0))
    return np.array(color_patterns)

# HC 각 쌍에 대해 disparity 계산
disparities_before = []
disparities_after = []

for i in range(len(hc_subjects)):
    for j in range(i+1, len(hc_subjects)):
        # Before hyperalignment
        pat_i = color_patterns_original[i]
        pat_j = color_patterns_original[j]
        _, _, disp_before = procrustes(pat_i, pat_j)

        # After hyperalignment (공통 공간에서)
        pat_i_aligned = hc_data[i] @ transformations[i]
        pat_j_aligned = hc_data[j] @ transformations[j]
        pat_i_aligned = trials_to_color_patterns(pat_i_aligned, labels[i])
        pat_j_aligned = trials_to_color_patterns(pat_j_aligned, labels[j])
        _, _, disp_after = procrustes(pat_i_aligned, pat_j_aligned)

        disparities_before.append(disp_before)
        disparities_after.append(disp_after)

print(f"Procrustes disparity:")
print(f"  Before hyperalignment: {np.mean(disparities_before):.4f}")
print(f"  After hyperalignment:  {np.mean(disparities_after):.4f}")
print(f"  Improvement: {np.mean(disparities_before) - np.mean(disparities_after):.4f}")
```

#### (2) Split-Half Stability
개인 내 일관성 (hyperalignment 전/후):
```python
def split_half_stability(trial_betas, trial_labels, n_splits=10):
    """Split-half Procrustes stability"""
    stabilities = []

    for _ in range(n_splits):
        # Random split
        n_trials = len(trial_betas)
        indices = np.random.permutation(n_trials)
        half1_idx = indices[:n_trials//2]
        half2_idx = indices[n_trials//2:]

        # 각 half의 색별 평균
        half1_patterns = trials_to_color_patterns(
            trial_betas[half1_idx],
            np.array(trial_labels)[half1_idx]
        )
        half2_patterns = trials_to_color_patterns(
            trial_betas[half2_idx],
            np.array(trial_labels)[half2_idx]
        )

        # Procrustes
        _, _, disparity = procrustes(half1_patterns, half2_patterns)
        stabilities.append(1 - disparity)

    return np.mean(stabilities)

# 각 HC에 대해
for s_idx, subj_id in enumerate(hc_subjects):
    # Before
    stab_before = split_half_stability(
        hc_data[s_idx],
        trial_labels[s_idx]
    )

    # After (공통 공간)
    data_aligned = hc_data[s_idx] @ transformations[s_idx]
    stab_after = split_half_stability(
        data_aligned,
        trial_labels[s_idx]
    )

    print(f"Subject {subj_id}:")
    print(f"  Before: {stab_before:.3f}")
    print(f"  After:  {stab_after:.3f}")
```

#### (3) RDM Similarity (Between-subject)
```python
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform

def compute_rdm(patterns):
    """8 colors → 8×8 RDM"""
    distances = pdist(patterns, metric='correlation')
    return squareform(distances)

# HC 간 RDM 유사도
rdm_corrs_before = []
rdm_corrs_after = []

for i in range(len(hc_subjects)):
    for j in range(i+1, len(hc_subjects)):
        # Before
        rdm_i = compute_rdm(color_patterns_original[i])
        rdm_j = compute_rdm(color_patterns_original[j])
        corr_before = spearmanr(rdm_i[np.triu_indices(8, k=1)],
                               rdm_j[np.triu_indices(8, k=1)]).correlation

        # After
        rdm_i_aligned = compute_rdm(color_patterns_aligned[i])
        rdm_j_aligned = compute_rdm(color_patterns_aligned[j])
        corr_after = spearmanr(rdm_i_aligned[np.triu_indices(8, k=1)],
                              rdm_j_aligned[np.triu_indices(8, k=1)]).correlation

        rdm_corrs_before.append(corr_before)
        rdm_corrs_after.append(corr_after)

print(f"RDM similarity (between-subject):")
print(f"  Before: {np.mean(rdm_corrs_before):.3f} ± {np.std(rdm_corrs_before):.3f}")
print(f"  After:  {np.mean(rdm_corrs_after):.3f} ± {np.std(rdm_corrs_after):.3f}")
```

---

### 3.2 시각화

#### Figure 1: Alignment Quality Overview
```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# (A) Procrustes disparity comparison
ax = axes[0, 0]
ax.bar(['Before', 'After'],
       [np.mean(disparities_before), np.mean(disparities_after)])
ax.set_ylabel('Procrustes Disparity')
ax.set_title('(A) Between-Subject Alignment')

# (B) Split-half stability by subject
ax = axes[0, 1]
x = np.arange(len(hc_subjects))
width = 0.35
ax.bar(x - width/2, stabilities_before, width, label='Before')
ax.bar(x + width/2, stabilities_after, width, label='After')
ax.set_xticks(x)
ax.set_xticklabels(hc_subjects)
ax.set_ylabel('Stability')
ax.set_title('(B) Within-Subject Stability')
ax.legend()

# (C) RDM similarity
ax = axes[0, 2]
ax.bar(['Before', 'After'],
       [np.mean(rdm_corrs_before), np.mean(rdm_corrs_after)])
ax.set_ylabel('RDM Correlation')
ax.set_title('(C) Representational Similarity')

# (D-F) 개별 HC의 색 공간 시각화 (PCA 2D)
from sklearn.decomposition import PCA
for subj_idx in range(3):
    ax = axes[1, subj_idx]

    # Before (original)
    pca = PCA(n_components=2)
    colors_2d = pca.fit_transform(color_patterns_original[subj_idx])
    ax.scatter(colors_2d[:, 0], colors_2d[:, 1],
               c=range(8), cmap='hsv', s=100, alpha=0.5, label='Before')

    # After (aligned)
    colors_2d_aligned = pca.fit_transform(color_patterns_aligned[subj_idx])
    ax.scatter(colors_2d_aligned[:, 0], colors_2d_aligned[:, 1],
               c=range(8), cmap='hsv', s=100, marker='^', label='After')

    ax.set_title(f'(D-F) Subject {hc_subjects[subj_idx]}')
    ax.legend()

plt.tight_layout()
plt.savefig('results/alignment_quality/hyperalignment_quality_V1.png', dpi=300)
```

---

## 🎓 Step 4: Common W 재학습 및 성능 비교

### 4.1 기존 Common W (Procrustes 정렬)
기존 결과와 비교를 위해 baseline 확보:
```python
# 기존 방식 (색별 평균 + Procrustes)
# 이미 수행됨: derivatives/BH2009_deoblique_v2/baseline81_deob_determin/
baseline_path = Path('derivatives/BH2009_deoblique_v2/baseline81_deob_determin')

baseline_results = {}
for roi in ['V1', 'V2', 'V3', 'hV4']:
    # LORO-CV reconstruction errors
    errors = []
    for subj_id in hc_subjects:
        result_file = baseline_path / f'sm*_sub-{subj_id}_{roi}_*/classification_results.txt'
        # Parse reconstruction error
        # ...
    baseline_results[roi] = np.mean(errors)
```

### 4.2 Hyperalignment 기반 Common W
```python
def train_common_w_hyperaligned(hc_data_aligned, trial_labels, n_channels=6):
    """
    공통 공간에서 공용 W 학습

    Parameters
    ----------
    hc_data_aligned : list of ndarray
        각 HC의 정렬된 데이터 (n_trials, n_features)
    trial_labels : list of arrays
        각 trial의 색 레이블
    n_channels : int
        채널 수 (기본 6)

    Returns
    -------
    W_common : ndarray (n_channels, n_features)
    """
    # 모든 HC 데이터 결합
    all_trials = np.vstack(hc_data_aligned)
    all_labels = np.concatenate(trial_labels)

    # 색별 평균
    unique_colors = np.unique(all_labels)
    color_patterns = []
    for color in unique_colors:
        mask = all_labels == color
        color_patterns.append(all_trials[mask].mean(axis=0))
    color_patterns = np.array(color_patterns)  # (8, n_features)

    # Channel response 계산
    color_angles = get_color_angles(unique_colors)  # 0-360°
    channel_responses = compute_channel_responses(color_angles, n_channels)
    # (8, n_channels)

    # W = (C^T C)^{-1} C^T Y
    # Y: (8, n_features), C: (8, n_channels)
    W_common = np.linalg.lstsq(channel_responses, color_patterns, rcond=None)[0]
    # (n_channels, n_features)

    return W_common

# 학습
W_common_hyper = train_common_w_hyperaligned(
    [hc_data[i] @ transformations[i] for i in range(len(hc_subjects))],
    trial_labels
)

# 저장
np.save(f'results/alignment_quality/W_common_hyperaligned_{roi_name}.npy',
        W_common_hyper)
```

### 4.3 LORO-CV 성능 비교
```python
def loro_cv_hyperalignment(hc_data, transformations, trial_labels, W_common):
    """
    Leave-One-Run-Out CV for hyperaligned data
    """
    reconstruction_errors = []

    for subj_idx in range(len(hc_subjects)):
        # 이 subject를 test로
        test_data = hc_data[subj_idx] @ transformations[subj_idx]
        test_labels = trial_labels[subj_idx]

        # 색별 평균
        test_patterns = trials_to_color_patterns(test_data, test_labels)

        # Decode using W_common
        # C_hat = Y W^T (W W^T)^{-1}
        channel_hat = test_patterns @ W_common.T @ \
                      np.linalg.inv(W_common @ W_common.T)

        # Reconstruct color angles
        predicted_angles = decode_angles_from_channels(channel_hat)
        true_angles = get_color_angles(np.unique(test_labels))

        # Angular error
        errors = np.abs(predicted_angles - true_angles)
        errors = np.minimum(errors, 360 - errors)  # Circular

        reconstruction_errors.append(errors.mean())

    return np.array(reconstruction_errors)

# 평가
errors_hyper = loro_cv_hyperalignment(hc_data, transformations,
                                      trial_labels, W_common_hyper)

print(f"\nReconstruction Error ({roi_name}):")
print(f"  Baseline (Procrustes): {baseline_results[roi_name]:.1f}°")
print(f"  Hyperalignment:        {errors_hyper.mean():.1f}°")
print(f"  Improvement:           {baseline_results[roi_name] - errors_hyper.mean():.1f}°")
```

---

## 📋 Deliverables (Phase 1 산출물)

### 코드
- [ ] `scripts/01_trial_wise_glm.py`: LS-S GLM 구현
- [ ] `scripts/02_trial_aligned_gpa.py`: HC-only GPA 구현
- [ ] `scripts/03_evaluate_alignment.py`: 정렬 품질 평가 (2-tier)

### 데이터
- [ ] Trial-wise beta maps (HC 5명 × ROIs)
  - Format: `(n_trials=384, n_voxels)` per subject per ROI
- [ ] GPA transformations (R_s)
  - 각 HC의 직교 변환 행렬 (n_voxels, n_voxels)
  - ⚠️ Full voxel space: e.g., V1 = (429, 429)
- [ ] X_common
  - 공통 표현 공간 (n_trials, n_voxels)
  - ⚠️ NO PCA: Full voxel space preserved
- [ ] Common W (GPA-aligned)
  - Channel encoder weights learned on aligned HC data
  - Shape: (n_voxels, 6) for 6-channel model

### 결과
- [ ] **Tier-1 Metrics**:
  - Inter-subject correlation (trial-level)
  - LOSO decoding accuracy
- [ ] **Tier-2 Metrics**:
  - Procrustes disparity (before/after)
  - Run-split stability
  - RDM between-subject correlation
- [ ] **Downstream Performance**:
  - Common W reconstruction error (LORO-CV)
  - Comparison: Procrustes vs GPA

### 문서
- [x] 본 문서 (PHASE1_HYPERALIGNMENT.md) - 용어 통일 완료
- [ ] Progress log 업데이트 (실험 결과 기록)
- [ ] Decision log (분기 조건 발동 여부)

---

## 🚧 Decision Points (분기 조건)

Phase 1 실행 중 다음 조건에 따라 전략 조정:

### Decision Point #1: Trial-wise Beta Reliability

**조건**: Split-half stability < 0.50 (trial-wise beta 신뢰도 낮음)

**분기**:
- ❌ **Trial-wise 포기** → Color-averaged GPA로 전환
  - 각 색의 run-averaged beta만 사용 (8 대응점)
  - GPA 대신 기존 Procrustes로 충분
  - Phase 2는 여전히 진행 가능

- ✅ **계속 시도** → SNR 개선 조치:
  - Spatial smoothing ↑ (6mm → 8mm)
  - AR1 regularization 강화
  - FIR deconvolution 고려

**판단 시점**: LS-S GLM 완료 후 즉시

---

### Decision Point #2: GPA Performance Check

**조건**: GPA 후 성능 지표 달성 실패

**Tier-1 실패** (Inter-subject corr < 0.20 OR LOSO < 20%):
- → **GPA 파라미터 재조정**:
  - Regularization strength ↑ (alpha: 0.1 → 0.3 → 0.5)
  - Spatial smoothing ↑ (6mm → 8mm)
  - Voxel selection (Low-SNR voxels 제거)
  - GPA iterations ↑ (20 → 50)

**Tier-2 실패** (Disparity 개선 없음 OR Stability 저하):
- → **Alignment + Downstream 분리**:
  - GPA는 좌표계 정렬만 사용
  - Encoder 학습 시 individual data도 병행
  - Common vs Individual 비교 강조

**판단 시점**: Step 3 평가 완료 후

---

### Decision Point #3: ROI별 성능 격차

**조건**: V1/V2는 성공, V3/hV4는 실패

**대응**:
- **Main analysis**: V1/V2만 (full pipeline)
- **Exploratory**: V3/hV4 (simplified or color-averaged)
- 논문: "V1/V2 showed robust results, V3/hV4 were exploratory"

**판단 시점**: 모든 ROI 결과 확인 후

---

## ⚠️ 예상 문제 및 해결책

### 문제 1: Trial-wise SNR 너무 낮음
**증상**: Beta estimates 매우 noisy, split-half stability < 0.5

**원인**:
- ISI 짧아서 HRF 겹침
- Run 내 drift 심함
- ROI 너무 작음 (voxel 수 부족)

**해결**:
1. **Spatial smoothing 증가** (6mm → 8mm)
2. **Temporal regularization** (AR1 model, high-pass filter)
3. **Run-level detrending** (polynomial drift removal)
4. **Decision Point #1 발동**: Color-averaged로 전환

---

### 문제 2: GPA 수렴 안 됨
**증상**: Reference 계속 변함, disparity 감소하지 않음

**원인**:
- Noise voxels 너무 많음 (Low-SNR voxels 포함)
- 초기 reference가 outlier
- Trial alignment 실패 (순서 불일치?)

**해결**:
1. **Voxel selection 강화**:
   - Low-SNR voxels 제거 (temporal SNR < threshold)
   - Feature selection 사전 적용
2. **초기 reference 변경**:
   - 첫 번째 subject 대신 median subject
   - 또는 모든 subject 평균으로 시작
3. **자극 순서 재확인** (`00_check_data_structure.py`)
4. **Regularization 강화**:
   ```python
   R_s = argmin ||X_s @ R_s - X_common||^2 + λ||R_s - I||^2
   # alpha: 0.1 → 0.3 → 0.5
   ```

---

### 문제 3: 정렬 후 오히려 성능 하락
**증상**: Common W 정확도 기존보다 낮음, LOSO < baseline

**원인**:
- Over-regularization: 정렬이 너무 강해서 개별성 손실
- Voxel selection 과도: 중요한 정보 voxels 제거됨
- Subject 간 variability가 실제로 중요한 정보였음

**해결**:
1. **Regularization 조정**:
   - alpha 값 감소 (0.5 → 0.1 → 0.01)
   - GPA iterations 감소 (50 → 20 → 10)
2. **Voxel selection 완화**:
   - SNR threshold 낮추기
   - 더 많은 voxels 포함
3. **Decision Point #2 발동**: Alignment + Downstream 분리
4. **Hybrid 접근**:
   - GPA로 좌표계만 맞춤
   - Individual W도 학습하여 Common W와 비교

---

**다음 단계**: Phase 2 (Continuous Hue Interpolation Model)로 진행

**업데이트**: 2025-12-28
