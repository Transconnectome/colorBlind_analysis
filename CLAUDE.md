# CLAUDE.md — colorBlind_analysis

> 하위 폴더 작업 전 해당 폴더 `CLAUDE.md` 필독. 결과 수치의 single source of truth = `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`.

## What / Why
개인화 신경 기반 **inverse filter**로 CVD 피험자가 HC와 유사한 색 인지를 하게 만든다.
전제: post-cortical mapping HC=CVD → 차이는 (a) 망막 cone shift, (b) cortical opponent gain / stimulus dilation.
Subjects: HC sub-01~07 (N=7); CVD sub-08 deutan, sub-09 protan, sub-10 deutan.
**sub-10 = 전 분석 제외.** 사유 = **2차 실험(필터 검증 세션) 미통과**. 1차 세션 데이터는 존재하므로 `full_dataset_C010`을 비롯한 산출물에 sub-10이 남아 있고, 구 스크립트 상당수가 `CVD_SUBJECTS = sub-08..10`으로 하드코딩되어 있다.
→ **저장된 결과를 인용하기 전에 CVD n을 반드시 확인할 것.** n=3이면 sub-10 포함이므로 재산출하거나 제외 후 재계산해야 한다. 논문 수치는 전부 n=2 (sub-08, sub-09) 기준.

## Two Main Contributions (논문 헤드라인 — 초록/서론/결론 프레임의 축) — **2026-09-02 개정**

> **개정 사유**: 전향적 신경 평가가 개인화를 지지하지 않고(deutan 기하는 두 필터 모두 HC 에서 멀어짐, protan hV4 보간은 개인화 필터가 세 조건 중 최하), disparity 는 대칭 LOSO 에서 16칸 중 1칸만 유의하다. 효능 주장과 왜곡 국재 주장을 철회하고 **방법 논문**으로 재배치한다. 전문 = `docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md` §0.7.

1. **범주 식별과 연속 보간의 해리 규명 (finding).** CVD 개인의 피질에서 **8색 범주 식별은 보존**되고 **같은 영역의 연속 hue 보간만 저하**된다. 두 측정이 **같은 복셀과 같은 런**에서 나오므로 신호 품질 저하로는 이 패턴이 설명되지 않는다. 통제군에서 hue 보간은 **hV4 단독**으로 성립하며 두 전처리 파이프라인에서 재현된다($p$ = .011 / .023). 선행 CVD fMRI 는 magnitude·gain(Tregillus 2021)·activation(Rina 2024)이고 이 해리를 보고한 바 없다. 선행 HC 연구(Brouwer&Heeger 2009, Kuriki 2015)는 group-level 이다.
   **주장하지 않는 것**: 왜곡의 피질 위치, 참가자별 국재, disparity 를 근거로 삼는 모든 서술. deutan 의 최대 편차 영역은 전처리에 따라 V2 ↔ V1 로 이동하고 V2 는 부호가 뒤집힌다.

2. **피질 기반 개인화 색교정 필터 프레임워크 (method, first).** 개인 **자신의 피질 색 표상**에서 역산한 CVD 교정 필터이며 망막·스펙트럼 모델(EnChroma·Brettel·Machado·Daltonization)이 아니다. 흐름: 왜곡을 2성분(S-cone축·confusion축 **hue rotation**)으로 모델링 → stimulus-space pre-image 로 역산 → per-person 필터.
   **"first" 의 스코프**: *피질 표상에서 역산한 CVD 필터*라는 **절차**에 한정하며 **효능을 포함하지 않는다.** "to our knowledge" 헤지를 쓴다. LOCO·디코딩 자체는 first 가 아니다(B&H 가 HC LOCO 선행).
   **N=2 전향 평가는 개념증명이고 결과는 혼재한다.** JND 는 개인화 필터에서 통제군 범위로 이동했고, 8AFC 는 deutan 에서 두 필터가 동등하며 protan 에서 배포필터만 저하시켰고, 신경 종점은 개선을 보이지 않았다. **효능 우위를 주장하지 않는다.**

## Pipeline (4 stages) — 현황
| Stage | 목적 | 코드 | 상태 |
|---|---|---|---|
| A | HC–CVD 신경차 (SRM/RDM/LOCO) | `phase1_procrustes_decoding`,`phase2_SRM_across_between`,`phase2_procrustes_cvd_hc`,`phase3_decoder_comparing`,`phase4_forward_model` | Complete |
| B+C | simulator 피팅 → stimulus-space 필터(pre-image) | **`phase5_filter_optimization`** | closure-ready |
| D | 필터 검증 (JND + fMRI, exp2) | `phase6_behavioral_analysis` | Complete (N=2) |
| E | **사후 분석** | `future_phase1_sensitivity`, `future_phase2_topology`, `future_phase3_geometry_synthesis` | Active |

**폴더 재편 2026-08-17**: `future_phase{1,2,3}_*` → `phase{4,5,6}_*` (본 파이프라인 완료), `phase4_topology` → `future_phase2_topology`, `future_phase4_geometry_synthesis` → `future_phase3_geometry_synthesis`. `future_phase*` 는 이제 **사후 분석 계층**을 뜻한다.
- `future_phase1_sensitivity` — 전처리 축 검정. 정리 문서 = 그 폴더 `README.md`, arm 스크립트·산출·그림 동봉

필터 관련 작업은 `phase5_filter_optimization/` 우선; 시작 전 그 폴더 CLAUDE.md(§0 Framework Decision) 정독. 전처리 강건성 관련은 `future_phase1_sensitivity/README.md` 정독.

## Data flow
raw `data/sub-*/` → fmriprep `derivatives/` → **C010 amplitudes** = 모든 하위 phase 입력:
`derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy` shape (6,8,n_vox). **ROI dir: hV4 = 디스크상 `V4`.**
trial_type `color_1..8` = red,orange,yellow,green,cyan,blue,purple,magenta (+blank).
자극 = **균일 색 원반**(grating 아님 — 스크립트 RadialStim은 런타임 미렌더); 논문·그림은 "uniform disc"로 기술.

## Canonical scripts
- Forward model: `phase4_forward_model/step_{a..d}_*.py`, `loco_canonical.py`
- SRM: `phase2_SRM_across_between/rerun_loo_consistent.py` (원복 금지)
- Filter fit: `phase5_filter_optimization/scripts/s10b_v6_pca_rdm.py` (v6 PCA canonical)
- PsychoPy exp: `~/…/OneDrive-Personal/Projects/colorBlind/colorBlind_test.py` (repo 밖)

## Naming & output
phase 폴더 `phase{N}_*`(본 파이프라인, frozen) / `future_phase{N}_*`(**사후 분석**, active) / `_archive`(폐기). 데이터셋 토큰 `C010`.
출력 flat, **timestamp 서브디렉토리 금지**(SLURM array 충돌), per-subject `sub-{ID}_*.json`, 배치당 `config.json` 1개.
**Figure captions**: NeuroImage 관례를 따라 **측정 대상·방법·기호·검정 방향만** 기술하고 결과 문장은 넣지 않는다. 전역 `~/.claude/writing/academic_writing_rules.md` §13("캡션은 takeaway를 진술")과 충돌하며, 이 프로젝트에서는 본 규칙이 우선한다.

## Env & gotchas
**서버 = `node1`** (`ssh node1`, 147.47.200.153). 작업폴더 `/scratch/connectome/haba6030/colorBlind`.
`ccsl1/2/3` 은 **이 프로젝트와 무관** — 쓰지 말 것. `connectome`(147.47.200.154)·`node3` 는 접속 불가한 때가 있으니 node1 우선.
서버 전용 데이터: `derivatives/full_dataset_C010_exp2{,_matched}`(exp2 amplitude)는 **로컬에 없음**.
**BrainIAK 는 로컬에도 있다 (0.12, `srm` 환경) — 2026-09-02 확인.** 종전 기록의 '서버 전용'은 사실이 아니었다. exp1 4개 arm 진폭(`full_dataset_C010_{with_residuals,motreg,motshift,hmc_v2}`)도 `analysis/phase1_procrustes_decoding/results/visualization/` 에 로컬로 있으므로, SRM·disparity 계열 재산출은 로컬에서 수 분이면 끝난다. 서버로 미루기 전에 로컬 가용성을 먼저 확인할 것.
`conda activate srm`(local) / `nilearn`(server: node2·node4 SLURM).
SLURM: `--partition`/`--qos` **금지**, `--chdir=<abs>` 필수, shell script **LF only**, 서버 seaborn 금지.
BrainIAK: `mpirun -np 1 python …` (bare python 금지). NotebookLM: 단일 `ColorBlind_comprehensive`만, 새 notebook **생성 금지**.

## Policy (필독)
**specificity claim 금지, selection-rule reformulation 금지.** Filter selection = subject별 LOCO-best
descriptive fit + behavioral validation. Specificity는 descriptive-only이지 selection criterion 아님.

## github-update rules

> 전역 `/github-update` skill이 이 섹션을 읽어 프로젝트별 차단/허용/커밋 규칙을 적용한다.
> (자동 commit/push 금지·`git add .` 금지·10MB 초과 차단은 skill의 불변 원칙)

**프로젝트 성격**: Neuroimaging (fMRI SRM) 분석

**차단 패턴 (절대 스테이징 금지):**
- `*.nii.gz` / `*.nii` — 뇌영상 데이터
- `*.npy` / `*.npz` — NumPy 배열
- `*.pkl` / `*.pickle` — 피클
- `derivatives/` — 분석 결과 디렉토리 전체
- `logs/*.out` / `logs/*.err` — SLURM 로그
- `results/full_dataset*` — 전체 데이터셋 결과
- `__pycache__/`

**허용 패턴 (스테이징 대상):**
- `*.py` (분석 스크립트), `*.sbatch` (SLURM), `*.sh` (셸)
- `*.md` (문서), `utils/` (유틸 모듈)
- `*.tex` (논문 소스, 특히 `docs/PAPER/`)
- `*.json` (10MB 미만), `.claude/skills/`

**커밋 prefix 표:**
| 변경 위치 | prefix | 예시 |
|---|---|---|
| `analysis/{phase}/*.py` | `phase{N}:` | `phase2: add permutation validation for SRM` |
| `*.sbatch` | `slurm:` | `slurm: update job configuration for node2` |
| `validation/` | `validation:` | `validation: add split-half ICC analysis` |
| `utils/` | `utils:` | `utils: update output_paths for phase3` |
| `*.md` 문서 | `docs:` | `docs: update METHODS_RESULTS_SUMMARY` |
| `docs/PAPER/**/*.tex` | `docs:` | `docs: fix encoding equation transpose in Methods` |
| `.claude/skills/` | `skills:` | `skills: add server-sync and slurm-monitor` |

---

## 🔴 커넥톰랩 랩서버 규칙 (node1~node4) — 예외 없음

이 규칙은 호스트명이 `node1`~`node4`이거나 경로가 `/scratch/connectome/` ·
`/storage/`인 환경에서 **항상** 적용된다.

### GPU는 Slurm으로만 실행한다
- ❌ 금지: 로그인 셸에서 `python train.py`, `python -c "...cuda..."`,
  `accelerate launch`, `torchrun`, `deepspeed`, `jupyter`, `ollama run` 등
  **GPU를 쓰는 명령을 직접 실행**하는 것. `CUDA_VISIBLE_DEVICES=0 python ...` 도 금지.
- ✅ 반드시 Slurm 경유:
  - 배치: `sbatch script.sh`
  - 대화형/디버깅: `srun --gres=gpu:1 --cpus-per-task=8 --mem-per-cpu=2G --pty bash -i`
- GPU가 필요한 코드를 실행해야 하면, **직접 실행하지 말고 sbatch 스크립트를 작성해서 제출**할 것.
  사용자가 "그냥 돌려봐"라고 해도 Slurm 경유로 바꿔서 제안한다.

### sbatch 스크립트 기본형
```bash
#!/bin/bash
#SBATCH --job-name=<이름>
#SBATCH --partition=debug        # 장시간 배치 기본값
#SBATCH --gres=gpu:2             # 1인 최대 4 (5개 이상은 preemptable로 자동 이동)
#SBATCH --cpus-per-task=24       # GPU 1개당 최대 12
#SBATCH --mem-per-cpu=3G         # CPU 1개당 최대 5G
#SBATCH --time=48:00:00
#SBATCH --output=./logs/%x_%j.out
#SBATCH --error=./logs/%x_%j.err
set -e
mkdir -p logs
source activate <env>
python train.py
```
--- 

## daily-checkin

> 전역 `daily-checkin` 스킬이 읽는 프로젝트 설정. (스킬 본문은 `~/.claude/skills/daily-checkin/SKILL.md`)

- **label**: colorblind
- **output**: `results/daily/`
- **sources** (우선순위 순, 전문 정독):
  - `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` — single source of truth (Phase 1/2/2b 결과, Pending Validations, Key Findings, Limitations)
  - `.claude/memory/project_brief.md`
  - `.claude/memory/repo_policy.md`
- **tasks_from**: `METHODS_RESULTS_SUMMARY_FOR_PAPER.md`의 **Pending Validations** 테이블 + **TODO (Next Steps)** 섹션에서 High priority 우선 top 3 추출.
- **focus** — `## Pipeline Status` 블록으로 렌더링:
  - Phase 1 (Preprocessing & Baseline): 완료/진행중 (N/M validations)
  - Phase 2 (SRM Between-Subject): 완료/진행중 (N/M)
  - Phase 2b (Decoder Model Comparison — LORO/LOCO): 완료/진행중 (N/M) — **Phase 2와 별개 섹션으로 반드시 표기**. LORO 6-model, LOCO interpolation, HC vs CVD, test-retest reliability 모두 여기 속함.
  - Phase 3 (Filter Optimization): Not started/진행중
  - Pending validations: 총 N (High H / Medium M / Low L)
- **notion_sync**: true — 저장 후 `sync_to_notion.py`(cron 9AM / LaunchAgent 8:30AM)가 자동 업로드. 전체 파이프라인: `bash ~/research_ops/run_daily_pipeline.sh --all`. 프로그램 방식 동일 출력: `python ~/research_ops/generate_project_daily.py --date YYYY-MM-DD`.
- **commit**: 사용자 판단 (Notion 동기화가 주 경로).
- **프로젝트 특이사항**:
  - 결과는 **Theme 단위 그룹핑**(예: SRM validation 1B/1C/2C/2D를 한 Theme으로) + Theme 서두 1–2줄 요약.
  - 각 작업에 **stats 테이블(실제 수치) + Interpretation** 포함.

