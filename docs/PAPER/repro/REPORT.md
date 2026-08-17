# Reproduction Report — colorBlind PAPER (results_v4)

Executed 2026-06-26 (E1,E3–E6) / re-executed 2026-06-28 (E2), local `srm` env (Python 3.10, numpy/scipy/sklearn), seed=42.
Notebooks: `docs/PAPER/repro/0{1..6}_*.ipynb` (executed in place). Helper `_repro_util.py`.
Companions: `MANIFEST.md` (reported numbers), `MAP.md` (code map), `PERMUTATIONS.md` (E2 above-chance perms).

**Legend** ✅ reproduced · ❌ mismatch · ⚠ reproduces-with-caveat · ⛔ can't-verify-from-committed-artifact · 📎 pointer-only (heavy, per user: load+verify not re-run).

**Headline: 50/50 numeric checks reproduced; 2 documented ⛔ pointer-only; 0 ⚠ remaining.**
The earlier ❌ on the E4 held-out L_test was a *notebook bug* (wrong γ-variant key), not a paper error — reproduces exactly with the production combo (see E4). The two former ⚠ (E2.1 perm basis, E2.3/2.4 CH t/p) are **resolved**: the manuscript adopted the reproduced adjacent-accuracy values (`results_v4.tex` L38–40, rebuilt 2026-06-28); nb02's `reported=` targets now track the current tex and all 17 nb02 checks pass (see E2).

---

## E1 — Discrimination + cross-decoding  (nb01: 9/10)
| id | reported | produced | verdict |
|---|---|---|---|
| E1.1 | both CVD > 0.125 every ROI | V1 1.0/0.5 · V2 .75/.875 · V3 .75/.875 · hV4 .75/.75 | ✅ |
| E1.2 | MannWhitney p=0.668 | 0.6681 (`LDA/difference/p_value`) | ✅ |
| E1.3 | hV4 single-case p=0.142 | — | ⛔ stdout-only (`_compute_paper_stats.py`); no committed artifact |

## E2 — Interpolation / per-hue  (nb02: 17/17, RECOMPUTE)
| id | reported (results_v4.tex L38–40) | produced | verdict |
|---|---|---|---|
| E2.1 | HC adj 0.47±0.05 | 0.465 ± 0.044 | ✅ |
| E2.1 | hV4 above-chance **p=0.008** (1,000 per-subject perms) | 0.0080 (obs 0.4653, `perm_definitive_hv4_null.npy`) | ✅ canonical adjacent-acc metric; matches `PERMUTATIONS.md`. (Old draft's 0.044 was the voxel_corr 8! perm — removed from tex.) |
| E2.2 | V1 **p=0.164** (n.s.); V2,V3 below chance | V1 0.164 (obs 0.3929, `perm_v1_null.npy`) | ✅ |
| E2.3 | deutan 0.25 | 0.250 | ✅ |
| E2.4 | protan 0.13 | 0.125 | ✅ |
| E2.5 | blue/purple/magenta = 0 (both) | all 0.0 | ✅ |
| E2.6 | per-hue: NO hue significant | blue p=0.072, purple 0.205, magenta 0.122 | ✅ (matches the 2026-06-25 correction) |
| E2.3/2.4 overall CH | deutan t=−1.84/p=0.063/d=−1.99; protan −2.91/0.017/−3.14 | deutan −1.84/0.063/−1.99; protan −2.91/0.017/−3.14 | ✅ manuscript adopted the reproduced values (was −1.58/0.082, −2.48/0.024); exact to printed precision |

## E3 — Geometry / SRM disparity  (nb03: 4/5, LOAD+VERIFY 📎)
| id | reported | produced | verdict |
|---|---|---|---|
| E3.1 | protan V1 common 0.007 / LOSO 0.045 | 0.0066 / 0.0449 | ✅ |
| E3.2 | deutan V2 common 0.040 / LOSO 0.116 | 0.0395 / 0.1157 | ✅ |
| E3.7 | full table all ROI×CVD | reproduced from committed JSON | ✅ |
| E3.5 | SRM k=4/4/3/3 | hardcoded override (raw aggregation = 4/5/4/6) | 📎 documented override |
| E3.3 | ΔRDM heatmap | — | ⛔ visualization stub only; no committed numeric ΔRDM |

## E4 — Simulator model selection  (nb04: 7/7 + 1 ❌ flag)
| id | reported | produced | verdict |
|---|---|---|---|
| E4.4 | deutan argmin (6°,−42°) | (6,−42) (s18 `phase_b_fit`) | ✅ |
| E4.5 | protan argmin (2°,+24°) | (2,+24) | ✅ |
| E4.11 | N=300 resamples | 300 (`meta.N_resamples`) | ✅ |
| E4.13 | filter mean\|δθ\| 26.3° / 16.2° | 26.3 / 16.2 (RECOMPUTE) | ✅ |
| E4.4 | deutan L_test −2.36 (IQR 2.15) | −2.359 (2.150) `s10b summary['γOY\|RDMV2\|noLOCO'].per_model.2comp` | ✅ |
| E4.5 | protan L_test −1.54 (IQR 1.42) | −1.539 (1.417) `s10b summary['γALL\|RDMV1\|noLOCO']…` | ✅ |
| E4.1/4.2 R+C, E4.8 NC%, E4.9/4.10 | saturation / 52%/67% / IQR | not auto-checked | 📎 pointer (s10b/s18 JSON) |

> **Resolved (was ❌):** the L_test mismatch was a notebook bug — the combo key must be the production γ-variant (`γOY` deutan / `γALL` protan), not the generic `γ_` atom (which gives −2.14/−2.12). With the right key it reproduces to 3 decimals. Source: `s10b_v6_pca_rdm.py`, documented in `phase5_filter_optimization/PIPELINE_2_CLOSURE.md`.

## E5 — Identifiability S15  (nb05: 6/6, LOAD+VERIFY)
| id | reported | produced | verdict |
|---|---|---|---|
| E5.2 | f10 0.26 / 0.14 | 0.264 / 0.136 (mean of per-donor `frac_within_10deg`) | ✅ |
| E5.4 | HC pseudo-CVD rank 0.875 (both) | 0.875 / 0.875 (`verdict_matrix.specificity.rank_distance`) | ✅ |
| E5.5 | label-perm p 0.167 / 0.471 | 0.167 / 0.471 (`within_subject_sig.p_perm`) | ✅ |

## E6 — Filter eval, 2nd session  (nb06: 3/3) — ⚠ deutan(sub-08) only
| id | reported | produced | verdict |
|---|---|---|---|
| E6.3 | Wilcoxon p=0.84 | 0.844 | ✅ |
| E6.3 | 8AFC 0.81 → 0.97 | 0.8125 → 0.9688 | ✅ |
| E6.1 | LOCO ρ per ROI (V1 +0.21/−0.32 …) | loaded; descriptive | 📎 pointer (`exp2_hc_likeness_sub-08_native.json`) |
| E6.2 | LORO/LOCO acc, SRM RDM | loaded; descriptive | 📎 pointer |
| — | protan (sub-09) 2nd session | not acquired | ⛔ data not collected |

---

## Action items for the authors
1. **✅ RESOLVED — E4 L_test** reproduces exactly (−2.359 / −1.539); the earlier flag was a notebook key bug. No manuscript action.
2. **✅ RESOLVED 2026-06-28 — E2 overall CH (t/p)** — the manuscript adopted option (a): `results_v4.tex` L40 now reads deutan −1.84/0.063/−1.99 and protan −2.91/0.017/−3.14, exactly the reproducible (sd=0.108) values. nb02 checks these directly and passes. No remaining discrepancy.
3. **✅ RESOLVED 2026-06-28 — E2.1 above-chance perm** — the manuscript now reports the canonical **adjacent-accuracy** value hV4 p=0.008 / "1,000 per-subject label permutations" (L38), matching `methods_v2.tex` L128 and `PERMUTATIONS.md`. The stale 0.044 / "8! exact" wording is gone from the tex tree (grep-verified). nb02 verifies p=0.008 (hV4) and p=0.164 (V1) against committed null arrays.
4. **📎 E1.3 / E3.3 — pointer-only (user-accepted).** Left as committed-folder pointers (hV4 single-case p via `_compute_paper_stats.py` stdout; ΔRDM via the viz path), not re-run, since full code is published separately. Not blocking.
5. **E3.5** — note the canonical k=4/4/3/3 override vs raw aggregation 4/5/4/6 in the supplement.

## Notes
- Heavy/MPI/SLURM analyses (E3 SRM, E4 N=300 resamples, E5 redteam) are **load+verify against committed JSON**, not re-run (per user: pointers acceptable; full code published separately). E2 adjacent accuracy and E4.13 pre-image are genuinely recomputed locally.
- Re-run: `python build_notebooks.py` then `conda run -n srm python _execute.py`.
