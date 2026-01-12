# 실행 가이드: 업로드, 실행, 로그/결과 위치

**날짜**: 2026-01-11

---

## 📤 1. 업로드

```bash
# 로컬 터미널
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts

scp 02_trial_wise_glm_optimized.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/

scp test_02_sub01_V1_optimized.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/
```

---

## 🚀 2. 실행

```bash
# 서버 접속
ssh haba6030@node2

# 작업 제출
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts
sbatch test_02_sub01_V1_optimized.sbatch

# 출력: Submitted batch job 123456
```

---

## 📊 3. 상태 확인

```bash
# 작업 상태
squeue -u haba6030

# 실시간 로그
tail -f /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_opt_sub01_V1_*.out
```

---

## 📁 4. 로그 위치 (서버)

```
/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/
├── test_trial_glm_opt_sub01_V1_123456.out  ← 메인 로그
└── test_trial_glm_opt_sub01_V1_123456.err  ← 에러 로그
```

### 로그 확인

```bash
# 전체 로그
cat logs/test_trial_glm_opt_sub01_V1_*.out

# RDM reliability만
grep -A 5 "RDM-based split-half" logs/*.out

# Data quality만
grep -A 10 "Data Quality Warnings" logs/*.out
```

---

## 📦 5. 결과 위치 (서버)

```
/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/
└── sub-01_V1/
    ├── trial_betas.npy          ← Beta values (n_trials, n_voxels)
    ├── trial_metadata.csv       ← Trial info (run, color, onset, etc)
    └── quality_metrics.json     ← Quality metrics (RDM r, recovery rate, warnings)
```

### 결과 확인

```bash
# 디렉토리 확인
ls -lh /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/sub-01_V1/

# JSON 내용 확인
cat results/trial_wise_glm/original_v3/sub-01_V1/quality_metrics.json | python -m json.tool

# CSV 확인
head -20 results/trial_wise_glm/original_v3/sub-01_V1/trial_metadata.csv
```

---

## ⚙️ 6. 설정(Config) 위치

### SBATCH 설정 (서버)

**파일**: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/test_02_sub01_V1_optimized.sbatch`

```bash
#SBATCH --qos=shared
#SBATCH --nodelist=node4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
```

### Python 기본 설정

**파일**: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/02_trial_wise_glm_optimized.py`

```python
# 데이터 경로
fmriprep_dir = '/storage/connectome/haba6030/fmriprep_out_original_v3'
bids_dir = '/storage/connectome/haba6030/bids_editted'
output_dir = '/scratch/.../results/trial_wise_glm'

# 분석 파라미터
smoothing_fwhm = 0.0  # Phase 0와 일치
confounds_strategy = 'motion'

# 품질 기준
MIN_TRIALS_PER_SPLIT = 3  # RDM 최소 threshold
EXPECTED_TOTAL_TRIALS = 432
```

---

## 📥 7. 결과 다운로드 (로컬로)

```bash
# 로컬 터미널
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace

# 결과 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/sub-01_V1/* \
    results/trial_wise_glm/original_v3/sub-01_V1/

# 로그 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_opt_sub01_V1_*.out \
    logs/
```

### 로컬에서 결과 분석

```python
import numpy as np
import pandas as pd
import json

# 결과 로딩
betas = np.load('results/trial_wise_glm/original_v3/sub-01_V1/trial_betas.npy')
metadata = pd.read_csv('results/trial_wise_glm/original_v3/sub-01_V1/trial_metadata.csv')

with open('results/trial_wise_glm/original_v3/sub-01_V1/quality_metrics.json') as f:
    metrics = json.load(f)

# 핵심 결과 확인
procrustes_stability = metrics['split_half_reliability']['mean']
rdm_r = metrics['rdm_reliability']['spearman_r']
recovery = metrics['data_quality']['recovery_rate']

print(f"Procrustes stability (PRIMARY): {procrustes_stability:.3f}")
print(f"RDM Spearman r (SECONDARY): {rdm_r:.3f}")
print(f"Trial recovery: {recovery*100:.1f}%")

if procrustes_stability >= 0.30:
    print("✅ GOOD or EXCELLENT - Proceed to full execution")
```

---

## 📋 빠른 참조

### 주요 경로 (서버)

| 항목 | 경로 |
|------|------|
| 스크립트 | `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/` |
| 로그 | `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/` |
| 결과 | `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/` |

### 주요 경로 (로컬)

| 항목 | 경로 |
|------|------|
| 스크립트 | `/Users/jinilkim/.../prediction_model_workspace/scripts/` |
| 결과 | `/Users/jinilkim/.../prediction_model_workspace/results/trial_wise_glm/original_v3/` |
| 로그 | `/Users/jinilkim/.../prediction_model_workspace/logs/` |

### 주요 명령어

```bash
# 업로드
scp local_file haba6030@node2:/scratch/.../scripts/

# 실행
sbatch script.sbatch

# 상태
squeue -u haba6030

# 로그
tail -f logs/*.out

# 다운로드
scp haba6030@node2:/scratch/.../results/* ./
```

---

## 🎯 핵심 확인 사항

### 로그에서 확인할 것

```bash
# Procrustes stability (PRIMARY - 핵심!)
grep "Procrustes stability (PRIMARY):" logs/*.out
# 예상: Procrustes stability (PRIMARY): 0.XXX

# RDM correlation (SECONDARY - 참고)
grep "RDM Spearman r (SECONDARY):" logs/*.out
# 예상: RDM Spearman r (SECONDARY): 0.XXX

# Trial recovery
grep "Total trials:" logs/*.out
# 예상: Total trials: 330/432 (76.4%)

# 품질 판단
grep "EXCELLENT\|GOOD\|MARGINAL\|POOR" logs/*.out
# 예상: ✅ EXCELLENT or ✅ GOOD or ⚠️ MARGINAL or ❌ POOR
```

### 성공 기준 (PRIMARY: Procrustes Stability)

- ✅ **Stability ≥ 0.50** → EXCELLENT, 즉시 전체 실행
- ✅ **0.30 ≤ Stability < 0.50** → GOOD, 전체 실행 진행
- ⚠️ **0.10 ≤ Stability < 0.30** → MARGINAL, 파라미터 조정 고려
- ❌ **Stability < 0.10** → POOR, 최적화 필요

**중요**: RDM correlation은 SECONDARY (국소적 진단용), 낮아도 Procrustes 높으면 OK!

---

**예상 시간**: 10-15분 (sub-01 V1 하나)
