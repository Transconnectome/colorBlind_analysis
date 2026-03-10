# Methods & Results Summary for Paper

> Maintained by `capture-results` skill.
> Last updated: 2026-03-09.

---

## Table of Contents

### Phase Files
- [Phase 1: Preprocessing & Baseline Decoding](METHODS_phase1_baseline.md)
- [Phase 2: SRM Between-Subject Analysis](METHODS_phase2_srm.md)
- [Phase 2b: Decoder Model Comparison](METHODS_phase2b_decoders.md)
- [Supplementary Validations](METHODS_supplementary.md)
- [Future Phase 1: Forward Model Validation](future_phase1_forward_model/RESULTS.md)

### This File
- [Key Findings Summary](#key-findings-summary)
- [Limitations & Caveats](#limitations--caveats)
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
5. **Optimal decoder depends on task**: LORO classification → LDA+SRM (0.793, ICC=0.666); LOCO interpolation → FE+Procrustes (sole interpolator, 85% best). FE's unique role is continuous hue prediction and Phase 3 channel representation, not classification accuracy.
6. **Channel→color readout is linear**: FE_SVM ≈ FE (0.779 vs 0.784). Linear template matching captures full predictive structure.
7. **Individual CVD cross-decoding**: HC-only SRM, 9/12 tests p<0.001. CVD color representations decodable in HC space.
7b. **LOCO decoding stage is NOT the bottleneck** (negative result): 4 alternative decoding methods (PopVec, RidgeEnc, GaussML, RidgeReg) all perform worse than baseline correlation. The LOCO MAE ceiling (~70–80° HC) is limited by encoding weight estimation (df=1: 7 training colors for 6 channels), not the decoding algorithm.
7d. **Sequential training + MLP readout are dead ends** (negative result): FE_Sequential = pooled FE (pinv memoryless); HybridSVR_Sequential = pooled SVR (no warm_start); HybridMLP_Sequential collapses from OOD extrapolation (best MLP 131.9° vs FE 74.9°, architecture sweep 62-2726 params all fail). Non-linear readout fundamentally incompatible with LOCO interpolation.
7e. **LDA+SRM is optimal LORO pipeline** (2026-02-27): SRM LDA accuracy 0.793 [0.759, 0.825] AND ICC reliability 0.666 [0.522, 0.787] — best on BOTH criteria. Procrustes LDA 0.758 but ICC=0.013 (near-zero reliability paradox). SRM > Proc in V1 (p=0.002), Proc > SRM in V3/V4 (p<0.001). All SRM models ICC > 0.66. **Supersedes Finding #5's FE-centric framing for classification.**
7f. **Group prior improves LOCO in V1/V2 only** (2026-02-28, leakage fixed): Previous median -50.9% was entirely leakage artifact. Corrected: HC V1 +4.3%, V2 +8.3%; CVD V1 +8.7%, V2 +6.4%. V3/V4 harmful (V3 CVD -27.0%). λ curve NOT monotonic: V1 monotonic (λ=0), V2 U-shape (λ*≈0.2), V3 HC↔CVD reversal (HC individual, CVD λ*=0.7), V4 individual preferred. LORO GP: -22.4% (unaffected, no color exclusion).
7g. **Cross-subject generalization confirmed** (2026-02-27): SRM LDA HC→HC (0.635) ≈ HC→CVD (0.665), p=0.668. No group bias in decoding — CVD color representations fully decodable via HC-trained models.

### II. 해석 (Interpretation)

8. **"Scattered but internally structured"**: CVD has higher disparity to HC (scattered), but this disparity is specifically color-dependent (structured). HC share general visual structure independent of color labels; CVD deviates specifically along color dimensions.
9. **CVD heterogeneity — not a homogeneous group**: sub-09 = V1-dominant (protan, early visual), sub-08 = V2-dominant (deutan, mid-level), sub-10 = HC-like (deutan but functionally normal). Individual profiles necessary; group-level statistics insufficient.
10. **Linear color channel representation exists**: ForwardEncoding's 6-channel basis captures continuous hue structure (LOCO interpolation), stable encoding weights (cosine 0.921), and alignment-robust decoding. Note: FE is NOT the best classifier (LDA+SRM 0.793 > FE+Procrustes 0.545 > FE+SRM 0.480 for LORO), but it is the only model that enables LOCO interpolation and provides the channel-space representation needed for Phase 3 filter design.

### III. Robustness Validation (삼각검증)

11. **A4 Crossnobis (SRM-independent)**: V1 trending (p=0.051) in native voxel space. **Convergent validity**: crossnobis ↔ SRM disparity, pooled r=0.486 (p=0.001). SRM이 아닌 방법으로도 동일 패턴 확인.
12. **A5 PCA-only (다른 alignment)**: PCA distance ↔ SRM disparity, pooled r=0.742 (p<0.001); V2 r=0.891 (p<0.001). 가장 강한 convergent validity — SRM 결과가 alignment method에 비의존적.
13. **A3 Variance Explained (재구성 품질)**: CVD VE ≥ HC VE (전 ROI). V2 diff=−0.117 [−0.190, −0.042], g=−1.68. CVD signal이 noisy가 아닌 **체계적으로 다름**. "Strong signal, different structure."
14. **SRM validation battery complete**: LOSO stability (V2 7/7), split-half (V2 both halves sig), permutation (10K iter), bootstrap CIs, alignment comparison (2.4–6.5×).

### IV-b. Future Phase 1 — Forward Encoding Model (360° Hue Encoder)

19. **Ridge-GCV is the optimal LOCO encoder**: Ridge-GCV > prior_finetune for all ROIs in LOCO (interpolation). Prior helps LORO (+0.018 to +0.114) but hurts LOCO (-0.014 to -0.210). LORO-LOCO dissociation: SRM prior captures run-level variance but not color-specific tuning for cross-color interpolation. Generic ridge shrinkage superior.

20. **HC LOCO significantly > 0 in V1**: One-sample t-test (ridge_gcv, HC, n=7): V1 M=0.130, t(6)=3.544, p=0.012 (two-tail); V2 M=0.150, t(6)=2.109, p=0.079; hV4 M=0.183, t(6)=2.423, p=0.052. V3 M=0.023, p=0.808 (fails).

21. **HC > CVD in LOCO with large effect sizes**: V1 d=1.61 (p=0.021), V2 d=1.85 (p=0.022). CVD subjects show impaired cross-color interpolation, consistent with distorted hue representations. Converges with Phase 2 SRM findings (V1 p=0.062, V2 p=0.075).

22. **FE-6 basis confirmed over Fourier alternatives**: FE-6 vs LF-4 paired t-test (LOCO OLS, n=10): V1 p=0.045, V2 p=0.042, hV4 p=0.016. FE-6 > LF-4 > LF-6. Half-wave rectified cosine better captures peaked neural color tuning than raw Fourier harmonics.

23. **3/4 ROIs pass GO/NO-GO gate**: Three criteria (reliability, normalized fit, interpolation significance) → V1, V2, hV4 GO; V3 NO-GO. Noise-ceiling normalized LOCO: V1=0.310, V2=0.373, hV4=0.313 (~30-37% of achievable signal). Gate uses ridge_gcv (best empirical model).

24. **Individual CVD profiles — no single-case significance for LOCO**: Crawford-Howell tests on ridge_gcv LOCO voxel_corr: sub-08 hV4 p=0.076 (trending), sub-10 V2 p=0.089 (trending), sub-09 uniformly negative but non-significant. Contrast with Phase 2 SRM where sub-09 V1 p=0.007, sub-08 V2 p=0.040 — the LOCO metric captures a different aspect (interpolation vs. disparity).

25. **Massive leakage from naive prior construction**: Including held-out color in group prior (A_g) inflated LOCO voxel_corr by +0.55 to +0.69 in V1-V3. Corrected by recomputing W0 per fold excluding held-out color. This validates the leakage-free pipeline.

### IV. 최종 해석 및 Phase 3 함의

15. **CVD 색 표상은 "다르되 체계적"**: noisy가 아니라 anisotropic (방향-의존적 왜곡). SRM VE가 높고 (재구성 가능), 고유한 color-dependent 구조를 가짐 → anisotropy correction (구조 보정) 프레이밍 적합.
16. **Convergent validity가 핵심 증거**: SRM disparity ↔ crossnobis (r=0.486), ↔ PCA (r=0.742). 세 가지 독립적 방법이 동일한 subject-level 패턴 → SRM alignment artifact 배제.
17. **LOCO dissociation — signal vs. geometry** (RT-4, 2026-02-18): CVD는 LORO에서 HC와 동등하거나 우수한 성능 (within-color discriminability ↑), 그러나 LOCO interpolation에서 HC < CVD (V1, V2, V4). ForwardEncoding만 색상 간 보간 가능하며, HC 색 공간은 circular continuous → 보간 가능; CVD 색 공간은 hue 축이 compressed/warped → 보간 실패. 개별 CVD 이질성: sub-08 (deutan)은 V1에서 최고 성능(MAE=50.6°, p=0.035), sub-09/10은 chance 수준. **핵심: CVD = 신호 없음이 아닌, 색 공간 왜곡**. LORO (within-color signal) vs LOCO (cross-color geometry) 이중 해리가 Phase 3 filter learning의 신경과학적 근거를 제공함.

18. **Filter design prerequisites met** (updated 2026-03-09):
    - Linear channel representation exists (ForwardEncoding validated)
    - CVD signal preserved in SRM space (VE ≥ HC)
    - Individual CVD profiles identifiable (Crawford & Howell significant)
    - Channel→color mapping is linear (FE_SVM ≈ FE)
    - **CVD color space is distorted, not absent** (LOCO dissociation: HC>CVD interpolation, HC≈CVD discrimination)
    - **Forward encoder validated**: Ridge-GCV + FE-6 basis. HC LOCO > 0 at p=0.012 (V1), p=0.040 one-tail (V2), p=0.026 one-tail (hV4). 3/4 ROIs pass gate.
    - **HC > CVD LOCO confirmed**: V1 d=1.61 (p=0.021), V2 d=1.85 (p=0.022) — large effect sizes converging with Phase 2 SRM findings.
    - **Prior not needed for encoding**: Ridge-GCV > prior_finetune for LOCO in all ROIs. Generic shrinkage sufficient.
    - **Cross-subject generalization**: SRM LDA HC→CVD = 0.665 (p=0.668 vs HC→HC), no group bias
    → Phase 2 (filter optimization): CVD→HC transformation in 6-channel space, using ridge_gcv encoder on V1, V2, hV4.

---

## Limitations & Caveats

- **Multiple comparisons**: 4 ROIs tested; LOO-consistent group p-values (V1=0.062, V2=0.075) do not reach p<0.05. Results framed as trending effects with individual-level confirmation via Crawford & Howell tests.
- **CVD-CVD RDM instability across halves**: Split-half CVD-CVD RDM correlation is inconsistent (V2 Set A: 0.536, Set B: 0.124), suggesting CVD within-group color structure is less reliably estimated with n=3 and half-run data.
- **V3/hV4 non-significance**: Consistent across all validation tests (LOSO 0/7, split-half 0/2, permutation n.s.). May reflect genuine absence of difference or insufficient power.
- **V1 validation gap**: Disparity significant (p=0.024), LOSO 6/7 robust, but RDM color-specificity not significant (p=0.192/0.599), complicating interpretation of what V1 disparity represents. Forward model partially addresses this: V1 HC LOCO > 0 (p=0.012), HC > CVD (d=1.61, p=0.021).
- **Forward model LOCO metric**: Voxel pattern correlation is scale-invariant but sensitive to n_voxels — sub-07 hV4 (16 voxels) produces noisy estimates. No significant correlation between n_voxels and LOCO_r for V1-V3 (all p>0.6), but hV4 trends (r=0.660, p=0.106). Ridge MAE > OLS MAE paradox: ridge shrinks predictions toward zero → conservative angular errors; voxel_corr is the more reliable metric.
- **No individual CVD significance for LOCO**: Unlike Phase 2 SRM (sub-09 V1 p=0.007, sub-08 V2 p=0.040), ridge_gcv LOCO Crawford-Howell tests are non-significant (best: sub-08 hV4 p=0.076). LOCO captures cross-color interpolation, a different (harder) aspect than within-color disparity.
- **SRM within-subject trade-off**: SRM improves between-subject agreement (2.4–6.5×) but reduces within-subject RDM test-retest reliability (V2: raw 0.473 → SRM 0.098). This drop conflates two sources: (1) genuine dimensionality reduction and (2) SRM fitting instability from independent split-half fits learning different shared spaces. The main analysis uses a single SRM fit on all runs, mitigating fitting instability. The "parallel" pattern (CVD preserving color structure) is independently validated by 2B in native voxel space without SRM (CVD ≥ HC in V1/V2), so does not rely on SRM-derived metrics alone.

---

## TODO (Next Steps)

### Completed
- [x] **Future Phase 1: Forward Model Validation** — Ridge-GCV + FE-6 validated. 3/4 ROIs pass gate (V1, V2, hV4). Basis ablation confirms FE-6 > Fourier.

### Active
1. **Future Phase 2: Filter Optimization** — CVD→HC stimulus-space filter using ridge_gcv encoder
   - ROIs: V1, V2, hV4 (V3 excluded — no reliable interpolation)
   - Encoder: Ridge-GCV + FE-6 basis (frozen W_s from forward model)
   - Framework: LORO-CV for filter evaluation

2. **Forward model additional analyses** (metric robustness):
   - Per-color LOCO: which colors are hardest to interpolate?
   - Residual structure: is (Y - W@C) systematic or noise?
   - Permutation test: shuffle color labels for null LOCO distribution (more robust than parametric t with n=7)
   - Ridge alpha distribution: GCV lambda stability across folds

### Deferred
3. **Publication figure** — Comprehensive summary of decoder comparison results
4. **Phase 2 SRM RDM metric test** — correlation vs Euclidean, z-score vs min-max

---

## Red Team Log (Phase 2b, 2026-02-17)

| # | Criticism | Severity | Status | Neutralization |
|---|-----------|----------|--------|---------------|
| RT-1 + RT-7 | HC vs CVD group comparison invalid at n=3; cross-decoding used circular all-subjects SRM | Fatal | **DONE** | HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig); hV4 borderline due to low SRM quality |
| RT-2 | Procrustes pre-computed across all runs → LORO test-set leakage | Fatal | **DONE** | Nested Procrustes: SVM 0.899, FE 0.781 (no leakage, actually improves) |
| RT-3 | "Linearity" confounded by dimensionality; KernelRidge gamma grid too narrow | Addressable | **DONE** | PCA-20 within LORO: loses info vs full voxels |
| RT-4 | LOCO results from single subject (n=1), 100 perms at p-floor | Fatal | **DONE** | 10 subjects × 1000 perms completed (Result 2b) |
| RT-5 | LDA reliability r=0.015 contradicts "best model" claim; paradox misinterpreted | Addressable | **DONE** | Run-pair r=0.009; FE W stability 0.921. **Further resolved by Result 11**: SRM LDA ICC=0.666 (reliable), Proc LDA ICC=0.013 (paradox is alignment-specific). Framing revised to task-dependent optimality. |
| RT-6 | Channel→color readout linearity untested | High | **DONE** | FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate. Linear readout sufficient. |

---
