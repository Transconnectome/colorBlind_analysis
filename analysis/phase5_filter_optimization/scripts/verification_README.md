# Phase B v6 PCA RDM — verification scripts (5-file suite)

Voxel-level verification of the 3 production candidates under v6 PCA 45°
categorical RDM atom, replacing the loss-function-level Method C injection
used by exp14/15/18/21/22.

Locked candidates:
- `S08-stable`  sub-08 deutan  `γALL|RDMV1|noLOCO`  (β_s=38, β_c=-10)
- `S08-robust`  sub-08 deutan  `γOY|RDMV2|noLOCO`   (β_s=6,  β_c=-42)
- `S09-primary` sub-09 protan  `γALL|RDMV1|noLOCO`  (β_s=2,  β_c=+24)

## Architecture

| # | File | Role | Runtime mode |
|---|---|---|---|
| 1 | `forward_voxel_synth.py`     | Foundation: voxel-level synth, per-HC W, noise estimation     | Module (import only) |
| 2 | `null_within_hc_loo.py`      | Source B null: B1 real HC-as-CVD, B2 synth GT=(0,0)            | Runnable (SLURM) |
| 3 | `null_label_permutation.py`  | Source C null: within-subject color-label permutation          | Runnable (SLURM) |
| 4 | `param_recovery_voxel.py`    | Stage 1: GT magnitude sweep × HC carrier × M realizations      | Runnable (SLURM) |
| 5 | `analyze_verification.py`    | Aggregation + verdict matrix + FDR                            | Runnable (local) |

## How they supplement/replace prior experiments

| Replaces | New script | Why |
|---|---|---|
| Exp 14/15 LOO null (`SUBSET_SIZE=4`) | `null_within_hc_loo.py` (`SUBSET_SIZE=5`) | Exp 14 used 4/3 split; v6 production used 5/2. Re-run mandatory for apples-to-apples specificity comparison. |
| Exp 18 Method C injection             | `forward_voxel_synth.py` + `param_recovery_voxel.py` | Method C swaps RDM rows wholesale — bypasses encoder W and ε. Voxel-level synth re-projects through HC_k's W with HC_k's residual covariance + AR(1). |
| Exp 21 forward recovery (Method C)   | `param_recovery_voxel.py`                            | Same scope (3 cands × 4 mags), but voxel-level injection. Adds frac_within_10° verdict. |
| Exp 22 origin loss specificity        | `analyze_verification.py` specificity verdict        | Now percentile-rank against voxel-level HC LOO null instead of Method C origin attractor. |
| —                                     | `null_label_permutation.py`                          | Source C was not previously implemented as standalone label-perm null. |

## Execution order

1. **Script 1** is imported by Scripts 2 and 4; no standalone run.
2. **Scripts 2 (only B2 synth path) and 4** are mutually independent — run in parallel.
3. **Script 2 B1** depends only on real data; can run alongside (2).
4. **Script 3** depends only on CVD data + HC pool; can run in parallel with (2)/(4).
5. **Script 5** (aggregation) runs locally after (2), (3), (4) write their JSONs.

## Expected compute (single CPU, conservative)

Based on Exp 21 telemetry (1 v6 fit ≈ 10–30 s for sub-08; sub-09 ~50% faster
due to fewer combos):

- Script 4 (param recovery): 3 × 4 × 7 × 20 = **1680 fits** ⇒ ≈ 5–14 h
- Script 3 (label perm): 3 × 1000 = **3000 fits** ⇒ ≈ 8–25 h (bottleneck)
- Script 2 B1: 3 × 7 = **21 fits** ⇒ minutes
- Script 2 B2: 3 × 7 × 20 = **420 fits** ⇒ 1–4 h
- Total wall-clock realistic on single CPU: **15–45 h**

**Parallelisation note**: Both runnable scripts accept `--candidates`,
`--hc-subset`/`--magnitudes`/`--perm-start`/`--perm-end` slicing so a SLURM
array (e.g. `--array=0-11`) can split across candidate × magnitude /
candidate × perm slice. On a 4-way array, total drops to ≈ 4–12 h.

## Anti-patterns the design avoids

- **σ-bin lookup at synthesis** — explicit voxel-level forward `Y = W_k @ C(θ + δθ) + ε`, no σ permutation of RDM rows.
- **CVD's own W to synthesize CVD** — synthesis always uses *donor* HC_k's W (circularity prevented). Specifically excluded in `_build_synth_fake_amps`.
- **Spectral or σ-aware injection on B1** — B1 uses raw HC amplitudes untouched; injection is real-data substitution, no synthesis.
- **KS test for N_real=1** — `analyze_verification.py` uses one-sided percentile rank, not KS.
- **Selection-rule reformulation** — verdict matrix is descriptive per project §0; not used to "select" a candidate. Specifically labelled in `verdict_matrix.md` output.
- **Reusing Exp 14 results despite `SUBSET_SIZE=4`** — task allowed reuse iff compatible; Exp 14 is not (4/3 vs production 5/2). We re-run.

## Key design decisions (and ambiguities resolved)

1. **`ROI_K` source**: Task spec says `{V1:4, V2:4, V3:3, V4:3}` but the live
   `neural_loss.ROI_K` is `{V1:6, V2:6, V3:6, V4:6}` (FE-6 uniform per
   2026-05-22 fix). v6 production used FE-6. **Resolution**: import live
   `ROI_K`; task spec values treated as outdated.

2. **Noise model parameters** (fixed module constants in `forward_voxel_synth.py`,
   echoed into every output JSON `config`):
   - `SPATIAL_COV_RANK = 20` — top-20 PCs of residual covariance (rank-safe for
     V_k > 20 voxels; auto-clamped to `min(20, n_residual_samples - 1)`).
   - `AR1_RHO = 0.3` — temporal AR(1) across runs (Schütt 2021 convention).
   - Residuals computed as `hc_amp − C_baseline @ W_k` broadcast over runs;
     centered per voxel before SVD.

3. **B1 sampling**: Single fit per HC carrier (7 fits per candidate) rather
   than internal N_RESAMPLES=300. Rationale: the donor HC is deterministic,
   so internal resampling of the 5/2 split would add variance estimate not
   distributional comparability to the real CVD. Production CVD argmin is
   median over 300, we record raw median in `s10_inclusion`; B1 raw 7 values
   form the HC null distribution for percentile rank.

4. **B2 noise realizations**: M=20 per HC carrier (420 total per candidate).
   Sufficient to estimate spread; matches scope of Exp 21's N=100 (which was
   single-HC).

5. **Permutation seed**: `RNG_SEED = 27182` for parity with Exp 14.

6. **KS vs percentile rank** (N_real=1): The 3 candidates each have ONE real
   CVD production estimate (median over 300 resamples), not a sample of N_real
   independent CVD subjects. KS would be pseudo-rigor. Percentile rank vs the
   7 HC nulls is the correct one-sided test.

7. **Specificity verdict threshold**: PASS = real CVD strictly exceeds every
   HC null on (a) β_s AND (b) Euclidean distance from origin in (β_s, β_c)
   plane. Equivalent to `rank ≤ 1/(7+1)`.

8. **FDR application**: BH at α=0.05 across 3 candidates × 3 main tests
   (identifiability, within-subject SIG, specificity) = 9 tests. Algorithm
   validation (mag=0) is a procedural diagnostic, not part of the FDR family.

9. **Production loss reference for SIG**: pulled from
   `results/s10_inclusion/s10b_v6_pca_rdm_results_{subject}.json` (median
   `train_loss` over the 300 resamples for the candidate combo). The +1
   conservative p-value formula is `(#perm_loss ≤ real + 1) / (n_perm + 1)`.

## Output files

| File | Producer |
|---|---|
| `results/redteam/null_within_hc_loo_v6_pca.json`   | Script 2 |
| `results/redteam/null_label_permutation_v6_pca.json` (or sliced `_pNNNN-MMMM.json`) | Script 3 |
| `results/redteam/param_recovery_voxel_v6_pca.json` | Script 4 |
| `results/redteam/verdict_matrix_v6_pca.json`       | Script 5 |
| `results/redteam/verdict_matrix.md`                | Script 5 |

## §0 policy compliance reminder

The verdict matrix is **descriptive only** per the project §0 rule. It is a
diagnostic for distinguishing identifiability from spurious recovery. It is
**not** a basis for re-opening filter selection or making a specificity claim
in the manuscript. See project `CLAUDE.md` §0 and §0.1.
