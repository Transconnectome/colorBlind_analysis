# Methods & Results Summary for Paper

> Maintained by `capture-results` skill.
> Last updated: 2026-02-26. Reorganized into per-phase files.

---

## Table of Contents

### Phase Files
- [Phase 1: Preprocessing & Baseline Decoding](METHODS_phase1_baseline.md)
- [Phase 2: SRM Between-Subject Analysis](METHODS_phase2_srm.md)
- [Phase 2b: Decoder Model Comparison](METHODS_phase2b_decoders.md)
- [Supplementary Validations](METHODS_supplementary.md)

### This File
- [Key Findings Summary](#key-findings-summary)
- [Limitations & Caveats](#limitations--caveats)
- [Pending Validations](#pending-validations)
- [TODO (Next Steps)](#todo-next-steps)
- [Red Team Log](#red-team-log)

---

## Key Findings Summary

### I. 핵심 결과 (Core Findings)

**Phase 1 — Preprocessing**:
1. **C010 + Procrustes is the optimal pipeline**: +1644% RDM reliability (0.028→0.487); ceiling utilization ~30%; whitening harmful (−47~92%).

**Phase 2 — SRM Group Comparison**:
2. **V1/V2에서 trending HC-CVD 차이**: V1 p=0.062 (g=1.16), V2 p=0.075 (g=1.04). V2 separation CI [0.001, 0.244] marginally excludes zero.
3. **Individual CVD dissociations**: sub-09 (protan) V1 p=0.007; sub-08 (deutan) V2 p=0.040; sub-10 HC range.
4. **CVD color-dependency confirmed (LOSO)**: CVD disparity is color-specific (V2 p=0.010, V3 p=0.000, hV4 p=0.016), HC is not (p=0.21–0.36). Asymmetry = strongest evidence.

**Phase 2b — Decoder Validation**:
5. **ForwardEncoding is the optimal decoder**: 78.1% acc_45, highest reliability (r=0.329), only LOCO interpolation (V3 p<0.01), most alignment-robust (Δ=+0.045).
6. **Channel→color readout is linear**: FE_SVM ≈ FE (0.779 vs 0.784). Linear template matching captures full predictive structure.
7. **Individual CVD cross-decoding**: HC-only SRM, 9/12 tests p<0.001. CVD color representations decodable in HC space.
7b. **LOCO decoding stage is NOT the bottleneck** (negative result): 4 alternative decoding methods (PopVec, RidgeEnc, GaussML, RidgeReg) all perform worse than baseline correlation. The LOCO MAE ceiling (~70–80° HC) is limited by encoding weight estimation (df=1: 7 training colors for 6 channels), not the decoding algorithm.
7d. **Sequential training + MLP readout are dead ends** (negative result): FE_Sequential = pooled FE (pinv memoryless); HybridSVR_Sequential = pooled SVR (no warm_start); HybridMLP_Sequential collapses from OOD extrapolation (best MLP 131.9° vs FE 74.9°, architecture sweep 62-2726 params all fail). Non-linear readout fundamentally incompatible with LOCO interpolation.

### II. 해석 (Interpretation)

8. **"Scattered but internally structured"**: CVD has higher disparity to HC (scattered), but this disparity is specifically color-dependent (structured). HC share general visual structure independent of color labels; CVD deviates specifically along color dimensions.
9. **CVD heterogeneity — not a homogeneous group**: sub-09 = V1-dominant (protan, early visual), sub-08 = V2-dominant (deutan, mid-level), sub-10 = HC-like (deutan but functionally normal). Individual profiles necessary; group-level statistics insufficient.
10. **Linear color channel representation exists**: ForwardEncoding's 6-channel basis captures continuous hue structure (LOCO interpolation), stable encoding weights (cosine 0.921), and alignment-robust decoding. → Phase 3 filter design on channel space justified.

### III. Robustness Validation (삼각검증)

11. **A4 Crossnobis (SRM-independent)**: V1 trending (p=0.051) in native voxel space. **Convergent validity**: crossnobis ↔ SRM disparity, pooled r=0.486 (p=0.001). SRM이 아닌 방법으로도 동일 패턴 확인.
12. **A5 PCA-only (다른 alignment)**: PCA distance ↔ SRM disparity, pooled r=0.742 (p<0.001); V2 r=0.891 (p<0.001). 가장 강한 convergent validity — SRM 결과가 alignment method에 비의존적.
13. **A3 Variance Explained (재구성 품질)**: CVD VE ≥ HC VE (전 ROI). V2 diff=−0.117 [−0.190, −0.042], g=−1.68. CVD signal이 noisy가 아닌 **체계적으로 다름**. "Strong signal, different structure."
14. **SRM validation battery complete**: LOSO stability (V2 7/7), split-half (V2 both halves sig), permutation (10K iter), bootstrap CIs, alignment comparison (2.4–6.5×).

### IV. 최종 해석 및 Phase 3 함의

15. **CVD 색 표상은 "다르되 체계적"**: noisy가 아니라 anisotropic (방향-의존적 왜곡). SRM VE가 높고 (재구성 가능), 고유한 color-dependent 구조를 가짐 → anisotropy correction (구조 보정) 프레이밍 적합.
16. **Convergent validity가 핵심 증거**: SRM disparity ↔ crossnobis (r=0.486), ↔ PCA (r=0.742). 세 가지 독립적 방법이 동일한 subject-level 패턴 → SRM alignment artifact 배제.
17. **LOCO dissociation — signal vs. geometry** (RT-4, 2026-02-18): CVD는 LORO에서 HC와 동등하거나 우수한 성능 (within-color discriminability ↑), 그러나 LOCO interpolation에서 HC < CVD (V1, V2, V4). ForwardEncoding만 색상 간 보간 가능하며, HC 색 공간은 circular continuous → 보간 가능; CVD 색 공간은 hue 축이 compressed/warped → 보간 실패. 개별 CVD 이질성: sub-08 (deutan)은 V1에서 최고 성능(MAE=50.6°, p=0.035), sub-09/10은 chance 수준. **핵심: CVD = 신호 없음이 아닌, 색 공간 왜곡**. LORO (within-color signal) vs LOCO (cross-color geometry) 이중 해리가 Phase 3 filter learning의 신경과학적 근거를 제공함.

18. **Filter design prerequisites met**:
    - Linear channel representation exists (ForwardEncoding validated)
    - CVD signal preserved in SRM space (VE ≥ HC)
    - Individual CVD profiles identifiable (Crawford & Howell significant)
    - Channel→color mapping is linear (FE_SVM ≈ FE)
    - **CVD color space is distorted, not absent** (LOCO dissociation: HC>CVD interpolation, HC≈CVD discrimination)
    → Phase 3: CVD→HC transformation in 6-channel space로 진행 가능.

---

## Limitations & Caveats

- **Small CVD sample (n=3)**: Group-level comparisons should be interpreted with caution. Individual CVD profiles are reported alongside group descriptive statistics. Effect sizes may be inflated due to small sample.
- **Multiple comparisons**: 4 ROIs tested; LOO-consistent group p-values (V1=0.062, V2=0.075) do not reach p<0.05. Results framed as trending effects with individual-level confirmation via Crawford & Howell tests.
- **No parametric group tests with n=3**: Permutation-based p-values and Hedges' g (small-sample corrected) used instead of parametric t-tests, which would violate normality assumptions.
- ~~**95% CIs not yet computed**~~: Resolved 2026-02-18 — Bootstrap 95% CIs computed for all disparity and RDM comparisons (10,000 iterations).
- **SRM disparity metric bias for majority group**: HC subjects (7/10) dominate SRM training, creating a "floor effect" on HC-to-reference disparity. HC LOO disparity is insensitive to color-label shuffling (single-SRM: V2 p=0.894), reflecting the structural floor from SRM training. **Resolved via LOSO analysis**: When HC is tested in a space they did NOT train (projected via SVD, same as CVD), HC disparity remains color-agnostic (p=0.21–0.36), confirming this is genuine rather than artifact. Meanwhile, CVD color-dependency remains significant under LOSO (V2 p=0.010, V3 p=0.000, hV4 p=0.016), providing the informative test for color-specific group differences.
- **CVD-CVD RDM instability across halves**: Split-half CVD-CVD RDM correlation is inconsistent (V2 Set A: 0.536, Set B: 0.124), suggesting CVD within-group color structure is less reliably estimated with n=3 and half-run data.
- **CVD individual stability moderate**: Run-split corrected reliability 8/12 moderate or better; sub-08 most stable, sub-09/sub-10 lower in V1/V2.
- **V3/hV4 non-significance**: Consistent across all validation tests (LOSO 0/7, split-half 0/2, permutation n.s.). May reflect genuine absence of difference or insufficient power.
- **V1 validation gap**: Disparity significant (p=0.024), LOSO 6/7 robust, but RDM color-specificity not significant (p=0.192/0.599), complicating interpretation of what V1 disparity represents.
- **CVD subtype mixing**: 2 deutan (sub-08, sub-10) + 1 protan (sub-09), precluding subtype-specific analysis. Notably, sub-09 (protan) shows the highest V1 disparity (+91%), while the two deutan subjects differ markedly (sub-08: consistent elevation vs sub-10: near-normal).
- ~~**SRM k-value**~~: Validated via 2C LOSO CV + mean rank aggregation (2026-02-18) — V1=4, V2=4, V3=3, hV4=3 (hV4 revised from k=4 to k=3).
- ~~**sub-01 noise ceiling**~~: Resolved 2026-02-17 — re-run with N=40.
- **SRM within-subject trade-off**: SRM improves between-subject agreement (2.4–6.5×) but reduces within-subject RDM test-retest reliability (V2: raw 0.473 → SRM 0.098). This drop conflates two sources: (1) genuine dimensionality reduction and (2) SRM fitting instability from independent split-half fits learning different shared spaces. The main analysis uses a single SRM fit on all runs, mitigating fitting instability. The "parallel" pattern (CVD preserving color structure) is independently validated by 2B in native voxel space without SRM (CVD ≥ HC in V1/V2), so does not rely on SRM-derived metrics alone.

---

## Pending Validations

### 1. Preprocessing Pipeline (→ Finding 1: C010+Procrustes optimal)

| Test | Status | Result |
|------|--------|--------|
| ~~Noise ceiling with sub-01~~ | **DONE** | Re-run 2026-02-17, N=39 valid (sub-07 hV4 excluded) |
| ~~Drift method comparison~~ | **PASSED** | 1st+2nd and 2nd-only identical HRF |
| ~~Onset randomization~~ | **DROPPED** | Fixed ISI; timing jitter not applicable |

### 2. SRM Group Difference (→ Findings 2–4: HC-CVD trending difference, individual CVD dissociations)

| Test | Status | Result |
|------|--------|--------|
| ~~1D: Permutation test~~ | **DONE** | V1 p=0.014, V2 p=0.036; V3/hV4 n.s. |
| ~~1D-ext LOO permutation re-run~~ | **DONE** | LOO-consistent analysis (rerun_loo_consistent.py); CVD color-dependency confirmed V2/V3/hV4 |
| ~~1D-ext-LOSO color-dependency~~ | **DONE** | HC color p=0.21–0.36 (n.s.); CVD color V2 p=0.010, V3 p=0.000, hV4 p=0.016; asymmetry confirmed |
| ~~Bootstrap 95% CIs (SRM disparity)~~ | **DONE** | V1/V2 separation CIs exclude zero; RDM CIs all ROI-group pairs (10,000 iter) |

### 3. SRM Reliability & Configuration (→ Findings 2–4 robustness)

| Test | Status | Result |
|------|--------|--------|
| ~~2A: Run-split ICC~~ | **DONE** | Mean r=0.475 (moderate) |
| ~~1B: LOSO stability~~ | **DONE** | V2 7/7 sig, V1 6/7 sig — no single subject drives results |
| ~~1C: Split-half reliability~~ | **DONE** | V2 both halves sig; cross-half r=0.71–0.78 for V1/V2/hV4 |
| ~~2B: RDM consistency~~ | **DONE** | CVD >= HC in V1/V2 — "parallel" confirmed |
| ~~2C: k-value selection~~ | **DONE** | V1=4, V3=3 confirmed; V2/hV4 competitive at k=3–4 |
| ~~Formal k aggregation~~ | **DONE** | V1=4, V2=4, V3=3, hV4=3 (hV4 revised from 4→3 via mean rank) |
| ~~2D: Alignment comparison~~ | **DONE** | SRM 2.4–6.5× over raw/Procrustes |

### 4. Convergent Validity — Triangulation (→ Findings 11–14, 16: SRM-independent confirmation)

| Test | Status | Result |
|------|--------|--------|
| ~~A3 Variance Explained~~ | **DONE** | CVD VE ≥ HC; V2 g=−1.68 [−4.02, −0.74] (CI excludes zero) |
| ~~A4 Crossnobis RDM~~ | **DONE** | V1 trending p=0.051; convergent r_pooled=0.486 (p=0.001) |
| ~~A5 PCA-CCA Replication~~ | **DONE** | PCA-only r_pooled=0.742 (p<0.001); PCA-CCA r_pooled=0.472 (p=0.002) |

### 5. Decoder Model Selection (→ Findings 5–6: FE optimal, linear readout sufficient)

| Test | Status | Result |
|------|--------|--------|
| ~~LORO model comparison~~ | **DONE** | LDA best (82.1%); linear > non-linear; HC ≈ CVD |
| ~~Bootstrap 95% CIs (decoder)~~ | **DONE** | All models except MLP CI lower > chance |
| ~~[RT-2] Nested Procrustes in LORO~~ | **DONE** | Nested improves: SVM 0.899, FE 0.781. No leakage. |
| ~~[RT-3] PCA within LORO~~ | **DONE** | PCA-20 loses info (SVM 0.847 vs 0.899 full). Signal spans >20 dims. |
| ~~[RT-5] LDA reliability analysis~~ | **DONE** | Run-pair r=0.009 explains paradox. FE W stability 0.921. |
| ~~Hybrid decoder (FE+MLP, FE+SVM)~~ | **DONE** | FE_SVM ≈ FE (0.779 vs 0.784); linear readout sufficient |

### 6. LOCO Interpolation & CVD Cross-Decoding (→ Findings 7, 10, 17–18: FE interpolation, CVD color space distortion)

| Test | Status | Result |
|------|--------|--------|
| ~~LOCO local test~~ | **DONE** | ForwardEnc only model with interpolation; V3 sig |
| ~~[RT-4] LOCO server deployment~~ | **DONE** | FE sole interpolator all ROIs; CVD heterogeneity = color space distortion (HC>CVD V1/V2/V4) |
| ~~[RT-1] Individual cross-decoding~~ | **DONE** | 12/12 tests p<0.05. All CVD decode in SRM space individually. |
| ~~LOCO results consolidation~~ | **DONE** | Group-level LOCO analysis completed; Crawford & Howell tests added |

### 7. Decoder Improvement Attempts — Negative Results (→ Findings 7b, 7d: decoding/encoding bottleneck)

| Test | Status | Result |
|------|--------|--------|
| ~~LOCO decoder improvement~~ | **DONE (negative)** | 4 alt. methods all worse than baseline FE. Correlation decoding confirmed optimal. |
| ~~LOCO ensemble improvement~~ | **DONE (partial)** | Per-run ensemble (alpha=0) improves V1 HC by −8.3°; Ridge/GaussML still harmful. |
| ~~Ensemble rollout: LOCO (all alignments)~~ | **DONE** | FE baseline confirmed across raw/procrustes/SRM. Non-linear models all worse. |
| ~~Sequential training (MLP/SVR/FE)~~ | **DONE (negative)** | FE/SVR = pooled. MLP: OOD collapse (131.9° vs FE 74.9°). Direction terminated. |
| ~~Dimensionality reduction + LOCO~~ | Superseded | Covered by ensemble rollout across alignments |

### 8. Phase 3 — Remaining

| Test | Status | Priority | Why needed |
|------|--------|----------|------------|
| **Filter pre-diagnosis** | Not started | **High** | Pair-level permutation test, LORO CV for filter, low-rank constraint, baseline comparison (filter_design_plan.md Criticism #4) |

---

## TODO (Next Steps)

### Immediate — Remaining

1. **Phase 3 Filter Implementation** — Begin CVD-to-HC filter in SRM/channel space
   - Prerequisites met: B1-B3 pre-validation done, ForwardEncoding confirmed optimal
   - LORO-CV framework for filter evaluation (filter_design_plan.md Criticism #4)

2. **Phase 3 RDM Metric & Normalization Test** — Validate metric choice before filter
   - Compare correlation vs Euclidean distance; z-score vs min-max normalization

### Completed Red Team Fixes

4. ~~**[RT-2] Nested Procrustes within LORO**~~ — **DONE** (2026-02-18). Nested Procrustes actually improves: SVM 0.899, FE 0.781. No leakage issue — original result was conservative.
5. ~~**[RT-3] PCA within LORO**~~ — **DONE** (2026-02-18). PCA-20 loses discriminative information vs full voxels. Signal spans >20 dimensions.
6. ~~**[RT-1 + RT-7] Individual CVD cross-decoding**~~ — **DONE** (2026-02-18). HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig). hV4 borderline (low SRM quality). Supersedes old all-subjects 12/12.
7. ~~**[RT-5] LDA reliability analysis**~~ — **DONE** (2026-02-18). Run-pair r=0.009 explains paradox; FE W stability 0.921; framing revised to FE-centric.
8. ~~**Bootstrap 95% CIs for SRM disparity**~~ — **DONE** (2026-02-18).
9. ~~**Formal k aggregation**~~ — **DONE** (2026-02-18). hV4 revised from k=4 to k=3.
10. ~~**[RT-6] Hybrid decoder (FE+MLP, FE+SVM)**~~ — **DONE** (2026-02-18). FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate; linear readout confirmed.

### Deferred (Low Priority)

10. **Dimensionality reduction + LOCO re-experiment** — SRM (k=3,4) + LOCO
11. **Cross-subject generalization (train HC → test CVD)** — Requires common space
12. **Publication figure** — Comprehensive summary of decoder comparison results

---

## Red Team Log (Phase 2b, 2026-02-17)

| # | Criticism | Severity | Status | Neutralization |
|---|-----------|----------|--------|---------------|
| RT-1 + RT-7 | HC vs CVD group comparison invalid at n=3; cross-decoding used circular all-subjects SRM | Fatal | **DONE** | HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig); hV4 borderline due to low SRM quality |
| RT-2 | Procrustes pre-computed across all runs → LORO test-set leakage | Fatal | **DONE** | Nested Procrustes: SVM 0.899, FE 0.781 (no leakage, actually improves) |
| RT-3 | "Linearity" confounded by dimensionality; KernelRidge gamma grid too narrow | Addressable | **DONE** | PCA-20 within LORO: loses info vs full voxels |
| RT-4 | LOCO results from single subject (n=1), 100 perms at p-floor | Fatal | **Submitted** | Server: 10 subjects × 1000 perms, 6h time limit |
| RT-5 | LDA reliability r=0.015 contradicts "best model" claim; paradox misinterpreted | Addressable | **DONE** | Run-pair r=0.009; FE W stability 0.921; framing revised to FE-centric |
| RT-6 | Channel→color readout linearity untested | High | **DONE** | FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate. Linear readout sufficient. |

---
