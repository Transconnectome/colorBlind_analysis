---
name: slurm-monitor
description: SLURM 작업 상태 확인 및 에러 진단을 수행합니다. "check job status", "작업 상태 확인", "debug SLURM error", "SLURM 에러", "job failed", "OOM error" 요청 시 사용.
---

# SLURM 모니터 (slurm-monitor)

## 목적

SLURM 작업 상태를 확인하고, 일반적인 에러를 진단하며, 해결 방법을 제시합니다.

---

## 상태 확인 명령

### 현재 작업 상태
```bash
# 내 작업 전체 확인
ssh haba6030@node3 "squeue -u haba6030"

# 특정 노드 작업 확인
ssh haba6030@node3 "squeue -w node2"
ssh haba6030@node3 "squeue -w node4"

# 특정 작업 상세 정보
ssh haba6030@node3 "sacct -j {JOB_ID} --format=JobID,JobName,State,ExitCode,MaxRSS,Elapsed"
```

### 메모리 확인
```bash
# 노드별 가용 메모리
ssh haba6030@node3 "free -h"
ssh haba6030@node3 "ssh node2 free -h"
ssh haba6030@node3 "ssh node4 free -h"
```

### 로그 확인
```bash
# 최근 출력 확인
ssh haba6030@node3 "tail -50 /scratch/connectome/haba6030/colorBlind/analysis/{phase}/logs/{job_name}_{jobid}.out"

# 에러 로그 확인
ssh haba6030@node3 "tail -50 /scratch/connectome/haba6030/colorBlind/analysis/{phase}/logs/{job_name}_{jobid}.err"

# 에러 키워드 검색
ssh haba6030@node3 "grep -i 'error\|oom\|killed\|failed' /scratch/connectome/haba6030/colorBlind/analysis/{phase}/logs/*.err"
```

---

## 에러 진단 카탈로그

### 1. OOM (Out of Memory)
**증상**: `slurmstepd: error: Detected 1 oom_kill event`
**원인**: 요청 메모리 초과
**해결**:
```bash
# 옵션 A: 메모리 증가
#SBATCH --mem=32G  # 16G → 32G

# 옵션 B: 동시 실행 수 감소
#SBATCH --array=1-10%3  # %5 → %3

# 확인: 총 메모리 = mem × concurrent ≤ available × 0.8
```

### 2. Invalid Partition
**증상**: `error: invalid partition specified`
**원인**: `--partition=` 줄 존재
**해결**: `--partition=` 줄을 **완전히 삭제**
```bash
# ❌ 절대 사용 금지
#SBATCH --partition=normal
#SBATCH --partition=shared

# ✅ partition 없이 qos만 지정
#SBATCH --qos=shared         # node2
#SBATCH --qos=shared_interactive  # node3
```

### 3. Wrong QOS
**증상**: `error: Unable to allocate resources`
**원인**: 노드-QOS 불일치
**해결**:
```
node2 → --qos=shared
node3 → --qos=shared_interactive
node4 → --qos=shared
```

### 4. Conda 에러
**증상**: `conda: command not found` 또는 `ModuleNotFoundError`
**원인**: conda 미활성화
**해결**:
```bash
# sbatch 파일에 반드시 포함
source ~/.bashrc
conda activate nilearn
```

### 5. Path Not Found
**증상**: `FileNotFoundError` 또는 `No such file or directory`
**원인**: 서버 경로 오류
**해결**:
```bash
# 올바른 기본 경로 확인
ls /scratch/connectome/haba6030/colorBlind/
ls /storage/connectome/haba6030/fmriprep_out_method3_header_mi/

# 로그 디렉토리 생성
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/{phase}/logs/
```

### 6. Seaborn Import 에러
**증상**: `ModuleNotFoundError: No module named 'seaborn'`
**원인**: 서버에 seaborn 미설치
**해결**: seaborn 코드를 matplotlib으로 교체
```python
# ❌ seaborn 사용 금지
import seaborn as sns
sns.heatmap(data)

# ✅ matplotlib 사용
import matplotlib.pyplot as plt
plt.imshow(data, cmap='RdBu_r')
plt.colorbar()
```

### 7. Job Pending (시작 안 됨)
**증상**: `squeue` 에서 STATE=PENDING
**원인**: 리소스 부족 또는 다른 작업 점유
**해결**:
```bash
# 대기 이유 확인
squeue -u haba6030 -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"

# 노드 상태 확인
sinfo -N -l

# 다른 노드로 전환 고려
```

---

## 제출 전 체크리스트

작업 제출 전 반드시 확인:

```bash
# 1. 가용 메모리 확인
ssh haba6030@node3 "ssh node2 free -h"

# 2. 현재 실행 중인 작업 확인
ssh haba6030@node3 "squeue -w node2"

# 3. 총 메모리 계산
# mem_per_task × max_concurrent ≤ available × 0.8

# 4. conda 테스트
ssh haba6030@node3 "source ~/.bashrc && conda activate nilearn && python -c 'import numpy; print(numpy.__version__)'"

# 5. 로그 디렉토리 존재 확인
ssh haba6030@node3 "ls /scratch/connectome/haba6030/colorBlind/analysis/{phase}/logs/ 2>/dev/null || echo 'logs dir missing - create it'"
```

---

## 동작 순서

1. **상태 확인**: `squeue` 로 현재 작업 상태 파악
2. **에러 감지**: 실패 작업의 로그 확인
3. **에러 분류**: 위 카탈로그에서 매칭
4. **해결 방안 제시**: 수정된 sbatch 또는 스크립트 제안
5. **재제출 명령 생성**: 수정 후 다시 실행할 명령

---

## 체크리스트

- [ ] SSH 접속은 node3 사용
- [ ] 에러 로그 확인함
- [ ] 에러 카탈로그와 매칭함
- [ ] 수정 방안 구체적으로 제시
- [ ] 메모리 공식 확인
