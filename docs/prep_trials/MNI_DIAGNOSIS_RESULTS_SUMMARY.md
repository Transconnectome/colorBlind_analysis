# MNI Chain Diagnosis Results - Summary Report

**실행일**: 2026-01-04
**피험자**: sub-01 ~ sub-10 (전체 10명)
**진단 스크립트**: `diagnose_mni_chain.py`

---

## 🎯 Executive Summary

### 주요 발견사항

**⚠️ CRITICAL: Template 불일치 문제 발견**

모든 피험자(10/10)에서 동일한 패턴이 관찰됨:
- ❌ T1w → MNI: PROBLEM
- ❌ BOLD → MNI: PROBLEM
- ✅ Grid consistency: OK

**근본 원인**:
- 진단 스크립트가 **잘못된 MNI template**를 사용
- fMRIPrep는 `MNI152NLin2009cAsym`을 사용
- 진단 스크립트는 `FSL MNI152_T1_2mm.nii.gz`를 사용
- 두 템플릿은 **bounding box가 다름**

**실제 상태**:
- MNI 정합 자체는 정상일 가능성이 **매우 높음**
- BOLD ↔ T1w 간 Grid는 완벽히 일치 (✅)
- 단지 비교 템플릿이 잘못되어 false alarm 발생

---

## 📊 상세 결과

### 1. Template Shape 비교

| 이미지 | Shape | Voxel Size | Origin | 출처 |
|--------|-------|------------|--------|------|
| **FSL Template** | (91, 109, 91) | 2×2×2mm | (90, -126, -72) | `/usr/local/fsl/data/standard/` |
| **fMRIPrep T1w(MNI)** | (97, 115, 97) | 2×2×2mm | (-96.5, -132.5, -78.5) | `MNI152NLin2009cAsym` |
| **fMRIPrep BOLD(MNI)** | (97, 115, 97) | 2×2×2mm | (-96.5, -132.5, -78.5) | `MNI152NLin2009cAsym` |

**해석**:
- fMRIPrep 출력끼리는 **완벽히 일치** ✅
- FSL template과는 **bounding box가 다름** (6 voxels 차이)
- 하지만 **같은 MNI 공간** (voxel size 동일)

### 2. Affine Matrix 비교

#### FSL Template
```
[[  -2.    0.    0.   90.]
 [   0.    2.    0. -126.]
 [   0.    0.    2.  -72.]
 [   0.    0.    0.    1.]]
```

#### fMRIPrep Output (T1w, BOLD 동일)
```
[[   2.     0.     0.   -96.5]
 [   0.     2.     0.  -132.5]
 [   0.     0.     2.   -78.5]
 [   0.     0.     0.     1. ]]
```

**차이점**:
1. **X축 방향 반대** (sign flip)
   - FSL: -2 (RAS)
   - fMRIPrep: +2 (LAS)
2. **Origin 위치 다름**
   - 6.5mm 차이 (3 voxels 정도)

**참고**: MNI152NLin2009cAsym은 LAS+ orientation, FSL MNI는 RAS+ orientation

### 3. 피험자별 결과

| 피험자 | T1w→MNI | BOLD→MNI | Grid | 진단 |
|--------|---------|----------|------|------|
| sub-01 | ❌ | ❌ | ✅ | Template mismatch |
| sub-02 | ❌ | ❌ | ✅ | Template mismatch |
| sub-03 | ❌ | ❌ | ✅ | Template mismatch |
| sub-04 | ❌ | ❌ | ✅ | Template mismatch |
| sub-05 | ❌ | ❌ | ✅ | Template mismatch |
| sub-06 | ❌ | ❌ | ✅ | Template mismatch |
| sub-07 | ❌ | ❌ | ✅ | Template mismatch |
| sub-08 | ❌ | ❌ | ✅ | Template mismatch |
| sub-09 | ❌ | ❌ | ✅ | Template mismatch |
| sub-10 | ❌ | ❌ | ✅ | Template mismatch |

**패턴**:
- **100% 일관성** - 모든 피험자 동일한 결과
- Grid consistency ✅ → fMRIPrep 내부 정합은 정상
- Template mismatch → 비교 대상 문제

---

## 🔍 근본 원인 분석

### Template 불일치의 배경

#### MNI152 Template 종류

MNI152 템플릿에는 여러 버전이 있음:

1. **MNI152 (FSL)**
   - 경로: `/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz`
   - Shape: (91, 109, 91)
   - Orientation: RAS+
   - 용도: FSL 기본 템플릿

2. **MNI152NLin2009cAsym (TemplateFlow)**
   - 경로: `~/.cache/templateflow/tpl-MNI152NLin2009cAsym/`
   - Shape: (97, 115, 97) @ 2mm
   - Orientation: LAS+
   - 용도: fMRIPrep, BIDS 표준

3. **MNI152NLin6Asym** (구버전)
   - fMRIPrep 이전 버전에서 사용
   - 현재는 deprecated

#### fMRIPrep가 MNI152NLin2009cAsym을 사용하는 이유

```bash
# fMRIPrep 명령어에서
--output-spaces MNI152NLin2009cAsym:res-2
```

- **BIDS 표준**: TemplateFlow가 BIDS 권장 템플릿
- **신경영상 연구 표준**: 최근 연구에서 널리 사용
- **더 나은 정규화**: Nonlinear 2009 버전이 더 정확

### 진단 스크립트의 Template 선택 문제

```python
# diagnose_mni_chain.py (line ~395)
template_dirs = [
    Path('/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'),  # ← 이게 먼저 선택됨!
    Path.home() / '.cache/templateflow/tpl-MNI152NLin2009cAsym/...'
]
```

**문제**:
- FSL template을 먼저 찾음
- 서버에 FSL이 설치되어 있어서 항상 FSL template 사용
- fMRIPrep가 사용한 template와 다름

---

## ✅ 해결 방안

### Option 1: 올바른 Template 사용하도록 스크립트 수정 (권장)

```python
# diagnose_mni_chain.py 수정
template_dirs = [
    # TemplateFlow를 우선순위로
    Path.home() / '.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz',
    # 또는 명시적 지정
    Path('/storage/connectome/haba6030/.cache/templateflow/...')
]
```

**장점**:
- 정확한 비교
- False alarm 제거

**단점**:
- 스크립트 재업로드 및 재실행 필요

### Option 2: 시각적 검증으로 직접 확인

올바른 template을 사용하여 수동 비교:

```bash
# 올바른 template 다운로드
TEMPLATE=~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz

# 또는 서버에서
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"

# 시각적 검증
fsleyes $TEMPLATE \
    fmriprep_out/sub-01/anat/*_space-MNI*_T1w.nii.gz -cm red -a 50
```

**장점**:
- 즉시 확인 가능
- 직접 눈으로 정합 품질 판단

**단점**:
- 피험자별 수동 작업 필요

### Option 3: 기존 분석 결과 신뢰

**근거**:
- fMRIPrep는 검증된 파이프라인
- Grid consistency ✅ → 내부 정합 정상
- 기존 baseline 분석이 이미 작동함

**판단 기준**:
- Baseline 분석에서 ROI extraction 성공
- Classification accuracy가 reasonable
- 시각화 결과가 정상

→ **MNI 정합은 실제로 정상일 가능성 높음**

---

## 📝 권장 조치

### 즉시 조치 (필수)

1. **올바른 Template 확인**
   ```bash
   # 서버에서
   python -c "from templateflow import api; print(api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w'))"
   ```

2. **시각적 검증 (샘플링)**
   - 최소 3명 피험자 (sub-01, sub-04, sub-08) 시각 검증
   - 정상이면 나머지도 정상으로 간주

3. **문서 업데이트**
   - 이 리포트를 문제 해결 가이드에 추가
   - Template 불일치 case 추가

### 선택적 조치

1. **스크립트 개선**
   - Template auto-detection 개선
   - fMRIPrep JSON에서 사용된 template 읽기
   ```python
   import json
   with open('sub-01_T1w.json') as f:
       metadata = json.load(f)
       template = metadata.get('TemplateSpace')
   ```

2. **재진단 실행**
   - 수정된 스크립트로 재실행
   - 올바른 template 사용 확인

---

## 🎯 결론

### 현재 상황

1. **False Alarm**:
   - 진단 결과 "❌ PROBLEM"은 **잘못된 template 비교** 때문
   - 실제 MNI 정합은 정상일 가능성 **매우 높음**

2. **증거**:
   - Grid consistency ✅ (100% 피험자)
   - fMRIPrep 검증된 파이프라인
   - Baseline 분석 성공적으로 작동

3. **필요 조치**:
   - 올바른 template으로 재확인 (시각적 검증)
   - 정상 확인 시 → 분석 진행 가능
   - 문제 발견 시 → 해당 피험자만 별도 처리

### Next Steps

**Immediate**:
```bash
# 1. Template 확인
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"

# 2. 샘플 피험자 시각 검증 (sub-01, sub-04, sub-08)
# - 다운로드 스크립트 실행
# - fsleyes로 확인

# 3. 정상이면 → 분석 진행
# 4. 문제 있으면 → 개별 진단
```

**중기**:
- 진단 스크립트 개선
- Template auto-detection 수정
- CI/CD에 template 확인 추가

---

## 📎 부록

### A. 사용된 파일 경로

```bash
# fMRIPrep Output
/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-*/

# 진단 스크립트가 사용한 Template (잘못됨)
/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz

# 올바른 Template (사용했어야 함)
~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz
```

### B. 참고 문서

- fMRIPrep spaces: https://fmriprep.org/en/stable/spaces.html
- TemplateFlow: https://www.templateflow.org/
- MNI152NLin2009cAsym: https://www.templateflow.org/browse/tpl-MNI152NLin2009cAsym

### C. 관련 이슈

이 문제는 다른 분석 파이프라인에서도 흔히 발생:
- FSL과 fMRIPrep 간 template 차이
- ANTs와 SPM 간 orientation 차이
- 해결: 항상 **동일한 template** 사용

---

**작성자**: Claude Code
**최종 수정**: 2026-01-04
**상태**: Template 불일치 확인됨, 시각적 재검증 권장
