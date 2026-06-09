# Camera-Ready Revision Outline — Path B (closure-canonical reframe)

**Target**: ICML 2026 GenBio workshop (camera-ready of `SD4H_draft_v6.1.tex`)
**Source of truth**: `future_phase2_filter_optimization/PIPELINE_2_CLOSURE.md` (2026-06-01) + `CLAUDE.md` §0/§2.6/§3
**Path B = closure-canonical reframe**: the April v6.1 Results conflict with the June-1 closure; this outline encodes the reconciled structure. Do NOT carry over v6.1 Results values.

> **Scope of this artifact**: planning only. No `.tex` edits. All "TBD" items require a data/render step before final numbers — do not fabricate.

---

## 0. The inversion (one-line diagnosis)

v6.1 is **LOCO-centric · two-model (Machado/R+C + closed-testing) · sub-08-anchored · physiological-value-claiming**.
Path B is **composite(γ+RDM)-centric · single 2-Component cortical model · sub-09-anchored (divergent correction) · mechanism-class-only**.
Every section below is checked against that inversion.

### Canonical facts (locked — source = closure docs; do not alter)

| Item | Path B value |
|---|---|
| Single model | **2-Component cortical opponent-axis (2-DOF)**: δθ(θ)=β_s·cos(θ−90°)+β_c·cos(θ−θ_conf); θ_conf: protan=16°, deutan=150° |
| sub-08 (deutan) | **(β_s=+6, β_c=−42)** [βc-dom]; combo γ_OY+RDM_V2; test_loss_median −2.36±2.15; param IQR (8,2); held-out RDM ΔL=−0.406 (7/7 folds beat (0,0)); γ ΔL=−13.8 (5/7) ✓ |
| sub-09 (protan) | **(β_s=+2, β_c=+24)** [βc-rot]; combo γ_all+RDM_V1; param IQR (0,0); mode share 87.7% (263/300); held-out RDM ΔL=−0.472 (7/7 folds); γ ΔL=−0.55 (4/7 ≈ null — report honestly) |
| sub-10 (deutan) | **null at LOCO and SRM; excluded** |
| R+C | **REJECTED** (boundary saturation: sub-08 bdy=100%, sub-09 41%; no β_c DOF; δθ=(2−g)·δθ_Machado) |
| Reportable | mechanism class = sign quadrant (sub-08 β_s+/β_c−, sub-09 β_c+); averaged-surface signal 2.1×–5.5× deeper than HC null |
| FORBIDDEN | absolute (β_s,β_c) physiological interpretation (noise floor ~20°/25°; 0/3 dual-pass null); any "Δλ matches moderate/mild anomaly" claim |
| Selection | held-out **test_loss_median** (5/2 HC split ×300 resample) + **structural adequacy**; NOT perm-p<0.05. LOCO_V4 = precondition gate only |
| HC specificity | **descriptive only, NOT selection criterion** (HC FPR high). Keep honest HC-FPR appendix; cut the rescue |
| Pre-image | 2-comp 8/8 exact both subjects (sub-08 mean\|δ\|=46.3°, sub-09 20.1°, residual<0.001°); retinal Machado sub-09 only 4/8 (arc 360°→~96°) |
| Divergence anchor | **sub-09** (retinal 4/8 collapse vs cortical 8/8 bijective), NOT sub-08 |
| Non-identifiability | sub-09 PCA (2,+24) vs SRM (32,0) → appendix/limitation ONLY |

---

## 1. Contribution statement (Path B, 3-tier)

> We pose individualized color-vision correction as a structured-distortion inference problem on fMRI hue-representation geometry, and resolve it through a three-tier argument that no single criterion can settle alone. **(Tier 1 — detection)** Multiple candidate distortion mechanisms — a retinal cone-shift account and a cortical opponent-axis account — agree at the level of *detection*: both flag the same two of three Ishihara-confirmed CVD individuals as carrying structured distortion, so detection-level agreement cannot adjudicate *which* mechanism to correct. **(Tier 2 — structural adequacy)** Held to the structural demands of the data, the 1-DOF retinal/compensation family saturates (no confusion-axis degree of freedom), whereas a 2-DOF cortical opponent-axis model remains interior and adequate; structural adequacy therefore narrows the account to the cortical model and resolves each individual to a **mechanism class (sign quadrant)** — deutan β_s+/β_c−, protan β_c+ — rather than to a physiologically-interpretable parameter value. **(Tier 3 — behavioral)** The retinal and cortical accounts, though convergent on detection, prescribe *divergent corrections* (for the protan case, the retinal model collapses 4/8 hues irreversibly while the cortical model preserves a bijective 8/8 pre-image), so the remaining adjudication is a falsifiable behavioral test, which we specify as the immediate next step. The methodological contribution is the inversion itself: detection-level agreement is insufficient for choosing an intervention, and structural adequacy plus a behavioral test together convert a descriptive phenotype into an individualized, invertible correction target.

**Tier → section map**: Tier 1+2 → Results §1; Tier 3 → Results §2. (Discriminator: if divergence/pre-image lands in §1, the tier logic has slipped.)

---

## 2. Reverse-outline table

| Section | (a) Topic (1 sentence) | (b) Changes from v6.1 | (c) Canonical facts/numbers it must carry | (d) Fig/Table dep |
|---|---|---|---|---|
| **Abstract** | Structured fMRI hue-geometry distortion is inferred as a single 2-Component cortical model; mechanisms converge on detection but diverge on correction. | Drop "both a one-parameter retinal cone-shift and a two-parameter retinal–cortical model" (L71) → single 2-Component cortical model. Demote LOCO-as-central-quantification → composite(γ+RDM) inference. Keep "detection-level agreement insufficient" thesis. | 2-Component (2-DOF); two CVD of three resolved, sub-10 null/excluded; mechanism class (sign quadrant); divergent correction; behavioral test = next step. No β values, no Δλ. | — |
| **Intro** | Health data carry structured, parameterizable distortions that can be inverted for individualized correction; CVD is the test case. | Cut contribution bullet "different individuals require different parsimonious models within a closed-testing escalation" (L104). Rewrite contributions to 3-tier (detection / structural-adequacy / behavioral). Replace "interpolation vulnerability profile" as the central object → composite geometry inference (γ behavioral + RDM neural). "1–2 DOF" → "2 DOF". | CVD ~8% males; LORO decoding no HC–CVD diff (p=0.668); heterogeneity → individual-level inference; 2-DOF cortical model; mechanism-class outcome. | — |
| **Methods** | Encoding model + composite loss (γ behavioral + RDM neural) fits a 2-DOF cortical opponent-axis distortion; selection by held-out test-loss + structural adequacy. | LOCO demoted to **precondition gate** (not the fitting objective). Selection rule rewritten: **held-out test_loss_median (5/2 HC split ×300) + structural adequacy**, NOT perm-p<0.05 (cut L188–189). Present R+C as a tested-and-rejected family (structural inadequacy), not an escalation tier (cut L156 closed-testing). Keep 2-Component eq; keep Machado/R+C definitions but framed as the *retinal/compensation family that fails structural adequacy*. | Composite = γ (per-pair JND z²) + RDM (PCA top-6 → 8×8 → 28-d cosine vs HC mean); θ_conf protan=16°/deutan=150°; β_s grid [0,50] one-sided, β_c [−50,50]; selection = test_loss_median ↓ then IQR ↓ + boundary<0.5; LOCO_V4 = gate only. **Define "detection" = passing the LOCO_V4 precondition gate (model-independent); sub-10 excluded (null at LOCO+SRM).** This is the basis Tier 1 refers to — not per-model perm-p. | Fig 1 (pipeline) |
| **Results §1** (Detection + structural adequacy → mechanism class) | The 2-Component model fits both CVD individuals, R+C fails structural adequacy, and each individual resolves to a sign-quadrant mechanism class supported by held-out and averaged-surface evidence. | **Replaces v6.1 §3.1 wholesale.** Drop Table 1 (R+C-as-primary, per-subject Machado/R+C rows, perm-p column). New Table = 2-Component fits with held-out test-loss + held-out RDM ΔL + folds-beating-(0,0). Drop LOCO-profile Fig2. Report mechanism class + averaged-surface depth, NOT absolute β as physiology. | sub-08 (+6,−42) test_loss −2.36±2.15, IQR (8,2), RDM ΔL=−0.406 7/7, γ ΔL=−13.8 (5/7); sub-09 (+2,+24) IQR (0,0), mode 87.7%, RDM ΔL=−0.472 7/7, γ ΔL=−0.55 (4/7 ≈null, honest); R+C rejected (sub-08 bdy=100%, sub-09 41%); averaged-surface 2.1×–5.5× deeper than HC null; sub-10 null/excluded. | **Fig 2 (new, RDM-based)**; Results Table (new) |
| **Results §2** (Convergent detection, divergent correction) | The retinal and cortical accounts converge on detection but prescribe divergent corrections, resolved only by behavior; pre-image feasibility re-anchored on sub-09. | **Re-anchor on sub-09**: retinal Machado collapses 4/8 hues (arc 360°→~96°), cortical 8/8 bijective. **Cut the sub-08 cosine=−0.18 / 3-8 comparison (L244, L396)** — it is R+C-vs-2comp, R+C rejected. Frame divergence as falsifiable behavioral 2AFC. | sub-09 retinal 4/8 vs cortical 8/8 (residual<0.001°); sub-08 cortical 8/8 mean\|δ\|=46.3°; sub-09 cortical 8/8 mean\|δ\|=20.1°; behavioral test = adjudicator. sub-09 retinal-vs-cortical correction cosine = **TBD**. | Fig (feasibility/collapse, app) |
| **Discussion** | From structured distortion to intervention: interpretable, invertible, but value-unresolved pending behavior. | Cut L266 "physiologically interpretable parameters" rescue. Limitations restructured to closure Themes A/B/C. Add: mechanism class robust, absolute magnitude not (noise floor ~20°/25°); CVD N=2 → CVD-level generalization impossible, behavioral session = sole path; HC FPR high (specificity descriptive only). | HC FPR (15/21, 2-comp 7/7); noise floor ~20°(β_s)/25°(β_c), 0/3 dual-pass null; CVD N=2; behavioral validation = primary next step. | — |
| **Conclusion** | A single cortical 2-Component model recovers subject-specific mechanism classes that converge on detection, diverge on correction, and yield a falsifiable behavioral test. | Drop "diverge on correction" anchored on sub-08; keep general thesis, mechanism-class framing. | mechanism class; divergent correction; behavioral test = next step. | — |
| **Impact** | Many conditions leave structured (not absent) signatures; low-dim invertible features turn descriptive phenotypes into individualized targets. | Minimal change. Optionally add the "detection ≠ intervention adequacy" methodological point. | — | — |
| **Appendix** | Notation; honest HC-FPR calibration; cross-ROI/criterion; pre-image details; null-testing/identifiability; sub-09 metric non-identifiability. | **Keep** HC-FPR table + mechanism (grid flexibility + regression-to-mean, r=−0.894). **CUT** the "why this does not invalidate" rescue (L367–373) — it is a forbidden specificity claim. Add Theme A null-testing (Test 1/2a/2c, Exp 14/15/17/22) and sub-09 PCA-vs-SRM non-identifiability (cosine 0.350) as limitation-only. Pre-image 8/8 details. | HC FPR 15/21; 2-comp 7/7; r=−0.894; noise floor ~20°/25°; 0/3 dual-pass; sub-09 PCA(2,+24) vs SRM(32,0), δθ cosine 0.350 (metric non-identifiability). | Table (notation), Table (HC-FPR), Fig (HC spec), Fig (feasibility), Table (full model comp — recast 2-comp-only) |

---

## 3. Topic-sentence chain (And-But-Therefore flow)

**Intro ¶1 (And — the general problem).** Many health-related measurements carry distorted structure that acts as a phenotype: systematic, repeatable changes in how stimuli relate within a high-dimensional biological response space, of which color vision deficiency is a concrete case.

**Intro ¶2 (And — the geometric framing).** Such phenotypes are naturally expressed as a representational geometry whose pairwise relations can be systematically distorted even when categorical decoding is preserved, making the geometry, not the classification, the inference target.

**Intro ¶3 (But — the gap).** Yet structured distortions have rarely been inverted into individualized perceptual corrections, and a generic fixed filter cannot, in principle, target an individual's distortion.

**Intro ¶4 (Therefore — the move).** We therefore fit a single low-dimensional cortical distortion model to each individual's hue geometry and ask, through a three-tier argument, which mechanism a correction should target.

**Methods ¶ (How).** We transform voxel responses into a structured hue representation via a hue-selective encoding model, then fit a 2-DOF cortical opponent-axis distortion by minimizing a composite loss that combines a behavioral (per-pair JND) term with a neural (RDM) term, selecting parameters by held-out test-loss and structural adequacy rather than by raw significance.

**Results §1 ¶1 (Detection — Tier 1).** The same two of three Ishihara-confirmed CVD individuals pass the model-independent **LOCO_V4 precondition gate** (sub-10 is excluded for being null at both LOCO and SRM), so every candidate mechanism — retinal and cortical alike — operates on the identical gate-passing set; detection therefore cannot decide which mechanism to correct. *(Detection = shared precondition gate, NOT per-model perm-p significance — this is deliberately model-independent so Tier 1 does not re-import the cut perm-p logic, and avoids claiming a retinal detection sub-08 never reached, e.g. v6.1 Machado p=0.058.)*

**Results §1 ¶2 (Structural adequacy — Tier 2).** But the 1-DOF retinal/compensation family saturates at its boundary for both individuals, lacking a confusion-axis degree of freedom, whereas the 2-DOF cortical model stays interior and adequate.

**Results §1 ¶3 (Mechanism class).** The cortical model therefore resolves each individual to a sign-quadrant mechanism class — deutan β_s+/β_c−, protan β_c+ — that is reproducible across HC resamples and held-out folds, with an averaged-surface signal 2.1×–5.5× deeper than the HC null, even though the absolute parameter values are not physiologically identifiable.

**Results §2 ¶1 (Divergent correction — Tier 3).** Despite agreeing on detection, the two accounts prescribe divergent corrections: for the protan individual, the retinal model collapses 4/8 hues irreversibly while the cortical model admits an exact 8/8 bijective pre-image.

**Results §2 ¶2 (Behavioral adjudication).** This divergence is a falsifiable prediction, so a behavioral 2AFC task would simultaneously validate the correction and localize the dominant processing level.

**Discussion ¶1 (Therefore — what it buys).** The composite-loss inference compresses high-dimensional voxel data into an interpretable, invertible cortical distortion model, but its parameters are resolved only to a mechanism class, not to a physiological magnitude.

**Discussion ¶2 (Limits).** Three structured limitations remain — parameter identifiability/specificity (mechanism class robust, magnitude at the ~20°/25° noise floor), sample/out-of-sample structure (CVD N=2 makes CVD-level generalization impossible), and modeling-framework choices — and a behavioral session is the sole remaining CVD-generalization path.

**Conclusion ¶ (So).** A single cortical 2-Component model recovers subject-specific mechanism classes that converge on detection and diverge on correction, yielding a concrete, falsifiable behavioral test as the immediate next step.

---

## 4. Must-cut checklist (v6.1 lines/claims to remove)

| v6.1 ref | Claim | Why cut (Path B) | Action |
|---|---|---|---|
| **L221** | "fitted Δλ falls within the established range for moderate–severe protanomaly" | Forbidden physiological-value claim (Δλ-matches-anomaly) | Remove; sub-09 reframed to cortical (+2,+24) |
| **L370** | "(i) inferred parameters fall within established physiological ranges (Sub-09 Δλ=13.5 nm … Sub-08 Δλ=2.0 nm …)" | Forbidden physiological-value claim | Remove |
| **L372** | "constraining the fit to physiologically interpretable dimensions" | Same forbidden claim type as L266/L370 (advisor catch) | Remove |
| **L266** | "distinguished from HC fits by physiologically interpretable parameters and cross-criterion convergence" | Specificity + physiological-value claim; specificity is descriptive only | Remove |
| **L104 / L156 / L201 / L225** | "closed-testing escalation"; Machado-first-then-R+C tiering | R+C rejected; no escalation; single 2-Component model | Remove all closed-testing language |
| **L104** | contribution: "different CVD individuals require different parsimonious models" | Both subjects = same 2-Component model; differentiation = sign quadrant, not model choice | Rewrite contribution |
| **Table 1 (L200–217)** | R+C/Machado as primary per-subject result, perm-p column | R+C rejected; selection ≠ perm-p; recast to 2-Component + held-out test-loss | Replace table |
| **L188–189** | "A valid model must reach significance (p<0.05) on the per-color vulnerability profile" | Selection = held-out test_loss_median + structural adequacy, NOT perm-p | Remove perm-p-as-selection |
| **L71 (Abstract)** | "both a one-parameter retinal cone-shift model and a two-parameter retinal–cortical model" | Single 2-Component cortical model | Rewrite |
| **L243** | sub-08 2-comp (β_s=38°,β_c=−14°); sub-09 2-comp (β_s=6°,β_c=−22°) | **Wrong values.** sub-08 = (+6,−42) [38,−14 is the DROPPED βs-dom]; sub-09 β_c is **+24** not −22 (sign flip) | Replace with canonical (+6,−42) / (+2,+24) |
| **L244, L396** | sub-08 R+C-vs-2comp correction cosine = −0.18, sign agreement 3/8 | R+C rejected → this comparison is dead; divergence re-anchored on sub-09 (advisor catch) | Cut; replace with sub-09 retinal-vs-cortical divergence (cosine TBD) |
| **L367–373** | HC-specificity "why this does not invalidate the CVD results" rescue paragraph | Rescue = forbidden specificity claim (CVD distinguished from HC). Keep the FPR table + mechanism; cut the rescue | Cut paragraph, keep table |
| throughout | "1–2 DOF" | Single model is 2-DOF | "2 DOF" |
| L70, L139–146, Fig1/Fig2, abstract | LOCO interpolation-vulnerability profile as the **central** quantified object | LOCO_V4 = precondition gate only; objective = composite (γ+RDM) | Demote LOCO; promote composite/RDM |

**Discriminator (run on every section):** does it (1) reintroduce R+C/Machado as a live candidate, (2) make LOCO the fitting objective, (3) state an absolute β/Δλ as physiology, (4) use perm-p<0.05 as selection, or (5) claim CVD-vs-HC specificity? Any "yes" = not Path B.

---

## 5. TBD / data-dependent list (mark clearly — do NOT fabricate)

| Item | Status | What's needed before a final number |
|---|---|---|
| **Fig 2 predicted ΔRDM panel + residual** | TBD | Observed ΔRDM = CVD − HC mean exists in pipeline; the *predicted* ΔRDM under fitted (β_s,β_c) and the *residual* (observed − predicted) require a render step (forward via 45° categorical lookup, `s10b_v6_pca_rdm.py` make_rdm_atom path). Fig2 = 2-row: top ΔRDM observed/predicted/residual; bottom loss landscape + argmin stability. |
| **sub-09 retinal-Machado vs cortical correction cosine** | TBD | The re-anchored divergence metric (sub-09). **Not** the 0.350 (that is PCA-vs-SRM δθ = metric non-identifiability, appendix only). **Not** the sub-08 −0.18 (R+C, dead). Must be computed from sub-09 retinal-Machado pre-image vs cortical 2-comp pre-image. |
| **Fig 2 loss-landscape + argmin-stability panel** | TBD (render) | Bottom row of Fig2; data exist (test_loss surface, mode share / IQR) but panel must be rendered. |
| sub-09 mode share 87.7% / IQR (0,0) wording | Report as **reproducibility/determinism**, NOT as evidence the value is correct (closure: stability ≠ correctness). Descriptive only. | No new data; wording guardrail. |
| Results Table (2-Component) exact column set | Confirm columns | Use held-out test_loss_median ± IQR, param IQR, mode share, RDM ΔL vs (0,0), folds beating (0,0), γ ΔL. All values in §0 table; assemble, do not invent. |

---

## 6. Fig2 decision (locked, for reference)

RDM-based, **2-row**. Top row = ΔRDM **observed / predicted / residual**. Bottom row = **loss landscape + argmin stability**. The v6.1 LOCO-profile Fig2 is **DROPPED**. (Predicted ΔRDM + residual = render TBD, item §5.)
