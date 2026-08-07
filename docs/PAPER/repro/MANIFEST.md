# Reproduction Manifest — colorBlind PAPER (results_v4)

Authoritative source: `docs/PAPER/main.tex` → `Results/results_v4.tex`, `Methods/methods_v2.tex`, `Supplementary/supplementary.tex`, `Supplementary/S3_identifiability.tex` (S15), `Figures/FIGURE_CAPTIONS.md`.
Order: document order (Results §1→§9). Split by experiment. Precision = as printed.
Env: local `conda activate srm`, Python 3.10 (numpy 1.24.3, scipy 1.11.3, sklearn 1.3.0, BrainIAK 0.11), seed=42.

Legend output type: STAT / TABLE / FIG / PROC(procedural threshold).

---

## E1 — Discrimination preserved + cross-decoding null (Results §1, Fig 2A, S14)

| id | section | reported value | type |
|---|---|---|---|
| E1.1 | R§1 | Both CVD exceed exact-acc chance 0.125 at every ROI (V1–hV4), 8-class LORO | STAT/FIG |
| E1.2 | R§1 | Cross-subject generalization HC→HC vs HC→CVD: Mann–Whitney U, 21 vs 14 pairs, **p = 0.668** | STAT |
| E1.3 | R§1 | Within-ROI hV4 single-case (Crawford–Howell), both CVD within HC range, **p = 0.142** | STAT |

## E2 — Interpolation impaired / vulnerability profile (Results §2, Fig 2B–C, Fig 3)

| id | section | reported value | type |
|---|---|---|---|
| E2.1 | R§2 | hV4 HC adjacent accuracy **0.47 ± 0.05** (mean±SEM, n=6, sub-07 excluded); above chance **p = 0.008** (1,000 per-subject label perms) | STAT |
| E2.2 | R§2 | V1 **p = 0.164** (n.s.); V2, V3 below chance (discrimination preserved) | STAT |
| E2.3 | R§2 | deutan adjacent **0.25** (CH t = −1.84, p = 0.063, n.s., d_cc = −1.99) | STAT |
| E2.4 | R§2 | protan adjacent **0.13** (CH t = −2.91, p = 0.017, d_cc = −3.14) | STAT |
| E2.5 | R§2 | per-hue profile v∈[0,1]^8; both CVD **zero** adjacent acc at blue, purple, magenta | STAT/FIG |
| E2.6 | R§2 / Fig3 cap | per-hue CH (1-tailed, uncorrected, exploratory): **significance at NO individual hue** [CORRECTED 2026-06-25; was blue d=2.20 p=0.042] | STAT |
| E2.7 | (canon config) | adjacent acc config = **FE-6 uniform basis + OLS decoder**, adjacent_deg=45°, via `loco_canonical.loco_forward_readouts` | PROC |

## E3 — Geometry distorted at distinct ROI / SRM disparity (Results §3, Fig 4)

| id | section | reported value | type |
|---|---|---|---|
| E3.1 | R§3 | protan elevated disparity **V1**: common-space **p = 0.007**; symmetric LOSO **p = 0.045**; none at V2/V3/hV4 | STAT/TABLE |
| E3.2 | R§3 | deutan elevated disparity **V2**: common-space **p = 0.040**; LOSO trend **p = 0.116**; none at V1/V3/hV4 | STAT/TABLE |
| E3.3 | R§3 | ΔRDM = RDM_CVD − mean(RDM_HC); deutan S-cone-intermediate elevation at V2; protan broad reorg at V1 | FIG |
| E3.4 | M§rdm | RDM = 8×8 correlation distance (1−Pearson r); disparity = mean of 28 upper-tri; HC ref via LOO; CH 1-tailed upper, df=6 | PROC |
| E3.5 | M§srm | SRM dims: V1 k=4, V2 k=4, V3 k=3, hV4 k=3 (mean-rank LOSO over 3 metrics) | PROC |
| E3.6 | supp | d_cc = t·√(8/7), n=7 (disparity table) | PROC |
| E3.7 | tab:disparity_loso | FULL table (both estimators, all ROI): **deutan** V1 t=1.10/p=0.157/d=1.18 (LOSO 0.48/0.323), **V2 t=2.11/p=0.040/d=2.26 (LOSO 1.33/0.116)**, V3 t=1.92/p=0.052/d=2.05 (LOSO 1.17/0.143), hV4 t=0.23/p=0.411 (LOSO 0.07/0.474); **protan** **V1 t=3.48/p=0.007/d=3.72 (LOSO 2.02/0.045)**, V2 t=0.99/p=0.181 (LOSO 0.77/0.234), V3 t=0.09/p=0.466, hV4 t=1.13/p=0.150 (LOSO 0.80/0.228) | TABLE |

## E4 — Simulator model selection (Results §4–6, Methods selection; Table modelfits)

| id | section | reported value | type |
|---|---|---|---|
| E4.1 | R§4 | R+C deutan: **⟨100%⟩** resample grid-boundary saturation (g=3.0) → rejected (>50% gate) | STAT |
| E4.2 | R§4 | R+C protan: **⟨41%⟩** saturation, g=2.95; dominated on held-out loss (L_test = −0.86 vs 2-comp −1.54) | STAT |
| E4.3 | R§4 | Ishihara: deutan 5/14, protan 7/14 plates correct | STAT |
| E4.4 | R§5 | deutan 2-comp: loss combo **γ_OY + L_RDM^(V2)** → (β̂_s,β̂_c) = **(6°, −42°)**; L_test = **−2.36** (IQR 2.15); competitor (38°,−10°) L_test=−1.14; HC-resample param IQR (8°,2°); 7-fold LOO β̂_c range **[−46°,−38°]** (all neg) | STAT |
| E4.5 | R§5 | protan 2-comp: combo **γ_all + L_RDM^(V1)** → (β̂_s,β̂_c) = **(2°, +24°)**; L_test = **−1.54** (IQR 1.42); nearest competitor −1.52; HC-resample IQR (0°,0°), **⟨87.7%⟩** same 45° bin; 7-fold LOO IQR (0°,0°); argmin shifts under SRM-basis | STAT |
| E4.6 | R§5 | LOCO loss family entered NEITHER winning combo (both JND+ΔRDM) | STAT |
| E4.7 | R§5 | RDM atom ROI = elevated-disparity ROI (V2 deutan p=0.040; V1 protan p=0.007) | STAT |
| E4.8 | R§5 | both fits beat no-correction baseline on all 7 folds; top 5–8% of grid combos; noise-ceiling reached **52%** (deutan), **67%** (protan) | STAT |
| E4.9 | R§6 | protan behavioral-only fit β̂_c≈+4°, ΔL=+0.01, 3/7 folds (no beat); deutan behavioral-only & combined share argmin (6°,−42°); neural-only β̂_c=−26° | STAT |
| E4.10 | R§6 | deutan: adding RDM cut boundary saturation **23% → 9.3%**; IQR (18°,6°)→(8°,2°) PCA, (10°,4°) SRM; protan IQR (6°,4°)→(0°,0°) PCA, (0°,2°) SRM | STAT |
| E4.11 | M§sel | 3-gate: G1 admit if signed Cohen's **d ≥ +0.5** vs HC LOO; G2 reject if **≥50%** boundary saturation; G3 median held-out L_test (N=⟨300⟩ 5-train/2-test) then IQR | PROC |
| E4.12 | M§grid | grid (β_s,β_c)∈[−90,90]² @2° = **8,281 cells**; β_s≥0; R+C g∈[0,3] | PROC |
| E4.13 | R§8/Fig7 | filter mean |δθ|: deutan **26.3°**, protan **16.2°**; 8/8 pre-images exact, residual <0.01° (Results) / **<0.001°** (Methods L246, captions — authoritative) | STAT |
| E4.14 | supp S13 | HC LOO ‖β̂‖ range: deutan loss 30.5°–58.1° (mean 49.1°), protan loss 23.4°–55.5° (mean 35.7°); CVD ‖β̂‖ = deutan 42.4°, protan 24.1° (both within HC range) | STAT |

## E5 — Identifiability (Results §7, S15)

| id | section | reported value | type |
|---|---|---|---|
| E5.1 | S15 | FDR BH α=0.05 over 6 tests (2 cand × 3): **0/6 significant** | STAT |
| E5.2 | S15 T1 | voxel param recovery f_10°: S08-robust **0.26** (bias +16°,−4.7°); S09-primary **0.14** (bias +11°,−27°); both FAIL (<0.5) | TABLE |
| E5.3 | S15 T2a | origin-null: S08 |β_s|med 22°(40)/|β_c|med 26°(10.5)/p95 44°/f_origin **0.00**; S09 16°(17.5)/24°(9)/48°/**0.00**; uncertainty ~20°(β_s) ~25°(β_c) | TABLE |
| E5.4 | S15 T2b | HC pseudo-CVD rank_dist: both **0.875** FAIL | TABLE |
| E5.5 | S15 T2c | label-perm p: S08 **0.167** (real −2.892, cut −3.136); S09 **0.471** (real −1.681, cut −3.053) | TABLE |
| E5.6 | R§7 | dominant axis β̂_c recovery bias **4.7°** (deutan); non-dominant |β̂_s|≤6° not recoverable | STAT |

## E6 — Filter evaluation, 2nd session (Results §8–9, Fig 8) — INCLUDED
**⚠ DEPENDENCY: deutan (sub-08) only collected. protan (sub-09) 2nd session NOT YET acquired.**
E6 notebook = deutan-only now; protan cells stubbed/parameterized, to fill when sub-09 data arrives. Mark every E6 number as single-case deutan, descriptive.

| id | section | reported value | type |
|---|---|---|---|
| E6.1 | R§8 Neural | LOCO ρ personalized vs deployed: V1 +0.21/−0.32, V2 +0.10/−0.19, V3 +0.05/−0.32, V4 +0.18/−0.39; Δρ 0.37–0.57; voxel-matched d: V2 +0.04, V1 +0.97→−0.82 | STAT |
| E6.2 | R§9 | LORO 8-way ≈0.69–0.72 at V1 (HC 0.71, chance 0.125); LOCO V1 adj 0.41 (HC 0.40), exact 0.34 (HC 0.28); deployed V1 adj 0.22 (chance 0.375) | STAT |
| E6.3 | R§9 Behav | JND |z|: baseline 2.24 → deployed 0.85 / personalized 0.78; 8AFC 0.81→0.97 both; Wilcoxon p=0.84 | STAT |

---

## Pre-flags (honesty)
1. **E2.6 corrected**: draft's "blue d=2.20 p=0.042 significant" removed 2026-06-25 — contamination from SRM V2 (d=2.20) + V2 blue-purple (p=0.042); real per-hue CH n.s. (blue |d|=1.87 p=0.072).
2. **E2.1 / E2.3 / E2.4 — RESOLVED 2026-06-28**: an earlier draft reported hV4 p=0.044 (voxel_corr 8! perm) and CH −1.58/0.082 & −2.48/0.024. The manuscript (`results_v4.tex` L38–40, rebuilt 2026-06-28) has since **adopted the reproduced adjacent-accuracy values** — hV4 p=0.008 (1,000 per-subj perms), V1 p=0.164, deutan −1.84/0.063/−1.99, protan −2.91/0.017/−3.14. The `reported=` targets above and in nb02 now track the current tex; all reproduce exactly. The old numbers no longer appear anywhere in the tex tree (grep-verified).
3. **No committed driver** produces per-hue adjacent accuracy (E2.5–E2.7) — only `loco_canonical` library fn; regen script is de facto driver.
4. **E1.2 / E3.1–E3.2 / E4 / E5 source folders**: span phase3_decoder_comparing (E1.2), phase2_SRM_across_between + phase2_procrustes_cvd_hc (E3), future_phase2_filter_optimization (E4, E5) — to be mapped in Phase 2.
5. `N=⟨300⟩` printed with literal `\langle\rangle` placeholder brackets in tex — confirm final N at Phase 2 (E4.11, E5).

## Verifier reconciliation (paper-analyst, 2026-06-26)
- **FIXED**: S14 table `tab:effect_sizes` (supplementary_content.tex L233–235) per-hue rows had STALE blue d=2.20/p=0.042 etc. — corrected to regen values (blue −1.87/0.072, purple −0.97/0.205, magenta −1.43/0.122), caption updated. This was the 4th location of the same Gate-1 error (after results_v4 L40/L52, FIGURE_CAPTIONS L18).
- **FIXED**: `FIGURE_CAPTIONS.md` Fig 2A "28 vs 12 pairs" → "**21 vs 14**" (L14 + changelog L90), matching Results/Methods/S14.
- **FIXED**: residual tolerance `results_v4.tex` L175 "<0.01°" → "**<0.001°**", matching Methods L246 + captions.
- **Added in-scope**: E3.7 (full disparity table), E4.14 (S13 anchor magnitudes).
- **OUT of repro scope (user-confirmed 2026-06-26)**: descriptive Methods facts / QC supplements NOT reproduced — demographics (N=13, age 22.7±2.5), ROI voxel counts, S2 coverage 84.3%, S3 activation QC, S5 cross-subject RDM corr. Notebooks cover computational analyses E1–E6 only.
- **E6 INCLUDED (user-confirmed)** but deutan-only until sub-09 2nd session collected — see E6 block.
