# Figure Captions — colorBlind_analysis
Generated: 2026-05-11. All captions target eLife style.

---

## Figure 1 | Experimental paradigm and analysis pipeline

**(A)** Stimulus set. Isoluminant chromatic stimuli were drawn from a DKL (Derrington–Krauskopf–Lennie) hue wheel at 8 equally-spaced angles (45° apart), spanning red, orange, yellow, green, cyan, blue, purple, and magenta. **(B)** Retinotopic regions of interest (ROIs). Four areas (V1, V2, V3, hV4) were delineated on each participant's cortical surface using standard retinotopic mapping procedures. **(C)** Analysis pipeline. Stage A (navy): raw fMRI responses were modeled with GLMsingle to obtain single-trial β amplitudes, aligned across sessions with Procrustes rotation, and projected into a group-shared color representation space using Shared Response Modeling (SRM; trained on healthy control participants only). Decoding stages (green): LORO and LOCO assessed discrimination and interpolation capacity, respectively. CVD characterization (coral): a 2-component model decomposed individual CVD distortions into a retinal component (β_s) and a cortical component (β_c), and the pre-image of the estimated distortion yielded a stimulus-space filter specific to each CVD subject. HC: healthy controls, n=7 (sub-01–07); deutan CVD: sub-08; protan CVD: sub-09.

---

## Figure 2 | Color discrimination is preserved but interpolation is selectively impaired at hV4 in CVD

**(A)** Leave-one-run-out (LORO) discrimination accuracy (LDA, 8-class, SRM-aligned) across visual areas V1–hV4 (defined in Figure 1). Gray bars: healthy control (HC) group mean ± SEM (n=7); individual HC values shown as dots. Orange square: sub-08 (deutan CVD); teal triangle: sub-09 (protan CVD). Dashed line: exact-accuracy chance (1/8 = 0.125). n.s.: HC-to-HC vs HC-to-CVD cross-subject LDA generalization, all ROIs pooled (28 HC-to-HC pairs vs 12 HC-to-CVD pairs, Mann-Whitney U, p = 0.668).

**(B)** Leave-one-color-out (LOCO) adjacent accuracy (ForwardEncoding, Procrustes-aligned). Adjacent accuracy: proportion of predictions within ±1 hue step of the target color (0–1; higher = better). Dashed line: adjacent-accuracy chance level (3/8 = 0.375). \*: sub-09 falls significantly below the HC distribution at hV4 (Crawford & Howell, 1998, modified t-test, t = −2.48, p = 0.024); sub-08: t = −1.58, p = 0.082, n.s. Asterisk refers to sub-09 only.

**(C)** Per-hue adjacent accuracy at hV4. HC bars: group mean ± SEM. Hue abbreviations: Org=orange, Yel=yellow, Grn=green, Cyn=cyan, Blu=blue, Pur=purple, Mag=magenta. Dashed line: 3/8 chance. Per-hue Crawford & Howell tests (one-tailed, uncorrected): blue — sub-08 d=2.13, p=0.047; sub-09 d=2.15, p=0.046; purple — sub-08 d=2.40, p=0.033.

---

## Figure 3 | Each CVD subject shows significantly elevated color representation disparity at a distinct ROI

**(A)** Representational dissimilarity matrix (RDM) difference (ΔRDM = RDM_CVD − mean RDM_HC-LOO) in SRM-aligned space, for sub-08 at V2 (left) and sub-09 at V1 (right). Each subject is shown at their primary ROI, defined as the ROI with a significant pairwise-disparity elevation in (B) (V2 for sub-08, V1 for sub-09). Warm colors: CVD pairwise distances larger than HC mean; cool colors: smaller. Annotated p-values are from a permutation test of whether the retinal + cortical (R+C) cone-shift model predicts the observed ΔRDM structure (sub-08 V2: p = 0.179, n.s.; sub-09 V1: p = 0.026\*). These p-values test model-geometry concordance and are independent of the disparity tests in (B).

**(B)** Mean pairwise correlation distance (disparity) in SRM-aligned space per subject per ROI. HC band: group mean ± 1 SD (n=7); individual HC leave-one-out values shown as dots. Significance markers from Crawford & Howell (1998) modified t-tests comparing each CVD subject to the HC distribution (sub-08 V2: p = 0.040\*; sub-09 V1: p = 0.007\*\*). Sub-10 (near-normal deutan): gray triangles, no significant elevation at any ROI. Note: (A) tests whether a cone-shift model predicts ΔRDM geometry; (B) tests whether absolute pairwise disparity is elevated—these are independent measures and their significance patterns need not agree.

---

## Figure 4 | A two-component model (retinal shift + cortical rotation) predicts hV4 LOCO vulnerability in individual CVD subjects (sub-08: ρ = 0.88, p = 0.004; sub-09: ρ = 0.69, p = 0.035)

**(A)** Per-hue LOCO vulnerability profiles at hV4. Filled circles: observed CVD vulnerability (HC-trained ForwardEncoding). Solid lines: 2-component model prediction at optimal (β_s, β_c). Dashed lines: Machado (1-parameter cone-shift) prediction. X-axis hue labels (0–315°, 45° spacing in DKL hue space): R=red, O=orange, Y=yellow, G=green, C=cyan, B=blue, P=purple, M=magenta.

**(B)** Spearman ρ between observed and model-predicted vulnerability across 8 hues. Solid bars: 2-component model; hatched bars: Machado. p-values from label-permutation test (40,320 permutations). Sub-08: 2-component ρ = 0.88, p = 0.004; Machado ρ = 0.62, p = 0.058 (n.s.). Sub-09: 2-component ρ = 0.69, p = 0.035; Machado ρ = 0.76, p = 0.018.

**(C)** Parameter landscape: Spearman ρ as a function of β_s (S-cone retinal shift) and β_c (cortical opponent-channel rotation). White star: LOCO-optimal parameters (sub-08: β_s = 38°, β_c = −14°; sub-09: β_s = 6°, β_c = −22°). Colormap: RdBu_r (blue = low ρ; red = high ρ).

---

## Figure 5 | The 2-component pre-image filter is exact for both CVD subjects and individually distinct

**(A)** Hue correction magnitude (|δθ|) at each stimulus position, computed as the exact pre-image of the 2-component distortion. Bar face color: approximate perceptual hue of each stimulus. Dashed lines: per-subject mean correction (sub-08: 46.3°; sub-09: 20.1°). Both subjects: 8/8 pre-images exact (maximum residual < 0.001°).

**(B)** Arc collapse in the Machado pre-image for sub-09. Green (135°), cyan (180°), and blue (225°) stimuli all map to a single pre-image angle (~127°), preventing exact inversion (4/8 exact; × marks failed hues). The 2-component pre-image maps each stimulus to a distinct corrected position across the full hue circle (8/8 exact).

**(C)** Signed correction profiles (δθ) for sub-08 (orange) and sub-09 (teal). Shaded region: sub-08 and sub-09 corrections have opposite signs (hues 5–8, cyan–magenta arc; 4/8 sign agreements overall; sub-08 vs sub-09 filter cosine similarity = 0.55).

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
