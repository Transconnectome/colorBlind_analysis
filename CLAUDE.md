# CLAUDE.md — colorBlind_analysis

## 1. Main Objective

개인화된 신경 기반 **inverse filter**로 CVD 피험자가 HC와 유사한 색 인지를 하도록 한다.

**전제**: post-cortical mapping은 HC = CVD 동일. 차이는 (a) 망막 cone shift, (b) cortical opponent gain 또는 stimulus-space dilation에서 발생.

## 2. Pipeline (4 stages)

| Stage | 목적 | 위치 |
|---|---|---|
| A | HC–CVD 신경 차이 측정 (V1→hV4, RDM, LOCO) | `phase1_procrustes_decoding`, `phase2_SRM_across_between`, `phase2_procrustes_cvd_hc`, `phase3_decoder_comparing` |
| B | CVD simulator 피팅 (cone + cortical) | **`future_phase2_filter_optimization`** |
| C | Inverse problem → stimulus-space 필터 (pre-image) | **`future_phase2_filter_optimization`** |
| D | 필터 검증 (JND + fMRI SRM/LOCO) | `future_phase3_behavioral_analysis` |

## 3. CURRENT FOCUS

**`future_phase2_filter_optimization/`** — 작업은 기본적으로 이 폴더를 우선 참조·수정한다. 작업 시작 전 다음 두 문서를 반드시 먼저 읽는다:

1. **`future_phase2_filter_optimization/CLAUDE.md`** — §0(Framework Decision), §2(Pipeline Assumptions), §3(Per-Subject Status), §8(Anti-Pattern) 순서로 확인. **specificity claim 금지, selection-rule reformulation 금지** 정책 명시됨.
2. **`future_phase2_filter_optimization/behav_validation.md`** — model class 결정의 ground truth. sub-08 2-component PASS / R+C FAIL 결정 사례.

**Filter selection rule** (전 프로젝트 공통): subject별 LOCO-best descriptive fit + behavioral validation. Specificity는 **descriptive only**, selection criterion이 아님.

## 4. Environment

```bash
conda activate nilearn   # server
conda activate srm       # local
```

Server: `haba6030@node3:/scratch/connectome/haba6030/colorBlind` (SSH/SCP = node3; SLURM = node2/node4).

## 5. SLURM (CRITICAL)

- **절대 지정 금지**: `--partition=*`, `--qos=*` (서버 기본값 사용).
- CPU: `--nodelist=node2`. GPU: `--nodelist=node3 --gres=gpu:1`.
- Shell scripts: **Unix LF only** (CRLF는 `invalid option` 에러).
- `--chdir=<absolute_path>` 필수.
- 서버에서 seaborn 사용 금지.
- scp는 동일 목적지끼리 wildcard로 묶어 2–3개 명령으로.

## 6. Data Paths & Subjects

**Subjects**: HC sub-01~07 (N=7), CVD sub-08 deutan, sub-09 protan, sub-10 deutan(mild/normal control).

**Server paths (method3_header_mi)**:
```
FMRIPREP_OUT=/storage/connectome/haba6030/fmriprep_out_method3_header_mi
EVENT_DIR=/storage/connectome/haba6030/bids_editted
DERIVATIVES=/scratch/connectome/haba6030/colorBlind/derivatives
```

**C010 amplitudes** (모든 하위 phase의 입력): `derivatives/full_dataset_C010/{subject}/{ROI_dir}/amplitudes_procrustes.npy`, shape `(6, 8, n_voxels)`. ROI dir: hV4 → **V4** on disk.

**trial_type**: `color_1`…`color_8` = red, orange, yellow, green, cyan, blue, purple, magenta. + `blank`.

## 7. Output Convention (CRITICAL)

- Flat structure — **timestamp 서브디렉토리 금지** (SLURM array 충돌).
- Per-subject: `sub-{ID}_*.json`. Batch-level: one `config.json` per output_dir.
- Grouping은 디렉토리 이름으로.

## 8. Subfolder Map

각 폴더의 `CLAUDE.md`를 작업 시작 전에 읽는다. 결과/수치는 해당 폴더의 `README.md`, `notion.md` 등에 있다.

| Dir | Stage | Status |
|---|:-:|---|
| `phase0_preprocessing/` | A | Frozen |
| `phase1_procrustes_decoding/` | A | Complete |
| `phase2_procrustes_cvd_hc/` | A | Complete |
| `phase2_SRM_across_between/` | A | Stabilized |
| `phase3_decoder_comparing/` | A | Complete |
| `future_phase1_forward_model/` | A→B bridge | Core complete |
| **`future_phase2_filter_optimization/`** | **B+C** | **ACTIVE** |
| `future_phase3_behavioral_analysis/` | D | Planning |

## 9. BrainIAK / SRM Note

BrainIAK은 mpi4py `MPI_Init_thread`를 호출. 인터랙티브/non-PMIx 환경에선 `mpirun -np 1 python script.py` (bare `python` 금지).
