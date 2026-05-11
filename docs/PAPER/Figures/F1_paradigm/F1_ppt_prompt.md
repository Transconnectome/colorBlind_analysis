Create a single academic figure slide for a neuroscience journal paper (eLife style).
Slide dimensions: 18 cm wide × 12 cm tall. White background. No slide title.
Font: Arial. Panel labels: bold 10pt uppercase (A, B, C), top-left corner of each panel.

---

## Panel A — Experimental paradigm (left third, ~6cm wide)

Top-left sub-element: A circular hue wheel divided into 8 equal sectors, labeled clockwise
starting from right: Red, Orange, Yellow, Green, Cyan, Blue, Purple, Magenta.
Colors should use perceptually correct hues. Label the circle "DKL hue wheel, 8 colors, 45° spacing".

Below the wheel, a plus sign (+) connecting to a horizontal stimulus timeline:
- Show a fixation cross, then a sequence of 8 colored squares (use the 8 hue colors above),
  with "..." at the end
- Label: "6 runs × 8 colours / run"
- Small arrow pointing to a target square labeled "RSVP — detect oddball target"

Bottom text (8pt, gray): "HC: sub-01–07 (N=7) | CVD: sub-08 deutan, sub-09 protan"

---

## Panel B — ROI anatomy schematic (center, ~5cm wide)

Draw a simplified lateral-view brain outline (smooth oval, gray outline, white fill).
Inside the brain, show 4 overlapping colored ellipses representing retinotopic areas:
- V1 (rightmost/posterior, blue, largest)
- V2 (overlapping V1, slightly left, light blue)
- V3 (overlapping V2, teal)
- hV4 (leftmost/anterior, coral/salmon, slightly smaller)

Label each with its name inside. Add small "Anterior" and "Posterior" text at left/right ends.
Below the brain: "V1 → V2 → V3 → hV4 (retinotopic hierarchy)" in 8pt italic.

Legend top-right (small): colored squares for V1 (blue), V2 (light blue), V3 (teal), hV4 (coral).

---

## Panel C — Analysis pipeline (full width, bottom half, ~18cm × 5cm)

Two horizontal rows of rounded-rectangle boxes connected by arrows, left to right.
All boxes: same height (~1.2cm), rounded corners, 8pt white bold text inside.

Row 1 label (left, gray italic 7pt): "Stage A | Preprocessing & alignment"
Row 1 boxes (dark navy blue fill, left to right):
1. "Raw fMRI"
2. "GLMsingle" (subtitle in 7pt: "β amplitudes")
3. "Procrustes align" (subtitle: "per session")
4. "SRM" (subtitle: "HC-only, K=3/4")
5. "Shared colour space" (subtitle: "hV4 W")

Arrows connecting each box left to right (→).

A vertical arrow down from "Shared colour space" splits into two branches going right:

Row 2 label (left, gray italic 7pt): "Stage B–C | Decoding & filter synthesis"
Row 2 boxes (dark green fill, left to right):
1. "LORO" (subtitle: "discrimination")
2. "LOCO" (subtitle: "interpolation")
3. "CVD characterise" (subtitle: "LOCO vulnerability", coral/red fill)
4. "2-component model" (subtitle: "β_s, β_c", coral/red fill)
5. "Pre-image filter" (subtitle: "δθ per colour", coral/red fill)

Arrows connecting each box left to right (→).
The vertical split from Row 1 end connects to BOTH "LORO" and "LOCO" with a Y-junction arrow.

---

## Style notes
- No shadow, no gradients — flat design
- Box border: none (or 0.5pt matching fill color)
- Arrow style: simple filled arrowhead, 1pt line, dark gray (#444444)
- Do not add any slide title, footer, or page number
- Export as editable PPTX and also as 300 DPI PNG
