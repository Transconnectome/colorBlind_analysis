---
name: generate-next-step
description: 다음 분석 단계의 Python 스크립트, SLURM sbatch, SCP 명령을 생성합니다. "다음 단계 생성", "create sbatch", "sbatch 만들어", "next analysis phase" 요청 시 사용.
---

# 다음 단계 생성 (generate-next-step)

## 목적

현재 파이프라인 위치를 파악하고, 다음 분석 단계에 필요한 SLURM-ready Python 스크립트 + sbatch 파일 + SCP 업로드 명령을 생성합니다.

---

## 파이프라인 순서

| 단계 | 디렉토리 | 설명 |
|------|----------|------|
| `prep_trials` | `analysis/prep_trials/` | fMRIPrep 후처리, 이벤트 파일 정리 |
| `phase1` | `analysis/phase1_preprocess_decoding/` | 전처리 + 디코딩 (Baseline32) |
| `phase2_SRM` | `analysis/phase2_SRM_across_between/` | SRM 기반 정렬 + 그룹 비교 |
| `phase2_procrustes` | (phase2 내) | Procrustes 정렬 + CVD-HC 비교 |
| `phase3` | `analysis/phase3_*/` | 필터 학습 |
| `future_phase1` | `analysis/future_phase1_hyperalignment/` | HC 공통 공간 (SRQ2) |
| `future_phase2` | `analysis/future_phase2_forward_model/` | 360° hue 인코더 (SRQ3) |
| `future_phase3` | `analysis/future_phase3_filter_optimization/` | CVD 필터 최적화 (SRQ4) |

---

## 동작 순서

1. **현재 위치 파악**: `analysis/` 내 각 phase 디렉토리의 결과 확인
2. **다음 단계 결정**: 결과가 없거나 미완성인 다음 phase 선택
3. **Python 스크립트 생성**: 분석 로직 + settings.json/results.json 저장
4. **sbatch 파일 생성**: SLURM 규칙 준수
5. **SCP 명령 생성**: 서버 업로드용 (node3 경로)
6. **실행 방법 안내**: 서버에서의 sbatch 제출 명령

---

## sbatch 템플릿 (CRITICAL - 반드시 준수)

### CPU 작업 (node2)
```bash
#!/bin/bash
#SBATCH --job-name={phase}_{description}
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# Array job (if needed)
#SBATCH --array=1-10%5

source ~/.bashrc
conda activate nilearn

export PYTHONUNBUFFERED=1

# Subject/ROI arrays
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# For array jobs
SUB_IDX=$((SLURM_ARRAY_TASK_ID - 1))
SUB=${SUBJECTS[$SUB_IDX]}

echo "=== Starting: sub-${SUB} ==="
echo "Time: $(date)"

python {script_name}.py --sub ${SUB}

EXIT_CODE=$?
echo "=== Finished: sub-${SUB} | Exit: ${EXIT_CODE} ==="
echo "Time: $(date)"
```

### GPU 작업 (node3)
```bash
#!/bin/bash
#SBATCH --job-name={phase}_{description}
#SBATCH --qos=shared_interactive
#SBATCH --nodelist=node3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

source ~/.bashrc
conda activate nilearn

export PYTHONUNBUFFERED=1
```

---

## SLURM 규칙 (절대 위반 금지)

- **node2 (CPU)**: `--qos=shared` 필수
- **node3 (GPU)**: `--qos=shared_interactive` 필수
- **절대 금지**: `--partition=` 어떤 값이든 지정 금지
- **Conda**: `source ~/.bashrc && conda activate nilearn`
- **서버에서 seaborn 사용 금지** → matplotlib만 사용

---

## 메모리 안전 공식

```
memory_per_task × max_concurrent ≤ available_memory × 0.8
```

| 노드 | 총 메모리 | 일반 가용 | 안전 한도 |
|------|----------|----------|----------|
| node2 | 502GB | ~450GB | 360GB |
| node4 | 514GB | ~176GB | 140GB |

---

## Python 스크립트 규칙

1. **경로**: `analysis/utils/output_paths.py` 사용하여 출력 경로 생성
2. **저장 형식**:
   - `settings.json`: 사용된 파라미터 기록
   - `results.json`: 결과 요약
3. **주요 경로**:
   ```python
   FMRIPREP_OUT = '/storage/connectome/haba6030/fmriprep_out_method3_header_mi'
   EVENT_DIR = '/storage/connectome/haba6030/bids_editted'
   DERIVATIVES = '/scratch/connectome/haba6030/colorBlind/derivatives'
   ```
4. **피험자 그룹**:
   ```python
   HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
   CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
   ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
   ```

---

## SCP 명령 규칙

- **서버**: `haba6030@node3:/scratch/connectome/haba6030/colorBlind/`
- 같은 목적지 파일은 **반드시** 하나의 scp로 합침
- 와일드카드 (`*.py`, `*.sbatch`) 활용
- 줄바꿈 없이 한 줄로 작성
- 목적지가 다를 때만 별도 scp 사용

```bash
# 예시: phase2 파일 업로드
scp analysis/phase2_SRM_across_between/{script.py,run.sbatch} haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/
```

---

## 출력 예시

스킬 실행 시 다음 3개를 순서대로 생성:

1. **Python 스크립트** (`analysis/{phase}/{script_name}.py`)
2. **sbatch 파일** (`analysis/{phase}/run_{name}.sbatch`)
3. **SCP 명령** (복사-붙여넣기용)
4. **서버 실행 명령** (`sbatch run_{name}.sbatch`)
5. **결과 다운로드 명령** (완료 후)

---

## 체크리스트

- [ ] `--partition=` 없는지 확인
- [ ] 올바른 `--qos=` 설정 확인
- [ ] `source ~/.bashrc && conda activate nilearn` 포함
- [ ] `PYTHONUNBUFFERED=1` 설정
- [ ] 메모리 공식 만족
- [ ] settings.json + results.json 저장 코드 포함
- [ ] seaborn 미사용 확인
- [ ] SCP 명령 줄바꿈 없음
