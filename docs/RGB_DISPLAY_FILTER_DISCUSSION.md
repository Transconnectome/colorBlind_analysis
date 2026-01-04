# RGB Display Filter 구현 방법 논의

**Date**: 2025-12-19
**Goal**: Phase 2A brain filter (A, b)를 사용하여 CVD를 위한 RGB display filter 구현

---

## 1. 목표 (Goal)

### 원하는 결과:
```
RGB_modified → CVD subject views → fMRI response ≈ HC pattern
```

즉, CVD에게 modified RGB를 보여주면 HC처럼 brain이 반응하도록 하는 **RGB display filter** 제작.

---

## 2. 우리가 가진 것 (What We Have)

### 2.1 Phase 2A Filter (Brain Space)
- **Filter**: `F = Y @ A + b`
  - Input: CVD brain pattern (Y) - (8, n_voxels)
  - Output: HC-like brain pattern (F) - (8, n_voxels)
  - A: (n_voxels, n_voxels) transformation matrix
  - b: (n_voxels,) bias vector
- **학습 완료**: `results/filters/models/optionD/20251219_122240/`

### 2.2 Data
- **8개 RGB 색상**: Original stimuli
  ```python
  RGB_COLORS = {
      'Red':        [1.0, 0.0, 0.0],
      'Orange':     [1.0, 0.5, 0.0],
      'Yellow':     [1.0, 1.0, 0.0],
      'Chartreuse': [0.5, 1.0, 0.0],
      'Green':      [0.0, 1.0, 0.0],
      'Cyan':       [0.0, 1.0, 1.0],
      'Blue':       [0.0, 0.0, 1.0],
      'Magenta':    [1.0, 0.0, 1.0]
  }
  ```

- **CVD brain patterns**: `amplitudes_z.npy` (baseline32_deob_determin)
  - Shape: (n_runs, 8, n_voxels)
  - Source: GLM beta values (z-scored)
  - Location: `derivatives/BH2009_deoblique_v2/baseline32_deob_determin/`

- **HC brain patterns**: HC mean pattern (4 subjects: 03, 05, 06, 07)
  - Shape: (8, n_voxels)
  - Location: `results/group_level/phase2a_data/patterns/HC_mean/`

### 2.3 Reconstruction W Matrix (Channel-Voxel Mapping)
- **Location**: `results/group_level/procrustes_reconstruction/{ROI}/W_common.npy`
- **Shape**: (n_voxels, 6) - voxels to 6 color channels
- **중요**: 이 W는 **Procrustes-aligned voxel space**에서 정의됨

---

## 3. 데이터 Space 확인 (CRITICAL)

### 질문: Phase 2A filter가 어떤 space에서 학습되었나?

#### Phase 2A 데이터 소스 확인:
```python
# scripts/phase2a_extract_patterns.py (lines 48-62)
amp_file = roi_dir / "amplitudes_z.npy"
amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_selected_voxels)
pattern = amplitudes.mean(axis=2)  # (8, n_selected) - run 평균
```

**결론**:
- Phase 2A는 **raw voxel space** (amplitudes_z) 사용
- **Procrustes alignment 적용 안 함**

#### Loss Function의 Geometric Nature:
```python
# Phase 2A loss (3 components)
L_total = λ_mag × L_magnitude + λ_base × L_baseline + λ_struct × L_structure_RDM
```

- **Magnitude**: Scale (L2 norm matching)
- **Baseline**: Translation (mean matching)
- **Structure (RDM)**: Rotation/shape (correlation-based, magnitude-free)

→ 이 3개 조합이 **Procrustes와 유사한 geometric transformation** 학습
→ **하지만 데이터 자체는 Procrustes align 안 됨!**

---

## 4. Space Mismatch 문제

### 현재 상황:
1. **Phase 2A Filter (A, b)**: Raw voxel space
2. **Reconstruction W matrix**: Procrustes-aligned voxel space

→ **두 개가 다른 coordinate space!**

### 사용 불가능:
```python
# ❌ WRONG: Space mismatch
CVD_voxel_raw --[Filter A,b]--> HC_voxel_raw
              --[W from Procrustes space]--> Channels ❌
```

---

## 5. 구현 방법 제안

### Option 1: Raw Voxel Space에서 완전 역연산 (Current Best)

**장점**: Phase 2A filter 직접 사용 가능

```python
# Step 1: CVD의 RGB → voxel encoder 학습 (raw space)
encoder = Ridge(alpha=1.0)
encoder.fit(RGB_8colors, CVD_voxel_raw)  # (8,3) → (8, n_voxels)

# Step 2: Target voxel 계산 (Filter 적용)
target_voxel = CVD_voxel_raw @ A + b  # (8, n_voxels) - HC-like brain

# Step 3: Pseudo-inverse로 RGB 찾기
W_enc = encoder.coef_  # (n_voxels, 3)
b_enc = encoder.intercept_  # (3,)
W_pinv = np.linalg.pinv(W_enc)  # (3, n_voxels)

RGB_modified = (target_voxel - b_enc[np.newaxis, :]) @ W_pinv.T  # (8, 3)
```

**결과**:
- `RGB_modified`를 CVD에게 보여주면 → `target_voxel` 생성 → HC-like brain!

**제약**:
- 8개 색상에 대해서만 계산 가능 (8 data points로 학습)
- Linear encoder assumption (실제 vision은 nonlinear일 수 있음)

---

### Option 2: Procrustes Space 사용 (Reconstruction W 활용)

**필요한 작업**:
1. Phase 2A를 **Procrustes-aligned space**에서 다시 학습
2. 또는 CVD/HC의 Procrustes transformation 찾아서 space 변환

```python
# Forward (reconstruction):
Channels → [W] → HC_aligned_voxels
         → [Procrustes_HC^-1] → HC_raw_voxels

# CVD goal:
RGB_modified → CVD → CVD_raw_voxels
             → [Filter A,b] → HC_raw_voxels (target)

# Reverse (need Procrustes transformations):
Channels → [W] → HC_aligned → [Procrustes_HC^-1] → HC_raw (target)
         → [A,b inverse] → CVD_raw needed
         → [Procrustes_CVD] → CVD_aligned
         → [W^-1] → Channels → RGB
```

**문제점**:
- CVD의 Procrustes transformation 필요 (어디서 구할까?)
- Phase 2A filter가 raw space에서 학습되어 호환 안 됨

---

### Option 3: Procrustes-Aligned Space에서 Phase 2A 재학습

**절차**:
1. CVD/HC patterns를 HC reference에 Procrustes align
2. Aligned space에서 Filter (A', b') 재학습
3. Reconstruction W matrix 사용하여 역연산

```python
# Step 1: Align all patterns to HC reference
CVD_aligned = procrustes_align(CVD_raw, HC_reference)
HC_aligned = procrustes_align(HC_raw, HC_reference)

# Step 2: Learn filter in aligned space
F' = CVD_aligned @ A' + b'  # Target: HC_aligned

# Step 3: Use reconstruction W
Channels = W_pinv @ HC_aligned  # HC → Channels
# ... (inverse to RGB)
```

**장점**: Reconstruction framework와 통합 가능

**단점**: Phase 2A 전체 재학습 필요

---

## 6. 현재 불확실한 점 (Questions)

### Q1: Phase 2A 데이터가 정말 raw voxel인가?
- **확인 필요**: `amplitudes_z.npy`가 Procrustes 적용 전인지 확인
- **사용자 언급**: "필터는 CVD procres -> HC procres"
  - 이것이 데이터가 Procrustes aligned라는 의미인가?
  - 아니면 loss function이 geometric transformation 학습한다는 의미인가?

### Q2: Reconstruction W matrix를 사용할 수 있나?
- W는 Procrustes space에서 정의
- Phase 2A filter는 raw space
- Space 변환 방법이 있나?

### Q3: 어떤 방법을 선택할까?
- **Option 1**: 간단, Phase 2A 직접 사용 (8 colors만)
- **Option 2**: Space conversion 필요 (복잡)
- **Option 3**: Phase 2A 재학습 (시간 소요)

---

## 7. 다음 단계 (Next Steps)

### Immediate:
1. **데이터 확인**: Phase 2A 패턴이 raw인지 Procrustes aligned인지 명확히 확인
   - `results/group_level/phase2a_data/patterns/` 파일들 검증
   - Procrustes transformation 정보가 저장되어 있는지 확인

2. **사용자 확인**: "필터는 CVD procres -> HC procres"의 정확한 의미
   - 데이터가 Procrustes aligned?
   - Loss function이 geometric transformation 학습?

### Based on Confirmation:
- **If raw voxel**: Option 1 구현 (간단)
- **If Procrustes aligned**: Option 2 or 3 선택

---

## 8. 임시 결론 (Tentative Conclusion)

**현재 가장 가능성 높은 방법**: **Option 1** (Raw Voxel Space)

**이유**:
1. Phase 2A가 `amplitudes_z.npy` (raw) 사용한 것으로 보임
2. Filter (A, b) 바로 사용 가능
3. 8개 색상에 대해서만 RGB 계산하면 됨
4. 추가 Procrustes alignment 필요 없음

**단, 사용자 확인 필요**: Phase 2A 데이터가 정말 raw voxel인지!

---

## Appendix: Code Verification

### Phase 2A Extract Patterns (확인됨)
```python
# scripts/phase2a_extract_patterns.py
amp_file = roi_dir / "amplitudes_z.npy"  # GLM beta (z-scored)
amplitudes = np.load(amp_file)  # (n_runs, 8, n_voxels)
pattern = amplitudes.mean(axis=2)  # (8, n_voxels)
# No Procrustes here!
```

### Reconstruction with Procrustes (별도 pipeline)
```python
# analysis/group_level/reconstruction_with_procrustes.py
aligned, disparity = align_to_reference(pattern, hc_reference)
# Procrustes alignment 적용
# W matrix 학습 in aligned space
```

→ **두 개가 별도 pipeline!**

---

**End of Discussion Document**
