# Server Execution Guide for Group-Level Options
# 서버 실행 가이드

**Date:** 2025-12-17
**Server:** node2 (haba6030@node2:/scratch/connectome/haba6030/colorBlind)

---

## 📋 준비물 체크리스트

- [x] Python 스크립트 3개 (`option1_*.py`, `option2_*.py`, `option3_*.py`)
- [x] SLURM sbatch 파일 5개
- [x] baseline81 데이터 (서버에 있어야 함)
- [x] conda 환경 (nilearn)
- [ ] BrainIAK 패키지 (Option 2 필요 시 자동 설치됨)

---

## 🚀 실행 순서 (권장)

### Step 0: 파일 업로드

```bash
# 로컬 터미널에서 (Mac/Linux)

# 1. Python 스크립트 업로드
scp analysis/group_level/option1_within_subject_reliability.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

scp analysis/group_level/option2_srm_analysis.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

scp analysis/group_level/option3_supersubject.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# 2. SLURM sbatch 파일 업로드
scp analysis/group_level/run_option*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# 또는 한 번에 업로드
scp analysis/group_level/option*.py analysis/group_level/run_option*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/
```

---

### Step 1: Option 1 (Within-Subject Reliability) 실행 ⭐⭐⭐

**필수 진단 - 가장 먼저 실행**

```bash
# 서버에 SSH 접속
ssh haba6030@node2

# 작업 디렉토리로 이동
cd /scratch/connectome/haba6030/colorBlind

# 로그 디렉토리 생성 (없으면)
mkdir -p logs/group_level

# Job 제출
sbatch analysis/group_level/run_option1_reliability.sbatch

# Job 상태 확인
squeue -u haba6030

# 로그 실시간 확인
tail -f logs/group_level/option1_reliability_*.out
```

**예상 실행 시간**: 2-3시간

**확인할 것**:
```bash
# Job이 끝나면 결과 확인
ls -lh analysis/group_level/option1_results/baseline81_deob_determin/

# 요약 통계 확인
cat analysis/group_level/option1_results/baseline81_deob_determin/summary_statistics.txt

# 해석 가이드 확인
cat analysis/group_level/option1_results/baseline81_deob_determin/interpretation_guide.txt
```

**의사 결정**:
- **평균 reliability > 0.7**: ✅ Step 2로 진행
- **평균 reliability 0.5-0.7**: ⚠️ 신중하게 Step 2 진행
- **평균 reliability < 0.5**: ❌ 데이터 품질 문제, 전처리 재검토 필요

---

### Step 2A: Option 2 (SRM) 실행 ⭐⭐⭐

**조건**: Option 1 결과가 만족스러울 때 (r > 0.5)

```bash
# HC만 먼저 분석
sbatch analysis/group_level/run_option2_srm.sbatch

# Job 상태 확인
squeue -u haba6030

# 로그 실시간 확인
tail -f logs/group_level/option2_srm_*.out
```

**예상 실행 시간**: 2-3일 (ROI 크기에 따라)

**결과 확인**:
```bash
# 요약 확인
cat analysis/group_level/option2_results/baseline81_deob_determin/srm_analysis_summary.txt

# ROI별 결과 확인
ls -lh analysis/group_level/option2_results/baseline81_deob_determin/*/
```

**CVD 포함 분석** (선택적):
```bash
# HC 분석이 끝나고 만족스러우면 CVD 포함 버전 실행
sbatch analysis/group_level/run_option2_srm_with_cvd.sbatch
```

---

### Step 2B: Option 3 (Supersubject) 실행 ⭐⭐

**조건**: 비교 목적 또는 SRM 보완용

```bash
# HC만 먼저 분석
sbatch analysis/group_level/run_option3_supersubject.sbatch

# Job 상태 확인
squeue -u haba6030

# 로그 실시간 확인
tail -f logs/group_level/option3_supersubject_*.out
```

**예상 실행 시간**: ~1일

**결과 확인**:
```bash
# 요약 확인
cat analysis/group_level/option3_results/baseline81_deob_determin/supersubject_summary.txt

# ROI별 결과 확인
ls -lh analysis/group_level/option3_results/baseline81_deob_determin/*/
```

**CVD 포함 분석** (선택적):
```bash
sbatch analysis/group_level/run_option3_supersubject_with_cvd.sbatch
```

---

## 📥 결과 다운로드

### Option 1 결과 다운로드

```bash
# 로컬 터미널에서

# 전체 결과 디렉토리 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option1_results/baseline81_deob_determin \
    ./analysis/group_level/option1_results/

# 또는 요약 파일만
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option1_results/baseline81_deob_determin/*.txt \
    ./analysis/group_level/option1_results/baseline81_deob_determin/

# 시각화 파일
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option1_results/baseline81_deob_determin/*.png \
    ./analysis/group_level/option1_results/baseline81_deob_determin/
```

### Option 2 결과 다운로드

```bash
# 전체 결과 디렉토리
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option2_results/baseline81_deob_determin \
    ./analysis/group_level/option2_results/

# 요약 파일만
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option2_results/baseline81_deob_determin/srm_analysis_summary.txt \
    ./analysis/group_level/option2_results/baseline81_deob_determin/
```

### Option 3 결과 다운로드

```bash
# 전체 결과 디렉토리
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option3_results/baseline81_deob_determin \
    ./analysis/group_level/option3_results/

# 요약 파일만
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option3_results/baseline81_deob_determin/supersubject_summary.txt \
    ./analysis/group_level/option3_results/baseline81_deob_determin/
```

---

## 🔍 Job 모니터링

### Job 상태 확인

```bash
# 현재 실행 중인 job 확인
squeue -u haba6030

# 특정 job 상세 정보
scontrol show job <JOB_ID>

# Job 종료 후 정보 확인
sacct -j <JOB_ID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS
```

### 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/group_level/option1_reliability_<JOB_ID>.out

# 에러 로그 확인
tail -f logs/group_level/option1_reliability_<JOB_ID>.err

# 전체 로그 보기
less logs/group_level/option1_reliability_<JOB_ID>.out
```

### Job 취소

```bash
# Job 취소 (필요시)
scancel <JOB_ID>

# 모든 내 job 취소
scancel -u haba6030
```

---

## ⚙️ 환경 설정 (처음 한 번만)

### BrainIAK 설치 (Option 2 필요)

```bash
# 서버에서
ssh haba6030@node2
conda activate nilearn

# BrainIAK 설치
pip install brainiak

# 설치 확인
python -c "import brainiak; print(brainiak.__version__)"
```

**설치 실패 시**:
```bash
# Conda로 설치 시도
conda install -c brainiak -c defaults -c conda-forge brainiak
```

---

## 🐛 문제 해결 (Troubleshooting)

### 1. "No such file or directory: derivatives/BH2009_deoblique_v2/baseline81_deob_determin"

**원인**: 서버에 baseline81 데이터가 없음

**해결**:
```bash
# 서버에서 baseline81 결과 확인
ls /scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/

# baseline81_deob_determin 디렉토리가 있는지 확인
ls /scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline81_deob_determin/

# 없으면 baseline 분석을 먼저 실행해야 함
```

**또는 baseline32 사용**:
```bash
# sbatch 파일에서 timestamp 수정
sed -i 's/baseline81_deob_determin/baseline32_deob_determin/g' analysis/group_level/run_option1_reliability.sbatch
```

### 2. Memory Error (Out of Memory)

**원인**: 메모리 부족

**해결**:
```bash
# sbatch 파일에서 메모리 증가
#SBATCH --mem=64G  # 32G → 64G로 증가

# 또는 ROI를 하나씩 분석
# Python 스크립트 실행 시 --rois 옵션 수정
python analysis/group_level/option1_within_subject_reliability.py \
    --rois V1  # 하나씩만
```

### 3. BrainIAK Import Error

**원인**: BrainIAK 미설치

**해결**:
```bash
# sbatch 파일에 자동 설치 로직이 있지만, 수동으로도 가능
conda activate nilearn
pip install brainiak
```

### 4. Job이 즉시 종료됨

**원인**: Python 스크립트 경로 오류 또는 권한 문제

**해결**:
```bash
# 스크립트 실행 권한 확인
ls -l analysis/group_level/option*.py

# 실행 권한 부여 (필요시)
chmod +x analysis/group_level/option*.py

# 에러 로그 확인
cat logs/group_level/option1_reliability_<JOB_ID>.err
```

### 5. "No module named 'brainiak'"

**원인**: conda 환경이 제대로 활성화되지 않음

**해결**:
```bash
# sbatch 파일의 conda 경로 확인 및 수정
# 현재 설정:
source /home/haba6030/miniconda3/etc/profile.d/conda.sh

# 본인의 conda 경로로 수정:
which conda  # 경로 확인
```

---

## 📊 예상 디스크 사용량

| 옵션 | 출력 크기 (추정) |
|------|-----------------|
| Option 1 | ~500MB (RDM 파일 + 시각화) |
| Option 2 | ~2GB (공유 공간 + 변환 행렬 + RDM) |
| Option 3 | ~1GB (Supersubject RDM + 시각화) |
| **Total** | ~3.5GB |

---

## 🎯 빠른 시작 (Quick Start)

```bash
# === 로컬에서 ===
# 1. 파일 업로드
scp analysis/group_level/option*.py analysis/group_level/run_option*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

# === 서버에서 ===
# 2. SSH 접속
ssh haba6030@node2

# 3. 디렉토리 이동
cd /scratch/connectome/haba6030/colorBlind

# 4. 로그 디렉토리 생성
mkdir -p logs/group_level

# 5. Option 1 실행 (진단)
sbatch analysis/group_level/run_option1_reliability.sbatch

# 6. Job 확인
squeue -u haba6030
tail -f logs/group_level/option1_reliability_*.out

# 7. 결과 확인 (Job 종료 후)
cat analysis/group_level/option1_results/baseline81_deob_determin/interpretation_guide.txt

# 8. reliability > 0.5이면 Option 2 또는 3 실행
sbatch analysis/group_level/run_option2_srm.sbatch
# 또는
sbatch analysis/group_level/run_option3_supersubject.sbatch

# === 로컬에서 ===
# 9. 결과 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/option*_results \
    ./analysis/group_level/
```

---

## 📝 실행 로그 예시

### Option 1 성공 로그

```
================================================================
Option 1: Within-Subject Reliability Analysis
================================================================
Job ID: 123456
Node: node2
Start time: Mon Dec 17 10:00:00 KST 2025

Python path: /home/haba6030/miniconda3/envs/nilearn/bin/python
Python version: Python 3.9.7

Running Option 1: Within-Subject Reliability...

Processing sub-01...
  V1: (8, 8, 1000) (runs=8, colors=8, voxels=1000)
    Reliability: 0.756 (p=0.0001)
    Corrected: 0.861
  V2: (8, 8, 950) (runs=8, colors=8, voxels=950)
    Reliability: 0.682 (p=0.0005)
    Corrected: 0.811
  ...

Processing sub-02...
  ...

================================================================
SUMMARY STATISTICS
================================================================

Overall:
Mean reliability: 0.718 ± 0.089
Range: [0.542, 0.856]
Corrected mean: 0.836 ± 0.067

Significant pairs (p < 0.05): 24/24 (100.0%)

✓ Results saved to analysis/group_level/option1_results/baseline81_deob_determin
✓ Summary saved to summary_statistics.txt
✓ Interpretation guide saved to interpretation_guide.txt

================================================================
INTERPRETATION GUIDE
================================================================

✅ 전체 평가: 높은 피험자 내 신뢰도 (r > 0.7)

의미:
- 개별 피험자의 RDM이 매우 안정적입니다
- 피험자 간 낮은 일관성은 실제 개인차를 반영합니다 (노이즈 아님)
- 데이터 품질이 우수합니다

다음 단계:
✅ Option 2 (SRM) 진행 가능 - 공유 구조 찾기
✅ Option 3 (Supersubject) 진행 가능 - 그룹 수준 모델
✅ '개인차' 서사로 논문 작성 가능

================================================================
Job finished
Exit code: 0
End time: Mon Dec 17 12:30:00 KST 2025
================================================================
```

---

## ✅ Baseline32 vs Baseline81 - 최종 권장

### 🏆 Baseline81 사용 강력 권장

| 항목 | Baseline32 (4mm) | Baseline81 (6mm) |
|------|------------------|------------------|
| **노이즈** | 더 높음 | ✅ 11-48% 감소 |
| **안정성** | 보통 | ✅ 더 안정적 |
| **결론** | 동일 | 동일 (mean ~0) |
| **Publication** | 괜찮음 | ✅ 더 robust |

**이유**:
1. ✅ 더 낮은 노이즈 (higher smoothing)
2. ✅ 더 안정적인 추정
3. ✅ 같은 질적 결론
4. ✅ 논문 심사에서 더 안전

### Baseline32를 사용하려면:

모든 sbatch 파일에서 `baseline81_deob_determin`을 `baseline32_deob_determin`으로 변경:

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind/analysis/group_level

# 일괄 변경
sed -i 's/baseline81_deob_determin/baseline32_deob_determin/g' run_option*.sbatch

# 확인
grep "timestamp" run_option*.sbatch
```

**하지만 baseline81 사용을 강력히 권장합니다!** ⭐⭐⭐

---

## 📞 추가 도움

- **스크립트 주석**: 모든 Python 파일에 상세한 한국어 주석
- **사용 가이드**: `OPTIONS_USAGE_GUIDE.md` 참조
- **Baseline 비교**: `docs/BASELINE_COMPARISON_32vs81.md` 참조

**Happy analyzing! 성공적인 분석을 기원합니다!** 🎉
