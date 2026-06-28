# LOCO adjacent-accuracy above-chance permutations (per ROI)

> Canonical record for the PAPER Fig 3 / §"interpolation reduced at hV4" above-chance test.
> Created 2026-06-27. This is the single source of truth for the per-ROI adjacent-accuracy
> permutation p-values; cite from `results_v4.tex` and `REPORT.md` (E2.1).

## What this tests

For each ROI, is HC group-mean **adjacent accuracy** (±1 hue step) above the
uniform-random chance level (3/8 = 0.375)? Only hV4 is expected to support
above-chance hue interpolation (Brouwer & Heeger 2009).

## Canonical config (MUST match to reproduce)

| Item | Value |
|---|---|
| Basis | FE-6 **uniform** (Phase-1 baseline; `create_basis_matrix(..., K=6, "fe")`) |
| Decoder | **OLS** pseudoinverse (`loco_canonical.loco_forward_readouts(..., decoder="ols")`) — NOT ridge_gcv |
| Metric | adjacent accuracy, mean over 6 runs per held-out color, then mean over colors |
| Permutation | **per-subject independent** color-label permutation (`rng.permutation(8)` per HC subject each draw) — matches committed `permutation_test_loco.py` |
| p-value | add-one, `(#{null>=obs}+1)/(N+1)` (Phipson & Smyth 2010) |
| N | 1,000 |
| Seed | `np.random.RandomState(42)` |
| HC set | hV4: sub-01..06 (**sub-07 excluded**, low voxels) → n=6. V1–V3: sub-01..07 → n=7 |
| Input | `…/full_dataset_C010_with_residuals/sub-{ID}/V4/amplitudes_procrustes.npy` (hV4 dir = `V4` on disk) |

## Results

| ROI | observed adj-acc | null mean | p (N=1000) | verdict |
|---|---|---|---|---|
| **hV4** | **0.4653** | 0.347 | **0.0080** | ✅ above chance |
| V1 | 0.3929 | 0.3464 | **0.164** | n.s. (point est. marginally > 0.375 but not significant) |
| V2 | 0.357 | — | not tested | observed **< chance** → not above-chance by inspection |
| V3 | 0.339 | — | not tested | observed **< chance** → not above-chance by inspection |

## Reproduce

```bash
conda run -n srm python docs/PAPER/repro/_perm_definitive_hv4.py   # hV4 → perm_definitive_hv4_null.npy
conda run -n srm python docs/PAPER/repro/_perm_v1.py               # V1  → perm_v1_null.npy
```

- Null arrays: `perm_definitive_hv4_null.npy`, `perm_v1_null.npy`.
- Logs: `_perm_def_hv4.log`, `_perm_v1.log`.

## Manuscript reconciliation (RESOLVED 2026-06-28)

- An earlier `results_v4.tex` L38 stated **"p = 0.044 under 8! = 40,320 exact label permutations."**
  That 0.044 was the committed **voxel_corr** metric permutation, not the adjacent-accuracy metric the
  sentence describes. The canonical adjacent-accuracy value is **hV4 p = 0.008, N = 1,000 per-subject perms**.
- `methods_v2.tex` L122 already says **"1,000 random … permutations"** → consistent with this run, not with "8! exact".
- **RESOLVED**: L38 now reads `p = 0.008` / "1,000 per-subject label permutations" for hV4.
  V1 permutation complete: observed 0.3929, **p = 0.164** (n.s.), null_mean 0.3464. V1 point estimate sits
  just above chance but is not significant; V2/V3 below chance. L38 wording finalized as
  **"V1–V3 did not significantly exceed chance"** (V1 p=0.164; V2, V3 below chance).
