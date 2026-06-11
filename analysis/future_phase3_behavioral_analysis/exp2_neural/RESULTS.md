# exp2 neural HC-likeness — sub-08 (descriptive)

**Question**: does the personalized **Optimal** filter make CVD voxel response more
HC-like than (a) the macOS **Window** filter and (b) **no filter**?

**Scope**: sub-08 deutan only; single-subject **descriptive** (Cohen's d vs HC
distribution, no inferential p — permutation null deprecated for grand-mean bias).
4 runs/condition (Window = runs 1,4,5,8; Optimal = runs 2,3,6,7; ABBA WOOWWOOW).
V1 primary, V2/V3 supporting, V4(hV4) descriptive-only.

## Figure
`figures/exp2_neural_hc_likeness_{native,matched}.png/.pdf` (`scripts/generate_exp2_fig.py`, cloned from
paper `generate_fig2.py` style). 2×2: A=LOCO ρ, B=FE-6 LORO (functional, ↑HC-like); C=SRM disparity
(↓HC-like), D=SRM-space RDM-ρ (geometry, ↑HC-like). HC reference bar + No-filter/Window/Optimal markers.

## Pipeline (scripts/)
1. `exp2_C010_conditions.py` — canonical C010 recipe (FIR→HRF GLM, per-run amplitudes),
   8 runs → condition split → **per-condition Procrustes** (each condition aligned to
   its own run-0, mirrors paper within-subject alignment). Output
   `derivatives/full_dataset_C010_exp2/sub-08/{window,optimal}/{ROI}/`.
   Mask = `masknone_gmTrue` (atlas∩GM) ∩ exp2 brain-mask coverage. All retained
   voxels are atlas∩GM (anatomical V1–hV4 gray matter) — exp2 kept ALL atlas∩GM
   (V1 858); exp1 `maskfunc` was the conservative one (560, partial occipital coverage).
2. `exp2_hc_likeness.py` — primary metric **within-condition LOCO ρ** (ridge_gcv FE-6,
   leave-one-color-out, δθ=0), vs HC exp1 distribution (run-count-matched to n=4).
   Convergent: LORO color-decoding accuracy; correlation-RDM cosine to HC-mean.

## Result (LOCO ρ, primary)

| ROI | HC(n4) | No-filter(exp1) | Window | Optimal | Opt d_vs_HC | Win d_vs_HC | Opt>NoFilter | LOO-sep |
|---|---|---|---|---|---|---|---|---|
| **V1** | 0.129 | 0.005 | −0.318 | **+0.212** | +0.97 | −5.18 | ✔ | ✔ |
| V2 | 0.162 | −0.211 | −0.190 | +0.098 | −0.47 | −2.61 | ✔ | ✔ |
| V3 | 0.053 | 0.066 | −0.320 | +0.048 | −0.02 | −1.86 | ✔ | ✔ |
| V4 | 0.208 | −0.272 | −0.388 | +0.179 | −0.16 | −3.34 | ✔ | ✔ |

- **Optimal restores HC-like hue structure** in all 4 ROIs (d_vs_HC ≈ 0; V1 reaches HC level),
  and is more HC-like than no-filter everywhere (Opt>NoFilter ✔).
- **Window does NOT** — ≈ or worse than no-filter; at V1/V3/V4 it pushes ρ strongly negative
  (actively distorts the canonical-hue forward mapping).
- **Robustness**: Optimal−Window survives dropping any single run (LOO-separated ✔ all ROIs);
  run-count matching barely moved HC (n4≈n6) so the confound is minor.
- **Dissociation (credibility)**: LORO *classification* ≈ equal (Win 0.69 ≈ Opt 0.72 ≈ HC 0.71)
  while LOCO *forward-model* strongly favors Optimal → Window preserves discriminability but
  distorts hue geometry; Optimal restores both. Consistent with "discrimination ≠ interpolation".
- **Code validated**: identical LOCO on sub-08 exp1 returns sane ~0 (not a bug) → Window's
  negativity is a real effect.

### Voxel-matched control (560-vox exp1 maskfunc; `*_matched.json`)
Re-extracting Window/Optimal on the *same* 560 voxels as the no-filter anchor confirms the
result is not a coverage artifact — though it shows V1's native strength was partly coverage-driven:

| ROI | HC(n4) | No-filter | Window | Optimal | Opt d_vs_HC | Opt>NoFilter | LOO-sep |
|---|---|---|---|---|---|---|---|
| V1 | 0.129 | 0.005 | −0.310 | +0.058 | −0.82 | ✔ | ✔ |
| V2 | 0.162 | −0.211 | −0.230 | **+0.167** | +0.04 | ✔ | ✔ |
| V3 | 0.053 | 0.066 | −0.320 | +0.045 | −0.04 | ✔ | ✔ |
| V4 | 0.208 | −0.272 | −0.388 | +0.179 | −0.16 | ✔ | ✔ |

- **Direction holds in all 4 ROIs at matched voxels**: Optimal more HC-like than both no-filter
  and Window (Opt>NoFilter ✔, LOO-separated ✔ everywhere); Window ≈/worse than no-filter everywhere.
- V1 Optimal attenuates (+0.21 native → +0.06 matched) → part of V1's native effect was the extra
  occipital coverage. V2/V4 Optimal robustly at/near HC even at matched voxels (V2 d=+0.04 = exactly HC).

## Convergent metrics (secondary) — they only PARTLY agree (`exp2_convergent.py`)

The project privileges LOCO (functional) over SRM/RDM (existence evidence, not fitting
criterion). The convergent metrics give a **more nuanced, partly divergent** picture:

**SRM Procrustes disparity into HC shared space** (K={4,4,3,3}; lower = more HC-like):

| ROI | HC | No-filter(n6) | No-filter(n4) | Window | Optimal |
|---|---|---|---|---|---|
| V1 | 0.45 | 0.55 | 0.51 | 0.82 | 0.75 |
| V2 | 0.49 | 0.72 | 0.69 | 0.81 | 0.77 |
| V3 | 0.54 | 0.74 | 0.72 | 0.91 | 0.88 |
| V4 | 0.72 | 0.88 | 0.87 | 1.00 | 0.89 |

- **Optimal < Window disparity in all ROIs** → convergent with LOCO on the Optimal>Window contrast.
- **BUT no-filter has the LOWEST disparity** — and this survives run-count matching (n4≈n6), so it is
  **not a run-count artifact**. By raw representational geometry, *any* filter moves the response
  AWAY from HC (Optimal less than Window); SRM does NOT support "filter → more HC-like than no filter".
**PAPER-CONSISTENT RDM** (corr-distance RDM computed **in SRM-aligned space**, per methods_v2 §RDM —
the paper does NOT use raw-voxel/PCA/crossnobis RDM). Two paper measures (native; HC self-consistency
Spearman in last column):

| ROI | metric | No-filter | Window | Optimal | HC |
|---|---|---|---|---|---|
| V1 | RDM-ρ to HC (↑=HC-like) | **0.667** | 0.140 | 0.240 | self 0.663 |
| V1 | mean pairwise disp (↓=HC-like) | 1.128 | 0.968 | 0.668 | 1.070 |
| V2 | RDM-ρ to HC | **0.567** | 0.110 | −0.022 | self 0.500 |
| V3 | RDM-ρ to HC | **0.269** | 0.109 | 0.170 | self 0.392 |
| V4 | RDM-ρ to HC | 0.080 | 0.114 | −0.214 | self 0.157 |

- **KEY: SRM-space RDM is RELIABLE** (HC self-consistency Spearman ρ ≈ 0.40–0.66) — unlike raw-voxel RDM
  (noise floor ~0.1, below). The SRM projection denoises the RDM, which is exactly why the paper computes
  it in SRM space. So this is the trustworthy RDM readout.
- **RDM-ρ (geometry similarity to HC): no-filter matches HC best** (ρ ≈ HC-self), **both filters disrupt
  the geometry** (Window/Optimal far lower); Optimal vs Window is mixed/weak (Opt>Win at V1/V3, Win>Opt at
  V2/V4). **Converges with SRM disparity** → geometry says no-filter closest, filters move away.
- Matched (560vox) identical pattern.

---
**Exploratory raw-voxel RDM variants (NOT the paper method) — all at noise floor** (pearson-to-HC;
HC self-consistency in parentheses; native 858vox):

| ROI | distance | No-filter | Window | Optimal | HC-self |
|---|---|---|---|---|---|
| V1 | correlation(raw) | — | — | — | ~0.1 |
| V1 | PCA | 0.08 | 0.26 | −0.32 | **0.11** |
| V1 | euclidean | 0.20 | 0.27 | 0.06 | **0.08** |
| V1 | crossnobis | 0.13 | 0.37 | 0.12 | **0.10** |
| V2 | PCA/eucl/xnob | 0.57/0.35/0.21 | 0.32/0.28/0.25 | 0.08/0.01/−0.11 | **−0.04/−0.03/−0.06** |

- **HC self-consistency r≈0.1 or below in every ROI × every distance** → the RDM readout cannot even
  tell HC from HC reliably, so it **cannot adjudicate condition HC-likeness** here.
- Crucially, **crossnobis (noise-normalized, the "best" RDM) is at the floor too** (HC-self 0.10–0.13),
  and euclidean likewise → the non-informativeness is **fundamental to the single-subject 8-color few-run
  design, NOT a distance-metric choice**. Adding crossnobis+euclidean (user request) confirmed this.
- Insofar as the (noisy) RDM values point anywhere, they do NOT favor Optimal — often Window or no-filter
  looks more HC-like. This is within noise and should not be over-read. Matched (560vox) identical pattern.

**Why LOCO and geometry (SRM/RDM) diverge — corrected interpretation (2026-06-11)**: the SRM-space RDM is *reliable here* (HC-self ρ 0.40–0.66), so geometry contradicting LOCO is **evidence, not a yardstick artifact**. (1) No-filter is geometrically closest to HC because of **stimulus identity** — no-filter and HC viewed the *same physical colors*; the filters changed them. This is the baseline the filter must beat: the design goal is that CVD cortex *under the filter* matches HC cortex *under original colors*, so success would make Optimal RDM-ρ **high**. It is not (V1 0.24, V2 −0.02, V4 −0.21 vs HC-self 0.66/0.50/0.16) → **the filter does not restore HC geometry**; rather it reshapes the configuration into one unlike both no-filter and HC and more compressed than either (V1 mean pairwise disp 0.67 vs no-filter 1.13 / HC 1.07), restoring the canonical angular ordering LOCO indexes while compressing the radial scale. (2) A session/batch confound was **downgraded**, not relied on: each subject was scanned on a *separate day* in both exp1 and exp2, so no acquisition day / head-pos / B0 is shared between no-filter and HC; only fmriprep config (unverified) and calendar scanner-block (unknown) remain — possible-minor, not the driver. The driver is stimulus identity, session-independent. (3) LOCO is the clean functional readout (within-condition leave-one-color-out self-consistency, not confounded by stimulus identity). (4) The clean contrast is **Optimal vs Window** (both exp2): LOCO strong, FE-6 LORO V1/V2, SRM disparity Opt<Win; SRM-space RDM-ρ mixed → the "restores toward HC" claim rests on LOCO (pre-registered primary), not geometry. (5) Optimal's *negative* RDM-ρ at V2/V4 and *lowest* dispersion = angular ordering restored (forward-tuning), radial scale compressed into a configuration distinct from both CVD and HC. (6) Global RDM-ρ is blunt; the pre-registered **HYPO-pair RDM (Stage-D analysis B)**, testing Opt>Win recovery only on model-predicted CVD-vulnerable pairs, is the proper geometry test and has **not been run**.

## What is and isn't supported (paper-consistent metrics: LOCO/LORO FE-6, SRM disparity, SRM-space RDM)
- **Optimal > Window** holds on **LOCO** (strong, V1 Δρ +0.53), **FE-6 LORO** (V1/V2), and **SRM disparity**
  (Opt<Win all ROIs). On the reliable **SRM-space RDM-ρ** it is mixed (Opt>Win at V1/V3, Win>Opt at V2/V4).
  → defensible as "Optimal at least as HC-like as, and on functional metrics more HC-like than, Window."
- **METRIC-DEPENDENT — filter vs NO-filter** (genuine divergence, reliable metrics both ways):
  - **Functional (LOCO, primary)**: Optimal restores canonical-hue tuning the unfiltered CVD lacks → Optimal
    more HC-like than no-filter.
  - **Geometry (SRM disparity AND paper SRM-space RDM-ρ, both reliable: HC-self 0.4–0.66)**: **no-filter is
    closest to HC**; both filters disrupt the 8-color geometry. So geometry does NOT support "filter → more
    HC-like than no filter."
  The "filter normalizes CVD toward HC" claim rests on the **functional forward-model (LOCO)**, not geometry.
- **Raw-voxel RDM (PCA/euclidean/crossnobis) is uninformative** (noise floor) — do not use; the paper's
  SRM-space RDM is the reliable one.

## Comparability audit (exp2-filtered vs existing CVD/HC values) — VERDICT: COMPARABLE-WITH-CAVEATS
(independent critic sub-agent, line-by-line, 2026-06-11)
- **GLM formula byte-for-byte identical** to canonical `run_full_dataset_C010.py` (FIR-HRF, 2nd-level
  design, drift, `lstsq` betas[:8], onset −3·TR, numpy masking). No z-scoring/normalization anywhere.
- **Procrustes is rotation-only** (`scale` returned but never applied) → amplitude magnitude preserved;
  aligning 4 vs 6 runs / different reference run does NOT change scale.
- **Every reported metric is scale-invariant** (LOCO/LORO/SRM-Frobenius-norm/correlation-RDM/crossnobis-
  whitened) OR compared via pearson/cosine of RDM vectors that cancel any global rescale (euclidean).
- Comparability rests on **metric scale-invariance, not raw amplitude identity**: exp2 uses a different
  fmriprep dir + un-normalized per-session HRF, so raw magnitudes aren't bit-identical — but this is the
  **same scale variation already present HC-subject-to-HC-subject**, which the canonical pipeline tolerates.
- **The real risk is the VOXEL SET (858 vs 560), not scale** → base all cross-source (vs-HC, vs-no-filter)
  claims on `--variant matched`; the Optimal-vs-Window contrast is voxel-clean in both variants.

## Caveats / open verifications
1. **Circularity — RESOLVED (2026-06-11, user-confirmed)**: exp2 Optimal stimuli used the
   **Phase-2-FROZEN (β_s,β_c)** (sub-08: +6,−42), NOT refit on exp2. exp2 is a new session →
   **genuine out-of-sample validation**. Phase-2 selection was RDM-based (LOCO_V4 precondition-gate
   only), so the LOCO-primary exp2 metric is also partly independent of the selection criterion.
2. **Voxel-recipe mismatch**: no-filter anchor uses exp1 maskfunc (560 vox); exp2 conditions use
   masknone∩coverage (858). Window/Optimal contrast is internally clean (same 858). To fully
   voxel-match the no-filter anchor, reprocess exp1 sub-08 with the exp2 recipe (TODO).
3. Single subject, n=4/condition (V1 minimum; rec was n=5). Descriptive only.
4. sub-09 exp2 not yet collected (re-run adding sub-09 when available).
5. SRM + v6 PCA-RDM convergent layer DONE (`exp2_convergent.py`) — see "Convergent metrics" above;
   they only partly agree (SRM: Optimal<Window yes, but no-filter best; PCA-RDM uninformative).
