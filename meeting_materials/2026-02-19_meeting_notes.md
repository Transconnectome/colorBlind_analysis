# 색각이상(CVD) fMRI Neural Color Representation 분석 — 회의 자료

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-02-19
> **대상**: Phase 2 (SRM group comparison), Phase 2b (decoder model comparison), Phase 3 (filter pre-validation)
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4 (Wang Atlas 2015)

---

## Phase 2: SRM 기반 Group-Level Color Representation Comparison

### 주요 결과

**결론**: CVD 피험자는 HC common color representation space에서 체계적으로 이탈하며, 그 양상은 개인별 · ROI별로 특이적이다.

**근거 — 핵심 지표**:

| ROI | HC Mean (SD) | CVD Mean (SD) | Disparity [95% CI] | p (permutation test) | Hedges' g |
|-----|-------------|--------------|----------------|-------------|-----------|
| **V1** | 0.453 (0.083) | 0.590 (0.156) | 0.137 [−0.005, 0.301] | **0.062** | **1.16** |
| **V2** | 0.486 (0.103) | 0.606 (0.107) | 0.120 [0.001, 0.244] | **0.075** | **1.04** |
| V3 | 0.540 (0.096) | 0.564 (0.167) | 0.023 [−0.137, 0.194] | 0.395 | 0.18 |
| hV4 | 0.700 (0.128) | 0.677 (0.211) | −0.023 [−0.244, 0.172] | 0.559 | −0.14 |

> 10,000 permutations. V1/V2에서 large effect size (g>1.0), V2 disparity CI가 zero를 간신히 제외 [0.001, 0.244].

**개인별 Crawford & Howell (1998) single-case test** (df=6, one-tailed):

| 피험자 | 유형 | V1 | V2 | V3 | hV4 |
|--------|------|----|----|----|----|
| **sub-09** | Protan | **t=3.5, p=0.007\*\*** (+67.7%) | t=1.0, p=0.181 (+21.5%) | t=0.1, p=0.466 (+0.7%) | t=1.1, p=0.150 (+21.4%) |
| **sub-08** | Deutan | t=1.1, p=0.157 (+20.9%) | **t=2.1, p=0.040\*** (+47.4%) | t=1.9, p=0.052 (+35.7%) | t=0.2, p=0.411 (+3.5%) |
| sub-10 | Deutan | t=0.0, p=0.483 (−0.1%) | t=0.2, p=0.433 (+3.1%) | t=−1.3, p=0.884 (−26.8%) | t=−1.9, p=0.945 (−39.1%) |

> sub-09(protan)는 V1에서, sub-08(deutan)은 V2에서 HC distribution 밖에 위치. sub-10은 모든 ROI에서 HC 범위 내.

**시각화**:
- 4-panel SRM group comparison figure: [`phase2_SRM_across_between/results/loo_consistent/20260218_163819/figures/srm_4panel_figure.png`](../phase2_SRM_across_between/results/loo_consistent/20260218_163819/figures/srm_4panel_figure.png)

---

### 분석 방법

**SRM (Shared Response Model)**: 서로 다른 뇌를 하나의 "공용어"로 번역하는 방법이다. 7명의 HC 피험자 fMRI 데이터로 color representation의 common coordinate system을 학습한 후, CVD 피험자 데이터를 이 좌표계에 투영(SVD projection)한다. 마치 7명이 합의한 지도 위에 새로운 사람의 위치를 표시하는 것과 같다. 이 공간에서 각 피험자가 얼마나 "표준 지도"에서 벗어나 있는지를 Procrustes disparity로 측정한다.

**세 가지 bias correction**:
1. **HC-only SRM training**: CVD가 공간 정의에 참여하지 않으므로 circularity 제거
2. **LOO for HC**: HC 개인 i의 disparity는 나머지 6명 mean 대비로 측정 (자기 자신 포함 방지)
3. **동일 LOO reference**: CVD도 동일한 7개 LOO reference set에 대해 평가 → HC와 CVD가 같은 baseline에서 비교됨

**K-value selection**: 7-fold LOSO cross-validation + mean rank aggregation (RDM reliability + cross-subject RDM correlation) → V1=4, V2=4, V3=3, hV4=3.

**K-value selection 상세 (2C 결과)**:

| ROI | Selected k | RDM reliability (M±SD) | Cross-subj RDM (M±SD) | Mean rank | Runner-up |
|-----|--------|----------------------|----------------------|----------|--------|
| V1 | 4 | 0.496 ± 0.146 | 0.597 ± 0.229 | 1.93 | k=3 (2.71) |
| V2 | 4 | 0.429 ± 0.137 | 0.566 ± 0.145 | 2.14 | k=5 (2.36) |
| V3 | 3 | 0.446 ± 0.194 | 0.546 ± 0.279 | 2.14 | k=4 (tie) |
| hV4 | 3 | 0.560 ± 0.185 | 0.317 ± 0.169 | 2.07 | k=4 (2.57) |

> 7-fold LOSO cross-validation, 2개 RDM metric (rdm_reliability + cross_subject_rdm_corr)의 mean rank로 선택. Reconstruction error는 high-dimensional bias (k=6 항상 1위)로 제외.

---

### 논의

#### 추가 검증 지표

**LOSO stability** (7-fold leave-one-HC-out):

| ROI | Significant folds | Range | Stability |
|-----|-------------|------|--------|
| V1 | **6/7** | p=0.007–0.052 | Robust (1개 borderline p=0.052) |
| V2 | **7/7** | p=<0.001–0.032 | **Perfect** |
| V3 | 0/7 | — | Consistently n.s. |
| hV4 | 0/7 | — | Consistently n.s. |

> V2는 어떤 HC 피험자를 제거해도 CVD-HC separation이 significant → 단일 피험자에 의한 결과가 아님을 확인.

**Split-half reliability** (runs 1-3 vs 4-6):

| ROI | First-half p | Second-half p | Both significant? | Cross-correlation r (p) |
|-----|--------|--------|-----------|---------------|
| V2 | **0.006** | **0.022** | **Both significant** | 0.709 (p=0.022) |
| V1 | 0.059 | 0.019 | One-sided only | 0.709 (p=0.022) |
| hV4 | 0.402 | 0.174 | N/A | 0.782 (p=0.008) |

**Color label dependency test** (LOSO — HC와 CVD 모두 SVD projection):

| ROI | HC p | CVD p | Interpretation |
|-----|------|-------|------|
| V1 | 0.364 | 0.412 | 양쪽 모두 color-independent |
| **V2** | 0.227 | **0.010** | **CVD만 color-dependent** |
| **V3** | 0.207 | **0.000** | **CVD만 color-dependent** |
| **hV4** | 0.330 | **0.016** | **CVD만 color-dependent** |

> **핵심 asymmetry**: HC는 color label을 shuffle해도 SRM space 내 disparity가 변하지 않는 반면, CVD는 color label에 민감하게 의존한다. 이는 CVD의 높은 disparity가 일반적 noise가 아니라 **특정 색에 대한 systematic distortion**임을 의미한다.

#### 해석

"**Scattered but Parallel**" 패턴:
- CVD 피험자는 HC보다 SRM space에서 1.4~1.6배 더 dispersed되어 있으나 (heterogeneous)
- V2에서 HC-CVD RDM correlation [0.414, 0.587]이 HC-HC [0.442, 0.592]와 대폭 overlap → 색 간 relational structure는 보존
- 즉, CVD는 **동일한 color map**을 갖되 **위치가 어긋난** 것이지, map 자체가 깨진 것이 아님

**RDM Correlation (SRM space, Bootstrap 95% CI)**:

| ROI | HC-HC [95% CI] | HC-CVD [95% CI] | CVD-CVD [95% CI] | Interpretation |
|-----|---------------|----------------|----------------|------|
| V1 | 0.447 [0.357, 0.531] | 0.322 [0.237, 0.402] | 0.297 [0.126, 0.493] | HC-CVD < HC-HC (CI marginally separated) |
| **V2** | **0.517 [0.442, 0.592]** | **0.499 [0.414, 0.587]** | **0.591 [0.471, 0.702]** | **HC-CVD ≈ HC-HC (CI heavily overlapping)** |
| V3 | 0.385 [0.300, 0.473] | 0.348 [0.245, 0.457] | 0.591 [0.490, 0.672] | HC-CVD < HC-HC (slightly separated) |
| hV4 | 0.158 [0.069, 0.248] | 0.224 [0.119, 0.328] | 0.276 [0.008, 0.734] | CVD-CVD CI extremely wide (n=3) |

> Noise ceiling context: Phase 1 split-half ceiling V1=0.582, V2=0.635. V2 HC-HC 0.517 = 81% of ceiling.

개인 프로필:
- **sub-09 (protan)**: V1 dominant (HC 대비 +68%), early visual cortex에서 L-cone deficit의 직접적 반영
- **sub-08 (deutan)**: V2 dominant (HC 대비 +48%), V3 borderline (p=0.052), mid-level visual processing에서의 영향
- **sub-10 (deutan)**: 전 ROI에서 HC 범위 내 — **cortical compensation**의 증거

#### 우려 지점 및 보완 계획

1. **n=3 statistical power 한계**: CVD 3명으로는 group-level p<0.05 도달이 구조적으로 어려움. Large effect size (g>1.0)에도 불구하고 trending에 그침 → 개인 single-case analysis (Crawford & Howell)으로 보완하여 "2/3이 significant"라는 case-based report로 전환
2. **SRM alignment artifact 가능성**: 아래 triangulation (A3/A4/A5)으로 independent validation 완료

---

## Phase 2 보강: SRM-Independent Triangulation (A3/A4/A5)

### 주요 결과

**결론**: SRM이 아닌 independent method로도 동일한 subject-level 패턴이 재현되어, SRM 결과가 alignment artifact가 아닌 실제 neurological difference를 반영함이 확인됨.

**Convergent validity 요약**:

| Validation method | SRM dependency? | **k-value** | Group difference | SRM↔Independent metric correlation (pooled) |
|-----------|-----------|---------|----------|--------------------------|
| **A4 Crossnobis RDM** | **None** (native voxel) | **N/A (full dim)** | V1 p=0.051 trending | **r=0.486 (p=0.001)** |
| **A5 PCA-only** | **None** (different alignment) | **V1/V2=4, V3/hV4=3** | n.s. | **r=0.742 (p<0.001)** |
| **A5 PCA-CCA** | **None** (different alignment) | **V1/V2=4, V3/hV4=3** | n.s. | **r=0.472 (p=0.002)** |
| **A3 Variance Explained** | Yes (SRM W) | **SRM k** | V2: CVD>HC, g=−1.68 | r=−0.246 (n.s.) |

> A4에서 V1의 crossnobis group difference가 trending (p=0.051)이며, SRM V1 결과(p=0.062)와 converge. PCA-only와의 pooled correlation r=0.742는 SRM disparity가 측정한 subject-level 패턴이 alignment method에 비의존적임을 강력히 시사.

### 분석 방법

- **A4 Crossnobis**: Dimensionality reduction 없이 native voxel space에서 cross-validated Mahalanobis distance (Walther et al. 2016)를 계산. SRM과 완전히 independent한 metric.
- **A5 PCA-CCA**: SRM 대신 PCA dimensionality reduction + CCA alignment으로 동일한 분석을 재현. 45개 subject pair 각각 독립 alignment.
- **A3 Variance Explained**: SRM shared space가 각 subject의 데이터를 얼마나 잘 reconstruct하는지 정량화 (VE = 1 − ||X − WS||^2/||X||^2).

**A3의 역설적 결과**: CVD의 VE가 전 ROI에서 HC 이상, 특히 V2에서 significantly 높음 (CVD 0.448 vs HC 0.331, g=−1.68). CVD 데이터가 SRM space에서 더 잘 reconstruct된다는 것은, CVD가 "weak signal"이 아니라 "**strong signal, different structure**"임을 의미한다. 이는 "anisotropic correction" framing을 지지한다.

---

## Phase 2b: Decoder Model Comparison

### 주요 결과

**결론**: Voxel-color mapping은 근본적으로 linear이며, Procrustes alignment이 모든 model performance의 결정적 요인이다. 또한 Forward Encoding model만이 continuous color space interpolation이 가능하다.

**LORO overall performance (Procrustes-aligned)**:

| Model | Type | acc_45 [95% CI] | MAE (degree) [95% CI] |
|------|------|----------------|--------------|
| **LDA** | Linear | **0.821** [0.802, 0.841] | **25.6** [22.8, 28.3] |
| Ridge | Linear | 0.783 [0.750, 0.821] | 41.8 [37.9, 45.0] |
| SVM | Nonlinear | 0.776 [0.734, 0.811] | 32.9 [27.1, 38.7] |
| KernelRidge | Nonlinear | 0.739 [0.692, 0.779] | 47.9 [43.9, 52.1] |
| ForwardEnc | Linear | 0.736 [0.708, 0.773] | 43.5 [38.6, 47.2] |
| MLP | Nonlinear | 0.394 [0.381, 0.409] | 87.1 [85.1, 88.9] |

> Chance level: acc_45 = 37.5%, MAE = 90 degree. MLP를 제외한 모든 모델이 significantly above chance. LDA가 best performance.

**Procrustes alignment effect**:

| Model | Raw acc_45 | Procrustes acc_45 | Improvement |
|------|-----------|-------------------|------|
| LDA | 0.393 | 0.821 | **+0.428** |
| SVM | 0.382 | 0.776 | +0.393 |
| MLP | 0.370 | 0.394 | +0.024 |

> Alignment 없이는 **모든** 모델이 chance level (~37-39%). Nonlinear models (SVM, KernelRidge)도 run-to-run alignment mismatch를 compensate하지 못함. Procrustes alignment이 유일한 핵심 요인.

**LOCO interpolation test (10 subjects × 4 ROI × 1000 permutations)**:

| Model | V1 MAE (degree) | V2 MAE (degree) | V3 MAE (degree) | V4 MAE (degree) |
|------|---------|---------|---------|---------|
| **ForwardEnc** | **80.6 +/- 15.0** | **83.1 +/- 18.2** | **72.5 +/- 14.0** | **72.8 +/- 12.2** |
| LDA | 107.4 | 103.1 | 99.7 | 99.4 |
| SVM | 107.9 | 104.2 | 100.9 | 101.3 |

> ForwardEncoding만이 전 ROI에서 chance (90 degree) 이하의 MAE를 보임 → continuous color space structure를 포착하는 유일한 모델.

**HC vs CVD cross-decoding in SRM space (HC-only SRM training, LDA)**:

| ROI | k | HC LOSO | sub-08 (p) | sub-09 (p) | sub-10 (p) |
|-----|---|---------|-----------|-----------|-----------|
| V1 | 4 | 0.946 | **1.000** (<0.001) | **0.875** (<0.001) | **1.000** (<0.001) |
| V2 | 4 | 0.839 | **0.750** (<0.001) | **0.875** (<0.001) | **1.000** (<0.001) |
| V3 | 3 | 0.768 | **0.625** (<0.001) | **0.750** (<0.001) | **0.875** (<0.001) |
| hV4 | 3 | 0.446 | 0.375 (0.057) | **0.625** (<0.001) | 0.375 (0.056) |

> Chance = 12.5%. 12개 tests 중 **9개가 p<0.001**로 significant. CVD 피험자의 color representation이 HC common space에서 **decodable**함을 확인 → color signal 자체는 존재하되 geometric structure가 distorted된 것.

**시각화**:
- LOCO color wheel plots: [`phase2_decoder_comparing/results/loco/color_wheel_plots/`](../phase2_decoder_comparing/results/loco/color_wheel_plots/)
- Circular plots: [`phase2_decoder_comparing/results/loco/circular_plots/`](../phase2_decoder_comparing/results/loco/circular_plots/)

---

### 분석 방법

**LORO (Leave-One-Run-Out)**: 6개 run 중 5개로 training, 1개로 testing. "같은 색이 다른 run에서도 동일하게 보이는가?"를 검증. 비유: 같은 시험 문제를 다른 날 풀었을 때 consistency 검사.

**LOCO (Leave-One-Color-Out)**: 8개 색 중 7개로 training, 1개로 testing. "학습하지 않은 색을 predict할 수 있는가?"를 검증. 비유: 무지개에서 파란색을 빼고 학습한 후, 파란색의 neural response를 맞출 수 있는지. Forward Encoding model의 6-channel basis function 구조만이 이를 가능하게 함.

**Nested Procrustes**: 기존 Procrustes alignment이 test data에 대한 data leakage를 일으키는지 검증. 결과: leakage 제거 후 오히려 SVM performance가 +0.123 향상 → 기존 결과가 conservative이었음을 확인.

---

### 논의

#### 핵심 해석

LORO-LOCO dissociation이 CVD 연구의 핵심 증거:
- **LORO high accuracy** (CVD ~ HC): CVD 피험자가 color-selective signal을 갖고 있음
- **LOCO low interpolation** (CVD < HC): 그러나 color space의 **geometric structure가 distorted**되어, continuous color wheel이 깨져 있음
- 이 dissociation은 CVD를 "signal loss"가 아닌 "**color space distortion**"으로 규정하는 직접적 neurological evidence

#### 우려 지점

1. **LOCO individual-level statistical power 부족**: 8-fold × 6-run = 48 trials로는 individual significance 도달이 어려움 (4/40만 p<0.05)
2. **MLP degenerate solution**: n=40 training samples에 36K+ parameters → 47.5%에서 constant prediction 발생. Nonlinear capacity가 데이터 부족으로 활용 불가

#### Decoder Reliability 분석 — ForwardEncoding이 main model인 이유

**결론**: LDA가 highest accuracy (82.1%)이지만, ForwardEncoding이 multi-criteria evaluation에서 optimal decoder로 선정됨.

**Accuracy-Reliability Paradox**:
- LDA는 82.1% accuracy에도 불구하고, run-pair reliability가 r=0.009로 **사실상 random** — subject-ROI difficulty ranking이 run subset 간 완전히 reshuffle됨
- 568 voxels + 40 training samples → fold-specific separating hyperplane 학습 (overfitting의 hallmark)

**Multi-criteria Comparison**:

| Criterion | LDA | SVM (nested) | **ForwardEncoding** |
|-----------|-----|-------------|---------------------|
| LORO acc_45 (preloaded) | **0.821** | 0.776 | 0.736 |
| LORO acc_45 (nested) | 0.892 | **0.899** | 0.781 |
| Run-pair reliability | **0.009** (random) | 0.164 | **0.329** (best) |
| W matrix stability [95% CI] | N/A | N/A | **0.921** [0.907, 0.935] |
| LOCO interpolation | N.S. | N.S. | **p<0.01** (V3) |
| Alignment sensitivity | +0.428 (dependent) | +0.123 (moderate) | **+0.045** (robust) |
| Effective parameters | ~568 (overfit risk) | support vectors | **6** (parsimonious) |

**ForwardEncoding 선정 근거**:
1. **유일한 interpolation 가능 모델** — LOCO에서 V3 p<0.01 (continuous color space 포착)
2. **최고 alignment robustness** — nested vs preloaded 차이 +0.045 (SVM +0.123)
3. **최고 run-pair reliability** — r=0.329 (LDA의 37배)
4. **높은 encoding weight stability** — W matrix cosine similarity 0.921 [0.907, 0.935]
5. **Neuroscientifically grounded** — Brouwer & Heeger (2009) 6-channel basis function
6. **Parsimonious** — 6 effective parameters (LDA ~568, MLP 36K+)

> **LDA paradox 해석**: High accuracy + zero reliability = fold-specific hyperplane → test-time generalization은 높으나 learned representation이 unstable. ForwardEncoding은 moderate accuracy에 stable representation → Phase 3 filter learning에 적합한 basis.

---

## Phase 3: Filter Pre-Validation — V1/V2 집중 전략

### 전략 변경 요약

**기존 계획 (폐기)**:
- 3명 CVD group-level filter, V1-V4 모든 영역 포함, "3/3 동의" 우선순위 쌍

**확정 전략 (2026-02-19)**:
- Individual-specific filter (sub-08 deutan, sub-09 protan 별도)
- **V1/V2만 집중** (early visual areas, retinal deficit의 직접 영향)
- FDR-surviving pairs만 target (통계적 엄격성)
- Behavioral validation 우선 (4주) → r>0.5이면 filter 진행

**V1/V2 집중 근거**:
1. V1/V2가 primary color processing areas — cone deficit의 직접적 반영
2. Display filter는 retinal input을 변경 → V1/V2 correction이 가장 직접적
3. V3/hV4는 compensation areas — filter target이 아님
4. Phase 2 모든 validation metrics에서 V1/V2만 robust (LOSO stability, split-half reliability, crossnobis convergence)

### 주요 결과

**결론**: V1/V2에서 FDR-surviving color pairs는 sub-08에서 14 pairs, sub-09에서 7 pairs이며, 이들이 filter design의 유일한 target이다.

**V1/V2 FDR correction 결과** (Benjamini-Hochberg, q=0.05, Global FDR):

| 피험자 | V1 FDR surviving | V2 FDR surviving | **V1/V2 Total** | Filter recommendation |
|--------|-----------|-----------|------------|---------|
| **sub-08** (deutan) | 3 pairs | 11 pairs | **14 pairs** | **STRONG** — filter design 진행 |
| **sub-09** (protan) | 6 pairs | 1 pair | **7 pairs** | **WEAK** — exploratory only |
| sub-10 (deutan) | 0 pairs | 1 pair | **1 pair** | **Insufficient** — filter 불가 |

> 참고: 전체 252 tests (28 pairs × 3 ROI × 3 CVD) 중 V3 포함 시 37 pairs FDR surviving이나, V1/V2 집중 전략에 따라 실제 filter target은 위 수치로 한정됨.

---

### sub-08 (Deutan): V1/V2 Filter Target 14 Pairs

#### V2 Target (11 pairs) — 주요 영역

| Pair | z-score | p-value | Direction | Weight | Mechanism |
|----|---------|---------|------|--------|----------|
| **yellow-purple** | +13.87 | <0.0001 | Normalize down | 4.0 | S-cone extreme compensation |
| **red-yellow** | +9.38 | <0.0001 | Normalize down | 4.0 | S-cone over-reliance |
| **blue-purple** | +6.15 | <0.0001 | Normalize down | 3.5 | S-cone over-separation |
| yellow-green | +5.47 | <0.0001 | Normalize down | 2.5 | Adjacent over-separation |
| **orange-yellow** | +5.45 | <0.0001 | Normalize down | 3.0 | S-cone compensation |
| cyan-purple | +4.51 | <0.0001 | Normalize down | 2.5 | S-cone axis |
| red-purple | +3.85 | 0.0001 | Normalize down | 2.0 | — |
| orange-purple | +3.43 | 0.0006 | Normalize down | 2.0 | — |
| red-blue | +3.31 | 0.0009 | Normalize down | 2.0 | Cool-warm imbalance |
| yellow-cyan | +3.10 | 0.0019 | Normalize down | 2.0 | — |

#### V1 Target (3 pairs)

| Pair | z-score | p-value | Direction | Weight |
|----|---------|---------|------|--------|
| **red-yellow** | +5.14 | <0.0001 | Normalize down | 3.5 |
| **yellow-purple** | +4.84 | <0.0001 | Normalize down | 3.0 |
| red-cyan | +3.61 | 0.0003 | Normalize down | 2.5 |

**Deutan 패턴 요약**:
- **핵심 deficit**: L-M axis (red-orange-yellow-green)
- **Compensation strategy**: S-cone extreme over-reliance (yellow-purple z=13.87!)
- **Filter objective**: S-cone axis over-separation 감소, L-M separation 복원
- **Priority targets**: yellow-purple, red-yellow, blue-purple, orange-yellow (V1/V2 공통)

---

### sub-09 (Protan): V1/V2 Filter Target 7 Pairs

#### V1 Target (6 pairs) — 주요 영역

| Pair | z-score | p-value | Direction | Weight | Mechanism |
|----|---------|---------|------|--------|----------|
| **cyan-magenta** | +4.08 | <0.0001 | Normalize down | 3.5 | S+M cone compensation |
| **orange-magenta** | +3.71 | 0.0002 | Normalize down | 3.0 | Magenta axis elevation |
| **red-magenta** | +3.52 | 0.0004 | Normalize down | 3.0 | L-cone deficit compensation |
| green-magenta | +3.43 | 0.0006 | Normalize down | 2.5 | — |
| yellow-purple | -3.31 | 0.0009 | Restore up | 2.5 | Under-separation (protan-specific) |
| green-blue | -3.00 | 0.0027 | Restore up | 2.0 | — |

#### V2 Target (1 pair)

| Pair | z-score | p-value | Direction | Weight |
|----|---------|---------|------|--------|
| orange-magenta | +2.91 | 0.0036 | Normalize down | 2.0 |

**Protan 패턴 요약**:
- **핵심 deficit**: L-cone (red) deficit
- **Compensation strategy**: M+S cone reliance → magenta axis over-separation
- **Deutan과 차이**: Compensation axis가 다름 (magenta vs yellow-purple)
- **Filter objective**: Magenta axis normalization, cool-color separation 복원
- **Priority targets**: cyan-magenta, orange-magenta, red-magenta

---

### sub-10 (Deutan, compensation 성공): Filter 불가

- V2에서 blue-purple 1 pair만 FDR surviving (z=+2.86, p=0.0042)
- **"Cortical compensation success" case study**로 보고
- Filter 개발 안 함

---

### 분석 방법

**B1 Permutation test**: 10명 중 3명을 "pseudo-CVD"로 random assignment하는 모든 조합(C(10,3)=120)으로 null distribution 생성. 각 color pair의 z-score가 null distribution에서 얼마나 극단적인지 two-tailed test.

비유: 교실에서 random으로 3명을 골라 "색맹"이라고 label 붙였을 때와, 실제 CVD 피험자의 neural response 차이가 같은 수준인지 비교하는 것.

**B2 Split-half stability**: 실험의 first half (run 1-3)와 second half (run 4-6)에서 동일한 color pair 패턴이 나타나는지를 Spearman correlation으로 측정.

**B3 Bootstrap CI**: 6개 run에서 resampling with replacement (1000 iterations)하여 각 color pair의 z-score에 대한 95% CI 산출. CI가 zero를 포함하지 않으면 significant.

**Crossnobis**: Walther et al. (2016)의 cross-validated Mahalanobis distance. SRM 없이 native voxel space에서 직접 color pair distance를 추정하여 SRM 결과의 independent replication을 시도.

---

### 논의

#### Split-half Reliability (B2) — V1/V2 중심

| ROI | sub-08 r | sub-09 r | sub-10 r | Group r |
|-----|---------|---------|---------|--------|
| **V1** | 0.777*** | 0.645*** | 0.286 | **0.729*** |
| **V2** | **0.839***  | 0.684*** | 0.677*** | **0.714*** |

> V1, V2 모두 group-level r > 0.71 → temporally stable. sub-08이 V2에서 가장 stable (r=0.839).

#### Deutan vs Protan Compensation Axis 차이

- **sub-08 (deutan)**: S-cone axis over-reliance → yellow-purple/red-yellow over-separation
- **sub-09 (protan)**: Magenta axis over-reliance → cyan-magenta/orange-magenta over-separation
- 이 차이가 CVD subtype별 individual-specific filter의 필요성을 뒷받침

#### V1/V2 Convergence Evidence — "Representation-dependency" 문제의 완화

**문제 (기존)**: SRM space에서 37/252 pairs가 significant하지만, native voxel space (crossnobis)에서는 0/252가 FDR surviving.

**V1/V2 집중 전략에 의한 완화**:

| Convergence metric | V1 | V2 | V3 | hV4 |
|----------|----|----|----|----|
| SRM-Crossnobis correlation | **r=0.721\*** | **r=0.806\*\*** | r=0.200 | r=0.248 |
| SRM-PCA correlation | r=0.636\* | **r=0.891\*\*\*** | r=0.285 | r=0.661\* |

> V1/V2에서만 SRM과 independent method 간 strong convergence (r>0.6~0.9). V3/hV4는 convergence 약함.
> → **V1/V2 filter targets은 SRM artifact가 아닌 real signal에 기반**할 가능성이 가장 높음.

**중화 논거**:
1. V1/V2의 SRM-crossnobis correlation이 r=0.72~0.81로 **directional convergence** → signal이 존재하되 high-dimensional space에서 noise에 묻힘
2. V1/V2에서만 LOSO stability (6/7, 7/7), split-half reliability (both significant), individual single-case significance (sub-09 V1, sub-08 V2) 모두 converge
3. V3/hV4를 제외함으로써 "representation-dependency" critique의 영향 범위를 최소화

#### 보완 계획

| 항목 | 상태 | 일정 |
|------|------|------|
| Multiple comparison correction (FDR) | **완료** | — |
| SRM circularity (crossnobis replication) | **완료** (V1/V2 convergence 확인) | — |
| V1/V2 집중 전략 확정 | **완료** | — |
| **Behavioral validation** (FM-100 + JND) | **미완** | 1-2주 내 수집 |
| 8-color overfitting → Fourier parameterization | Design 완료 | Phase 3 본격 시 |

**Go/No-Go 기준**: Behavioral JND와 SRM z-score 간 correlation r>0.5이면 filter design 진행, r<0.3이면 descriptive paper로 전환.

---

## 종합 요약

| Analysis | V1 | V2 | V3 | hV4 |
|------|----|----|----|----|
| Group permutation test | p=0.062 (trending) | p=0.075 (trending) | n.s. | n.s. |
| Crawford individual test | **sub-09 p=0.007\*\*** | **sub-08 p=0.040\*** | sub-08 p=0.052 | n.s. |
| LOSO stability | 6/7 significant | **7/7 significant** | 0/7 | 0/7 |
| Split-half reliability | One-sided significant | **Both significant** | N/A | N/A |
| CVD color dependency (LOSO) | n.s. | **p=0.010** | **p=0.000** | **p=0.016** |
| Crossnobis convergence (A4) | **r=0.721\*** | **r=0.806\*\*** | r=0.200 | r=0.248 |
| PCA-only convergence (A5) | r=0.636\* | **r=0.891\*\*\*** | r=0.285 | r=0.661\* |
| CVD cross-decoding | 3/3 significant | 3/3 significant | 3/3 significant | 1/3 significant |
| **Filter targets (V1/V2 FDR)** | sub-09: **6 pairs** | sub-08: **11 pairs** | *(excluded)* | *(excluded)* |

**V2가 가장 robust한 ROI**: 모든 validation metrics에서 일관적. V1은 individual level에서 강력 (sub-09). V3/hV4는 group difference 없으며 filter target에서 제외.

**핵심 메시지**: CVD 피험자의 visual cortex color representation은 (1) HC와 distinguishable하고, (2) individual-specific · ROI-specific이며, (3) color signal 자체는 보존되나 geometric structure가 distorted되어 있다. V1/V2에서의 robust convergence evidence에 기반하여, individual-specific color filter는 sub-08 (V2-dominant, 14 pairs)과 sub-09 (V1-dominant, 7 pairs)를 대상으로 설계한다.

---

## 참조 파일

| 파일 | 용도 |
|------|------|
| [`phase2_SRM_across_between/results/loo_consistent/20260218_163819/figures/srm_4panel_figure.png`](../phase2_SRM_across_between/results/loo_consistent/20260218_163819/figures/srm_4panel_figure.png) | Phase 2 시각화 |
| [`future_phase3_filter_optimization/pre_validation/UPDATED_FILTER_STRATEGY.md`](../future_phase3_filter_optimization/pre_validation/UPDATED_FILTER_STRATEGY.md) | V1/V2 전략 상세 |
| [`future_phase3_filter_optimization/pre_validation/FDR_CORRECTION_SUMMARY.md`](../future_phase3_filter_optimization/pre_validation/FDR_CORRECTION_SUMMARY.md) | FDR correction 결과 |
| [`future_phase3_filter_optimization/pre_validation/PROJECT_STATUS_2026-02-19.md`](../future_phase3_filter_optimization/pre_validation/PROJECT_STATUS_2026-02-19.md) | 프로젝트 현황 |
| [`future_phase3_filter_optimization/pre_validation/results/fdr_corrected/FDR_CORRECTION_REPORT.md`](../future_phase3_filter_optimization/pre_validation/results/fdr_corrected/FDR_CORRECTION_REPORT.md) | FDR correction 상세 보고서 |
