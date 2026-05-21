# Run-count validation plan (Phase 3)

**Date**: 2026-05-19
**Trigger**: PI request — justify current 6 runs × 8 colors paradigm, or demonstrate 4 runs is sufficient.
**Status**: Plan only. Execution gated on Phase 2 closure (see `project_phase2_closure.md`).

---

## 1. Question

현재 paradigm = 6 runs × 8 colors × 1 trial/color/run (PsychoPy `colorBlind_test.py`, RSVP oddball-K).
지도교수 검증 요구: **6 runs 가 정당화되는가? 4 runs 로 줄여도 핵심 결과가 보존되는가?**

이를 두 sub-question 으로 분해:

- **Q1 (sensitivity)**: 현재 pipeline 의 핵심 유의 결과(아래 §4 anchor list)가 n_runs ∈ {2,3,4,5} 부분집합에서 얼마나 자주 재현되는가?
- **Q2 (specificity)**: HC LOCO FPR=7/7 (label-permutation null, 6 runs) 및 sub-10 near-null 이 run 수 축소 시 어떻게 변하는가? (run 감소가 specificity 를 더 악화시킬 가능성 — MEMORY: hV4 baseline-Δρ rank 7/8 already CVD-indistinguishable at 6 runs.)

**Honest framing**: literature 시뮬레이션(아래 §6)은 RDM-based model discrimination 안정화에 ≥16 runs 권장. 6 runs 는 이미 simulation floor 미만. 본 검증의 정확한 질문은 "4 runs 가 6 runs 와 등가인가" 가 아니라 "**현재 6-run 결과의 어떤 부분이 4 runs 에서 살아남는가**" 이다.

---

## 2. Metrics to track as a function of run count

| Metric | What it captures | Estimator | n_runs ∈ |
|---|---|---|---|
| LOCO ρ (V1/V2/V4, ridge_gcv pooled) | Color generalization (Stage A primary) | Pooled n_runs × 7 = {14, 21, 28, 35} train samples | {2,3,4,5,6} |
| LORO ρ | Pattern stability across runs | Requires n_runs ≥ 2 folds | {2,3,4,5,6} |
| Split-half reliability (color-pattern) | Cross-run repeatability | Even vs odd run halves; n=6→3v3, n=4→2v2 | {2,4,6} only |
| Label-permutation p (LOCO) | Statistical power | 5,000 perm per subset | {2,3,4,5,6} |
| Crossnobis ΔRDM cosine, Spearman | RDM SNR (Walther 2016) | Cross-validated over runs | {2,3,4,5,6} |
| Per-pair ΔRDM permutation p | Pair-level effect size | Subset perm null | {2,3,4,5,6} |
| Δρ (sub vs LOO-HC) | Effect detectability (Crawford-Howell) | Per subject vs LOO HC mean | {2,3,4,5,6} |
| 2-component β_s, β_c bootstrap CI | Filter-fitting stability (MEMORY R+C) | Bootstrap on n_runs subset | {3,4,5,6} (n=2 too few for fit) |
| HC FPR (label-permutation) | Specificity (CRITICAL) | Fraction HC subjects with LOCO perm p<0.05 per subset | {2,3,4,5,6} |
| LOCO→JND concordance | Cross-modal robustness (Phase 3) | 6/6 pairs at n=6; recompute per subset | {2,3,4,5,6} |

---

## 3. Procedure

### 3.1 Subsampling design (CRITICAL — combinatorial, not bootstrap)

C(6,n) for n ∈ {2,3,4,5} = {15, 20, 15, 6}. **All unique subsets enumerated**, no bootstrap resampling needed (would mis-state SE). 6 runs = single point (no subset variance).

Two subsetting modes — they answer different questions:

- **Random subsets** (all C(6,n) combinations): tests signal sufficiency, marginalizes over run position.
- **Leading subsets** (first n chronologically: {1..n}): tests the *actual* proposed shorter protocol. Run-position effects (attention drift, motion drift, registration quality) bias these — exactly what PI's protocol question asks.

**Both reported.** Disagreement between them is itself a result (e.g., late runs degraded → fewer runs paradoxically helps).

Pool / fold mechanics (disambiguate "n_runs"):
- LOCO (color generalization): pooled samples = n_runs × 7 train colors. n=4 → 28 train samples (vs 42 at n=6).
- LORO (run generalization): n_runs CV folds. n=2 = 1 train / 1 test, unstable; report but interpret cautiously.

Code reuse:
- `analysis/future_phase2_filter_optimization/scripts/loco_distortion_fit.py` (accepts run mask)
- `analysis/phase3_decoder_comparing/model_comparison_validation/scripts/loco_baseline.py`
- `analysis/phase2_SRM_across_between/rerun_loo_consistent.py` (LOO-HC + Crawford-Howell)
- `analysis/future_phase2_filter_optimization/scripts/diagnostic_delta_rdm.py`

New utility needed: `run_count_subsample.py` — wraps existing scripts with `--run_mask` arg over enumerated subsets.

### 3.2 Saturation curves

Per ROI (V1/V2/hV4) × per metric:
- y-axis: metric value (ρ, ΔRDM cos, β_s, p, …)
- x-axis: n_runs ∈ {2,3,4,5,6}
- Bands: across-subset SD (NOT bootstrap CI), separate trace for random vs leading subsets
- Anchored at n=6 single point

Quantify marginal gain: Δ(metric)_{4→6} / Δ(metric)_{2→6}. If Δ_{4→6} < 0.1 × Δ_{2→6} → 4 runs near-saturation for that metric/ROI.

### 3.3 Power retention for landmark findings (the actual decision data)

For each anchor finding (§4), report fraction of subsets at n_runs ∈ {2,3,4,5} that retains significance at original threshold:

```
finding                              n=2    n=3    n=4    n=5    n=6
sub-08 hV4 LOCO p<.01                 ?      ?      ?      ?     1/1
sub-08 V1  LOCO p<.001                ?      ?      ?      ?     1/1
sub-08 V1  Δλ=34.92nm p<.05 (W-fixed) ?      ?      ?      ?     1/1
sub-08 V2  Δλ=3.87nm p<.05 (W-fixed)  ?      ?      ?      ?     1/1
sub-09 V1  ΔRDM p<.01                 ?      ?      ?      ?     1/1
sub-10 V1  LOCO p>.05 (null)          ?      ?      ?      ?     ✓
HC FPR ≤ baseline                     ?      ?      ?      ?    7/7 (existing)
LOCO→JND 6/6                          ?      ?      ?      ?     6/6
```

**Note on excluded anchor**: sub-09 V1 cone-shift Δλ≈16.5nm is intentionally NOT used as a landmark because MEMORY (Gen-4 Tasks #20–#22) flags it as geometry-weak, neural-fail (c8 magenta anti-prediction), and family-non-specific (protan vs deutan margin <0.05). Using a contested finding as a decision anchor would invite dismissal of the whole validation. The W-fixed Phase-2 v2 results (sub-08 V1 / V2) are substituted because they are unqualified positives in the MEMORY record.

### 3.4 HC specificity tracking (do not skip)

Per HC subject (sub-01..07), per n_runs, per ROI: fraction of subsets giving LOCO perm p<0.05. If FPR rises monotonically as runs drop → reducing runs amplifies the existing false-positive problem identified in MEMORY (`baseline_delta_rho`). This is a stopping criterion: even if CVD effects survive, HC FPR climbing above current 7/7 disqualifies a reduction.

---

## 4. Decision rules (anchored to existing findings)

**Do not** judge by abstract "statistical equivalence at n=4 vs n=6". Bind to specific landmark results from MEMORY:

1. **Pass-4 (4 runs justifiable)** requires ALL of:
   - sub-08 hV4 LOCO p<.01 retained in ≥80% of C(6,4)=15 random subsets AND in leading-4
   - sub-08 V1 LOCO p<.01 retained in ≥80% of subsets
   - sub-08 V1 W-fixed Δλ p<.05 retained in ≥70% of subsets (W-fixed is more brittle than LOCO; threshold relaxed accordingly)
   - sub-09 V1 ΔRDM p<.01 retained in ≥80% of subsets
   - sub-10 V1/hV4 LOCO non-significant (p>.05) in ≥95% of subsets — *false-positive guard*
   - HC LOCO FPR at n=4 ≤ HC FPR at n=6 (no specificity loss)
   - LOCO→JND concordance ≥5/6 at n=4 (loss of ≤1 pair acceptable)
   - 2-component β_s 95% bootstrap CI excludes 0 for both sub-08 and sub-09 V1 at n=4

**Scope clarification (CLAUDE.md §3 compliance)**: Specificity tracking here addresses paradigm sufficiency (does the experiment yield specific results?), not filter selection. The project's no-specificity-claim rule (CLAUDE.md §3) applies to filter selection rule and is not violated by tracking HC FPR / sub-10 null-retention as a run-count diagnostic.

2. **Conditional-5 (5 runs sufficient, 4 not)** if criteria above met at n=5 but ≥2 fail at n=4.

3. **Fail (keep 6 runs)** if any landmark at n=4 retained in <50% of subsets, OR HC FPR rises, OR sub-10 false-positive rate rises.

4. **Independent reporting (not decision-binding)**: saturation curves and Δ_{4→6}/Δ_{2→6} marginal-gain ratios — descriptive evidence accompanying the binary decision.

---

## 5. Deliverables & file paths

- Scripts: `analysis/future_phase3_behavioral_analysis/scripts/run_count_subsample.py` (new wrapper), plus subset-aware patches to `loco_distortion_fit.py`, `diagnostic_delta_rdm.py`. Existing scripts must accept `--run_mask` (binary 6-vector) without re-running SRM training (W is run-position-agnostic at the current stage).
- Results: `analysis/future_phase3_behavioral_analysis/run_count_validation/`
  - `per_subject_per_n_runs.json` (one per subject)
  - `landmark_retention.json` (the §3.3 table)
  - `hc_fpr_per_n.json`
  - `config.json` (single, batch-level)
- Figures (server-only; no seaborn):
  - F1: saturation curves per metric × ROI, random vs leading overlay
  - F2: landmark-retention heatmap (8 anchors × 5 n_runs)
  - F3: HC FPR vs n_runs
  - F4: 2-component β_s/β_c CI shrinkage curves
  - F5: LOCO→JND concordance retention
- Reporting doc: `analysis/future_phase3_behavioral_analysis/run_count_validation/REPORT.md`

---

## 6. References

### Already in NotebookLM (`ColorBlind_comprehensive`, id `fa13d441-21f2-40a0-8170-8cc8eb49cc7b`)
- **Brouwer & Heeger 2009** (JNeurosci 29:13992) — 8–10 runs/session, minimum 8 used for combining; V1 LORO saturates dramatically with more sessions, MT+ barely improves even at 18.
- **Brouwer & Heeger 2013** (JNeurosci 33:15454) — event-related 78 trials/run × multiple runs.
- **Parkes et al. 2009** (J Vision 9:1) — Exp1: 6 runs × 9 trials, Exp2: 5 runs × 12 trials. **Closest paradigm match to ours.**
- **Bannert & Bartels 2018** (Curr Biol) — 6 runs × 36 trials. Real-color block design.
- **Kuriki 2015 / 2025** — 2025 paper: 10 runs/task × 12 hues. Note MEMORY's literature framing entry.
- **Goddard & Mullen 2020** — 6 runs × 29 blocks.
- **Taylor & Xu 2022** — 12 single-conjunction + 12 double-conjunction runs (high run count for orthogonality of color × form).
- **Walther et al. 2016** (NeuroImage) — Crossnobis estimator. Cited in notebook but as secondary reference.
- **Allefeld & Haynes 2014** (NeuroImage 89:345) — cvMANOVA. Cited.
- **Schütt / Diedrichsen RSA simulation** (already in notebook): power-law SNR vs n_measurements; **≥16 runs recommended for RDM-based model discrimination given 5 subjects**.

### Gaps to add to NotebookLM (recommend user import)
1. **Tarhan & Konkle 2020** — "Reliability-based voxel selection" (NeuroImage 207:116350). DOI: 10.1016/j.neuroimage.2019.116350. Direct relevance: split-half reliability of voxel tuning across runs as principled selection; supports our run-count→reliability framing.
2. **Walther et al. 2016** as a *primary* source (currently cited only via Schütt). DOI: 10.1016/j.neuroimage.2015.12.012. Title: "Reliability of dissimilarity measures for multi-voxel pattern analysis."
3. **Valente et al. 2021** — "Cross-validation and permutations in MVPA: validity of permutation strategies and power of cross-validation schemes." NeuroImage 238:118145. https://www.sciencedirect.com/science/article/pii/S1053811921004225 — directly addresses CV-scheme power and is the most relevant 2020+ result for our subsampling design.
4. **Schütt et al. 2023** (eLife, RSA toolbox paper) — already cited; useful to add the full PDF as primary if not yet present (NotebookLM answer cites it indirectly).
5. (Optional) **Naselaris & Kay reviews** — for run-count justifications in encoding/decoding literature; the existing notebook has Kay 2008 noted but specific run counts not in source text.

### Additional candidates from WebSearch (user discretion)
- Stelzer, Chen & Turner 2013 — searchlight permutation power (older but foundational; not in notebook).
- "Stimulus repetition and sample size considerations in item-level RSA" — Lang. Cogn. Neurosci. 39(9), 2023, doi 10.1080/23273798.2023.2232903 — repetition-suppression caveats relevant to our 1 trial/color/run design.

---

## 7. Timeline & dependencies

- **Prerequisite**: Phase 2 closure (Cycle 10c finalized, see `project_phase2_closure.md`).
- **Step 1** (0.5 person-day): write `run_count_subsample.py`; verify subset-mask path through `loco_distortion_fit.py`.
- **Step 2** (1 person-day local, or 1 SLURM array job ~2h on node2): run all C(6,n) enumerations × 3 ROIs × 10 subjects × 5 metrics. Total ≈ 15+20+15+6+1 = 57 subsets × 30 (subject×ROI) × 5 metrics ≈ 8,500 fits. Each fit <1s with current ridge_gcv pooled pipeline.
- **Step 3** (permutation nulls, budgeted explicitly):
  - **Naive scope** (5,000 perm × 57 subsets × 10 subjects × 3 ROIs × ~5 fit-types) ≈ 8.55M fits per metric type, ~99 days serial @ <1s/fit. **Rejected.**
  - **Budgeted scope**:
    - Permute only at n_runs ∈ {4, 6} (the decision boundary). Drop n ∈ {2,3,5} from perm; keep them only for descriptive saturation curves.
    - Permute only at the 8 landmark anchors (§3.3) — fixed subject × ROI × metric combinations, not the full grid.
    - n=6: 1 subset. n=4: C(6,4)=15 subsets random + 1 leading = 16. Total = 17 subsets × 8 anchors × 5,000 perm = 680,000 fits.
    - SLURM array on `--nodelist=node2`, 50 parallel tasks, ~1s/fit → ~4 wall-hours. Realistic.
  - Person-day estimate: 1 person-day to write the perm wrapper, submit, collect.
  - Server constraints: no `--qos`, no `--partition`, `--chdir=<absolute>`, Unix LF, no seaborn.
- **Step 4** (0.5 person-day): figures + REPORT.md.
- **Step 5** (notebook additions, if user approves): import 3 papers above to `ColorBlind_comprehensive`, re-query for confirmatory citations.
- **Total**: ~3.5 person-days (Step 1: 0.5, Step 2: 1, Step 3: 1, Step 4: 0.5, Step 5: 0.5).
- **Anti-pattern guard**: do not reformulate selection rules post-hoc to pass at n=4 (CLAUDE.md §3 — "selection-rule reformulation 금지"). Decision rules (§4) freeze on this plan's commit date.

---

## 8. Honesty addenda

- 4 runs is **below** the simulation-recommended floor (≥16 runs for RDM-model discrimination with 5 subjects, Schütt). Our 6 runs is already below floor; reducing further increases the gap. A "pass" at n=4 in our specific pipeline does not generalize to broader RDM model-comparison claims.
- Existing HC LOCO FPR=7/7 (label-permutation, 6 runs, MEMORY) is the dominant specificity concern. The run-count question cannot be answered favorably without simultaneously demonstrating non-degradation of this number.
- The Phase 3 narrative ("LOCO→JND 6/6 concordance") rests on 6 runs. A 4-run protocol with <5/6 concordance retention forecloses that narrative.
