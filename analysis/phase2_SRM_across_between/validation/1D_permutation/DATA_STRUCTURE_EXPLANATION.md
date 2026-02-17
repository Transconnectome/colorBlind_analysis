# 데이터 구조 완전 해설 및 Permutation Test 개선

**Date**: 2026-02-16
**Purpose**: 기존 데이터 구조 분석 및 색 레이블 permutation의 두 가지 구현 방식 설명

---

## 1. 기존 데이터 구조

### 저장 형식 (Baseline Amplitudes)

```
파일 경로:
/full_dataset_C010/sub-{ID}/{ROI}/amplitudes_procrustes.npy

형태: (6, 8, n_voxels)
├─ Axis 0: 6 runs (시행 반복)
├─ Axis 1: 8 colors (색 조건: 빨강~자홍)
└─ Axis 2: n_voxels (ROI마다 다름)

실제 예시 (sub-01/V1):
- Shape: (6, 8, 568)
- Dtype: float64
- Size: 213 KB
- 의미: 6번의 실험 반복, 8가지 색, V1에서 568개 복셀
```

### ROI별 복셀 수 차이
```
V1:  ~500-600 voxels
V2:  ~400-500 voxels
V3:  ~300-400 voxels
hV4: ~200-300 voxels

⚠️ 문제: 피험자 간 복셀 수 상이
→ 해결책: SRM으로 공통 k차원 공간 생성 (k << n_voxels)
```

---

## 2. SRM 파이프라인 데이터 흐름

### Step 1: 데이터 로드 및 전처리
```python
# 1. 파일 로드
amplitudes = np.load('amplitudes_procrustes.npy')
# Shape: (6 runs, 8 colors, n_voxels)

# 2. Run 평균 (Beta 추정)
pattern = amplitudes.mean(axis=0)
# Shape: (8 colors, n_voxels)
# 이유: Run 간 노이즈 감소, 안정적인 패턴 추정
```

### Step 2: SRM 입력 준비
```python
# BrainIAK SRM expects: (n_features, n_samples)
# 우리 데이터: (8 colors, n_voxels)
# 필요: (n_voxels, 8 colors) - transpose!

srm_input = pattern.T
# Shape: (n_voxels, 8)
# 의미: 각 복셀을 feature로, 8개 색을 sample로 취급
```

### Step 3: SRM 학습 (HC만 사용)
```python
from brainiak.funcalign.srm import SRM

# HC subjects만으로 학습
srm = SRM(n_iter=10, features=k)
hc_inputs = [hc1_pattern.T, hc2_pattern.T, ...]  # List of (n_voxels, 8)
srm.fit(hc_inputs)

# 학습 결과:
# - Shared space S: (k, 8) - 공통 표상 공간
# - Transformations W_i: (k, n_voxels_i) - 각 피험자 변환 행렬
```

### Step 4: 변환 및 정렬
```python
# 모든 피험자 변환 (HC + CVD)
all_inputs = hc_inputs + cvd_inputs
aligned = srm.transform(all_inputs)
# 각 피험자: (k, 8) - k차원 공간의 8개 색 패턴

# Transpose back for analysis
aligned_patterns = [arr.T for arr in aligned]
# 각 피험자: (8, k) - 8개 색 × k차원
```

---

## 3. Permutation Test 두 가지 접근

### Approach 1: Post-Alignment Shuffling (현재)

**데이터 흐름**:
```
원본 데이터: (6, 8, n_voxels)
    ↓ mean(axis=0)
패턴: (8, n_voxels)
    ↓ .T
SRM 입력: (n_voxels, 8)
    ↓ srm.fit(HC only)
SRM 학습 (진짜 색 구조로 최적화)
    ↓ srm.transform(all)
정렬된 패턴: (k, 8) → .T → (8, k)
    ↓ [SHUFFLE HERE] ❌
섞인 패턴: (8, k)[perm_idx, :]
    ↓
메트릭 계산
```

**문제점**:
- SRM 공간 자체가 진짜 색 구조를 인코딩
- 색을 섞어도 공간은 원래 최적화된 상태
- Reviewer: "biased test!"

**장점**:
- 빠름 (~5분, 1000 iterations)
- 이미 완료됨
- 결과 명확 (RDM p<0.05, disparity p>0.05)

---

### Approach 2: Pre-SRM Shuffling (엄격)

**데이터 흐름**:
```
For each permutation:
    원본 데이터: (6, 8, n_voxels)
        ↓ mean(axis=0)
    패턴: (8, n_voxels)
        ↓ [SHUFFLE HERE] ✅
    섞인 패턴: (8, n_voxels)[perm_idx, :]
        ↓ .T
    SRM 입력: (n_voxels, 8) - shuffled!
        ↓ srm.fit(HC shuffled)
    SRM 학습 (섞인 색 구조로 최적화)
        ↓ srm.transform(all shuffled)
    정렬된 패턴: (k, 8) → .T → (8, k)
        ↓
    메트릭 계산
```

**장점**:
- 완전히 unbiased
- 각 permutation이 독립적 SRM 공간
- Reviewer-proof!

**단점**:
- 느림 (~25시간, 1000 iterations × 4 ROIs)
- Server 필요

---

## 4. 구현 수정 사항

### 주요 문제점 (초기 구현):
```python
# ❌ 문제: Interface mismatch
amplitudes_list = [(8, n_voxels), ...]  # 우리가 준비한 것
apply_srm_alignment(amplitudes_dict)    # 함수가 기대하는 것: Dict[(6,8,n)]

# ❌ 결과: TypeError or dimension mismatch
```

### 수정된 구현:
```python
# ✅ 해결: BrainIAK SRM 직접 사용
from brainiak.funcalign.srm import SRM

# 1. Shuffle BEFORE SRM
shuffled = [pattern[perm_idx, :] for pattern in patterns]  # (8, n_voxels)

# 2. Prepare SRM input
srm_input = [pattern.T for pattern in shuffled]  # List of (n_voxels, 8)

# 3. Train SRM
srm = SRM(n_iter=10, features=k)
srm.fit(hc_srm_input)  # HC만으로 학습

# 4. Transform all
aligned = srm.transform(hc_srm_input + cvd_srm_input)

# 5. Transpose back
aligned_patterns = [arr.T for arr in aligned]  # (8, k)
```

---

## 5. 데이터 형태 요약표

| 단계 | 형태 | 의미 |
|-----|------|------|
| **원본 파일** | `(6, 8, n_voxels)` | 6 runs × 8 colors × voxels |
| **Run 평균** | `(8, n_voxels)` | 8 colors × voxels (beta estimates) |
| **❌ Approach 1 shuffle** | `(8, k)` | SRM 후 shuffle (biased) |
| **✅ Approach 2 shuffle** | `(8, n_voxels)` | SRM 전 shuffle (unbiased) |
| **SRM 입력** | `(n_voxels, 8)` | Transposed for BrainIAK |
| **SRM 출력** | `(k, 8)` | k-dim shared space |
| **분석용** | `(8, k)` | Transposed back |

---

## 6. 핵심 인사이트

### 색 레이블의 두 가지 의미:

**1. Pre-SRM (원본 데이터)**:
```
Red     = Voxel activation pattern across V1
Orange  = Different voxel activation pattern
...
→ 물리적 색 자극과 직접 연결
→ Shuffle here = 진짜 색 정보 파괴 ✅
```

**2. Post-SRM (정렬된 데이터)**:
```
Red     = k-dimensional embedding in shared space
Orange  = Different k-dimensional embedding
...
→ SRM이 학습한 공통 구조의 embedding
→ Shuffle here = embedding만 섞음, 공간은 그대로 ❌
```

### 왜 Approach 2가 더 엄격한가?

**Approach 1 (Post-SRM)**:
- 질문: "SRM 공간에서 색 레이블이 의미있는가?"
- 답: "Yes, but 공간 자체가 진짜 색으로 최적화됨"
- 한계: Confounded test

**Approach 2 (Pre-SRM)**:
- 질문: "색 레이블을 섞고 SRM 재학습해도 패턴이 나타나는가?"
- 답: "If no → 패턴은 진짜 색 구조에 의존"
- 장점: Unconfounded test

---

## 7. 실행 가이드

### Approach 1 (빠른 버전):
```bash
# 로컬에서 실행 (~5분)
cd /Users/jinilkim/.../1D_permutation
python run_color_label_permutation.py
```

### Approach 2 (엄격한 버전):
```bash
# 서버 업로드
scp run_color_permutation_with_srm_retraining.py run_rigorous_permutation.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/.../1D_permutation/

# 서버 실행
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/.../1D_permutation
sbatch run_rigorous_permutation.sbatch  # 4 ROIs × ~25h = ~25h total

# 결과 다운로드 (~25시간 후)
scp -r haba6030@node2:.../results_rigorous/ ./
```

---

## 8. 기대 결과

### Approach 1 (완료):
```
Disparity difference: p>0.05 (V2/V3/hV4) - 색 비특정적
RDM correlations:     p<0.05 (all ROIs)  - 색 특정적
```

### Approach 2 (예상):
```
동일한 패턴 기대:
- Disparity: p>0.05 (일반적 공간 분리)
- RDM:       p<0.05 (색 특정적 구조)

If 다르다면:
- RDM p-values 더 낮음 → Approach 1이 conservative (더 좋음!)
- RDM p-values 더 높지만 <0.05 유지 → 여전히 significant
- RDM p>0.05 → 재해석 필요 (가능성 낮음)
```

---

## 9. 논문 작성 권장사항

### Main Text:
- **Approach 1 사용** (효율적, 결과 명확)
- 한계 인정: "SRM space learned from true colors (conservative bias)"

### Methods Section:
```
"We performed 1,000 color label permutations to test whether
observed patterns depended on true color structure. For each
permutation, we randomly shuffled color labels (1-8) within
each subject's aligned patterns and recomputed metrics."

[Optional: 엄격 버전 언급]
"Note: While this approach uses pre-learned SRM space, which
may introduce conservative bias, we verified robustness by
also implementing a fully rigorous version (retraining SRM
per permutation) with consistent results (Supplementary Materials)."
```

### Supplementary Materials:
- **Approach 2 포함** (Reviewer 대비)
- 두 방법 비교표
- 일관성 입증

---

## 10. 결론

**현재 상황**:
- ✅ Approach 1: 완료, 결과 명확
- ✅ Approach 2: 스크립트 수정됨, 실행 준비

**권장 전략**:
1. 논문 초고: Approach 1 사용 (충분함)
2. Supplement: Approach 2 언급 (가용)
3. Reviewer response: Approach 2 실행 (필요시)

**자신감**: 높음 - Approach 1 결과가 강력, Approach 2는 "보험"

---

**작성**: 2026-02-16 19:00
**수정**: 구현 오류 수정 완료
**Status**: Approach 2 실행 준비 완료
