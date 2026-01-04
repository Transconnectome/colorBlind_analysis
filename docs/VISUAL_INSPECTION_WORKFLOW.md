# Visual Inspection Workflow for MNI Chain

**목적**: fsleyes를 사용한 체계적 시각적 검증 워크플로우

---

## 🎯 빠른 시작

### 1단계: 필요한 파일 다운로드

```bash
#!/bin/bash
# download_for_visual_inspection.sh

SUBJECT="01"
SERVER="haba6030@node2"
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_deoblique_v2"

# Create local directory
mkdir -p visual_inspection/sub-${SUBJECT}/{anat,func}

# Download T1w MNI
scp "${SERVER}:${FMRIPREP_OUT}/sub-${SUBJECT}/anat/*space-MNI*T1w.nii.gz" \
    visual_inspection/sub-${SUBJECT}/anat/

# Download BOLD MNI (boldref)
scp "${SERVER}:${FMRIPREP_OUT}/sub-${SUBJECT}/func/*run-1*space-MNI*boldref.nii.gz" \
    visual_inspection/sub-${SUBJECT}/func/

echo "✅ Files downloaded to visual_inspection/sub-${SUBJECT}/"
```

### 2단계: Template 준비

```bash
# Check if template exists
TEMPLATE=~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz

if [ ! -f "$TEMPLATE" ]; then
    echo "Downloading template..."
    python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"
fi

echo "Template: $TEMPLATE"
```

### 3단계: 검증 실행

```bash
# Set paths
TEMPLATE=~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz
T1W=visual_inspection/sub-01/anat/*T1w.nii.gz
BOLD=visual_inspection/sub-01/func/*boldref.nii.gz

# Step A
fsleyes $TEMPLATE $T1W -cm red -a 50

# Step B
fsleyes $TEMPLATE $BOLD -cm blue -a 50

# Step C
fsleyes $T1W $BOLD -cm red -a 50
```

---

## 📋 상세 체크리스트

### Step A: T1w(MNI) vs MNI Template

**목표**: T1w → MNI normalization 품질 확인

#### View 1: Sagittal Midline (x=0)

```bash
fsleyes $TEMPLATE $T1W -cm red -a 50
# Navigate to x=0
```

**체크 포인트**:
```
[ ] Interhemispheric fissure가 정중선에 위치
[ ] Corpus callosum 좌우 대칭
[ ] Brainstem 중앙 정렬
[ ] Cerebellum vermis 중앙
```

**정상 예시**:
```
✅ GOOD:
Red overlay (T1w)가 gray template와 정확히 겹침
뇌 윤곽이 일치
Ventricles가 동일 위치

❌ BAD:
T1w가 회전되어 있음
좌우 비대칭
Corpus callosum 중심이 벗어남
```

#### View 2: Axial Ventricles (z=20)

```bash
# Navigate to z=20
```

**체크 포인트**:
```
[ ] Lateral ventricles 크기/모양 일치
[ ] 3rd ventricle 위치 정확
[ ] Caudate/putamen 위치 일치
[ ] Cortical ribbon 두께 유사
```

#### View 3: Coronal Occipital (y=-90)

```bash
# Navigate to y=-90 (occipital pole)
```

**체크 포인트**:
```
[ ] Occipital pole 정렬
[ ] Cerebellum 위치 일치
[ ] Inferior temporal cortex 정렬
```

**스크린샷 저장**:
- `screenshots/sub-01_StepA_sagittal_midline.png`
- `screenshots/sub-01_StepA_axial_ventricles.png`
- `screenshots/sub-01_StepA_coronal_occipital.png`

---

### Step B: BOLD(MNI) vs MNI Template

**목표**: BOLD → MNI 전체 체인 확인

#### View 1: Sagittal V1 Region (x=-20, x=20)

```bash
fsleyes $TEMPLATE $BOLD -cm blue -a 50
# Navigate to x=-20 (left V1), then x=20 (right V1)
```

**체크 포인트**:
```
[ ] Calcarine sulcus 위치 정확
[ ] Occipital pole에서 왜곡 없음
[ ] V1 예상 위치에 signal 존재
[ ] Coverage가 후두엽 포함
```

**일반적 문제**:
```
⚠️ WARNING SIGNS:
- 후두엽이 크게 이동 (SDC 미적용)
- Signal dropout in V1 (coverage 문제)
- 심한 geometric distortion
```

#### View 2: Axial Visual Cortex (z=-10)

```bash
# Navigate to z=-10
```

**체크 포인트**:
```
[ ] 양측 occipital cortex 대칭
[ ] Temporal lobes 정렬
[ ] EPI distortion 패턴 확인
[ ] Signal uniformity
```

#### View 3: Coronal Calcarine (y=-90 to y=-70)

```bash
# Scroll through y=-90 to y=-70
```

**체크 포인트**:
```
[ ] Calcarine sulcus 따라 signal 존재
[ ] Lingual gyrus 정렬
[ ] Cuneus 정렬
[ ] Fusiform gyrus coverage
```

**스크린샷 저장**:
- `screenshots/sub-01_StepB_sagittal_V1_left.png` (x=-20)
- `screenshots/sub-01_StepB_sagittal_V1_right.png` (x=20)
- `screenshots/sub-01_StepB_axial_visual.png` (z=-10)
- `screenshots/sub-01_StepB_coronal_calcarine.png` (y=-80)

---

### Step C: BOLD(MNI) vs T1w(MNI)

**목표**: Grid/resolution 일관성 확인

#### View 1: Sagittal Comparison (x=-20)

```bash
fsleyes $T1W $BOLD -cm red -a 50
# Navigate to x=-20
```

**체크 포인트**:
```
[ ] Gray-white matter boundary 일치
    (BOLD는 blocky하지만 위치는 동일해야 함)
[ ] Cortical ribbon 정렬
[ ] Subcortical structures 위치 일치
[ ] No systematic shift
```

**정상 vs 비정상**:
```
✅ NORMAL:
- BOLD is lower resolution (blocky)
- BUT structures align perfectly
- Same grid, different smoothness

❌ ABNORMAL:
- BOLD shifted relative to T1w
- Structures don't align
- Different grid/coordinate system
```

#### View 2: Axial Comparison (z=0)

```bash
# Navigate to z=0 (AC-PC line)
```

**체크 포인트**:
```
[ ] Anterior commissure 위치 일치
[ ] Posterior commissure 위치 일치
[ ] Thalamus/basal ganglia 정렬
[ ] CSF spaces 크기 유사
```

#### View 3: Coronal Comparison (y=-80)

```bash
# Navigate to y=-80 (visual cortex)
```

**체크 포인트**:
```
[ ] Calcarine sulcus depth 일치
[ ] White matter 경계 정렬
[ ] Voxel edges aligned
```

**스크린샷 저장**:
- `screenshots/sub-01_StepC_sagittal_comparison.png` (x=-20)
- `screenshots/sub-01_StepC_axial_comparison.png` (z=0)
- `screenshots/sub-01_StepC_coronal_comparison.png` (y=-80)

---

## 🎨 fsleyes 팁

### 유용한 설정

```bash
# Multiple overlays with different colors
fsleyes template.nii.gz \
        t1w.nii.gz -cm red -a 40 \
        bold.nii.gz -cm blue -a 30

# Edge detection
fsleyes template.nii.gz \
        t1w.nii.gz -ot mask

# Difference image
fsleyes template.nii.gz \
        difference.nii.gz -cm red-yellow -dr -100 100
```

### 단축키

| Key | Function |
|-----|----------|
| `Space` | Toggle overlay on/off |
| `←` `→` | Move slices |
| `↑` `↓` | Change overlay |
| `Ctrl + L` | Show location |
| `Ctrl + O` | Ortho view |
| `Ctrl + L` | Lightbox view |
| `Ctrl + S` | Screenshot |
| `Ctrl + B` | Brightness/contrast |

### 최적 Display 설정

```
Overlay settings:
  - Colormap: red (for overlay)
  - Alpha: 40-50%
  - Display range: Auto

View settings:
  - Cursor: Crosshair
  - Orientation labels: On
  - Show cursor location: On
```

---

## 📊 판정 기준

### Rating Scale

각 Step에 대해:

**✅ PASS (Good)**
- 모든 체크 포인트 통과
- 주요 구조물 정확히 일치
- Minor imperfections OK (< 1 voxel offset)

**⚠️ ACCEPTABLE (Borderline)**
- 대부분 체크 포인트 통과
- 약간의 misalignment (1-2 voxels)
- ROI 분석에는 문제 없을 것으로 예상

**❌ FAIL (Poor)**
- 다수 체크 포인트 실패
- 명확한 misalignment (> 2 voxels)
- 구조물 왜곡/이동
- ROI 분석 불가능

### Overall Decision

| Step A | Step B | Step C | Decision |
|--------|--------|--------|----------|
| ✅ | ✅ | ✅ | **PASS** - Ready for analysis |
| ⚠️ | ✅ | ✅ | **ACCEPTABLE** - Proceed with caution |
| ❌ | - | - | **FAIL** - T1w normalization issue |
| ✅ | ❌ | - | **FAIL** - BOLD registration issue |
| ✅ | ✅ | ❌ | **FAIL** - Grid inconsistency |

---

## 📝 리포트 작성

### 간단한 기록 템플릿

```markdown
## Visual Inspection Report: Sub-XX

**Date**: YYYY-MM-DD
**Inspector**: [Name]

### Step A: T1w vs Template
- Midline: ✅ / ⚠️ / ❌
- Ventricles: ✅ / ⚠️ / ❌
- Occipital: ✅ / ⚠️ / ❌
- **Overall**: ✅ PASS / ⚠️ ACCEPTABLE / ❌ FAIL
- Notes: [Any specific observations]

### Step B: BOLD vs Template
- V1 region: ✅ / ⚠️ / ❌
- Visual cortex: ✅ / ⚠️ / ❌
- Distortion: ✅ / ⚠️ / ❌
- **Overall**: ✅ PASS / ⚠️ ACCEPTABLE / ❌ FAIL
- Notes: [Any specific observations]

### Step C: BOLD vs T1w
- GM/WM boundaries: ✅ / ⚠️ / ❌
- Grid alignment: ✅ / ⚠️ / ❌
- No offset: ✅ / ⚠️ / ❌
- **Overall**: ✅ PASS / ⚠️ ACCEPTABLE / ❌ FAIL
- Notes: [Any specific observations]

### Final Decision
- [ ] ✅ PASS - Ready for ROI analysis
- [ ] ⚠️ ACCEPTABLE - Proceed with caution
- [ ] ❌ FAIL - Requires intervention

**Action**: [None / Re-run fMRIPrep / Exclude / Other]

**Screenshots**: See `screenshots/sub-XX_*.png`
```

---

## 🔄 Batch Processing

### 여러 피험자 검증

```bash
#!/bin/bash
# batch_visual_inspection.sh

SUBJECTS=(01 02 03 05 06 07 08 09 10)  # Excluding sub-04

for sub in "${SUBJECTS[@]}"; do
    echo "=== Processing sub-${sub} ==="

    # Download files
    ./download_for_visual_inspection.sh ${sub}

    # Open fsleyes for Step A
    echo "Step A: T1w vs Template"
    echo "Press Enter when done..."
    fsleyes $TEMPLATE visual_inspection/sub-${sub}/anat/*T1w.nii.gz -cm red -a 50
    read

    # Step B
    echo "Step B: BOLD vs Template"
    echo "Press Enter when done..."
    fsleyes $TEMPLATE visual_inspection/sub-${sub}/func/*boldref.nii.gz -cm blue -a 50
    read

    # Step C
    echo "Step C: BOLD vs T1w"
    echo "Press Enter when done..."
    fsleyes visual_inspection/sub-${sub}/anat/*T1w.nii.gz \
            visual_inspection/sub-${sub}/func/*boldref.nii.gz -cm red -a 50
    read

    echo "✅ sub-${sub} complete"
    echo ""
done

echo "All subjects completed!"
```

---

## 💡 문제 해결

### 일반적 이슈

**Q: Template을 찾을 수 없음**
```bash
A: TemplateFlow 설치 및 다운로드
pip install templateflow
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"
```

**Q: 이미지가 너무 어둡거나 밝음**
```
A: fsleyes에서 Ctrl+B로 brightness/contrast 조정
또는 Display range min/max 수동 설정
```

**Q: Overlay가 보이지 않음**
```
A:
1. Space 키로 toggle
2. Alpha를 50% 정도로 설정
3. Overlay가 선택되어 있는지 확인 (왼쪽 패널)
```

**Q: 좌표계가 이상함**
```
A: fsleyes는 자동으로 orientation 감지
   File → File information에서 header 확인
```

---

## 📚 참고 자료

- **MNI Template 정보**: https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009
- **FSLeyes 문서**: https://users.fmrib.ox.ac.uk/~paulmc/fsleyes/userdoc/latest/
- **fMRIPrep outputs**: https://fmriprep.org/en/stable/outputs.html

---

**END OF WORKFLOW GUIDE**

이 가이드를 따라 체계적으로 시각적 검증을 수행하세요.
