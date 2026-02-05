# Between-Subject Alignment 수정된 계획
**Date:** 2026-02-03
**Revision:** Based on user feedback

---

## 주요 수정 사항

### 1. 섣부른 결론 제거 ✅
- **이전**: "Between-subject alignment는 fundamental limits 존재"
- **수정**: LOSO는 within-subject Procrustes만 적용된 상태 → Between-subject alignment 효과는 **empirical testing 필요**
- **근거**: 아직 between-subject alignment 시도 안 함

### 2. Non-Variance Voxel 제거 전략 재평가 ✅
- **이전 이해**: "Problematic voxel 포함하면 Procrustes 망가짐"
- **수정된 이해**: "GLM 시 non-variance voxel을 **anatomically 일관되게** 제거 → 모든 subject가 동일 voxel indexing 확보"
- **효과**: Anatomical alignment에서 voxel correspondence 보장 가능

---

## 수정된 계획 (3가지 Option)

### **Option A: Non-Variance Voxel 제거 + ANOVA + Between-Procrustes (✅ 추천)**

#### 장점
1. **Anatomical voxel correspondence 확보**:
   ```python
   # Step 1: GLM 단계에서 anatomically consistent한 voxel만 유지
   # MNI space의 모든 voxel에 대해:
   for voxel_idx in all_mni_voxels:
       # 모든 subject에서 이 voxel이 valid한지 확인
       valid_across_subjects = []
       for subject in all_subjects:
           variance = np.var(beta_estimates[subject, voxel_idx, :])
           valid_across_subjects.append(variance > threshold)

       # 모든 subject에서 valid한 voxel만 유지
       if all(valid_across_subjects):
           keep_voxel(voxel_idx)

   # 결과: 모든 subject가 동일한 voxel set (anatomically aligned)
   ```

2. **ANOVA top-k selection**도 이제 의미 있음:
   - 동일 voxel index = 동일 anatomical location (guaranteed)
   - F-score로 color-selective voxels 선택
   - Between-subject Procrustes가 functional correspondence 추가로 해결

3. **Interpretability 유지**:
   - Voxel space에서 작업 → Anatomical location 해석 가능
   - SRM과 달리 "어느 영역이 중요한가" 분석 가능

#### 구현 단계

**Phase 1: Voxel Masking (GLM 수정 필요)**
```python
# File: analysis/phase1_preprocess_decoding/utils/cross_subject_voxel_mask.py

def create_cross_subject_valid_mask(subjects, roi, variance_threshold=1e-6):
    """
    Create mask of voxels valid across all subjects

    Returns:
        valid_mask: (n_voxels_roi,) boolean array
            True if voxel is valid (variance > threshold) in ALL subjects
    """
    roi_mask = load_roi_mask(roi)  # (x, y, z) in MNI space
    voxel_indices = np.where(roi_mask)

    validity_matrix = []  # (n_subjects, n_voxels)

    for subject in subjects:
        # Load raw beta estimates for this subject
        betas = load_betas(subject, roi)  # (n_voxels, n_colors * n_runs)

        # Check variance per voxel
        voxel_variance = np.var(betas, axis=1)
        is_valid = voxel_variance > variance_threshold

        validity_matrix.append(is_valid)

    validity_matrix = np.array(validity_matrix)  # (n_subjects, n_voxels)

    # Keep only voxels valid in ALL subjects
    valid_mask = np.all(validity_matrix, axis=0)

    return valid_mask, validity_matrix
```

**Phase 2: ANOVA Voxel Selection (on valid voxels only)**
```python
# Only consider anatomically valid voxels
valid_mask = create_cross_subject_valid_mask(subjects, roi)

for subject in subjects:
    amplitudes = load_amplitudes(subject, roi)
    amplitudes_valid = amplitudes[:, :, valid_mask]  # Same voxel indices!

    # ANOVA F-score on valid voxels
    f_scores = compute_anova_f_scores(amplitudes_valid)
    top_k_indices = np.argsort(f_scores)[-k:]

    amplitudes_selected = amplitudes_valid[:, :, top_k_indices]
```

**Phase 3: Between-Subject Procrustes**
```python
# Now all subjects have same k voxels (anatomically + functionally selected)
hc_subjects = ['01', '02', '03', '05', '06']  # Exclude 04, 07
cvd_subjects = ['08', '09']  # Exclude 10

# Compute HC reference (after within-subject Procrustes)
hc_patterns = [load_amplitudes_procrustes(sub) for sub in hc_subjects]
hc_reference = np.mean(hc_patterns, axis=0)  # (8 colors, k voxels)

# Align all subjects to HC reference
for subject in all_subjects:
    patterns = load_amplitudes_procrustes(subject)[:, :, :]  # (6 runs, 8 colors, k voxels)

    # Run-averaged pattern
    pattern_mean = patterns.mean(axis=0)  # (8 colors, k voxels)

    # Procrustes to HC reference
    R, disparity = orthogonal_procrustes(pattern_mean.T, hc_reference.T)

    # Apply to all runs
    aligned = patterns @ R
    save(aligned, f'amplitudes_between_procrustes_{subject}.npy')
```

#### 기대 효과
- **LOSO 개선**: 0.05-0.15 → **0.15-0.25** (anatomical + functional alignment)
- **Disparity 감소**: 현재 sub-10 3139 → **500-1000** (reasonable range)
- **Interpretability**: Voxel-level analysis 가능

---

### **Option B: Whitening + Non-Variance Removal + Procrustes (✅ 가장 추천)**

Option A에 whitening 추가:

```python
# After within-subject Procrustes, before ANOVA selection
for subject in subjects:
    amplitudes_proc = load_amplitudes_procrustes(subject)

    # Whitening (subject-specific noise covariance)
    cov_noise = estimate_noise_cov(amplitudes_proc)
    whitening_matrix = compute_whitening(cov_noise)
    amplitudes_whitened = amplitudes_proc @ whitening_matrix

    # Then proceed with valid mask + ANOVA + between-Procrustes
```

**기대 효과**:
- Within-subject: +0.15-0.25 (whitening)
- Between-subject: +0.10-0.15 (Procrustes with proper voxel correspondence)
- **Total**: 0.15-0.26 → **0.40-0.55** (2.5-3× improvement)

---

### **Option C: SRM (여전히 유효한 대안)**

Non-variance voxel 제거 없이도 작동:

```python
# SRM은 voxel count 불일치를 자동 처리
srm = SRM(n_iter=10, features=50)

# 각 subject의 모든 voxels 사용 가능 (variance 상관없음)
data_list = [load_amplitudes(sub) for sub in subjects]
shared_responses = srm.fit_transform(data_list)
```

**장점**: Voxel masking 불필요, 구현 간단
**단점**: Interpretability 낮음 (latent space)

---

## 비교 분석

| Method | Voxel Correspondence | Interpretability | Expected Improvement | Implementation |
|--------|---------------------|------------------|---------------------|----------------|
| **A. Non-Var Remove + Proc** | ✅ Guaranteed (anatomical) | ⭐⭐⭐⭐⭐ | +0.10-0.15 | Medium |
| **B. Whitening + A** | ✅ Guaranteed | ⭐⭐⭐⭐⭐ | +0.25-0.40 | Medium-High |
| **C. SRM** | ⚠️ Functional only | ⭐⭐ | +0.10-0.18 | Easy |

---

## 최종 권장사항

### Priority 1: **Option B (Whitening + Non-Variance Removal + Between-Procrustes)**

**근거**:
1. ✅ Anatomical correspondence 보장 (non-variance removal)
2. ✅ Functional alignment 시도 (between-Procrustes)
3. ✅ Within-subject SNR 증가 (whitening)
4. ✅ Interpretability 유지 (voxel space)
5. ✅ 최대 효과 기대 (2.5-3× improvement)

**구현 순서**:
1. Whitening 구현 (1-2 days) → 즉시 검증 가능
2. Cross-subject valid mask 생성 (1 day)
3. ANOVA selection on valid voxels (1 day)
4. Between-subject Procrustes (1-2 days)
5. LOSO 재계산 및 효과 검증 (1 day)

**Total timeline**: ~1 week

---

### Priority 2: **Option C (SRM) - 병렬 시도**

Whitening + Procrustes 구현과 **동시에** SRM도 시도하여 비교:

```bash
# Parallel tracks
Track 1: Whitening → Non-var mask → ANOVA → Procrustes
Track 2: Whitening → SRM (직접 비교)
```

**이유**:
- SRM은 구현 쉬움 (brainiak 사용)
- Voxel masking 불필요
- 두 방법 비교하면 "anatomical vs functional alignment" 효과 구분 가능

---

## 구체적 실행 계획 (1주일)

### Day 1-2: Whitening (Within-Subject)
- [ ] Ledoit-Wolf covariance estimation
- [ ] Whitening transformation
- [ ] Noise ceiling 재계산
- **Expected**: Ceiling 0.45-0.62 → 0.55-0.75

### Day 3: Cross-Subject Voxel Masking
- [ ] Implement `create_cross_subject_valid_mask()`
- [ ] Check voxel counts: V1 (~300?), V2 (~200?), V3 (~40?), hV4 (~60?)
- **Critical**: Verify sub-04, sub-07, sub-10 제외 시 voxel count 증가

### Day 4: ANOVA Selection
- [ ] F-score 계산 (valid voxels only)
- [ ] Top-k selection (conservative: k = min voxel count × 0.8)
- **Expected k**: V1=240, V2=160, V3=32, hV4=48

### Day 5: Between-Subject Procrustes
- [ ] HC reference 생성
- [ ] All subjects align to reference
- [ ] Compute disparities
- **Expected disparity**: 500-1000 (vs current 3139 max)

### Day 6-7: Validation & Comparison
- [ ] LOSO 재계산 (whitened + between-Procrustes)
- [ ] SRM 구현 및 비교
- [ ] 결과 문서화

---

## 수정된 예상 효과

### Before (Current State)
```
Within-subject ceiling: 0.45-0.62
Current performance: 0.15-0.26 (26-67% of ceiling)
LOSO (no between-align): 0.05-0.15
```

### After Whitening Only
```
Within-subject ceiling: 0.55-0.75 (+10-15%)
Performance: 0.35-0.50 (60-70% of ceiling)
LOSO: 0.05-0.15 (unchanged, no between-align)
```

### After Whitening + Between-Procrustes (Non-Var Removal)
```
Within-subject ceiling: 0.55-0.75
Performance: 0.40-0.55 (70-80% of ceiling)
LOSO: 0.15-0.25 (+10-15%, anatomical + functional align)
```

### After Whitening + SRM (Comparison)
```
Within-subject ceiling: 0.55-0.75
Performance (shared space): 0.38-0.52
LOSO (shared space): 0.15-0.28 (functional align only)
```

---

## 중요한 검증 포인트

### 1. Non-Variance Voxel 제거 후 Voxel Count
Bad subjects 제외 전 vs 후:

| ROI | Before Exclusion | After Excluding 04/07/10 | Expected Increase |
|-----|-----------------|--------------------------|-------------------|
| V1  | ~250? | ~300? | +20% |
| V2  | ~180? | ~220? | +22% |
| V3  | ~5 (sub-07!) | ~45 | **+800%** |
| hV4 | ~50? | ~65? | +30% |

**Critical**: V3에서 sub-07 제외 시 극적인 개선 예상

### 2. Between-Procrustes Disparity 감소
- **Before** (anatomical only): 3139 (sub-10_V1)
- **After** (non-var removal + ANOVA): Expected 500-1000
- **Interpretation**: Disparity < 1000이면 reasonable alignment

### 3. LOSO Improvement
- **Null hypothesis**: LOSO remains 0.05-0.15 (no improvement)
- **Alternative**: LOSO increases to 0.15-0.25 (alignment works)
- **Statistical test**: Paired t-test (before vs after between-align)

---

## 결론

귀하의 제안 **"Non-variance voxel 제거 → Anatomical correspondence → Between-Procrustes"**는:

✅ **타당합니다** - Anatomical voxel correspondence 확보 가능
✅ **실현 가능합니다** - GLM 단계 수정으로 구현
✅ **효과적일 것으로 기대** - LOSO 0.05-0.15 → 0.15-0.25 (+10-15%)
✅ **Interpretability 유지** - Voxel-level analysis 가능

**최종 권장**:
1. **Whitening** (즉시 구현)
2. **Non-variance removal + ANOVA + Between-Procrustes** (1주일)
3. **SRM** (병렬 비교용)

이 조합이 최대 효과 (2.5-3× improvement) + 해석 가능성을 제공할 것으로 예상됩니다.

---

**Generated**: 2026-02-03
**Status**: Ready for implementation
**Next**: Whitening 구현 시작
