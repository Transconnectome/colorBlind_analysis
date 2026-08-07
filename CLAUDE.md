# CLAUDE.md — colorBlind_analysis

> 하위 폴더 작업 전 해당 폴더 `CLAUDE.md` 필독. 결과 수치의 single source of truth = `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`.

## What / Why
개인화 신경 기반 **inverse filter**로 CVD 피험자가 HC와 유사한 색 인지를 하게 만든다.
전제: post-cortical mapping HC=CVD → 차이는 (a) 망막 cone shift, (b) cortical opponent gain / stimulus dilation.
Subjects: HC sub-01~07 (N=7); CVD sub-08 deutan, sub-09 protan, sub-10 deutan.
**sub-10 = 전 분석 제외.** 사유 = **2차 실험(필터 검증 세션) 미통과**. 1차 세션 데이터는 존재하므로 `full_dataset_C010`을 비롯한 산출물에 sub-10이 남아 있고, 구 스크립트 상당수가 `CVD_SUBJECTS = sub-08..10`으로 하드코딩되어 있다.
→ **저장된 결과를 인용하기 전에 CVD n을 반드시 확인할 것.** n=3이면 sub-10 포함이므로 재산출하거나 제외 후 재계산해야 한다. 논문 수치는 전부 n=2 (sub-08, sub-09) 기준.

## Two Main Contributions (논문 헤드라인 — 초록/서론/결론 프레임의 축)
1. **CVD 피질 색 표상 기하 왜곡의 규명 (finding).** 개인 CVD의 피질 색 표상 기하는 선행연구에 미규명이었음(선행 = HC 대상, group-level: Brouwer&Heeger 2009, Kuriki 2015; CVD fMRI = magnitude/gain[Tregillus 2021]·activation[Rina 2024]). 본 연구: 균일 신호 감쇠(magnitude)가 **아니라**, 표시 색의 **범주변별은 보존**되나 색 간 **연속 hue 기하가 선택적으로 왜곡**되며 그 양상이 **개인마다 다름**(왜곡 ROI: deutan V2, protan V1).
2. **피질 기반 개인화 색교정 필터 프레임워크 (framework, first).** 개인 **자신의 피질 색 표상**에서 역산한 CVD 교정 필터 — 망막/스펙트럼 모델(EnChroma·Brettel·Machado·Daltonization)이 아님. 흐름: 왜곡을 2성분(S-cone축·confusion축 **hue rotation**)으로 모델링 → stimulus-space pre-image로 역산 → per-person 필터. **"first"의 정확한 스코프**: *피질 표상에서 역산한 CVD 필터*에 한정하며 "to our knowledge" 헤지 사용. LOCO/디코딩 자체는 first 아님(B&H가 HC LOCO 선행). Novelty 층위 = **필터 설계**이지 디코딩 방법이 아님.

## Pipeline (4 stages) — 현황
| Stage | 목적 | 코드 | 상태 |
|---|---|---|---|
| A | HC–CVD 신경차 (SRM/RDM/LOCO) | `phase1_procrustes_decoding`,`phase2_SRM_across_between`,`phase2_procrustes_cvd_hc`,`phase3_decoder_comparing`,`future_phase1_forward_model` | Complete |
| B+C | simulator 피팅 → stimulus-space 필터(pre-image) | **`future_phase2_filter_optimization`** | closure-ready |
| D | 필터 검증 (JND + fMRI, exp2) | `future_phase3_behavioral_analysis` | Planning (N=2) |

작업은 기본적으로 `future_phase2_filter_optimization/` 우선; 시작 전 그 폴더 CLAUDE.md(§0 Framework Decision) 정독.

## Data flow
raw `data/sub-*/` → fmriprep `derivatives/` → **C010 amplitudes** = 모든 하위 phase 입력:
`derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy` shape (6,8,n_vox). **ROI dir: hV4 = 디스크상 `V4`.**
trial_type `color_1..8` = red,orange,yellow,green,cyan,blue,purple,magenta (+blank).
자극 = **균일 색 원반**(grating 아님 — 스크립트 RadialStim은 런타임 미렌더); 논문·그림은 "uniform disc"로 기술.

## Canonical scripts
- Forward model: `future_phase1_forward_model/step_{a..d}_*.py`, `loco_canonical.py`
- SRM: `phase2_SRM_across_between/rerun_loo_consistent.py` (원복 금지)
- Filter fit: `future_phase2_filter_optimization/scripts/s10b_v6_pca_rdm.py` (v6 PCA canonical)
- PsychoPy exp: `~/…/OneDrive-Personal/Projects/colorBlind/colorBlind_test.py` (repo 밖)

## Naming & output
phase 폴더 `phase{N}_*`(frozen) / `future_phase{N}_*`(active) / `_archive`(폐기). 데이터셋 토큰 `C010`.
출력 flat, **timestamp 서브디렉토리 금지**(SLURM array 충돌), per-subject `sub-{ID}_*.json`, 배치당 `config.json` 1개.

## Env & gotchas
`conda activate srm`(local) / `nilearn`(server: node3 SSH·GPU / node2·node4 SLURM).
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
