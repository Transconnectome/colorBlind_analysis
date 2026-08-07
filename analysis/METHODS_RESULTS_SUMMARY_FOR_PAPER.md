# Methods & Results Summary for Paper

> **Hub index — headline numbers + pointers only.** Full per-analysis statistics live in each
> directory's own summary markdown (see the pointer table). Restructured 2026-06-27.
> Maintained by `capture-results` skill · Last updated: 2026-06-27 (was 2026-03-09).

---

## Directory pointer table (full statistics live here)

| Area | Detailed summary (full stats) | Scope |
|---|---|---|
| Phase 1 — Preprocessing & baseline | `METHODS_phase1_baseline.md` | C010 + Procrustes pipeline selection |
| Phase 2 — SRM between-subject | `METHODS_phase2_srm.md` · `phase2_SRM_across_between/*.md` | group/individual disparity, convergent validity, SRM battery |
| Phase 2 — Procrustes CVD–HC | `phase2_procrustes_cvd_hc/README.md` | 3-D heterogeneity characterization (RQ2/SRQ1) |
| Phase 2b — Decoder comparison | `METHODS_phase2b_decoders.md` · `phase3_decoder_comparing/README.md` | LORO/LOCO model comparison, LDA/FE |
| Future Phase 1 — Forward model | `future_phase1_forward_model/RESULTS.md` | ridge-GCV + FE-6 encoder, GO/NO-GO gate |
| Future Phase 2 — Filter optimization | `future_phase2_filter_optimization/README.md` + closure docs | 2-comp fit, inverse filter, model selection |
| Future Phase 3 — Behavioral / exp2 | `future_phase3_behavioral_analysis/README.md` | filter validation (JND, 8AFC), 2nd session |
| PAPER reproduction | `../docs/PAPER/repro/REPORT.md` · `PERMUTATIONS.md` | reproduce ledger + adjacent-accuracy per-ROI permutations |
| Supplementary validations | `METHODS_supplementary.md` | permutation/bootstrap/split-half battery |
| Univariate signal | `phase_supplementary/README.md` | overall-signal control |

---

## Headline numbers (load-bearing for the paper)

> Canonical current values only. Each block points to the directory holding the full statistics.
> The manuscript's adjacent-accuracy interpolation ledger is `../docs/PAPER/repro/PERMUTATIONS.md`.

### Phase 2 — SRM between-subject  → `METHODS_phase2_srm.md`
- Group disparity (trending): V1 p=0.062 (g=1.16), V2 p=0.075 (g=1.04)
- Individual: sub-09 (protan) V1 p=0.007; sub-08 (deutan) V2 p=0.040; sub-10 (deutan) HC range
- SRM K = V1 4 / V2 4 / V3 3 / hV4 3
- Convergent validity: crossnobis r=0.486, PCA r=0.742

### Phase 2 — Procrustes CVD–HC heterogeneity  → `phase2_procrustes_cvd_hc/README.md`
- CVD is heterogeneous: three distinct 3-D distortion profiles (magnitude / sign / structure), not one shared pattern
- Subtypes: sub-08 deutan, sub-09 protan, sub-10 deutan (same-genotype contrast = sub-08 vs sub-10)

### Phase 2b — Decoder comparison  → `METHODS_phase2b_decoders.md`
- LORO best = LDA+SRM (0.793, ICC=0.666); LOCO interpolation = ForwardEncoding (sole interpolator)
- Cross-subject generalization: HC→CVD 0.665 vs HC→HC, Mann-Whitney p=0.668
- Channel→color readout linear (FE_SVM ≈ FE)

### Future Phase 1 — Forward model  → `future_phase1_forward_model/RESULTS.md`
- Encoder: ridge-GCV + FE-6 basis (smooth_tikh rejected)
- HC LOCO > 0: V1 p=0.012; HC > CVD gap V1 d=1.61 (p=0.021), V2 d=1.85 (p=0.022)
- 3/4 ROIs pass GO/NO-GO (V1, V2, hV4 GO; V3 NO-GO)
- **Robustness (3 axes, PV-2 ✅ 2026-07-13)** — hV4 GO는 세 축 모두 통과, 임의선택 민감성 아님:
  - *Per-color dominance* (Friedman across 8 colors, HC): hV4 χ²=6.48 **p=0.485** (색간 균일 → GO가 특정 색에 안 끌림); V1 p=0.011 / V2 p=0.047 (discrim-only ROI만 색별 이질). `results/loco_reinforcement/per_color_breakdown.json`
  - *Residual structure* (r between encoding residual RDM & color RDM, HC mean): hV4 **r=0.053** (잔차 무구조 = well-specified); V1/V2 r≈0.45 (잔차에 색구조 잔존 = under-fit). resid/signal ratio hV4 0.454 < V1/V2 0.658. `residual_structure.json`
  - *GCV λ stability* (`lambda_stability_loco.py` → `lambda_stability.json`): hV4 GCV α가 73% fold에서 α=1로 수렴(log₁₀α SD=0.46); encoding ρ은 α 전구간(0.001–1000)에서 peak의 ≥90% 유지 = **λ-무관 plateau (7/7 grid pts)**, GCV ρ 0.205 ≈ peak fixed ρ 0.208 → p~0.044가 λ 우연 아님. (V1/V2 modal α=10, plateau 2–3/7로 더 민감하나 GO 근거는 hV4.)

### PAPER — interpolation (adjacent accuracy @hV4, FE-6 OLS)  → `../docs/PAPER/repro/PERMUTATIONS.md`
> **2026-08-07 재산출.** 정렬 공간을 Procrustes로 통일하고(§ 아래) sub-07을 포함해 **n=7**로 전 ROI 재계산. 이전 수치(n=6, hV4 p=0.008)는 ROI마다 n이 달라 비교 불가였다.
- HC 0.456 ± 0.039 (n=7); above-chance permutation **p=0.011** (N=1000 per-subject, seed 42). 순열 귀무 mean = **0.346**, 해석적 chance 0.25가 아님
- 전 ROI 순열: V1 p=0.164 (obs 0.393), V2 p=0.424 (0.357), V3 p=0.586 (0.339), **hV4 p=0.011 (0.456)** → 게이트 통과는 hV4 단독
- deutan 0.25 (Crawford-Howell t=-1.89, p=0.054 n.s., d_cc=-2.02); protan 0.13 (t=-3.04, p=0.012, d_cc=-3.25)
- per-hue single-case: **NO individual hue significant** (blue p=0.051, purple 0.229, magenta 0.096)
- LORO discrimination: both CVD > 0.125 chance at all ROIs (최저 0.375 @hV4); 단일사례 8검정 전부 p ≥ 0.189 (양측), |d_cc| 0.25–1.58
- **정렬 공간 정책**: 피험자 내 판독(LORO/LOCO) = Procrustes (`utils_forward_model.load_amplitudes`가 정본), 피험자 간 비교(교차전이·기하) = SRM. SRM 판본은 논문 Supplementary §S20
- driver: `docs/PAPER/repro/_perm_adjacent_n7.py` (정본 `loco_canonical`과 1e-12 일치 검증 내장, 4 ROI 3분)

### Future Phase 2 — Filter  → `future_phase2_filter_optimization/README.md`
- 2-comp argmin: deutan (β_s=6°, β_c=-42°), protan (β_s=2°, β_c=+24°)
- Filter mean |δθ|: deutan 26.3°, protan 16.2°
- Held-out composite test-loss: deutan -2.36 (IQR 2.15), protan -1.54 (IQR 1.42); N=300 resamples
- Identifiability: 2-comp 12/12 fail absolute recovery; 0/6 recovery survive FDR → descriptive embedding only
- Exp2 filter validation: **N=2** (sub-08 deutan, sub-09 protan), 단일 세션·4 runs/조건 → **descriptive only**. 상세 = 아래 exp2 블록 · `exp2_neural/RESULTS.md` · ResearchNOTE §6.5.

### Future Phase 3 — exp2 filter validation (N=2, descriptive)  → `future_phase3_behavioral_analysis/exp2_neural/RESULTS.md` · ResearchNOTE §6.5 · `future_phase4_geometry_synthesis/FINDINGS.md`

2nd MRI: sub-08(deutan)+sub-09(protan), 조건 = no-filter / deployed accessibility filter / individualized filter. N=2, 4 runs/조건 → descriptive (Cohen's d vs HC; inferential p 없음). **명칭: "individualized filter"(구 Optimal/personalized), "deployed accessibility filter"(구 Window).**

**primary — hV4 LOCO adjacent accuracy** (chance 0.375, HC 0.46±0.11) — 두 피험자 **정반대**:

| | no-filter | deployed | individualized |
|---|---|---|---|
| sub-08 deutan | 0.23 | 0.25 | **0.31** (개선) |
| sub-09 protan | 0.14 | 0.19 | **0.06** (역전, d_cc=−3.70) |

- **geometry** (affected ROI: sub-08 V2 / sub-09 V1): sub-08은 양 필터가 HC서 **멀어짐**(NF 최근접), sub-09는 양 필터가 HC로 **회복하나 deployed≈individualized**(개인화-특이 아님). 둘 다 완전 HC 기하 미달.
- **행동**: 두 필터 판별 복원; individualized가 **새 유의 편차 만들지 않은 유일 필터**(deployed는 sub-09 green-blue·cyan-magenta 유의화). Opt-vs-Win 순위불가(N=2).
- **LORO**: 전 ROI×조건 chance(0.125) 훨씬 위 → 신호 보존.
- **결론**: 필터 효과 phenotype-비일관, 효능 **미확인(열린 문제)**. 3층 프레이밍(§6.5): 확증=왜곡 특성화 / 탐색=필터효과 / 한계=N=2·지표불일치.

---

## Limitations & Caveats

- **Multiple comparisons**: 4 ROIs tested; LOO-consistent group p-values (V1=0.062, V2=0.075) do not reach p<0.05. Results framed as trending effects with individual-level confirmation via Crawford & Howell tests.
- **CVD-CVD RDM instability across halves**: Split-half CVD-CVD RDM correlation is inconsistent (V2 Set A: 0.536, Set B: 0.124), suggesting CVD within-group color structure is less reliably estimated with n=3 and half-run data.
- **V3/hV4 non-significance**: Consistent across all validation tests (LOSO 0/7, split-half 0/2, permutation n.s.). May reflect genuine absence of difference or insufficient power.
- **V1 validation gap**: Disparity significant (p=0.024), LOSO 6/7 robust, but RDM color-specificity not significant (p=0.192/0.599), complicating interpretation of what V1 disparity represents. Forward model partially addresses this: V1 HC LOCO > 0 (p=0.012), HC > CVD (d=1.61, p=0.021).
- **Forward model LOCO metric**: Voxel pattern correlation is scale-invariant but sensitive to n_voxels — sub-07 hV4 (16 voxels) produces noisy estimates. No significant correlation between n_voxels and LOCO_r for V1-V3 (all p>0.6), but hV4 trends (r=0.660, p=0.106). Ridge MAE > OLS MAE paradox: ridge shrinks predictions toward zero → conservative angular errors; voxel_corr is the more reliable metric.
- **No individual CVD significance for LOCO**: Unlike Phase 2 SRM (sub-09 V1 p=0.007, sub-08 V2 p=0.040), ridge_gcv LOCO Crawford-Howell tests are non-significant (best: sub-08 hV4 p=0.076). LOCO captures cross-color interpolation, a different (harder) aspect than within-color disparity.
- **SRM within-subject trade-off**: SRM improves between-subject agreement (2.4–6.5×) but reduces within-subject RDM test-retest reliability (V2: raw 0.473 → SRM 0.098). This drop conflates two sources: (1) genuine dimensionality reduction and (2) SRM fitting instability from independent split-half fits learning different shared spaces. The main analysis uses a single SRM fit on all runs, mitigating fitting instability. The "parallel" pattern (CVD preserving color structure) is independently validated by 2B in native voxel space without SRM (CVD ≥ HC in V1/V2), so does not rely on SRM-derived metrics alone.

---

## Pending Validations

검증 대기 항목 (우선순위 + blocker). daily-checkin `tasks_from` 소스. 총 4 (High 2 / Med 1 / Low 1). [PV-2 완료 2026-07-13]

| # | Pending validation | Domain | Priority | Blocker / next action |
|---|---|---|---|---|
| PV-1 | sub-09 behavioral session (sub-08-equivalent JND 8-pair + 8AFC 64-trial) | Phase 3 | **High** | 데이터 미수집 — Phase 3 first priority |
| ~~PV-2~~ | ~~Forward-model robustness (per-color LOCO, residual structure, GCV λ stability)~~ | Stage A | ✅ Done | **완료 2026-07-13** — hV4 3축 통과 (per-color p=0.485, residual r=0.053, λ plateau 7/7). 결과: Forward model 섹션 |
| PV-3 | exp2 filter validation at adequate power | Phase 3 | **High** | 재프레이밍 ✅ 완료(2026-07-14, N=2 descriptive 3층 — 논문 abstract/results_v4/discussion_v3 + ResearchNOTE §6.5 + summary exp2 블록). 잔여: 사전등록 target metric + 추가 피험자/촬영(확증엔 미충족) |
| PV-4 | V1 disparity ↔ color-specificity gap | Stage A | Med | disparity sig (p=0.024)이나 RDM color-specificity n.s. (p=0.192/0.599) — 해석 미해결 |
| PV-5 | Phase 2 SRM RDM metric test (correlation vs Euclidean, z-score vs min-max) | Stage A | Low | Deferred (TODO Deferred #4) |

---

## TODO (Next Steps)

### Completed
- [x] **Future Phase 1: Forward Model Validation** — Ridge-GCV + FE-6 validated. 3/4 ROIs pass gate (V1, V2, hV4). Basis ablation confirms FE-6 > Fourier.
- [x] **Future Phase 2: Filter Optimization** — 2-component fit + analytic inverse filter; per-subject argmin and |δθ| frozen (see future_phase2 closure docs).
- [x] **PAPER adjacent-accuracy permutations** — 2026-08-07 재산출, n=7 Procrustes 통일: hV4 p=0.011 (통과); V1 0.164, V2 0.424, V3 0.586 (미통과, 단 **네 ROI 모두 해석적 chance 0.25 초과** — 판별자는 순열 귀무 ~0.35). driver `docs/PAPER/repro/_perm_adjacent_n7.py`.
- [x] **Forward model robustness (PV-2, 2026-07-13)** — 3축 완료: per-color dominance (hV4 Friedman p=0.485), residual structure (hV4 r=0.053), GCV λ stability (hV4 ρ plateau 7/7, GCV 0.205≈peak 0.208). hV4 GO는 색/잔차/λ 임의선택에 무관. `results/loco_reinforcement/{per_color_breakdown,residual_structure,lambda_stability}.json`.

### Active
_(none — PV-2 완료 후 Stage A robustness 스레드 종결. 다음: PV-1/PV-3 Phase 3 데이터 대기)_

### Deferred
3. **Publication figure** — comprehensive decoder-comparison summary.
4. **Phase 2 SRM RDM metric test** — correlation vs Euclidean, z-score vs min-max.

---

## Red Team Log (Phase 2b, 2026-02-17)

| # | Criticism | Severity | Status | Neutralization |
|---|-----------|----------|--------|---------------|
| RT-1 + RT-7 | HC vs CVD group comparison invalid at n=3; cross-decoding used circular all-subjects SRM | Fatal | **DONE** | HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig); hV4 borderline due to low SRM quality |
| RT-2 | Procrustes pre-computed across all runs → LORO test-set leakage | Fatal | **DONE** | Nested Procrustes: SVM 0.899, FE 0.781 (no leakage, actually improves) |
| RT-3 | "Linearity" confounded by dimensionality; KernelRidge gamma grid too narrow | Addressable | **DONE** | PCA-20 within LORO: loses info vs full voxels |
| RT-4 | LOCO results from single subject (n=1), 100 perms at p-floor | Fatal | **DONE** | 10 subjects × 1000 perms completed (Result 2b) |
| RT-5 | LDA reliability r=0.015 contradicts "best model" claim; paradox misinterpreted | Addressable | **DONE** | Run-pair r=0.009; FE W stability 0.921. **Further resolved**: SRM LDA ICC=0.666 (reliable), Proc LDA ICC=0.013 (paradox is alignment-specific). Framing revised to task-dependent optimality. |
| RT-6 | Channel→color readout linearity untested | High | **DONE** | FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate. Linear readout sufficient. |

---
