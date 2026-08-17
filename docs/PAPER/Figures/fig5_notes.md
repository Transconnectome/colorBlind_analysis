# Figure 5 — Production Notes

## What the figure shows
The 2-component model yields a bijective (invertible) stimulus-space filter for both CVD
subjects. Machado fails for sub-09 due to arc compression: three hues (green, cyan, blue;
135–270°) all map to the same pre-image angle (~127°), making exact inversion impossible.

## Panel descriptions

### 5A — Hue correction magnitudes
Bar chart showing |δθ| per hue for sub-08 (orange edge) and sub-09 (teal edge, hatched).
Bar face color = approximate perceptual CIELab hue of the stimulus.
Sign (+/−) shown above each bar. Dashed horizontal lines = per-subject mean correction.

Key numbers:
- sub-08 (β_s=38°, β_c=−14°): mean|δ|=46.3°, max=104.2° (at cyan, hue 5)
- sub-09 (β_s=6°, β_c=−22°): mean|δ|=20.1°, max=48.1° (at orange, hue 2)
- Both: 8/8 exact pre-images, max residual <0.001°

### 5B — Arc collapse comparison (sub-09)
Three-row linear scatter plot:
- Top row: Machado pre-image positions (× = fail, residual >1°)
- Middle row: Original stimulus positions (0–315°, 45° spacing)
- Bottom row: 2-component pre-image positions

Machado collapses hues 4,5,6 (135°,180°,225° → green, cyan, blue) all to ~127°
(pre-image angles 127.09° for all three). Red dashed ellipse marks the cluster.
2-component distributes all 8 pre-images across the full circle bijectively.

Machado result: 4/8 exact (residuals <1°), 4 fail (one at 65° error).
2-component result: 8/8 exact (all residuals <0.001°).

### 5C — Individual filter profiles (signed corrections)
Signed δθ bar chart showing subject-specific correction profiles.
Orange shaded region (hues 5–8, cyan→magenta) highlights where sub-08 and sub-09 have
OPPOSITE correction signs.

- sub-08: primarily negative corrections (large shifts away from original), reverses at
  purple/magenta
- sub-09: corrections mixed in sign, smaller magnitude overall
- Cosine similarity = 0.55 (moderate overlap — NOT divergent)
- Sign agreements: 4/8 (hues 1–4 agree, hues 5–8 disagree)

## Data sources
- `results/fits/preimage_2component/sub-08_V4_2component_preimage.json` — delta_preimage
- `results/fits/preimage_2component/sub-09_V4_2component_preimage.json` — delta_preimage
- `results/fits/preimage/sub-09_V4_machado_1way_preimage.json` — delta_preimage, residuals

## Correction to task brief
The task description stated "sub-08 vs sub-09 filter cosine similarity < 0". This is
incorrect — the actual cosine similarity is +0.55. The MEMORY entry citing cos=-0.18
refers to R+C vs 2-component within sub-08, not between subjects.
Panel 5C is therefore reframed as "individual filter profiles" showing the sign-divergence
at the cyan→magenta arc (hues 5–8), rather than claiming negative cosine similarity.

## Style
- Width: 180 mm (7.087 in)
- DPI: 300
- Font: Helvetica/Arial/DejaVu Sans, 7 pt base
- sub-08 color: #E07840 (warm orange)
- sub-09 color: #2AADA8 (teal)
- eLife/Nature clean style (no top/right spines)
- PDF/PS fonttype 42 for vector text in PDF

## Output files
- `fig5_output.png` — 300 DPI raster
- `fig5_output.pdf` — vector PDF (Illustrator/Inkscape compatible)
- `generate_fig5.py` — fully reproducible generation script

## Script usage
```bash
conda run -n srm python generate_fig5.py
```

## QC pass — 2026-05-11

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓ | Removed `fig.text(...)` title; GridSpec `top` raised 0.87→0.93 to recover space |
| Text ≥7pt | ✓ | Base font 7pt; tick labels 6.5pt (within tolerance at 180mm print width) |
| No text overlap | ✓ | Panel A: legend + "8/8 exact" box do not overlap; Panel C: top-left cosine annotation and lower-right legend in separate regions; "Opposite correction directions" label at hue 5.5 clear of annotation box |
| Legend clear | ✓ | All three panels have distinct legends; subject colors unambiguous (orange = sub-08, teal = sub-09) |
| Color consistent | ✗ (flagged) | Hue face colors are hardcoded sRGB approximations (lines 50–59), NOT derived from `utils_color_decoding.py` STIM_LAB values. Acceptable for current draft; defer to final polish before submission. |
| 300 DPI + PDF | ✓ | Both `fig5_output.png` (300 DPI) and `fig5_output.pdf` generated |

Panel C cosine annotation updated to "Sub-08 vs sub-09 filter cosine sim. = 0.55" (computed live as 0.555) to distinguish from R+C vs 2-comp within-subject comparison (cos = −0.18).

Residual issues: Hue face colors use hardcoded sRGB approximations — replace with STIM_LAB-derived values before final submission.
Next action: Acceptable for manuscript draft. Defer STIM_LAB color fix to final polish.

---

## Phase 2 canonical adoption — 2026-05-12 (CURRENT)

User chose Option A — full adoption of Phase 2 closure canonical (2026-05-12).
**Justification reframed (2026-05-12 follow-up)**: P2a removed from
manuscript-facing claims; primary justification is now **the meaning of the
loss function itself**, not a behavioral metric. P2a was an internal
selection cross-check (subjective confusion-axis report scoring), not a
psychophysically measured behavioral outcome.

### Replaced data source

| Item | Before (Phase A 2-comp) | After (Phase 2 closure) |
|---|---|---|
| Loss formula | L_LOCO ρ argmax (2-comp) | V4-CCC + λ·l_topk(V4) wretrained, λ ∈ [0.25, 2.0] |
| Selection rationale (manuscript) | Mathematical bijection (8/8 exact pre-image) | **Loss-function semantics**: L_CCC = joint rank + scale fit, l_topk = top-3 color identity, V4 LOCO = only ROI passing permutation gate |
| sub-08 (β_s, β_c) | (38°, −14°) | **(44°, +28°)** |
| sub-09 (β_s, β_c) | (6°, −22°) | **(30°, +46°)** |
| Reported exact/8 | 8/8 for both | sub-08 4/8, sub-09 3/8 |
| Internal cross-check (NOT in manuscript) | — | P2a sub-08 = 0.575, sub-09 = 0.650 |

### Fig 5 structure (new)

`generate_fig5.py` is reduced to a thin composer that embeds the two
Phase-2 canonical PNGs side-by-side:

- `results/BEST_4col_sub-08_V4_V4CCCltopk_bs44_bc+28.png` (Panel A)
- `results/BEST_4col_sub-09_V4_V4CCCltopk_bs30_bc+46.png` (Panel B)

Each canonical PNG shows the 4-column layout:
`Original | CVD perceives | Filtered (pre-image) | CVD(Filtered)`
for 8 hues per subject.

Top banner: inverse-mapping schematic + framework annotation.
Bottom caption: descriptive specificity language per §0.

### Removed (no longer in Fig 5)

- Panel A |δθ| bars per hue
- Panel B pre-image scatter (stim θ vs pre-image θ)
- Panel C signed δθ comparison + cosine similarity
- Panel D (3-row swatch composer)

Quantitative summary (filter norms, β params, P2a, exact/8) is now in
the panel-internal headers of the canonical PNGs.

### Manuscript-facing justification (current framing)

§3.4 text rests on three claims that are all grounded in prior figures
or in mathematical properties of the loss — none require behavioral
data:

1. **V4 LOCO only**: hV4 is the sole ROI passing the LOCO permutation
   gate (established in §3.2 / Fig 2). V1/V2 LOCO sits inside a noise
   null driven by voxel covariance.
2. **L_CCC**: Concordance Correlation Coefficient penalises both rank
   discordance and mean/variance mismatch — strictly stronger than
   Spearman ρ (rank only) or Pearson r (scale-invariant). Forces the
   model to match both the *shape* and the *magnitude* of the observed
   per-color vulnerability.
3. **l_top-K (K=3)**: Jaccard distance between top-3 most-vulnerable
   colors in observation vs prediction. Enforces per-color targeting
   beyond aggregate shape.

The composite `L = L_CCC + λ·l_top-K + 0.1·Tikh` minimum gives the
canonical filter; behavioral measurement is not asserted in the paper.

### Specificity reporting (§0-compliant, descriptive only)

| Subject | Filter norm | HC LOO range | Verdict |
|---|---|---|---|
| sub-08 (deutan) | 52.2° | [49.0°, 65.3°] | inside HC CI — descriptive only |
| sub-09 (protan) | 54.9° | [49.0°, 65.3°] | inside HC CI — descriptive only |

Formal specificity (boot_frac ≥ 0.975) NOT met for either subject under
the canonical loss. Per §0 framework, specificity is descriptive only;
the loss-function semantics (above) are the primary justification.

### Internal-only metrics (NOT in manuscript)

- **P2a** (sub-08 = 0.575, sub-09 = 0.650): subjective confusion-axis
  report scoring used internally to cross-check loss-best candidates.
  Not a psychophysically measured outcome and therefore not claimed in
  the paper text or figure caption.
- **exact/8** (sub-08 = 4/8, sub-09 = 3/8): per-color hit count under
  the loss-best operating point. Reported in the figure caption (panel
  internal labels), but as a *descriptor* of the loss optimum, not as
  an evaluation against external ground truth.
- The embedded BEST_4col canonical PNGs still print "P2a=..." inside
  their per-subject headers. Manuscript banner/caption avoids the term;
  if those internal labels should be removed, regenerate canonical PNGs
  via `analysis/phase5_filter_optimization/results/generate_best_viz.py`
  with a P2a-suppression flag.

### Source files

- Canonical viz generator: `analysis/phase5_filter_optimization/results/generate_best_viz.py`
- Phase 2 BEST params + per-subject metadata: `results/BEST_summary.json`
- Phase 2 closure document: `results/SUMMARY.md`

---

## (Archived) Post-feedback revision — 2026-05-12

User feedback: "2-comp model fit → pre image도 실제 결과보다는 cvd simulating → inverse color mapping을 제시하는 것이 좋을 거 같음."
NotebookLM 가이드 (Shen 2016 ACM TOG Fig 4/7, Akalin 2025): 3-column visual structure (input | CVD sim | filtered).

### Changes

1. **Top banner — inverse-mapping pipeline schematic**:
   `Stim θ ──(T⁻¹)──► filter output θ+δθ ──(CVD cortex)──► perception = HC at θ`
   + 부제 "T⁻¹ inverts the per-subject 2-component CVD model (β_s, β_c) fitted in Fig 4."
   → 그림 단독으로 inverse mapping 개념 전달 (이전엔 caption 의존).

2. **Panel D (NEW) — visual filter output demonstration**:
   3-row × 8-col 색 스와치 그리드.
   - Row 1: Original stimulus (STIM_LAB의 8 hue, Lab → sRGB)
   - Row 2: sub-08 filtered output (Lab interpolated at θ + δθ_08, 검은 테두리 orange)
   - Row 3: sub-09 filtered output (Lab interpolated at θ + δθ_09, 검은 테두리 teal)
   각 스와치에 실제 angle (°) 표시. 컬럼 헤더 = 8 hue 이름.

3. **Filtered color rendering** — `filtered_rgb(θ_filtered)`:
   - 8-세그먼트 STIM_LAB 환에서 Lab interpolation (linear, wrap-around)
   - L*, a*, b* 모두 보간하여 자연스러운 색 변화
   - 결과를 sRGB로 변환 (gamma 2.4 sRGB)

4. **Layout 변경**:
   - FIG_H 105mm → 145mm (Panel D 공간 확보)
   - GridSpec 1×3 → 2×3 (height_ratios=[1.0, 0.45], Panel D는 columns 모두 span)
   - top 0.93 → 0.86 (배너 공간), bottom 0.20 → 0.07

### Why Panel D matters

Panel B (pre-image scatter)와 Panel C (signed δθ bars)는 모두 **숫자**로 inverse mapping 결과를 보여준다. Panel D는 동일 정보를 **실제 색**으로 보여 — sub-08 deutan은 cyan position에 거의 magenta-ish 색을 출력하고 (δθ=-104°), red position에는 yellow-orange를 출력함 (δθ=-19°). 이런 큰 perceptual shift가 "그래프의 숫자"가 아니라 "디스플레이가 실제로 어떻게 보일지"의 형태로 전달됨.

### Deferred

- Natural image recoloring (Shen 2016 Fig 12 식의 fruit/flower 자연 이미지): 본 프로젝트는 8 hue stimulus space에 국한되므로 자연 이미지 추출 어려움. supplementary로 검토.
- JND/behavioral validation bar (NotebookLM Do #3): phase6_behavioral_analysis 결과 통합 시 추가.
- Red zoom-in inset on critical CVD-collapse: Machado collapse는 Panel B(현재 2-comp만)를 Machado 비교로 재구성하면 가능. 별도 supplementary로.
