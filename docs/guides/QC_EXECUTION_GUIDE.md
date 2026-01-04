# 🚀 QC 실행 가이드 - SLURM Array Job

**날짜**: 2026-01-04
**대상**: fMRIPrep original_v3 (--fs-no-reconall)
**Subject**: 10명 (01-10) 병렬 처리

---

## ⚡ 빠른 실행

### **1단계: 서버에 파일 업로드**

```bash
# 로컬에서
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp qc_runwise_improved.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_qc_all_subjects_array.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### **2단계: 서버에서 실행**

```bash
# 서버 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# SLURM array job 제출 (10명 병렬 처리)
sbatch run_qc_all_subjects_array.sbatch
```

**예상 출력:**
```
Submitted batch job 70XXX
```

### **3단계: 진행 상황 확인**

```bash
# Job 상태 확인
squeue -u haba6030

# 실시간 로그 확인 (예: Sub-01)
tail -f logs/qc_original_v3_70XXX_1.out

# 모든 subject 완료 확인
ls derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-*.tsv | wc -l
# 예상 출력: 10
```

### **4단계: 결과 다운로드**

```bash
# 로컬에서
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

mkdir -p derivatives/QC_new
scp "haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-*.tsv" derivatives/QC_new/

# 다운로드 확인
ls derivatives/QC_new/
```

### **5단계: 비교 분석**

```bash
# 로컬에서
python3 compare_fmriprep_versions.py "preps/qc_runwise_sub-*.tsv" "derivatives/QC_new/qc_runwise_sub-*.tsv"
```

---

## 📊 SLURM Array Job 특징

**장점:**
- ✅ **병렬 처리**: 10명을 동시에 처리 (기존 직렬보다 10배 빠름)
- ✅ **자동 재시도**: 개별 subject 실패 시 해당 subject만 재실행 가능
- ✅ **로그 분리**: 각 subject별 독립적인 로그 파일

**실행 시간 예상:**
- Subject당: 5-10분
- 전체 (병렬): 5-10분
- 기존 직렬 방식: 50-100분

---

## 🔍 트러블슈팅

### **문제 1: Job이 제출되지 않음**

```bash
# 원인: sbatch 파일 형식 문제
# 해결:
dos2unix run_qc_all_subjects_array.sbatch
chmod +x run_qc_all_subjects_array.sbatch
sbatch run_qc_all_subjects_array.sbatch
```

### **문제 2: 일부 subject만 완료됨**

```bash
# 확인: 어떤 subject가 실패했는지 확인
for i in {1..10}; do
    SUB=$(printf "%02d" $i)
    if [ -f "derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-${SUB}.tsv" ]; then
        echo "Sub-${SUB}: ✅"
    else
        echo "Sub-${SUB}: ❌"
    fi
done

# 실패한 subject의 로그 확인
cat logs/qc_original_v3_70XXX_4.err  # 예: Sub-04가 실패했을 때

# 개별 재실행 (예: Sub-04만)
bash qc_runwise_improved.sh 04
```

### **문제 3: "No BOLD files found" 에러**

```bash
# 원인: fMRIPrep 출력이 없음
# 확인:
ls /storage/connectome/haba6030/fmriprep_out_original_v3/sub-04/func/*_desc-preproc_bold.nii.gz

# 해당 subject의 fMRIPrep이 실패했는지 확인
cat logs/fmriprep_original_70168_4.out
```

---

## 📋 완료 후 체크리스트

```bash
# 1. 모든 subject QC 완료 확인
ls derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-*.tsv | wc -l
# 기대값: 10

# 2. 각 파일 크기 확인 (너무 작으면 에러 발생)
ls -lh derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-*.tsv
# 기대값: 각 파일 3-5KB

# 3. 간단한 통계 확인
for SUB in 01 02 03 04 05 06 07 08 09 10; do
    FILE="derivatives/QC_fmriprep_out_original_v3/qc_runwise_sub-${SUB}.tsv"
    if [ -f "$FILE" ]; then
        LINES=$(wc -l < "$FILE")
        echo "Sub-${SUB}: $((LINES-1)) measurements"
    fi
done
# 기대값: 각 subject 24 measurements (6 runs × 4 ROIs)
```

---

## 🎯 다음 단계

QC 완료 후 자동으로 다음 액션 제시됨:

```
IF Dice >= 0.85:
    ✅ 문제 해결됨
    → CLAUDE.md 업데이트
    → Baseline 분석 시작

ELIF Dice >= 0.70:
    ⚠️ 부분 개선
    → 좋은 subject 선택
    → 분석 진행

ELSE:
    ❌ 추가 진단 필요
    → check_transform_chain.sh 실행
    → Visual QC
```

---

## 📝 한 줄 요약

```bash
# 서버에서
sbatch run_qc_all_subjects_array.sbatch

# 로컬에서 (완료 후)
python3 compare_fmriprep_versions.py "preps/qc_*.tsv" "derivatives/QC_new/qc_*.tsv"
```

**예상 소요 시간**: 약 10분

---

**작성**: Claude Code
**최종 업데이트**: 2026-01-04
