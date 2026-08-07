# TODO — Supplementary statistical treatment (HLLM / hierarchical mixed models)

> Scope: full statistical detail for the **behavioral filter evaluation** (exp2, N=2 CVD).
> Main text (`Results/results_v4.tex` §Behavioral, line ~194) stays as-is: **deficit-anchored,
> distance-to-HC (Crawford–Howell |z|) framing**. This file collects the extra statistics that
> belong in Supplementary, plus the two small main-text additions agreed below.
>
> **Decision (do not relitigate):** the mixed model is an **auditor, not the headline**. Primary
> behavioral evidence = Crawford–Howell single-case (deficit existence) + descriptive distance-to-HC
> (targeting) + RSVP accuracy with CI. HLLM only certifies we did not fool ourselves with
> pseudoreplication / single-pair dominance. Aggregate JND effect is **n.s. under every correctly
> specified analysis** — that is the honest, intended result, consistent with "most pairs have no
> baseline deficit to correct."

---

## 0. Why aggregate JND is n.s. (the point the supplement must make cleanly)

Two compounding reasons, state both:
1. **Most pairs have no baseline deficit** (already HC-like) → nothing to improve there → they dilute any mean effect.
2. **The deutan effect that exists is concentrated in ~1 pair** (orange–yellow accounts for ~93% of the summed baseline→optimal improvement). At 8-pair granularity a single-point-dominated estimate is fragile.

Neither is a failure; both motivate the **deficit-anchored, per-pair** frame used in the main text.

---

## 1. JND — supplementary HLLM table (the "auditor" panel)

Goal: show that the JND filter effect is **not** robustly distinguishable from zero at the aggregate
level, and that the only specifications that say "significant" rely on a false assumption. Report as a
single Supplementary table, sub-08 optimal-vs-baseline (the most favorable case):

| Specification | Unit / structure | sub-08 optimal p | Honest? | Why |
|---|---|---|---|---|
| staircase-level OLS `~cond + C(pair)` | 2 staircases treated independent | ≈0.04–0.07 | ✗ | pseudoreplication (2 staircases per pair not independent) |
| MixedLM random-intercept `~cond + (1\|pair)` | 48 rows, `(1\|pair)` | ≈0.03–0.055 | ✗ | assumes filter effect **homogeneous across pairs** (false) → wrong (too-small) error term |
| **MixedLM random-slope `~cond + (cond\|pair)`** | correct error term | **0.29** | ✓ | lets filter effect vary by pair |
| paired t (8 pair-mean diffs) | 8 pairs | 0.32 | ✓ | pairing = within-pair contrast |
| Wilcoxon signed-rank | 8 pairs | 0.55 | ✓ | current main-text non-parametric |
| pair-cluster bootstrap (5k) | resample 8 pairs | 95% CI **[-0.316, +0.019]** (crosses 0) | ✓ | respects cluster + outlier |
| drop orange–yellow, paired t | 7 pairs | 0.72 (mean d = -0.009) | ✓ | shows single-pair dominance |

Variance components (random-intercept fit): σ²_pair ≈ 0.007, σ²_resid ≈ 0.020, ICC ≈ 0.25 (sub-08);
ICC ≈ 0.44 (sub-09). Note ICC is modest **because** the big cross-condition swing in orange–yellow
loads onto residual, not intercept — the direct signature of effect heterogeneity that motivates the
random slope.

**Reporting rule:** the supplement leads with the random-slope / bootstrap n.s. result; the
random-intercept p is shown only to explain *why* it is anti-conservative here. Do **not** cite the
random-intercept p as evidence of an effect anywhere.

### `(1|pair)` — what it means / what it does NOT do (one supplementary sentence)
- `(1|pair)` gives each color pair its own baseline JND level (models between-pair difficulty spread,
  σ²_pair) and correctly treats the 2 staircases of a pair as correlated → **blocks staircase-level
  pseudoreplication**.
- It does **not** account for the filter effect being concentrated in one pair. That requires the
  **random slope `(condition|pair)`** (or paired-difference / pair bootstrap). This is the subtlety
  the supplement should state explicitly.

---

## 2. sub-09 (protan) — no deficit to correct

Crawford–Howell baseline JND vs n=7 HC: **no significant deviant pair** (overall z = -0.16, p = 0.89);
green–blue only trending (z = 2.36, p = 0.070). → filter has no JND target; deployed filter mildly
distorts (green–blue → p = 0.003), individualized filter neutral. Already in main text; supplement
carries the per-pair Crawford–Howell table for both subjects.

---

## 3. RSVP 8AFC — main-text addition + supplementary per-color

**Main-text addition (small):** report aggregate accuracy **with Wilson 95% CI** (currently line 194
gives "0.81 to 0.97" bare). Individualized-filter numbers:

| Subject | baseline | window (deployed) | **optimal (individualized)** |
|---|---|---|---|
| sub-08 (deutan) | 0.81 [0.70, 0.89] | 0.97 [0.89, 0.99] | **0.97 [0.89, 0.99]** |
| sub-09 (protan) | 1.00 [0.94, 1.00] | 0.86 [0.75, 0.92] | **0.98 [0.92, 1.00]** |

(Wilson binomial, n=64/condition. Window's protan drop is acceptable — headline filter is optimal.)

**Supplementary (per-color targeting panel — "마찬가지로 todo"):** the mechanism is that the filter
lifts exactly the confusable hues and leaves ceiling hues untouched. sub-08:

```
deficit hues:  yellow 0.62 → 1.00,  green 0.62 → 1.00,  purple 0.62 → 1.00
ceiling hues:  red/cyan/blue 1.00 → 1.00 (nothing to fix)
residual:      magenta 0.75 → 0.75
```
This converges with the JND deficit axis (yellow–green) → two independent behavioral measures point to
the same deutan confusion axis. Report as a Supplementary per-color accuracy figure/table.

**Model caveat for supplement:** a `correct ~ condition + (1|color)` GLMM is the RSVP analog of
`(1|pair)` (color = the 8-hue grouping; blocks the 64→8 pseudoreplication). BUT the optimal condition
has 7/8 colors at 100% → **perfect separation** → GLMM unstable/non-convergent. Therefore descriptive
per-color accuracy + Wilson CI is primary; GLMM (Firth-penalized if attempted) is auditor only.

---

## 4. Concrete to-do checklist

- [x] **Main text** (`results_v4.tex` §Behavioral): add Wilson CI to the 0.81→0.97 sentence (table above). *(done: "0.81 (95\% CI [0.70,0.89]) to 0.97 ([0.89,0.99]) ... Wilson score interval, n=64")*
- [ ] **Supplement §HLLM**: JND specification table (§1) + one-paragraph `(1|pair)` vs `(condition|pair)` explanation.
- [ ] **Supplement**: Crawford–Howell per-pair baseline-deficit table, both subjects (§1/§2 numbers).
- [ ] **Supplement**: RSVP per-color accuracy panel (§3) + separation/GLMM caveat.
- [ ] **Canonical script**: promote the scratchpad analyses into
      `analysis/future_phase3_behavioral_analysis/analyze_exp2_mllm.py` (JND MixedLM int/slope +
      pair bootstrap + RSVP Wilson/per-color), writing to `results/exp2_behavior/`. (Currently only
      prototyped in session scratchpad.)
- [ ] Verify main-text |z| numbers (2.24 → 0.85/0.78) against the canonical script output before submission.

## 5. Numbers are from (provenance)
- JND staircase summaries: `data/behavior/{sub}_jnd_ses1_no_filter_summary.csv`,
  `data/behavior/2nd_exp/{sub}/jnd_ses2_run{1,2}_*_summary.csv`
- RSVP: `data/behavior/{sub}_rsvp_8afc_ses1_run1.csv`, `data/behavior/2nd_exp/{sub}/rsvp_8afc_ses2_run*.csv`
- HC reference: sub-01..07 ses1 no-filter.
- Crawford & Howell (1998) single-case t-test (treats n=7 HC as sample); Wilson score interval for
  binomial CI; pair-cluster bootstrap = resample the 8 pairs.
