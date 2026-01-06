# Preprocessing Methods Comparison: Execution Guide

**목적**: 4가지 registration 방법을 Sub-01, 03, 06에 실제 적용하고 Dice 비교

---

## Step 0: 사전 준비

### 로컬에서 서버로 파일 업로드

```bash
# 로컬 terminal에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# prep_trials 디렉토리 전체 업로드
scp -r analysis/prep_trials haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/

# 또는 스크립트만 업로드
scp analysis/prep_trials/scripts/*.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/
scp analysis/prep_trials/scripts/*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/
```

---

## Step 1: Method 1 Baseline 준비 (이미 있는 결과 활용)

### Option A: original_v3 결과에서 Dice만 계산

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials

# Activate conda environment
conda activate nilearn

# Method 1 Dice 계산 (original_v3 결과 사용)
for SUBJECT in 01 03 06; do
    for RUN in 1 2 3 4 5 6; do
        python scripts/compute_dice.py \
            --subject ${SUBJECT} \
            --method method1_flirt_bbr \
            --run ${RUN} \
            --base_dir /storage/connectome/haba6030/fmriprep_out_original_v3 \
            --output results/dice_method1_flirt_bbr.csv
    done
done
```

**Note**: original_v3 결과가 prep_trials 구조와 다를 수 있으므로 스크립트 수정 필요할 수 있습니다.

### Option B: Method 1도 prep_trials에서 재실행 (권장)

```bash
# Method 1 스크립트 생성 (original_v3와 동일, output만 prep_trials로)
# 이미 작성된 sbatch 파일 확인 후 제출
sbatch scripts/run_method1_flirt_bbr.sbatch  # (별도 작성 필요)
```

---

## Step 2: Method 2 실행 (Header → BBR)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials

# Submit SLURM job
sbatch scripts/run_method2_header_bbr.sbatch

# Check job status
squeue -u haba6030

# Monitor logs (실시간)
tail -f logs/method2_*.out

# 예상 시간: 3 subjects × 1 hour = ~3 hours
```

### Job 완료 후 Dice 계산

```bash
conda activate nilearn

for SUBJECT in 01 03 06; do
    for RUN in 1 2 3 4 5 6; do
        python scripts/compute_dice.py \
            --subject ${SUBJECT} \
            --method method2_header_bbr \
            --run ${RUN}
    done
done

# Check results
cat results/dice_method2_header_bbr.csv
```

---

## Step 3: Method 3 실행 (Header → MI)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials

# Submit SLURM job
sbatch scripts/run_method3_header_mi.sbatch

# Check job status
squeue -u haba6030

# Monitor logs
tail -f logs/method3_*.out

# 예상 시간: 3 subjects × 30 min = ~1.5 hours
```

### Job 완료 후 Dice 계산

```bash
conda activate nilearn

for SUBJECT in 01 03 06; do
    for RUN in 1 2 3 4 5 6; do
        python scripts/compute_dice.py \
            --subject ${SUBJECT} \
            --method method3_header_mi \
            --run ${RUN}
    done
done

# Check results
cat results/dice_method3_header_mi.csv
```

---

## Step 4: 중간 결과 확인

```bash
# Method 2, 3 결과 비교
conda activate nilearn

python scripts/compare_methods.py

# 결과 확인
cat results/comparison_report.md
open results/dice_comparison.png  # 로컬에서
```

### Method 2, 3 결과에 따른 결정:

```bash
# IF Method 2 성공 (Dice > 0.85):
#   → Method 4 (bbregister --no-pass1) 시도 가치 있음
#   → Header initialization 작동함

# IF Method 2 실패 (Dice < 0.80):
#   → Method 4 스킵
#   → Header initialization 부정확

# IF Method 3 최고 성능:
#   → 예상대로, 최종 권장
```

---

## Step 5 (조건부): Method 4 실행 (Header → BBR 1-pass)

**조건**: Method 2가 Dice > 0.85 달성 시에만

```bash
# Method 4 스크립트 작성 필요
# (현재 미작성, 필요 시 작성)

sbatch scripts/run_method4_header_bbr1pass.sbatch

# Dice 계산
for SUBJECT in 01 03 06; do
    for RUN in 1 2 3 4 5 6; do
        python scripts/compute_dice.py \
            --subject ${SUBJECT} \
            --method method4_header_bbr1pass \
            --run ${RUN}
    done
done
```

---

## Step 6: 최종 비교 및 시각화

### 모든 결과 다운로드 (로컬)

```bash
# 로컬 terminal에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials

# Results 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results ./

# Logs 다운로드 (optional)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs ./
```

### 최종 비교 분석

```bash
# 서버 또는 로컬에서 실행
python scripts/compare_methods.py

# Output:
#   results/dice_comparison.png      # 시각화
#   results/comparison_report.md     # 상세 보고서
```

### 결과 확인

```bash
# 보고서 읽기
cat results/comparison_report.md

# Plot 확인
open results/dice_comparison.png  # macOS
# 또는
eog results/dice_comparison.png   # Linux
```

---

## Step 7: 의사결정

### 시나리오별 권장사항

#### **Scenario 1: Method 3 (MI) 최고 성능**

```
예상 결과:
  Method 3 Mean Dice: 0.92-0.95
  Method 1 Mean Dice: 0.87
  Improvement: +0.05-0.08

의사결정:
  ✅ Method 3 (mri_coreg) 채택
  → Sub-06/07 포함 전체 10명 재실행 고려
  → 또는 Sub-06/07만 Method 3 사용
```

#### **Scenario 2: Method 2 (Header) 성공**

```
예상 결과:
  Method 2 Mean Dice: 0.88-0.90
  Method 1 Mean Dice: 0.87
  Improvement: +0.01-0.03

의사결정:
  ⚠️ 소폭 개선
  → 복잡도 대비 이득 작음
  → Method 1 유지 권장
```

#### **Scenario 3: 모든 방법 비슷**

```
예상 결과:
  All methods: Dice 0.87-0.89

의사결정:
  ✅ Method 1 (original_v3) 유지
  → 이미 충분히 좋음
  → 추가 preprocessing 불필요
  → 즉시 분석 시작
```

---

## Troubleshooting

### Method 2 실패 시

```bash
# Check logs
cat logs/method2_*.err

# Common issues:
#   1. Header qform/sform mismatch
#   2. BBR failed (insufficient WM boundary)
#   3. Memory issues

# Solution:
#   → Skip Method 4 (같은 원인으로 실패할 것)
```

### Method 3 실패 시

```bash
# Check logs
cat logs/method3_*.err

# Common issues:
#   1. FreeSurfer not available
#   2. ANTs not installed
#   3. MNI template path incorrect

# Solution:
#   → Check FreeSurfer/ANTs installation
#   → Update MNI_TEMPLATE path in script
```

### Dice computation 실패 시

```bash
# Check file structure
ls -R method2_header_bbr/sub-01/func/

# Expected files:
#   sub-01_task-rsvp_run-1_space-MNI*_desc-brain_mask.nii.gz

# If missing:
#   → Check fMRIPrep/processing logs
#   → Verify registration completed successfully
```

---

## 예상 소요 시간

| 단계 | 작업 | 시간 |
|------|------|------|
| 0 | 파일 업로드 | 5 min |
| 1 | Method 1 Dice 계산 | 10 min |
| 2 | Method 2 실행 + Dice | 3.5 hours |
| 3 | Method 3 실행 + Dice | 2 hours |
| 4 | 중간 비교 | 10 min |
| 5 | Method 4 (조건부) | 2 hours |
| 6 | 최종 비교 | 15 min |
| 7 | 의사결정 | - |

**총 예상 시간**:
- Method 2, 3만: ~6 hours
- Method 2, 3, 4 모두: ~8 hours

**병렬 실행 가능**:
- Method 2, 3을 동시에 실행하면 ~4 hours

---

## 다음 단계 (실험 완료 후)

### 1. 최종 방법 선택

```bash
# 가장 좋은 방법으로 전체 10명 재실행 (필요 시)
# 또는
# 문제 subjects (Sub-06/07)만 재실행
```

### 2. Gitignore 처리

```bash
# prep_trials는 대용량이므로 gitignore
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

echo "analysis/prep_trials/method*" >> .gitignore
echo "analysis/prep_trials/work_*" >> .gitignore
echo "analysis/prep_trials/logs/" >> .gitignore

# 하지만 scripts와 results는 커밋
git add analysis/prep_trials/scripts/
git add analysis/prep_trials/results/
git add analysis/prep_trials/README.md
git add analysis/prep_trials/EXECUTION_GUIDE.md
```

### 3. 결과 문서화

```bash
# Update preprocessing report
# 실험 결과 반영:
#   - 각 방법의 실제 Dice
#   - 최종 선택 이유
#   - Sub-06/07 해결책
```

---

**Status**: 준비 완료, 실행 시작 가능!
**First command**: `scp -r analysis/prep_trials haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/`
