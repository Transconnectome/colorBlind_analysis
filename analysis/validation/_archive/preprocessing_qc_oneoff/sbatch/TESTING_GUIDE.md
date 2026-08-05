# Testing and Optimization Guide

이 가이드는 전체 array job 실행 전에 단일 job으로 리소스 사용량을 프로파일링하고 최적화하는 방법을 설명합니다.

## 워크플로우

```
1. Test single job → 2. Review profiling → 3. Optimize parameters → 4. Run array job
```

---

## Phase 1: Noise Ceiling Test

### 1단계: 테스트 실행

```bash
# 서버 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# 테스트 job 제출 (sub-01, V1 only)
sbatch sbatch/test_noise_ceiling.sbatch

# Job ID 확인
squeue -u haba6030
```

### 2단계: 실시간 모니터링

```bash
# 로그 실시간 확인
tail -f /scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_noise_ceiling_<JOB_ID>.out

# 다른 터미널에서 메모리 모니터링
watch -n 5 'squeue -u haba6030 -o "%.18i %.9P %.30j %.8u %.8T %.10M %.6D %.6C %.10m"'
```

### 3단계: 결과 확인

테스트 완료 후 로그에서 자동으로 표시되는 프로파일링 결과 확인:

```
PROFILING RESULTS
=================
Memory Usage:
  Maximum resident set size: XXXXXX kbytes
  Peak memory: XX.XX GB
  Recommended --mem: XXG (30% safety margin)

CPU Usage:
  Percent of CPU: XXX%
  Effective CPUs used: X.XX
  Recommendation: [...]

Runtime:
  Elapsed time: HH:MM:SS
  Estimated array job time (40 jobs, %8 parallel): X.X hours
```

### 4단계: 파라미터 최적화

프로파일링 결과에 따라 `run_noise_ceiling_evaluation.sbatch` 수정:

**시나리오 A: 메모리 여유 있음 (Peak < 16GB)**
```bash
#SBATCH --mem=16G              # 20G → 16G
#SBATCH --array=1-40%10        # %8 → %10 (병렬도 증가)
```

**시나리오 B: CPU 사용률 낮음 (< 200%)**
```bash
#SBATCH --cpus-per-task=2      # 4 → 2
# 그리고 Python 스크립트에서:
--n_jobs 2                      # 4 → 2
```

**시나리오 C: 실행 시간 짧음 (< 20분)**
```bash
#SBATCH --time=01:00:00        # 02:00:00 → 01:00:00
```

### 5단계: 전체 Array Job 실행

```bash
# 최적화된 설정으로 실행
sbatch sbatch/run_noise_ceiling_evaluation.sbatch

# 진행 상황 모니터링
watch -n 30 'squeue -u haba6030 | grep noise_ceiling'
```

---

## Phase 2: Whitening + SNR Test

### 1단계: 테스트 실행

```bash
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# 테스트 job 제출
sbatch sbatch/test_whitening.sbatch

# Job ID 확인
JOB_ID=$(squeue -u haba6030 -h -o "%i" | head -1)
echo "Job ID: $JOB_ID"
```

### 2단계: 실시간 모니터링

```bash
# 로그 실시간 확인
tail -f /scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_whitening_${JOB_ID}.out

# 메모리 사용량 집중 모니터링 (covariance estimation이 메모리 많이 씀)
watch -n 5 'free -h && echo "---" && squeue -u haba6030'
```

### 3단계: 결과 확인

프로파일링 결과 주요 지표:

```
PROFILING RESULTS
=================
Memory Usage:
  Peak memory: XX.XX GB
  Recommended --mem: XXG (40% safety margin for covariance)
  ⚠ WARNING: Memory usage close to 24GB limit!  # 이 경고 주의!

CPU Usage:
  Effective CPUs used: X.XX

Runtime:
  Elapsed time: HH:MM:SS
  Estimated array job time (40 jobs, %6 parallel): X.X hours
```

### 4단계: 파라미터 최적화

**시나리오 A: 메모리 부족 위험 (Peak > 20GB)**
```bash
#SBATCH --mem=32G              # 24G → 32G
#SBATCH --array=1-40%4         # %6 → %4 (병렬도 감소)
```

**시나리오 B: 메모리 여유 있음 (Peak < 18GB)**
```bash
#SBATCH --mem=20G              # 24G → 20G
#SBATCH --array=1-40%8         # %6 → %8 (병렬도 증가)
```

**시나리오 C: 실행 시간 매우 긺 (> 90분)**
```bash
#SBATCH --time=04:00:00        # 03:00:00 → 04:00:00
```

### 5단계: 전체 Array Job 실행

```bash
sbatch sbatch/run_whitening_ceiling_evaluation.sbatch

# 모니터링
watch -n 30 'squeue -u haba6030 | grep whitening'
```

---

## 최적화 의사결정 플로우차트

```
                           Test Job 실행
                                |
                                v
                      Peak Memory 확인
                                |
                    ┌───────────┴───────────┐
                    |                       |
               < 80% limit              > 80% limit
                    |                       |
              병렬도 증가 가능         ┌─────┴─────┐
                    |               메모리 증가  병렬도 감소
                    |                       |
                    └───────────┬───────────┘
                                v
                        CPU 사용률 확인
                                |
                    ┌───────────┴───────────┐
                    |                       |
              > 300% (good)            < 200% (low)
                    |                       |
              설정 유지               cpus-per-task 감소
                    |                       |
                    └───────────┬───────────┘
                                v
                        실행 시간 확인
                                |
                    ┌───────────┴───────────┐
                    |                       |
              < 50% time limit         > 80% time limit
                    |                       |
              time 감소                  time 증가
                    |                       |
                    └───────────┬───────────┘
                                v
                        최적화 완료!
                        Array Job 실행
```

---

## 리소스 제한 (Node2)

### 안전한 동시 실행 한도

| Phase | --mem per job | Safe %N | Max concurrent | Total RAM |
|-------|--------------|---------|----------------|-----------|
| Phase 1 (NC) | 16G | %12 | 12 | 192GB |
| Phase 1 (NC) | 20G | %10 | 10 | 200GB |
| Phase 2 (WH) | 20G | %8 | 8 | 160GB |
| Phase 2 (WH) | 24G | %6 | 6 | 144GB |
| Phase 2 (WH) | 32G | %4 | 4 | 128GB |

**Node2 안전 한도**: ~360GB (450GB free의 80%)

### 계산 공식

```bash
# 최대 병렬도 계산
MAX_PARALLEL = floor(360GB / MEM_PER_JOB)

# 예시:
# --mem=24G → MAX_PARALLEL = 15
# 하지만 실제로는 여유를 두고 %10 정도 사용 권장
```

---

## 트러블슈팅

### 문제 1: Out of Memory (OOM)

**증상**: Job이 중간에 종료되고 로그에 "Out of memory" 또는 "Killed"

**해결**:
```bash
# 1. Test job에서 peak memory 확인
grep "Maximum resident set size" <test_log>

# 2. 40% 여유를 두고 메모리 증가
# Peak 18GB → --mem=26G (18 × 1.4)

# 3. 병렬도 감소
#SBATCH --array=1-40%4  # 메모리 여유 확보
```

### 문제 2: Job Pending 오래 지속

**증상**: `squeue`에서 PENDING 상태가 계속됨

**원인**: 다른 job들이 메모리 사용 중

**해결**:
```bash
# 1. 현재 node 메모리 확인
ssh node2 free -h

# 2. 실행 중인 job 확인
squeue -w node2

# 3-1. 기다리기 (추천)
# 3-2. 병렬도 감소하여 재제출
scancel <JOB_ID>
# --array=1-40%4로 수정 후 재제출
```

### 문제 3: 실행 시간 초과 (Time Limit)

**증상**: Job이 time limit에 도달하여 종료

**해결**:
```bash
# 1. Test job runtime 확인
grep "Elapsed" <test_log>

# 2. 2× 여유를 두고 time 증가
# 실제 45분 → --time=02:00:00

# 3. 긴 job만 재실행
# 완료된 task 확인
sacct -j <ARRAY_JOB_ID> --format=JobID,State,Elapsed | grep COMPLETED

# 실패한 task만 재제출
sbatch --array=3,7,15,28 sbatch/run_whitening_ceiling_evaluation.sbatch
```

### 문제 4: Python Module Not Found

**증상**: `ModuleNotFoundError: No module named 'sklearn'`

**해결**:
```bash
# 1. 수동으로 conda 환경 테스트
conda activate nilearn
python -c "import sklearn; import scipy; import numpy; print('OK')"

# 2. Sbatch 스크립트의 conda 경로 확인
which conda
# 출력: /home/haba6030/miniconda3/bin/conda

# 3. Sbatch 스크립트 수정 (필요시)
source /home/haba6030/miniconda3/etc/profile.d/conda.sh
```

---

## 체크리스트

### 테스트 실행 전
- [ ] Baseline 결과 확인 (`amplitudes_raw.npy` 존재)
- [ ] 로그 디렉토리 생성됨
- [ ] Node2 메모리 충분 (`free -h` 확인)

### 테스트 실행 중
- [ ] Job이 RUNNING 상태로 변경됨
- [ ] 로그 파일에 출력 시작됨
- [ ] 메모리 사용량 모니터링 중

### 테스트 완료 후
- [ ] Exit code = 0 확인
- [ ] Profiling 결과 검토
- [ ] Peak memory 기록
- [ ] Runtime 기록
- [ ] Output 파일 생성 확인

### Array Job 실행 전
- [ ] Test 결과 기반으로 파라미터 최적화
- [ ] 메모리 계산: N × --mem ≤ 360GB
- [ ] Time limit 충분히 설정

---

## 예상 프로파일링 결과

### Phase 1 (Noise Ceiling)

**예상 리소스**:
- Memory: 12-16GB (split-half permutations)
- CPU: 300-350% (4 cores)
- Time: 15-25분

**최적 설정**:
```bash
#SBATCH --mem=20G
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --array=1-40%8
```

### Phase 2 (Whitening + SNR)

**예상 리소스**:
- Memory: 18-22GB (covariance: n_voxels × n_voxels)
- CPU: 250-300% (4 cores, Ledoit-Wolf is CPU-bound)
- Time: 30-50분

**최적 설정**:
```bash
#SBATCH --mem=24G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --array=1-40%6
```

---

## 추가 팁

### 빠른 재테스트

특정 파라미터만 변경하여 빠르게 재테스트:

```bash
# n_iterations 줄여서 빠르게 테스트
sbatch sbatch/test_noise_ceiling.sbatch
# 그 전에 스크립트에서 --n_iterations 1000 → 100 수정

# 또는 직접 실행 (interactive mode)
srun --qos=shared --nodelist=node2 --mem=20G --cpus-per-task=4 --time=01:00:00 --pty bash
conda activate nilearn
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts
/usr/bin/time -v python evaluate_with_noise_ceiling.py --subject 01 --roi V1 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline \
    --output_dir ./test_output --n_iterations 100 --n_jobs 4
```

### 로그 자동 분석

프로파일링 결과만 빠르게 추출:

```bash
# Peak memory
grep "Maximum resident set size" <log> | awk '{print $6/1024/1024 " GB"}'

# Runtime
grep "Elapsed" <log> | awk '{print $8}'

# CPU usage
grep "Percent of CPU" <log> | awk '{print $7}'
```

---

## 다음 단계

1. **Phase 1 Test** → Optimize → **Phase 1 Array**
2. **Phase 2 Test** → Optimize → **Phase 2 Array**
3. Download results and aggregate
4. Run Phase 3 (SRM) if needed

**마지막 업데이트**: 2026-02-02
