# future_phase3_behavioral_analysis — README

**Stage D · Status (2026-05-30): Planning, exp2 design finalized**

## Goal

개인별 inverse 필터 (Phase 2)를 deploy해 CVD 색 지각이 HC 방향으로 이동하는지 행동·fMRI로 검증.

## Active design — exp2 (2nd MRI experiment) under Path A (α'')

**Window 조건 = 실제 deployed macOS Color Filter**, **Optimal 조건 = per-subject 2-comp pre-image δθ 필터** (PsychoPy 렌더링). 2 conditions × 4 runs = 8 runs in one session, ABBA/mirror counterbalancing.

Rationale: Mechanism은 Phase 1-2에서 origin 확보 (V1 cone-shift + V4 cortical rotation 2-comp model). Phase 3 exp2는 mechanism-derived 필터의 deployed-product 대비 검증. "Outdated 알고리즘과 비교" critique 회피 (현재 Apple shipping algorithm). Pipeline confound는 인정하되 (A)–(E) mechanism-specific 분석으로 우회.

자세한 정책: `CLAUDE.md`.

## Analyses to run on exp2 fMRI data

| Code | 분석 | Mechanism strength | Pipeline confound robustness |
|---|---|---|---|
| (A) | RDM shape convergence to HC (cosine sim) | medium | high (scale-invariant) |
| (B) | HYPO-pair-specific RDM distance change | high | high (pair-selective ≠ uniform shift) |
| (C) | Per-color decodability shift toward HC | medium | medium |
| (D) | 2-comp model parameter recovery from exp2 | **highest** | high (model-specific) |
| (E) | Cross-subject filter swap (behavioral only) | high | full (same PsychoPy path) |

## Behavioral sessions (outside scanner)

1. **Self-tune calibration** (pre-scan, per subject): subject sets macOS color filter intensity to maximize 8-hue distinguishability. Record slider position + Settings screenshot.
2. **Cross-subject filter swap session** (post-scan or separate day): 4 conditions JND task — no filter / macOS Window / own optimal / other CVD subject's optimal. 2×2 (filter source × subject) interaction test.

## Folder layout

```
future_phase3_behavioral_analysis/
├── CLAUDE.md                          # active policy + exp2 design
├── README.md                          # this file
├── notion.md                          # pre-analysis narrative (older — see CLAUDE.md for current)
├── results/                           # exp2 analysis outputs (flat per-subject)
├── scripts/                           # analysis scripts (A)–(E)
├── run_count_validation/              # Phase 3 run-count Tier 1/2/3 validation
├── comprehensive_pipeline/            # earlier integrative pipeline
├── figures/
└── images/
```

## Data & paths

- exp1 (baseline, no filter) C010 amplitudes: `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010/{subject}/{ROI_dir}/amplitudes_procrustes.npy`, shape (6, 8, n_voxels)
- exp2 data path: TBD when collected
- HC reference RDM (for analyses A–C): from Phase 1-2 results (`phase2_SRM_across_between/`, `phase2_procrustes_cvd_hc/`)
- 2-comp model (for analyses B, D): `future_phase2_filter_optimization/` — pre-image generator + parameter fitter

## Implementation TODOs

- [ ] Strip Window branch from `filters_exp2.py` (project: colorBlind, NOT analysis); keep Optimal δθ pre-image only
- [ ] HYPO-pair forward-prediction script (model-driven, not Phase 1-2 data-driven)
- [ ] Self-tune calibration GUI/script (macOS Settings deeplink + slider position logger)
- [ ] Cross-swap JND task script
- [ ] Pre-experiment spectroradiometer/colorimeter measurement protocol
- [ ] Trigger pulse × OS filter state sync logging
- [ ] OS auto-update lockout policy (MDM or manual)

## Rules of action

1. 필터 specificity 요건 (future_phase2)이 충족된 뒤 본실험 진행.
2. Mechanism claim wording = "consistent with" / "in directions predicted by". *Causal* mechanism 표현 금지 (pipeline confound 존재).
3. "LOCO → JND" 연결은 유지. "SRM z → JND"를 예측적 주장으로 격상 금지 (Plateau 가설 기각 상태).
4. 결과 저장 규칙: flat `results/<name>/`, per-subject json, batch당 `config.json` 1개.

## Related documents

- `CLAUDE.md` — current active policy, exp2 design, limitations
- `exp2_protocols.md` — concrete protocols (HYPO forward-prediction, self-tune, cross-swap)
- `notion.md` — pre-analysis narrative (verify currency before reuse)
- `behavioral_alignment_2026-05-19.md` — LOCO/JND alignment record
- `run_count_validation_plan_20260519.md` + `_addendum_20260520.md` — Phase 3 run-count justification (Tier 1/2/3, V1 as primary endpoint)
- `~/.claude/projects/.../memory/project_exp2_filter_validation.md` — design log + neurodesign gotcha
- `~/.claude/projects/.../memory/project_run_count_validation_v2.md` — power decisions
