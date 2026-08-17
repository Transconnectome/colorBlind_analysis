# Final Journal Submission and Manuscript Strategy Report

> **출처**: 외부 검토 리포트, 수령 2026-08-15. 원문 그대로 보존한다 (편집 금지).
>
> **성격**: 이 문서는 *입력*이다. 우리 쪽 대응 현황과 판정은
> [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md) 에서 관리한다.
>
> **주의**: 이 리포트는 2026-08-06 ~ 08-10 사이에 종결된 작업(움직임 3-arm 검정, U2 β_c 부호,
> JND staircase 진단)을 반영하지 않은 시점의 검토다. 중복 착수 전 status 문서를 먼저 볼 것.

**Manuscript**: Individual-specific distortion of cortical hue geometry in color vision deficiency informs personalized color correction

---

## Executive Summary

This manuscript has a credible path to a strong neuroscience or vision-science journal, but journal selection should not yet be finalized. The highest-priority next step is not collecting a larger CVD cohort or adding exploratory analyses. It is resolving a potentially consequential cross-session registration/preprocessing asymmetry and determining whether the Session-2 neural evaluation remains qualitatively unchanged.

The manuscript should be positioned as an individual-level human visual neuroscience proof of principle. Its central contribution is not that a new color-correction method has been shown to outperform existing filters. Rather, the study shows that, in two individually characterized CVD cases:

1. hue identity remains cortically decodable;
2. continuous/relational hue representation is nevertheless disrupted;
3. aspects of that distortion can be summarized by an individualized cortical model;
4. the fitted transformation can be inverted into a physically realizable, individually derived stimulus filter; and
5. applying the frozen filter prospectively produces measurable behavioral and neural consequences.

The study does not establish that individualized filters reliably normalize cortical representation, outperform deployed filters at the population level, or work specifically because each filter is matched to its respective individual. The last claim would require a crossed-filter or other appropriate personalization-control design, which the present experiment does not contain.

The principal vulnerabilities are therefore not simply the CVD sample size of N=2. They are:

1. cross-session comparability and registration robustness;
2. inconsistent neural effects of the individualized intervention;
3. incomplete parameter identifiability;
4. lack of an independent unfiltered test–retest measurement of the inferred individual distortion;
5. colorimetric/luminance limitations; and
6. asymmetry between the individualized and deployed filter implementations.

The appropriate journal should be selected after the registration reanalysis, because that result could materially change §3.10, §4.3, the Abstract, and the overall interpretation of the intervention experiment.

---

## 1. Scientific Identity of the Paper

The manuscript should not primarily be framed as:

> A new treatment for color vision deficiency.

Nor should it be presented as:

> A conventional fMRI comparison of N=2 CVD participants against N=7 controls.

The stronger scientific identity is:

> An individual-level human visual neuroscience study asking whether an altered cortical sensory representation can be characterized, computationally summarized, inverted into an individualized stimulus transformation, and prospectively evaluated.

The experimental structure supports this framing. Session 1 characterizes each participant's cortical color representation, fits the distortion, and derives an inverse transformation. Session 2 prospectively evaluates the frozen filter using fMRI and psychophysics.

The conceptual sequence is therefore:

**Measure → characterize → model → invert → intervene → evaluate**

This is more compelling as a systems/computational visual-neuroscience study than as an accessibility-filter efficacy study.

---

## 2. Strongest Scientific Finding

The strongest result is the dissociation between preserved hue information and disrupted relational representation.

All eight hues remain decodable in the two CVD participants, including transfer from an encoder derived from healthy controls. This indicates that cortical information about individual hue identity is not abolished.

However, continuous hue interpolation at hV4 is substantially impaired. In the healthy controls, hV4 supports above-null interpolation, whereas both CVD participants fall substantially below the control distribution. The impairment is especially pronounced around blue, purple, and magenta.

Representational geometry also differs between individuals: the strongest deviation occurs at V1 in the protan participant and primarily around V2 in the deutan participant, although the latter is less robust to the symmetric reference analysis.

The strongest defensible neuroscience statement is therefore:

> In these two CVD cases, hue identity remained cortically decodable despite disruption of the continuous relational organization of hue representations, and the observed representational deviations differed between individuals.

This should be the manuscript's primary discovery.

The filter should follow from this finding rather than replace it as the headline result.

---

## 3. How N=2 Should Be Framed

The manuscript should neither apologize for N=2 nor use "precision neuroimaging" as a blanket justification for any inference from two participants.

The correct argument is narrower.

The study does not estimate a population-level CVD effect. The manuscript explicitly uses single-case comparisons and states that population-level claims about protan and deutan subtypes require additional participants.

The inferential structure is instead:

```
individual cortical representation
→ individual fitted model
→ individually derived transformation
→ prospective evaluation in that observer
```

The manuscript itself states that the filter operates at the level of the individual observer and that the present experiment tests feasibility rather than superiority over a subtype-average correction.

That is a defensible individual-level neuroscience design.

However, the manuscript should not overstate the depth of the precision-neuroimaging evidence. There is only one baseline characterization of each individual's distortion, followed by an intervention session. There is no independent unfiltered test–retest session demonstrating that the inferred cortical phenotype and fitted parameters reproduce across sessions.

The appropriate description is therefore:

> An intensively characterized individual-case proof of principle with prospective intervention testing, but without independent test–retest replication of the baseline cortical distortion.

---

## 4. What "Individualized" Means—and Does Not Mean

This distinction should be made explicit throughout the paper.

### 4.1 Personalized/individualized construction — demonstrated

Each participant's neural and psychophysical measurements generate that participant's own fitted model and filter.

The two resulting transformations are demonstrably different. Their dominant confusion-axis components differ in direction, and the resulting corrections even point in opposite directions for yellow and purple.

Therefore: **The filters are individually derived.** This is directly demonstrated.

### 4.2 Prospective within-person effects — demonstrated at proof-of-concept level

Each frozen individually derived filter is subsequently applied to the participant from whom it was derived, and behavioral and neural measurements are collected.

Therefore: **The prospective consequences of applying an individually derived transformation can be measured.** This is also demonstrated.

### 4.3 Personalization advantage — not demonstrated

The experiment does not include a crossed-filter design:

- Participant A + Filter A versus Participant A + Filter B
- Participant B + Filter B versus Participant B + Filter A

Consequently, the present data cannot establish:

> The matched individualized filter works better because it is specifically matched to that individual.

Nor can they establish superiority over a subtype-average individualized model.

The manuscript already correctly states that comparison against a subtype-average correction would require several individuals within the same subtype.

Thus, terminology should distinguish:

- **individualized construction** — established;
- **within-person prospective consequence** — demonstrated preliminarily;
- **personalization advantage** — not tested.

This distinction eliminates the need for a cross-filter result that the present experiment does not contain.

---

## 5. Recommended Four-Question Structure

The existing Describe → Summarize → Correct → Validate architecture is strong and should be preserved.

The problem is not the architecture but the definition of validation.

The current fourth question asks whether the individualized filter moves cortical representation closer to the healthy-control reference than a deployed accessibility filter.

That criterion is stronger than what the current neural results consistently demonstrate.

However, replacing it with an open-ended question such as "How does the filter alter neural and behavioral measures?" would weaken the manuscript and could appear post hoc.

A better structure is:

**1. Describe** — Does an individual's cortical hue geometry in CVD carry structured distortion, with individual hues remaining decodable while their continuous arrangement is impaired?

**2. Summarize** — Can a small number of interpretable parameters provide a compact operational description of that distortion?

The phrase *operational description* is important because the fitted parameters should not be interpreted as precise physiological measurements.

**3. Correct** — Can the fitted individual distortion be inverted into a realizable stimulus-space filter?

This is strongly supported. The inversion succeeds for all eight target hues to within 10⁻³ degrees.

**4. Validate** — Does applying the individually derived filter produce measurable changes in neural and behavioral color processing?

This is a genuine prospective validation question without requiring an unsupported personalization advantage.

An alternative, somewhat stronger formulation is:

> Do the individually derived filters produce measurable changes in their respective observers' neural and behavioral color processing?

The wording should avoid "individual-specific effects", because demonstrating that the effect itself is specific to the matching individual would require cross-filter data.

---

## 6. Validation Should Be Hierarchical

The evaluation should distinguish three questions rather than treating them as equivalent.

**Primary feasibility question** — Can the fitted cortical model be converted into a physically realizable individualized transformation? → **yes.**

**Prospective consequence question** — Does applying that frozen transformation subsequently alter measured behavior and/or cortical responses? → **yes**, although the direction and consistency differ across outcomes and individuals.

**Strong efficacy question** — Does the transformation reliably normalize cortical representation and outperform a deployed filter? → **not established.**

This hierarchy allows the manuscript to retain a falsifiable validation stage without defining the entire study as unsuccessful because the strongest efficacy criterion is not consistently satisfied.

---

## 7. Behavioral Evaluation

The behavioral results provide meaningful proof-of-concept evidence.

In the deutan participant, the three substantially elevated baseline discrimination thresholds return to within the healthy-control range under both filters.

In the protan participant, the individualized filter reduces the elevated green–blue threshold to approximately +0.9 control SD and keeps all tested pairs within approximately ±1.5 SD. In contrast, the deployed filter produces large deviations in green–blue and cyan–magenta.

However, this should not be described as proof of superiority.

The manuscript itself appropriately concludes that more participants are required to establish whether the individualized filter outperforms the deployed comparator.

There is also an important distinction between behavioral endpoints.

The JND measurements contributed to model fitting, whereas the 8AFC identification measure was held out from the fitting loss. The second-session JND results therefore constitute prospective evaluation of a frozen model, but not a fully independent behavioral validation of the model's construction.

The 8AFC task provides the cleaner independent behavioral readout.

---

## 8. Neural Evaluation Remains a Major Scientific Limitation

The individualized filter does not consistently move the measured neural representation toward the healthy-control state.

At hV4, individualized filtering increases adjacent interpolation accuracy in the deutan participant but decreases it in the protan participant. The protan individualized condition reaches 0.06 compared with 0.14 at the unfiltered baseline and 0.19 under the deployed filter.

Representational geometry is similarly heterogeneous. In the deutan participant, both filters move V2 disparity farther from the HC reference. In the protan participant, disparity improves under both filters, whereas RDM similarity favors the deployed condition rather than the individualized condition.

Therefore the study does not establish:

> The individualized filter restores cortical hue representation toward normal.

This should remain explicit.

---

## 9. Highest-Priority Technical Issue: Cross-Session Registration

Before journal selection or submission, the cross-session registration/preprocessing asymmetry should be resolved.

Session 1 and Session 2 were not anatomically processed identically: Session 1 used an ezBIDS conversion that defaced the anatomical image, whereas Session 2 used dcm2bids and retained the undefaced anatomical.

This matters because the registration is demonstrably sensitive to changes outside the brain. Removing facial voxels while leaving the brain unchanged moves the estimated coregistration solution by:

- **1.9 mm** in the deutan participant
- **9.4 mm** in the protan participant

The manuscript itself concludes that the mutual-information optimum is shallow under the limited occipital field of view.

This becomes particularly important because:

- Unfiltered baseline = Session 1
- Individualized + deployed filters = Session 2

Therefore a baseline-versus-filter neural difference potentially contains:

> filter effect + session effect + registration/preprocessing asymmetry.

The problem is especially consequential in the protan participant, who shows both the largest registration sensitivity and the most anomalous neural intervention result.

This does not establish that registration caused that result. It establishes a credible alternative explanation that should be excluded before submission.

---

## 10. Required Reanalysis Before Submission

The anatomical treatment of Session 1 and Session 2 should be made symmetric.

For example:

**Option A** — Session 1 defaced anatomical; Session 2 equivalently defaced anatomical.

or, if technically and ethically feasible:

**Option B** — Session 1 original non-defaced anatomical; Session 2 non-defaced anatomical.

The important feature is symmetry rather than which convention is selected.

The critical neural endpoints should then be recomputed without changing downstream analytical choices in response to the result.

Ideally, the reanalysis plan should be frozen beforehand:

- anatomical treatment;
- registration procedure;
- ROI definitions;
- LOCO/LORO procedures;
- disparity calculation;
- RDM similarity;
- predefined target ROIs;
- comparison rules.

This makes the analysis a transparent sensitivity analysis addressing an identified technical asymmetry, rather than an optimization exercise.

---

## 11. What the Registration Reanalysis Can and Cannot Resolve

The reanalysis could substantially strengthen or change Session-1 versus Session-2 comparisons.

For example, it could determine whether the apparent protan reduction from 0.14 unfiltered → 0.06 individualized survives technically symmetric registration.

However, it cannot explain every neural result.

The deployed and individualized filters are both measured in Session 2. Therefore the within-Session-2 difference — 0.19 deployed versus 0.06 individualized — cannot be attributed simply to the Session-1/Session-2 anatomical asymmetry.

Thus, even if harmonized registration alters baseline-to-filter contrasts, the deeper issue of inconsistent neural support for the individualized transformation may remain.

---

## 12. Test–Retest: Valuable but Not Mandatory

An additional unfiltered baseline session would be scientifically valuable because the current experiment contains no independent test–retest estimate of each participant's baseline cortical distortion.

A repeated unfiltered session could test whether:

- the same representational abnormality recurs;
- the dominant fitted direction recurs;
- the individualized model is stable across independent measurements.

This would materially strengthen the precision-neuroscience argument, particularly in the deutan participant, whose dominant confusion-axis direction appears relatively stable under the existing resampling analyses.

However, this should be distinguished from the registration reanalysis.

- **Before submission** — Registration harmonization/reanalysis: necessary.
- **High-value optional upgrade** — Independent unfiltered test–retest session: strongly desirable if practical.
- **Not required for the present proof-of-concept claim** — A substantially larger CVD cohort.

A larger cohort becomes necessary for population, subtype, or personalization-advantage claims, but not necessarily for the narrower individual-level feasibility claim.

---

## 13. Parameter Identifiability

Parameter identifiability remains an important limitation.

The fitted deutan confusion-axis component is relatively stable in direction, but the protan solution is more dependent on analysis basis. The fitted S-cone-axis components are below the uncertainty of the recovery procedure, and the recovery analyses do not justify treating every fitted numerical coefficient as a precise physiological measurement.

Therefore:

> The model parameters should be interpreted as an operational low-dimensional description sufficient to construct an inverse transformation, not as precise estimates of underlying physiological mechanisms.

This is already consistent with the manuscript's stated intention to treat the parameters as a compact description rather than physiological measurements.

---

## 14. Comparator Asymmetry

The deployed accessibility filter and individualized filter should not be described as perfectly mechanistically matched interventions if their implementation differs.

If the macOS filter transforms the entire display while the individualized transformation is applied only to the target stimulus, then the comparison has different interpretations for behavior and fMRI.

For behavior, the system-wide deployed filter may be an appropriate ecological comparator because it represents the actual user-facing intervention.

For fMRI, however, transformations of fixation/task elements or the null/filler condition could affect the GLM baseline.

The Methods/Supplement should therefore state precisely:

- which screen elements each filter transforms;
- whether the gray filler changes;
- whether fixation and letter-stream elements change;
- and what implications this has for interpreting the neural comparator.

The deployed filter should be described as an **ecological comparator**, not necessarily a transformation-matched experimental control.

---

## 15. Revised Ranking of Scientific Risks

At present, the manuscript's major vulnerabilities should be ranked approximately as follows:

1. Cross-session validity and registration/preprocessing asymmetry
2. General preprocessing/coregistration robustness
3. Inconsistent neural intervention results
4. Parameter identifiability and analysis-basis dependence
5. Absence of independent unfiltered test–retest replication
6. Colorimetric and luminance limitations
7. Comparator implementation asymmetry
8. N=2/generalizability, provided claims remain strictly individual-level

Thus, the participant count should not dominate the submission discussion.

---

## 16. Journal Selection Should Be Deferred

A final journal should not be selected before the harmonized-registration analysis is completed.

The correct sequence is:

1. Freeze the registration reanalysis plan.
2. Harmonize Session-1 and Session-2 anatomical processing.
3. Recompute the predefined neural endpoints.
4. Compare the original and harmonized results.
5. Determine which scientific conclusions survive.
6. Revise the Abstract, §3.10, §4.3, and validation language accordingly.
7. Select the journal based on the resulting manuscript.

This prevents the analysis from being unconsciously optimized toward a predetermined journal narrative.

---

## 17. Conditional Journal Strategy

The journal decision should depend on the reanalysis.

### Scenario A: Main neural results are robust

If the Session-1 findings and Session-2 neural conclusions remain qualitatively stable after harmonized registration:

**Journal of Neuroscience** becomes a defensible first submission.

The strongest framing would be: preserved cortical information despite altered representational geometry, followed by individualized computational inversion and prospective evaluation.

### Scenario B: Baseline-to-filter neural effects change, but the core Session-1 representational findings remain robust

The manuscript becomes more clearly a *cortical representation + individualized inversion proof-of-concept* paper rather than a neural-normalization paper.

In this scenario, both JNeurosci and **Journal of Vision** should be reconsidered based on the revised story.

Journal of Vision could become particularly attractive because the readership is exceptionally well matched to color representation, CVD, psychophysics, and cortical encoding.

### Scenario C: Core Session-1 representational findings are registration-sensitive

Journal selection should stop temporarily. The primary result itself would first need methodological stabilization.

---

## 18. Human Brain Mapping Should Not Automatically Be Considered the Safe Fallback

HBM remains a strong topical fit for individual-level fMRI, representational geometry, SRM, encoding/decoding, and cortical mapping.

However, its methodological readership may scrutinize the unconventional preprocessing and registration choices particularly closely.

Therefore HBM should be considered a **technical-fit option**, not automatically a lower-risk fallback from JNeurosci.

Depending on the reanalysis, a plausible eventual sequence could be:

> JNeurosci → Cerebral Cortex / Journal of Vision → Human Brain Mapping / Vision Research

but that ranking should remain provisional until the reanalysis is complete.

---

## 19. Final Claim Hierarchy

The final manuscript should distinguish clearly among what is demonstrated, suggested, and untested.

### Demonstrated

1. Hue identity remains decodable in both CVD cases.
2. Continuous/relational hue representation is disrupted.
3. The observed cortical representational deviations differ between the two individuals.
4. A compact individualized model can operationally describe aspects of those distortions.
5. The fitted transformation can be inverted into a physically realizable individually derived stimulus filter.
6. Applying the frozen filters prospectively produces measurable behavioral and neural changes.

### Suggested but preliminary

7. The individualized transformation may improve abnormal psychophysical discrimination in some individuals without introducing the same deficits produced by a deployed comparator.

### Not established

8. The individualized filter reliably normalizes cortical representation.
9. The individualized filter is superior to existing accessibility filters.
10. The filter works specifically because it is matched to the individual.
11. The two observed cortical patterns represent general protan-versus-deutan subtype differences.
12. The fitted coefficients are precise physiological measurements of cortical mechanisms.

This hierarchy should govern the Abstract, Introduction, Results interpretation, Discussion, and cover letter.

---

## Final Recommendation

The manuscript contains a genuinely interesting neuroscience idea and should not be downgraded primarily because it contains two CVD cases.

Its strongest contribution is:

> In two individually characterized observers with color vision deficiency, hue identity remained cortically decodable despite disruption of continuous representational organization. Those individual distortions could be operationally modeled and inverted into physically realizable, individually derived stimulus transformations, which were subsequently evaluated prospectively.

The term *individualized* should refer primarily to the derivation of the model and filter, not to demonstrated individual-specific efficacy. The latter would require cross-filter or comparable personalization-control data that the present experiment does not contain.

The Describe → Summarize → Correct → Validate architecture should be retained. Validation should test the prospective consequences of applying the individually derived filter, while normalization, superiority, and personalization advantage should be treated as stronger hypotheses that remain unresolved.

Before submission, however, the Session-1/Session-2 registration asymmetry should be resolved. Because the resulting reanalysis could materially change the intervention results and therefore the manuscript's scientific identity, journal selection should follow the reanalysis rather than precede it.

Accordingly, the immediate recommendation is not:

> Submit to Journal X.

It is:

> Freeze and perform the harmonized-registration reanalysis, determine which conclusions survive, and only then choose between a general neuroscience positioning and a specialist visual-neuroscience positioning.

If the principal results remain robust, The Journal of Neuroscience remains a credible and ambitious first target. If the intervention narrative weakens while the representational and psychophysical findings remain strong, Journal of Vision becomes particularly attractive rather than merely serving as a fallback.

An independent unfiltered test–retest session would be a high-value upgrade, but it is conceptually distinct from the registration issue and should not be treated as mandatory for the present individual-level feasibility claim.
