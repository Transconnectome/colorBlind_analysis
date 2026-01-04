# fMRIPrep Version Comparison Guide

**목적**: 여러 fMRIPrep 출력 버전의 MNI 정합 품질 비교

---

## 📋 비교 대상 버전

### Version 1: deoblique_v2 (현재 사용 중)

```bash
경로: /storage/connectome/haba6030/fmriprep_out_deoblique_v2
특징:
  - Deoblique 전처리 적용
  - Fieldmap 적용 (B0FieldIdentifier)
  - BBR registration (DOF 9)
  - Dummy scans 제거
상태: ✅ Baseline 분석 완료
용도: 현재 메인 분석
```

### Version 2: original_v3

```bash
경로: /storage/connectome/haba6030/fmriprep_out_original_v3
특징:
  - [확인 필요]
상태: 🔍 검증 필요
용도: 비교 분석
```

---

## 🚀 비교 실행 방법

### Step 1: 스크립트 업로드

```bash
# 로컬에서
scp run_mni_diagnosis_comparison.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp diagnose_mni_chain.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: 비교 실행

```bash
# 서버에서
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# 전체 피험자 비교
sbatch run_mni_diagnosis_comparison.sbatch

# 또는 샘플만
sbatch --array=1,4,8 run_mni_diagnosis_comparison.sbatch
```

### Step 3: 진행 모니터링

```bash
# 작업 상태
squeue -u haba6030 | grep mni_compare

# 실시간 로그
tail -f logs/mni_diagnosis/mni_compare_sub-1.out
```

### Step 4: 결과 다운로드

```bash
# 로컬에서
mkdir -p logs/mni_diagnosis_comparison

# 비교 요약 다운로드
scp 'haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/comparison_summary_sub-*.txt' \
    logs/mni_diagnosis_comparison/

# 전체 로그
scp 'haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/mni_compare_sub-*.out' \
    logs/mni_diagnosis_comparison/
```

---

## 📊 결과 분석

### 비교 요약 파일 구조

각 피험자당 생성되는 `comparison_summary_sub-XX.txt`:

```
========================================
MNI Chain Diagnosis - Version Comparison
========================================
Subject: sub-01
Date: ...

----------------------------------------
Version: deoblique_v2
----------------------------------------
Shape (T1w/BOLD):
   Shape:      (97, 115, 97)
   Shape:      (97, 115, 97)

Results:
T1w → MNI:        ✅ OK / ❌ PROBLEM
BOLD → MNI:       ✅ OK / ❌ PROBLEM
Grid consistency: ✅ OK / ❌ PROBLEM

----------------------------------------
Version: original_v3
----------------------------------------
[Same format]
```

### 비교 패턴 해석

| deoblique_v2 | original_v3 | 해석 |
|--------------|-------------|------|
| ✅✅✅ | ✅✅✅ | 둘 다 정상 - 어느 것이든 사용 가능 |
| ✅✅✅ | ❌-- | deoblique_v2가 더 나음 |
| ❌-- | ✅✅✅ | original_v3이 더 나음 |
| ❌-- | ❌-- | 둘 다 문제 - 시각적 검증 필요 |

**참고**: 현재는 FSL template 사용으로 인한 false alarm 가능성 있음

---

## 🔍 상세 비교 항목

### 1. Shape 비교

**기대값** (MNI152NLin2009cAsym res-2):
```
T1w:  (97, 115, 97)
BOLD: (97, 115, 97)
```

**다른 경우**:
- fMRIPrep 설정 차이
- 또는 다른 template 사용

### 2. Grid Consistency

**핵심 지표**:
```
BOLD(MNI) ↔ T1w(MNI) affine match: ✅ YES
```

**의미**:
- ✅ YES → ROI 분석 가능
- ❌ NO → Resolution/resampling 문제

### 3. 시각적 품질 (필요 시)

Shape/grid이 같아도 **정합 품질**은 다를 수 있음:
- Distortion 정도
- Alignment 정확도
- Coverage 범위

---

## 📈 비교 결과 활용

### Case 1: 둘 다 정상

**판단 기준**:
- Shape 동일
- Grid consistency ✅
- (시각적으로도 정상)

**선택**:
```python
# 다른 요소로 판단
if deoblique_v2_accuracy > original_v3_accuracy:
    use('deoblique_v2')  # Baseline 분석 결과 기준
elif original_v3_has_better_coverage:
    use('original_v3')
else:
    use('deoblique_v2')  # 현재 사용 중인 것 유지
```

### Case 2: 한쪽만 정상

**명확한 선택**:
```
✅ → 정상인 버전 사용
❌ → 문제 있는 버전 제외
```

### Case 3: 둘 다 문제 (unlikely)

**조치**:
1. 시각적 검증으로 실제 확인
2. fMRIPrep 로그 상세 분석
3. 필요 시 fMRIPrep 재실행

---

## 📝 Quick Commands

### 전체 요약 보기

```bash
# 모든 피험자 비교 결과
for sub in 01 02 03 04 05 06 07 08 09 10; do
    echo "=== sub-$sub ==="
    cat logs/mni_diagnosis_comparison/comparison_summary_sub-${sub#0}.txt 2>/dev/null || echo "  (Not found)"
    echo ""
done
```

### 특정 버전만 추출

```bash
# deoblique_v2 결과만
grep -A 10 "Version: deoblique_v2" logs/mni_diagnosis_comparison/comparison_summary_*.txt

# original_v3 결과만
grep -A 10 "Version: original_v3" logs/mni_diagnosis_comparison/comparison_summary_*.txt
```

### 차이점만 강조

```bash
# Grid consistency 비교
for sub in {01..10}; do
    echo "=== sub-$sub ==="
    grep "Grid consistency:" logs/mni_diagnosis_comparison/comparison_summary_sub-${sub#0}.txt
done
```

---

## ⚠️ 주의사항

### 주의 1: Template 불일치

현재 진단 스크립트는 FSL template 사용:
- **모든 버전이 ❌로 나올 수 있음**
- **Grid consistency ✅가 핵심 지표**
- 시각적 검증으로 최종 확인

### 주의 2: 버전 경로 확인

비교 전 두 경로 모두 존재 확인:

```bash
# 서버에서
ls -ld /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-01
ls -ld /storage/connectome/haba6030/fmriprep_out_original_v3/sub-01
```

### 주의 3: Sub-04 특수 케이스

sub-04는 두 버전 모두:
- MNI 정합은 OK일 수 있음
- 하지만 V1 signal dropout (데이터 자체 문제)
- 어느 버전을 써도 분석 불가

---

## 🎯 예상 시나리오

### 시나리오 A: deoblique_v2가 더 나음

**예상**:
- deoblique_v2: ✅✅✅
- original_v3: ❌ 또는 ⚠️

**이유**:
- Deoblique 전처리가 효과적
- Fieldmap 적용으로 distortion 개선

**조치**:
- deoblique_v2 계속 사용
- original_v3 참고용

### 시나리오 B: 둘 다 비슷함

**예상**:
- 둘 다 ✅✅✅
- Shape/grid 동일

**이유**:
- 전처리 차이가 MNI 정합에 영향 적음
- 둘 다 검증된 파이프라인

**조치**:
- Baseline 분석 결과로 선택
- 또는 현재 사용 중인 것 유지 (deoblique_v2)

### 시나리오 C: original_v3이 더 나음 (unlikely)

**예상**:
- original_v3: ✅✅✅
- deoblique_v2: ❌

**이유**:
- Deoblique가 오히려 artifact 유발?
- 또는 설정 차이

**조치**:
- 원인 분석
- 필요 시 original_v3으로 전환

---

## 📚 관련 문서

- `COMPREHENSIVE_MNI_TRANSFORMATION_GUIDE.md` - MNI 변환 종합 가이드
- `MNI_DIAGNOSIS_RESULTS_SUMMARY.md` - 진단 결과 요약
- `GUIDE_to_fMRIprep.md` - fMRIPrep 설정 가이드

---

## 💡 Tips

### Tip 1: 빠른 샘플링

전체 10명 비교 전에 **샘플 3명만** 먼저:

```bash
sbatch --array=1,5,8 run_mni_diagnosis_comparison.sbatch
# sub-01: Non-CVD
# sub-05: Non-CVD middle
# sub-08: CVD
```

패턴 파악 후 전체 실행 여부 결정

### Tip 2: 차이점 자동 검출

```bash
# Shape이 다른 피험자 찾기
for sub in {01..10}; do
    file="logs/mni_diagnosis_comparison/comparison_summary_sub-${sub#0}.txt"
    if [ -f "$file" ]; then
        shapes=$(grep "Shape:" $file | awk '{print $2}')
        unique_shapes=$(echo "$shapes" | sort -u | wc -l)
        if [ $unique_shapes -gt 1 ]; then
            echo "⚠️  sub-$sub: Different shapes detected"
        fi
    fi
done
```

### Tip 3: 시각적 비교 준비

차이가 의심되는 경우:

```bash
# 두 버전 모두 다운로드
mkdir -p visual_compare/sub-01/{v2,v3}

# deoblique_v2
scp 'haba6030@node2:/storage/.../fmriprep_out_deoblique_v2/sub-01/func/*boldref.nii.gz' \
    visual_compare/sub-01/v2/

# original_v3
scp 'haba6030@node2:/storage/.../fmriprep_out_original_v3/sub-01/func/*boldref.nii.gz' \
    visual_compare/sub-01/v3/

# 동시에 보기
fsleyes visual_compare/sub-01/v2/*boldref.nii.gz \
        visual_compare/sub-01/v3/*boldref.nii.gz
```

---

**작성**: 2026-01-04
**용도**: fMRIPrep 버전 간 MNI 정합 품질 비교
**상태**: 실행 준비 완료
