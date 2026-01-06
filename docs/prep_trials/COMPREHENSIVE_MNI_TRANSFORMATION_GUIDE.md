# Comprehensive MNI Transformation Diagnosis Guide

**목적**: BOLD, T1w, MNI 간 변환 체인의 완전한 진단 및 검증 프로토콜

**작성일**: 2025-01-04
**대상**: 장거리 비행 중 참고용 - 인터넷 없이 독립적으로 진단 가능

---

## 📋 목차

1. [개요: MNI 변환 체인의 구조](#1-개요-mni-변환-체인의-구조)
2. [진단 워크플로우](#2-진단-워크플로우)
3. [단계별 상세 진단](#3-단계별-상세-진단)
4. [문제 패턴 및 해결](#4-문제-패턴-및-해결)
5. [시각적 검증 가이드](#5-시각적-검증-가이드)
6. [체크리스트](#6-체크리스트)

---

## 1. 개요: MNI 변환 체인의 구조

### 1.1 전체 변환 파이프라인

```
Raw Data (Native Space)
         ↓
┌────────────────────────────────────────────────┐
│  fMRIPrep Preprocessing                        │
├────────────────────────────────────────────────┤
│                                                │
│  T1w Processing:                               │
│  ① Skull stripping (antsBrainExtraction)       │
│  ② Normalization to MNI (ANTs SyN)             │
│     → T1w(native) → T1w(MNI)                   │
│                                                │
│  BOLD Processing:                              │
│  ① Motion correction                           │
│  ② Susceptibility distortion correction (SDC)  │
│  ③ Registration to T1w (BBR)                   │
│     → BOLD(native) → BOLD(T1w)                 │
│  ④ Apply T1w→MNI transform                     │
│     → BOLD(T1w) → BOLD(MNI)                    │
│                                                │
└────────────────────────────────────────────────┘
         ↓
MNI Space Output
  - T1w in MNI space
  - BOLD in MNI space
  - All aligned to template
```

### 1.2 변환 체인의 핵심 링크

| 링크 | 변환 | 도구 | 실패 시 증상 |
|------|------|------|--------------|
| **Link 1** | T1w → MNI | ANTs SyN | T1w(MNI) ≠ Template |
| **Link 2** | BOLD → T1w | BBR (FSL) | BOLD-T1w misalignment |
| **Link 3** | BOLD(T1w) → BOLD(MNI) | Apply T1w warp | Grid mismatch |
| **Link 4** | SDC | fieldmap or SyN | Geometric distortion |

### 1.3 검증해야 할 공간들

```
┌──────────────┐
│ Native Space │ ← Raw acquisition
└──────────────┘
       ↓
┌──────────────┐
│  T1w Space   │ ← Individual anatomy reference
└──────────────┘
       ↓
┌──────────────┐
│  MNI Space   │ ← Standard template (MNI152NLin2009cAsym)
└──────────────┘
```

**검증 포인트**:
1. T1w(MNI) vs MNI Template → Link 1 검증
2. BOLD(MNI) vs MNI Template → Link 1+2+3 검증
3. BOLD(MNI) vs T1w(MNI) → Grid/resolution 일관성

---

## 2. 진단 워크플로우

### 2.1 전체 프로세스

```
┌─────────────────────┐
│ 1. 자동 수치 진단   │  diagnose_mni_chain.py
│   - Affine 비교     │  (5분)
│   - Shape 비교      │
│   - Voxel size 비교 │
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 2. 시각적 검증      │  fsleyes
│   - Step A: T1w-MNI │  (15분/피험자)
│   - Step B: BOLD-MNI│
│   - Step C: 상호비교│
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 3. 원인 판정        │  해석 매트릭스
│   - 문제 링크 식별  │  (5분)
│   - 해결 방안 선택  │
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 4. 해결 및 재검증   │
│   - fMRIPrep 재실행 │
│   - 또는 수동 보정  │
└─────────────────────┘
```

### 2.2 타임라인 (피험자 10명 기준)

| 단계 | 소요 시간 | 병렬 가능 | 총 시간 |
|------|-----------|-----------|---------|
| 자동 진단 실행 | 30분 | ✅ Yes | 30분 |
| 결과 다운로드 | 5분 | - | 5분 |
| 수치 결과 확인 | 30분 | - | 30분 |
| 시각적 검증 | 15분/명 | ⚠️ Partial | 2-3시간 |
| 원인 판정 | 10분/명 | - | 1시간 |
| **총계** | - | - | **4-5시간** |

---

## 3. 단계별 상세 진단

### 3.1 Step 0: 사전 준비

#### 필요한 파일들

```bash
# Server (실행 환경)
/storage/connectome/haba6030/fmriprep_out_deoblique_v2/
├── sub-01/
│   ├── anat/
│   │   └── *_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz
│   └── func/
│       └── *_run-1_space-MNI152NLin2009cAsym_boldref.nii.gz
├── sub-02/
└── ...

# MNI Template (로컬 또는 서버)
~/.cache/templateflow/tpl-MNI152NLin2009cAsym/
└── tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz
```

#### 환경 체크리스트

- [ ] Python 환경: nilearn, nibabel, numpy
- [ ] fsleyes 설치됨
- [ ] Template 다운로드됨
- [ ] 충분한 디스크 공간 (이미지 다운로드 시 ~5GB/피험자)

---

### 3.2 Step 1: 자동 수치 진단

#### 실행

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind
sbatch run_mni_diagnosis.sbatch

# 또는 특정 피험자만
sbatch --array=1,2,3 run_mni_diagnosis.sbatch
```

#### 출력 해석

**예시 출력**:
```
=========================================
  Image Metadata
=========================================

📋 MNI Template:
   Shape:      (91, 109, 91)
   Voxel size: [2. 2. 2.] mm
   MNI bbox:   [-90. -126.  -72.] → [ 90.  90.  108.]

📋 T1w(MNI):
   Shape:      (91, 109, 91)
   Voxel size: [2. 2. 2.] mm
   MNI bbox:   [-90. -126.  -72.] → [ 90.  90.  108.]

📋 BOLD(MNI):
   Shape:      (91, 109, 91)
   Voxel size: [2. 2. 2.] mm
   MNI bbox:   [-90. -126.  -72.] → [ 90.  90.  108.]

=========================================
  Chain Diagnosis
=========================================

🔍 Comparing T1w(MNI) vs Template:
   Affine match:      ✅ YES
   Shape match:       ✅ YES
   Voxel size match:  ✅ YES

🔍 Comparing BOLD(MNI) vs Template:
   Affine match:      ✅ YES
   Shape match:       ✅ YES
   Voxel size match:  ✅ YES

🔍 Comparing BOLD(MNI) vs T1w(MNI):
   Affine match:      ✅ YES
   Shape match:       ✅ YES
   Voxel size match:  ✅ YES

=========================================
  Summary
=========================================
T1w → MNI:        ✅ OK
BOLD → MNI:       ✅ OK
Grid consistency: ✅ OK
```

#### 수치 기준

| 항목 | 정상 범위 | 경고 범위 | 실패 |
|------|-----------|-----------|------|
| Affine max diff | < 0.001 | 0.001-0.1 | > 0.1 |
| Shape match | Exact | - | Any diff |
| Voxel size diff | < 0.01mm | 0.01-0.1mm | > 0.1mm |

---

### 3.3 Step 2: 시각적 검증

#### Step A: T1w(MNI) ↔ MNI Template

**목적**: T1w → MNI 변환의 품질 확인

**실행**:
```bash
# fsleyes 명령어 (자동 생성됨)
fsleyes $TEMPLATE $T1W_MNI -cm red -a 50
```

**체크 포인트**:

1. **Midline (sagittal view, x=0)**
   - [ ] Interhemispheric fissure 정중선
   - [ ] Corpus callosum 중앙 정렬
   - [ ] Brainstem 중앙 정렬

2. **Ventricles (axial view, z=20)**
   - [ ] Lateral ventricles 크기/모양
   - [ ] 3rd ventricle 중앙 위치
   - [ ] 4th ventricle 위치

3. **Occipital cortex (sagittal view, x=±20)**
   - [ ] Calcarine sulcus 위치
   - [ ] Occipital pole 정렬
   - [ ] Cerebellum 경계

**정상 예시**:
```
✅ GOOD:
- Template와 T1w의 주요 구조물이 정확히 겹침
- 회백질/백질 경계가 일치
- 뇌 윤곽이 매끄럽게 정렬

❌ BAD:
- 뇌가 회전되어 있음 (affine 문제)
- 국소적 왜곡 (warp field 문제)
- Ventricle 크기 불일치 (registration 실패)
```

#### Step B: BOLD(MNI) ↔ MNI Template

**목적**: BOLD → MNI 전체 체인 확인

**실행**:
```bash
fsleyes $TEMPLATE $BOLD_MNI -cm blue -a 50
```

**체크 포인트**:

1. **Overall position**
   - [ ] 뇌 전체가 template 범위 내
   - [ ] 극단적 오프셋 없음
   - [ ] Coverage가 적절함

2. **Occipital cortex (critical!)**
   - [ ] V1 영역이 template와 정렬
   - [ ] 후두엽 왜곡 없음
   - [ ] Signal dropout 확인

3. **Distortion artifacts**
   - [ ] 전두엽 susceptibility 확인
   - [ ] EPI 왜곡 패턴
   - [ ] Ghosting/aliasing 없음

**정상 vs 비정상**:

| 관찰 | 정상 | 비정상 (원인) |
|------|------|---------------|
| 전체 위치 | Template 내 중앙 | 크게 벗어남 (BBR 실패) |
| 후두엽 | 정렬됨 | 왜곡/이동 (SDC 미적용) |
| SNR | 충분함 | 매우 낮음 (signal dropout) |
| Coverage | 전체 뇌 | 일부 누락 (acquisition) |

#### Step C: BOLD(MNI) ↔ T1w(MNI)

**목적**: Grid/resolution 일관성 확인

**실행**:
```bash
fsleyes $T1W_MNI $BOLD_MNI -cm red -a 50
```

**체크 포인트**:

1. **Gray-white matter boundaries**
   - [ ] Cortical ribbon 정렬
   - [ ] Subcortical structures 위치
   - [ ] CSF spaces 일치

2. **Relative offset**
   - [ ] Systematic shift 없음
   - [ ] Rotation 없음
   - [ ] Scaling 일치

3. **Resolution difference**
   - [ ] BOLD가 더 낮은 해상도 (정상)
   - [ ] 하지만 격자(grid)는 동일
   - [ ] Partial volume effect 이해

**Expected**:
- BOLD는 T1w보다 "blocky" (낮은 해상도)
- 하지만 구조물의 위치는 정확히 일치
- Voxel edges가 aligned됨

---

### 3.4 Step 3: 원인 판정

#### 해석 매트릭스

| T1w→MNI | BOLD→MNI | BOLD↔T1w | 진단 | 원인 링크 | 우선 조치 |
|---------|----------|----------|------|-----------|----------|
| ❌ | - | - | **T1w normalization 실패** | Link 1 | T1w skull-stripping 확인 |
| ✅ | ❌ | - | **BOLD registration 실패** | Link 2 or 4 | BBR/SDC 로그 확인 |
| ✅ | ✅ | ❌ | **Grid 불일치** | Link 3 | fMRIPrep resolution flag 확인 |
| ✅ | ✅ | ✅ | **MNI 체인 정상** | - | ROI 분석 코드 확인 |

#### 상세 원인 분석

##### Case 1: T1w → MNI 실패 (❌--)

**증상**:
- T1w(MNI)가 template와 크게 다름
- 회전/이동/크기 불일치
- Ventricles 위치 맞지 않음

**가능한 원인**:
1. **Skull-stripping 실패**
   - 뇌 실질이 과도하게 제거됨
   - 또는 skull이 남아있음
   - → Registration의 input이 잘못됨

2. **ANTs registration 실패**
   - 낮은 SNR로 최적화 실패
   - 극단적 해부학적 변이
   - Motion artifact로 T1w 품질 저하

3. **Template 불일치**
   - 잘못된 template 사용
   - Resolution mismatch

**진단 명령어**:
```bash
# T1w brain mask 확인
fsleyes $T1W_NATIVE $T1W_BRAIN_MASK

# ANTs registration 로그
cat fmriprep_work/*/anat_preproc_wf/anat_norm_wf/registration/log.txt

# 사용된 template 확인
grep "template" fmriprep_out/sub-01/anat/*_T1w.json
```

**해결 방안**:
```bash
# Option 1: 다른 skull-strip 방법 시도
--skull-strip-t1w force  # 강제 적용
--skull-strip-t1w skip   # 이미 stripped된 경우

# Option 2: Registration 파라미터 조정
# (fMRIPrep에서는 제한적, manual registration 고려)

# Option 3: 피험자 제외
# (극단적인 경우)
```

##### Case 2: BOLD → MNI 실패 (✅❌-)

**증상**:
- T1w(MNI)는 정상
- BOLD(MNI)가 template와 다름
- 특히 후두엽 misalignment

**가능한 원인**:
1. **BBR (Boundary-Based Registration) 실패**
   - BOLD-T1w contrast 불충분
   - Motion으로 BOLD 품질 저하
   - White matter boundary 불명확

2. **SDC (Susceptibility Distortion Correction) 미적용**
   - Fieldmap 없음 또는 인식 실패
   - B0FieldIdentifier 누락
   - SyN-SDC도 실패

3. **Motion corruption**
   - 과도한 움직임
   - Registration이 잘못된 시점 사용

**진단 명령어**:
```bash
# BBR 로그 확인
cat fmriprep_work/*/func_preproc_wf/bold_reg_wf/bbreg_wf/log.txt

# SDC 적용 여부
grep "B0FieldSource" fmriprep_out/sub-01/func/*_bold.json
# 있으면: SDC 적용됨
# 없으면: SDC 미적용

# Motion 확인
cat fmriprep_out/sub-01/func/*_desc-confounds_timeseries.tsv | \
  grep framewise_displacement
```

**해결 방안**:
```bash
# Option 1: SDC 활성화
--use-syn-sdc  # Fieldmap 없을 때 SyN-based SDC
# + B0FieldIdentifier 확인

# Option 2: BBR 강제
--force-bbr
--bold2t1w-dof 9  # DOF 증가 (6 → 9)

# Option 3: Dummy scans 제거
--dummy-scans 5  # 초기 불안정 볼륨 제거
```

##### Case 3: Grid 불일치 (✅✅❌)

**증상**:
- 수치적으로 T1w, BOLD 모두 MNI space
- 하지만 서로 간 affine이 다름
- Shape 또는 voxel size 불일치

**가능한 원인**:
1. **fMRIPrep output-spaces 설정 불일치**
   - T1w와 BOLD가 다른 resolution으로 출력
   - 또는 다른 template 사용

2. **Resampling 문제**
   - BOLD가 다른 grid로 resampling됨
   - Affine matrix가 달라짐

**진단 명령어**:
```bash
# fMRIPrep 명령어 확인
cat run_fmriprep_*.sbatch | grep "output-spaces"

# 예상: --output-spaces MNI152NLin2009cAsym:res-2

# Header 확인
fslhd $T1W_MNI | grep -A 10 "^dim"
fslhd $BOLD_MNI | grep -A 10 "^dim"
```

**해결 방안**:
```bash
# fMRIPrep 재실행 with consistent settings
--output-spaces MNI152NLin2009cAsym:res-2

# 모든 출력이 동일한 grid 사용하도록
```

##### Case 4: MNI 체인 정상 (✅✅✅)

**증상**:
- 모든 수치 검증 통과
- 시각적으로도 정상
- 하지만 ROI extraction에서 문제

**가능한 원인**:
1. **ROI atlas 문제**
   - Atlas가 다른 MNI space
   - 또는 native space에서 정의됨
   - Resolution 불일치

2. **Analysis 코드 버그**
   - Resampling 누락
   - Incorrect coordinate system
   - Off-by-one error

**진단 명령어**:
```python
# Atlas space 확인
from nilearn import datasets
atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
roi_img = atlas.maps

print("Atlas affine:")
print(roi_img.affine)

print("\nBOLD(MNI) affine:")
print(bold_mni_img.affine)

# Should be identical
```

**해결 방안**:
```python
# ROI를 BOLD space로 resample
from nilearn.image import resample_to_img

roi_resampled = resample_to_img(
    roi_img,
    bold_mni_img,
    interpolation='nearest'
)
```

---

## 4. 문제 패턴 및 해결

### 4.1 빈번한 문제 패턴

#### Pattern A: Sub-04 타입 (Zero BOLD signal)

**특징**:
- fMRIPrep 완료되지만 ROI 위치에 signal 없음
- Brain mask가 visual cortex 제외
- Functional coverage 불충분

**원인**:
- EPI acquisition 범위가 좁음
- Severe signal dropout
- Incorrect slice prescription

**해결**:
- 피험자 제외
- 또는 acquisition 재획득

#### Pattern B: Sub-01 타입 (Outlier voxel count)

**특징**:
- 개별 분석은 작동
- 하지만 group level에서 voxel 수 극단적으로 적음
- 다른 피험자 대비 <10%

**원인**:
- Registration quality는 OK
- 하지만 signal quality 낮음
- Feature selection에서 대부분 제거됨

**해결**:
- Individual analysis는 유지
- Group analysis에서 제외

#### Pattern C: SDC 미적용

**특징**:
- 후두엽 geometric distortion
- Especially inferior temporal/frontal

**원인**:
- Fieldmap 없음
- B0FieldIdentifier 누락
- SyN-SDC 실패

**해결**:
```bash
# Fieldmap 확인
ls bids/sub-01/fmap/

# B0FieldIdentifier 추가 (dataset_description.json)
{
  "IntendedFor": "func/sub-01_task-rsvp_run-1_bold.nii.gz",
  "B0FieldIdentifier": "fmap01"
}

# 또는 SyN-SDC 사용
fmriprep ... --use-syn-sdc
```

### 4.2 해결 플로우차트

```
문제 발견
    ↓
수치 진단으로 원인 링크 식별
    ↓
시각적 검증으로 확인
    ↓
    ├─ Link 1 문제 → fMRIPrep 로그 확인 → skull-strip/ANTs 재설정
    ├─ Link 2 문제 → BBR 로그 확인 → BBR/SDC 재설정
    ├─ Link 3 문제 → output-spaces 확인 → 재실행
    └─ Link 4 문제 → ROI 코드 확인 → resampling 추가
    ↓
재실행 또는 보정
    ↓
재검증
    ↓
✅ 통과 또는 피험자 제외
```

---

## 5. 시각적 검증 가이드

### 5.1 fsleyes 사용법

#### 기본 명령어

```bash
# 단순 overlay
fsleyes template.nii.gz image.nii.gz

# Colormap 및 투명도 조정
fsleyes template.nii.gz image.nii.gz -cm red -a 50

# Multiple overlays
fsleyes template.nii.gz \
        t1w_mni.nii.gz -cm red -a 50 \
        bold_mni.nii.gz -cm blue -a 30
```

#### 유용한 단축키

| 키 | 기능 |
|----|------|
| `Space` | Toggle overlay on/off |
| `←` `→` | Navigate slices |
| `Ctrl + L` | Location info |
| `Ctrl + O` | Ortho view |
| `Ctrl + S` | Screenshot |

#### 체크해야 할 뷰

```
Sagittal (x축):
  - x = 0 (midline)
  - x = ±20 (V1 영역)
  - x = ±40 (lateral V2/V3)

Coronal (y축):
  - y = -90 (occipital pole)
  - y = -70 (calcarine)
  - y = 0 (central sulcus)

Axial (z축):
  - z = -20 (inferior temporal)
  - z = 0 (AC-PC line)
  - z = 20 (ventricles)
  - z = 60 (superior parietal)
```

### 5.2 스크린샷 가이드

**필수 스크린샷** (피험자당):

```bash
# Step A: T1w vs Template
fsleyes $TEMPLATE $T1W_MNI -cm red -a 50

# Save:
- T1w_vs_Template_sagittal_midline.png (x=0)
- T1w_vs_Template_axial_ventricles.png (z=20)
- T1w_vs_Template_coronal_occipital.png (y=-90)

# Step B: BOLD vs Template
fsleyes $TEMPLATE $BOLD_MNI -cm blue -a 50

# Save:
- BOLD_vs_Template_sagittal_V1.png (x=-20)
- BOLD_vs_Template_axial_visual.png (z=-10)
- BOLD_vs_Template_coronal_occipital.png (y=-90)

# Step C: BOLD vs T1w
fsleyes $T1W_MNI $BOLD_MNI -cm red -a 50

# Save:
- BOLD_vs_T1w_sagittal.png (x=-20)
- BOLD_vs_T1w_axial.png (z=0)
```

**파일 구조**:
```
logs/mni_diagnosis/
└── visual_inspection/
    ├── sub-01/
    │   ├── Step_A_T1w_vs_Template/
    │   ├── Step_B_BOLD_vs_Template/
    │   └── Step_C_BOLD_vs_T1w/
    ├── sub-02/
    └── ...
```

---

## 6. 체크리스트

### 6.1 진단 실행 체크리스트

**사전 준비**:
- [ ] fMRIPrep v2 완료됨
- [ ] Python 환경 설정됨 (nilearn, nibabel)
- [ ] fsleyes 설치됨
- [ ] Template 다운로드됨
- [ ] 충분한 디스크 공간

**자동 진단**:
- [ ] `diagnose_mni_chain.py` 업로드
- [ ] `run_mni_diagnosis.sbatch` 업로드
- [ ] sbatch 제출 완료
- [ ] 작업 완료 확인 (`squeue`)
- [ ] 로그 다운로드

**수치 검증**:
- [ ] 모든 피험자 .out 파일 확인
- [ ] Summary 섹션 확인
- [ ] ❌ 있으면 해당 피험자 우선 검토

**시각적 검증** (문제 피험자):
- [ ] 이미지 파일 다운로드
- [ ] Step A 실행 및 스크린샷
- [ ] Step B 실행 및 스크린샷
- [ ] Step C 실행 및 스크린샷
- [ ] 체크 포인트 모두 확인

**원인 판정**:
- [ ] 해석 매트릭스 적용
- [ ] 원인 링크 식별
- [ ] fMRIPrep 로그 확인 (필요 시)
- [ ] 해결 방안 선택

**조치**:
- [ ] fMRIPrep 재실행 또는
- [ ] 분석 코드 수정 또는
- [ ] 피험자 제외
- [ ] 재검증 실행

### 6.2 피험자별 진단 템플릿

```markdown
## Sub-XX MNI Chain Diagnosis

**Date**: YYYY-MM-DD

### Numerical Validation
- [ ] T1w → MNI: ✅ OK / ❌ FAIL
- [ ] BOLD → MNI: ✅ OK / ❌ FAIL
- [ ] Grid consistency: ✅ OK / ❌ FAIL

### Visual Inspection
**Step A (T1w vs Template)**:
- [ ] Midline aligned
- [ ] Ventricles correct
- [ ] Occipital cortex OK
- Rating: ✅ / ⚠️ / ❌

**Step B (BOLD vs Template)**:
- [ ] Overall position OK
- [ ] Occipital alignment OK
- [ ] No severe distortion
- Rating: ✅ / ⚠️ / ❌

**Step C (BOLD vs T1w)**:
- [ ] GM/WM boundaries align
- [ ] No offset
- [ ] Grid consistent
- Rating: ✅ / ⚠️ / ❌

### Diagnosis
- Primary issue: [Link 1 / Link 2 / Link 3 / Link 4 / None]
- Root cause: [Describe]
- Action: [fMRIPrep rerun / Code fix / Exclude / None]

### Follow-up
- [ ] Issue resolved
- [ ] Re-validated
- [ ] Ready for analysis
```

---

## 7. 빠른 참조

### 7.1 명령어 치트시트

```bash
# === 진단 실행 ===
# 서버
sbatch run_mni_diagnosis.sbatch                    # 전체
sbatch --array=1,2,3 run_mni_diagnosis.sbatch      # 선택

# 결과 다운로드
./DOWNLOAD_MNI_RESULTS.sh

# === 시각적 검증 ===
# 이미지 다운로드
scp 'haba6030@node2:/storage/.../sub-01/anat/*space-MNI*T1w.nii.gz' ./
scp 'haba6030@node2:/storage/.../sub-01/func/*run-1*boldref.nii.gz' ./

# fsleyes
fsleyes template.nii.gz t1w.nii.gz -cm red -a 50

# === 진단 로그 확인 ===
# BBR
cat fmriprep_work/*/bold_reg_wf/bbreg_wf/log.txt

# ANTs
cat fmriprep_work/*/anat_norm_wf/registration/log.txt

# SDC
grep "B0FieldSource" fmriprep_out/sub-01/func/*_bold.json

# === 파일 정보 ===
# Header
fslhd image.nii.gz

# Python
python -c "import nibabel as nib; img=nib.load('img.nii.gz'); print(img.affine)"
```

### 7.2 해석 매트릭스 (간략)

| T1w | BOLD | Grid | 원인 | 조치 |
|-----|------|------|------|------|
| ❌ | - | - | Link 1 | Skull-strip 확인 |
| ✅ | ❌ | - | Link 2/4 | BBR/SDC 확인 |
| ✅ | ✅ | ❌ | Link 3 | output-spaces 확인 |
| ✅ | ✅ | ✅ | ROI issue | Analysis 코드 확인 |

### 7.3 품질 기준 (Quick Reference)

| 메트릭 | 정상 | 경고 | 실패 |
|--------|------|------|------|
| Affine max diff | < 0.001 | 0.001-0.1 | > 0.1 |
| Shape | Exact | - | Different |
| Voxel size diff | < 0.01mm | 0.01-0.1mm | > 0.1mm |
| Visual alignment | Perfect | Minor offset | Obvious misalignment |

---

## 8. 부록

### 8.1 관련 문서

- `MNI_CHAIN_DIAGNOSIS_GUIDE.md` - 기본 사용 가이드
- `MNI_DIAGNOSIS_SERVER_GUIDE.md` - 서버 실행 가이드
- `MNI_DIAGNOSIS_REPORT_TEMPLATE.md` - 리포트 템플릿
- `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md` - 이전 진단 결과
- `GUIDE_to_fMRIprep.md` - fMRIPrep 설정 가이드

### 8.2 파일 경로 레퍼런스

```bash
# === Server Paths ===
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_deoblique_v2"
FMRIPREP_WORK="/storage/connectome/haba6030/fmriprep_work_deoblique_v2_batch1"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind"

# === Key Files ===
# T1w MNI
${FMRIPREP_OUT}/sub-XX/anat/sub-XX_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz

# BOLD MNI (boldref)
${FMRIPREP_OUT}/sub-XX/func/sub-XX_task-rsvp_run-X_space-MNI152NLin2009cAsym_boldref.nii.gz

# Template
~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz

# === Logs ===
# fMRIPrep logs
${FMRIPREP_WORK}/sub-XX/anat_preproc_wf/
${FMRIPREP_WORK}/sub-XX/func_preproc_wf/

# Diagnosis logs
${SCRIPT_DIR}/logs/mni_diagnosis/
```

### 8.3 문제 해결 FAQ

**Q: "No template found" 에러**
```bash
A: Template 다운로드
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"
```

**Q: Affine이 거의 일치하지만 약간 다름 (max diff ~0.01)**
```
A: 일반적으로 문제 없음. 부동소수점 오차 범위.
   시각적 검증에서 확인.
```

**Q: Shape은 같지만 affine이 다름**
```
A: Grid 불일치 문제. fMRIPrep output-spaces 재확인.
```

**Q: 모든 검증 통과했는데 ROI에서 이상한 값**
```
A: ROI atlas resampling 문제. resample_to_img() 사용.
```

---

**END OF GUIDE**

이 문서는 인터넷 연결 없이도 MNI 변환 체인을 완전히 진단할 수 있도록 작성되었습니다.
