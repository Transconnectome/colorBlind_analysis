# Phase B v6 PCA RDM — Verification verdict matrix

_Generated: 2026-05-31T17:55:04.106682Z_

| Candidate | Identifiability | Within-subj SIG | Specificity vs HC | Algorithm validation | FDR-sig (BH α=0.05) |
|---|---|---|---|---|---|
| **S08-stable** | FAIL (f10=0.05, bias=(-6.0,19.0)) | FAIL (p_perm=0.8661338661338661, n=1000) | FAIL (rank_dist=0.5) | FAIL (median@GT0=(None,None)) | ident={'p_value_proxy': 0.95, 'BH_significant': False}, sig={'p_value_proxy': 0.8661338661338661, 'BH_significant': False}, spec={'p_value_proxy': 0.5, 'BH_significant': False} |
| **S08-robust** | FAIL (f10=0.2, bias=(16.0,-4.0)) | FAIL (p_perm=0.16683316683316685, n=1000) | FAIL (rank_dist=0.875) | FAIL (median@GT0=(None,None)) | ident={'p_value_proxy': 0.8, 'BH_significant': False}, sig={'p_value_proxy': 0.16683316683316685, 'BH_significant': False}, spec={'p_value_proxy': 0.875, 'BH_significant': False} |
| **S09-primary** | FAIL (f10=0.15, bias=(11.0,-27.0)) | FAIL (p_perm=0.47052947052947053, n=1000) | FAIL (rank_dist=0.875) | FAIL (median@GT0=(None,None)) | ident={'p_value_proxy': 0.85, 'BH_significant': False}, sig={'p_value_proxy': 0.47052947052947053, 'BH_significant': False}, spec={'p_value_proxy': 0.875, 'BH_significant': False} |

## Notes
- Identifiability uses param_recovery_voxel @ mag=1.0; PASS = frac_within_10° ≥ 0.5 AND |bias|<10° both axes.
- Within-subject SIG uses null_label_permutation with the production loss median as the real reference.
- Specificity uses null_within_hc_loo B1 (real HC as fake CVD); PASS = real CVD exceeds every HC null on β_s AND distance from origin (one-sided high, percentile rank).
- Algorithm validation uses param_recovery_voxel @ mag=0.0; PASS = |bias|<5° in both axes.
- FDR (Benjamini-Hochberg) is applied across 3 candidates × 3 main tests (identifiability, sig, specificity) = 9 tests at α=0.05.

## §0 framework reminder
Specificity result is **descriptive only** per project §0; the verdict matrix is a diagnostic, not a selection criterion.
