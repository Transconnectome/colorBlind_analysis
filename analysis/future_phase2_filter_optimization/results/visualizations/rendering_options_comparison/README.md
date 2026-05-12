# Rendering Options Comparison

**Date**: 2026-05-10
**Test case**: sub-08 deutan, 2-comp F0 canonical (β_s=38°, β_c=-14°)
**Scope**: c1-c8 only (Tier 1 fMRI ring)
**Purpose**: Choose visualization rendering convention that best matches actual MRI screen.

## Source of MRI Stimulus

`/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind/colorBlind_test.py:81-91`

```python
COLOR_LAB = {
    'color_1': [75, -40.0, 0.0],     # 0°  Red
    'color_2': [75, -28.28, -28.28], # 45° Orange
    ...
    'color_8': [75, -28.28, 28.28],  # 315° Magenta
}
# All at L*=75, C*=40 isoluminant ring.
# PsychoPy was set to display COMPLEMENTARY colors (per user 2026-05-10).
```

## Files

| File | Description |
|---|---|
| `option_A_vivid_sub08_2comp.png` | All 4 cols use `angle_to_rgb_vivid` (max-saturation per hue) |
| `option_B_psychopy_complement_sub08_2comp.png` | All 4 cols use `lab2rgb([75, +C·cos(θ), +C·sin(θ)])` (PsychoPy + complement applied) |
| `option_C_current_state_sub08_2comp.png` | **Current state** — col 1,3 vivid; col 2,4 ring + Machado anchor (Q1 BUG) |
| `option_D_psychopy_no_complement_sub08_2comp.png` | All 4 cols use `lab2rgb` on dict directly (no complement; hue ≠ label) |
| `sidebyside_col1_4options.png` | Col 1 (Original) c1-c8 across all 4 options for direct comparison |

## Per-option summary

### Option A — vivid (max saturation)
- Hue convention: standard CIELab (matches labels)
- L*: hue-dependent sweep [20-97], picks max saturation point
- C*: hue-dependent max in-gamut (range ~50-150)
- **Visual**: Vivid, saturated colors (e.g., c1 dark magenta-red, c3 bright yellow, c5 bright cyan)
- **Pros**: Visually striking; matches user's empirical MRI memory
- **Cons**: Does NOT match PsychoPy theoretical output; no model basis for L*/C* choice
- **For 2-comp viz**: Hue rotation only (no ΔL*); col 2,4 = vivid render of perceived hue

### Option B — PsychoPy + complement (theoretical faithful)
- Hue convention: standard CIELab (matches labels, post-complement)
- L*: 75 (fixed)
- C*: 40 (fixed)
- **Visual**: Pastel, desaturated colors (e.g., c1 light pink, c3 muddy ochre, c5 pale teal)
- **Pros**: Theoretically faithful to PsychoPy; matches actual experimental ring spec
- **Cons**: User reports MRI screen looks more vivid than this
- **For 2-comp viz**: Hue rotation only; all 4 cols at L=75, C=40

### Option C — current state (with Q1 bug)
- Col 1, 3: vivid (Option A method)
- Col 2, 4: ring at L=75±Machado_ΔL*, C=40 (Option B method but with cone-shift L*)
- **Visual**: Inconsistent — col 1,3 vivid; col 2,4 pastel
- **Cons**: (a) Q1 bug — uses Machado Δλ even in 2-comp viz; (b) Q3 issue — col 1,3 vs col 2,4 use different rendering convention
- **Status**: Current production output (F0/F1/F2/F3/F4/F6 PNGs). To be replaced.

### Option D — PsychoPy no complement
- Hue convention: dict values used directly (no complement)
- **Visual**: Hue mismatches labels (c1 "Red" → green/cyan; c5 "Cyan" → pink)
- **Cons**: Internally inconsistent; conflicts with user's "보색 적용" statement
- **Use**: Only if user can confirm PsychoPy did NOT do complement (then labels are wrong)

## How to choose

Open the PNGs side-by-side with your memory of the MRI screen and select:

1. **If MRI looked vivid (saturated colors, Yellow=bright yellow, Red=vivid red)**: Option A
2. **If MRI looked pastel (light pink, muddy yellow, pale cyan)**: Option B
3. **If neither matches well**: Need monitor calibration data or actual MRI screenshot

Once selected, apply the rendering convention uniformly across all 4 columns (Q3 fix) and remove Machado anchor for 2-comp model (Q1 fix).

## Bug fix coupling (decided regardless of rendering option)

**Q1 bug**: `dlam_cvd = cell['dlam_anchor']` (Machado Δλ) used for L* anchor in 2-comp viz.
**Fix**: For 2-comp, force L_cvd = L_STAR = 75 (no cone-shift; 2-comp ΔL* = 0 by definition).
**Files**: `visualize_phase3_preimage.py:230-262`, `visualize_filter_candidates.py:444-478`.

For Machado / R+C viz, keep model-specific ΔL* (each model's own cone-shift).
