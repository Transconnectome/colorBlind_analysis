# fig1_pipeline — image-generation prompts (SD4H ICML poster / LinkedIn) — REV 4

Grounded in SD4H_draft_v7.tex. Palette = 8 isoluminant hues:
red, orange, yellow, green, cyan, blue, purple, magenta.

Rev-4 changes vs rev-3:
- (a) BACK to circle → warped circle (shows STRUCTURAL/geometric distortion, not swatch color shift).
- (c) 2-component model = a color circle with TWO AXES drawn on it; minimal text (drop loss formula & chips).
- RDM · neural = two circles (HC circle + warped circle) with double-headed arrows between a few
  color points → the arrow lengths ARE the pairwise distances, and you see how they change.
- Phase numbering ①②③ REMOVED. Four phase words aligned to four boxes: Response · Diagnose · Simulate · Correct
  (each box has a colored header bar carrying its phase word → alignment is automatic).
- Simulate box: drop "grid-fit 1–2 DOF"; enlarge "simulate the distortion".
- Explicit box/bar sizes given below.

---

## LAYOUT SPEC (canvas 1600 × 1000 px; use for SVG/vector build)

Top panel: y 0–470 · thin gray divider at y≈485 · Bottom panel: y 500–1000.

TOP (a) left half  : x 40–780   — HC circle, center arrow, warped circle.
TOP (c) right half : x 820–1560 — color circle with two axes.

BOTTOM — 4 equal boxes, left-to-right, joined by arrows:
- outer margin 40 px each side → usable width 1520.
- arrow gap between boxes = 70 px (×3 = 210).
- box width = (1520 − 210) / 4 = 327 px each.
- box x-ranges:  B1 40–367 · B2 437–764 · B3 834–1161 · B4 1231–1558.
- box body: y 560–960 (height 400), corner radius 16.
- header BAR on top of each box: y 560–620 (bar height 60), same x-range as its box,
  filled with the box's phase color, phase word centered in large bold white type.
- arrows sit at y≈760 in the 70-px gaps.

Phase colors: Response = blue · Diagnose = amber · Simulate = purple · Correct = green.

---

## PROMPT A — full figure (pure image-AI, approach 3)

> A clean professional scientific pipeline figure, flat vector infographic style
> (BioRender / Nature Methods aesthetic), pure white background, rounded rectangles, LARGE bold
> legible sans-serif labels, high whitespace, no drop shadows, crisp thin outlines, landscape
> ~3:2. Two stacked panels separated by one thin gray divider.
>
> TOP PANEL (concept), two sub-panels side by side.
> Left (a) — STRUCTURAL distortion. LEFT: a perfect thin gray circle with eight colored discs
> (red, orange, yellow, green, cyan, blue, purple, magenta) EVENLY spaced around it, big label
> "HC". A big rightward arrow labeled "CVD distortion". RIGHT: the SAME circle and same eight
> discs but the ring is geometrically WARPED — squeezed and pinched into an egg/rubber-sheet
> shape so the discs are unevenly spaced (compressed on one arc, stretched on another), big
> label "CVD". Emphasize that the STRUCTURE of the ring is deformed, colors unchanged.
> Right (c) — the 2-COMPONENT CORTICAL MODEL, drawn as ONE color circle (eight hues on a ring)
> with TWO straight axes crossing through its center (a rotated plus-sign); each axis is a
> double-headed arrow annotated only "component 1" and "component 2". Big title above:
> "2-component cortical model". TWO small input icons feed into this model from the left, one
> above the other, joined by short arrows: (i) two adjacent color chips with a double-headed
> arrow between them, one-word label "behavioral"; (ii) a small round circle beside a warped
> circle with a couple of double-headed arrows between color points, one-word label "neural".
> Keep text minimal — icons + these one-word labels only, no formulas.
>
> BOTTOM PANEL (pipeline) — four equal rounded boxes in a row, each with a COLORED HEADER BAR
> carrying one phase word, joined left-to-right by short arrows. Phase words, in order:
> "Response" (blue bar), "Diagnose" (amber bar), "Simulate" (purple bar), "Correct" (green bar).
> Box 1 body: a side-view brain icon with a small horizontal strip of eight colored swatches;
> caption "fMRI hue responses · V1–hV4".
> Arrow labeled "dimensionality reduction".
> Box 2 body: TWO icons —
>   • a smooth curved manifold (arc) with seven colored dots on it and ONE dot lifted off as a
>     dashed hollow circle with an arrow to its predicted spot; caption "leave-one-color-out".
>   • two small circles (a round HC circle and a warped CVD circle) with double-headed arrows
>     drawn between a few pairs of colored points; caption "pairwise distance (shared space)".
> Arrow labeled "inverse inference".
> Box 3 body: an HC color circle feeding a small model block that outputs a WARPED distorted
> circle; LARGE caption "simulate the distortion".
> Arrow labeled "invert".
> Box 4 body: a top row of collapsed/dull color swatches, arrows through a lens/filter icon,
> a bottom row of restored vivid swatches; caption "color-correction filter".
>
> Consistent 8-hue palette, minimal, high contrast, no photorealism, no numbering, no LORO text.

---

## PROMPT B — art only, WORDLESS (hybrid, approach 1)

Same as PROMPT A but every text instruction becomes: **"leave an empty label zone, NO text,
letters, digits or words anywhere — wordless icons and shapes only."**
Append: *"Absolutely no typography anywhere in the image."*
Overlay the LABEL SHEET strings in a vector tool using the LAYOUT SPEC coordinates.

---

## LABEL SHEET (exact strings — big type)

TOP:
- (a): `HC` · center arrow `CVD distortion` · `CVD`
- (c) title: `2-component cortical model` · axes: `component 1` / `component 2`
- (c) inputs (icons, one word each): `behavioral` (JND: two chips + double arrow) / `neural` (RDM: circle + warped circle + distance arrows)

HEADER BARS (aligned to boxes): `Response` | `Diagnose` | `Simulate` | `Correct`

BOX BODIES:
1. `fMRI hue responses · V1–hV4`
2. LOCO: `leave-one-color-out` · RDM: `pairwise distance (shared space)`
3. `simulate the distortion`   (large)
4. `color-correction filter`

ARROWS: `dimensionality reduction` → `inverse inference` → `invert`
