# MNI Registration Chain Diagnosis Guide

## 🎯 목적

MNI 정합 체인의 어느 링크가 문제인지 체계적으로 진단:

1. **T1w → MNI** 변환 검증
2. **BOLD → MNI** 변환 검증
3. **Grid/Affine 일관성** 검증

---

## 📋 작업 흐름

```
┌─────────────┐
│  진단 실행  │  → 수치적 검증 (affine, shape, voxel size)
└─────────────┘
       ↓
┌─────────────┐
│ 시각적 검증 │  → fsleyes로 실제 정합 확인
└─────────────┘
       ↓
┌─────────────┐
│  원인 판정  │  → 해석 매트릭스 기반 결론
└─────────────┘
```

---

## 🚀 사용 방법

### Option 1: 서버에서 직접 실행 (권장)

```bash
# SSH 접속
ssh haba6030@node2

# 작업 디렉토리 이동
cd /scratch/connectome/haba6030/colorBlind

# 스크립트 업로드 (로컬에서)
scp diagnose_mni_chain.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 진단 실행
conda activate nilearn
python diagnose_mni_chain.py \
    --subject 01 \
    --fmriprep-dir /storage/connectome/haba6030/fmriprep_out_deoblique_v2 \
    --run 1 \
    --output mni_diagnosis_sub-01.txt
```

### Option 2: 로컬에서 실행 (파일 다운로드 필요)

```bash
# 1. 필요한 파일 다운로드
mkdir -p temp_diagnosis/sub-01/anat temp_diagnosis/sub-01/func

# T1w MNI
scp 'haba6030@node2:/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-01/anat/*space-MNI*T1w.nii.gz' \
    temp_diagnosis/sub-01/anat/

# BOLD MNI (boldref)
scp 'haba6030@node2:/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-01/func/*run-1*space-MNI*boldref.nii.gz' \
    temp_diagnosis/sub-01/func/

# 2. 진단 실행
python diagnose_mni_chain.py \
    --subject 01 \
    --fmriprep-dir temp_diagnosis \
    --run 1
```

---

## 📊 출력 해석

### 수치적 검증 결과

스크립트는 다음을 자동 체크:

```
✅ Affine match: YES/NO
   → 변환 행렬이 동일한가?

✅ Shape match: YES/NO
   → 이미지 차원이 동일한가?

✅ Voxel size match: YES/NO
   → 복셀 크기가 동일한가?
```

### 해석 매트릭스

| T1w(MNI) | BOLD(MNI) | T1w↔BOLD | 진단 |
|----------|-----------|----------|------|
| ❌ | - | - | **T1w → MNI warp 문제** |
| ✅ | ❌ | - | **BOLD → T1w 또는 SDC 문제** |
| ✅ | ✅ | ❌ | **Grid/resolution 불일치** |
| ✅ | ✅ | ✅ | **MNI 체인 정상 → ROI 코드 재점검** |

---

## 🔍 시각적 검증 (Critical!)

### Step A: T1w(MNI) ↔ MNI Template

```bash
# 자동 생성된 명령어 사용 (mni_diagnosis_sub-01.txt 참조)
fsleyes $TEMPLATE $T1W_MNI -cm red -a 50
```

**확인 사항:**
- [ ] Midline 정렬
- [ ] Ventricles 위치
- [ ] 후두엽/소뇌 경계

### Step B: BOLD(MNI) ↔ MNI Template

```bash
fsleyes $TEMPLATE $BOLD_MNI -cm blue -a 50
```

**확인 사항:**
- [ ] 뇌 전체 위치
- [ ] 후두엽 위치 왜곡 여부
- [ ] 전반적 정합 품질

### Step C: BOLD(MNI) ↔ T1w(MNI)

```bash
fsleyes $T1W_MNI $BOLD_MNI -cm red -a 50
```

**확인 사항:**
- [ ] 회백질 경계 일치
- [ ] 상대적 위치 오프셋 없음
- [ ] 해상도 차이 확인

---

## 🛠️ 문제별 해결 방안

### Case 1: T1w → MNI 문제 (❌✅✅ 또는 ❌---)

**원인:**
- T1w skull-stripping 실패
- Template 불일치
- ANTs registration 파라미터 문제

**해결:**
```bash
# fMRIPrep 로그 확인
cat /storage/.../fmriprep_work_*/sub-01/anat_preproc_wf/anat_norm_wf/log.txt

# 사용된 template 확인
grep "template" /storage/.../sub-01/anat/*_T1w.json
```

### Case 2: BOLD → MNI 문제 (✅❌-)

**원인:**
- BOLD → T1w registration 실패
- SDC (susceptibility distortion correction) 문제
- Motion corruption

**해결:**
```bash
# BBR 로그 확인
cat /storage/.../bold_reg_wf/bbreg_wf/log.txt

# SDC 적용 여부 확인
grep "B0FieldSource" /storage/.../sub-01/func/*_bold.json
```

### Case 3: Grid 불일치 (✅✅❌)

**원인:**
- fMRIPrep resolution flag 불일치
- T1w와 BOLD가 다른 MNI grid 사용
- Resampling 파라미터 문제

**해결:**
```bash
# fMRIPrep 명령어 확인
cat run_fmriprep_*.sbatch

# --output-spaces 확인
# 예: MNI152NLin2009cAsym:res-2 (2mm isotropic)
```

### Case 4: 모두 정상 (✅✅✅)

**원인:**
- ROI atlas 자체 문제
- Analysis 코드의 resampling 오류
- ROI → MNI 변환 누락

**해결:**
```python
# ROI atlas 검증
from nilearn import datasets, plotting

atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
roi_img = atlas.maps

# Atlas와 BOLD(MNI)가 같은 공간인지 확인
print(roi_img.affine)
print(bold_mni_img.affine)
```

---

## 📝 체크리스트

분석 전 확인:

- [ ] fMRIPrep v2 출력 사용 중 (fieldmap 적용됨)
- [ ] `--output-spaces MNI152NLin2009cAsym:res-2` 설정
- [ ] T1w, BOLD 모두 MNI space 파일 존재
- [ ] Template 경로 확인 (templateflow cache)

진단 후 확인:

- [ ] 수치적 검증 완료
- [ ] fsleyes 시각적 검증 완료
- [ ] 원인 분류 완료
- [ ] 해결 방안 시도

---

## 🔗 관련 문서

- `GUIDE_to_fMRIprep.md` - fMRIPrep 설정 가이드
- `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md` - 이전 정합 진단 결과
- fMRIPrep docs: https://fmriprep.org/en/stable/outputs.html

---

## 💡 추가 팁

### 여러 피험자 일괄 진단

```bash
for sub in 01 02 03 04 05; do
    echo "=== sub-$sub ==="
    python diagnose_mni_chain.py \
        --subject $sub \
        --fmriprep-dir /storage/.../fmriprep_out_deoblique_v2 \
        --run 1 \
        --output mni_diagnosis_sub-${sub}.txt
done
```

### Template 다운로드 (로컬 실행 시)

```bash
# TemplateFlow 설치
pip install templateflow

# Template 다운로드
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w', desc=None)"
```

### FSLeyes 설치 (없는 경우)

```bash
conda install -c conda-forge fsleyes
# 또는
pip install fsleyes
```
