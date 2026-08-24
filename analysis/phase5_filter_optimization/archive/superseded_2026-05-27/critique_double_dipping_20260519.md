# Pipeline meta-critique: double dipping & beyond (2026-05-19)

**Scope**: Phase 2 (`phase5_filter_optimization/`) adversarial review from the perspective of Reviewer #2 / Nature/NeurIPS standards. Code modification is out of scope. All citations are file:line.

---

## A. Double-dipping mapping (PI 1st critique)

The PI's phrase "selection = evaluation criteria" actually covers four structurally distinct circularity layers that require separate fixes. The table below traces what data/metric is used at each decision stage.

| Step | Data used | Metric | Reused at next step? | Circularity risk |
|---|---|---|---|---|
| **Loss-variant selection** (Cycle 1~15, 15 variants) | HC `boot_frac` over CVD LOCO `vuln` | `boot_frac ≥ 0.975` = "distinct" | Yes — winning variant's `perm_p` reported as paper result | Loss selected from a pool of 15 formulations all in the same LOCO measurement family; `perm_p` at the surviving formulation is post-selection and uncontrolled |
| **Model class selection** (Machado / R+C / 2-comp) | CVD LOCO vulnerability profile | L_fit argmin, then `perm_p` at winner | Yes — `perm_p` of best model reported per subject | 3 models evaluated, winner reported without Bonferroni or model-count correction; `loco_distortion_fit.py:670-694` runs permutation at each model's argmin |
| **(β_s, β_c) grid argmin → permutation test** | CVD LOCO, all 1326 grid points evaluated | `L_fit` argmin at (β_s, β_c) | Yes — permutation null (`permutation_test_spearman`) conditioned on this argmin | `loco_distortion_fit.py:337-396` exhaustive grid; `:530-561` permutes color labels at the argmin only. Null = "what if colors were randomly assigned, but parameters were still this argmin?" The distribution of argmin L_fit across the full landscape is never tested — a critical defect |
| **ROI selection (V4 over V1)** | HC group LOCO ρ permutation (`phase4_forward_model`), THEN CVD L_fit | Forward LOCO gate p=0.044 (uncorrected, n=7, 4 ROIs tested) | Yes — V4 adoption justifies the entire filter coordinate | V1 rejected despite *lower* L_fit (sub-08 V1 L_fit=0.159 vs V4 0.201) and *stronger* perm_p (sub-08 V1 p=0.001 vs V4 p=0.004; `SUMMARY.md:94-97`). V4 wins on a side-criterion from a different analysis that itself has 4-way multiple testing exposure. This is not model-blind ROI pre-selection |
| **HC null threshold** | HC subjects' own LOCO fits (same W, same design matrix) | `boot_frac` (bootstrap over HC mean norm) | CVD distinctness judgment | HC FPR=100% under label-permutation null (confirmed `hc_specificity/`, project memory 2026-04-11). Threshold is not calibrated against a control group whose CVD status is known |
| **Specificity claim via sub-10 exclusion** | sub-10 LOCO fits | sub-10 classified as "CVD-HC indistinguishable" (§A7) AND "dropped out of 2nd-scan" (`BEST_summary.json:cvd_excluded_reason`) | Excludes the one subject that could serve as an in-family specificity control | Two non-equivalent exclusion rationales for the same subject (§A7 vs operational dropout); cannot use sub-10 as null simultaneously |

**Summary of dipping structure**: The same 8-color LOCO vulnerability vector `vuln_cvd` is used to (a) select which loss formulation to run, (b) select which model class wins, (c) define the argmin grid point, and (d) run the permutation test. The permutation test is valid conditional on the triple selection already made — it does not account for any of the selection variance.

---

## B. Top 5 critical weaknesses

### B1. perm_p reported with ★★ but HC FPR = 100%

**Weakness**: The BEST table (`SUMMARY.md:22-23`) headlines `perm_p = 0.004 ★★` (sub-08) and `perm_p = 0.035 ★` (sub-09) with asterisks that any neuroscience reviewer reads as "CVD-distinct from HC." The same document at line 141 states: "HC FPR=100% under `hc_specificity_check.py`." These two claims are in the same document and directly contradict each other. CLAUDE.md §0 forbids specificity claims and restricts `perm_p` to "fit-validity" status, but the summary table does not communicate this demotion — it leads with asterisks.

**What it invalidates**: The primary evidence for "sub-08/09 have a measurable cortical distortion" rests on `perm_p`. If HC subjects routinely pass the same test (100% FPR), the test is uninformative about CVD status. The data underlying MEMORY 2026-04-11 shows sub-08 Δρ rank=5/8 (emp_p=0.50) — worse than three HC subjects — and sub-09 rank=7/8 (emp_p=0.25) with HC sub-03 Δρ=+1.095 exceeding sub-09's. The ★★ claim has a direct numerical counterexample within the same pipeline output.

**How reviewer attacks**: "The authors report p=0.004 for sub-08 yet their own specificity check (CLAUDE.md, `hc_specificity/` directory) yields 100% false positive rate over n=7 healthy controls. By the authors' own evidence, the starred p-value is consistent with being a healthy observer."

**Severity**: Fatal as written (misrepresentation of what `perm_p` means in this context). Addressable by rewriting all asterisk notation, relabeling `perm_p` explicitly as "label-permutation fit-validity (not CVD-vs-HC specificity)", and reporting HC percentile ranks in-line.

**Neutralization**:
- Experiment: Report each CVD subject's LOCO ρ as an explicit percentile of the 7-HC distribution (already computable from project memory: sub-08 emp_p=0.50, sub-09 emp_p=0.25). Do not use asterisk notation.
- Remove `★` from all summary tables; replace with notation like "(rank 5/7 among HC)."
- Effort: 2h (text-only rewrite). Does not require new data.
- Reviewer logic: "The authors use a descriptive position within the HC distribution — this is the honest claim, and it is honest precisely because N is too small for formal inference."

---

### B2. β_s "Emery convergence" claim is internally inconsistent

**Weakness**: `README.md:282-289` states:

> Sub-08 β_s = 20.0 ± 8.0 deg; Sub-09 β_s = 23.0 ± 10.2 deg; Cross-subject mean: ~21.5 deg. Literature (Emery et al. 2021): 21.4 deg B-Y rotation. Independent methods (behavioral hue-scaling vs fMRI ΔRDM fitting) converge within 0.1 deg.

The `BEST_summary.json` (canonical filter) sets sub-08 β_s = **38°**, sub-09 β_s = **6°** (`BEST_summary.json:bs` fields). The "convergence within 0.1 deg" narrative is anchored to a *different* analysis (xnobis bootstrap from `comprehensive_2component_analysis.py`, project memory 2026-04-07: "sub-08 V1 xnobis β_s=20±8, sub-09 V1 xnobis β_s=23±10"). The shipped filter uses neither of those values. Project memory itself explicitly flags this: "Emery 연결은 β_s 수치가 아니라 모델 구조(S-cone축 선택)의 근거. hV4 LOCO 유의성(p=0.004/0.035)이 primary evidence." But README still leads with the parameter-value convergence claim.

**What it invalidates**: The most quotable "biological grounding" result in the pipeline — the Emery convergence — does not apply to the filter that is actually shipped. Reviewer #2 will compute: Emery says 21.4°. Sub-08 filter has β_s=38° (1.77x larger). Sub-09 filter has β_s=6° (0.28x smaller). The match is absent, not present.

**How reviewer attacks**: "Table 1 reports β_s values of 38° and 6°. The Methods section argues convergence with Emery 2021's 21.4° B-Y rotation. 38° ≠ 21.4° and 6° ≠ 21.4°. The convergence statement applies to a different analysis (xnobis bootstrap at V1) that produced different parameters than the filter itself. This is selective reporting."

**Severity**: Fatal for the "physiological grounding via Emery" narrative if the claim remains about parameter values. Addressable by restricting the Emery comparison to model *structure* only (S-cone axis choice), as project memory already instructs, and removing the "within 0.1 deg" language from README.

**Neutralization**:
- Rewrite README L282-289 to: "The choice of S-cone axis (90° in Stockman opponent space) is consistent with Emery et al.'s (2021) cortical B-Y rotation; parameter magnitudes differ per subject and are not expected to replicate exactly across paradigms."
- Report xnobis β_s = 20-23° as a *separate analysis* (V1 ΔRDM fitting), not as a validation of the hV4 LOCO filter.
- Effort: 2h. Does not require new data.

---

### B3. V4 selection rests on a forward LOCO gate that does not survive Bonferroni correction

**Weakness**: The biological rationale for fitting at V4 rather than V1 depends critically on the "forward LOCO gate" (`SUMMARY.md:58-67`, `BEST_summary.json:roi_selection_rationale`): hV4 p=0.044 (single uncorrected, n=7 HC). Four ROIs were tested (V1, V2, V3, hV4). Bonferroni correction sets α = 0.05/4 = 0.0125. The hV4 gate p=0.044 fails this correction by a factor of 3.5.

V1 has lower L_fit (0.159 vs 0.201) and stronger perm_p (sub-08: p=0.001) than V4 (`SUMMARY.md:94-97`). V4 is adopted not because the data prefer it on fit metrics, but because a separately-run gate test at an uncorrected threshold rejects V1/V2/V3. If that gate test is non-significant after correction, the entire V4 vs V1 choice reverts to the fit-metric comparison — which favors V1.

**What it invalidates**: The ROI selection decision and, with it, the interpretation of (β_s, β_c) as "cortical-level" parameters. If V1 is the correct ROI, the filter changes (sub-09 V1 β_c flips sign: +22° vs V4 −22°), the etiology changes, and the "bilateral sub-09 β_c sign agreement" argument (SUMMARY L107-108) is exactly backwards.

**How reviewer attacks**: "The authors justify V4 adoption using p=0.044 from a permutation test over 4 ROIs. Bonferroni correction gives α=0.0125; p=0.044 is not significant. V1 yields better fit statistics (L_fit=0.159 < 0.201; perm_p=0.001 < 0.004). The ROI selection appears outcome-driven: V4 was selected because its parameters produce a biologically preferred interpretation, not because the data require it."

**Severity**: Fatal for the mechanistic interpretation layer. Addressable by either (a) running a properly corrected gate test (ANOVA over 4 ROIs jointly), or (b) reporting V1 and V4 fits symmetrically in the main text without claiming V4 is "the correct ROI."

**Neutralization**:
- Experiment (2h): Report hV4 gate with explicit Bonferroni qualifier: "uncorrected p=0.044; corrected (Bonferroni-4 ROIs) p=0.176, NS." Do not use this as a filter-selection criterion.
- Experiment (2d): Re-run the HC group permutation test with a single pre-planned contrast (hV4 only, planned on biological prior). This requires a pre-registration time-stamp predating analysis — retroactively impossible but honest to state.
- Alternatively, adopt a symmetric report: "V4 and V1 fits are provided; V4 is reported as primary on biological prior grounds alone, not on statistical selection criteria."

---

### B4. g = −2.25 (sub-08, R+C model) is outside published literature and not explained

**Weakness**: Sub-08's R+C diagnostic yields g = −2.25, which means 125% cortical overshoot (`BEST_summary.json:etiology_via_rc_diagnostic`; `SUMMARY.md:31`: "large cortical overshoot"). The cited Tregillus et al. 2021 range is 20–40% overcompensation (g ≈ −1.20 to −1.40). Project memory 2026-04-07 explicitly notes: "Sub-08 g = −2.25... g=-2.25 = 125% overshoot (non-physiological)." The paper retains R+C as a "diagnostic" for etiology interpretation (cortical-dominant sub-08 vs retinal-dominant sub-09), but the diagnostic value of a parameter that lands outside the physiological range is unclear: it could equally indicate a model mis-specification.

**What it invalidates**: The differential-etiology narrative ("sub-08 cortical-dominant, sub-09 retinal-dominant") rests on R+C decomposition. If sub-08's g is non-physiological, the decomposition is unreliable for sub-08. The same data point (sub-08) that provides the most statistically robust fit (boot_frac=1.000) is also the one whose R+C diagnostic is outside any published parameter range.

**How reviewer attacks**: "The authors claim sub-08 shows 'cortical-dominant CVD etiology' based on g=−2.25 from their R+C model. No published study of cortical plasticity in CVD has reported compensation exceeding ~40% (Tregillus 2021). At 125% overshoot the parameter is outside the physiological regime; it may reflect overfitting of the 2-parameter R+C model to 8 data points. This calls into question whether the 'diagnostic' is informative for sub-08 at all."

**Severity**: Addressable (does not invalidate the 2-comp filter; R+C is stated as diagnostic-only). But it weakens the paper's most novel mechanistic claim (differential etiology).

**Neutralization**:
- Experiment (2d): Constrain g to Tregillus physiological range [−1.5, 0.5] and report the constrained fit. If sub-08 L_fit degrades substantially under the constraint, that's evidence for model mis-specification; if it doesn't, the unconstrained g was likely an artifact.
- Framing: "Sub-08 R+C fit produces g outside the published physiological range; we therefore interpret the etiology flag conservatively as 'inconsistent with purely retinal etiology' rather than 'cortical-dominant.'"
- Effort: 2d.

---

### B5. N=2 with no between-subject replication and inconsistent sub-10 rationale

**Weakness**: The paper has N=2 CVD subjects (sub-08, sub-09). Sub-10 (mild deutan) is excluded under two non-equivalent rationales documented in the same pipeline:
- CLAUDE.md §A7: "sub-10 분석 제외 — CVD-HC 차이 미포착, downstream 분석에서 제외" (outcome-based exclusion: sub-10 looks like HC)
- `BEST_summary.json:cvd_excluded_reason`: "sub-10 dropped out of 2nd-scan behavioral acquisition" (operational exclusion)

The outcome-based rationale is circular: sub-10 was classified as normal-appearing by the same pipeline that now claims to detect CVD distortion. The operational rationale is factually independent but was not stated as the pre-specified exclusion criterion. SUMMARY.md L77-84 uses only the operational rationale. Using the outcome-based rationale in any public document creates a circularity path.

Additionally, CLAUDE.md §A8 acknowledges that "8 colors / 4 ROIs = 32 dof로 다중 mechanism 분리 한계" — the DOF comment undermines the three-model comparison (Machado 1-DOF / R+C 2-DOF / 2-comp 2-DOF all fitted to 8 data points), making the "best model" selection ambiguous even without selection inflation.

**What it invalidates**: The generalizability of the filter (N=2, single family each), the exclusion of the only data point that could anchor an in-family specificity test (sub-10 = mild deutan, same family as sub-08), and the differential mechanism claim which has exactly one subject per mechanism level.

**How reviewer attacks**: "The authors exclude their third CVD subject on grounds that they could not distinguish them from HC — using the same pipeline they are presenting as the detection tool. This is circular. Furthermore, no independent deutan or protan replication subject exists: each mechanistic finding (cortical-dominant vs retinal-dominant) rests on a single subject. N=1 per claim is not a finding."

**Severity**: Fatal for generalization claims. Addressable for a "proof-of-concept" framing explicitly limiting scope to N=2 case study.

**Neutralization**:
- Framing (2h): Replace "inverse filter" with "personalized filter derivation proof-of-concept, N=2." All mechanism claims become "consistent with" rather than "demonstrates."
- Sub-10 exclusion: State only the operational reason (behavioral dropout) in the paper. Never use the outcome-based reason (CVD-HC indistinguishable) in a public document.
- Future work: Specify replication plan (≥1 additional deutan + ≥1 protan, full pipeline, pre-registered) as a stated gap. `SUMMARY.md:166` already lists this — move it to the Abstract limitations sentence.

---

## C. Additional risks not in PI feedback — Top 3

### C1. Grid-search argmin permutation test is not a valid null for selection inflation

`loco_distortion_fit.py:530-561` runs `permutation_test_spearman(best_vuln_sim, vuln_cvd)`, where `best_vuln_sim` is the simulated vulnerability at the **grid argmin**. The permutation null shuffles color labels, but keeps the argmin parameters fixed. This does not test "what is the best perm_p over the full 1326-point grid under a random null?" — which is the correct question.

The correct null distribution is: for each permuted label assignment, run the full 1326-point grid and take the argmin perm_p. This is the "end-to-end LOO + full-null" the PI calls for. The documented null is ~3 orders of magnitude computationally cheaper but also ~3 orders of magnitude more anti-conservative. For a 26×51 grid with n=8 colors, the chance of finding *some* grid point with good rank correlation under a random null is substantially higher than the 1/40320 = 2.5×10^−5 suggested by the label-perm probability. The reported p=0.004 and p=0.035 are lower bounds, not actual p-values.

**No fix currently exists in the pipeline.** The correct null requires full-grid refit under each permutation — estimated 1326 × 40320 evaluations per subject (~53M function calls). At the current SLURM throughput, this is a 2w computation. A cheaper approximation is to run n_perm=1000 full-grid permutations (1.326M calls) and check whether any permuted label set finds a better grid argmin than the real data. This is the test that should appear in the Methods.

**Severity**: Addressable (required for publication). Effort: 2w on server.

### C2. Stimulus equiluminance is violated by the filter and the pipeline does not account for it

The filter rotates hue angle while assuming L*=75 remains constant post-correction. `README.md:92-97` documents a "luminance-aware rendering" fix as a *display* control: "This is a display/data-presentation control, not a constraint on the filter." For protan observers, shifting hue angle along the confusion axis changes the L-cone activation, which changes perceived luminance even when photometric L* is controlled. Correcting cyan→blue (sub-09 δθ = +21.1° at blue) while maintaining CIE L*=75 does not guarantee equal effective luminance for a protan with shifted L-cone fundamentals.

The behavioral test will therefore confound hue correction with a luminance change. The Stockman cone fundamentals in the pipeline could compute the predicted ΔL* under the filter shift, but this is not done for the corrected stimuli themselves — only for the display simulation. This is a gap between the pipeline's internal awareness of the issue and its practical resolution.

**Severity**: Addressable (requires computing predicted cone-activation-weighted luminance for each corrected angle and verifying ΔL* < 1 JND). Effort: 2d.

### C3. HC W precomputed with all 7 HC included in the pool used to evaluate CVD "distinctness"

`loco_distortion_fit.py:643`: `hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_original)`. The same `hc_W_dict` is used to simulate `vuln_sim` under parameter sweep AND to compute `delta_rdm_obs` at line 649-651. The `delta_rdm_obs` comparison (`Δrdm_cvd - mean_HC_RDM`) uses the same HC pool as the W-training set. When sub-04 is in both the training pool and the reference distribution, sub-04's atypical encoding inflates the HC mean W, which affects both the simulation and the observed RDM target. CLAUDE.md §2.5 acknowledges sub-04 as a mean-distorting outlier — but the pipeline never excludes sub-04 from the reference pool in sensitivity analysis. The 15 loss variants in `loss_inventory.md` were all evaluated under sub-04-inclusive HC mean; CLAUDE.md §2.5 caveat only: "sub-04 제외 시 boot_frac 1.000으로 더 강해짐" for sub-08. Sub-09's sub-04 dependence is the opposite direction.

A LOO-HC robustness check (compute (β_s, β_c) under each of 7 HC leave-one-out pools, report range) has been proposed but never run (SUMMARY.md:168 lists "LOHO robustness" as a Next Step). If sub-09's LOCO-canonical (β_s=6, β_c=−22) shifts by more than 10° under LOHO, the Phase 2 BEST table is unstable to the reference pool composition.

**Severity**: Addressable. Effort: 2d.

---

## D. Priority list — top 3 most urgent verifications

**D1. End-to-end LOO permutation test (PI #1 / C1 above)** — HIGHEST PRIORITY

Design: For sub-08 and sub-09, run N_perm = 1000 full-grid permutation fits: in each permutation, shuffle the 8 color labels in `vuln_cvd`, then run the complete 26×51 grid search, and record the minimum L_fit achieved. Construct the null distribution of "best achievable fit under random labels." Report the fraction of permuted runs that achieve L_fit below the real-data argmin. Compare against current `label_perm_p` to quantify how anti-conservative the present test is.

Compute cost estimate: 1000 × 1326 = 1.326M grid evaluations per subject. At ~50ms/eval on node2, ~18h per subject. Two subjects = ~36h, one SLURM job per subject with --time=48:00:00.

**D2. LOHO (leave-one-HC-out) stability of (β_s, β_c)** — HIGH PRIORITY

Design: For each of 7 HC subjects {01..07}, remove that subject from the HC pool, recompute W on the remaining 6, refit (β_s, β_c) for sub-08 and sub-09 via the same 1326-point grid, record the resulting filter parameters. Report the range and SD of (β_s, β_c) across 7 LOHO runs. If β_s or β_c range exceeds ±10°, the filter is unstable to reference pool composition and must be qualified in the paper as "conditional on full HC pool."

Compute cost estimate: 7 × 2 × 1326 = 18,564 grid evaluations per subject. At ~50ms/eval, ~15 min per subject. Trivial on node2 as a single array job.

**D3. Behavioral-only ablation of model classes (PI #4)** — MEDIUM PRIORITY

Design: Fit Machado, R+C, and 2-comp to sub-08/09 color-naming P2a data alone (the pre-Phase-2 behavioral report, which already exists) without any fMRI LOCO signal. Find the (β_s, β_c) or (Δλ, g) that maximizes P2a agreement with the existing data. Compare the behavioral-only (β_s, β_c) to the neural-fit (β_s, β_c) = (38,−14)/(6,−22). If they agree, fMRI adds nothing beyond behavior. If they disagree, the disagreement is the paper's novel contribution — and needs to be framed as such rather than concealed. This is the experiment that isolates what the neural measurement contributes over psychophysics.

Compute cost estimate: No new data collection needed; uses existing color-naming reports + analytical fitting. Effort: 2d.

---

## File references

- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/results/SUMMARY.md` — L22-23 (perm_p ★★), L58-67 (forward LOCO gate), L94-97 (V1 vs V4 fit comparison), L117-127 (three convergent failures), L141 (HC FPR=100%), L282-289 (β_s Emery claim)
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/results/BEST_summary.json` — `current_best.sub-08.bs/bc` (canonical filter params), `roi_selection_rationale.supporting_forward_loco_gate` (uncorrected p=0.044), `framework_caveat` (HC FPR admission)
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/scripts/loco_distortion_fit.py` — L337-396 (grid search), L530-561 (permutation test at argmin only), L643-651 (HC W precomputation and ΔRDM using same pool), L670-694 (model loop without cross-model correction)
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/CLAUDE.md` — §0 (specificity claim ban), §A7 (sub-10 outcome-based exclusion), §A8 (8-color DOF ceiling), §2.5 (loss inventory + sub-04 outlier)
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/README.md` — L282-289 (β_s Emery convergence claim anchored to wrong analysis)
