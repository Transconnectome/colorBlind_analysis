# Run-count validation — Addendum (2026-05-20)

**Trigger**: 2nd MRI 실험 설계 추가 정보 — (i) **2 filter conditions** (digital monitor/OS color filter vs custom) within-subject, (ii) **behavioral JND = PRIMARY endpoint**, (iii) session duration constraint.

**Filter A 정정 (사용자 확인 2026-05-20)**: "상용 윈도우필터" = 모니터 OSD 또는 OS-level (macOS Accessibility / Windows Color Filter) 색보정 = **digital LUT-based filter**, multi-notch optical 안경 (EnChroma 등) 이 *아님*. 함의:
- Stimulus rendering pipeline에서 LUT를 적용·해제만으로 두 조건 toggle 가능. 안경 교체·재calibration 시간 0.
- Spectral profile은 measure가 아닌 *디스플레이의 RGB→RGB transformation*. STIM_LAB rendering에서 LUT를 source로 등록.
- 두 condition간 attentional/effort confound 가능성 낮음 (안경 vs 무안경 비교가 아니므로).
- Phase 1의 baseline data (filter 없음)을 *third condition*으로 사후 비교 가능 — 실험 설계상 자연스러운 control.
**Status**: Companion document to `run_count_validation_plan_20260519.md`. Does not replace; extends.

**Session duration verification (2026-05-20)**: `colorBlind_test.py` 분석 결과, 각 run의 schedule file (72 trials × TRIAL_DURATION=1.5s + fixation 2–4s + ISI 3.0/4.5/6.0s)은 last trial onset≈426s + 1.5s = **약 7.5분/run in-scanner task time**. 사용자 명시 (2026-05-20): scanner 외부 준비/anatomical/break는 데이터 품질과 무관하므로 task time만 평가. 따라서:

| 설계 | in-scanner task time |
|---|---|
| 현행 single condition (6 runs) | ~45분 |
| 2-condition × 6 runs | **~90분** ← 사용자 1.5h 우려의 정확한 근거 |
| 2-condition × 4 runs | ~60분 |
| 2-condition × 3 runs | ~45분 (현행 single과 동일) |

**fMRI 권장 in-scanner task time은 일반적으로 60–75분 max** (피험자 attention/motion 임계). 따라서 2-condition × 6 runs (90분)은 명백히 한계 초과 → reduction 필요성 자체는 정당. 2-condition × 4 runs (60분)는 권장 경계, × 3 runs (45분)는 안전.

---

## 0. Why an addendum

`run_count_validation_plan_20260519.md` answers: *"Can the existing 6-run paradigm be reduced to 4 runs without losing the current Phase 1/2 landmark findings?"* — single-condition framing.

오늘의 질문이 가져오는 *진짜* 새 정보는 **두 filter 조건을 한 session에서 모두 측정해야 한다는 paired-filter design**이다. behavioral JND가 primary라는 framing 자체는 새롭지 않다 (MEMORY: Phase 1에서 이미 LOCO→JND 6/6 concordance가 핵심 narrative였고, 19일 plan §3.3도 이를 anchor로 포함). **새 정보**:

1. **Paired filter design**: 같은 subject·session에서 filter A·B 모두 측정 → between-subject 분산 제거 → paired LMM 통계 효율 1.4–2× 증가 (Gonzalez-Castillo 2017 variance decomposition 기반)
2. **Total run budget 두 배 압박**: 6×2=12 runs가 2-hour session으로 attention 한계 초과 → reduction이 *실질적으로 강제됨*

두 framing이 함께 작동: 19일 plan의 **모든 anchor retention 검증은 그대로 유효**하다. 오늘 addendum은 (a) paired filter design이 통계 효율과 새 metric 정의를 어떻게 바꾸는지, (b) fMRI가 mechanistic secondary로 동작할 때 어떤 decision rule이 추가/완화되는지를 추가한다.

---

## 1. Design change summary

| 축 | 5월 19일 plan | 5월 20일 addendum |
|---|---|---|
| 비교 구조 | 단일 protocol (HC vs CVD between-group) | filter A vs B **paired within-subject** |
| Primary endpoint | fMRI LOCO/ΔRDM | **Behavioral JND (filter A vs B paired)** |
| fMRI 역할 | confirmatory | **mechanistic descriptive** |
| Run budget | 4 vs 6 (single condition) | 4×2 = 8 (or 3×2=6) per session |
| Specificity bar | HC FPR ≤ 7/7 | 유지 + sub-10 paired filter null |

---

## 2. Paired-filter design — statistical implications

Within-subject paired comparison reduces variance vs Phase 1 between-group framing:

- **Phase 1 variance budget** (Gonzalez-Castillo 2017): residual measurement noise (dominant) + across-session + across-runs + across-blocks. Between-subject variance enters when comparing HC vs CVD.
- **Phase 2 paired**: same subject, same session, 두 filter 조건 → between-subject 항이 0. 남는 분산은 within-session 변동 (across-runs + across-blocks + residual) + filter-specific noise.

**Implication for power**: 같은 subject가 두 조건에 모두 노출되므로, paired t / LMM 의 분모(within-subject SD)는 Phase 1의 between-subject SD 보다 통상 30–60% 작다. 즉 같은 effect size에서 paired design의 검출 power가 unpaired 대비 ~1.4–2× 높다.

**구체적 가정**:
- Filter A vs B 의 fMRI LOCO 차이가 within-subject Cohen $d_z \geq 0.6$ 라면, N=3 CVD 만으로 paired-t 검정은 underpowered이나 LMM (subject random + filter fixed + ROI fixed)는 ROI×subject×color cell 단위 (3×4×8 = 96 cells)로 검정 가능. 이 분해가 paired design의 실제 power 출처.

---

## 3. Behavioral-primary 전환 → fMRI decision rule 완화

**중요 caveat**: behavioral-primary framing은 fMRI의 *confirmatory* bar만 완화한다. 19일 plan에서 식별된 **HC LOCO FPR=7/7 (label-permutation, 6 runs)** 와 **baseline_delta_rho rank 7/8 specificity 문제**는 fMRI가 primary든 secondary든 *동일하게* 유효하다. 이유: fMRI mechanistic narrative ("filter 조건 간 신경 표상이 다르다")는 specificity가 보장되지 않으면 collapse한다 — secondary라도 specificity 없이 narrative를 쓰면 reviewer가 즉시 dismiss. **19일 plan §4의 HC FPR / sub-10 null 기준은 이 addendum에서 양보 불가 (CLAUDE.md §3 일관).**

5월 19일 plan §4 의 Pass-4 criteria는 fMRI 결과를 primary로 가정한 confirmatory bar 다. behavioral JND primary 전환 후 fMRI는 mechanistic이므로 다음만 만족하면 충분:

**Revised fMRI bar (mechanistic secondary)**:

| 기준 | n=4 paired filter 설계에서 요구 |
|---|---|
| Filter-conditional LOCO ρ recoverability | 각 filter 조건에서 ≥ Phase 1 baseline ρ - 1 SD |
| Δ(LOCO ρ, filter A − filter B) per subject | bootstrap CI에서 방향 일치 (≥2/3 subjects same sign) |
| Filter-conditional RDM split-half reliability | r ≥ 0.5 (Walther 2016 권고: crossnobis + multivariate noise normalization 사용 시 4-run에서 도달 가능) |
| HC null (sub-10 또는 추가 control HC) | Filter A vs B paired Δ LOCO not significant |
| 2-component β_s/β_c bootstrap CI | excludes 0 for each filter condition |

**핵심**: fMRI는 *"filter 조건별로 신경 표상이 다르다"*를 보여주는 mechanistic narrative를 지원하면 충분. behavioral JND가 *"filter A vs B 차이가 행동에서 검출된다"*를 confirmatory로 입증.

19일 plan의 **HC FPR / sub-10 specificity 기준은 양보 불가** (CLAUDE.md §3).

---

## 4. Behavioral JND — power budget for primary endpoint

**스코프 재조정 (사용자 redirection 2026-05-20)**: 본 addendum의 §4 behavioral 섹션은 *plan-only placeholder*. 사용자 우선순위는 **fMRI 기존 6-run 데이터 subsampling으로 4-run 등가성 실증**이며, JND protocol 결정은 그 결과 이후의 별도 트랙. 본 섹션은 후속 결정 시 참고용으로만 유지.

### 4.1 측정 설계 옵션

**경고 — 아래 effect-size 추정은 derived가 아닌 *placeholder* 다.** 실제 결정 전에는 (a) 기존 LOCO→JND 데이터에서 within-subject JND SD를 추출, (b) `simr` 또는 직접 LMM Monte Carlo 시뮬레이션으로 power 곡선을 그려야 한다. 아래는 그 시뮬레이션을 짤 때의 출발점일 뿐:

| 옵션 | 시간 | 정성적 power 평가 (실 simulation 필요) |
|---|---|---|
| A. 1 JND per filter, between-subject only | 5–10 min × 2 | N=3 paired-t (2 df) → $d_z \gtrsim 2.5$ 만 검출. 강력 효과 외 미사용. |
| B. **Repeated JND (4× per filter, 8 hues) + LMM** | 30–60 min × 2 | LMM이 cell 단위(3 subj × 8 hue × 4 rep × 2 filter = 192 cells)로 검정 → df 증가. 정성적으로 옵션 A보다 small-medium effect 검출 가능하지만 *정확한 $d_z$는 simulation 필요*. |
| C. Multi-stimulus JND map (8 hues × 2 filters) | 40–60 min | LMM cell 수 동일 (B와 차이는 repetition vs hue 분포만) |

**선결 작업**: LMM 시뮬레이션 (`simr` R package 또는 Python statsmodels Monte Carlo)으로 가정된 effect size 범위 (d_z ∈ [0.3, 1.0])에서 N=3 paired의 power 곡선 산출. **이 시뮬레이션 결과 없이 옵션 B/C가 "실용적"이라고 단정 불가** — advisor 지적 (2026-05-20).

**잠정 추천**: 옵션 B의 measurement 구조 (4 repeats × 8 hues × 2 filters per subject) 를 채택하되, 진행 전 simulation으로 효과 크기 가정 점검. Scanner 외부에서 pre/post로 실행 (각 filter 착용 직후 ~30–60 min). 총 추가 시간 1–2시간, fMRI run 예산과 무관하지만 *세션 총 시간에는 영향*.

### 4.2 분석

```
JND ~ filter + (filter | subject) + (filter | hue)
```

- Fixed: filter (commercial vs custom)
- Random: subject intercept + slope; hue intercept + slope
- Primary test: filter fixed-effect Wald or LRT

### 4.3 사전 effect size 가정

문헌 (Tregillus 2021, Reddy 2024 EnChroma) 기준 filter 효과는 d ~ 0.5–1.0 범위. Custom filter (이론적 최적)가 commercial보다 우월할 것으로 *기대*하지만, paired Wilks 검정 결과로 검정 (사전 일방향 가설 정당화 가능).

---

## 5. 새 metric — paired filter design 전용

19일 plan §2 metrics에 추가:

| Metric | 정의 | n_runs ∈ |
|---|---|---|
| Filter-Δ LOCO ρ | $\rho_{A} - \rho_{B}$ per subject per ROI per color | {3,4,5,6} |
| Filter-Δ RDM cosine | $\cos(\mathrm{RDM}_A, \mathrm{RDM}_B)$ deviation from identity | {3,4,5,6} |
| Filter-Δ β_s, β_c | 2-component fit comparison: filter A vs B | {3,4,5,6} |
| Filter-conditional LOCO→JND concordance | LOCO Δρ 방향과 behavioral JND Δ 방향 일치 | {3,4,5,6} |
| **Cross-modal coupling** | $r(\Delta_\text{fMRI}, \Delta_\text{JND})$ across subjects | {3,4,5,6} |

`run_count_subsample.py` (19일 plan §5 deliverable)에 `--paired_filter_mode` flag 추가 필요.

---

## 6. NotebookLM evidence base

**사용자 redirection (2026-05-20)**: 새 notebook 분리 운영하지 않고 기존 `ColorBlind_comprehensive` (id `fa13d441-21f2-40a0-8170-8cc8eb49cc7b`) 에 본 작업의 sources를 통합한다.

본 작업에서 수집·정리한 sources (5월 20일 일시 notebook `9c52afce-2edf-434e-a020-1650e5971f92` 에서 `ColorBlind_comprehensive` 로 이전 예정):
- Nili 2014 — Noise ceiling (PLOS CB toolbox paper, PDF added)
- Walther 2016 — Crossnobis reliability + multivariate noise normalization (diedrichsenlab PDF added)
- Allen NSD 2021/22 (Nature Neuro) — text summary
- Tregillus 2021 Curr Biol — CVD fMRI within-subject paradigm (text summary)
- Gonzalez-Castillo 2017 — variance decomposition (text summary)
- Ma 2024 NeuroImage — pseudo TPR/FPR subsampling framework (text summary)
- 프로젝트 컨텍스트 (Phase 2 design)

19일 plan §6 의 추가 권장 sources (Tarhan & Konkle 2020, Valente 2021, Schütt 2023)도 동일 notebook에 추가 임포트 권장.

### NotebookLM 합성 결론 (요약)

질의 두 번 (run reduction general; behavioral-primary specific) 후 NotebookLM이 일관되게 도출한 4가지 reporting metric:

1. **Pseudo TPR/FPR** (Ma 2024 framework) — 4-run subset이 6-run "ground truth" 결과를 재현하는 비율
2. **Noise ceiling at n=4** (Nili 2014) — RDM 모델이 도달 가능한 상한, 4-run에서 6-run 대비 절대값
3. **Split-half RDM reliability with crossnobis + MVNN** (Walther 2016) — 4-run에서 split-half r 평가
4. **Cone-shift Δλ stability** (자체 데이터) — 4-run 데이터의 Δλ가 Phase 1 6-run 추정치와 ±tolerance 내

---

## 7. Decision rule overlay (19일 plan §4 위에 덧대기)

19일 plan §4의 Pass-4 criteria는 **모두 유지**. 추가로 behavioral-primary 전환을 반영하여:

**Pass-4-paired** (4 runs × 2 filter conditions 정당화) requires ALL of:

A. 19일 plan §4의 Pass-4 모든 기준 (single-condition retention) — **HC FPR / sub-10 null 양보 불가** (§3 위 caveat 참조)

B. 새 paired-filter 기준:
- Filter-conditional LOCO ρ at n=4 가 Phase 1 baseline (n=6) ρ 의 ≥80%
- HC sub-10 (또는 추가 HC pilot) 의 filter A vs B paired Δ LOCO ρ p > 0.10 (specificity guard)
- **Behavioral JND LMM power simulation 선결**: simr/Monte Carlo로 가정 effect size에서 power ≥ 0.7 입증 (§4.1 placeholder 대체 작업). 시뮬레이션 결과가 power < 0.7이면 N 확장 또는 healthy-CVD pilot 추가가 본 기준에 포함됨.

C. Cross-modal sanity:
- LOCO→JND concordance retention ≥ 5/6 at n=4 (19일 plan §3.3 기준 유지)
- Filter-Δ LOCO 와 Filter-Δ JND 방향 일치 (≥2/3 CVD subjects)

---

## 8. Honesty addenda (19일 plan §8 보강)

- behavioral JND primary 전환은 fMRI decision bar를 *완화*시키지만, **HC FPR / specificity 기준을 양보하지 않는다**. 19일 plan §8의 첫 번째 honesty 항목 (4 runs는 simulation floor 미만) 은 그대로 유효.
- Paired filter design은 통계 효율을 높이지만 **새 confound (filter-induced attention/effort 차이)** 를 도입. counterbalancing + attention task performance를 covariate로 반드시 보고.
- Filter A=commercial 의 효과가 null이라는 사전 가능성도 진지하게 다룰 것. 두 filter 모두 null이면 paired Δ 는 정보 없음.
- Behavioral N=3 CVD에서 LMM power가 충분하지 않다면 (effect size가 d<0.8), **scanner 외부에서 healthy-CVD pilot (N=5–10) 추가**하여 행동 ground truth 먼저 확보 후 scanner로 진입하는 것이 안전.

---

## 8.5. v1 subsampling 실행 결과 (2026-05-20)

Script: `scripts/run_count_subsample.py`. Output: `run_count_validation/v1_allroi_n4_vs_n6.json`. Scope: V1/V2/V3/hV4 × 10 subjects × 17 subsets (1×n=6 anchor + 1×n=4 leading + 15×n=4 random C(6,4)). Point estimate only (encoding-direction ridge_gcv LOCO ρ, unshifted machado_1way Δλ=0 design).

**핵심 결과** — sub-08 deutan LOCO ρ **sign retention** across all 4 ROIs:

| ROI | n=6 ρ | n=4 ρ range (16 subsets) | Sign retention |
|---|---:|---:|:---:|
| V1 | −0.198 | [−0.266, −0.035] | **16/16** |
| V2 | −0.153 | [−0.298, −0.105] | **16/16** |
| V3 | −0.134 | [−0.181, −0.069] | **16/16** |
| hV4 | −0.213 | [−0.266, −0.161] | **16/16** |

**Critical framing**: 위 결과는 *sign-of-ρ retention* (16/16 across all ROIs). **p<.01 retention과 동일하지 않음**. 19일 plan §4 Pass-4 criterion ("sub-08 hV4 LOCO p<.01 retained in ≥80% of subsets")의 충족은 permutation null SLURM job 별도 실행 후 확인 가능.

**부가 관찰**:
1. **Leading-4 subset (runs {0,1,2,3})이 n=6 anchor를 매우 가까이 재현**: sub-08 V4 = −0.216 vs n=6 −0.213 (3rd decimal 일치). Gonzalez-Castillo 2017의 "occipital cortex 후반 runs는 measurement noise 추가"와 일치하는 자체 데이터 증거.
2. **HC mean ρ가 n=4에서 동등 또는 약간 *증가*** (V1: +0.138→+0.121–0.199; hV4: +0.055→+0.019–0.136). 일부 후반 runs가 encoder training에 noise만 추가했을 가능성.
3. **sub-10 V2 false-positive 경고**: n=6 ρ=−0.057 (slight negative — CVD-like sign in *near-normal* subject). n=4 모든 subset에서 동일 sign 유지. MEMORY의 baseline_delta_rho rank 7/8 specificity 문제와 일관. **HC FPR perm test 필요**.

**미해결 항목 (v2/v3)**:
- Permutation null at n=4 vs n=6 (perm p value 비교 — 19일 plan §7 budget Step 3) — separate SLURM array, ~4 wall-hours
- ΔRDM / crossnobis split-half reliability (Walther 2016 권고) — separate metric class
- Paired-filter mode — 2nd MRI 데이터 수집 후 별도

**Pass/Fail preliminary verdict (point estimate only)**:
- ✓ sub-08 LOCO landmark sign retention 16/16 across all 4 ROIs
- ⚠ sub-10 V2 false-positive sign retention 16/16 — pre-existing specificity 문제, n=4에서 *해결되지 않음* (하지만 *악화되지도 않음*)
- ✓ sub-09 hV4 sign retention 15/16
- ⚠ p-value retention (binding criterion) 미검증 → SLURM perm null 필요

---

## 9. Next steps — execution path

본 addendum은 *plan-only* (advisor 지적 2026-05-20). 실제 decision은 다음 execution을 거쳐야:

### Step 0 — 선결 (block 해소)
- **A. Filter A (commercial) 사양 확정**: "상용 윈도우필터"가 정확히 무엇인지 사용자 확인 필요. EnChroma 안경 vs 모니터 부착 윈도우 필터 vs ColorMax/Pilestone 등 spectral profile이 다름. STIM_LAB rendering pipeline 등록 전 결정.
- **B. Behavioral LMM power simulation**: Phase 1 기존 JND 데이터에서 within-subject SD 추출 → simr/statsmodels Monte Carlo로 가정 effect size별 power 곡선. 결과가 §4.1 옵션 선택 및 §7-B의 Pass-4 기준을 binding함.

### Step 1 — 19일 plan §5 subsampling 실행 (1 person-day SLURM)
- `analysis/future_phase3_behavioral_analysis/scripts/run_count_subsample.py` 작성 (19일 plan §5 deliverable). 본 addendum 반영하여 `--paired_filter_mode` flag 추가 (실제 paired filter data는 Phase 2 데이터에서 *가상*으로 simulate하거나 단일 condition 6-run subsample만 우선).
- 모든 C(6, n) subset × 3 ROI × 10 subject × 5 metric → ~8,500 fits, <1초/fit으로 local 또는 node2.
- Permutation null은 19일 plan §7 Step 3 budgeted scope (n=4, n=6 만, anchor 8개만) — 16 subsets × 8 anchors × 5,000 perm ≈ 680K fits, SLURM array ~4 wall-hours.

### Step 2 — 결과 → decision (0.5 person-day)
- `landmark_retention.json`, `hc_fpr_per_n.json` 산출 후 19일 plan §4 + 본 addendum §7 decision rule 적용.
- Pass-4 / Conditional-5 / Fail 판정.

### Step 3 — Behavioral JND protocol 확정 (0.5 person-day)
- Step 0-B simulation 결과로 옵션 A/B/C 중 선택 + N 결정.
- 필요 시 healthy-CVD pilot (N=5–10) scanner 외 사전 측정 trigger.

### Step 4 — NotebookLM 보강 (별도, optional)
- 19일 plan §6 권장 3편 (Tarhan & Konkle 2020, Valente 2021, Schütt 2023) 을 `ColorBlind_comprehensive` notebook에 추가 → 재query하여 본 addendum 보강.

### Step 5 — PI review 송부
- 19일 plan + 본 addendum + Step 2 결정 결과를 합본으로 PI 검토 요청.

**Total**: Step 0 (선결) → Step 1–3 약 2 person-day → Step 5 송부. Step 4는 병렬.

---

## 10. 참고: 새 NotebookLM 두 query 풀 응답

본 addendum §6의 4 reporting metric은 다음 두 query에서 도출:

- Q1 ("Given an event-related task fMRI paradigm with 8 conditions and currently 6 runs, what empirical evidence and statistical methods support reducing to 3-4 runs...")
- Q2 ("Given the primary endpoint is behavioral JND, how does that change the run-count validation framework for the fMRI side?")

전문 응답은 notebook의 `conversation_id: 011efbc0-8e6f-4122-94ee-71acaf2ed701` 에 보존. 향후 follow-up query는 동일 conversation으로 진행하면 컨텍스트 누적.
