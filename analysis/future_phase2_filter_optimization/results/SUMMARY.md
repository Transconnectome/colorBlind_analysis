# Phase 2 Filter Optimization — Summary

**Date**: 2026-05-17 (Phase 2 closure)
**Previous version**: `_archive/cleanup_2026-05-17/SUMMARY_pre_2026-05-17.md` (Option C era, OLD label scheme)

---

## Current Best Filter (Phase 2 closure)

| Subject | (β_s, β_c) | norm | perm_p | corrected P2a | exact | Etiology (R+C diagnostic) |
|---|---|---:|---:|---:|---:|---|
| **sub-08 deutan** | (38°, −14°) | 40.5° | **0.004** | **0.750** | 2/8 | Cortical-dominant (Δλ=2.5 nm, g=−2.25) |
| **sub-09 protan** | (6°, −22°) | 22.8° | **0.035** | **0.975** | 7/8 | Retinal-dominant (Δλ=19.5 nm, g=−1.10, near-physiological) |

**Loss form**: `L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth` (`loco_distortion_fit.py:200`) @ V4 hV4 LOCO
**Filter form**: 2-component standalone `δθ = β_s·cos(h_base − 90°) + β_c·cos(h_base − axis°)`
**Pre-image**: 8/8 exact for both subjects

Viz: `c3_relabel/CORRECTED_LOCO_canonical_4col_sub-{08,09}.{png,pdf}`

---

## Independent CVD-HC Signal Anchor (NOT in loss)

V4 cross-color correlation matrix cosine to HC pool — **Bonferroni-passed for both subjects**:
- sub-08: p=0.007 ★★
- sub-09: p=0.010 ★
- sub-10 (normal control): not significant ✓

This is the only group-level statistical test that passes. Paper anchor for "V4 carries CVD signal." Independent of loss formulation.

---

## Key Framework Decisions (logged 2026-05-16 / 2026-05-17)

### 1. P2a as post-hoc consistency check (§0.1, REVISED 2026-05-17)
- **Not paper-reportable** as primary endpoint (circular — same data used for fit + validation)
- Used internally as binary screen: P2a ≥ identity → PRIMARY candidate; below identity → CONTROL
- All candidates (PRIMARY + CONTROL) presented in pre-registered behavioral test; asymmetric prediction is paper claim
- Independent paper validation requires NEW behavioral acquisition (pre-registered)

### 2. Statistical criteria reframe (CLAUDE.md §0.2)
- (2a) **Label permutation perm_p**: per-subject fit quality only (NOT CVD vs HC)
- (2b) **V4 cc-matrix Bonf-pass**: independent CVD vs HC anchor (loss외 evidence)
- (2c) **HC LOO descriptive percentile**: context only, no p-value claim
- Strict specificity NOT validated under HC FPR=100% — descriptive only per §0

### 3. R+C decomposition: diagnostic only (advisor reversal 2026-05-16)
- R+C 2-stage as filter form: **rejected** (Check 4 empirical falsification; P2a 0.588/0.787 < 2-comp standalone 0.750/0.975)
- R+C decomposition retained as paper finding: "differential mechanism per subject (sub-08 cortical, sub-09 retinal)"
- Filter form: 2-comp standalone (LOCO-canonical)

### 4. Phase 2 closure
- Option C (40,+26)/(12,−28) — adopted 2026-05-13 under OLD labels — **deprecated 2026-05-17**
  - Corrected-label P2a is 0.500 (sub-08, worst zone cell) / 0.887 (sub-09, below identity)
- LOCO-canonical adopted as final Phase 2 filter

---

## Next Steps (Phase 3 trigger)

1. **OSF pre-registration** (30-50 lines, prospective): freeze pipeline + behavioral acquisition protocol before subject session
2. **Independent behavioral test**: filter (PRIMARY: LOCO-canonical) vs sham vs Control candidates vs no-filter, per-color naming accuracy
3. **Subject acquisition for replication**: ≥1 additional deutan + ≥1 additional protan (within-category)
4. **Paper draft**: framework structure per `c3_relabel/SCIENTIFIC_NARRATIVE_2026-05-16.md`
   - Headline: cortical-vs-retinal etiology dissociation
   - R+C as diagnostic, 2-comp as filter form
   - Acknowledged limits: N=2, HC FPR, descriptive-only

---

## Files retained (results/ root)

- `BEST_summary.json` — canonical filter parameters
- `MANIFEST.md` — directory navigation
- `SUMMARY.md` — this file
- `landscapes_consolidated.parquet` (2.75 MB) — 30 landscape JSONs consolidated
- `phase_a_summary.csv` (14 KB) — 70 phase-A fit summaries
- `smooth_sweep_summary.csv` (6 KB) — 40 epsilon sweep summaries
- `CONSOLIDATION_REPORT_2026-05-16.md` — consolidation methodology
- `LABEL_CLEANUP_PLAN_2026-05-16.md` — OLD-label cleanup record

## Files archived (2026-05-17 cleanup)

To `_archive/cleanup_2026-05-17/`:
- 28 outdated docs (LIT2Neural_*, P2AMAX_*, LITERATURE_*, NOTEBOOKLM_*, ANALYSIS_C_DETAILED, CLEANUP_PROPOSAL, REVALIDATION_BRETTEL_CRITIQUE, BEST_summary_PREVIOUS_bayesian, hc_optC_*, sub08_bc_*, server_bootstrap_*)
- Previous `MANIFEST.md`, `SUMMARY.md`, `BEST_summary.json` (Option C era)

To `c3_relabel/_archive_2026-05-17/`:
- 30 intermediate Track A/B exploration files (LOSS_REVISION_REPORT.md, RELABEL_FINDINGS.md, TRACK_A_*, TRACK_B_*, intermediate JSONs)

## Caveats (per CLAUDE.md §0)

- All filter selection is descriptive — specificity claims forbidden under HC FPR=100%
- Behavioral validation requires pre-registered independent acquisition (TO BE COLLECTED)
- Paper claims should reframe "framework" → "proof-of-concept methodology" (N=2 limit)
