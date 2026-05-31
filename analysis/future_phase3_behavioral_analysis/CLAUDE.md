# future_phase3_behavioral_analysis — CLAUDE.md

**Stage D** · **Status**: Planning / preparation.

## Objective

future_phase2에서 유도한 개인별 필터를 CVD 피험자에게 적용하고, 착용 전/후의 **behavioral (JND)** 및 **fMRI (SRM, LOCO)** 지표가 HC 분포 방향으로 이동하는지 평가한다.

## Direction

- **Functional 지표(LOCO)가 behavior를 예측한다**는 기존 관찰을 프레임으로 유지한다. Metric 지표(SRM z)는 보조적 참고로만 쓴다.
- 필터 specificity(HC에서 null)가 future_phase2에서 보장된 뒤 본실험을 시작한다.
- 실험 프로토콜(자극 calibration, L\*=75 clamp 등)은 future_phase2의 filter_visualization과 수치적으로 정합되어야 한다.
- 대조: (a) 필터 미착용 baseline, (b) 개인별 필터, (c) 필요 시 대안 모델 필터.

## 2nd-experiment (exp2) filter conditions — FINAL decision 2026-05-30 (supersedes 05-29)

### Path A (α'') 채택 — Deployed product as baseline + mechanism-rich analyses

- **Window 조건 = 실제 deployed macOS Color Filter** (System Settings > Accessibility > Display > Color Filters). 알고리즘 재구현 X. 우리가 *실제 CVD 사용자가 마주하는 deployed product를 능가함*을 입증한다.
- **Optimal 조건 = per-subject 2-comp pre-image δθ 필터** (`filters_exp2.py`로 PsychoPy 렌더링).
- 2 conditions × 4 runs = 8 runs, ABBA/mirror counterbalancing (sub-08 WOOWWOOW, sub-09 mirror). Baseline = exp1 무필터 (별도 세션).

### "Outdated" 비판 회피
- Path A는 *현재 Apple이 shipping하는 알고리즘*과 비교 → "17년 전 Machado 2009 baseline" critique 자동 dodge.
- Machado+Fidaner 재구현 (Path B) 검토했으나 outdated critique에 노출 + macOS와 별개의 proxy라 사용자 입장에서 less ecological이므로 기각.

### Mechanism claim 보존 전략 — Phase 1-2 origin 활용
**Mechanism은 exp2 contrast에서 새로 발견하는 게 아니라 Phase 1-2에서 이미 확보됨**(2-comp model: V1 cone-shift + V4 cortical rotation). Phase 3 exp2는 이 mechanism-derived 필터의 작동을 *deployed standard 대비 검증*. Manuscript wording:
- **OK**: "filter *derived from* fMRI-measured distortion", "improvements *in directions predicted by* our model", "consistent with mechanism"
- **금지**: "improvement is *because of* our mechanism (causal)" — pipeline confound 때문.

### Pipeline confound (#3) — 인정 + 우회 분석으로 mitigation
Window (OS-level transform after PsychoPy) vs Optimal (PsychoPy direct render) = 서로 다른 rendering stage. 이건 양보 안 함. Limitation에 명시. 단 다음 mechanism-specific 분석은 pipeline confound의 *uniform-shift* prediction을 위배하므로 *partially robust*:

#### (A) RDM shape convergence to HC
- 각 조건에서 V1/V4 RDM 계산 → HC RDM (exp1)과 cosine sim / Spearman ρ
- Predict: `sim(Optimal_RDM, HC_RDM) > sim(Window_RDM, HC_RDM)`
- Robust: cosine은 scale-invariant → uniform pipeline shift에 무관

#### (B) HYPO-pair-specific RDM distance change
- HYPO pair = 2-comp model이 *forward predict*하는 CVD-vulnerable pair (data-driven X, model-driven O — selection bias 회피)
- Predict: HYPO pair에서 RDM distance가 Optimal > Window (HC 방향 회복), HC-equivalent pair에서는 변화 작음
- Robust: pair-selective 패턴은 pipeline의 균등 효과로 설명 불가

#### (C) Per-color decodability shift toward HC
- 각 색 1-vs-rest decoding accuracy under each condition
- HC reference와의 per-color pattern 일치 verification

#### (D) 2-comp model parameter recovery from exp2
- exp2 데이터 자체에서 cone-shift Δλ, cortical rotation β_c 재추정
- Optimal 조건의 잔여 distortion < Window 조건 → "우리 model이 예측한 distortion이 우리 필터로 줄어든다" (가장 강한 mechanism evidence)
- Power 주의: Window/Optimal 각 4 run → condition 분할 fitting은 sample 절반. Joint design matrix에 condition regressor로 넣어 fit 권장.

#### (E) Cross-subject filter swap (behavioral only)
- 2×2: (filter_source × subject) interaction. Each subject sees: their own optimal filter, the other CVD subject's optimal filter.
- Predict: 본인 filter > 타인 filter (대각선 > 비대각선)
- Pipeline robust (둘 다 PsychoPy 렌더링이라 path 동일)
- Scanner 밖 행동 supplementary session에서 수행 (extra fMRI 부담 회피)

### Self-tune (severity) protocol
- 본스캔 전 별도 세션 (스캐너 밖 외부 모니터).
- 피험자가 macOS 슬라이더로 색 필터 강도 직접 조정 → 8 hue가 "가장 다양하게 보이는" 위치 confirm.
- 슬라이더 위치 + Settings 패널 스크린샷 저장 (`config_sub-{ID}.json`).
- 본스캔 시 실험자가 동일 위치로 설정.

### Implementation TODO
- `filters_exp2.py`: Window 분기 **삭제** (OS가 처리), Optimal 분기만 유지 (δθ pre-image 렌더링)
- `run_filter_assignment.csv`: 그대로. 실험자 토글 체크리스트의 driver
- Pre-experiment: spectroradiometer/colorimeter로 8 colors × 2 conditions × subject intensity 측정 → 실제 자극 Lab ground truth 기록
- Per-run: 실험자 휴식기에 OS 필터 수동 토글, 트리거 펄스와 OS state log 동시 기록
- MRI stim PC OS = **macOS 확정** (Linux/Windows였으면 Path A 불가)
- OS auto-update lockout (MDM 또는 manual) — LUT 변경 방지

### Limitations to declare in manuscript
1. macOS color filter is proprietary post-display transform; algorithm not disclosed → outcome comparison only, not algorithmic decomposition.
2. Rendering pipelines differ between conditions (OS-level vs PsychoPy direct). Mitigated via post-projector colorimetric measurement + mechanism-specific analyses (A)–(E) that are robust to uniform pipeline shifts. Cannot fully exclude pair-selective pipeline artifacts.
3. Empirical literature on commercial daltonization shows mixed efficacy; the relatively modest improvement under Window in our data is consistent with this and itself motivates personalization.

## Results location

- 행동·fMRI 재측정 결과, 교차검증 로그: 이 폴더의 `results/`, `docs/`.
- 사전 분석 서술: `notion.md`.

## Rule of action

1. 필터가 specificity 요구를 충족하기 전에는 본실험 설계·집행을 진행하지 않는다 (future_phase2 진행 상태 먼저 확인).
2. "LOCO → JND" 연결은 기존 관찰을 근거로 유지. "SRM z → JND"를 예측적 주장으로 격상하지 않는다.
3. Plateau 가설(FE basis smoothness 관련)은 기각된 상태 — 되돌리지 않는다.
4. 결과 저장 규칙: flat `results/<name>/`, per-subject json, batch당 `config.json` 1개.
