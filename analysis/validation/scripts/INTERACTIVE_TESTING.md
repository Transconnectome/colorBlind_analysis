# Interactive Mode Testing Guide

Interactive mode에서 직접 Python을 실행하여 빠르게 테스트하고 최적화하는 가이드입니다.

---

## Quick Start

### 1. 파일 업로드

```bash
# Local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

scp -r utils sbatch evaluate_*.py test_*_interactive.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

### 2. Interactive Session 시작

```bash
# Server
ssh haba6030@node2

# Request interactive allocation
srun --qos=shared --nodelist=node2 --cpus-per-task=4 --mem=24G --time=02:00:00 --pty bash
```

### 3. 환경 설정

```bash
# Conda 환경 활성화
source /home/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate nilearn

# 작업 디렉토리 이동
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# 환경 확인
python --version
python -c "import numpy, scipy, sklearn; print('All imports OK')"
```

---

## Phase 1: Noise Ceiling Test

### Option A: 스크립트 실행 (추천)

```bash
# 실행 권한 부여
chmod +x test_phase1_interactive.sh

# 실행
./test_phase1_interactive.sh
```

**출력 예시:**
```
==================================================
Interactive Test: Phase 1 Noise Ceiling
==================================================

Test Configuration:
  Subject: sub-01
  ROI: V1
  Output: /scratch/.../INTERACTIVE_TEST_20260202_143022

Checking input files...
✓ Found: /scratch/.../amplitudes_raw.npy

Starting evaluation with profiling...

[... 진행 중 ...]

==================================================
Test Complete (Exit code: 0)
==================================================

Peak Memory Usage:
  14 GB used

✓ Results created successfully

Split-half reliability: 0.682
95% CI: [0.654, 0.708]
```

### Option B: 직접 Python 실행

```bash
# 간단한 테스트 (iterations 줄임)
/usr/bin/time -v python evaluate_with_noise_ceiling.py \
    --subject 01 \
    --roi V1 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline \
    --output_dir ./test_output_phase1 \
    --n_iterations 100 \
    --n_jobs 4
```

### Memory Monitoring (별도 터미널)

```bash
# 다른 터미널에서 실시간 모니터링
ssh haba6030@node2

# 메모리 사용량 watch
watch -n 2 'free -h && echo "---" && ps aux | grep evaluate_with_noise | grep -v grep | head -1'
```

---

## Phase 2: Whitening + SNR Test

### Option A: 스크립트 실행 (추천)

```bash
chmod +x test_phase2_interactive.sh
./test_phase2_interactive.sh
```

**출력 예시:**
```
==================================================
Interactive Test: Phase 2 Whitening + SNR
==================================================

Test Configuration:
  Subject: sub-01
  ROI: V1

Checking input files...
✓ Found: /scratch/.../amplitudes_raw.npy
  Shape: (6, 8, 487)
  Estimated covariance memory: 1.81 GB
⚠ Residuals not found (will estimate from data variance)

Starting evaluation...
This tests: Does whitening improve data quality (ceiling + SNR)?

[... 진행 중 ...]

==================================================
Test Complete (Exit code: 0)
==================================================

Peak Memory Usage:
  19 GB used, 430 GB free

✓ Results created successfully

=== Noise Ceiling ===
Raw:      0.682
Whitened: 0.854
Improvement: +25.2%

=== Pattern SNR ===
Raw:      1.24
Whitened: 3.08
Improvement: +148.4%

=== RDM Correlation ===
Raw:              0.187
Raw + Procrustes: 0.214
Whitened + Proc:  0.389
```

### Option B: 직접 Python 실행

```bash
# 직접 실행
/usr/bin/time -v python evaluate_whitening_ceiling_snr.py \
    --subject 01 \
    --roi V1 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline \
    --output_dir ./test_output_phase2 \
    --n_ceiling_iterations 1000 \
    --n_jobs 4 \
    --save_whitened_data
```

---

## 빠른 디버깅 테스트

### Minimal Test (빠른 검증용)

```bash
# Phase 1 - iterations 줄임
python evaluate_with_noise_ceiling.py \
    --subject 01 --roi V1 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline \
    --output_dir ./quick_test_nc \
    --n_iterations 10 \
    --n_jobs 2

# Phase 2 - iterations 줄임
python evaluate_whitening_ceiling_snr.py \
    --subject 01 --roi V1 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline \
    --output_dir ./quick_test_wh \
    --n_ceiling_iterations 10 \
    --n_jobs 2
```

**예상 실행 시간**: Phase 1 ~2분, Phase 2 ~5분

### Python Console에서 단계별 테스트

```bash
python
```

```python
import numpy as np
import sys
sys.path.append('/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts')

# Phase 1 functions test
from utils.noise_ceiling import compute_split_half_reliability

# Load data
baseline_dir = "/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline"
amp_file = f"{baseline_dir}/sub-01/V1/amplitudes_raw.npy"
amplitudes = np.load(amp_file)

print(f"Loaded amplitudes: {amplitudes.shape}")

# Quick test (10 iterations)
reliability, ci_lower, ci_upper, raw_r = compute_split_half_reliability(
    amplitudes, n_iterations=10, n_jobs=2
)

print(f"Split-half reliability: {reliability:.3f}")
print(f"95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

# Phase 2 functions test
from utils.whitening import estimate_noise_covariance, whiten_amplitudes

# Estimate noise covariance
cov, shrinkage = estimate_noise_covariance(amplitudes.reshape(-1, amplitudes.shape[-1]))
print(f"Covariance shape: {cov.shape}, Shrinkage: {shrinkage:.3f}")

# Apply whitening
whitened, W = whiten_amplitudes(amplitudes, cov)
print(f"Whitened shape: {whitened.shape}")

# Check if whitening worked
print(f"Original std: {amplitudes.std():.3f}")
print(f"Whitened std: {whitened.std():.3f}")
```

---

## Resource Profiling 분석

### 실행 후 리소스 로그 확인

```bash
# Peak memory 확인
tail -n +2 test_output/resource_usage.log | awk -F',' '{print $2}' | sort -n | tail -1
# 출력: 14 (GB)

# Memory timeline plot (간단한 텍스트 그래프)
tail -n +2 test_output/resource_usage.log | awk -F',' '{print $2}' | \
    awk '{printf "%s: "; for(i=0;i<$1;i++) printf "="; print ""}'

# /usr/bin/time -v 출력 확인
grep "Maximum resident set size" test_output/execution_profile.log
grep "Percent of CPU" test_output/execution_profile.log
grep "Elapsed" test_output/execution_profile.log
```

### Memory 계산기

```bash
# Array job 메모리 계산
PEAK_MEM_GB=14
SAFETY_MARGIN=1.3
CONCURRENT_JOBS=8

echo "Peak memory: ${PEAK_MEM_GB}GB"
RECOMMENDED_MEM=$(echo "scale=0; $PEAK_MEM_GB * $SAFETY_MARGIN / 1" | bc)
echo "Recommended --mem: ${RECOMMENDED_MEM}G"

TOTAL_MEM=$(echo "$RECOMMENDED_MEM * $CONCURRENT_JOBS" | bc)
echo "Total for ${CONCURRENT_JOBS} concurrent jobs: ${TOTAL_MEM}GB"

if [ $TOTAL_MEM -lt 360 ]; then
    echo "✓ Safe for node2 (< 360GB)"
else
    echo "⚠ Exceeds safe limit, reduce concurrent jobs"
    SAFE_CONCURRENT=$(echo "360 / $RECOMMENDED_MEM" | bc)
    echo "  Suggested concurrent: ${SAFE_CONCURRENT}"
fi
```

---

## Troubleshooting

### ImportError: No module named 'sklearn'

```bash
# Conda 환경 재확인
conda deactivate
conda activate nilearn
which python  # /home/haba6030/miniconda3/envs/nilearn/bin/python 이어야 함

# 패키지 재설치 (필요시)
pip install scikit-learn scipy numpy
```

### FileNotFoundError: Baseline amplitudes not found

```bash
# 파일 존재 확인
ls /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/sub-01/V1/amplitudes_raw.npy

# 경로 확인
echo $BASELINE_DIR

# 수동 검색
find /scratch/connectome/haba6030/colorBlind/derivatives -name "amplitudes_raw.npy" | grep "sub-01.*V1"
```

### Memory Error during covariance estimation

```python
# Covariance 크기 사전 확인
import numpy as np
data = np.load('amplitudes_raw.npy')
n_voxels = data.shape[-1]
cov_size_gb = n_voxels ** 2 * 8 / 1024**3
print(f"Covariance will need {cov_size_gb:.2f} GB")

# V1 ~500 voxels → ~2GB
# V2 ~800 voxels → ~5GB
# hV4 ~1500 voxels → ~18GB ⚠️
```

**해결책**: hV4 같은 큰 ROI는 더 많은 메모리 필요
```bash
# hV4 테스트할 때
srun --mem=32G --time=02:00:00 --pty bash
```

### Job hangs during split-half computation

```bash
# 다른 터미널에서 Python 프로세스 확인
ssh haba6030@node2
ps aux | grep python | grep evaluate

# CPU 사용률 확인
top -u haba6030

# 강제 종료 (필요시)
kill -9 <PID>
```

---

## 최적화 결과 정리

### Phase 1 Example Results

```
Test: sub-01, V1
Peak Memory: 14.2 GB
CPU Usage: 345%
Runtime: 18 minutes

Optimization:
  --mem=18G (was 20G, 30% margin)
  --cpus-per-task=4 (good utilization)
  --time=01:00:00 (was 02:00:00)
  --array=1-40%10 (was %8)
```

### Phase 2 Example Results

```
Test: sub-01, V1 (487 voxels)
Peak Memory: 19.3 GB
Covariance: 1.8 GB
CPU Usage: 280%
Runtime: 42 minutes

Optimization:
  --mem=26G (was 24G, 40% margin for larger ROIs)
  --cpus-per-task=4 (reasonable)
  --time=02:00:00 (was 03:00:00)
  --array=1-40%6 (safe)
```

---

## Next Steps

### 테스트 성공 후

1. **결과 확인**
   ```bash
   cat test_output_phase1/sub-01_V1_noise_ceiling.json
   cat test_output_phase2/sub-01_V1_whitening_results.json
   ```

2. **Array job 파라미터 업데이트**
   - `run_noise_ceiling_evaluation.sbatch` 수정
   - `run_whitening_ceiling_evaluation.sbatch` 수정

3. **전체 실행**
   ```bash
   sbatch sbatch/run_noise_ceiling_evaluation.sbatch
   sbatch sbatch/run_whitening_ceiling_evaluation.sbatch
   ```

### 추가 테스트 (optional)

다른 subject나 ROI로 테스트:
```bash
# 다른 ROI 테스트 (V2는 더 큼)
python evaluate_with_noise_ceiling.py --subject 01 --roi V2 --output_dir ./test_v2 --n_iterations 100 --n_jobs 4

# 다른 subject 테스트
python evaluate_with_noise_ceiling.py --subject 02 --roi V1 --output_dir ./test_sub02 --n_iterations 100 --n_jobs 4
```

---

**마지막 업데이트**: 2026-02-02
