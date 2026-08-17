# 검토자 회신안 — 리포트에 없던 정보 · 정정 · 되묻는 질문 (2026-08-15)

> **용도**: [`REVIEW_JOURNAL_STRATEGY_2026-08-15.md`](REVIEW_JOURNAL_STRATEGY_2026-08-15.md) 를 준 검토자에게 그대로 보낼 수 있는 회신 초안. 본문은 영문. **원칙**: 리포트의 결론 대부분을 채택한다. 다만 **검토자가 갖고 있지 않았던 산출물 5건**이 우선순위를 바꾸므로 그것을 먼저 알린다. 방어가 아니라 정보 갱신이다.

---

## Draft response

Thank you — the framing recommendations (§1–6, §19) are adopted essentially in full, and the claim hierarchy will govern the Abstract, Results interpretation, Discussion, and cover letter.

Five analyses completed between 2026-08-06 and 2026-08-10 were not available when the report was written. They do not overturn the report's conclusions, but they change which items are still open and, in two places, the recommended priority. Details below, followed by five questions.

---

### 1. The 1.9 mm / 9.4 mm figures are our own measurement, and the same test carries a baseline the report omits

The displacement figures cited in §9 come from our defacing sensitivity test (FreeSurfer 7.2.0 + FSL `bet2`, `mri_coreg --regheader`, SLURM job 164976, 2026-08-07). That test also measured **run-to-run coregistration variability within a session**, which is the reference scale for judging whether the defacing displacement matters:

| | defacing displacement | run-to-run variability (ses-1 / ses-2) | ratio |
|---|---|---|---|
| deutan | 1.95 mm | 1.78 / 4.18 mm | **0.5×** |
| protan | 9.43 mm | 0.93 / 3.02 mm | **3.1×** |

In the deutan participant the defacing displacement is *smaller* than the coregistration jitter between runs of the same session. The asymmetry is materially consequential in the protan participant only — which happens to be the participant carrying the anomalous neural result, so the report's concern stands for that case, but not as a general property of the dataset.

A second result from that test bears on §10. In the protan participant the two solutions differ by a rotation about x of $+5.75^\circ$ (original) versus $-1.29^\circ$ (defaced), and both are plausible small rotations. They are two local optima of a shallow mutual-information cost, not a correct and an incorrect solution. **Harmonizing the anatomical treatment removes the asymmetry but does not by itself establish which registration is more accurate.** We therefore plan to run an independent registration-accuracy QC (occipital Dice, visual inspection) alongside the harmonization, kept orthogonal to the color endpoints so that it cannot function as endpoint selection.

### 2. The asymmetry has two layers, and Options A and B remove only one

Code review confirms the sessions differ in more than defacing. Session 1 uses the session-1 T1w (ezBIDS, defaced); session 2 uses **its own session-2 T1w** (dcm2bids 3.2.0, undefaced), with an independent T1w→MNI normalization. Everything downstream of the anatomical is identical (`mri_coreg --regheader` MI, FLIRT 12-DOF → FNIRT, `MNI152NLin2009cAsym` res-2).

Matching the defacing convention (Option A or B) leaves the two sessions referenced to two different anatomical volumes and two independently estimated normalizations.

We propose **Option D**: reference both sessions to the session-1 anatomical, composing `BOLD → ses2-T1w → ses1-T1w → MNI` with a 6-DOF whole-brain rigid registration between the two T1w volumes. This removes both layers at once. It also has two practical advantages over Option B, which we consider the riskier route:

- It leaves every session-1 endpoint unchanged **by construction**, so the primary representational findings are not reopened. Under Option B they would all be recomputed, including endpoints already cross-validated across three preprocessing arms (item 3 below).
- It moves the asymmetry out of the ill-conditioned step. The underlying problem is registering a 24-slice occipital BOLD volume to a whole-brain T1w under a shallow MI cost. T1w-to-T1w registration does not have that problem.

If the report sees a reason to prefer A or B over D, we would want to hear it before freezing the plan.

### 3. Preprocessing robustness is established for session 1 on the temporal axis only — the registration axis has never been perturbed

Every session-1 neural endpoint was recomputed on three arms — the primary arm, a motion-regression arm (six motion parameters plus temporal derivatives), and a **circular-shift control** in which the same twelve regressors are entered with their temporal alignment destroyed.

- The hV4 interpolation gate survives in all three arms ($p$ = .011 / .013 / .002), and no other ROI passes in any arm.
- The single-case interpolation contrasts lose significance under motion regression through an inflation of the control dispersion that the shifted control reproduces **without removing any motion-aligned variance** — so the loss of power is attributable to the twelve added regressors, not to motion removal.
- Color-specificity detection rises from 7 to 15 cells under motion regression but falls to 3 under the shifted control, which rejects the "regressor artifact" account and attributes the increase to removal of motion-aligned variance.

Two gaps remain, and we want to be precise that these arms do not close either of them.

**These three arms perturb the temporal axis, not the spatial one.** Motion regression acts on the second-level design matrix and changes the variance composition of the timeseries; it does not move signal between voxels, so voxel identity and ROI membership are invariant. Changing the registration acts upstream of everything and changes which anatomical location each analyzed voxel corresponds to. A 9.4 mm displacement moves voxels across ROI boundaries that are millimeters apart in occipital cortex. The two perturbations therefore have different signatures, and passing one carries no information about the other:

- Under motion regression the control mean was preserved (0.456 → 0.458) and only the dispersion inflated, because no signal moved between voxels. A registration change can move the mean itself, by changing which voxels constitute hV4.
- LOCO reads the structure of a voxel pattern. Adding regressors costs degrees of freedom but leaves the spatial arrangement intact; a registration shift rearranges the pattern.
- Most importantly, motion regression is applied identically to every subject and session, so its cost largely cancels in a between-condition difference. The defacing asymmetry applies to session 1 only and acts differentially across participants (0.5× versus 3.1× relative to run-to-run jitter), so it enters the difference directly. The three arms test the first kind of perturbation; the reanalysis targets the second.

The two remaining gaps are therefore: **(i) the session-2 endpoints have never been recomputed on any arm**, which the harmonization covers; and **(ii) the session-1 endpoints have never been perturbed on the registration axis at all.**

For (ii) we plan a fourth arm in the same format as the motion arms, which does not require recovering a non-defaced session-1 anatomical: apply a rigid perturbation of the magnitude we actually measured (the $+5.75^\circ$ versus $-1.29^\circ$ difference in rotation about x, and translations of 1.9 and 9.4 mm) to the BOLD→T1w transform, then recompute the session-1 primary endpoints. If the hV4 interpolation gate survives its own permutation null under that perturbation, Scenario C is excluded. If it does not, that is a more serious problem than the cross-session asymmetry and would take priority over both the reanalysis and the journal discussion.

### 4. The identifiability conclusion in §13 has since been tested directly

We refit each participant's selected loss combination on the motion-regressed amplitudes, holding the combination, grid, resampling count, and seed fixed, with a reproduction gate confirming the published values first. Result:

| | primary arm | motion-regressed arm | $\beta_c$ sign |
|---|---|---|---|
| deutan | $(6^\circ, -42^\circ)$ | $(20^\circ, -48^\circ)$ | negative in 300/300 in **both** arms |
| protan | $(2^\circ, +24^\circ)$ | $(22^\circ, -24^\circ)$ | **reverses**: 263/300 positive → 300/300 negative |

This confirms §13 from an axis the report did not have. The deutan sign is preprocessing-robust; the protan sign is not, adding a second dependency to the basis-dependence already documented. The manuscript language has been prepared accordingly, treating the parameters as a descriptive embedding. We note additionally that the deutan fit's boundary-saturation rate rises from 0.09 to 0.73 in the regressed arm, so its *location* is not robust even where its sign is.

### 5. The protan JND anomaly noted in §7 has been diagnosed

An exhaustive scan of all 208 staircases collected in the study identified the source of the elevated staircase disagreement in the protan individualized condition: a single track in the orange–yellow pair, which settled four times higher after answering correctly at a four-times-smaller separation earlier in the same block. Its partner staircase converged normally on the same rendered stimuli, which excludes a rendering or gamut failure. Removing that pair returns the condition's staircase disagreement to the participant's own baseline level. The green–blue result that carries the protan behavioral claim is unaffected (both tracks converged). The pair is reported on the two-track average as everywhere else, with the discrepancy disclosed.

The same scan found that the deutan orange–yellow baseline threshold is **censored at the largest presentable separation** — the only such case among the 208 staircases. That censoring understates the baseline deficit and therefore also understates the improvement recorded under either filter.

### 6. Two items the report did not raise that we expect reviewers to raise

**(a) The 8AFC contrast in the protan participant may be stronger evidence than §7 credits.** We agree that 8AFC is the cleaner readout because it was held out from the fitting loss. Its values are: unfiltered 1.00 (95% CI [0.94, 1.00]), individualized 0.98 ([0.92, 1.00]), deployed 0.86 ([0.75, 0.92]). On the only behavioral endpoint that did not contribute to model fitting, the deployed comparator degraded normal-level identification while the individualized filter preserved it. This is currently reported in a single sentence at the end of a JND paragraph. We intend to separate it as an independent endpoint. We would value the report's view on whether that changes the §17 scenario weighting.

**(b) Functional-meaningfulness benchmarking against Patterson et al. (2022).** We use that paper in the Introduction to characterize the limits of existing filters, which obliges us to apply its criterion to ourselves. Using between-staircase disagreement as the JND-unit noise floor: the deutan baseline-to-individualized change is 6.09× the floor (the only filter passing in Patterson, VINO, was 4.2×); the protan change is 1.48×. The protan value requires an equivalence framing rather than a superiority ratio, because that participant's baseline is already at control level, so a small change is the intended outcome. The important limitation is that our floor is a **within-session** quantity while Patterson's retest SD is **between-session**, so our ratios are an optimistic bound and not a like-for-like reproduction. We have no repeated-session JND data to close that gap. We would welcome a view on whether to report this and, if so, whether it belongs in Results or the Supplement.

---

### Questions

**Q1 — Does §11 make the reanalysis gating for journal selection, or only for reviewer defense?** The report notes that the within-session-2 contrast (0.19 deployed versus 0.06 individualized in the protan participant) cannot be explained by the session-1/session-2 anatomical asymmetry. If that is right, then harmonization cannot rescue the protan intervention result under any outcome, and the manuscript is in Scenario B already. In that case the reanalysis is necessary as a defense against a predictable reviewer question, but it is not informative for the journal decision — which would mean journal selection need not wait on it. Is that reading correct, or is there an outcome of the reanalysis that would return the manuscript to Scenario A?

**Q2 — Is Option D acceptable as the symmetry route?** See item 2 above.

**Q3 — Does the revised Validate question in §5 need a directional prediction?** "Does applying the individually derived filter produce measurable changes in neural and behavioral color processing?" is satisfied by a change in either direction, which a methodological reviewer may read as unfalsifiable. We can pre-specify a direction for the psychophysical endpoint (thresholds move toward the control range) while leaving the neural endpoint descriptive, but that reintroduces an asymmetry between the two. Which trade would the report prefer?

**Q4 — Should 8AFC be elevated to a primary behavioral endpoint?** It is the only behavioral measure held out from the fitting loss. Elevating it makes the prospective claim cleaner but reduces the weight of the JND results, which carry the deutan normalization finding.

**Q5 — Why is eLife absent from §17–18?** Our existing target plan lists eLife first, with Journal of Neuroscience as the safe option. The reviewed-preprint model would let the methodological questions raised in this report be adjudicated in public review rather than pre-emptively resolved, which seems well matched to a manuscript whose main vulnerability is methodological rather than evidential. We would want to know whether eLife was excluded deliberately.

**Q6 — Section numbering.** The report refers to §3.10 and §4.3. Please confirm these map to the Results filter-evaluation subsection and the Discussion validation subsection respectively, so that our revisions target the intended text.

---

## 부록 — 회신에 넣지 않은 판단 (내부용)

| | |
|---|---|
| 리포트 §15 순위 | 우리 상태에 맞춰 재배열하면 #2(일반 전처리 강건성)는 exp1 에서 이미 내려갔고, #4(식별성)는 U2 로 종결됐다. 실질 잔여는 **#1(exp2 세션 간) · #3(신경 개입 비일관) · #7(비교자 비대칭)** 셋 |
| 리포트에 동의하지 않는 유일한 지점 | 없음(결론 층위). 다만 **우선순위**는 다르다 — N2·N3·N4 는 N1 결과와 무관하므로 대기시키지 않는다 |
| 회신에서 뺀 것 | sub-10 제외 사유(2차 세션 미통과). 리포트 판단에 영향 없고, 설명 비용만 든다 |
| Q1 의 의도 | 리포트가 "저널 선택을 N1 뒤로" 라고 했는데, 자기 §11 과 긴장이 있다. 이 긴장을 지적하면 N1 공수 산정이 정확해진다 |
