# Revision Report — Methods/methods_v2.tex — 2026-05-14

Target: `docs/PAPER/Methods/methods_v2.tex` (343 lines)
Rules: §2–§18, §19, §20, §23, §26
Pre-draft: `docs/PAPER/pre_draft_2026-05-10.md` §5 Methods

---

## 1. Reverse Outline

| Lines | Paragraph | One-sentence summary |
|---|---|---|
| L17–25 | §Participants | 13 recruited; 7 HC / 2 CVD (sub-08 deutan, sub-09 protan) / 4 excluded; all CVD results treated as single-case. |
| L32–36 | §Stimuli ¶1 | Eight isoluminant CIELab hues at 45° spacing were used with a gray null filler. |
| L38–46 | §Stimuli ¶2 | Stimuli were shown in RSVP order optimised by Neurodesign; 6 runs × 8 repetitions. |
| L48–51 | §Stimuli ¶3 | CVD participants completed a second session under three filter conditions. |
| L58–61 | §MRI ¶1 | Data acquired on 3T scanner with 24 oblique slices perpendicular to the calcarine sulcus. |
| L63–68 | §MRI ¶2 | Preprocessing: BIDS conversion, mutual-information coregistration, affine+nonlinear MNI normalisation. |
| L75–78 | §ROI ¶1 | Wang-atlas ROIs (V1–hV4) defined at >50% probability with voxel counts reported. |
| L80–88 | §ROI ¶2 | Single-trial amplitudes estimated by two-stage FIR+ridge GLM, organised as 6×8×V arrays. |
| L90–94 | §ROI ¶3 | Run-to-run noise attenuated by within-subject Procrustes rotation (scaling prohibited). |
| L101–118 | §SRM | SRM trained on HC only; CVD projected by SVD; K chosen by 7-fold LOSO mean-rank aggregation on three quality metrics. |
| L125–134 | §LORO ¶1 | LORO used LDA (acc_exact) and RidgeCV (for LOCO consistency); primary metric is 8-class exact accuracy. |
| L136–142 | §LORO ¶2 | Group HC–CVD comparison via Mann–Whitney on 21 HC-to-HC and 14 HC-to-CVD pairwise scores; single-case by Crawford–Howell. |
| L149–153 | §LOCO ¶1 | LOCO held out each hue and predicted it by nearest-neighbour matching in forward-encoding channel space. |
| L155–163 | §LOCO — adj_acc | adj_acc = proportion within ±1 hue step (chance 3/8); HC above-chance by permutation, CVD by Crawford–Howell. |
| L165–171 | §LOCO — vuln. profile | The 8-dim adj_acc vector **v** constitutes the hue vulnerability profile; Spearman ρ reports model fit. |
| L173–176 | §LOCO — per-hue stats | Per-hue Crawford–Howell with Hedges' d effect sizes. |
| L183–184 | §RDM intro | Section opener: two RDM measures characterise LOCO-impairment geometry. |
| L186–194 | §RDM — disparity | Pairwise correlation distance averaged over 28 pairs; CVD vs HC-LOO by Crawford–Howell. |
| L196–205 | §RDM — ΔRDM | ΔRDM = CVD minus HC-LOO mean; cone-shift model fit tested by Spearman ρ with sign-flip permutations. |
| L207–212 | §RDM — independence note | Pairwise-disparity and ΔRDM tests are statistically independent (different null hypotheses). |
| L219–237 | §2-comp — model | Two-component angular shift (β_s S-cone, β_c confusion-axis) grounded in Emery 2021 / Brettel 1997 / Machado 2009. |
| L239–264 | §2-comp — loss | Combined MSE + RDM cosine loss with Tikhonov regularisation; simulated pattern via HC-trained ForwardEncoding weights. |
| L266–276 | §2-comp — search | 26×51 grid search; HC FPR = 7/7 so results are descriptive fits, not specificity claims. |
| L283–299 | §Filter | Pre-image of 2-component transform gives per-hue correction; verified by Brent's method to <0.001°. |
| L306–319 | §Behavioral — JND | 1-up/1-down staircases for 8 hue pairs; LOCO–JND concordance by classification agreement. |
| L321–324 | §Behavioral — 8AFC | 8AFC identifications compared to Ishihara post-hoc. |
| L326–329 | §Behavioral — planned | Phase-3 2AFC arm planned (data not collected). |
| L336–342 | §Reproducibility | Python 3.10 stack with fixed seeds; code and data available. |

### Drift vs pre-draft outline

1. **GLMsingle vs two-stage GLM**: Pre-draft ¶2 says "GLMsingle로 단일 시행 진폭 추정"; file L80–88 describes a two-stage FIR+ridge GLM with no GLMsingle cite. Unresolved since revision_report_2026-05-13. Requires PI confirmation on which pipeline is canonical.
2. **sub-10 removed**: Pre-draft ¶1 mentions sub-10 as normal control; correctly removed from current draft. ✓
3. **Second session ¶ zig-zag**: Pre-draft ¶8 (behavioral) = PENDING; file places second-session content (L48–51) inside §Stimuli, not §Behavioral concordance. Structural drift (§17).
4. **All other sections**: Match pre-draft ¶3–¶7. ✓

---

## 2. §19 Vocabulary Scan

### Tier A — Banned (1 hit, conditionally pass)

- **L266** — "Parameters were searched by **exhaustive** grid over…(26×51=1,326 cells at 2° resolution)."
  → §19A: "exhaustive" requires enumerating what was covered. The explicit cell count and resolution operationalize the claim. **CONDITIONAL PASS** — retain as is. If journal style requires, replace with "systematic grid (26×51=1,326 cells, 2° resolution)."

### Tier B — Untestable verbs (0 hits)

No instances of `study`, `explore`, `investigate`, `address`, `examine` in problematic senses.

### Tier C — Vague adjectives (2 hits)

- **L184** — "To characterise the geometric basis of LOCO impairment we computed two **complementary** measures in SRM-aligned space."
  → §19C: "complementary" must specify in what sense. Replace: "To characterise the geometric basis of LOCO impairment we computed two measures in SRM-aligned space: mean pairwise disparity (absolute elevation) and ΔRDM (directional structure)." — The distinction between absolute vs. structured is the operative sense.

- **L93** — "This step **preserves** color representational geometry while **attenuating** run-to-run measurement noise."
  → §19C borderline (implied claims without measure). Also §7 violation (motivation mixed with method). Consider moving to footnote or omitting — readers can infer the rationale. If retained, cite or quantify (e.g., "ICC before/after" if available).

### Tier D — Self-praise (0 hits)

No `elegant`, `principled`, `clean`, `unified`, `surprising`.

---

## 3. §20 Citation Audit

### Method-origin mismatches (3 — 2 persistent, 1 new)

- **L39**: `\cite{brouwer2009}` for "Rapid Serial Visual Presentation (RSVP) design" — RSVP not originated by Brouwer & Heeger. **Persistent** (unfixed since revision_report_2026-05-13). Options: cite RSVP origin (Potter & Levy 1969; or Forster 1970) or remove cite and treat as standard paradigm.

- **L81**: `\cite{dale1999, brouwer2009, brouwer2013}` for "two-stage GLM" (FIR extraction + ridge regression). **Suspect**: Dale 1999 covers event-related designs in general; Brouwer 2009/2013 are applications, not the source of this two-stage approach. Either (a) identify the correct source of the FIR+ridge procedure, or (b) note it as an in-house procedure with no cite, or (c) if this is actually GLMsingle (Prince 2022), replace entirely.

- **L102**: `\citeNP{chen2015, haxby2011, guntupalli2016}` for SRM. chen2015 = SRM origin ✓. **haxby2011 and guntupalli2016 are hyperalignment papers**, not SRM. **Persistent** (unfixed since revision_report_2026-05-13). Trim to `\citeNP{chen2015}` only, or add a note: "cf. hyperalignment \citeNP{haxby2011}."

### No cite for established concept (1 suspect)

- **L174–175**: "Hedges' $d$ with the Crawford–Howell correction" — Hedges 1981 citation still missing. **Persistent** from revision_report_2026-05-13.

### General-claim / specific-cite mismatches (0 new)

No new issues beyond those above.

### Citation density (0 stacks ≥5)

Largest stack: 3 (L81). No problem.

---

## 4. §23 Methods-specific Issues

### Results in Methods (1 — persistent)

- **L297–299**: "Comparison with alternative model classes (**arc-compression failure under the 1-DOF Machado model for sub-09**) is reported in Appendix~\ref{app:altmodels}."
  → "arc-compression failure…for sub-09" is an empirical result, not a method description. §23 explicit: "State what was done, not what happened." Replace with: "Behaviour of alternative model classes (1-DOF Machado cone-shift) under pre-image inversion is detailed in Appendix~\ref{app:altmodels}."

### Notation collision — FATAL

- **L166**: $\mathbf{v} \in [0,1]^8$ = 8-dimensional adj_acc scalar vector (hue vulnerability profile).
- **L253**: $\mathbf{v}_{\rm sim}, \mathbf{v}_{\rm obs} \in \mathbb{R}^{n_{\rm voxel} \times 8}$ = voxel pattern matrix.

Same symbol $\mathbf{v}$ denotes two structurally different objects (scalar vector vs. matrix). §6 violation. Rename one; suggest $\mathbf{P}_{\rm sim}, \mathbf{P}_{\rm obs}$ for the voxel pattern matrices in the 2-comp loss, and reserve $\mathbf{v}$ for the adj_acc vector.

### Undefined notation (2 — persistent)

- **L103**: $W_i \in \mathbb{R}^{V \times k}$ — `V` (voxels) not defined verbally before use. Add inline gloss: "$W_i \in \mathbb{R}^{V \times k}$ ($V$ voxels, $k$ latent dimensions)".
- **L103–104**: `k` introduced symbolically; "Reduced dimensions" appears at L115. Gloss needed at first use.

### Zig-zag — second session paragraph (§17, persistent)

- **L48–51**: CVD second session (filter evaluation) described in §Stimuli. Content belongs in §Behavioral concordance or §Filter. Move to §\ref{sec:methods:behavioral} and add a brief forward pointer in §Stimuli: "CVD participants completed a second session for filter evaluation (Section~\ref{sec:methods:behavioral})."

### Filler opener (§5)

- **L207**: "**Note that** pairwise-disparity tests…and $\Delta$RDM permutation tests are statistically independent."
  → Replace: "Pairwise-disparity tests (Crawford \& Howell) and $\Delta$RDM permutation tests address different null hypotheses: the former tests whether absolute pairwise distances are elevated; the latter tests whether a specific distortion model accounts for the \emph{structure} of those deviations. A significant result under one test does not imply significance under the other."

### Planned method in Methods section (§23)

- **L326–329**: "Phase-3 filter validation (planned)" — paragraphs in Methods should describe completed procedures. A planned arm with no collected data is non-standard. Options: (a) move to a "Planned analyses" or "Pre-registration" subsection clearly labelled as such, (b) move to Discussion §limitations, or (c) add a clear `% PENDING` comment and a journal note. The current label "(planned)" in `\paragraph{}` is informal.

### Missing software versions (Minor)

- FreeSurfer version (L65) — not reported.
- FSL FLIRT/FNIRT version (L66–67) — not reported.
- ezBIDS version (L63) — not reported.
- Neurodesign version (L41) — not reported.

---

## 5. §26 Checklist

### Reverse outline
- [✓] Each paragraph has one identifiable role
- [~] §LOCO vulnerability paragraph (L165–171): mixes profile definition + model-fit stat forward-ref + group-comparison intro — borderline §7
- [✗] Match to pre-draft outline: GLMsingle vs two-stage GLM still unresolved (¶2 drift)
- [✓] No paragraph requires two sentences to summarize

### Claims
- [✓] Tier A: no banned vocabulary (exhaustive enumerated — pass)
- [✓] Tier B: no untestable verbs
- [✗] Tier C: "complementary" (L184), "preserves…attenuating" (L93)
- [✓] Tier D: no self-praise

### Citations
- [✗] Method origin: L39 RSVP cite wrong (persistent)
- [✗] Method origin: L81 two-stage GLM cite stack suspect (persistent)
- [✗] Method origin: L102 SRM cite includes hyperalignment (persistent)
- [✗] Method origin: L175 Hedges 1981 missing (persistent)
- [✓] No 5+ citation stacks

### Structure
- [✗] L166 vs L253: **v** notation collision — FATAL
- [✗] L297–299: results in Methods ("arc-compression failure") — persistent
- [✗] L48–51: second session zig-zag in §Stimuli (§17) — persistent
- [✗] L207: "Note that" filler opener (§5)
- [✗] L103: V, k undefined at first appearance
- [✓] Topic sentences first: all 11 subsections open with purpose-defining sentence
- [✓] Terminology consistent: hV4 consistent; "gray filler" consistent; adj_acc consistent
- [✓] Pronouns unambiguous

### Section-by-section (Methods-specific, §23)
- [✓] Order matches Results: LORO → LOCO → ΔRDM → 2-comp → Filter → Behavioral ✓
- [✗] No results in Methods: L297–299 violation (persistent)
- [✓] Variables defined before use (except V, k at L103)
- [~] Software versions: Python stack ✓; FreeSurfer/FSL/ezBIDS/Neurodesign missing

---

## 6. Priority Summary

Total issues: **14** (1 Fatal, 6 Serious, 7 Minor)

### Fatal (1)
1. **L166 vs L253**: $\mathbf{v}$ notation collision (adj_acc vector vs voxel matrix) — **Fix first.**

### Serious (6)
2. **L297–299**: results-in-methods ("arc-compression failure for sub-09") — rephrase as method description
3. **L81**: two-stage GLM citation stack (dale1999/brouwer2009/brouwer2013) — none supports FIR+ridge; resolve with PI
4. **L102**: SRM cite includes hyperalignment (haxby2011, guntupalli2016) — trim to chen2015
5. **L48–51**: second-session paragraph zig-zag in §Stimuli — move to §Behavioral
6. **L103**: V and k undefined at first use — add inline gloss
7. **L39**: RSVP cite brouwer2009 wrong origin — replace or remove

### Minor (7)
8. L175: Hedges 1981 citation missing
9. L207: "Note that" filler opener — restate directly
10. L184: "complementary" — specify absolute vs. structured distinction inline
11. L93: "This step preserves…" motivation line — move or cut
12. Pre-draft GLMsingle vs file two-stage GLM — needs PI decision before final submission
13. L326–329: planned-method paragraph — reframe or move
14. Missing software versions: FreeSurfer, FSL, ezBIDS, Neurodesign

**Recommended fix order**: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (batched with 3) → 9–14 batched.

**Pass status**: Methods is NOT submission-ready. Fatal (notation collision) + 2 persistent Serious (results leak, wrong SRM cite) block §26 pass.
