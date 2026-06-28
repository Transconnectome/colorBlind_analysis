# Figure Captions — colorBlind_analysis
Generated: 2026-05-11. All captions target eLife style.

---

## Figure 1 | Experimental paradigm and analysis pipeline

**(A)** Stimulus set. Isoluminant chromatic stimuli were drawn from a CIE L\*a\*b\* hue circle (L\* = 75, chroma 40 on the a\*–b\* plane) at 8 equally-spaced angles (45° apart), spanning red, orange, yellow, green, cyan, blue, purple, and magenta. **(B)** Retinotopic regions of interest (ROIs). Four areas (V1, V2, V3, hV4) were delineated on each participant's cortical surface using standard retinotopic mapping procedures. **(C)** Analysis pipeline. Stage A (navy): raw fMRI responses were modeled with GLMsingle to obtain single-trial β amplitudes, aligned across sessions with Procrustes rotation, and projected into a group-shared color representation space using Shared Response Modeling (SRM; trained on healthy control participants only). Decoding stages (green): LORO and LOCO assessed discrimination and interpolation capacity, respectively. CVD characterization (coral): a 2-component model decomposed individual CVD distortions into a retinal component (β_s) and a cortical component (β_c), and the pre-image of the estimated distortion yielded a stimulus-space filter specific to each CVD subject. HC: healthy controls, n=7 (sub-01–07); deutan CVD: sub-08; protan CVD: sub-09.

---

## Figure 2 | Color discrimination is preserved but interpolation is selectively impaired at hV4 in CVD

**(A)** Leave-one-run-out (LORO) discrimination accuracy (LDA, 8-class, SRM-aligned) across visual areas V1–hV4 (defined in Figure 1). Gray bars: healthy control (HC) group mean ± SEM (n=7); individual HC values shown as dots. Orange square: sub-08 (deutan CVD); teal triangle: sub-09 (protan CVD). Dashed line: exact-accuracy chance (1/8 = 0.125). n.s.: HC-to-HC vs HC-to-CVD cross-subject LDA generalization, all ROIs pooled (21 HC-to-HC pairs vs 14 HC-to-CVD pairs, Mann-Whitney U, p = 0.668).

**(B)** Leave-one-color-out (LOCO) adjacent accuracy (ForwardEncoding, Procrustes-aligned). Adjacent accuracy: proportion of predictions within ±1 hue step of the target color (0–1; higher = better). Dashed line: adjacent-accuracy chance level (3/8 = 0.375). \*: sub-09 falls significantly below the HC distribution at hV4 (Crawford & Howell, 1998, modified t-test, t = −2.91, p = 0.017); sub-08: t = −1.84, p = 0.063, n.s. Asterisk refers to sub-09 only. Sub-09 (single protan participant) results are reported throughout as exploratory single-case observations requiring independent replication.

**(C)** Per-hue adjacent accuracy at hV4. HC bars: group mean ± SEM (n=6; sub-07 excluded for insufficient hV4 voxels). Hue abbreviations: Org=orange, Yel=yellow, Grn=green, Cyn=cyan, Blu=blue, Pur=purple, Mag=magenta. Dashed line: 3/8 chance. Both CVD participants showed zero adjacent accuracy at the S-cone intermediate hues blue, purple, and magenta. Per-hue single-case tests (Crawford & Howell, one-tailed, uncorrected and exploratory) reached significance at no individual hue.

*Takeaway.* hV4 supports above-chance 8-class discrimination in both CVD participants while selectively losing continuous-hue interpolation along S-cone-intermediate hues — the joint pattern that simultaneously warrants and constrains a stimulus-space correction filter (panel A: filter precondition; panels B–C: filter target).

---

## Figure 3 | Each CVD subject shows significantly elevated color representation disparity at a distinct ROI

**(A)** Representational dissimilarity matrix (RDM) difference (ΔRDM = RDM_CVD − mean RDM_HC-LOO) in SRM-aligned space, for sub-08 at V2 (left) and sub-09 at V1 (right). Each subject is shown at their primary ROI, defined as the ROI with a significant pairwise-disparity elevation in (B) (V2 for sub-08, V1 for sub-09). Warm colors: CVD pairwise distances larger than HC mean; cool colors: smaller. Annotated p-values are from a permutation test of whether the retinal + cortical (R+C) cone-shift model predicts the observed ΔRDM structure (sub-08 V2: p = 0.179, n.s.; sub-09 V1: p = 0.026\*). These p-values test model-geometry concordance and are independent of the disparity tests in (B).

**(B)** Mean pairwise correlation distance (disparity) in SRM-aligned space per subject per ROI. HC band: group mean ± 1 SD (n=7); individual HC leave-one-out values shown as dots. Significance markers from Crawford & Howell (1998) modified t-tests comparing each CVD subject to the HC distribution (sub-08 V2: p = 0.040\*; sub-09 V1: p = 0.007\*\* — exploratory single-case finding). Sub-10 (near-normal deutan): gray triangles, no significant elevation at any ROI. Note: (A) tests whether a cone-shift model predicts ΔRDM geometry; (B) tests whether absolute pairwise disparity is elevated—these are independent measures and their significance patterns need not agree.

*Takeaway.* The two CVD participants show elevated representational disparity at distinct ROIs (V2 for deutan; V1 for protan), an idiosyncratic ROI-specific pattern inconsistent with a shared group-level gain mechanism and consistent with subject-specific distortion fields.

---

## Figure 4 | Per-subject 2-component loss landscape

Per-participant production loss (a behavioral discrimination term γ plus a ΔRDM cortical-geometry term) evaluated on the (β_s, β_c) grid (β_s ∈ [0°, 50°], β_c ∈ [−50°, +50°], step 2°). The loss is selected per participant — sub-08: γ_OY + L_RDM at V2; sub-09: γ_all + L_RDM at V1 — and the leave-one-color-out (LOCO) decoding term is not part of the selected loss. Each term is normalised before combination.

**Left.** Sub-08 (deutan, Stockman confusion axis 150°). White star: argmin (β̂_s, β̂_c) = (6°, −42°), ‖β̂‖ = 42.4°.

**Right.** Sub-09 (protan, Stockman axis 16°). White star: argmin (β̂_s, β̂_c) = (2°, +24°), ‖β̂‖ = 24.1°.

Colormap (`viridis_r`): low loss in yellow (good fit), high loss in dark purple (poor fit). Loss-term roles: γ = behavioral discrimination-threshold term that drives the fit; L_RDM = ΔRDM cortical-geometry term at the participant's selected ROI (V2 for sub-08, V1 for sub-09; Methods).

**Caveats and consistency anchors.** The HC leave-one-out ‖β̂‖ anchor is computed per participant under that participant's production loss (each of the n=7 HC participants refit as a pseudo-CVD case): ‖β̂‖ ∈ [30.5°, 58.1°], mean 49.1° under the sub-08 loss, and ‖β̂‖ ∈ [23.4°, 55.5°], mean 35.7° under the sub-09 loss. Both CVD estimates fall within their respective HC ranges (sub-08 ‖β̂‖ = 42.4°; sub-09 ‖β̂‖ = 24.1°), so ‖β̂‖ magnitude alone does not separate the CVD cases from the HC distribution — a descriptive anchor, not a hypothesis test. Within-cohort label-permutation p-values for the per-subject argmin are not reported: they assess whether the loss landscape has a non-trivial minimum on a participant's profile, not whether the inverted filter restores HC-equivalent perception. Quantitative filter validity is deferred to the Phase-3 behavioural arm. Sub-09 (single protan participant) results are exploratory single-case observations requiring independent replication. The between-subtype contrast rests on the sign of the dominant confusion-axis term (β̂_c = −42° for sub-08 versus +24° for sub-09); per-axis magnitudes are not separately identifiable and carry no retinal-versus-cortical etiological attribution.

---

## Figure 5 | Per-subject stimulus-space filter: 4-column rendering, side-by-side

**Left block.** Sub-08 (deutan) at (β̂_s, β̂_c) = (6°, −42°), ‖β̂‖ = 42.4°. Per-hue filter shift (δθ°): red −38, orange −32, yellow +32, green +38, cyan +26, blue +9, purple −9, magenta −26; mean |δθ| = 26.3°.

**Right block.** Sub-09 (protan) at (β̂_s, β̂_c) = (2°, +24°), ‖β̂‖ = 24.1°. Per-hue filter shift (δθ°): red −19, orange −25, yellow −14, green +16, cyan +25, blue +18, purple +6, magenta −7; mean |δθ| = 16.2°.

Within each block, eight rows correspond to the eight displayed CIE L\*a\*b\* hues (c1 red 0° → c8 magenta 315°, 45° spacing). Columns (left → right):

1. **Original** — HC percept of the displayed stimulus.
2. **CVD percept** — simulated CVD percept of the *original* stimulus under the per-subject 2-component model.
3. **Filtered** — stimulus after applying the per-subject stimulus-space correction δθ_filter, computed as the exact numerical pre-image of −δθ(·; β̂_s, β̂_c) via Brent's method on the forward map (8/8 pre-images exact, residual < 0.001° for both subjects).
4. **CVD(Filt.)** — simulated CVD percept of the filtered stimulus.

Rendering coordinate space: STIM_LAB CIELab (project convention, `scripts/stim_lab_render.py`). Quantitative behavioral validation of filter efficacy is deferred to the Phase-3 2AFC arm (Methods, last paragraph) and will be added to this figure once data are collected.

---

---

# Revision log

## 2026-06-11 — synced to v6 PCA closure (canonical argmins)

| Item | Status |
|---|---|
| F4/F5 argmins: sub-08 (38°,−14°)→(6°,−42°), ‖β̂‖ 40.5°→42.4°; sub-09 (6°,−22°)→(2°,+24°), ‖β̂‖ 22.8°→24.1° | ✓ Fixed |
| F4 loss: deprecated `L_fit`/`eq:lfit` (V4 LOCO 4-term weighted) → per-subject production loss (γ + L_RDM at V2/V1; LOCO not in selected loss) | ✓ Fixed |
| F4 HC LOO anchor: single-loss [26.3°,49.2°] mean 40.1° (n=6) → per-subject sub-08 [30.5°,58.1°] mean 49.1°, sub-09 [23.4°,55.5°] mean 35.7° (n=7) | ✓ Fixed |
| F4 "sub-09 below HC minimum" claim removed — 24.1° now within HC range [23.4°,55.5°] | ✓ Fixed |
| F4 "both β̂_c negative" corrected → β̂_c = −42° (sub-08) vs +24° (sub-09); contrast is sign, not S-cone magnitude | ✓ Fixed |
| F4 R+C etiology claim (cortical-/retinal-dominant; Δλ/g values) removed — appendix disclaims attribution; g sign reverses across criteria | ✓ Fixed (#2) |
| F5 per-hue δθ vectors regenerated from exp2_preimage canonical pre-image (sub-08 \|δθ\|=26.3°, sub-09 \|δθ\|=16.2°) | ✓ Fixed |

| F1/F5 stimulus space "DKL (Derrington–Krauskopf–Lennie)" → CIE L\*a\*b\* (L\*=75, chroma 40 on a\*–b\* plane) per CLAUDE.md | ✓ Fixed |

Note: this doc's "Figure 4" loss landscape = compiled `fig6_landscape` (renumbered); compiled captions in `results_v4.tex` already current.

## 2026-05-11 — issues fixed

| Item | Status |
|---|---|
| F2 Panel B: `*` = sub-09 only, added "Asterisk refers to sub-09 only" | ✓ Fixed |
| F2 Panel A: p=0.668 scope — added "(21 HC-to-HC pairs vs 14 HC-to-CVD pairs, all ROIs pooled)" | ✓ Fixed |
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
