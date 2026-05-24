# OHBM 2026 Poster — Layout v9 (draft for discussion)

**Source abstract**: `OHBM_Abstract_v8.md` (v8, post-Phase 2/3, FE-unified)
**Format assumed**: OHBM standard landscape ~120 × 90 cm (1.33:1). Adjust columns if portrait.
**Status**: layout draft to discuss; figure drafts in this folder.

---

## 0. One-line takeaway (poster header, large type)

> **Hue interpolation, not discrimination, is disrupted in color vision deficiency** — an fMRI dissociation under matched forward-encoding readout.

Authors · affiliations · QR (right side) · funding (small).

---

## 1. Three-column, seven-block layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TITLE (banner) — Authors, SNU, contact                                       │
├───────────────────────┬──────────────────────────┬──────────────────────────┤
│ COL 1                  │ COL 2                     │ COL 3                     │
│                        │                           │                           │
│ ▌1  BACKGROUND & GAP   │ ▌3  ONE READOUT,          │ ▌5  RESULT B —            │
│                        │     TWO QUESTIONS         │     INTERPOLATION         │
│  · CVD = reweighted    │                           │     IMPAIRED AT hV4        │
│    cortical input¹     │   FIG 1 — design +        │                           │
│  · gap: signal-loss    │     pipeline +            │   FIG 2(A vs B)           │
│    vs geometric        │     LOCO concept         │     LORO bars (small)     │
│    distortion?         │     wedge fan            │     LOCO bars (large)     │
│  · classify ≠ inter-   │                          │   Caption: dissociation   │
│    polate (B&H '09)    │  Caption: "same FE       │     g=1.69 at hV4         │
│                        │   readout, LORO vs LOCO" │                           │
│ ▌2  HYPOTHESIS          │                          │ ▌6  CONVERGENT GEOMETRY   │
│   pre-specified        │ ▌4  RESULT A —            │                           │
│   directional          │     CLASSIFICATION        │   FIG 3 (NEW) — SRM       │
│   dissociation:        │     PRESERVED             │     single-case panel:    │
│                        │                           │     HC mean V1 RDM        │
│   signal-loss →        │   small bar inset         │     sub-09 V1 RDM         │
│     LORO↓ AND LOCO↓    │   "no ROI reaches sig"   │     difference (L-M box)  │
│   distortion →         │     g≤0.92 everywhere    │                           │
│     LORO≈, LOCO↓       │                          │   below: FIG 2D (small)   │
│     specifically       │                          │     SRM disparity z       │
│     where inter-       │                          │     across all subj.      │
│     polation lives     │                          │                           │
│                        │                          │                           │
├───────────────────────┴──────────────────────────┴──────────────────────────┤
│ ▌7  CONCLUSION + FUTURE WORK                                                 │
│   "Hue circle is warped, not broken" → defines a target for stimulus-space   │
│   correction (pilot 2-component & R+C cone-shift models; behavioral tests   │
│   planned).  Refs (5) · Funding · QR for code/data.                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Block-by-block content (text + figure mapping)

### Block 1 · Background & Gap (~250 chars, plus 1 small icon)
Pull from abstract Intro ¶1–2.
- CVD reweights cortical input (Tregillus 2021)¹
- Existing fMRI = group-mean activation; doesn't dissociate amplitude loss vs geometric reshape
- Decoding conflates **classify** (known hue) vs **interpolate** (novel hue) — Brouwer & Heeger³, Bannert & Bartels²

### Block 2 · Hypothesis (~200 chars)
Two-row table:

| Account | LORO | LOCO @ hV4 |
|---|---|---|
| Signal loss | ↓ | ↓ |
| Geometric distortion | ≈ | ↓ |

Directional, pre-specified.

### Block 3 · Design + Pipeline + LOCO Concept (BIG figure: Fig 1)
**Fig 1 v9** (replaces v8.1 Fig 1):
- **Row A**: stimulus ring (8 vivid hues — pull from `colorBlind_test.py` screenshots, not pastel CIELab)
- **Row B**: pipeline boxes (same as v8.1 — fMRIPrep → Wang ROIs → GLM → Procrustes → FE-6 → LORO/LOCO branch). Keep tight.
- **Row C** (NEW): "What is LOCO?" cartoon (left) + HC sub-06 hV4 wedge fan (middle, MAE 62°) + CVD sub-09 V1 wedge fan (right, MAE 103°). See `loco_cartoon_v9_2_draft.png`.

Caption (~250 chars):
> 8 isoluminant DKL hues; same forward-encoding model under two CV schemes. **LOCO** holds out one *colour* — tests interpolation. **LORO** holds out one *run* — tests classification. Wedges = per-run prediction spread; wedge width = uncertainty.

### Block 4 · Result A — Classification preserved (small figure)
**Fig 2A** from v8.1 — LORO bars, just a thumbnail. Key numbers as a 1-line: V1 g=0.37, V2 g=0.92, V3 g=0.38, hV4 g=0.43; *all p ≥ 0.108*.

### Block 5 · Result B — Interpolation impaired (BIG figure)
**Fig 2B + 2C side-by-side** from v8.1, possibly enlarged. Key story: hV4 p=.017, g=1.69; HC-only label-perm null shows only hV4 LOCO exceeds null (p=.026), so the dissociation is meaningful precisely where interpolation is well-defined.

Caption stress: effect-size ratio at hV4 ≈ 4:1 (LOCO 1.69 / LORO 0.43) anchors dissociation in **operation**, not model class.

### Block 6 · Convergent Geometry (NEW figure + Fig 2D)
- **Top**: `srm_single_case_v9_draft.png` — HC mean V1 RDM | sub-09 V1 RDM | difference. L-M cone-opponent cells boxed; cells with reduced dissimilarity = perceptually confused pairs.
- **Bottom**: Fig 2D from v8.1 (SRM disparity z bars, all 4 ROIs, sub-08/sub-09/sub-10) — kept compact.

Caption stress:
- Individual example shows what "geometric distortion" looks like at the level of color pairs.
- Group SRM is a summary statistic over the full k-dim space; bars show this generalizes beyond the single case (sub-09 V1 p=.003, sub-08 V2 p=.033, sub-10 null everywhere — specificity control).

### Block 7 · Conclusion + Future Work (text only, with QR)
3 sentences:
1. Dissociation: classification preserved, interpolation selectively impaired at hV4 — same readout, different operation.
2. Convergent SRM geometry corroborates at V1/V2.
3. Geometric (not amplitude) distortion → invertible in principle → pilot inverse-filter work (cone shift + cortical) is underway.

References (5 max), funding, QR for repo/preprint.

---

## 3. Figure assembly checklist

| Figure | Status | Source file | Notes |
|---|---|---|---|
| Fig 1 row A (stimulus ring) | ✓ exists | v8.1 `make_fig1_v8_1.py` | replace pastel colors with vivid (per `guide_for_OHBM.md`) |
| Fig 1 row B (pipeline) | ✓ exists | v8.1 `make_fig1_v8_1.py` | keep as is |
| Fig 1 row C (NEW LOCO cartoon) | draft | `make_loco_cartoon_v9_2.py` | polish concept panel; consider polar inset |
| Fig 2 A/B/C/D | ✓ exists | v8.1 `make_fig2_v8_1.py` | keep; 2D shrunk to make room for Fig 3 |
| Fig 3 (SRM single case) | draft | `make_srm_single_case_v9.py` | scope = sub-09 V1 only; do NOT overclaim |

---

## 4. Open questions for discussion

1. **Block 5 vs Block 6 size**: should Fig 2A (LORO) be a thumbnail (current plan) or full-size for "honest negative" emphasis? Bigger = stronger dissociation visual; smaller = saves real estate.
2. **Fig 3 ROI**: V1 (strongest individual SRM, but locus mismatch with LOCO hV4) — confirmed via advisor as honest choice. Confirm OK before polishing.
3. **Inverse-filter teaser**: text-only one paragraph (current plan) or add a small schematic? Risk: teaser-figure invites questions Phase 3 hasn't answered yet.
4. **Stimulus color extraction**: use screenshots from `~/Projects/colorBlind/Screenshots/` (per OHBM guide §1) — needs ~30 min of pixel-sampling work; defer or do now?
5. **Block 1/2 split**: combine into one block to free space for an enlarged Fig 3 below Block 6?
6. **QR target**: GitHub repo, OSF preprint, or both (two QRs)?

---

## 5. Production order (if proceeding)

1. Settle questions in §4 with PI.
2. Iterate Fig 1 row C and Fig 3 to publication quality (~2 hr each).
3. Re-export v8.1 Fig 2 panels at poster DPI; replace pastel with vivid colors.
4. Assemble in PowerPoint / Affinity Publisher (template TBD).
5. PI review pass → printer.

---

## Appendix: numbers to feature on the poster

(All from v8 abstract; verified against `Figure_2_v8_1_numbers.json`.)

- N = 10 (7 HC + 3 CVD: sub-08 deutan, sub-09 protanomalous, sub-10 mild deutan)
- LORO FE: V1 g=0.37 (p=.342), V2 g=0.92 (p=.108), V3 g=0.38 (p=.300), hV4 g=0.43 (p=.250)
- LOCO FE: **hV4 g=1.69 p=.017**, V2 g=0.94 p=.075 (trend), V1 p=.242, V3 p=.633
- HC label-perm null: **hV4 p=.026** (only ROI exceeding null), V1/V2/V3 all p > .35
- SRM individual: **sub-09 V1 z=5.17 p=.003**, sub-08 V2 z=2.94 p=.033; sub-10 null at all ROIs
- Effect-size ratio at hV4: LOCO/LORO = 1.69/0.43 ≈ **4:1**
