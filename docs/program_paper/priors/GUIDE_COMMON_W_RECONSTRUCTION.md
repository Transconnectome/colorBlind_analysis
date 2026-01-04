# Common W Matrix Reconstruction: Procrustes-based Analysis

## 개요

이 문서는 **HC의 common W matrix를 CVD에 적용하여 applicability를 검증**한 실험을 설명합니다.

### 핵심 아이디어

```
문제: CVD와 HC가 다른 voxel coordinate system 사용
    ↓
방법: 1) HC subjects로부터 common W matrix 학습
     2) Procrustes alignment로 CVD를 HC space에 정렬
     3) HC W 적용 → Reconstruction 평가
    ↓
검증: CVD aligned error << no-align error → Applicability 증명
```

---

## 실험 절차 (Experimental Procedure)

### 데이터 및 피험자

**Baseline Configuration:**
- **Dataset**: `deoblique_v2` (fMRIPrep with fieldmap applied)
- **Timestamp**: `baseline81_deob_determin` (81 color bins, deterministic)
- **Data Path**: `derivatives/BH2009_deoblique_v2/baseline81_deob_determin/`
- **Data Format**: `amplitudes_z.npy` (n_runs=6, n_colors=8, n_voxels)

**Subject Groups:**
- **HC (Healthy Control)**: sub-03, 05, 06, 07 (4 subjects)
  - **제외**: sub-02 (Procrustes alignment 시 문제 발생)
- **CVD (Color Vision Deficiency)**: sub-08, 09, 10 (3 subjects)
- **ROIs**: V1, V2, V3, hV4

**Voxel Count Handling:**
- HC와 CVD 간 voxel 개수 차이 존재
- 최소 voxel 개수로 truncate하여 dimension 일치
- W matrix도 동일하게 truncate

---

### Phase 1: HC Common W Training

**목표**: HC subjects로부터 consistent한 common W matrix 학습

**절차**:

1. **HC Reference 생성**
   ```python
   # 4명의 HC amplitudes 로드
   hc_patterns = [load_amplitudes(sub) for sub in ['03','05','06','07']]
   # (각각: 6 runs × 8 colors × n_voxels)

   # Run별 평균 계산 → Reference
   hc_reference = mean(hc_patterns, axis=0)  # (6 runs, 8 colors, n_voxels)
   ```

2. **Procrustes Alignment**
   ```python
   for each HC subject:
       for each run:
           # Pattern: (8 colors, n_voxels)
           pattern = amplitudes_z[run_idx]
           reference = hc_reference[run_idx]

           # Procrustes alignment
           aligned_pattern, disparity = procrustes(reference, pattern)

           # 저장
           amp_aligned[run_idx] = aligned_pattern
   ```

3. **LORO-CV (Leave-One-Run-Out Cross-Validation)**
   ```python
   for test_run_idx in range(6):  # 6 runs
       # Train runs = 나머지 5 runs
       train_runs = [r for r in range(6) if r != test_run_idx]

       # Step 3a: Train W using only train runs
       X_train = []
       C_train = []
       for train_run_idx in train_runs:
           for color_idx in range(8):
               voxel_pattern = amp_aligned[train_run_idx, color_idx, :]
               X_train.append(voxel_pattern)

               # 6-channel basis
               channel_response = compute_channel_response(color_idx)
               C_train.append(channel_response)

       # W estimation: W = X^T × C^T × (C × C^T)^-1
       W_loro = estimate_weight_matrix(X_train, C_train)

       # Step 3b: Test on test run
       X_test = amp_aligned[test_run_idx]  # (8 colors, n_voxels)
       C_est = (W_loro^T W_loro)^-1 W_loro^T X_test^T

       # Step 3c: Reconstruction
       reconstructed_hue = argmax_corr(C_est, hue_templates)

       # Step 3d: Error calculation
       error = circular_diff(reconstructed_hue, true_hue)
   ```

4. **HC No-alignment Comparison**
   ```python
   # Same LORO-CV but with ORIGINAL (unaligned) data
   for test_run_idx in range(6):
       train_runs = [r for r in range(6) if r != test_run_idx]

       # Train W with aligned data (same as above)
       W_loro = train_W_with_aligned_data(train_runs)

       # Test with UNALIGNED data
       X_test_noalign = amp_original[test_run_idx]  # NO alignment
       C_est_noalign = (W_loro^T W_loro)^-1 W_loro^T X_test_noalign^T

       # Compare aligned vs no-align error
       error_aligned = compute_error(X_test_aligned)
       error_noalign = compute_error(X_test_noalign)
       benefit = error_noalign - error_aligned
   ```

5. **HC Common W 저장**
   ```python
   # 모든 6 runs 사용하여 final W 계산
   X_all = concatenate([amp_aligned[r] for r in range(6)])
   C_all = corresponding_channels
   W_common = estimate_weight_matrix(X_all, C_all)

   # 저장: results/group_level/procrustes_reconstruction/{ROI}/
   save('procrustes_model.pkl', {
       'W_common': W_common,
       'hc_reference': hc_reference,
       'n_voxels': n_voxels
   })
   ```

---

### Phase 2: CVD Testing (With Alignment)

**목표**: HC common W를 CVD에 적용하여 applicability 검증

**절차**:

1. **CVD Amplitudes 로드**
   ```python
   cvd_amplitudes = load_amplitudes('sub-08')  # (6, 8, n_voxels_cvd)
   ```

2. **Voxel 개수 일치**
   ```python
   min_voxels = min(n_voxels_cvd, n_voxels_hc)
   cvd_amp = cvd_amplitudes[:, :, :min_voxels]
   hc_ref = hc_reference[:, :, :min_voxels]
   W_truncated = W_common[:min_voxels, :]
   ```

3. **Procrustes Alignment (CVD → HC Reference)**
   ```python
   for run_idx in range(6):
       pattern = cvd_amp[run_idx]  # (8, min_voxels)
       reference = hc_ref[run_idx]

       # CVD를 HC reference에 맞춤
       aligned_pattern, disparity = procrustes(reference, pattern)
       cvd_aligned[run_idx] = aligned_pattern
   ```

4. **LORO-CV with HC W**
   ```python
   for test_run_idx in range(6):
       train_runs = [r for r in range(6) if r != test_run_idx]

       # HC W 재학습 (train runs만 사용)
       W_loro = retrain_W_with_HC_data(train_runs)

       # CVD aligned data로 test
       X_test = cvd_aligned[test_run_idx]
       C_est = (W_loro^T W_loro)^-1 W_loro^T X_test^T

       # Reconstruction & error
       reconstructed_hue = argmax_corr(C_est, hue_templates)
       error = circular_diff(reconstructed_hue, true_hue)
   ```

5. **결과 저장**
   ```python
   # cvd_reconstruction_errors.csv
   save_csv({
       'subject_id': '08',
       'mean_error': mean(errors),
       'accuracy': accuracy,
       'n_runs': 6
   })
   ```

---

### Phase 3: CVD Testing (No Alignment - Comparison)

**목표**: Alignment benefit 정량화

**절차**:

1. **CVD Unaligned Data 로드**
   ```python
   cvd_original = load_amplitudes('sub-08')[:, :, :min_voxels]
   # NO Procrustes alignment
   ```

2. **LORO-CV with HC W (No Alignment)**
   ```python
   for test_run_idx in range(6):
       train_runs = [r for r in range(6) if r != test_run_idx]

       # Same HC W (학습은 HC aligned data로)
       W_loro = load_HC_W_loro(train_runs)

       # Test with CVD UNALIGNED data
       X_test_noalign = cvd_original[test_run_idx]
       C_est_noalign = (W_loro^T W_loro)^-1 W_loro^T X_test_noalign^T

       # Reconstruction
       reconstructed_hue_noalign = argmax_corr(C_est_noalign, hue_templates)
       error_noalign = circular_diff(reconstructed_hue_noalign, true_hue)
   ```

3. **Benefit 계산**
   ```python
   benefit = error_noalign - error_aligned
   # V1 예시: 87° - 5.5° = 81.5° benefit
   ```

4. **결과 저장**
   ```python
   # cvd_reconstruction_errors_noalign.csv
   save_csv({
       'subject_id': '08',
       'mean_error': mean(errors_noalign),
       'accuracy': accuracy_noalign,
       'n_runs': 6
   })
   ```

---

### 통계 분석

**Circular Error Metrics:**
```python
def circular_diff_deg(hue1, hue2):
    """Circular distance in degrees [0, 180]"""
    diff = abs(hue1 - hue2)
    if diff > 180:
        diff = 360 - diff
    return diff
```

**Classification Accuracy:**
```python
# 8 color bins at 45° intervals (0, 45, 90, ..., 315)
predicted_color = argmin(circular_diff(reconstructed_hue, bin_centers))
accuracy = sum(predicted == true) / n_total
```

**Chance Level:**
- Uniform circular distribution: 90°
- 8 colors at 45° intervals → average error to nearest bin ≈ 90°

**Comparison Tests:**
- Aligned vs No-align: Paired comparison (same subjects)
- HC vs CVD: Group comparison
- Statistical significance: t-test, permutation test (if needed)

---

### 실행 요약

**Train HC Common W:**
```bash
sbatch run_procrustes_reconstruction_train.sbatch
# → results/group_level/procrustes_reconstruction/{ROI}/procrustes_model.pkl
# → results/group_level/procrustes_reconstruction/{ROI}/hc_reconstruction_summary.csv
```

**Test CVD (Aligned):**
```bash
sbatch run_procrustes_reconstruction_test.sbatch
# → results/group_level/procrustes_reconstruction/{ROI}/cvd_reconstruction_errors.csv
```

**Test CVD (No Alignment):**
```bash
sbatch run_procrustes_reconstruction_test_noalign.sbatch
# → results/group_level/procrustes_reconstruction/{ROI}/cvd_reconstruction_errors_noalign.csv
```

**Comparison:**
```python
aligned = read_csv('cvd_reconstruction_errors.csv')
noalign = read_csv('cvd_reconstruction_errors_noalign.csv')
benefit = noalign['mean_error'] - aligned['mean_error']
```

---

## 실험 결과 (2025-12-19)

### ✅ 주요 발견

#### 1. HC Common W의 Consistency 증명

```
ROI    | HC Aligned | HC No-align | HC Baseline (Individual) | Benefit
-------|------------|-------------|--------------------------|--------
V1     | 5.1°       | 49.5°       | 30-40°                   | 44.3°
V2     | 5.6°       | 54.4°       | 30-40°                   | 48.8°
V3     | 9.6°       | 70.2°       | 30-40°                   | 60.6°
hV4    | 15.4°      | 69.7°       | 30-40°                   | 54.3°
```

**해석:**
- HC aligned (5-15°) << baseline (30-40°) → **Common W가 individual W보다 robust**
- HC no-align (50-70°) > baseline → Alignment 없이는 성능 저하
- **결론: HC subjects가 consistent한 W 공유**

#### 2. CVD에 HC W 적용 가능성 증명

```
ROI    | CVD + HC W (Aligned) | CVD + HC W (No-align) | Benefit
-------|----------------------|-----------------------|--------
V1     | 5.5°                 | 87.0°                 | 81.5°
V2     | 5-6°                 | 84.0°                 | 78-79°
V3     | 5-10°                | 96.0°                 | 86-91°
hV4    | 5-10°                | 93.0°                 | 83-88°
```

**해석:**
- Aligned: 5-10° → **HC-like reconstruction 달성!**
- No-align: 84-96° (≈ chance 90°) → **Alignment 절대 필수**
- CVD benefit (81°) > HC benefit (44°) → **CVD가 더 다른 coordinate system**

#### 3. 필터 설계 로직 검증

```
목표: CVD voxel response를 HC voxel response와 일치
방법: Input color 조정 (Procrustes alignment)
평가: 동일한 W (HC common W) 사용 → Reconstruction
결과: 5° error → HC와 동등한 성능
```

**의의:**
- ✅ Voxel response 일치 시 동일한 decoder (W) 사용 가능
- ✅ HC common W의 consistency가 필터 유효성의 근거
- ✅ CVD neural pattern이 HC-like structure 포함 증명

---

### ⚠️ Limitations & Future Directions

#### 검증 필요 사항:

**1. W가 HC-CVD 간 정말 공통인가?**
- **현재**: Procrustes alignment 후 동일한 W 사용 가능 (reconstruction error 5°)
- **부족**: W 자체가 HC-CVD 간 동일한지 직접 검증 안 됨
- **필요**:
  - CVD individual W 학습 후 HC common W와 직접 비교
  - W matrix의 structure similarity 분석
  - Cross-validation: HC W로 CVD 학습, vice versa

**2. 만약 W가 다르다면?**
- **Individual model**: CVD 개인별 W 학습 필요
- **Nonlinear transformation**: Linear Procrustes로 부족할 수 있음
- **Forward encoding model**: Color stimulus → Neural response 예측 모델 필요

**3. Neural vs. Perceptual**
- **현재**: Neural reconstruction (fMRI-based)
- **필요**: Behavioral validation
  - CVD가 필터 적용 후 실제로 색 구분 개선되는지
  - Subjective color naming task
  - Discrimination threshold 측정

#### HC No-alignment 결과의 의미:

```
HC no-align (49-70°) vs Baseline (30-40°)
→ 왜 no-align이 더 높은가?
```

**가능한 설명:**
1. Common W < Individual W (개인 최적화의 중요성)
2. Voxel selection이 subject-specific일 수 있음
3. Alignment가 voxel correspondence 정확도를 높임

**향후 탐구:**
- Individual W vs Common W의 structure 비교
- Alignment가 voxel-level correspondence를 어떻게 개선하는지
- Subject-specific vs Group-level feature의 trade-off

---

### 🎯 현재 연구의 Contribution

**증명된 것:**
1. ✅ HC common W의 consistency와 robustness
2. ✅ CVD에 HC W 적용 가능 (Procrustes alignment 통해)
3. ✅ CVD neural pattern의 HC-like structure 존재
4. ✅ 색 조정 필터의 **이론적 근거** 제공

**실용적 의의:**
- Filter 설계의 validation metric 제시
- Voxel response alignment → 성능 평가 pipeline 확립
- CVD intervention 가능성의 neural evidence

**다음 단계:**
- Forward model 개발 (color → neural response)
- Behavioral validation (실제 색 구분 개선 확인)
- Individual vs Common W의 최적 balance 탐색

---

**최종 업데이트:** 2025-12-19
**실험 코드**: `analysis/group_level/reconstruction_with_procrustes.py`
**SLURM Scripts**: `run_procrustes_reconstruction_*.sbatch`
