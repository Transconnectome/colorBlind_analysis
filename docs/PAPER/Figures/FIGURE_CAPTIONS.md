# Figure Captions — colorBlind_analysis
Generated: 2026-05-11. All captions target eLife style.

---

## Figure 1 | Experimental paradigm and analysis pipeline

**(A)** Stimulus set. Isoluminant chromatic stimuli were drawn from a DKL (Derrington–Krauskopf–Lennie) hue wheel at 8 equally-spaced angles (45° apart), spanning red, orange, yellow, green, cyan, blue, purple, and magenta. **(B)** Retinotopic regions of interest (ROIs). Four areas (V1, V2, V3, hV4) were delineated on each participant's cortical surface using standard retinotopic mapping procedures. **(C)** Analysis pipeline. Stage A (navy): raw fMRI responses were modeled with GLMsingle to obtain single-trial β amplitudes, aligned across sessions with Procrustes rotation, and projected into a group-shared color representation space using Shared Response Modeling (SRM; trained on healthy control participants only). Decoding stages (green): LORO and LOCO assessed discrimination and interpolation capacity, respectively. CVD characterization (coral): a 2-component model decomposed individual CVD distortions into a retinal component (β_s) and a cortical component (β_c), and the pre-image of the estimated distortion yielded a stimulus-space filter specific to each CVD subject. HC: healthy controls, n=7 (sub-01–07); deutan CVD: sub-08; protan CVD: sub-09.

---

## Figure 2 | Color discrimination is preserved but interpolation is selectively impaired at hV4 in CVD

**(A)** Leave-one-run-out (LORO) discrimination accuracy (LDA, 8-class, SRM-aligned) across visual areas V1–hV4 (defined in Figure 1). Gray bars: healthy control (HC) group mean ± SEM (n=7); individual HC values shown as dots. Orange square: sub-08 (deutan CVD); teal triangle: sub-09 (protan CVD). Dashed line: exact-accuracy chance (1/8 = 0.125). n.s.: HC-to-HC vs HC-to-CVD cross-subject LDA generalization, all ROIs pooled (28 HC-to-HC pairs vs 12 HC-to-CVD pairs, Mann-Whitney U, p = 0.668).

**(B)** Leave-one-color-out (LOCO) adjacent accuracy (ForwardEncoding, Procrustes-aligned). Adjacent accuracy: proportion of predictions within ±1 hue step of the target color (0–1; higher = better). Dashed line: adjacent-accuracy chance level (3/8 = 0.375). \*: sub-09 falls significantly below the HC distribution at hV4 (Crawford & Howell, 1998, modified t-test, t = −2.48, p = 0.024); sub-08: t = −1.58, p = 0.082, n.s. Asterisk refers to sub-09 only. Sub-09 (single protan participant) results are reported throughout as exploratory single-case observations requiring independent replication.

**(C)** Per-hue adjacent accuracy at hV4. HC bars: group mean ± SEM. Hue abbreviations: Org=orange, Yel=yellow, Grn=green, Cyn=cyan, Blu=blue, Pur=purple, Mag=magenta. Dashed line: 3/8 chance. Per-hue Crawford & Howell tests (one-tailed, uncorrected): blue — sub-08 d=2.13, p=0.047; sub-09 d=2.15, p=0.046; purple — sub-08 d=2.40, p=0.033.

*Takeaway.* hV4 supports above-chance 8-class discrimination in both CVD participants while selectively losing continuous-hue interpolation along S-cone-intermediate hues — the joint pattern that simultaneously warrants and constrains a stimulus-space correction filter (panel A: filter precondition; panels B–C: filter target).

---

## Figure 3 | Each CVD subject shows significantly elevated color representation disparity at a distinct ROI

**(A)** Representational dissimilarity matrix (RDM) difference (ΔRDM = RDM_CVD − mean RDM_HC-LOO) in SRM-aligned space, for sub-08 at V2 (left) and sub-09 at V1 (right). Each subject is shown at their primary ROI, defined as the ROI with a significant pairwise-disparity elevation in (B) (V2 for sub-08, V1 for sub-09). Warm colors: CVD pairwise distances larger than HC mean; cool colors: smaller. Annotated p-values are from a permutation test of whether the retinal + cortical (R+C) cone-shift model predicts the observed ΔRDM structure (sub-08 V2: p = 0.179, n.s.; sub-09 V1: p = 0.026\*). These p-values test model-geometry concordance and are independent of the disparity tests in (B).

**(B)** Mean pairwise correlation distance (disparity) in SRM-aligned space per subject per ROI. HC band: group mean ± 1 SD (n=7); individual HC leave-one-out values shown as dots. Significance markers from Crawford & Howell (1998) modified t-tests comparing each CVD subject to the HC distribution (sub-08 V2: p = 0.040\*; sub-09 V1: p = 0.007\*\* — exploratory single-case finding). Sub-10 (near-normal deutan): gray triangles, no significant elevation at any ROI. Note: (A) tests whether a cone-shift model predicts ΔRDM geometry; (B) tests whether absolute pairwise disparity is elevated—these are independent measures and their significance patterns need not agree.

*Takeaway.* The two CVD participants show elevated representational disparity at distinct ROIs (V2 for deutan; V1 for protan), an idiosyncratic ROI-specific pattern inconsistent with a shared group-level gain mechanism and consistent with subject-specific distortion fields.

---

## Figure 4 | A neural-primary HYBRID-loss fit recovers per-subject 2-component distortion at hV4

Two rows: sub-08 (deutan), sub-09 (protan).

**(A)** Per-hue LOCO vulnerability profiles at hV4. Filled circles: observed CVD vulnerability (HC-trained ForwardEncoding); colored line: 2-component model prediction at the HYBRID argmin (β̂_s, β̂_c). X-axis hue labels (DKL, 45° spacing): R=red, O=orange, Y=yellow, G=green, C=cyan, B=blue, P=purple, M=magenta.

**(B)** HYBRID-loss component decomposition at the per-subject argmin. Bar height: value of L_mse, L_rdm, and the Tikhonov penalty under weighting (w_pat, w_rdm, μ) = (0.7, 0.3, 2.0) (Eq. eq:hybrid). Post-hoc Spearman ρ at the same point — sub-08: 0.38 (n.s., p=0.18); sub-09: −0.26 (n.s., p=0.75) — is annotated in text for reference but is not part of the loss being optimized. HYBRID jointly weighs first-order pattern similarity and second-order RDM similarity rather than rank-order monotonicity.

**(C)** HYBRID-loss landscape L(β_s, β_c) over β_s ∈ [0°, 50°], β_c ∈ [−50°, 50°] (1,326 cells at 2° resolution). White star: per-subject argmin — sub-08: (16°, +40°); sub-09: (12°, −30°). Colormap shows low L (good fit) in red, high L in blue (preserves visual continuity with earlier ρ-coloured landscapes).

**Caveats and consistency anchors.** The 2-component HYBRID fit achieves nominal LOCO significance for 7/7 HCs under label permutation, so per-subject p-values are descriptive of representational-geometry fit, not CVD-specificity claims (full HC distributions in Supplementary §HC permutation). Sub-09 (single protan participant) results are exploratory single-case observations requiring independent replication. The recovered β̂_c sign is positive for sub-08 (deutan) and negative for sub-09 (protan), aligning with the L–M opponent-axis polarity predicted by Brettel's cone-physiology model [Brettel et al. 1997]; both subjects' β̂_s are directionally consistent with Emery's S-cone-axis hV4 RDM finding [Emery et al. 2021]. These are post-hoc directional consistency checks, not quantitative validations — the latter is deferred to a Phase-3 2AFC behavioral arm. Comparison with alternative model classes (1-DOF Machado, 2-DOF R+C) under the historical LOCO-ρ argmax criterion is reported in Appendix A.

---

## Figure 5 | HYBRID-derived per-subject stimulus-space filter: 4-column rendering

Two rows: sub-08 (deutan) at (β̂_s, β̂_c) = (16°, +40°), ‖β̂‖ = 43.1°; sub-09 (protan) at (12°, −30°), ‖β̂‖ = 32.3°. For each subject, columns are:

1. **Original** — HC percept of the 8 displayed stimuli (DKL hues, 45° apart).
2. **CVD perceives** — simulated CVD percept of the *original* stimulus under the per-subject 2-component model.
3. **Filtered** — stimulus after applying the per-subject stimulus-space correction δθ_filter, computed as the exact numerical pre-image of −δθ(·; β̂_s, β̂_c) via Brent's method on the forward map (8/8 pre-images exact, residual < 0.001° for both subjects).
4. **CVD(Filtered)** — simulated CVD percept of the filtered stimulus, qualitatively closer to the HC percept of the original.

Per-hue correction magnitudes |δθ_filter|, signed correction profiles, and the cosine similarity between the two subjects' filters are reported in Supplementary §Filter details.

Rendering coordinate space: STIM_LAB CIELab (project convention, `scripts/stim_lab_render.py`). Closeness of column 4 to column 1 is *qualitative*; quantitative behavioral validation of filter efficacy is deferred to the Phase-3 2AFC arm (Methods, last paragraph). Comparison with the arc-compression failure of the 1-DOF Machado pre-image (sub-09 only) is reported in Appendix A.

---

---

# Revision log

## 2026-05-11 — issues fixed

| Item | Status |
|---|---|
| F2 Panel B: `*` = sub-09 only, added "Asterisk refers to sub-09 only" | ✓ Fixed |
| F2 Panel A: p=0.668 scope — added "(28 HC-to-HC pairs vs 12 HC-to-CVD pairs, all ROIs pooled)" | ✓ Fixed |
| F2 Panel C: "no within-hue tests" removed; per-hue C&H stats added from per_color_breakdown.json | ✓ Fixed |
| F2: HC defined "(healthy control, HC; n=7)" at first use | ✓ Fixed |
| F3 Panel A: ROI selection explained "(V2 for sub-08, V1 for sub-09)" | ✓ Fixed |
| F3 Panel A/B: two p-value families explicitly distinguished in note | ✓ Fixed |
| F4 title: "accounts for" → "predicts … (ρ = 0.88, p = 0.004; ρ = 0.69, p = 0.035)" | ✓ Fixed |
| F4 Panel B: "Pre-image validation … Figure 5" cross-reference removed; pure description retained | ✓ Fixed |
| F4 Panel B: bar encoding added "Solid bars: 2-component; hatched bars: Machado" | ✓ Fixed |
| F5 Panel B: "bijectively" → "maps each stimulus to a distinct corrected position" | ✓ Fixed |
| F5 Panel C: last sentence (interpretation) removed | ✓ Fixed |
| F1: "personalized" → "specific to each CVD subject" | ✓ Fixed |
| F1: DKL defined at first use | ✓ Fixed |
| F2/F4: ROIs defined "(defined in Figure 1)" | ✓ Fixed |
| F2: Crawford & Howell full name "(Crawford & Howell, 1998)" at first use | ✓ Fixed |

## Remaining open items (defer to final polish)

| Item | Reason deferred |
|---|---|
| F5 Panel A bar face colors are hardcoded sRGB, not STIM_LAB-derived | Does not affect caption text; tracked in F5/FIGURE_NOTES.md |
| F4 Panel B sub-09: Machado ρ=0.76 > 2-comp ρ=0.69 not reconciled in caption | Justification belongs in Results text, not caption; manuscript ¶E handles it |
| F3 title: "idiosyncratically" absent | Factual title acceptable for caption; word available for Results heading |
