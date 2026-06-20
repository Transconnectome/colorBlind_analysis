# SRM interpolation: structural gain vs dimensionality reduction?

**Exploratory test (read-only on existing results). Not production. Not for paper without replication.**
Date: 2026-06-13. HC group (sub-01..07; sub-07 excluded at hV4 → n=6 there, n=7 elsewhere).

## Question

Does the SRM-aligned (HC shared) space give CVD-relevant **interpolation** an advantage because it
has a genuinely more *circular / ring-like* hue geometry — or is any SRM interpolation benefit just
**dimensionality reduction / denoising** that a plain PCA-to-the-same-k of the Procrustes space would
also give?

## Design (all three representations run through the identical LOCO harness)

Decoder fixed: **B&H 2009 forward encoding, alpha=0 (pseudoinverse), FE n_channels=6.** LOCO =
leave-one-color-out, train pooled (6 runs × 7 colors = 42), decode per held-out run (6 predictions),
adjacent accuracy = fraction within ±45° (chance 3/8 = 0.375), MAE in degrees. This exactly
replicates `phase2_decoder_comparing/.../loco_baseline.py:loco_cv` + `LOCOForwardEncodingDecoder`.

| Rep | What | k |
|---|---|---|
| `procrustes` | `amplitudes_procrustes.npy` as-is (full voxels) | full V |
| `pca` | **Transductive** PCA on the full 48×V Procrustes matrix (centered within subject), top-k scores → (6,8,k) | V1=4,V2=4,V3=3,hV4=3 |
| `srm` | `amplitudes_srm.npy` (canonical HC-only shared space, on-disk k) | V1=4,V2=4,V3=3,hV4=3 |

**Why transductive PCA (not per-fold).** The saved SRM and Procrustes arrays were both fit on the full
8 colors (transductive). Fitting PCA per-fold (train-colors-only) would hold PCA to a *stricter*
leakage standard than SRM, and any "SRM>PCA" could be pure leakage asymmetry rather than geometry.
PCA is therefore fit on the full 48×V matrix so all three reps share "transform fit on full data,
decoder LOCO'd." On-disk SRM k confirmed = (V1 4, V2 4, V3 3, hV4 3) → PCA k is exactly matched.

**Harness validity check (passed).** Replicated `loco_cv` on `amplitudes_srm.npy` reproduces the
canonical SRM LOCO json to 4 decimals: sub-01 V1 0.2292/91.875, V2 0.375/85.375, V3 0.2083/110.979,
hV4 0.5833/61.917. So Procrustes/PCA numbers below are produced by the same validated harness.

## Circular-structure metrics (on the 8 color-mean patterns)

- `rdm_circ` — Spearman(1−corr RDM upper-tri, |circular hue-distance| model). Higher = more circular. **Chance = 0.**
- `order_pres` — 1 − (circular-order inversions / 8) of the 8 hues in the top-2 PC plane. **Chance ≈ 0.29.**
- `nn_adj` — fraction of hues whose nearest neighbor (1−corr) is a ±1 circular hue neighbor. **Chance ≈ 2/7 ≈ 0.29.**
- `pc2_var` — variance fraction in top-2 PCs. **Reported only, NOT a verdict metric** (mechanically inflated for low-k reps).

## Results — HC group mean

| rep | ROI | n | adj_acc | MAE | rdm_circ | order_pres | nn_adj | pc2_var |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| procrustes | V1 | 7 | 0.393 | 76.4 | −0.008 | 0.23 | 0.32 | 0.59 |
| pca | V1 | 7 | **0.429** | 74.5 | −0.003 | 0.29 | 0.21 | 0.86 |
| srm | V1 | 7 | 0.360 | 80.0 | −0.215 | 0.27 | 0.09 | 0.76 |
| procrustes | V2 | 7 | 0.357 | 80.0 | 0.044 | 0.27 | 0.41 | 0.58 |
| pca | V2 | 7 | 0.360 | 76.5 | −0.006 | 0.39 | 0.32 | 0.86 |
| srm | V2 | 7 | 0.283 | 84.9 | −0.008 | 0.27 | 0.43 | 0.73 |
| procrustes | V3 | 7 | 0.339 | 76.9 | 0.049 | 0.34 | 0.34 | 0.61 |
| pca | V3 | 7 | 0.345 | 79.7 | 0.045 | 0.27 | 0.20 | 0.90 |
| srm | V3 | 7 | 0.220 | 99.3 | −0.054 | 0.29 | 0.30 | 0.86 |
| **procrustes** | **hV4** | 6 | 0.465 | **68.6** | −0.004 | 0.29 | 0.33 | 0.71 |
| **pca** | **hV4** | 6 | 0.382 | 74.4 | 0.023 | 0.33 | 0.19 | 0.92 |
| **srm** | **hV4** | 6 | **0.490** | 71.2 | −0.162 | 0.31 | 0.17 | 0.90 |

hV4 = primary ROI. Bold marks the best interpolation cell per ROI / the lowest MAE at hV4.

### Per-subject robustness at hV4 (n=6)

- **SRM > PCA on adjacent accuracy: 6/6 subjects** (MAE better in 4/6). The +0.108 adj_acc gap is consistent, not driven by one subject.
- **SRM > raw Procrustes: only 2/6** on adj_acc and 2/6 on MAE. So SRM ≈ raw Procrustes at hV4; PCA *underperforms* raw Procrustes (0.382 < 0.465), and SRM merely recovers to ~Procrustes level.

## Verdict (two decoupled answers)

**1. Circular-structure hypothesis: REJECTED at every ROI.** SRM is never the most circular
representation. At hV4 it is the *worst* on `rdm_circ` (−0.162) and `nn_adj` (0.17). There is **no
SRM-specific circular-geometry gain** in the 8-color means.

Caveat (important): *no* representation shows clearly above-chance circular structure — `rdm_circ`
hovers around 0 (chance), `order_pres` and `nn_adj` straddle their ~0.29 chance levels. With only 8
points these metrics are underpowered, so this is "no detectable circular-geometry advantage for SRM,"
not "proof that the underlying geometry is non-circular."

**2. Interpolation-beyond-PCA: YES, but only at hV4, and NOT via circular structure.**
At matched k=3, SRM beats PCA on hV4 interpolation (adj_acc 0.490 vs 0.382, 6/6 subjects). Crucially,
generic dim-reduction (PCA) *hurts* hV4 interpolation relative to raw voxels, while SRM does not — so
whatever SRM adds beyond PCA is not "dimensionality reduction." But (a) the structural metrics show the
mechanism is **not** the circular geometry this test measures, and (b) SRM does **not** exceed raw
Procrustes voxels (2/6), so the honest framing is: *PCA discards interpolation-relevant signal that SRM
(via cross-subject alignment to a shared basis) retains; SRM ≈ full-voxel Procrustes, not better.*

**Bottom line for the original question** — *"Is SRM's interpolation benefit a genuine circular-geometry
gain, or just dim-reduction/denoising PCA would also give?"*: **Neither.** It is not a circular-geometry
gain (rejected), and it is not reducible to dim-reduction (SRM > PCA at hV4, 6/6). The plausible mechanism
is cross-subject **alignment/denoising** that preserves interpolation-relevant structure PCA loses — a
geometry this 8-point circularity test does not capture.

## Caveats

- **n** = 7 (V1–V3), 6 at hV4 (sub-07 hV4 ~16 voxels excluded). Small; per-subject counts reported instead of inferential p-values.
- **Structural metrics on 8 points are low-power** — all reps near chance; treat structure conclusions as "no detectable advantage," not absence of structure.
- **SRM structural metric used the actual saved SRM-projected patterns** (`amplitudes_srm.npy`), not just the existing LOCO numbers — so structure and interpolation are on the same patterns.
- **SRM leakage ≥ PCA leakage.** Canonical SRM shared space is HC-group-trained *including the target subject itself* (`training_subjects` lists sub-01..07) and uses all 8 colors; transductive PCA is within-subject + all 8 colors. So the hV4 SRM>PCA edge is an **upper bound** — a cleaner symmetric-inductive (per-fold) design could shrink it. Re-running SRM differently was out of scope (no-retrain constraint).
- **adj/MAE tension at hV4:** raw Procrustes has the lowest MAE (68.6) while SRM leads adjacent accuracy (0.490) — reported both; not cherry-picked.
- **pc2_var is not a verdict metric** — it rises monotonically as k shrinks (procrustes 0.59–0.71 < pca/srm 0.73–0.92) purely from dimensionality, exactly the artifact the order/RDM metrics avoid.

## Exact commands run on the server

```bash
# all via: ssh -o ConnectTimeout=25 haba6030@node3
source /usr/anaconda3/etc/profile.d/conda.sh && conda activate base   # node3 has only base; numpy 1.17.2, scipy 1.3.1
cd /scratch/connectome/haba6030/colorBlind/analysis/phase_supplementary
python srm_interp_structure_test.py   # main: validation + table -> srm_interp_structure_raw.json
python srm_followup.py                # per-subject hV4 win counts + on-disk SRM k confirm
```

Scripts and raw output live in `phase_supplementary/`:
`srm_interp_structure_test.py`, `srm_followup.py`, `srm_interp_structure_raw.json`.
