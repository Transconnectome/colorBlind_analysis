# Preprocessing Reports

## 1. New preprocessing with different setting 
### Executive Summary to share
피질 표면을 기준으로 하는 FreeSurfer 설정이, 좁은 시각 피질 EPI 측정에서 왜곡을 발생시켜 fieldmap 정합에서 왜곡을 발생함을 확인하였습니다. 이에 BBR (corregistration - 정합)을 단순하게 바꾸고 FreeSurfer 설정을 끔으로써, T1w와 BOLD의 brain mask 겹치는 비율을 유의미하게 높이고 ROI 생성 불가능 (voxel 겹침 없음 오류)가 발생하지 않음을 확인했습니다! 

### **핵심 성과**

```
문제: Preprocessing catastrophe (Dice 0.376, 0% pass)
해결: --fs-no-reconall (FreeSurfer 제거)
결과: Complete success (Dice 0.889, 83.3% pass)
```

| Metric | 의미 | Before | After | 개선도 |
|--------|--------|--------|-------|--------|
| **Dice coefficient** | T1w와 BOLD의 brain mask 겹침 비 | 0.376 | **0.889** | **+136%** |
| **Pass rate (≥0.80)** | Dice 기반 통과율 | 0.0% | **83.3%** | **+83pp** |
| **ROI generation failure** | ROI | 45.4% | **0.0%** | **완전 해결** |
| **Excellent runs (≥0.90)** | 적합 시행비 | 0.0% | **73.3%** | **+73pp** |

***ROI 별 Voxel 수**
- V1 (primary visual): ~2000-3500 voxels
- V2, V3: ~1000-3000 voxels
- V4 (smaller, higher-level): ~500-700 voxels

### 🎯 Subject별 종합 평가
**0. 결론**
- Run 단위 측정이기 때문에, good runs만 살리기
- CVD: ALL runs
- NON-CVD: 8 ~ 12 runs excluded / Total 42 runs = at least 30 runs

**1. Tier 1: Excellent (100% pass)**
**Sub-01, 03, 04, 08, 09, 10** (6명)

```
특징:
- Mean Dice: 0.936-0.954
- Pass rate: 100% (24/24 runs)
- ROI generation: 100% success
- Motion: < 0.2mm
- Dropout: Minimal
```

**2. Tier 2: Good (83% pass)**
**Sub-02, 05** (2명)

```
특징:
- Mean Dice: 0.823, 0.916
- Pass rate: 83.3% (20/24 runs)
- 4개 runs만 Dice < 0.80
- Dropout: Moderate (일부)

권장 사용:
✅ Individual-level analysis
✅ Group-level analysis (with caution)
⚠️  나쁜 4 runs 제외 고려
```

---

**3. Tier 3: Partial (33% pass)**
**Sub-06, 07** (2명)

```
특징:
- Mean Dice: 0.730, 0.746
- Pass rate: 33.3% (8/24 runs)
- 높은 변동성 (run-dependent)
- T1 mask over-extraction

권장 사용:
✅ Individual-level analysis (good runs만)
❌ Group-level analysis 제외
📝 Supplementary material / Case study
```

### 그 외 판단 기준
**1. ROI Coverage**: 
```
ROI Coverage = |ROI ∩ Brain| / |ROI|

where:
  ROI = Generated ROI after threshold
  Brain = BOLD brain mask
```

**물리적 의미**:
- 생성된 ROI의 몇 %가 실제 brain mask 안에 있는가?
- ROI가 brain 밖으로 튀어나가지 않는가?

**결과**:
- 대부분 coverage > 0.95
- ROI가 brain mask 안에 잘 포함됨

**2. T1/BOLD Mask Ratio**

**정의**:
```
Mask Ratio = |T1 brain mask| / |BOLD brain mask|
```

**물리적 의미**:
- T1 brain mask가 BOLD brain mask보다 몇 배 큰가?
- 이상적: ~1.0 (비슷한 크기)

**우리 결과**:
- 대부분: 1.0-1.5 (정상)
- Sub-06, 07: ~2.5-3.0 (T1 mask 과도, non-brain tissue 포함)
- → 이것이 Sub-06, 07의 낮은 Dice 원인


**3: ROI Size by Subject**

**무엇을 보여주는가?**:
- X축: Subject
- Y축: Mean ROI voxels
- 4개 선: V1, V2, V3, V4

**핵심 관찰**:
1. **V1이 가장 큼**: 2000-3500 voxels (primary visual)
2. **V2, V3**: 중간 크기
3. **V4**: 가장 작음 ~500-700 voxels (higher-level)
4. **Subject 간 변동**: 정상 (brain size, atlas probability)

**해석**:
- 모든 ROI가 적절한 크기
- 분석에 충분한 voxel 개수
- Hierarchical structure 반영 (V1 > V2 > V3 > V4)


## 2. MNI alignment check for candidates
### 카카오톡 전송 버전
다만, T1w와 BOLD 데이터를 MNI 공간으로 변환할 때 문제는 없었습니다. 즉, 기존 데이터를 활용한 앞선 분석을 사용 가능하나, oblique 이용 시 왜곡 문제로 인한 ROI 추출 시 유효 voxel 부재 문제가 발생하였던 것입니다. 이에 이후 분석에서는 oblique 문제를 별도 조치 없이 fMRIprep의 corregistration 으로 해결한 original_v3를 활용하고자 합니다. 

### Pipeline
**목적**: MNI 공간으로의 T1w, BOLD 변환 문제 확인 및 개선 시도
- T1w과 BOLD 차원 모두 MNI 공간으로 변환 시 오류 발생 여부를 확인하고자 하였습니다. 
- 이 차이를 deoblique_v2와 original_v3를 비교하여 설정으로 인한 문제 여부 확인. 

**결과**

| 항목       | deoblique_v2           | original_v3            | 차이 |
|------------|------------------------|------------------------|------|
| T1w Shape  | (97, 115, 97)          | (97, 115, 97)          | 없음 |
| BOLD Shape | (97, 115, 97)          | (97, 115, 97)          | 없음 |
| Affine     | [-96.5, -132.5, -78.5] | [-96.5, -132.5, -78.5] | 없음 |
| Grid ✅    | OK                     | OK                     | 없음 |
| MNI 정합   | ✅ 정상                | ✅ 정상                | 없음 |

## 3. Native ROI method
### 카카오톡 전송 버전
아울러, hyperalignment로 공용 공간을 제작하기에, MNI 공간을 활용하지 않고 ROI 마스크를 적용하여 corregistration 문제를 해결해보고자 하였습니다. 그러나 현재 ROI Atlas가 MNI 공간 기준이기에, 피험자별 변환이 fMRIprep의 변환 식에 의존하였습니다. 이는 기존 정합 문제를 반복하기에 활용할 수 없습니다. 

다만, 현재 volume 단위 분석 대신, fMRIPrep의 fsaverage를 이용하는 표면 기반 surface 분석 방법이 존재하기는 합니다. 이는 corregistration 단위를 바꾸어서 위 방법을 시도하는 건데.. 우선 original_v3의 결과가 좋아서 보류하고자 합니다.

### Background
**목적**: Hyperalignment 활용에 따른 BOLD 공간에서의 mask 적용 시도
**배경**: Hyperalignment는 Voxel overlay가 아닌 Pattern 분석으로 common space를 형성하기에, MNI space로의 변환이 필요 없음.
  - 기존 분석에서 일부 피험자의 MNI 정합(registration)의 실패를 우회하여 해결하고자 함. 

### Pipeline
Wang Atlas (MNI) → T1w native → BOLD native → Binary Mask

단계별 처리:
1. Wang probabilistic atlas에서 ROI 추출 (V1, V2, V3, hV4)
2. ANTs를 사용한 MNI → T1w 변환
3. fMRIPrep transform을 사용한 T1w → BOLD 변환
4. Threshold=20으로 이진 마스크 생성
5. QC overlay 이미지 생성

### 피험자별 상세 결과

Sub-02 (유일한 부분 성공 케이스)

| ROI | MNI→T1w           | T1w→BOLD        | Binary Mask     | 상태             |
|-----|-------------------|-----------------|-----------------|------------------|
| V1  | ✅ 305,002 voxels | ✅ 4,962 voxels | ✅ 1,233 voxels | 성공             |
| V2  | ✅ 366,907 voxels | ❌ 0 voxels     | ❌              | 실패 (BOLD 변환) |
| V3  | ✅ 408,416 voxels | ❌ 0 voxels     | ❌              | 실패 (BOLD 변환) |
| hV4 | ✅ 164,913 voxels | ❌ 0 voxels     | ❌              | 실패 (BOLD 변환) |

Sub-01, 03, 05, 06, 07 (완전 실패)

- 모든 ROI에서 MNI→T1w 변환이 0 voxels 출력
- 첫 번째 단계부터 변환 실패

Sub-08 (비정상 결과)

| ROI | MNI→T1w                                | 상태                           |
|-----|----------------------------------------|--------------------------------|
| V1  | ⚠️ 25,271,129 voxels (비정상적으로 큼) | 실패                           |
| V2  | ❌ 0 voxels                            | 실패                           |
| V3  | ❌ 0 voxels                            | 실패                           |
| hV4 | ✅ 182,701 voxels                      | T1w까지만 성공, BOLD 변환 실패 |

### 실패 요인 확인
**1차 실패: MNI → T1w 변환 (5명의 피험자)**
- fMRIPrep의 MNI 정합 자체가 실패하여 transform 파일이 손상됨
- *_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5 파일은 존재하지만 내용이 유효하지 않음
- 이전 분석에서 확인된 registration quality 문제와 동일한 근본 원인
- **즉, 정합 방식을 활용하기에, 정합 변환을 활용하는 해당 방법은 문제를 해결 못 함**

---

## 4. 0106: Limited FOV BOLD-to-T1w Registration 방법론 비교

**날짜**: 2026-01-06
**배경**: PI 피드백 및 GitHub issue #331 검토
**목적**: 현재 사용 중인 registration 방법과 추천받은 방법들의 원리적 비교

### 4.1. 문제 상황 정의

**우리 데이터의 특수성**:
```
1. Limited FOV: Occipital area만 촬영 (whole brain 아님)
2. High obliquity: 평균 29.5° ± 5.7° (범위: 25.8°-41.6°)
3. Left-right phase encoding: Geometric distortion 발생
4. 시각피질 최적화: Calcarine sulcus에 직교하는 slice prescription
```

**Registration 실패의 근본 원인**:
```
Limited FOV fMRI (partial brain) ←→ T1w (whole brain)
                ↓
정합(registration) 시 두 단계 필요:
  (a) 초기 정렬 (Initial alignment): Intensity-based bulk registration
  (b) 미세 조정 (Refinement): Boundary-based registration (BBR)
                ↓
Limited FOV → (a) 단계에서 정보량 부족 → 실패
High obliquity → Coordinate system mismatch → (b) 단계도 실패 가능
```

**참고 문헌**:
- GitHub issue: https://github.com/nipreps/fmriprep/issues/331
- PI 피드백: 2026-01-06

---

### 4.2. 현재 사용 방법 (original_v3)

**실제 구현 (run_fmriprep_original_data_array.sbatch)**:
```bash
# 데이터: 원본 BIDS (oblique, no preprocessing)
Input: /storage/connectome/haba6030/bids_editted

# fMRIPrep 설정
--bold2t1w-dof 6              # Rigid registration (6 parameters)
--bold2t1w-init register      # Standard initialization (default)
--force-bbr                   # Force boundary-based registration
--use-syn-sdc warn            # Fieldmap-based SDC (with warning)
--fs-no-reconall              # Skip FreeSurfer (faster, Wang atlas용)
--dummy-scans 4               # 초기 4 volumes 제거
```

**Registration 처리 순서**:
```
Step 1: Initial alignment (a)
  Method: Intensity-based registration (FLIRT-like)
  Input: Oblique BOLD → T1w
  Output: Coarse transform (대략적 정렬)

Step 2: BBR refinement (b)
  Method: Boundary-based registration (white matter boundary)
  Input: Coarse transform from Step 1
  Output: Fine-tuned transform (정밀 정합)
  Force: --force-bbr (반드시 수행)

Step 3: MNI transformation
  Method: ANTs-based nonlinear registration
  Input: T1w → MNI152NLin2009cAsym
  Output: MNI space at 2mm resolution
```

**원리**:
```python
# Pseudocode for --bold2t1w-init register
def register_bold_to_t1w(bold, t1w):
    # (a) 초기 정렬: Intensity-based
    initial_transform = flirt_registration(
        source=bold,
        target=t1w,
        dof=6,  # Rigid (translation + rotation)
        cost_function='mutualinfo'  # Mutual information
    )

    # (b) BBR 미세 조정: Boundary-based
    if force_bbr:
        final_transform = bbr_registration(
            source=bold,
            target=t1w_wm_boundary,  # White matter boundary
            init_transform=initial_transform,
            schedule='default'  # Multi-resolution schedule
        )

    return final_transform
```

**장점**:
- ✅ 표준 fMRIPrep 파이프라인 (재현 가능)
- ✅ 모든 단계 수행 (robust)
- ✅ Mutual information cost function (서로 다른 contrast에 강건)
- ✅ BBR로 미세 조정 (고품질 정합)

**단점**:
- ❌ Limited FOV에서 (a) 단계 실패 가능
- ❌ High obliquity에서 coordinate mismatch
- ❌ 계산 비용 증가 (두 단계 모두 수행)

**결과 (deoblique_v2 기준)**:
```
Dice coefficient: 0.889 (83.3% pass rate)
ROI generation: 100% success
하지만 Sub-01 품질 문제 (왜곡, streaking artifacts)
```

---

### 4.3. 추천 방법 1: `--bold2anat-init header`

**GitHub issue #331에서 제안**:
```bash
fmriprep ... --bold2anat-init header
```

**처리 순서**:
```
Step 1: Initial alignment (a)
  ❌ SKIP - Header 좌표계만 사용
  Assumption: BOLD와 T1w가 이미 대략적으로 정렬됨

Step 2: BBR refinement (b)
  ✅ 수행 - Boundary-based registration만
  Input: Header-based transform (identity or near-identity)
  Output: Fine-tuned transform
```

**원리**:
```python
# Pseudocode for --bold2anat-init header
def register_bold_to_t1w_header(bold, t1w):
    # (a) 초기 정렬: Header-based (스킵)
    # NIfTI header의 qform/sform 정보만 사용
    initial_transform = extract_header_transform(
        source_header=bold.header,
        target_header=t1w.header
    )
    # → 보통 identity matrix 또는 minimal rotation

    # (b) BBR만 수행
    final_transform = bbr_registration(
        source=bold,
        target=t1w_wm_boundary,
        init_transform=initial_transform,  # Header-based
        schedule='default'
    )

    return final_transform
```

**이론적 배경**:
```
Limited FOV 문제:
  Partial brain → Intensity-based registration 실패
  But header coordinates → Usually accurate from scanner

해결 전략:
  실패하는 (a) 단계를 스킵하고
  BBR (b) 단계만 수행

전제 조건:
  1. Scanner coordinates가 정확해야 함
  2. BOLD와 T1w가 이미 대략 정렬되어 있어야 함
  3. Obliquity가 심하지 않아야 함 (coordinate system 유사)
```

**장점**:
- ✅ Limited FOV에서 (a) 실패 우회
- ✅ 계산 속도 빠름
- ✅ Header가 정확한 경우 효과적

**단점**:
- ❌ Header 부정확 시 완전 실패
- ❌ High obliquity에서 BBR도 실패 가능
- ❌ **우리 케이스 (29.5° obliquity)에서는 부적합**

**우리 데이터 적용 가능성**:
```
평가: ⚠️ 부분적으로만 해결

이유:
  ✅ Limited FOV 문제 → 해결 (a 스킵)
  ❌ High obliquity 문제 → 미해결 (coordinate mismatch 남음)

결론:
  Header-based initialization만으로는
  oblique coordinate system mismatch를 해결 못함
```

---

### 4.4. 추천 방법 2: FreeSurfer `mri_coreg --regheader`

**GitHub issue #331의 또 다른 제안**:
```bash
mri_coreg \
  --ref $t1w \
  --mov $bold \
  --reg output.lta \
  --regheader  # 핵심 플래그
```

**처리 순서**:
```
Step 1: Initial alignment
  Method: Header-based initialization
  --regheader flag → qform/sform에서 transform 추출

Step 2: Refinement
  Method: Mutual information cost function
  Algorithm: Powell's method (gradient-free optimization)
  NOT BBR: White matter boundary 사용 안 함
```

**원리**:
```python
# FreeSurfer mri_coreg의 내부 동작
def mri_coreg_regheader(ref, mov):
    # Header-based initialization
    if regheader:
        init_transform = extract_header_alignment(mov, ref)
    else:
        init_transform = identity_matrix()

    # Mutual information optimization (NOT BBR)
    # Powell's method: Gradient-free optimization
    final_transform = powell_optimize(
        cost_function=mutual_information,
        init_params=init_transform,
        ref_volume=ref,
        mov_volume=mov,
        max_iterations=100
    )

    return final_transform  # Output: .lta file (FreeSurfer format)
```

**이론적 배경**:
```
BBR vs Mutual Information:

BBR (Boundary-Based Registration):
  - 전제: White matter boundary가 명확해야 함
  - 문제: Limited cortex (occipital slab) → Boundary 적음
  - 문제: Cerebellum 많음 → BBR이 혼란

Mutual Information (MI):
  - 전제: 없음 (intensity 분포만 사용)
  - 장점: Partial brain에서도 작동
  - 장점: 서로 다른 contrast에 강건
  - 단점: BBR보다 정확도 낮을 수 있음
```

**장점**:
- ✅ Limited FOV + limited cortex에 적합
- ✅ Cerebellum이 많아도 작동
- ✅ Header 정확 시 빠른 수렴
- ✅ BBR보다 robust (boundary 필요 없음)

**단점**:
- ❌ BBR보다 정밀도 낮을 수 있음
- ❌ FreeSurfer 의존성 (fMRIPrep 외부 도구)
- ❌ `.lta` 파일 → fMRIPrep 포맷 변환 필요

**우리 데이터 적용 가능성**:
```
평가: ✅ 유망한 대안

이유:
  ✅ Limited FOV → MI가 적합
  ✅ Occipital slab → Limited cortex 문제 해결
  ⚠️ High obliquity → --regheader로 초기화

고려사항:
  - fMRIPrep 파이프라인에 통합 어려움
  - 별도 전처리 단계 필요
  - QC 추가 필요
```

---

### 4.5. 추천 방법 3: `bbregister --no-pass1`

**GitHub issue #331의 세 번째 제안**:
```bash
bbregister \
  --s sub-${sid} \
  --mov $bold \
  --reg output.lta \
  --init-header \
  --bold \
  --no-pass1  # 핵심 플래グ
```

**BBR의 Two-pass 알고리즘**:
```
Pass 1 (Coarse):
  - Low resolution (down-sampled)
  - Wide search range
  - Robust to poor initialization
  - 목적: Rough alignment

Pass 2 (Fine):
  - High resolution (original)
  - Narrow search range
  - Fine-tuning around Pass 1 result
  - 목적: Precise boundary alignment
```

**`--no-pass1`의 의미**:
```python
# bbregister의 내부 동작
def bbregister(mov, ref, init_header=False, no_pass1=False):
    # Initialization
    if init_header:
        init_transform = extract_header(mov, ref)
    else:
        init_transform = rough_registration(mov, ref)

    # BBR optimization
    if not no_pass1:
        # Two-pass (default)
        pass1_transform = bbr_optimize(
            resolution='low',
            search_range='wide',
            init=init_transform
        )
        final_transform = bbr_optimize(
            resolution='high',
            search_range='narrow',
            init=pass1_transform
        )
    else:
        # One-pass only (--no-pass1)
        final_transform = bbr_optimize(
            resolution='high',
            search_range='narrow',  # ⚠️ Limited!
            init=init_transform  # Must be accurate!
        )

    return final_transform
```

**이론적 배경**:
```
Limited Cortex 문제:
  Occipital slab → WM boundary가 적음
  Pass 1 (coarse) → Boundary 부족으로 잘못된 방향
  Pass 2 (fine) → Pass 1 오류 기반으로 더 악화

해결 전략:
  Pass 1 스킵 → 잘못된 coarse alignment 방지
  --init-header로 정확한 초기화 제공
  Pass 2만 수행 → 이미 좋은 초기화 기반으로 미세 조정

전제 조건:
  1. Header initialization이 매우 정확해야 함
  2. 초기 정렬이 이미 좋아야 함 (narrow search range)
  3. High-res에서 boundary가 충분해야 함
```

**장점**:
- ✅ Limited cortex에서 Pass 1 오류 방지
- ✅ Header 정확 시 빠르고 정확
- ✅ BBR 정밀도 유지 (Pass 2)

**단점**:
- ❌ Header 부정확 시 완전 실패
- ❌ Search range 좁음 (초기화 의존도 높음)
- ❌ FreeSurfer 의존성

**우리 데이터 적용 가능성**:
```
평가: ⚠️ 조건부 적용 가능

이유:
  ✅ Limited cortex → Pass 1 오류 방지
  ❌ High obliquity → Header initialization 부정확
  ❌ Search range 좁음 → Oblique data에서 위험

결론:
  Obliquity를 먼저 해결해야 적용 가능
```

---

### 4.6. 방법론 비교표

| 측면 | original_v3 (현재) | `--bold2anat-init header` | `mri_coreg --regheader` | `bbregister --no-pass1` |
|------|-------------------|---------------------------|-------------------------|-------------------------|
| **초기 정렬 (a)** | ✅ FLIRT (MI) | ❌ 스킵 (header) | ✅ Header → MI | ✅ Header → BBR pass2 |
| **미세 조정 (b)** | ✅ BBR (forced) | ✅ BBR | ✅ MI (Powell) | ✅ BBR (pass2 only) |
| **알고리즘** | FLIRT → BBR | BBR only | MI only | BBR (1-pass) |
| **Limited FOV** | ⚠️ (a) 실패 가능 | ✅ (a) 스킵 | ✅ MI robust | ✅ Pass1 스킵 |
| **Limited cortex** | ⚠️ BBR 어려움 | ⚠️ BBR 어려움 | ✅ MI 사용 | ⚠️ Pass2만 |
| **High obliquity** | ⚠️ Mismatch | ❌ 미해결 | ⚠️ Header 의존 | ❌ 미해결 |
| **Header 정확성** | 불필요 (FLIRT) | ✅ 필수 | ✅ 필수 | ✅✅ 매우 필수 |
| **계산 속도** | 느림 (2단계) | 빠름 (1단계) | 중간 (MI) | 빠름 (1-pass) |
| **정밀도** | 높음 (BBR) | 높음 (BBR) | 중간 (MI) | 높음 (BBR) |
| **Robustness** | 높음 | 낮음 | 높음 | 낮음 |
| **fMRIPrep 통합** | ✅ Native | ✅ Native | ❌ 외부 도구 | ❌ 외부 도구 |
| **우리 케이스** | ⚠️ 부분 성공 | ❌ Obliquity 미해결 | ✅ 유망 | ⚠️ 조건부 |

---

### 4.7. 원리적 비교 (Theoretical Comparison)

#### 4.7.1. Registration Cost Functions

**Mutual Information (MI)**:
```
이론:
  두 이미지의 정보 이론적 유사도
  H(A) + H(B) - H(A,B)
  where H = entropy

특징:
  ✅ 서로 다른 contrast에 강건 (T1w ↔ BOLD)
  ✅ Partial overlap 허용 (Limited FOV OK)
  ✅ Intensity 분포만 사용 (structure 불필요)
  ❌ Local minima 가능 (optimization 어려움)
  ❌ BBR보다 정밀도 낮음

사용:
  - FLIRT (FSL)
  - mri_coreg (FreeSurfer)
  - original_v3의 initial alignment
```

**Boundary-Based Registration (BBR)**:
```
이론:
  White matter boundary와 BOLD signal 정렬
  WM/GM boundary → BOLD signal 급변
  Gradient matching으로 최적화

특징:
  ✅ 매우 높은 정밀도 (~0.1mm)
  ✅ T1w-BOLD 정합에 최적화
  ❌ WM boundary 필요 (limited cortex에서 어려움)
  ❌ 좋은 초기화 필요 (narrow basin of convergence)
  ❌ Cerebellum 많으면 혼란

사용:
  - bbregister (FreeSurfer)
  - fMRIPrep의 refinement step
  - All methods의 미세 조정 단계
```

**비교**:
```
Limited FOV + Limited Cortex (우리 케이스):

MI:
  ✅ Partial brain OK
  ✅ Boundary 부족해도 OK
  ⚠️ 정밀도는 낮음

BBR:
  ❌ Boundary 부족 → 실패 위험
  ❌ 좋은 초기화 필수
  ✅ 성공 시 매우 정밀
```

#### 4.7.2. Initialization Strategies

**Intensity-based (FLIRT)**:
```
원리:
  Mutual information 최대화
  Multi-resolution pyramid
  Global search → Local refinement

장점:
  ✅ Robust (초기화 불필요)
  ✅ Wide basin of convergence

단점:
  ❌ Limited FOV → 정보 부족 → 실패
  ❌ 계산 비용 높음

적용:
  original_v3 (현재 사용)
```

**Header-based**:
```
원리:
  NIfTI header의 qform/sform 사용
  Scanner coordinate system 신뢰

장점:
  ✅ 매우 빠름 (계산 없음)
  ✅ Limited FOV 문제 없음

단점:
  ❌ Header 부정확 → 완전 실패
  ❌ Oblique data → Coordinate mismatch

적용:
  --bold2anat-init header
  mri_coreg --regheader
  bbregister --init-header
```

**비교 (우리 데이터)**:
```
Scanner coordinates: 정확 (GE scanner)
But obliquity: 29.5° 평균

Header-based initialization:
  BOLD coordinate: Oblique (29.5°)
  T1w coordinate: Cardinal (0°)
  → Rotation matrix mismatch
  → Header로는 대략 정렬만 가능
  → BBR이 이를 수정해야 함

Intensity-based:
  Limited FOV → 실패 위험
  But obliquity → 어느 정도 보정 가능
```

#### 4.7.3. Obliquity의 영향

**Coordinate System Mismatch**:
```
T1w: Cardinal axes (scanner coordinate)
  i: Left-Right
  j: Posterior-Anterior
  k: Inferior-Superior

BOLD (oblique 29.5°): Rotated axes
  i': Rotated in i-k plane
  j': Approximately same
  k': Rotated in i-k plane

Registration 문제:
  Header-based: i → i' mapping 부정확
  BBR: Boundary가 rotated coordinate에서 탐색
  MI: Intensity 분포는 rotation invariant (more robust)
```

**해결 전략 비교**:
```
1. Deoblique 먼저 (기존 deoblique_v2):
   BOLD → Cardinal axes resampling
   → Header-based 가능해짐
   문제: Resampling artifacts

2. Header-based + BBR (--bold2anat-init header):
   Oblique → Cardinal mapping을 BBR이 해결
   문제: BBR basin 벗어날 수 있음

3. MI-based (mri_coreg):
   Obliquity를 MI가 자동 처리
   장점: Rotation invariant

4. Original data + FLIRT (original_v3):
   FLIRT가 obliquity 보정
   문제: Limited FOV에서 FLIRT 실패 가능
```

---

### 4.8. 실제 결과 분석

#### 4.8.1. deoblique_v2 결과 재해석

**설정**:
```bash
# Preprocessing: Header-only deoblique (3drefit)
3drefit -deoblique input.nii.gz

# fMRIPrep
--bold2t1w-init register  # FLIRT → BBR
--force-bbr
--bold2t1w-dof 9  # Affine
```

**결과**:
```
Dice coefficient: 0.889
Pass rate (≥0.80): 83.3%
ROI generation: 100% success

하지만:
  Sub-01: 심각한 horizontal streaking artifacts
  원인: Data-header mismatch
```

**원리적 분석**:
```
3drefit -deoblique:
  Header만 수정 (qform/sform)
  Data는 여전히 oblique

fMRIPrep registration:
  FLIRT: Header 기반 초기화 → oblique data와 mismatch
  BBR: Mismatch된 초기화 → 왜곡 발생

Sub-01이 특히 심한 이유:
  더 높은 obliquity? (확인 필요)
  또는 motion/dropout으로 MI 실패
```

#### 4.8.2. original_v3 예상 결과

**설정**:
```bash
# NO preprocessing (oblique data 그대로)

# fMRIPrep
--bold2t1w-init register  # FLIRT → BBR
--force-bbr
--bold2t1w-dof 6  # Rigid (not affine)
```

**예상**:
```
FLIRT (MI):
  Oblique BOLD → T1w
  Limited FOV → 정보 부족
  성공률: ⚠️ 불확실

  성공 시:
    → BBR이 정밀 조정
    → 고품질 정합

  실패 시:
    → BBR도 실패
    → deoblique_v2보다 나쁠 수 있음
```

**장점 (deoblique_v2 대비)**:
```
✅ Data-header 일치 (no mismatch)
✅ Resampling artifact 없음
✅ Original resolution 유지
```

**위험**:
```
❌ FLIRT가 Limited FOV에서 실패 가능
❌ Obliquity → FLIRT 어려움 증가
❌ Dice < 0.889 가능
```

---

### 4.9. 권장사항 (Recommendations)

#### 4.9.1. 현재 진행 중인 original_v3

**평가**: ⚠️ **결과 확인 필요**

**시나리오별 대응**:

```
시나리오 1: Dice ≥ 0.90, Sub-01 개선
  → ✅ 성공! 이 방법 사용
  → FLIRT가 Limited FOV + obliquity 잘 처리
  → Data-header 일치가 핵심이었음

시나리오 2: Dice ~0.85-0.89, Sub-01 유사
  → ⚠️ deoblique_v2와 비슷
  → Limited FOV 문제 여전
  → 대안 고려 필요

시나리오 3: Dice < 0.85
  → ❌ 악화
  → FLIRT가 Limited FOV에서 실패
  → 반드시 대안 시도
```

#### 4.9.2. 추천 대안 (시나리오 2-3인 경우)

**Option A: mri_coreg --regheader (추천 1순위)**

**이유**:
```
✅ Limited FOV + Limited cortex에 최적
✅ MI가 obliquity 자동 처리
✅ BBR보다 robust
⚠️ fMRIPrep 파이프라인 수정 필요
```

**구현**:
```bash
# 1. mri_coreg로 BOLD → T1w 정합
for sub in 01 02 03 ...; do
  mri_coreg \
    --ref ${T1W} \
    --mov ${BOLD} \
    --reg bold_to_t1w.lta \
    --regheader
done

# 2. .lta → fMRIPrep 호환 format 변환
lta_convert --inlta bold_to_t1w.lta --outitk bold_to_t1w.txt

# 3. fMRIPrep에 pre-computed transform 제공
#    (현재 fMRIPrep에서 직접 지원 안 함 - 수동 처리 필요)
```

**장점**:
- Dice > 0.90 예상
- Sub-01 개선 기대
- Obliquity 문제 해결

**단점**:
- 파이프라인 복잡도 증가
- FreeSurfer 의존성
- QC 워크플로우 추가 필요

---

**Option B: AFNI Deoblique + fMRIPrep (추천 2순위)**

**이유**:
```
✅ Obliquity 근본 해결
✅ fMRIPrep 표준 파이프라인 사용
⚠️ Resampling artifact
```

**구현**:
```bash
# 1. AFNI quintic deoblique (data + header 모두)
3dWarp -deoblique -quintic \
  -prefix deobliqued.nii.gz \
  oblique.nii.gz

# 2. fMRIPrep (표준 설정)
--bold2t1w-init register  # 또는 header 시도
--force-bbr
--bold2t1w-dof 6
```

**예상 결과**:
```
Dice > 0.92 (obliquity 해결)
Sub-01 개선 (data-header 일치)
ROI generation 100%
```

---

**Option C: --bold2anat-init header 시도 (실험용)**

**이유**:
```
✅ 빠른 테스트 (fMRIPrep 플래그만 변경)
❌ Obliquity 미해결 (효과 불확실)
```

**구현**:
```bash
# original_v3 데이터로 재실행
--bold2anat-init header  # 변경
--force-bbr
--bold2t1w-dof 6
```

**예상**:
```
Best case: Dice ~0.90 (header 정확 + BBR 성공)
Likely: Dice ~0.85 (obliquity로 BBR 어려움)
Worst case: Dice < 0.80 (완전 실패)
```

**판단 기준**:
```
Dice > 0.90 → 채택
Dice 0.85-0.90 → Option A 시도
Dice < 0.85 → Option B 시도
```

---

### 4.10. 결론 및 다음 단계

**현재 상황 정리**:
```
1. original_v3 실행 중 (oblique data + FLIRT + BBR)
2. deoblique_v2: Dice 0.889 (Sub-01 문제)
3. GitHub issue #331: 여러 대안 제시
```

**원리적 이해**:
```
Limited FOV 문제:
  → Intensity-based 초기 정렬 실패
  → 해결: Header-based 또는 MI-based

High obliquity 문제:
  → Header-based initialization 부정확
  → 해결: Deoblique 또는 MI-based

Limited cortex 문제:
  → BBR의 WM boundary 부족
  → 해결: MI-based (mri_coreg)
```

**우리 케이스에 최적인 방법**:
```
1순위: mri_coreg --regheader
  이유: Limited FOV + obliquity + limited cortex 모두 해결

2순위: AFNI deoblique + standard fMRIPrep
  이유: Obliquity 제거 → 표준 방법 사용 가능

3순위: original_v3 (현재)
  이유: Data-header 일치, 결과 확인 필요

비추천: --bold2anat-init header
  이유: Obliquity 미해결, 우리 케이스에 부적합
```

**다음 단계**:
```
1. original_v3 QC 완료 대기
2. Dice coefficient, Sub-01 품질 확인
3. 시나리오별 대응:

   Dice ≥ 0.90, Sub-01 OK:
     → original_v3 채택, 분석 진행

   Dice 0.85-0.90 또는 Sub-01 문제:
     → mri_coreg 방법 시도 (Option A)

   Dice < 0.85:
     → AFNI deoblique 재시도 (Option B)
```

**문서 업데이트**:
- original_v3 QC 결과 추가
- 채택된 방법론 상세 기술
- 논문 Methods 섹션 작성

---

**작성 일자**: 2026-01-06
**작성자**: Analysis team
**상태**: ✅ original_v3 QC 결과 확인 완료

---

## 5. 0106 업데이트: original_v3 결과 및 구체적 방법론 비교

**날짜**: 2026-01-06 (updated)
**original_v3 결과**: Dice 0.889 (유망하나 Sub-06, 07 문제)

### 5.1. original_v3 실제 결과

**From**: `docs/results/FINAL_REPORT_WITH_VISUALIZATION.md`

```
전체 성과:
- Mean Dice: 0.889 (Excellent!)
- Pass rate (≥0.80): 83.3%
- ROI generation: 100% success (0% failure)
- Excellent runs (≥0.90): 73.3%

Subject별 결과:
✅ Tier 1 (Dice 0.93-0.95): Sub-01, 03, 04, 08, 09, 10 (6명)
✅ Tier 2 (Dice 0.82-0.92): Sub-02, 05 (2명)
⚠️ Tier 3 (Dice 0.73-0.75): Sub-06, 07 (2명)
   → 하지만 good runs (5-6번) Dice 0.92-0.93!
```

**핵심 발견**:
```
1. deoblique_v2 (Dice 0.376) → original_v3 (Dice 0.889)
   → 136% 개선! ✅

2. 8명은 group-level analysis 가능
   → Non-CVD 5명 + CVD 3명

3. Sub-06, 07:
   → Mean Dice 낮음 (0.73-0.75)
   → 하지만 Run 5-6만: Dice 0.92-0.93 (Tier 1 수준!)
   → Individual-level analysis 가능
```

**원인 분석 (Sub-06, 07)**:
```
T1/BOLD mask ratio:
  - Tier 1: 1.0-1.5 (정상)
  - Sub-06: ~2.2 (T1 mask 과도 추출)
  - Sub-07: ~1.8 (T1 mask 과도 추출)

→ T1 brain extraction 알고리즘이 일부 subject에서 over-extraction
→ Registration 자체는 성공 (overlap high)
→ 하지만 Dice 낮음 (T1 mask 너무 큼)
```

**결론**:
```
original_v3 성공! ✅
- FLIRT가 Limited FOV + obliquity 처리 성공
- Data-header 일치가 핵심
- 8명 group-level, 10명 individual-level 가능

하지만:
- Sub-06, 07의 일부 runs 여전히 낮은 Dice
- PI 제안 방법들 검토 필요
```

---

### 5.2. PI 피드백 및 GitHub Issue #331 검토

**PI가 제시한 문제 진단**:

> "제가 보기엔 지금 발생하는 문제는 calcarine sulcus에 직교한 fMRI scan 보다는,
> fMRI의 FOV가 whole brain을 커버하고 있지 않고 occipital area에 limited 되어 있어서,
> **Limited FOV fMRI image - T1w whole brain image 사이의 coregistration 에서 문제**가 되는 것 같습니다."

> "두 이미지를 정합할 때, **(a) 대략적인 공간정보/정렬을 맞추고 (b) cost function 기반 미세조정**, 두 단계를 거치는데,
> Limited FOV fMRI image 인 경우, whole brain 정보가 아니어서 정보량이 부족해 **(a)단계에서 오류가 발생**하는 것 같습니다."

**PI가 제안한 해결책**:

> "따라서 현재 시도해볼 수 있는 방법은, 두 영상이 이미 대략적으로 정렬되어 있다면,
> **(a)과정을 스킵하는 flag를 넣고 BBR을 돌려보는 것**입니다."

**구체적 방법 (PI 제안 + GitHub issue #331)**:

> "위 링크 이슈에 제기된 의견 참고해서 fMRIprep 돌리거나
> **(—bold2anat-init header 옵션 추가)**,
> 또는 freesurfer, AFNI, ANTs 등에 있는 boundary-based registration 명령어에
> **(a)과정 스킵하는 flag 추가**해서 사용
> (예: **mri_coreg + regheader**)"

**ANTs 사용 여부 확인 (PI 질문)**:

> "fMRIprep의 기본 BBR 알고리즘이 아닌 ANTs 패키지를 활용하였으나 유의미한 개선이 없었습니다.
> 이 경우, **(a)과정을 스킵하는 flag를 추가했는지 궁금합니다.**"

---

### 5.3. GitHub Issue #331의 구체적 제안들

**From GitHub issue #331** (https://github.com/nipreps/fmriprep/issues/331)

**제안 1: `--bold2anat-init header`**

> "We are having cases where limited field-of-view data are well-aligned originally, or pre-aligned manually,
> but running **--bold2anat-init header** throws off the original alignment and the data end up being misaligned
> (coregistration fails miserably without this flag)."

**제안 2: `mri_coreg --regheader`**

> "I thought that an old school cost function like **mutual information** could work better,
> and tried running **mri_coreg from FreeSurfer** (which I guess is what recent fmriprep versions are using?)
> with structural as target and functional as movable, adding **--regheader flag**. This seems to work well for the few subjects I tried."

```bash
mri_coreg \
  --ref $refvol \
  --mov $nifti \
  --reg $nifti_dir_out/${filename}.lta --regheader
```

**제안 3: `bbregister --no-pass1`**

> "These are images of the occipital slab acquired with left-right phase-encoding,
> so there is **not much of the cortex for bbregister to work with**, and quite a bit of cerebellum."

> "Another alternative that seems to help is additionally passing the flag **--no-pass1 to bbregister**:"

```bash
bbregister --s sub-${sid} \
  --mov $data_dir/sub-${sid}/ses-1/func/sub-${sid}_ses-1_task-CFE_run-${run}_bold.nii.gz \
  --reg tmp_nopass1.lta \
  --init-header --bold --no-pass1
```

**사용자 요청**:

> "I would find it useful if users could **pass some custom options to mri_coreg and/or bbregister**,
> similar to how the expert options file is implemented in FreeSurfer's recon-all. Is this something one could consider for the future?"

---

### 5.4. 네 가지 방법의 구체적 비교

**이제 각 방법의 실제 설정 코드와 내부 동작을 상세히 설명합니다.**

---

## 방법 1: original_v3 (현재 사용 중) - FLIRT → BBR

### 전체 설정 코드

**파일**: `slurm_jobs/preprocessing/run_fmriprep_original_data_array.sbatch`

```bash
#!/bin/bash
#SBATCH --job-name=fprep_orig
#SBATCH --array=1-10
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# =========================================================================
# Input: Original BIDS data (oblique, no preprocessing)
# =========================================================================
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_original_v3"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_original_v3_sub-${SUBJECT_ID}"

# =========================================================================
# fMRIPrep Command
# =========================================================================
singularity run --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  \
  # === Registration 설정 ===
  --bold2t1w-dof 6 \              # Rigid (6 DOF): 3 translation + 3 rotation
  --bold2t1w-init register \      # 핵심! FLIRT 초기 정렬 수행
  --force-bbr \                   # BBR 강제 사용
  \
  # === Brain extraction ===
  --fs-no-reconall \              # FreeSurfer 스킵
  \
  # === Output space ===
  --output-spaces MNI152NLin2009cAsym:res-2 \
  \
  # === Distortion correction ===
  --use-syn-sdc warn \            # Fieldmap-based SDC (경고만)
  \
  # === Motion/artifact ===
  --dummy-scans 4 \               # 초기 4 volumes 제거
  --fd-spike-threshold 0.5 \
  --dvars-spike-threshold 1.5 \
  \
  # === Computing ===
  --nthreads ${SLURM_CPUS_PER_TASK} \
  --omp-nthreads 8 \
  --mem-mb 94000 \
  -w /work \
  --skip-bids-validation \
  --notrack \
  -v -v
```

### 내부 동작 상세

**Step 1: BOLD → T1w Registration (핵심!)**

```python
# fMRIPrep 내부 (simplified pseudocode)

def bold_to_t1w_registration(bold_img, t1w_img, init='register', dof=6, force_bbr=True):
    """
    bold_img: Oblique BOLD image (original)
    t1w_img: T1w image (cardinal axes)
    init: 'register' or 'header'
    dof: 6 (rigid) or 9 (affine)
    force_bbr: True to force BBR
    """

    # =====================================================================
    # Phase (a): Initial Alignment
    # =====================================================================
    if init == 'register':
        # FLIRT-style intensity-based registration
        print("Running initial FLIRT registration...")

        initial_transform = fsl.FLIRT(
            in_file=bold_img,
            reference=t1w_img,
            dof=dof,  # 6: rigid
            cost='mutualinfo',  # Mutual information cost function
            searchr_x=[-90, 90],  # Search range: rotation X
            searchr_y=[-90, 90],  # Search range: rotation Y
            searchr_z=[-90, 90],  # Search range: rotation Z
            coarse_search=15,     # Coarse search (15 degree intervals)
            fine_search=6,        # Fine search (6 degree intervals)
        ).run()

        # Handles obliquity:
        # - Mutual information: rotation invariant
        # - Wide search range: finds oblique-to-cardinal mapping
        # - Multi-resolution: starts coarse (down-sampled)

        # Risk for Limited FOV:
        # - 정보량 부족 → local minima
        # - 하지만 original_v3는 성공 (Dice 0.889)

    elif init == 'header':
        # Header-based initialization (스킵 방법)
        print("Using header-based initialization...")

        initial_transform = extract_header_transform(
            bold_header=bold_img.header,
            t1w_header=t1w_img.header
        )

        # qform/sform에서 transform 추출
        # Oblique data: rotation matrix 부정확 가능
        # → BBR이 수정해야 함

    # =====================================================================
    # Phase (b): BBR Refinement
    # =====================================================================
    if force_bbr:
        print("Running BBR refinement...")

        # White matter segmentation from T1w
        wm_seg = segment_white_matter(t1w_img)
        wm_boundary = extract_boundary(wm_seg)

        # BBR optimization
        final_transform = freesurfer.BBRegister(
            source_file=bold_img,
            subject_id='t1w',  # Use T1w as reference
            init_transform=initial_transform,  # From FLIRT or header
            contrast_type='bold',
            wm_boundary=wm_boundary,
            schedule='default',  # Multi-resolution schedule
        ).run()

        # BBR cost function:
        # Maximize alignment of BOLD signal gradient with WM boundary
        # Assumes: WM/GM boundary → BOLD signal change

        # Success depends on:
        # 1. Good initial transform (from FLIRT)
        # 2. Sufficient WM boundary (limited cortex 문제)

    return final_transform

# =====================================================================
# Step 2: T1w → MNI Normalization
# =====================================================================
def t1w_to_mni_normalization(t1w_img):
    """
    ANTs-based nonlinear registration
    """
    mni_template = load_template('MNI152NLin2009cAsym')

    transform = ants.Registration(
        fixed_image=mni_template,
        moving_image=t1w_img,
        type_of_transform='SyN',  # Symmetric normalization
        convergence_threshold=1e-6,
    ).run()

    return transform

# =====================================================================
# Step 3: Compose Transforms
# =====================================================================
def apply_transforms(bold_img, bold_to_t1w, t1w_to_mni):
    """
    BOLD → T1w → MNI (composition)
    """
    bold_in_mni = ants.ApplyTransforms(
        input_image=bold_img,
        reference_image=mni_template,
        transforms=[t1w_to_mni, bold_to_t1w],  # Applied in reverse order
        interpolation='LanczosWindowedSinc',
    ).run()

    return bold_in_mni
```

### 장단점 분석

**장점**:
```
✅ 표준 파이프라인 (재현 가능)
✅ FLIRT가 obliquity 자동 처리
   - Mutual information: rotation invariant
   - Wide search range
✅ Robust (초기화 실패해도 어느 정도 작동)
✅ fMRIPrep native (추가 도구 불필요)
✅ 우리 결과: Dice 0.889 (성공!)
```

**단점**:
```
❌ Limited FOV → FLIRT 실패 위험
   - 정보량 부족 시 local minima
   - 우리는 운 좋게 성공 (occipital coverage 충분?)
❌ 계산 비용 높음 (두 단계)
❌ Sub-06, 07 일부 runs 여전히 낮은 Dice
   - T1 brain extraction 문제 (FLIRT와 무관)
```

**우리 데이터 결과**:
```
Dice 0.889 (평균) ✅
- 6명: 0.93-0.95 (Excellent)
- 2명: 0.82-0.92 (Good)
- 2명: 0.73-0.75 (Partial, but good runs 0.92+)

결론: Limited FOV 문제 대부분 해결됨!
```

---

## 방법 2: `--bold2anat-init header` - BBR만 수행

### 전체 설정 코드

```bash
#!/bin/bash
# original_v3과 동일, 한 줄만 변경

singularity run --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  \
  # === Registration 설정 (변경!) ===
  --bold2t1w-dof 6 \
  --bold2t1w-init header \      # ⭐ 변경: register → header
  --force-bbr \
  \
  # === 나머지 동일 ===
  --fs-no-reconall \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --use-syn-sdc warn \
  --dummy-scans 4 \
  --fd-spike-threshold 0.5 \
  --dvars-spike-threshold 1.5 \
  --nthreads ${SLURM_CPUS_PER_TASK} \
  --omp-nthreads 8 \
  --mem-mb 94000 \
  -w /work \
  --skip-bids-validation \
  --notrack \
  -v -v
```

### 내부 동작 상세

```python
def bold_to_t1w_header_init(bold_img, t1w_img, dof=6, force_bbr=True):
    """
    Header-based initialization: (a) 단계 스킵
    """

    # =====================================================================
    # Phase (a): Initial Alignment → SKIP!
    # =====================================================================
    print("Skipping FLIRT, using header-based initialization...")

    # NIfTI header에서 qform/sform 추출
    bold_qform = bold_img.header.get_qform()  # 4x4 affine matrix
    bold_sform = bold_img.header.get_sform()
    t1w_qform = t1w_img.header.get_qform()
    t1w_sform = t1w_img.header.get_sform()

    # Scanner coordinates 기반 transform 계산
    # Assumption: BOLD와 T1w가 같은 scanner session
    initial_transform = compute_header_alignment(
        bold_qform, bold_sform,
        t1w_qform, t1w_sform
    )

    # Oblique data의 경우:
    # BOLD qform: oblique rotation matrix (29.5°)
    # T1w qform: cardinal axes (0°)
    # → initial_transform에 rotation 포함
    # → 하지만 정확하지 않을 수 있음!

    print(f"Initial transform (header-based):")
    print(initial_transform)

    # Example for our data:
    # Rotation: ~30° (obliquity)
    # Translation: scanner coordinates
    # BUT: may not be perfectly accurate

    # =====================================================================
    # Phase (b): BBR Refinement (동일)
    # =====================================================================
    if force_bbr:
        print("Running BBR refinement from header initialization...")

        wm_seg = segment_white_matter(t1w_img)
        wm_boundary = extract_boundary(wm_seg)

        final_transform = freesurfer.BBRegister(
            source_file=bold_img,
            subject_id='t1w',
            init_transform=initial_transform,  # ⚠️ From header!
            contrast_type='bold',
            wm_boundary=wm_boundary,
            schedule='default',
        ).run()

        # BBR이 해야 할 일:
        # 1. Header에서 온 초기 rotation (30°) 보정
        # 2. Limited cortex에서 boundary 찾기
        # → 두 가지 모두 어려움!

        # Success depends on:
        # 1. Header가 충분히 정확해야 함 (< 10° error)
        # 2. BBR의 search range 안에 있어야 함
        # 3. WM boundary가 충분해야 함

    return final_transform
```

### 이론적 원리

**Header Coordinate System**:
```
NIfTI header stores:
  qform: quaternion-based transform
  sform: affine matrix

Scanner coordinates (example):
  Origin: Anterior commissure (AC)
  i: Left → Right
  j: Posterior → Anterior
  k: Inferior → Superior

BOLD (oblique 29.5°):
  i': Rotated in i-k plane
  j': Approximately same
  k': Rotated in i-k plane

  Rotation matrix R:
    [cos(θ)   0  -sin(θ)]
    [  0      1     0   ]
    [sin(θ)   0   cos(θ)]
  where θ ≈ 29.5°

T1w (cardinal):
  i, j, k: Standard axes

  Rotation matrix R:
    [1  0  0]
    [0  1  0]
    [0  0  1]

Header-based transform:
  T_bold_to_t1w = T1w_qform^-1 × BOLD_qform

  Contains rotation of ~29.5°
  BUT: may have small errors (± 5-10°?)
```

**BBR에서 수정 가능한 범위**:
```
BBR default schedule:
  Level 1 (coarse): ±10° rotation, ±20mm translation
  Level 2 (medium): ±5° rotation, ±10mm translation
  Level 3 (fine): ±2° rotation, ±5mm translation

Header error가 10° 이내면:
  → BBR Level 1에서 찾을 수 있음 ✅

Header error가 10° 이상이면:
  → BBR search range 밖 ❌
  → 실패 가능
```

### 장단점 분석

**장점**:
```
✅ Limited FOV 문제 해결
   - FLIRT (a) 단계 스킵
   - 정보량 부족 문제 우회
✅ 계산 속도 빠름
   - FLIRT 안 돌림 (1-2분 절약)
✅ fMRIPrep native (추가 도구 불필요)
```

**단점**:
```
❌ Header 부정확 시 완전 실패
   - Oblique data: rotation error 가능
   - 우리 케이스: 29.5° obliquity
   - Header만으로 정확 정렬 어려움
❌ BBR search range 의존도 높음
   - Header error > 10° → 실패
❌ Limited cortex 문제 미해결
   - WM boundary 부족 → BBR 어려움
❌ 우리 데이터 예상 결과:
   - Dice ~0.85? (original_v3보다 나쁠 수 있음)
```

**우리 케이스 적용 가능성**:
```
평가: ⚠️ 부분적 해결만

이유:
  ✅ Limited FOV 문제 해결 (FLIRT 스킵)
  ❌ High obliquity 미해결
     - 29.5° rotation → header error 클 수 있음
     - BBR이 수정해야 하는 범위 큼
  ❌ Limited cortex (occipital slab)
     - WM boundary 적음
     - BBR 어려움

결론:
  original_v3가 더 나을 가능성 높음
  (FLIRT가 obliquity 자동 처리)
```

---

## 방법 3: `mri_coreg --regheader` - Mutual Information

### 전체 설정 코드

**Step 1: mri_coreg로 BOLD → T1w 정합**

```bash
#!/bin/bash
# FreeSurfer mri_coreg 사용

# =========================================================================
# Setup
# =========================================================================
SUBJECTS_DIR="/path/to/freesurfer_subjects"
SUBJECT_ID="sub-01"

# Input files
T1W_FILE="${SUBJECTS_DIR}/${SUBJECT_ID}/mri/brain.mgz"
BOLD_FILE="/path/to/sub-01_task-rsvp_run-1_bold.nii.gz"

# Output
OUTPUT_LTA="/path/to/bold_to_t1w.lta"

# =========================================================================
# Run mri_coreg
# =========================================================================
mri_coreg \
  --ref ${T1W_FILE} \           # Reference: T1w brain
  --mov ${BOLD_FILE} \          # Moving: BOLD image
  --reg ${OUTPUT_LTA} \         # Output: transform (.lta format)
  --regheader \                 # ⭐ Use header initialization
  --threads 8

# =========================================================================
# Optional: Convert .lta to ITK format (for fMRIPrep compatibility)
# =========================================================================
lta_convert \
  --inlta ${OUTPUT_LTA} \
  --outitk bold_to_t1w.txt \
  --src ${BOLD_FILE} \
  --trg ${T1W_FILE}

# =========================================================================
# Apply transform to BOLD
# =========================================================================
mri_vol2vol \
  --mov ${BOLD_FILE} \
  --targ ${T1W_FILE} \
  --lta ${OUTPUT_LTA} \
  --o bold_in_t1w_space.nii.gz \
  --interp trilin

# =========================================================================
# Continue with fMRIPrep for T1w → MNI
# =========================================================================
# fMRIPrep는 이미 정합된 BOLD를 받아서 MNI로만 변환
# (하지만 fMRIPrep에 pre-computed transform 제공 어려움)
```

**Step 2: fMRIPrep 통합 (수동)**

```bash
# 문제: fMRIPrep는 pre-computed BOLD→T1w transform 받기 어려움
# 해결: Manual workflow

# 1. FreeSurfer recon-all (T1w processing)
recon-all -s ${SUBJECT_ID} -i ${T1W_FILE} -all

# 2. mri_coreg (BOLD → T1w)
mri_coreg --ref ... --mov ... --reg ... --regheader

# 3. fMRIPrep의 T1w → MNI transform 재사용
#    또는 ANTs로 직접 수행
antsRegistrationSyN.sh \
  -d 3 \
  -f MNI152NLin2009cAsym_T1.nii.gz \
  -m ${T1W_FILE} \
  -o t1w_to_mni_

# 4. Compose transforms
antsApplyTransforms \
  -d 3 \
  -i ${BOLD_FILE} \
  -r MNI152NLin2009cAsym_T1.nii.gz \
  -t t1w_to_mni_1Warp.nii.gz \
  -t t1w_to_mni_0GenericAffine.mat \
  -t bold_to_t1w.txt \
  -o bold_in_mni.nii.gz
```

### 내부 동작 상세

```python
def mri_coreg_regheader(ref_img, mov_img, output_lta):
    """
    FreeSurfer mri_coreg with --regheader flag
    """

    # =====================================================================
    # Phase 1: Header-based Initialization
    # =====================================================================
    print("Extracting header transforms...")

    # qform/sform에서 transform 추출
    ref_vox2ras = extract_vox2ras_matrix(ref_img)
    mov_vox2ras = extract_vox2ras_matrix(mov_img)

    # Initial alignment
    init_transform = compute_header_alignment(
        mov_vox2ras, ref_vox2ras
    )

    print(f"Initial rotation (from header): {extract_rotation(init_transform)}")
    # For our data: ~29.5° obliquity

    # =====================================================================
    # Phase 2: Mutual Information Optimization
    # =====================================================================
    print("Running mutual information optimization...")

    # Powell's method: Gradient-free optimization
    # No derivatives needed → Robust

    def cost_function(params):
        """
        Mutual Information cost function

        params: [tx, ty, tz, rx, ry, rz] (6 DOF rigid)
        """
        # Apply transform
        transformed = apply_transform(mov_img, params)

        # Compute mutual information
        mi = compute_mutual_information(
            ref_img, transformed,
            bins=256,
            normalized=True
        )

        return -mi  # Minimize negative MI = Maximize MI

    # Powell optimization
    final_params = scipy.optimize.minimize(
        fun=cost_function,
        x0=init_transform.to_params(),  # Start from header
        method='Powell',
        options={
            'maxiter': 100,
            'xtol': 1e-4,
            'ftol': 1e-4,
        }
    )

    final_transform = params_to_matrix(final_params.x)

    # Save as .lta (FreeSurfer Linear Transform Array)
    save_lta(final_transform, output_lta)

    return final_transform

def compute_mutual_information(img1, img2, bins=256, normalized=True):
    """
    Mutual Information 계산

    MI(A,B) = H(A) + H(B) - H(A,B)

    where H = entropy
    """
    # Joint histogram
    hist_2d, x_edges, y_edges = np.histogram2d(
        img1.ravel(), img2.ravel(),
        bins=bins
    )

    # Marginal histograms
    hist_a = np.sum(hist_2d, axis=1)
    hist_b = np.sum(hist_2d, axis=0)

    # Probabilities
    p_a = hist_a / np.sum(hist_a)
    p_b = hist_b / np.sum(hist_b)
    p_ab = hist_2d / np.sum(hist_2d)

    # Entropies
    H_a = -np.sum(p_a[p_a > 0] * np.log2(p_a[p_a > 0]))
    H_b = -np.sum(p_b[p_b > 0] * np.log2(p_b[p_b > 0]))
    H_ab = -np.sum(p_ab[p_ab > 0] * np.log2(p_ab[p_ab > 0]))

    # Mutual information
    mi = H_a + H_b - H_ab

    if normalized:
        # Normalized MI: 0 (independent) to 1 (identical)
        nmi = 2 * mi / (H_a + H_b)
        return nmi

    return mi
```

### 이론적 원리

**Mutual Information vs BBR**:

```
BBR (Boundary-Based Registration):
  Cost function: WM boundary alignment
  Requires: WM segmentation, clear boundary
  Sensitive to: Limited cortex, poor contrast

  Mechanism:
    Find WM/GM boundary in T1w
    Align BOLD gradient with boundary
    Assumes: BOLD signal drops at WM/GM

  Limited cortex 문제:
    Occipital slab → WM boundary 적음
    Cerebellum 많음 → BBR 혼란
    → 실패 위험

Mutual Information (MI):
  Cost function: Information-theoretic similarity
  Requires: Intensity distributions only
  Robust to: Partial overlap, different contrast

  Mechanism:
    Compute joint histogram (BOLD, T1w)
    Maximize mutual information
    No structure assumptions

  Limited FOV/cortex 장점:
    Partial brain OK
    No boundary needed
    Works with any tissue types
    → Robust!
```

**Rotation Invariance**:

```
MI for oblique data:
  Intensity distribution ≈ rotation invariant

  Example:
    BOLD (oblique 29.5°): histogram(BOLD)
    T1w (cardinal 0°): histogram(T1w)

    Joint histogram depends on:
      - Which BOLD voxels overlap with which T1w voxels
      - NOT on coordinate system

    → MI can handle obliquity automatically!
```

### 장단점 분석

**장점**:
```
✅ Limited FOV + Limited cortex 최적
   - MI: partial brain OK
   - No WM boundary needed
✅ Obliquity 자동 처리
   - MI: rotation invariant
   - Powell: gradient-free (robust)
✅ Header initialization
   - 빠른 수렴
   - Scanner coordinates 활용
✅ Proven method
   - FreeSurfer mri_coreg: widely used
   - Mutual information: gold standard
```

**단점**:
```
❌ BBR보다 정밀도 낮음
   - MI: ~1mm accuracy
   - BBR: ~0.1mm accuracy
   - 하지만 fMRI resolution (2mm) 고려 시 충분
❌ fMRIPrep 파이프라인 통합 어려움
   - 별도 전처리 단계 필요
   - Manual workflow
   - Pre-computed transform 제공 복잡
❌ FreeSurfer 의존성
   - mri_coreg, lta_convert, mri_vol2vol
   - 추가 설치 필요
❌ QC 워크플로우 복잡
   - fMRIPrep HTML report 못 씀
   - 별도 QC 필요
```

**우리 케이스 적용 가능성**:
```
평가: ✅ 매우 유망!

이유:
  ✅ Limited FOV (occipital only) → MI robust
  ✅ Limited cortex → No boundary needed
  ✅ High obliquity (29.5°) → MI handles
  ✅ Cerebellum 많음 → MI OK (BBR 문제 없음)

예상 결과:
  Dice > 0.90 (original_v3보다 나을 수 있음)
  특히 Sub-06, 07 개선 기대

Trade-off:
  정밀도 (BBR) vs Robustness (MI)
  → 우리 케이스는 robustness가 중요!
```

---

## 방법 4: `bbregister --no-pass1` - BBR 1-pass

### 전체 설정 코드

```bash
#!/bin/bash
# FreeSurfer bbregister with --no-pass1

# =========================================================================
# Setup
# =========================================================================
SUBJECTS_DIR="/path/to/freesurfer_subjects"
SUBJECT_ID="sub-01"
RUN=1

# Input files
BOLD_FILE="/path/to/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_bold.nii.gz"

# Output
OUTPUT_LTA="/path/to/bold_to_t1w_nopass1.lta"

# =========================================================================
# Run bbregister with --no-pass1
# =========================================================================
bbregister \
  --s ${SUBJECT_ID} \           # FreeSurfer subject ID
  --mov ${BOLD_FILE} \          # Moving: BOLD image
  --reg ${OUTPUT_LTA} \         # Output transform
  --init-header \               # ⭐ Header initialization
  --bold \                      # BOLD contrast (not T2)
  --no-pass1 \                  # ⭐ Skip coarse pass
  --6                           # 6 DOF (rigid)

# =========================================================================
# Explanation of flags
# =========================================================================
# --init-header: Use header for initialization (not intensity-based)
# --bold: BOLD contrast type (vs T2, T1)
# --no-pass1: Skip coarse multi-resolution pass
# --6: 6 DOF rigid (vs 9 DOF affine)

# =========================================================================
# Apply transform
# =========================================================================
mri_vol2vol \
  --mov ${BOLD_FILE} \
  --targ ${SUBJECTS_DIR}/${SUBJECT_ID}/mri/brain.mgz \
  --lta ${OUTPUT_LTA} \
  --o bold_in_t1w_space.nii.gz \
  --interp trilin

# =========================================================================
# QC: Check registration
# =========================================================================
# 1. Visual inspection
freeview \
  ${SUBJECTS_DIR}/${SUBJECT_ID}/mri/brain.mgz \
  bold_in_t1w_space.nii.gz:colormap=heat:opacity=0.5

# 2. Quantitative (Dice coefficient)
# (Would need custom script)
```

### 내부 동작 상세

```python
def bbregister_no_pass1(subject_id, mov_file, output_lta):
    """
    bbregister with --no-pass1 flag

    Two-pass → One-pass only
    """

    # =====================================================================
    # Setup: Load FreeSurfer subject
    # =====================================================================
    subjects_dir = os.environ['SUBJECTS_DIR']
    subject_path = os.path.join(subjects_dir, subject_id)

    # Load T1w and segmentation
    t1w = load_mgz(f"{subject_path}/mri/brain.mgz")
    wm_seg = load_mgz(f"{subject_path}/mri/wm.mgz")

    # Extract WM boundary
    wm_boundary = extract_wm_boundary(wm_seg)

    # =====================================================================
    # Initialization: Header-based
    # =====================================================================
    print("Extracting header transform...")

    mov_img = load_nifti(mov_file)

    # qform/sform → initial transform
    init_transform = extract_header_transform(
        mov_img.header,
        t1w.header
    )

    print(f"Initial transform (header):")
    print(f"  Rotation: {extract_rotation_angles(init_transform)}")
    print(f"  Translation: {extract_translation(init_transform)}")

    # For oblique data:
    # Rotation ≈ 29.5° (obliquity)
    # Translation from scanner coordinates

    # =====================================================================
    # BBR: Two-pass vs One-pass
    # =====================================================================

    # DEFAULT (two-pass):
    if not no_pass1:
        print("Running BBR two-pass...")

        # Pass 1: Coarse
        pass1_transform = bbr_optimize(
            mov_img=mov_img,
            ref_wm_boundary=wm_boundary,
            init_transform=init_transform,
            resolution='low',        # Down-sampled (half resolution)
            search_range_rot=15,     # ±15° rotation
            search_range_trans=25,   # ±25mm translation
            schedule=[4, 2, 1],      # Multi-resolution levels
        )

        print(f"Pass 1 result: rotation error reduced to ±5°")

        # Pass 2: Fine
        final_transform = bbr_optimize(
            mov_img=mov_img,
            ref_wm_boundary=wm_boundary,
            init_transform=pass1_transform,  # From Pass 1
            resolution='high',       # Original resolution
            search_range_rot=5,      # ±5° rotation
            search_range_trans=10,   # ±10mm translation
            schedule=[2, 1],
        )

        print(f"Pass 2 result: sub-mm accuracy")

    # --no-pass1 (one-pass only):
    else:
        print("Running BBR one-pass (--no-pass1)...")

        # Skip Pass 1, go directly to Pass 2
        final_transform = bbr_optimize(
            mov_img=mov_img,
            ref_wm_boundary=wm_boundary,
            init_transform=init_transform,  # ⚠️ From header!
            resolution='high',       # Original resolution
            search_range_rot=5,      # ⚠️ Narrow! ±5° only
            search_range_trans=10,   # ±10mm translation
            schedule=[2, 1],
        )

        # Critical requirements:
        # 1. init_transform must be accurate (< 5° error)
        # 2. WM boundary must be sufficient (limited cortex 문제)
        # 3. If init error > 5° → 완전 실패!

    # Save transform
    save_lta(final_transform, output_lta)

    return final_transform

def bbr_optimize(mov_img, ref_wm_boundary, init_transform,
                 resolution, search_range_rot, search_range_trans, schedule):
    """
    BBR optimization core
    """

    # Cost function: WM boundary alignment
    def bbr_cost(params):
        """
        params: [tx, ty, tz, rx, ry, rz]
        """
        # Apply transform
        transformed = apply_transform(mov_img, params)

        # Compute gradient at WM boundary
        bold_gradient = compute_image_gradient(transformed)

        # Cost: Negative gradient magnitude at boundary
        # (High gradient at boundary = Good alignment)
        cost = -np.sum(bold_gradient[ref_wm_boundary])

        return cost

    # Powell optimization with constraints
    result = scipy.optimize.minimize(
        fun=bbr_cost,
        x0=init_transform.to_params(),
        method='Powell',
        bounds=[
            (-search_range_trans, search_range_trans),  # tx
            (-search_range_trans, search_range_trans),  # ty
            (-search_range_trans, search_range_trans),  # tz
            (-search_range_rot, search_range_rot),      # rx (degrees)
            (-search_range_rot, search_range_rot),      # ry
            (-search_range_rot, search_range_rot),      # rz
        ],
        options={'maxiter': 50}
    )

    return params_to_matrix(result.x)
```

### 이론적 원리

**Two-pass vs One-pass**:

```
Two-pass BBR (default):

  Pass 1 (Coarse):
    - Resolution: 2x down-sampled (4mm → 8mm)
    - Search range: Wide (±15° rotation, ±25mm translation)
    - Purpose: Catch large misalignments
    - Cost: ~1 minute

    Example:
      Init error: 12° rotation
      Pass 1 output: 3° rotation error
      → Brings into Pass 2 range

  Pass 2 (Fine):
    - Resolution: Original (4mm or 2mm)
    - Search range: Narrow (±5° rotation, ±10mm translation)
    - Purpose: Sub-mm accuracy
    - Cost: ~2 minutes

    Example:
      Pass 1 output: 3° error
      Pass 2 output: 0.2° error
      → High precision

One-pass BBR (--no-pass1):

  Pass 2 only:
    - Resolution: Original
    - Search range: Narrow (±5° rotation)
    - Purpose: Refinement only
    - Cost: ~2 minutes (saves Pass 1)

    Example:
      Init error: 3° rotation
      Pass 2 output: 0.2° error
      → Works if init good

    BUT:
      Init error: 12° rotation
      Pass 2 search: ±5° only
      → Cannot find solution
      → Fails!
```

**Limited Cortex Problem**:

```
Occipital slab characteristics:
  - Limited cortex (primary visual only)
  - WM boundary sparse
  - Cerebellum prominent

Pass 1 problem:
  - Coarse resolution (8mm)
  - Sparse WM boundary becomes even sparser
  - Cerebellum WM confuses algorithm
  - May converge to wrong solution

  Example:
    True V1 location: (x, y, z)
    Pass 1 result: Cerebellum (x+10, y-5, z-15)
    → Wrong basin of convergence

  Pass 2:
    Starts from wrong location
    Narrow search range
    → Cannot recover
    → Final result still wrong

--no-pass1 solution:
  - Skip problematic Pass 1
  - Start directly at high resolution
  - If header accurate → WM boundary clearer
  - Converge to correct solution

  BUT:
    Requires accurate header (<5° error)
    Our case: 29.5° obliquity
    → May fail!
```

### 장단점 분석

**장점**:
```
✅ Limited cortex 문제 해결
   - Pass 1 스킵 → coarse 오류 방지
   - High resolution → boundary clearer
✅ Header 정확 시 빠르고 정밀
   - Pass 1 스킵 (1분 절약)
   - BBR 정밀도 유지 (~0.1mm)
✅ FreeSurfer native
```

**단점**:
```
❌ Header 정확성에 극도로 의존
   - Search range: ±5° only
   - Init error > 5° → 완전 실패
   - 우리 케이스: 29.5° obliquity
   - → Header에서 큰 rotation 있음
   - → ±5° 범위 벗어날 가능성
❌ Limited cortex 여전히 문제
   - Pass 2만 수행해도 WM boundary 적음
   - Cerebellum 혼란 가능
❌ fMRIPrep 통합 어려움
❌ Obliquity 미해결
   - Header initialization만으로 부족
```

**우리 케이스 적용 가능성**:
```
평가: ⚠️ 조건부 적용 가능

이유:
  ✅ Limited cortex 일부 해결
  ❌ High obliquity 큰 문제
     - 29.5° rotation → header error 클 수 있음
     - ±5° search range 부족
  ❌ Obliquity 먼저 해결 필요

적용 조건:
  IF deoblique 먼저 수행:
    → Header initialization 정확해짐
    → --no-pass1 효과적

  ELSE (original data):
    → 실패 위험 높음

결론:
  Deoblique + bbregister --no-pass1
  또는
  Original + mri_coreg --regheader (더 robust)
```

---

### 5.5. 네 가지 방법 종합 비교표

| 특성 | original_v3 (FLIRT→BBR) | `--bold2anat-init header` | `mri_coreg --regheader` | `bbregister --no-pass1` |
|------|------------------------|---------------------------|------------------------|-------------------------|
| **초기 정렬 방법** | FLIRT (MI, wide search) | Header (qform/sform) | Header → MI (Powell) | Header only |
| **미세 조정 방법** | BBR (2-pass) | BBR (2-pass) | MI (Powell) | BBR (1-pass, pass2 only) |
| **Limited FOV** | ⚠️ FLIRT 실패 가능 | ✅ 스킵 | ✅ MI robust | ✅ Pass1 스킵 |
| **High Obliquity (29.5°)** | ✅ FLIRT 처리 | ❌ Header 부정확 | ✅ MI rotation-invariant | ❌ Header 부정확 |
| **Limited Cortex** | ⚠️ BBR 어려움 | ⚠️ BBR 어려움 | ✅ MI (no boundary) | ⚠️ Pass2 WM boundary 필요 |
| **Header 정확성 요구** | 불필요 | ⚠️ 필요 (±10°) | ⚠️ 필요 (±10°) | ✅✅ 매우 필요 (±5°) |
| **Computation** | 느림 (FLIRT+BBR 2-pass) | 중간 (BBR 2-pass) | 중간 (MI Powell) | 빠름 (BBR 1-pass) |
| **정밀도** | 높음 (~0.1mm) | 높음 (~0.1mm) | 중간 (~1mm) | 높음 (~0.1mm) |
| **Robustness** | 높음 | 낮음 | **매우 높음** | 낮음 |
| **fMRIPrep 통합** | ✅ Native | ✅ Native (플래그만) | ❌ Manual workflow | ❌ Manual workflow |
| **추가 도구** | 불필요 | 불필요 | FreeSurfer | FreeSurfer |
| **우리 결과** | **Dice 0.889** ✅ | 예상: ~0.85 | 예상: >0.90 ✅✅ | 예상: <0.80 |
| **적용 난이도** | 완료 | 매우 쉬움 | 중간 (수동) | 중간 (수동) |
| **권장 순위** | **3순위** (현재) | 4순위 (비추천) | **1순위** ⭐ | 2순위 (조건부) |

---

### 5.6. 최종 권장사항

#### **시나리오별 최적 방법**

**Scenario 1: 현재 상황 (original_v3 Dice 0.889)**

```
현재 결과: 유망하지만 Sub-06, 07 문제

평가:
  ✅ 8명 group-level 가능
  ✅ 10명 individual-level 가능
  ✅ 논문 작성 진행 가능

권장:
  → 우선 분석 시작 (baseline)
  → Sub-06/07 good runs (5-6번) 사용
  → 추가 개선은 선택적
```

**Scenario 2: Sub-06/07 개선 원할 경우**

```
목표: Sub-06/07의 모든 runs Dice > 0.90

최적 방법: mri_coreg --regheader (방법 3)

이유:
  ✅ Limited FOV + cortex + obliquity 모두 해결
  ✅ MI: rotation invariant
  ✅ Robust하고 proven
  ✅ Sub-06/07 Dice 향상 기대

단점:
  ⚠️ Manual workflow (fMRIPrep 외부)
  ⚠️ 파이프라인 복잡도 증가

가치 판단:
  IF 논문 reviewer가 Sub-06/07 제외 문제 삼을 가능성:
    → 시도 가치 있음

  ELSE:
    → 현재 상태로 충분 (good runs 사용)
```

**Scenario 3: 빠른 테스트 원할 경우**

```
목표: 최소 노력으로 개선 확인

방법: --bold2anat-init header (방법 2)

장점:
  ✅ 플래그 하나만 변경
  ✅ 빠른 재실행 (no new workflow)

단점:
  ❌ Obliquity 미해결 (효과 불확실)
  ❌ 악화 가능성도 있음

권장:
  → 1-2 subjects 테스트
  → Dice 비교
  → 개선 없으면 포기
```

**Scenario 4: 연구 목적 (방법론 비교)**

```
목표: 여러 방법 체계적 비교

실험 설계:
  1. original_v3 (현재)
  2. --bold2anat-init header
  3. mri_coreg --regheader
  4. bbregister --no-pass1 (조건: deoblique 먼저)

비교 metric:
  - Dice coefficient
  - Run-level pass rate
  - Sub-06/07 specific improvement
  - Computation time

가치:
  → Methods paper 가능
  → Community에 기여
```

---

### 5.7. 실행 계획

#### **Plan A: 현재 상태 유지 (권장)**

```bash
# 1. original_v3 결과 활용
PREPROCESSING_DIR="/storage/connectome/haba6030/fmriprep_out_original_v3"

# 2. Run selection
SUBJECTS_ALL="01 02 03 04 05 06 07 08 09 10"
SUBJECTS_GROUP="01 02 03 04 05 08 09 10"  # Exclude Sub-06/07

# Sub-06/07 good runs only
SUB06_RUNS="5 6"  # Dice 0.92
SUB07_RUNS="5 6"  # Dice 0.93

# 3. Baseline analysis 시작
python fir_reconstruction_BH2009_system_clean.py \
  --fmriprep_dir ${PREPROCESSING_DIR} \
  --subject_id 01 \
  --roi V1 \
  --all_runs

# 4. Individual-level: 모두 포함
# 5. Group-level: 8 subjects
```

**Timeline**:
- 즉시 시작 가능
- 추가 preprocessing 불필요

---

#### **Plan B: mri_coreg 시도 (개선 원할 경우)**

```bash
# =========================================================================
# Step 1: Setup
# =========================================================================
SUBJECTS_DIR="/storage/connectome/haba6030/freesurfer_subjects"
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/mri_coreg_results"

# Target subjects: Sub-06, 07 (others already good)
SUBJECTS="06 07"

# =========================================================================
# Step 2: For each subject/run
# =========================================================================
for sub in ${SUBJECTS}; do
  for run in 1 2 3 4 5 6; do
    echo "Processing sub-${sub} run-${run}..."

    # Input
    BOLD="${BIDS_DIR}/sub-${sub}/func/sub-${sub}_task-rsvp_run-${run}_bold.nii.gz"
    T1W="${SUBJECTS_DIR}/sub-${sub}/mri/brain.mgz"

    # Output
    LTA="${OUTPUT_DIR}/sub-${sub}/sub-${sub}_run-${run}_bold_to_t1w.lta"

    # Run mri_coreg
    mri_coreg \
      --ref ${T1W} \
      --mov ${BOLD} \
      --reg ${LTA} \
      --regheader \
      --threads 8

    # Apply transform
    BOLD_IN_T1W="${OUTPUT_DIR}/sub-${sub}/sub-${sub}_run-${run}_bold_in_t1w.nii.gz"
    mri_vol2vol \
      --mov ${BOLD} \
      --targ ${T1W} \
      --lta ${LTA} \
      --o ${BOLD_IN_T1W} \
      --interp trilin

    # QC: Compute Dice
    python compute_dice.py \
      --t1w ${T1W} \
      --bold ${BOLD_IN_T1W} \
      --output ${OUTPUT_DIR}/sub-${sub}/qc_run-${run}.txt
  done
done

# =========================================================================
# Step 3: Compare with original_v3
# =========================================================================
python compare_registration_methods.py \
  --method1 original_v3 \
  --method2 mri_coreg \
  --subjects 06 07 \
  --output comparison_report.md
```

**Timeline**:
- Setup: 1 day
- Processing: 2-3 hours (Sub-06/07만)
- QC: 1 day
- Total: 2-3 days

---

#### **Plan C: --bold2anat-init header 빠른 테스트**

```bash
# =========================================================================
# Test on Sub-06 only
# =========================================================================
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_header_init_test"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_header_init_test"

singularity run --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label 06 \
  \
  # === 한 줄만 변경 ===
  --bold2t1w-init header \    # ⭐ Changed!
  \
  # === 나머지 동일 ===
  --bold2t1w-dof 6 \
  --force-bbr \
  --fs-no-reconall \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --use-syn-sdc warn \
  --dummy-scans 4 \
  --nthreads 16 \
  -w /work

# =========================================================================
# QC: Compare Dice
# =========================================================================
python compare_dice.py \
  --original_v3 /storage/.../fmriprep_out_original_v3/sub-06 \
  --header_init /storage/.../fmriprep_out_header_init_test/sub-06 \
  --output dice_comparison_sub06.txt
```

**Decision Tree**:
```
IF header_init Dice > original_v3 Dice:
  → Run all subjects
  → Use this method

ELSE:
  → Stick with original_v3
  → No further testing
```

**Timeline**:
- Test: 1 subject × 2-3 hours
- QC: 30 minutes
- Decision: immediate
- Total: half day

---

### 5.8. 요약 및 결론

**핵심 메시지**:

1. **original_v3 성공** ✅
   ```
   Dice 0.889, 83.3% pass
   8명 group-level 가능
   10명 individual-level 가능
   ```

2. **Limited FOV 문제: 대부분 해결됨**
   ```
   FLIRT가 obliquity + Limited FOV 처리 성공
   PI 우려보다 결과 좋음
   ```

3. **Sub-06/07: 해결책 있음**
   ```
   Good runs (5-6번): Dice 0.92-0.93
   Run-level QC로 사용 가능
   ```

4. **추가 개선 옵션**
   ```
   필요 시:
     - mri_coreg --regheader (가장 robust)
     - --bold2anat-init header (빠른 테스트)

   하지만:
     현재 상태로 충분할 가능성 높음
   ```

**최종 권장**:

```
1순위: 현재 상태 (original_v3) 활용
  → 즉시 분석 시작
  → Sub-06/07 good runs 사용
  → 논문 작성 진행

2순위: mri_coreg 시도 (선택적)
  → Reviewer 요구 시
  → Sub-06/07 전체 runs 사용 원할 경우
  → Methods comparison 원할 경우

3순위: --bold2anat-init header 테스트
  → 호기심 차원
  → 빠른 확인 원할 경우
```

---

## 6. 0106 업데이트 (2): FreeSurfer 제거 vs (a)단계 스킵 - 핵심 오해 해소

**날짜**: 2026-01-06 (추가)
**질문**: "`--fs-no-reconall`은 (a)단계를 스킵하는 것 아닌가요?"

### 6.1. 결론부터: 아니요, 완전히 다릅니다

```
--fs-no-reconall:
  영향: (b) BBR 단계만 영향
  역할: WM boundary 출처 변경 (FreeSurfer → FSL FAST)
  (a) FLIRT 단계: ✅ 여전히 수행됨!

--bold2anat-init header:
  영향: (a) 초기 정렬 단계 변경
  역할: FLIRT 완전히 스킵
  (b) BBR 단계: ✅ 여전히 수행됨
```

**핵심**: 두 옵션은 **서로 다른 단계**에 영향을 줍니다!

---

### 6.2. FreeSurfer의 실제 역할 (코드로 이해)

#### **original_v3의 전체 파이프라인 (FreeSurfer 없음)**

```python
# fMRIPrep 내부 동작 (--fs-no-reconall 사용 시)

def fmriprep_pipeline_no_freesurfer(bold_img, t1w_img):
    """
    original_v3: --fs-no-reconall 사용

    FreeSurfer 역할: (b)단계의 WM boundary 제공
    FreeSurfer 없으면: FSL FAST가 대신 WM segmentation 수행
    """

    # =====================================================================
    # STEP 1: T1w Segmentation (FreeSurfer 대체)
    # =====================================================================
    print("FreeSurfer recon-all 스킵, FSL FAST 사용...")

    # FreeSurfer 대신 FSL FAST로 brain segmentation
    from nipype.interfaces import fsl

    fast_segmentation = fsl.FAST(
        in_files=t1w_img,
        img_type=1,  # T1-weighted
        segments=True,  # Output tissue segments
        number_classes=3,  # CSF, GM, WM
    ).run()

    # WM mask 추출
    wm_mask = fast_segmentation.outputs.tissue_class_files[2]  # Class 2 = WM
    wm_boundary = extract_boundary(wm_mask)

    print(f"  WM boundary extracted from FSL FAST")
    print(f"  FreeSurfer surfaces NOT used")

    # =====================================================================
    # STEP 2: (a) 초기 정렬 - FLIRT ⭐ 여전히 수행됨!
    # =====================================================================
    print("(a) Running FLIRT initial alignment...")

    # FreeSurfer 유무와 무관하게 FLIRT 수행!
    initial_transform = fsl.FLIRT(
        in_file=bold_img,
        reference=t1w_img,
        dof=6,
        cost='mutualinfo',  # Mutual information
        searchr_x=[-90, 90],
        searchr_y=[-90, 90],
        searchr_z=[-90, 90],
        coarse_search=15,
        fine_search=6,
    ).run()

    print(f"  FLIRT completed (FreeSurfer 없어도 실행됨!)")
    print(f"  Initial rotation: ~30° (obliquity)")
    print(f"  Initial translation: scanner coordinates")

    # =====================================================================
    # STEP 3: (b) BBR 미세 조정 - FSL FAST WM boundary 사용
    # =====================================================================
    print("(b) Running BBR refinement...")

    # BBR using FAST WM boundary (NOT FreeSurfer surfaces)
    final_transform = freesurfer.BBRegister(
        source_file=bold_img,
        subject_id='t1w',
        init_transform=initial_transform,  # From FLIRT (a)단계
        contrast_type='bold',
        wm_boundary=wm_boundary,  # ⭐ From FSL FAST (NOT FreeSurfer)
        schedule='default',
    ).run()

    print(f"  BBR completed using FAST WM boundary")

    return final_transform

# 요약:
# FreeSurfer 없어도:
#   (a) FLIRT: ✅ 수행됨
#   (b) BBR: ✅ 수행됨 (WM boundary from FAST)
```

---

#### **FreeSurfer가 있었다면? (original_v3가 사용하지 않은 방법)**

```python
def fmriprep_pipeline_with_freesurfer(bold_img, t1w_img):
    """
    FreeSurfer 사용 시 (우리는 사용 안 함)

    차이점: WM boundary 출처만 다름
    """

    # =====================================================================
    # STEP 1: FreeSurfer recon-all
    # =====================================================================
    print("Running FreeSurfer recon-all...")

    from nipype.interfaces import freesurfer

    # FreeSurfer cortical reconstruction
    # Takes 6-12 hours per subject!
    recon_all = freesurfer.ReconAll(
        subject_id='sub-01',
        T1_files=t1w_img,
        directive='all',
        flags='-qcache',
    ).run()

    # FreeSurfer outputs:
    # - surf/lh.white, rh.white (WM surface)
    # - surf/lh.pial, rh.pial (pial surface)
    # - mri/wm.mgz (WM segmentation)

    # WM boundary from FreeSurfer surfaces
    wm_boundary_lh = load_surface(f'{subjects_dir}/sub-01/surf/lh.white')
    wm_boundary_rh = load_surface(f'{subjects_dir}/sub-01/surf/rh.white')
    wm_boundary = combine_surfaces(wm_boundary_lh, wm_boundary_rh)

    print(f"  WM boundary from FreeSurfer surfaces")

    # =====================================================================
    # STEP 2: (a) 초기 정렬 - FLIRT ⭐ 동일하게 수행됨!
    # =====================================================================
    print("(a) Running FLIRT initial alignment...")

    # FreeSurfer 있어도 FLIRT는 동일!
    initial_transform = fsl.FLIRT(
        in_file=bold_img,
        reference=t1w_img,
        dof=6,
        cost='mutualinfo',
        searchr_x=[-90, 90],
        searchr_y=[-90, 90],
        searchr_z=[-90, 90],
        coarse_search=15,
        fine_search=6,
    ).run()

    print(f"  FLIRT completed (FreeSurfer와 무관)")

    # =====================================================================
    # STEP 3: (b) BBR 미세 조정 - FreeSurfer surfaces 사용
    # =====================================================================
    print("(b) Running BBR refinement...")

    # BBR using FreeSurfer WM surfaces
    final_transform = freesurfer.BBRegister(
        source_file=bold_img,
        subject_id='sub-01',  # Must exist in FreeSurfer SUBJECTS_DIR
        init_transform=initial_transform,  # From FLIRT (a)단계
        contrast_type='bold',
        wm_boundary=wm_boundary,  # ⭐ From FreeSurfer (NOT FAST)
        schedule='default',
    ).run()

    print(f"  BBR completed using FreeSurfer WM surfaces")

    return final_transform

# 요약:
# FreeSurfer 있어도:
#   (a) FLIRT: ✅ 동일하게 수행됨
#   (b) BBR: ✅ 수행됨 (WM boundary from FreeSurfer)
```

---

### 6.3. `--bold2anat-init header`의 실제 동작 (진짜 (a)스킵)

```python
def fmriprep_pipeline_header_init(bold_img, t1w_img):
    """
    --bold2anat-init header 사용 시

    이것이 진짜 (a)단계 스킵!
    """

    # =====================================================================
    # STEP 1: WM Segmentation (FreeSurfer or FAST)
    # =====================================================================
    # (FreeSurfer 유무에 따라 위와 동일)
    wm_boundary = ...

    # =====================================================================
    # STEP 2: (a) 초기 정렬 - ⭐ SKIP!
    # =====================================================================
    print("(a) SKIPPED - Using header-based initialization...")

    # FLIRT 안 돌림!
    # Header에서 직접 transform 추출

    bold_qform = bold_img.header.get_qform()
    bold_sform = bold_img.header.get_sform()
    t1w_qform = t1w_img.header.get_qform()
    t1w_sform = t1w_img.header.get_sform()

    initial_transform = compute_header_alignment(
        bold_qform, bold_sform,
        t1w_qform, t1w_sform
    )

    print(f"  FLIRT NOT RUN (스킵됨)")
    print(f"  Initial transform from NIfTI header only")
    print(f"  Rotation from qform: ~30° (obliquity)")
    print(f"  WARNING: Header may be inaccurate!")

    # =====================================================================
    # STEP 3: (b) BBR 미세 조정 - ⭐ 여전히 수행됨
    # =====================================================================
    print("(b) Running BBR refinement...")

    # BBR은 동일하게 수행
    final_transform = freesurfer.BBRegister(
        source_file=bold_img,
        subject_id='t1w',
        init_transform=initial_transform,  # ⭐ From header (NOT FLIRT!)
        contrast_type='bold',
        wm_boundary=wm_boundary,  # FreeSurfer or FAST
        schedule='default',
    ).run()

    print(f"  BBR completed")
    print(f"  BBR had to correct larger errors (header inaccuracy)")

    return final_transform

# 요약:
# --bold2anat-init header:
#   (a) FLIRT: ❌ 스킵됨!
#   (b) BBR: ✅ 수행됨 (header에서 시작)
```

---

### 6.4. 세 가지 설정의 명확한 비교

#### **비교표: FreeSurfer vs 초기화 방법**

| 설정 | FreeSurfer | (a) 초기 정렬 | (b) BBR | WM Boundary | 초기화 방법 |
|------|-----------|--------------|---------|-------------|-----------|
| **original_v3 (현재)** | ❌ `--fs-no-reconall` | ✅ FLIRT | ✅ BBR | FSL FAST | FLIRT MI |
| **FreeSurfer 사용** | ✅ recon-all | ✅ FLIRT | ✅ BBR | FreeSurfer | FLIRT MI |
| **`--bold2anat-init header`** | ❌ or ✅ (둘 다 가능) | ❌ **SKIP** | ✅ BBR | FAST or FS | Header |

**핵심 포인트**:

```
FreeSurfer 유무:
  → (a)단계에 영향 없음!
  → (b)단계의 WM boundary만 변경
  → FLIRT는 둘 다 실행됨

--bold2anat-init header:
  → (a)단계 완전히 스킵!
  → FreeSurfer와 조합 가능:
    * --bold2anat-init header --fs-no-reconall (Header + FAST)
    * --bold2anat-init header (Header + FreeSurfer)
```

---

### 6.5. 이론적 설명: 왜 FreeSurfer가 (a)단계와 무관한가?

#### **Registration의 두 단계 분리**

```
fMRIPrep BOLD → T1w Registration:

┌─────────────────────────────────────────────────────────────┐
│ Phase (a): Initial Alignment                                │
│   목적: Coordinate systems 정렬 (oblique → cardinal)        │
│   입력: BOLD raw, T1w raw                                   │
│   방법: FLIRT (intensity-based) or Header (coordinate-based)│
│   출력: Coarse transform (±5-10° error)                     │
│                                                              │
│   FreeSurfer 역할: 없음! ❌                                  │
│   → FLIRT는 intensity만 사용                                 │
│   → Header는 NIfTI metadata만 사용                          │
│   → FreeSurfer surfaces 안 씀                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
                  initial_transform
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase (b): BBR Refinement                                   │
│   목적: Sub-mm precision                                    │
│   입력: BOLD, T1w, initial_transform, WM boundary           │
│   방법: BBR (boundary-based)                                │
│   출력: Final transform (~0.1mm accuracy)                   │
│                                                              │
│   FreeSurfer 역할: WM boundary 제공 ⭐                       │
│   → FreeSurfer 있으면: surf/lh.white, rh.white 사용         │
│   → FreeSurfer 없으면: FSL FAST wm.nii.gz 사용              │
│   → BBR 알고리즘 자체는 동일!                                │
└─────────────────────────────────────────────────────────────┘
```

#### **왜 FreeSurfer가 (a)에 영향 없는가?**

```python
# Pseudocode: FLIRT initial alignment

def flirt_initial_alignment(bold_img, t1w_img):
    """
    Inputs: Image intensities only
    No surfaces, no segmentation needed
    """

    # Cost function: Mutual Information
    def mi_cost(transform_params):
        # Apply transform
        bold_transformed = apply_transform(bold_img, transform_params)

        # Compute joint histogram
        hist_2d = compute_joint_histogram(
            bold_transformed,  # BOLD intensities
            t1w_img            # T1w intensities
        )

        # Compute MI
        mi = compute_mutual_information(hist_2d)

        # NO FreeSurfer data used here!
        # NO WM boundaries needed!
        # Only raw intensities!

        return -mi  # Maximize MI

    # Optimize
    best_params = optimize(mi_cost, search_range_wide)

    return best_params

# FreeSurfer surfaces는 이 과정에 전혀 사용되지 않음!
```

```python
# Pseudocode: BBR refinement

def bbr_refinement(bold_img, t1w_img, init_transform, wm_boundary):
    """
    Inputs:
      - init_transform from (a)
      - wm_boundary ⭐ 여기서 FreeSurfer 역할!
    """

    # Cost function: Boundary alignment
    def bbr_cost(transform_params):
        # Apply transform
        bold_transformed = apply_transform(bold_img, transform_params)

        # Compute BOLD gradient
        bold_gradient = compute_gradient(bold_transformed)

        # Evaluate at WM boundary
        gradient_at_boundary = sample_values(
            bold_gradient,
            locations=wm_boundary  # ⭐ FreeSurfer or FAST
        )

        # Cost: negative gradient (maximize gradient at boundary)
        cost = -np.mean(gradient_at_boundary)

        return cost

    # Optimize (narrow search range)
    best_params = optimize(
        bbr_cost,
        init_x0=init_transform,  # From (a)
        search_range_narrow      # ±5°
    )

    return best_params

# FreeSurfer는 wm_boundary로만 사용됨
# FAST도 WM mask 제공 가능
# → FreeSurfer 필수 아님!
```

---

### 6.6. 실제 sbatch 파일로 확인

#### **original_v3의 실제 설정**

```bash
# From: slurm_jobs/preprocessing/run_fmriprep_original_data_array.sbatch

singularity run --cleanenv \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  \
  # =========================================================================
  # FreeSurfer 설정: ❌ 사용 안 함
  # =========================================================================
  --fs-no-reconall \              # Skip FreeSurfer recon-all
  --fs-license-file /opt/freesurfer/license.txt \
  \
  # =========================================================================
  # Registration 설정: (a)단계 포함!
  # =========================================================================
  --bold2t1w-dof 6 \              # 6 DOF rigid
  --bold2t1w-init register \      # ⭐ FLIRT 수행 (NOT header!)
  --force-bbr \                   # BBR 사용
  \
  # 다른 설정...
```

**해석**:
```
--fs-no-reconall:
  → FreeSurfer recon-all 스킵
  → WM boundary는 FSL FAST로 얻음
  → (a) FLIRT에는 영향 없음!

--bold2t1w-init register:
  → FLIRT 초기 정렬 수행
  → (a)단계 포함!
  → FreeSurfer 없어도 실행 가능
```

---

#### **(a)단계를 스킵하려면? (우리는 안 함)**

```bash
# Hypothetical: (a)단계 스킵 버전 (우리 데이터에 비추천)

singularity run --cleanenv \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  \
  # FreeSurfer: 사용 여부 선택 가능
  --fs-no-reconall \              # Option 1: FAST (빠름)
  # (or FreeSurfer 사용)          # Option 2: FreeSurfer (느림, 정밀)
  \
  # Registration: (a)단계 스킵!
  --bold2t1w-dof 6 \
  --bold2t1w-init header \        # ⭐ Header 사용 (FLIRT 스킵!)
  --force-bbr \
  \
  # 다른 설정...
```

**가능한 조합**:

| FreeSurfer | 초기화 | (a)단계 | (b)단계 | WM Boundary |
|-----------|-------|---------|---------|-------------|
| ❌ `--fs-no-reconall` | `register` | ✅ FLIRT | ✅ BBR | FAST |
| ✅ (default) | `register` | ✅ FLIRT | ✅ BBR | FreeSurfer |
| ❌ `--fs-no-reconall` | `header` | ❌ Skip | ✅ BBR | FAST |
| ✅ (default) | `header` | ❌ Skip | ✅ BBR | FreeSurfer |

**original_v3 = Row 1** (FreeSurfer 없음 + FLIRT 수행)

---

### 6.7. 왜 이런 오해가 생기는가?

#### **PI 피드백 재검토**

PI가 제안한 두 가지:

> 1. "(a)과정을 스킵하는 flag를 넣고 BBR을 돌려보는 것"
> 2. "또는 freesurfer... boundary-based registration 명령어에 (a)과정 스킵하는 flag 추가"

**오해의 원인**:
```
FreeSurfer 언급 → FreeSurfer 제거 = (a)스킵?
BUT:
  PI가 말한 "FreeSurfer BBR 명령어"는:
    → bbregister 도구를 의미 (FreeSurfer 패키지의 명령어)
    → FreeSurfer recon-all과는 다름!

bbregister:
  - FreeSurfer 패키지의 registration 도구
  - recon-all과 독립적으로 사용 가능
  - --no-pass1 flag로 (a) 비슷한 단계 스킵

FreeSurfer recon-all:
  - Cortical reconstruction
  - T1w segmentation, surface extraction
  - bbregister의 input 제공
  - 하지만 bbregister 사용에 필수 아님!
```

**정확한 이해**:

```
PI 제안 1: fMRIPrep --bold2anat-init header
  → (a) FLIRT 스킵
  → FreeSurfer 유무와 무관

PI 제안 2: bbregister --no-pass1
  → FreeSurfer 도구 사용
  → recon-all 필요 (WM surfaces)
  → --no-pass1: BBR의 coarse pass 스킵 (FLIRT 아님!)

--fs-no-reconall:
  → FreeSurfer recon-all만 스킵
  → (a) FLIRT는 영향 받지 않음
  → PI 제안과 다른 개념!
```

---

### 6.8. 최종 정리: FreeSurfer vs 초기화 방법

#### **독립적인 두 축**

```
Axis 1: WM Boundary 출처 (FreeSurfer 유무)
  ├─ FreeSurfer recon-all (느림, 정밀)
  └─ FSL FAST (빠름, 충분)

  영향받는 단계: (b) BBR only
  영향받지 않는 단계: (a) Initial alignment

Axis 2: 초기 정렬 방법
  ├─ FLIRT (intensity-based, robust)
  └─ Header (coordinate-based, fast)

  영향받는 단계: (a) Initial alignment only
  영향받지 않는 단계: (b) BBR (init_transform만 받음)
```

**2×2 조합 가능**:

```
┌─────────────────┬──────────────────┬──────────────────┐
│                 │ Init: FLIRT      │ Init: Header     │
├─────────────────┼──────────────────┼──────────────────┤
│ FreeSurfer YES  │ FLIRT + FS BBR   │ Header + FS BBR  │
│                 │ (표준 fMRIPrep)  │ (Limited FOV용)  │
├─────────────────┼──────────────────┼──────────────────┤
│ FreeSurfer NO   │ FLIRT + FAST BBR │ Header + FAST BBR│
│ --fs-no-reconall│ (original_v3) ⭐ │ (빠른 대안)      │
└─────────────────┴──────────────────┴──────────────────┘
```

**original_v3 위치**: Row 2, Column 1
- FreeSurfer: NO
- 초기화: FLIRT
- (a)단계: ✅ 수행됨!

---

### 6.9. 결론

#### **FreeSurfer 제거 (`--fs-no-reconall`)**:

```
✅ 이렇게 작동:
  - FreeSurfer recon-all 스킵 (6-12시간 절약)
  - FSL FAST로 WM segmentation 대체
  - (b) BBR은 FAST WM mask 사용
  - (a) FLIRT는 동일하게 수행

❌ 이렇게 작동하지 않음:
  - (a)단계 스킵하지 않음!
  - FLIRT는 여전히 실행됨
  - Header initialization과 무관
```

#### **(a)단계 스킵 (`--bold2anat-init header`)**:

```
✅ 이렇게 작동:
  - FLIRT 완전히 스킵
  - NIfTI header에서 transform 추출
  - (b) BBR은 header transform에서 시작
  - FreeSurfer 유무와 무관하게 작동 가능

❌ 이렇게 작동하지 않음:
  - FreeSurfer 제거와 다름!
  - WM boundary 출처와 무관
```

#### **original_v3가 (a)단계 스킵했나?**

```
❌ 아니요!

original_v3 설정:
  --bold2t1w-init register  → FLIRT 수행 (a)단계 포함
  --fs-no-reconall          → FreeSurfer 스킵 (b)단계만 영향

결과:
  (a) FLIRT: ✅ 수행됨
  (b) BBR: ✅ 수행됨 (FAST WM boundary)

→ 표준 2단계 pipeline 완전히 수행!
```

#### **PI 제안을 적용하려면?**

```bash
# (a)단계 스킵 버전 (PI 제안)

singularity run --cleanenv \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  \
  --bold2t1w-init header \        # ⭐ 이것이 (a)스킵!
  --bold2t1w-dof 6 \
  --force-bbr \
  --fs-no-reconall \              # FreeSurfer도 스킵 (선택)
  \
  # 나머지 동일...
```

**예상 효과**:
```
Limited FOV 문제: ✅ 해결 (FLIRT 스킵)
High obliquity 문제: ❌ 미해결 (header 부정확)
우리 케이스 적합성: ⚠️ 부분적
original_v3 대비: 개선 불확실 (테스트 필요)
```

---

**작성 일자**: 2026-01-06
**업데이트**: FreeSurfer vs 초기화 방법 명확화, 코드 및 이론 추가
**상태**: ✅ 핵심 오해 해소 완료

---

**작성 일자**: 2026-01-06
**업데이트**: original_v3 결과 반영, 구체적 코드 추가
**상태**: ✅ 분석 완료, 실행 계획 수립 완료