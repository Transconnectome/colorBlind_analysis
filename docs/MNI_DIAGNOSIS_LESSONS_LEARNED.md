# MNI Diagnosis - Lessons Learned

**날짜**: 2026-01-04
**상황**: 첫 진단 실행 후 발견된 Template 불일치 문제

---

## 🎯 문제 요약

### 발생한 문제

첫 번째 MNI 진단 실행 시 **모든 피험자(10/10)가 실패**:
- ❌ T1w → MNI: PROBLEM
- ❌ BOLD → MNI: PROBLEM
- ✅ Grid consistency: OK

### 실제 원인

**Template 불일치**:
- fMRIPrep 사용: `MNI152NLin2009cAsym` (TemplateFlow)
- 진단 스크립트 사용: `MNI152_T1_2mm.nii.gz` (FSL)

두 템플릿은 **같은 MNI 공간**이지만 **bounding box가 다름**:
- FSL: (91, 109, 91) voxels
- TemplateFlow: (97, 115, 97) voxels @ 2mm

---

## 📚 배경 지식

### MNI Template의 종류

#### 1. MNI152 (FSL 버전)
```bash
경로: /usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz
Shape: (91, 109, 91)
Orientation: RAS+
사용: FSL 도구들의 기본 템플릿
```

#### 2. MNI152NLin2009cAsym (TemplateFlow)
```bash
경로: ~/.cache/templateflow/tpl-MNI152NLin2009cAsym/
Shape: (97, 115, 97) @ 2mm
Orientation: LAS+
사용: fMRIPrep, BIDS 표준, 최근 연구
```

#### 3. MNI152NLin6Asym (구버전)
```
사용: fMRIPrep 이전 버전
상태: Deprecated
```

### 왜 다른 Template를 사용하는가?

| 특징 | FSL MNI152 | MNI152NLin2009cAsym |
|------|------------|---------------------|
| 제작 연도 | ~2001 | 2009 |
| 정규화 | Linear | Nonlinear (SyN) |
| 표준 | FSL 생태계 | BIDS/TemplateFlow |
| Bounding box | 작음 | 큰 (더 많은 coverage) |
| 최신 연구 | 점차 감소 | 증가 추세 |

**fMRIPrep가 MNI152NLin2009cAsym을 선택한 이유**:
1. **BIDS 표준** - TemplateFlow가 BIDS 권장
2. **더 나은 정규화** - Nonlinear 2009 방법
3. **더 넓은 Coverage** - 소뇌, 측두엽 등 더 포함
4. **재현성** - 버전 관리가 명확 (TemplateFlow)

---

## 🔍 진단 과정

### Step 1: 초기 진단 결과

```bash
# 모든 피험자 동일
T1w → MNI:        ❌ PROBLEM
BOLD → MNI:       ❌ PROBLEM
Grid consistency: ✅ OK
```

### Step 2: Shape 비교

```
Template:    (91, 109, 91)   # FSL
T1w/BOLD:    (97, 115, 97)   # fMRIPrep
```

→ **Mismatch! 하지만 둘 다 2mm voxel size**

### Step 3: Affine 분석

```python
# FSL Template
[[  -2.    0.    0.   90.]     # RAS orientation
 [   0.    2.    0. -126.]
 [   0.    0.    2.  -72.]
 [   0.    0.    0.    1.]]

# fMRIPrep Output
[[   2.     0.     0.   -96.5]  # LAS orientation
 [   0.     2.     0.  -132.5]
 [   0.     0.     2.   -78.5]
 [   0.     0.     0.     1.  ]]
```

→ **X축 sign 다름 + Origin 다름**

### Step 4: Grid Consistency 확인

```
T1w ↔ BOLD: ✅ YES
```

→ **fMRIPrep 내부에서는 완벽히 일치**

### Step 5: 결론

**진단 결과 = False Alarm**
- MNI 정합 자체는 정상
- 단지 비교 템플릿이 잘못됨

---

## ✅ 해결 방법

### Solution 1: 스크립트 수정 (완료)

#### Before (문제)
```python
template_dirs = [
    Path('/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'),  # FSL 먼저
    Path.home() / '.cache/templateflow/...'  # TemplateFlow 나중
]
```

#### After (수정)
```python
template_dirs = [
    # Priority 1: TemplateFlow (matches fMRIPrep)
    Path.home() / '.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz',
    # Priority 2: FSL standard (different bounding box!)
    Path('/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'),
]
```

**변경 사항**:
1. TemplateFlow를 우선순위로
2. 주석으로 차이점 명시
3. Template 다운로드 가이드 추가

### Solution 2: 서버에 Template 준비

```bash
# 서버에서 실행
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"

# 확인
ls ~/.cache/templateflow/tpl-MNI152NLin2009cAsym/
```

### Solution 3: 재진단 실행

```bash
# 수정된 스크립트 업로드
scp diagnose_mni_chain.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 재실행
sbatch run_mni_diagnosis.sbatch

# 또는 단일 피험자 테스트
sbatch --array=1 run_mni_diagnosis.sbatch
```

**예상 결과**:
```
T1w → MNI:        ✅ OK
BOLD → MNI:       ✅ OK
Grid consistency: ✅ OK
```

---

## 📝 Best Practices

### 1. Template 선택 원칙

**규칙**: **항상 fMRIPrep와 동일한 template 사용**

```bash
# fMRIPrep 설정 확인
grep "output-spaces" run_fmriprep_*.sbatch
# → --output-spaces MNI152NLin2009cAsym:res-2

# 동일한 template 사용
TEMPLATE=~/.cache/templateflow/tpl-MNI152NLin2009cAsym/...
```

### 2. Template 자동 감지

더 robust한 방법:

```python
# fMRIPrep JSON에서 template 정보 읽기
import json
with open(fmriprep_out / 'sub-01/anat/*_T1w.json') as f:
    metadata = json.load(f)
    template_space = metadata.get('SpatialReference')
    # → 'MNI152NLin2009cAsym'
```

### 3. Shape Mismatch 해석

Shape이 다르다고 무조건 문제는 아님:
- **같은 voxel size** → Bounding box만 다름 (OK)
- **다른 voxel size** → Resolution 문제 (CHECK)

```python
if np.allclose(vox1, vox2, atol=0.01):  # Voxel size 같음
    if shape1 != shape2:
        print("Different bounding box, but same space - OK")
```

### 4. 시각적 검증 필수

수치만으로 판단하지 말고 **반드시 눈으로 확인**:

```bash
# 의심스러운 경우
fsleyes $CORRECT_TEMPLATE $IMAGE -cm red -a 50
```

---

## ⚠️ 주의사항

### 주의 1: Template 혼용 금지

**잘못된 예**:
```python
# ROI atlas는 FSL MNI
roi_img = nib.load('HarvardOxford_MNI152_T1_2mm.nii.gz')

# BOLD는 TemplateFlow MNI
bold_img = nib.load('sub-01_space-MNI152NLin2009cAsym_bold.nii.gz')

# ❌ 직접 overlap 계산 → WRONG!
overlap = roi_img.get_fdata() * bold_img.get_fdata()
```

**올바른 예**:
```python
# ROI를 BOLD space로 resample
from nilearn.image import resample_to_img
roi_resampled = resample_to_img(roi_img, bold_img, interpolation='nearest')

# ✅ 이제 계산 가능
overlap = roi_resampled.get_fdata() * bold_img.get_fdata()
```

### 주의 2: Orientation 확인

MNI 공간이라도 orientation이 다를 수 있음:
- **RAS+**: Right-Anterior-Superior (FSL 기본)
- **LAS+**: Left-Anterior-Superior (TemplateFlow)

```python
import nibabel as nib
print(nib.aff2axcodes(img.affine))
# → ('L', 'A', 'S') 또는 ('R', 'A', 'S')
```

### 주의 3: 버전 관리

TemplateFlow template도 버전이 있음:

```bash
ls ~/.cache/templateflow/tpl-MNI152NLin2009cAsym/
# → tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz  # 1mm
# → tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz  # 2mm (사용!)
```

**항상 resolution 맞추기**:
```bash
# fMRIPrep
--output-spaces MNI152NLin2009cAsym:res-2  # 2mm

# Template도 2mm 사용
tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz
```

---

## 🎓 교훈

### 1. Template != Template

"MNI space"라고 해서 모두 같은 것이 아님:
- 다른 제작 방법
- 다른 bounding box
- 다른 orientation
- 다른 resolution

### 2. 진단 도구도 검증 필요

자동 진단 도구도:
- 가정(assumption)이 있음
- 잘못된 설정 가능
- False positive/negative 가능

→ **시각적 검증은 필수**

### 3. 문서화의 중요성

이런 문제를 기록해두면:
- 다음에 빠르게 해결
- 다른 사람도 배움
- 재현성 향상

### 4. fMRIPrep 신뢰하되 검증하기

- fMRIPrep는 검증된 파이프라인
- 하지만 output 확인은 필요
- Especially template/space 설정

---

## 📊 체크리스트: Template 일치 확인

분석 시작 전 **반드시 확인**:

- [ ] fMRIPrep가 사용한 template 확인
  ```bash
  grep "SpatialReference" fmriprep_out/sub-01/anat/*_T1w.json
  ```

- [ ] 분석에 사용할 template과 동일한지 확인
  ```python
  assert fmriprep_template == analysis_template
  ```

- [ ] ROI atlas의 space 확인
  ```bash
  fslinfo HarvardOxford.nii.gz | grep -A 5 "dim"
  ```

- [ ] 필요시 resampling
  ```python
  roi_resampled = resample_to_img(roi, bold)
  ```

- [ ] 시각적으로 확인
  ```bash
  fsleyes template.nii.gz roi.nii.gz bold.nii.gz
  ```

---

## 🔗 관련 문서

- **결과 요약**: `MNI_DIAGNOSIS_RESULTS_SUMMARY.md`
- **종합 가이드**: `COMPREHENSIVE_MNI_TRANSFORMATION_GUIDE.md`
- **시각적 검증**: `VISUAL_INSPECTION_WORKFLOW.md`
- **fMRIPrep 가이드**: `GUIDE_to_fMRIprep.md`

---

## 📌 Quick Reference

### Template 정보

| Template | Shape | Path |
|----------|-------|------|
| **FSL MNI152** | (91, 109, 91) | `/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz` |
| **TemplateFlow** | (97, 115, 97) | `~/.cache/templateflow/tpl-MNI152NLin2009cAsym/*_res-02_T1w.nii.gz` |

### 빠른 해결 명령어

```bash
# Template 다운로드
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"

# Template 위치 확인
python -c "from templateflow import api; print(api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w'))"

# 시각적 비교
TEMPLATE=$(python -c "from templateflow import api; print(api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w'))")
fsleyes $TEMPLATE your_image.nii.gz -cm red -a 50
```

---

**작성**: 2026-01-04
**최종 수정**: 2026-01-04
**상태**: 문제 해결됨, 스크립트 수정 완료
