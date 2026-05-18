# JSON → Parquet/CSV Consolidation Report (2026-05-16)

**Trigger**: User request 2026-05-16 — "json file들이 너무 많으면 csv로 통합해서 관리하는 게 어떨까요"

## Outputs

| File | Format | Size | Source |
|---|---|---|---|
| `results/landscapes_consolidated.parquet` | parquet (snappy) | 2.75 MB | 30 landscape JSONs (45,070 rows × 46 cols) |
| `results/phase_a_summary.csv` | CSV | 13.9 KB | 70 phase-A fit JSONs (subject × ROI × model) |
| `results/smooth_sweep_summary.csv` | CSV | 6.0 KB | 40 smooth-sweep JSONs (subject × ROI × ε) |

**Total reduction**: 26.55 MB JSON landscapes → 2.75 MB parquet (**89.7% saved**).
                     24.36 MB summary JSONs → 19.9 KB CSV (**99.9% saved** — much of this was already in landscapes; actual phase_a summary size ~200 KB).

## What was consolidated

### Landscape parquet schema

One row per `(subject × roi × variant × bs × bc)` cell:

```
source_file       subject roi  variant  bs bc
delta_theta_c1..c8   (8 cols, per-color δθ — flattened from 8-vec)
vuln_sim_c1..c8      (8 cols, per-color simulated vuln)
l_fit, l_vuln, l_rank, l_rdm, l_smooth, l_ccc, l_topk, l_pearson  (loss terms; NaN if absent)
spearman_r, pearson_r, ccc, rdm_cosine    (fit metrics)
sim_mean, sim_std, obs_mean, obs_std       (descriptives)
L_combined, tikh                          (combined loss + Tikh regularizer)
```

Loss formulations vary across variants — fields are NaN where not computed.

### Variants available (30 landscapes total)

| Subject | ROI | Variants |
|---|---|---|
| 08 | V1 | simplified |
| 08 | V4 | 4term, CIELab175p7, Stockman150, V1demeaned, V2pearson, V3rankw02, V3rankw03, V4CCC_SRMRDM, V4ccc, simplified, wfixed |
| 09 | V4 | 4term, CIELab11p8, CIELab11p8ext, Stockman16, Stockman16ext, V1demeaned, V2pearson, V3rankw02, V3rankw03, V4CCC_SRMRDM, V4ccc, axis150_fine, simplified, wfixed |
| 10 | V4 | 4term, wfixed |

### Phase-A summary CSV columns

```
source_file, subject, roi, model_class
best_bs, best_bc, perm_p, spearman_r, pearson_r, rdm_cosine
l_fit, l_vuln, l_rank, l_rdm, l_smooth, l_vuln_raw, l_rank_raw
method, n_evaluations, elapsed_s
```

70 rows covering subject × ROI × model class (machado_1way, rc_opponent, 2component, fourier_warp, etc.).

## Helper module

`scripts/landscape_loader.py` — drop-in replacement for `c3_alternative_losses.load_landscape`:

```python
from landscape_loader import load_landscape_pq, list_variants

# Old per-file JSON load:
# grid = load_landscape(ROOT / 'results/old_formula/sub-08_V4_V4ccc_landscape.json')

# New parquet-backed:
grid = load_landscape_pq(subject='08', roi='V4', variant='V4ccc')
```

`list_variants()` returns all available (subject, roi, variant) combos.

Returns same dict-of-2D-grids format as the original `load_landscape`, so downstream code (`argmin_global`, `argmin_combined`) needs no changes once the load call is swapped.

## What was NOT consolidated (kept as JSON)

| Type | Reason |
|---|---|
| Pre-image JSONs (`fits/preimage/*.json`, ~10 files) | Nested arrays of varying length (design_matrices, residuals, fourier_approx) — CSV/parquet would inflate, not reduce |
| Diagnostic summaries (`hc_baseline_rho_summary.json`, `hc_specificity_summary.json`, `profile_likelihood_ci_summary.json`, etc.) | Unique per-file schemas; semantic unit-per-file |
| `BEST_summary.json`, `MANIFEST.md`, `SUMMARY.md` | Active configuration; not tabular |
| c3_relabel result JSONs (`p2a_corrected_labels.json`, etc.) | Mixed schemas (bin defs + top P2a cells + summary) |
| `step2c_manifest.json`, similar manifests | Run metadata, semantic |

## Migration status (c3 chain)

**Current**: Original landscape JSONs still in place (`results/old_formula/`, `results/axis_3way/`, `results/CANDIDATE/tier2_v4ccc_srm_rdm/`). NEW c3 chain (`c3_alternative_losses.py`, `c3_loss_to_p2amax.py`, `c3_relabel_p2a.py`) still reads JSONs directly.

**Recommended next step (not done — requires testing)**: 
1. Replace `from c3_alternative_losses import load_landscape` calls with `from landscape_loader import load_landscape_pq` in c3 scripts.
2. Replace hardcoded path lookups (`sub08['axis_3way']`, etc.) with `load_landscape_pq('08', 'V4', 'Stockman150')`.
3. Run end-to-end verification (`p2a_corrected(38, -14, 150.0, SUB08_ORIG_NEW)` should still return `0.750` for sub-08).
4. After verification, archive original landscape JSONs to `_archive/old_labels_pre_2026-05-16/landscape_jsons_consolidated_to_parquet/`.

Until step 3 passes, **do not archive the original JSONs** — that would break the live c3 chain.

## Scripts written

- `scripts/consolidate_landscapes_to_parquet.py` — landscape → parquet builder
- `scripts/consolidate_phase_a_to_csv.py` — phase-A summary + smooth sweep → CSVs
- `scripts/landscape_loader.py` — parquet read helper (drop-in)

All idempotent; can re-run any time to refresh consolidated files from current JSONs.
