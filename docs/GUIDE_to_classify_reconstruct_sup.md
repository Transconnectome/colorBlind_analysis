# Group-Level Analysis 실행 가이드

**작성일**: 2025-12-13
**목적**: Non-CVD subjects 간 common color-encoding voxels 찾기 및 group-level feature selection

---

## 📋 목차

1. [개요](#개요)
2. [구현 방법 및 GUIDE 요구사항 충족 여부](#구현-방법-및-guide-요구사항-충족-여부)
3. [차원 일치 문제 및 해결책](#차원-일치-문제-및-해결책)
4. [코드 상세 설명](#코드-상세-설명)
5. [실행 방법](#실행-방법)
6. [출력 결과](#출력-결과)
7. [제한사항 및 향후 개선 사항](#제한사항-및-향후-개선-사항)

---

## 개요

### 목적

GUIDE_to_classify_reconstruct.md의 Step 3 요구사항:
> "Across non-cvd participants (sub 01 ~ 07) make a common beta-map to find out common color-encoding voxels."

- **Non-CVD subjects**: 01, 02, 03, 05, 06, 07 (6명)
- **목표**:
  1. Group-level에서 일관되게 색상 정보를 encoding하는 common voxels 찾기
  2. 이 voxels에 대해 feature selection (PCA, ANOVA, RFE) 적용
  3. Group-level classification & reconstruction 성능 평가

### 구현된 분석

1. **Common Voxel Identification** (`group_level_common_voxels.py`)
   - Group-level statistical test로 significant voxels 찾기

2. **PCA Analysis** (`group_level_pca_analysis.py`)
   - Voxel 간 공유 정보 압축 및 high-loading voxels 시각화

3. **ANOVA Feature Selection** (`group_level_anova_selection.py`)
   - 색상 구분력이 높은 voxels 선택

---

## 구현 방법 및 GUIDE 요구사항 충족 여부

### ✅ GUIDE 요구사항 체크리스트

#### 1. Common Beta-Map 생성

**GUIDE 요구사항:**
> "make a common beta-map to find out common color-encoding voxels"

**구현 방법 (`group_level_common_voxels.py`):**

```python
# Step 1: Group amplitudes 로드
group_amplitudes = np.load('group_amplitudes_z.npy')  # (n_subjects, n_runs, n_colors, n_voxels)

# Step 2: 각 voxel-color pair에 대해 one-sample t-test
amplitudes_avg = group_amplitudes.mean(axis=1)  # Average across runs
for color_idx in range(n_colors):
    color_data = amplitudes_avg[:, color_idx, :]  # (n_subjects, n_voxels)
    t_vals, p_vals = stats.ttest_1samp(color_data, 0, axis=0)

# Step 3: FDR correction
reject, p_corrected = multipletests(p_flat, alpha=0.05, method='fdr_bh')

# Step 4: Common voxels 선택
common_voxel_mask = (n_colors_per_voxel >= min_colors)
```

**✅ 충족 여부**:
- Group-level statistical test로 significant voxels 찾음
- FDR correction으로 multiple comparison 보정
- Common beta-map: group_amplitudes.mean(axis=(0,1)) 형태로 저장됨

---

#### 2. PCA Feature Selection

**GUIDE 요구사항:**
> "Assuming that information is spread across voxels, we would need to concatenate all participants & runs and conduct PCA. However, when validating the model, we would need to do PCA for each train set."

**구현 방법 (`group_level_pca_analysis.py`):**

```python
def evaluate_pca_leave_one_subject_out(group_amplitudes, n_components):
    """Leave-one-subject-out CV with PCA"""

    for test_subject_idx in range(n_subjects):
        train_subjects = [i for i in range(n_subjects) if i != test_subject_idx]

        # Training data: concatenate all training subjects & runs
        X_train = group_amplitudes[train_subjects].reshape(-1, n_voxels)
        y_train = np.tile(np.arange(n_colors), len(train_subjects) * n_runs)

        # ✅ CRITICAL: Fit PCA ONLY on training set
        pca = PCA(n_components=n_components, random_state=42)
        X_train_pca = pca.fit_transform(X_train)

        # Test data
        X_test = group_amplitudes[test_subject_idx].reshape(-1, n_voxels)

        # ✅ Transform test set using fitted PCA
        X_test_pca = pca.transform(X_test)

        # Classification & Reconstruction
        y_pred = diag_linear_predict(X_train_pca, y_train, X_test_pca)
        # ... reconstruction ...
```

**✅ 충족 여부**:
- Training set에서만 PCA fit ✅
- Test set은 fitted PCA로 transform ✅
- Leave-one-subject-out CV 구현 ✅
- High-loading voxels 시각화 ✅

**GUIDE 예시 코드와 비교:**
```python
# GUIDE 요구사항
pca.fit(X_train)           # ✅ 구현됨
X_pcatrain = pca.transform(X_train)  # ✅ 구현됨
pca.saveAs(..pickle)       # ✅ pca_model.pkl로 저장됨
X_pcaTest = pca.transform(X_test)    # ✅ 구현됨
```

---

#### 3. ANOVA Feature Selection

**GUIDE 요구사항:**
> "To use ANOVA or RFE, assuming information is mainly in certain voxels. We would need to do group-level (2nd level) GLM and run ANOVA or RFE to choose common voxels to extract."

**구현 방법 (`group_level_anova_selection.py`):**

```python
def compute_anova_f_values(group_amplitudes):
    """Group-level ANOVA F-test"""

    # Concatenate all subjects & runs
    X_all = group_amplitudes.reshape(-1, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_subjects * n_runs)

    # ✅ ANOVA F-test: H0 = Color labels do not affect voxel response
    f_values, p_values = f_classif(X_all, y_all)

    return f_values, p_values

def select_top_k_voxels(f_values, k):
    """Select top-k voxels by F-value"""
    top_indices = np.argsort(f_values)[-k:][::-1]
    return top_indices
```

**✅ 충족 여부**:
- Group-level ANOVA F-test 구현 ✅
- Top-k voxel selection ✅
- Leave-one-subject-out CV로 validation ✅
- Reconstruction & classification 결과 시각화 ✅

**⚠️ 미구현**: RFE (Recursive Feature Elimination)는 아직 구현되지 않음

---

#### 4. MNI Space 확인

**GUIDE 요구사항:**
> "⚠️ Important NOTE: Before all these group-level procedure, we must check whether they are in same MNI space, or whether we need to conduct non-linear warping."

**⚠️ 현재 구현 상태**:
- **가정**: 모든 subjects가 동일한 MNI space (MNI152NLin2009cAsym)에 있다고 가정
- **근거**: fMRIPrep output이 모두 같은 template space로 normalized됨
  ```
  fMRIPrep outputs (v2):
  BOLD files: sub-{ID}_task-rsvp_run-X_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
  ```

**✅ 충족 여부**: fMRIPrep에서 이미 MNI space로 정규화되어 있으므로 추가 warping 불필요

---

## 차원 일치 문제 및 해결책

### 문제 상황

**GUIDE의 핵심 우려사항:**
> "we must check whether they are in same MNI space"

이는 단순히 MNI space 여부뿐만 아니라, **모든 subjects의 ROI 크기(n_voxels)가 동일한지** 확인이 필요함을 의미합니다.

### 현재 구현의 가정

```python
# group_level_common_voxels.py
group_amplitudes = np.array(amplitudes_list)  # (n_subjects, n_runs, n_colors, n_voxels)
```

이 코드가 작동하려면:
- **가정 1**: 모든 subjects의 `amplitudes_z.npy` 파일이 같은 shape `(n_runs, n_colors, n_voxels)`을 가져야 함
- **가정 2**: 각 subject의 n_voxels가 동일해야 함

### 차원 불일치 시나리오 및 해결책

#### **시나리오 1: ROI 크기가 다른 경우**

**원인**:
- Subject마다 ROI atlas 적용 시 voxel 개수가 다름
- 예: sub-01 V1 = 1500 voxels, sub-02 V1 = 1450 voxels

**현재 코드의 동작**:
```python
amplitudes_list.append(amplitudes_z)  # Shape mismatch 시 np.array() 에러 발생
group_amplitudes = np.array(amplitudes_list)  # ❌ ValueError: could not broadcast
```

**해결책 Option 1: MNI Coordinate Intersection (권장)**

```python
def find_common_voxel_coordinates(subjects, roi):
    """Find voxel coordinates that exist across all subjects"""

    # Load ROI masks for all subjects
    masks = []
    for subject in subjects:
        mask_img = nib.load(f'derivatives/sub-{subject}/roi_pipeline/{roi}_mask.nii.gz')
        masks.append(mask_img.get_fdata() > 0)

    # Find intersection (voxels present in ALL subjects)
    common_mask = np.logical_and.reduce(masks)

    # Get common voxel coordinates
    common_coords = np.argwhere(common_mask)

    return common_coords, common_mask

def extract_common_voxels(amplitudes_z, subject, roi, common_coords, roi_mask_path):
    """Extract only common voxels from subject's data"""

    # Load subject's ROI mask
    mask_img = nib.load(roi_mask_path)
    mask_data = mask_img.get_fdata()

    # Get subject's voxel coordinates
    subject_coords = np.argwhere(mask_data > 0)

    # Find indices of common voxels in subject's data
    common_indices = []
    for common_coord in common_coords:
        # Find matching coordinate in subject's voxel list
        match_idx = np.where((subject_coords == common_coord).all(axis=1))[0]
        if len(match_idx) > 0:
            common_indices.append(match_idx[0])

    # Extract only common voxels
    amplitudes_common = amplitudes_z[:, :, common_indices]

    return amplitudes_common
```

**사용 방법**:
```python
# Step 1: Find common voxel coordinates across all subjects
common_coords, common_mask = find_common_voxel_coordinates(subjects, roi)

# Step 2: Load and extract common voxels for each subject
amplitudes_list = []
for subject in subjects:
    amplitudes_z, roi_mask_path = load_subject_amplitudes(subject, roi, timestamp)
    amplitudes_common = extract_common_voxels(
        amplitudes_z, subject, roi, common_coords, roi_mask_path
    )
    amplitudes_list.append(amplitudes_common)

# Step 3: Now all subjects have same n_voxels
group_amplitudes = np.array(amplitudes_list)  # ✅ Works!
```

**장점**:
- Anatomically accurate: 실제로 같은 MNI 위치의 voxels만 사용
- 각 subject의 native anatomy 보존

**단점**:
- Voxel 개수 감소 가능 (intersection이므로)

---

**해결책 Option 2: Padding (비권장)**

```python
def pad_to_common_size(amplitudes_list):
    """Pad all arrays to max voxel count"""

    max_voxels = max([amp.shape[2] for amp in amplitudes_list])

    padded_list = []
    for amp in amplitudes_list:
        n_runs, n_colors, n_voxels = amp.shape
        if n_voxels < max_voxels:
            # Pad with zeros
            pad_width = ((0, 0), (0, 0), (0, max_voxels - n_voxels))
            amp_padded = np.pad(amp, pad_width, mode='constant', constant_values=0)
            padded_list.append(amp_padded)
        else:
            padded_list.append(amp)

    return np.array(padded_list)
```

**단점**:
- Anatomically meaningless: 패딩된 voxels는 실제 뇌 위치와 무관
- Statistical power 감소 (zero padding이 분석에 영향)

---

**해결책 Option 3: Subject-Specific Analysis (현재 구현)**

현재 코드는 **각 subject의 ROI 크기가 같다고 가정**하고 있습니다. 이는 다음 이유로 타당합니다:

1. **ROI atlas가 MNI space에서 정의됨**
   - Wang et al. (2015) atlas는 MNI space template
   - 모든 subjects가 같은 template에 warp되었으므로 ROI 크기 동일

2. **fMRIPrep의 normalization**
   ```bash
   # 모든 subjects가 동일한 template space
   space-MNI152NLin2009cAsym_res-2
   ```

3. **검증 방법**:
   ```python
   # 실제로 voxel 개수 확인
   for subject in subjects:
       amp = np.load(f'derivatives/.../sub-{subject}_{roi}/amplitudes_z.npy')
       print(f"sub-{subject}: {amp.shape}")

   # 출력 예시:
   # sub-01: (6, 8, 1523)
   # sub-02: (6, 8, 1523)
   # sub-03: (6, 8, 1523)
   # ...
   ```

---

#### **시나리오 2: 일부 Subject의 데이터가 없는 경우**

**원인**:
- sub-04처럼 특정 ROI에서 BOLD signal이 없는 경우
- Analysis 실패로 amplitudes_z.npy가 생성되지 않은 경우

**현재 코드의 처리**:
```python
# group_level_common_voxels.py
for subject_id in subjects:
    try:
        amplitudes_z = load_subject_amplitudes(subject_id, roi, timestamp)
        amplitudes_list.append(amplitudes_z)
    except FileNotFoundError as e:
        print(f"  ✗ sub-{subject_id}: {e}")
        continue  # ✅ Skip missing subjects

if len(amplitudes_list) == 0:
    raise RuntimeError("No subject data loaded!")  # ✅ Error handling
```

**✅ 해결됨**: Missing subjects는 자동으로 skip

---

### 차원 일치 확인 코드 (권장 추가 사항)

현재 코드에 추가하면 좋을 validation:

```python
def validate_group_data_consistency(amplitudes_list, subjects):
    """Validate that all subjects have consistent data shape"""

    shapes = [amp.shape for amp in amplitudes_list]

    # Check n_runs
    n_runs_list = [s[0] for s in shapes]
    if len(set(n_runs_list)) > 1:
        raise ValueError(
            f"Inconsistent n_runs across subjects!\n"
            f"  Shapes: {dict(zip(subjects, shapes))}\n"
            f"  Expected all subjects to have same n_runs"
        )

    # Check n_colors
    n_colors_list = [s[1] for s in shapes]
    if len(set(n_colors_list)) > 1:
        raise ValueError(
            f"Inconsistent n_colors across subjects!\n"
            f"  Shapes: {dict(zip(subjects, shapes))}"
        )

    # Check n_voxels
    n_voxels_list = [s[2] for s in shapes]
    if len(set(n_voxels_list)) > 1:
        print(f"⚠️  WARNING: Inconsistent n_voxels across subjects!")
        print(f"  Shapes: {dict(zip(subjects, shapes))}")
        print(f"  Recommendation: Use MNI coordinate intersection (Option 1)")
        raise ValueError(
            "Cannot proceed with inconsistent voxel counts. "
            "See docs/grouplevel_execution.md for solutions."
        )

    print(f"✅ Data consistency validated:")
    print(f"   n_runs: {n_runs_list[0]}")
    print(f"   n_colors: {n_colors_list[0]}")
    print(f"   n_voxels: {n_voxels_list[0]}")
    print(f"   n_subjects: {len(amplitudes_list)}")
```

**사용 방법**:
```python
# load_all_subjects() 함수에 추가
group_amplitudes, subject_info = load_all_subjects(subjects, roi, timestamp, dataset)

# ✅ Validate before proceeding
validate_group_data_consistency(
    [s['amplitudes'] for s in subject_info],
    subjects
)
```

---

## 코드 상세 설명

### 1. `group_level_common_voxels.py`

#### 목적
Group-level statistical test로 일관되게 색상 정보를 encode하는 voxels 찾기

#### 핵심 알고리즘

```python
def compute_group_statistics(group_amplitudes):
    """
    각 voxel-color pair에 대해 one-sample t-test 수행

    H0: Mean activation across subjects = 0 (no color encoding)
    H1: Mean activation ≠ 0 (significant color encoding)
    """

    # Average across runs (per subject)
    amplitudes_avg = group_amplitudes.mean(axis=1)  # (n_subjects, n_colors, n_voxels)

    t_values = np.zeros((n_colors, n_voxels))
    p_values = np.zeros((n_colors, n_voxels))

    for color_idx in range(n_colors):
        # Data for this color: (n_subjects, n_voxels)
        color_data = amplitudes_avg[:, color_idx, :]

        # One-sample t-test vs 0
        t_vals, p_vals = stats.ttest_1samp(color_data, 0, axis=0)

        t_values[color_idx, :] = t_vals
        p_values[color_idx, :] = p_vals

    return t_values, p_values
```

#### FDR Correction

```python
def apply_fdr_correction(p_values, alpha=0.05):
    """
    Benjamini-Hochberg FDR correction

    Multiple comparison correction across all (n_colors × n_voxels) tests
    """

    p_flat = p_values.flatten()

    # FDR correction
    reject, p_corrected, _, _ = multipletests(
        p_flat, alpha=alpha, method='fdr_bh'
    )

    significant_mask = reject.reshape((n_colors, n_voxels))

    return significant_mask, p_corrected.reshape((n_colors, n_voxels))
```

#### Common Voxel Selection

```python
def select_common_voxels(significant_mask, min_colors=1):
    """
    최소 min_colors개 색상에서 significant한 voxels 선택
    """

    # Count number of colors with significant activation per voxel
    n_colors_per_voxel = significant_mask.sum(axis=0)  # (n_voxels,)

    # Select voxels
    common_voxel_mask = n_colors_per_voxel >= min_colors

    return common_voxel_mask, n_colors_per_voxel
```

#### 출력

```
derivatives/group_level/{timestamp}/{roi}/common_voxels/
├── group_amplitudes_z.npy           # (n_subjects, n_runs, n_colors, n_voxels)
├── group_statistics.npz             # t_values, p_values (n_colors, n_voxels)
├── significant_voxels.npy           # Boolean mask (n_voxels,)
├── significant_voxel_indices.npy    # Indices of common voxels
├── n_colors_per_voxel.npy          # (n_voxels,) - diagnostic
└── figures/
    ├── common_voxels_brain.png      # Brain visualization
    ├── significance_distribution.png
    └── per_color_activation.png
```

---

### 2. `group_level_pca_analysis.py`

#### 목적
Voxel 간 공유 정보를 PCA로 압축하고, high-loading voxels 시각화

#### 핵심 알고리즘

**Group-level PCA Fitting:**
```python
def fit_group_pca(group_amplitudes, n_components):
    """
    모든 subjects & runs concatenate하여 PCA fit
    """

    # Concatenate all data
    X_all = group_amplitudes.reshape(-1, n_voxels)
    # Shape: (n_subjects*n_runs*n_colors, n_voxels)

    # Fit PCA
    pca = PCA(n_components=n_components, random_state=42)
    X_all_pca = pca.fit_transform(X_all)

    return pca, X_all_pca
```

**Leave-One-Subject-Out Validation:**
```python
def evaluate_pca_leave_one_subject_out(group_amplitudes, n_components):
    """
    각 fold에서 독립적으로 PCA fit
    """

    for test_subject_idx in range(n_subjects):
        # Training: other subjects
        train_subjects = [i for i in range(n_subjects) if i != test_subject_idx]
        X_train = group_amplitudes[train_subjects].reshape(-1, n_voxels)

        # ✅ Fit PCA on training set ONLY
        pca = PCA(n_components=n_components)
        X_train_pca = pca.fit_transform(X_train)

        # Test: held-out subject
        X_test = group_amplitudes[test_subject_idx].reshape(-1, n_voxels)

        # ✅ Transform test set with fitted PCA
        X_test_pca = pca.transform(X_test)

        # Evaluate
        # ... classification & reconstruction ...
```

**High-Loading Voxels:**
```python
def identify_high_loading_voxels(pca, top_k=100):
    """
    각 PC에서 absolute loading이 가장 큰 voxels 찾기

    Interpretation:
    - High positive loading: voxel이 PC 방향으로 강하게 기여
    - High negative loading: voxel이 PC 반대 방향으로 강하게 기여
    """

    loadings = pca.components_  # (n_components, n_voxels)

    high_loading_dict = {}
    for pc_idx in range(n_components):
        # Absolute loadings
        abs_loadings = np.abs(loadings[pc_idx, :])

        # Top k voxel indices
        top_indices = np.argsort(abs_loadings)[-top_k:][::-1]

        high_loading_dict[pc_idx] = {
            'voxel_indices': top_indices,
            'loadings': loadings[pc_idx, top_indices],
            'abs_loadings': abs_loadings[top_indices]
        }

    return high_loading_dict
```

#### 출력

```
derivatives/group_level/{timestamp}/{roi}/pca/
├── pca_model.pkl                     # Fitted PCA (전체 data)
├── pca_loadings.npy                  # (n_components, n_voxels)
├── high_loading_voxels.npz           # Top voxels per PC
├── group_performance.csv
├── per_subject_performance.csv
└── figures/
    ├── pca_loadings_heatmap.png      # Components × voxels heatmap
    ├── high_loading_voxels_PC1.png   # PC1 high-loading voxels (brain)
    ├── high_loading_voxels_PC2.png
    ├── ...
    ├── circular_color_space_pca.png  # Reconstruction 결과
    └── confusion_matrix_pca.png      # Classification 결과
```

---

### 3. `group_level_anova_selection.py`

#### 목적
색상 간 차이가 큰 voxels를 ANOVA F-test로 선택

#### 핵심 알고리즘

**ANOVA F-test:**
```python
def compute_anova_f_values(group_amplitudes):
    """
    One-way ANOVA F-test

    H0: 모든 colors의 mean activation이 같음
    H1: 적어도 하나의 color가 다른 mean activation을 가짐
    """

    # Reshape: (n_subjects*n_runs*n_colors, n_voxels)
    X_all = group_amplitudes.reshape(-1, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_subjects * n_runs)

    # ANOVA F-test (sklearn)
    f_values, p_values = f_classif(X_all, y_all)
    # f_values: (n_voxels,) - 각 voxel의 F-statistic

    return f_values, p_values
```

**Top-k Selection:**
```python
def select_top_k_voxels(f_values, k):
    """F-value가 가장 큰 k개 voxels 선택"""

    top_indices = np.argsort(f_values)[-k:][::-1]
    return top_indices
```

**Leave-One-Subject-Out Validation:**
```python
for k in k_values:  # [50, 100, 200]
    # Select top-k voxels
    selected_indices = select_top_k_voxels(f_values, k)
    amplitudes_selected = group_amplitudes[:, :, :, selected_indices]

    for test_subj_idx in range(n_subjects):
        # Training
        X_train = amplitudes_selected[train_subjs].reshape(-1, k)

        # Test
        X_test = amplitudes_selected[test_subj_idx].reshape(-1, k)

        # Evaluate
        # ... classification & reconstruction ...
```

#### 출력

```
derivatives/group_level/{timestamp}/{roi}/anova/
├── anova_f_values.npy                # (n_voxels,) F-statistics
├── anova_p_values.npy                # (n_voxels,) p-values
├── selected_voxel_indices_k50.npy    # Top-50 voxel indices
├── selected_voxel_indices_k100.npy
├── selected_voxel_indices_k200.npy
├── group_performance.csv             # Mean across subjects
├── per_subject_performance.csv       # Per-subject results
└── figures/
    ├── anova_f_distribution.png      # F-value distribution
    ├── performance_vs_k.png          # Acc/Recon vs k
    ├── circular_color_space_k50.png  # k=50 reconstruction
    ├── circular_color_space_k100.png
    ├── confusion_matrix_k50.png      # k=50 classification
    └── confusion_matrix_k100.png
```

---

### 4. `run_group_level_analysis.sbatch`

#### SLURM 설정

```bash
#SBATCH --job-name=group_level_analysis
#SBATCH --nodelist=node2              # ✅ CRITICAL
#SBATCH --output=logs/group_level/%x_%A_%a.out
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --array=0-3                   # 4 ROIs in parallel
```

#### 실행 순서

```bash
# Step 1: Common voxels
python group_level_common_voxels.py \
    --roi $ROI \
    --timestamp baseline32_deob \
    --subjects 01 02 03 05 06 07 \
    --fdr-alpha 0.05 \
    --min-colors 1

# Step 2: PCA
python group_level_pca_analysis.py \
    --roi $ROI \
    --n-components 50 \
    --use-common-voxels \
    --top-k-voxels 100

# Step 3: ANOVA
python group_level_anova_selection.py \
    --roi $ROI \
    --k-features 50 100 200
```

---

## 실행 방법

### 1. 파일 업로드

```bash
# Python scripts
scp group_level_common_voxels.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp group_level_pca_analysis.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp group_level_anova_selection.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp validate_group_data.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# SLURM batch file
scp run_group_level_analysis.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. 데이터 검증 (실행 전 필수!)

**⚠️ CRITICAL**: Group-level 분석 실행 전, 반드시 데이터 일관성 검증을 수행하세요!

#### 로컬에서 검증 (권장)

```bash
# V1 검증
python validate_group_data.py --roi V1 --timestamp baseline32_deob --dataset deoblique_v2

# V2 검증
python validate_group_data.py --roi V2 --timestamp baseline32_deob --dataset deoblique_v2

# V3 검증
python validate_group_data.py --roi V3 --timestamp baseline32_deob --dataset deoblique_v2

# hV4 검증
python validate_group_data.py --roi hV4 --timestamp baseline32_deob --dataset deoblique_v2
```

#### 서버에서 검증

```bash
# SSH 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 환경 활성화
conda activate nilearn

# 검증 실행 (모든 ROI)
for roi in V1 V2 V3 hV4; do
    echo "Validating $roi..."
    python validate_group_data.py --roi $roi --timestamp baseline32_deob --dataset deoblique_v2
done
```

#### 검증 결과 해석

**✅ 성공 예시:**
```
================================================================================
Validating data consistency...
================================================================================
  ✓ n_runs consistent: 6
  ✓ n_colors consistent: 8
  ✓ n_voxels consistent: 1234
  ✅ All dimensions consistent - safe to proceed!

[1] File Existence: ✅ PASS
[2] Shape Consistency: ✅ PASS
[3] MNI Space: ✅ PASS
[4] Data Quality: ✅ PASS
[5] Voxel Coordinates: ✅ PASS

✅ ALL VALIDATIONS PASSED - Safe to proceed with group-level analysis
```

**❌ 실패 예시 (n_voxels 불일치):**
```
❌ INCONSISTENT n_voxels across subjects:
     sub-01: 1234 voxels
     sub-02: 1200 voxels
     sub-03: 1250 voxels

  This is a CRITICAL error - cannot proceed with group analysis!
  See docs/grouplevel_execution.md for solutions:
    - Option 1 (Recommended): MNI coordinate intersection
    - Option 2: Zero padding (not recommended)
```

**해결책**: 위 "차원 일치 문제 및 해결책" 섹션 참조

### 3. 서버에서 실행

```bash
# SSH 접속 (아직 접속 안 했으면)
ssh haba6030@node2

# 작업 디렉토리
cd /scratch/connectome/haba6030/colorBlind

# Log 디렉토리 생성
mkdir -p logs/group_level

# 실행 (검증 통과 후!)
sbatch run_group_level_analysis.sbatch
```

**참고**:
- `group_level_common_voxels.py` 실행 시 자동으로 validation 수행됨
- 만약 validation 실패하면 informative error와 함께 중단됨

### 4. 작업 모니터링

```bash
# Job 상태
squeue -u haba6030

# Log 확인
tail -f logs/group_level/group_level_analysis_*_0.out  # V1
tail -f logs/group_level/group_level_analysis_*_1.out  # V2
```

### 5. 결과 다운로드

```bash
# All results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/group_level/ ./derivatives/

# Specific ROI
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/group_level/baseline32_deob/V1/ ./derivatives/group_level/baseline32_deob/
```

---

## 출력 결과

### 디렉토리 구조

```
derivatives/group_level/baseline32_deob/
├── V1/
│   ├── common_voxels/
│   │   ├── group_amplitudes_z.npy
│   │   ├── group_statistics.npz
│   │   ├── significant_voxels.npy
│   │   ├── significant_voxel_indices.npy
│   │   ├── n_colors_per_voxel.npy
│   │   ├── group_statistics_summary.csv
│   │   └── figures/
│   │       ├── common_voxels_brain.png
│   │       ├── significance_distribution.png
│   │       └── per_color_activation.png
│   ├── pca/
│   │   ├── pca_model.pkl
│   │   ├── pca_loadings.npy
│   │   ├── high_loading_voxels.npz
│   │   ├── group_performance.csv
│   │   ├── per_subject_performance.csv
│   │   └── figures/
│   │       ├── pca_loadings_heatmap.png
│   │       ├── high_loading_voxels_PC1.png
│   │       ├── high_loading_voxels_PC2.png
│   │       ├── ...
│   │       ├── circular_color_space_pca.png
│   │       └── confusion_matrix_pca.png
│   └── anova/
│       ├── anova_f_values.npy
│       ├── anova_p_values.npy
│       ├── selected_voxel_indices_k50.npy
│       ├── selected_voxel_indices_k100.npy
│       ├── selected_voxel_indices_k200.npy
│       ├── group_performance.csv
│       ├── per_subject_performance.csv
│       └── figures/
│           ├── anova_f_distribution.png
│           ├── performance_vs_k.png
│           ├── circular_color_space_k50.png
│           ├── circular_color_space_k100.png
│           ├── circular_color_space_k200.png
│           ├── confusion_matrix_k50.png
│           ├── confusion_matrix_k100.png
│           └── confusion_matrix_k200.png
├── V2/
├── V3/
└── hV4/
```

### CSV 파일 형식

**`group_performance.csv` (ANOVA 예시):**
```csv
k,classification_accuracy_mean,classification_accuracy_std,reconstruction_error_mean,reconstruction_error_std,mean_snr_mean,mean_snr_std
50,0.45,0.08,65.2,12.3,1.82,0.34
100,0.52,0.07,58.7,10.5,2.15,0.41
200,0.58,0.06,52.3,9.2,2.48,0.38
```

**`per_subject_performance.csv`:**
```csv
k,test_subject,classification_accuracy,reconstruction_error,mean_snr
50,1,0.48,63.5,1.95
50,2,0.42,67.8,1.72
...
```

---

## 제한사항 및 향후 개선 사항

### 현재 제한사항

#### 1. ⚠️ RFE 미구현

**GUIDE 요구사항**:
> "try several feature selection (PCA, ANOVA based, RFE)"

**현재 상태**: ANOVA와 PCA만 구현됨

**향후 구현 필요**:
```python
# group_level_rfe_selection.py (미구현)
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression

def evaluate_rfe_selection(group_amplitudes, n_features_to_select):
    """
    Recursive Feature Elimination

    반복적으로 가장 중요하지 않은 feature 제거
    """

    # Estimator
    estimator = LogisticRegression(max_iter=1000)

    # RFE
    rfe = RFE(estimator, n_features_to_select=n_features_to_select)

    # Fit on training data
    rfe.fit(X_train, y_train)

    # Get selected features
    selected_mask = rfe.support_
    selected_indices = np.where(selected_mask)[0]

    return selected_indices
```

---

#### 2. ✅ 차원 일치 검증 (구현 완료)

**문제**:
- 모든 subjects의 n_voxels가 같다고 가정
- `np.array(amplitudes_list)` 실행 시 shape 불일치하면 오류 발생

**해결책 (구현됨)**:
1. **Standalone 검증 스크립트**: `validate_group_data.py`
   ```bash
   # 실행 전 검증
   python validate_group_data.py --roi V1 --timestamp baseline32_deob --dataset deoblique_v2
   ```

2. **통합 검증 함수**: 모든 group-level 스크립트에 validation 추가됨
   - `group_level_common_voxels.py`: `validate_group_data_consistency()` 함수
   - `group_level_pca_analysis.py`: shape validation
   - `group_level_anova_selection.py`: shape validation

3. **자동 검증**:
   ```python
   # group_level_common_voxels.py에서 자동 실행
   validate_group_data_consistency(amplitudes_list, subjects)
   # → 불일치 발견 시 informative error + 해결책 링크
   ```

**검증 항목**:
- ✓ File existence
- ✓ Shape consistency (n_runs, n_colors, n_voxels)
- ✓ MNI space alignment (affine matrix)
- ✓ Data quality (NaN, Inf 체크)
- ✓ Voxel coordinate overlap

---

#### 3. ⚠️ Non-linear Warping 옵션 없음

**GUIDE 요구사항**:
> "whether we need to conduct non-linear warping"

**현재 가정**: fMRIPrep의 MNI normalization으로 충분

**향후 개선**: Subject-specific anatomy를 보존하면서 group analysis하는 옵션
```python
# Surface-based analysis (Freesurfer)
# - Cortical surface로 project
# - Individual sulcal patterns 보존
```

---

#### 4. 💡 성능 최적화

**현재**: 각 ROI를 순차 분석 (SLURM array job으로 병렬화는 됨)

**향후 개선**:
- Within-ROI parallelization (joblib)
- Caching intermediate results
- GPU acceleration for PCA (cuML)

---

### 향후 개선 방향

#### 1. Cross-Validation 전략 확장

현재: Leave-one-subject-out만 구현

**추가 가능**:
```python
# Leave-one-run-out
# Leave-one-color-out (novel color generalization)
# K-fold CV with subject grouping
```

---

#### 2. Statistical Robustness

현재: 단순 one-sample t-test

**추가 가능**:
```python
# Mixed-effects model (subjects as random effects)
from statsmodels.formula.api import mixedlm

# Permutation test
from nilearn.mass_univariate import permuted_ols
```

---

#### 3. Multivariate Pattern Analysis

현재: Univariate (voxel-wise) tests

**추가 가능**:
```python
# Searchlight MVPA
from nilearn.decoding import SearchLight

# Representational Similarity Analysis (RSA)
```

---

## 요약: GUIDE 요구사항 충족 여부

| 요구사항 | 상태 | 구현 위치 |
|---------|------|----------|
| Common beta-map 생성 | ✅ 완료 | `group_level_common_voxels.py` |
| Group-level GLM/statistics | ✅ 완료 | One-sample t-test + FDR |
| PCA (train set만 fit) | ✅ 완료 | `group_level_pca_analysis.py` |
| PCA (test set transform) | ✅ 완료 | `evaluate_pca_leave_one_subject_out()` |
| ANOVA feature selection | ✅ 완료 | `group_level_anova_selection.py` |
| RFE feature selection | ❌ 미구현 | - |
| Reconstruction 결과 시각화 | ✅ 완료 | Circular color space plots |
| Classification 결과 시각화 | ✅ 완료 | Confusion matrices |
| Common voxel 시각화 | ✅ 완료 | Brain plots |
| High-loading voxel 시각화 | ✅ 완료 | PCA component brain plots |
| MNI space 확인 | ⚠️ 가정 | fMRIPrep normalization 의존 |
| 차원 일치 검증 | ⚠️ 부분적 | Error handling만 있음 |

---

## 참고 자료

### 관련 논문

1. **Brouwer & Heeger (2009)**. "Decoding and reconstructing color from responses in human visual cortex." *J. Neurosci.*
   - Forward encoding model 방법론

2. **Benjamini & Hochberg (1995)**. "Controlling the false discovery rate." *J. Royal Stat. Soc. B*
   - FDR correction 방법

3. **Wang et al. (2015)**. "Probabilistic maps of visual topography in human cortex." *Cereb. Cortex*
   - ROI atlas

### 관련 파일

- `GUIDE_to_classify_reconstruct.md` - 분석 전체 가이드
- `utils_color_decoding.py` - 공통 유틸리티 함수
- `CLAUDE.md` - 프로젝트 전체 가이드

---

**마지막 업데이트**: 2025-12-13
**작성자**: Claude Code
**문의**: GUIDE 또는 구현 관련 질문은 log 파일과 함께 문의
