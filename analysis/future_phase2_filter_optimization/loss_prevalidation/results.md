# Loss Prevalidation: Cross-ROI Consistency

> **날짜**: 2026-03-17
> **스크립트**: `scripts/check_cross_roi_consistency.py`
> **결과 JSON**: `results/cross_roi_consistency.json`

---

## 배경: Cone Shift Filter 기각과 파이프라인 전환

### Cone Shift 접근 (기각됨)

Stockman cone 모델로 CVD의 망막 cone sensitivity shift(deutan M cone +13nm 등)를 계산하고, 각 색의 hue angle 이동량(θ_equiv)을 예측하여 hV4 반응을 보정하려 했다.

**결과**: 보정 후 예측이 극적으로 악화 (3명 모두 Wilcoxon p<0.05, 잘못된 방향).

| Subject | Type | Baseline r | Corrected r | Delta |
|---------|------|:---:|:---:|:---:|
| sub-08 | deutan (13nm) | 0.390 | 0.069 | -0.321 |
| sub-09 | protan (40nm) | 0.495 | -0.080 | -0.575 |
| sub-10 | normal (12nm) | 0.441 | 0.185 | -0.256 |

**기각 이유**: Cone shift는 망막 수준에서 47~109도 각도 이동을 예측하지만, 실제 hV4 복셀 패턴은 원래 각도 그대로 넣었을 때 HC와 잘 맞음(baseline r≈0.39~0.50). 피질이 망막 왜곡을 상당 부분 보상하고 있어, 망막 shift를 대입하면 오히려 깨진다. CVD 문제는 "각 색의 위치가 통째로 이동"이 아니라 "색 간 **거리 구조**(geometry)가 왜곡"된 것.

### 현재 파이프라인: RDM Matching Filter

자극의 hue angle을 미세 조정(T_ψ)하여 CVD의 색 간 거리 구조를 HC와 맞추는 것이 목표.

```
원래: 8색 θ → C(θ) → W_CVD → Y_pred → RDM_CVD (pair distances 왜곡)
교정: 8색 θ → T_ψ(θ) → C(T_ψ(θ)) → W_CVD → Y_pred → RDM_corrected ≈ RDM_HC
```

T_ψ(θ) = θ + a₁cosθ + b₁sinθ + a₂cos2θ + b₂sin2θ (Fourier 4 params)

| | Cone Shift (기각) | 현재 파이프라인 |
|---|---|---|
| 하는 일 | 각 색의 각도를 통째로 이동 | 색 간 거리 구조를 HC에 맞춤 |
| 파라미터 | 1개 (Δλ nm) | 4개 (Fourier) |
| Loss | 없음 (물리 모델 대입) | V2 RDM: Σ[d_pred(i,j) - d_HC(i,j)]² |
| Evaluation | hV4 voxel corr | hV4 LOCO per-color |
| 이동량 | 47~109도 (과격) | 최적화로 결정 |

> **출처**: `future_phase1_forward_model/results/cone_shift_loco/cone_shift_prediction_results.json`

---

## 0. 목적

Phase 2 filter 파이프라인의 전제 조건 검증:
- **핵심 질문**: V2 SRM pair 왜곡을 loss로 사용하고, hV4 LOCO를 evaluation으로 사용하는 2-ROI 파이프라인이 타당한가?
- **방법**: 3단계 교차 검증 (cross-ROI → cross-metric → cross-modal)

---

## 1. Level 1: V2 ↔ hV4 28-pair Distortion Correlation

**질문**: V2에서 왜곡된 pair가 hV4에서도 왜곡되는가?

**방법**: CVD pair distance − HC mean pair distance = distortion (28 pairs). V2 distortion과 hV4 distortion 간 Spearman 상관.

### 결과

| Subject | Type | Spearman r | p-value | 판정 |
|---------|------|:---:|:---:|:---:|
| **sub-08** | Distortion | **0.878** | **<0.0001** | PASS |
| **sub-08** | Z-score | **0.686** | **0.0001** | PASS |
| sub-09 | Distortion | 0.472 | 0.011 | PASS |
| sub-09 | Z-score | 0.479 | 0.010 | PASS |
| sub-10 | Distortion | 0.112 | 0.570 | FAIL |
| sub-10 | Z-score | 0.118 | 0.551 | FAIL |
| **Pooled** (84) | Distortion | **0.565** | **<0.0001** | PASS |

### 해석

1. **sub-08 (deutan)**: r=0.878로 V2와 hV4가 거의 동일한 왜곡 프로파일을 공유. V2 loss → hV4 evaluation 파이프라인의 **강력한 근거**.
2. **sub-09 (protan)**: r=0.472로 중간 상관. V2 왜곡이 hV4와 부분적으로 공유되지만 독립 성분도 존재.
3. **sub-10 (보상형)**: 상관 없음. 왜곡 자체가 미미하므로(mean |z|=0.69, 유의 pair 1/28) filter 대상이 아님.
4. **Pooled**: r=0.565 (p<0.0001) → 전체적으로 cross-ROI consistency 존재.

**결론**: V2 pair 왜곡을 loss signal로 사용하는 것은 sub-08에서 강력하게, sub-09에서 조건부로 지지됨. sub-10은 filter 자체가 불필요.

---

## 2. Level 2: V2 Distortion Burden → hV4 LOCO Per-Color (미고려)

**질문**: V2에서 많이 왜곡된 색이 hV4 LOCO에서도 실패하는가?

**방법**: 색 c에 관여하는 7개 pair의 V2 왜곡 L2 norm → burden(c) = sqrt(Σ_j Δd(c,j)²). hV4 LOCO voxel_corr(c)와 상관.

### 결과

| Subject | Spearman r | p-value | n |
|---------|:---:|:---:|:---:|
| sub-08 | -0.214 | 0.610 | 8 |
| sub-09 | -0.167 | 0.693 | 8 |
| sub-10 | +0.333 | 0.420 | 8 |
| Pooled | -0.297 | 0.159 | 24 |

**모두 유의하지 않음.**

### 해석

Level 1과 Level 2의 괴리 원인:

1. **차원 축소 손실**: 28 pair → 8 color로 L2 norm 축약 시, pair-level 방향 정보 소실.
2. **n=8의 검정력 한계**: Spearman 유의에 r>0.71 필요 (α=0.05, n=8).
3. **개념적 불일치**: 예시 — sub-08 red: V2 burden=0.84 (2위, red-yellow z=10.3 기여) BUT hV4 LOCO=+0.573 (최고). Red의 V2 pair 왜곡이 크더라도, 나머지 7색에서 red로의 hV4 보간은 성공할 수 있음.

**결론**: V2 왜곡은 **pair 수준**에서 hV4와 일관되지만 (Level 1), **per-color 집약 후**에는 hV4 LOCO를 예측하지 못함. → Filter 최적화는 반드시 **28 pair distance를 직접** target해야 하며, per-color metric은 부적절. 기존 `loss_rdm()` 구조(pair-level)가 적합.

---

## 3. Level 3: Behavioral JND ↔ V2 Distortion (sub-08)

**질문**: 행동적으로 더 둔감한 pair가 V2에서도 더 왜곡되었는가?

**방법**: JND ratio (CVD/HC) vs V2 signed distortion, 8 matched pairs.

### 결과

| Metric | r | p | n |
|--------|:---:|:---:|:---:|
| Spearman (signed) | 0.500 | 0.207 | 8 |
| Spearman (\|dist\|) | 0.500 | 0.207 | 8 |

### Per-Pair Detail

| Pair | JND ratio | V2 dist | JND 방향 |
|------|:---:|:---:|:---:|
| yellow-green | 2.71 | +0.296 | HYPO |
| yellow-purple | 2.50 | +0.559 | HYPO |
| orange-yellow | 1.90 | +0.453 | HYPO |
| cyan-magenta | 0.84 | +0.127 | HYPER |
| green-blue | 0.76 | -0.042 | HYPER |
| blue-purple | 0.73 | +0.246 | HYPER |
| red-cyan | 0.32 | +0.374 | HYPER |
| red-orange | 0.27 | +0.044 | HYPER |

### 해석

방향은 맞지만 통계적 유의에 미달 (n=8 검정력 부족). 주요 불일치:

- **red-cyan**: JND 0.32 (HYPER = CVD가 더 잘 변별) BUT V2 distortion +0.374 (과분리). 고전적 deutan 특성 — L-M axis shift로 red-cyan 거리 증가는 변별에 유리하게 작용.
- **blue-purple**: JND 0.73 (약한 HYPER) + V2 +0.246 (과분리). 방향 일치하지만 S-cone 보존으로 HYPER가 예상보다 약함.

**Phase 3 notion.md §3-1과의 비교**: SRM z vs JND는 6쌍 중 4쌍 불일치(67%). 본 분석의 V2 distortion vs JND도 유사한 패턴. 이유: SRM z와 V2 distortion은 모두 **끝점 간 거리** (전역 기하)를 측정하지만, JND는 **국소 보간 기울기**(local sensitivity)를 측정. 끝점 과분리(양의 distortion/z)가 국소 기울기 감소(HYPO)와 공존 가능.

---

## 4. 종합 판정

| Level | 질문 | 결과 | 판정 |
|-------|------|------|:---:|
| 1 | V2 ↔ hV4 pair 왜곡 일관성 | r=0.878 (sub-08) | **PASS** |
| 2 | V2 per-color burden → hV4 LOCO | r=-0.21 (sub-08) | FAIL |
| 3 | JND ↔ V2 distortion | r=0.50 (underpowered) | 보류 |

### 파이프라인 결정

**Primary: V2 RDM loss → hV4 LOCO evaluation** (§5에서 상세). Level 1 PASS로 pair-level 근거 확보. Level 2 FAIL은 per-color 축약이 부적절함을 확인 → loss 함수는 28 pair distance를 직접 최적화해야 함.

**Alternative: hV4 LOCO loss → V2 RDM evaluation** (§6에서 상세). Phase 3 notion.md §3-2에서 LOCO 취약성 → JND HYPO 일치율 100% (3/3) → LOCO가 SRM z보다 행동을 잘 예측.

### Per-Subject Loss ROI 전략

sub-08(deutan)과 sub-09(protan)는 색약 유형이 다르므로 각각의 최적 loss ROI가 다름.

**sub-08 (deutan)**: V2 단독 (r=0.878, 11/28 sig → 명확)

**sub-09 (protan)**: V1 + V2 병행

| 기준 | V1 | V2 |
|------|:---:|:---:|
| |z|>1.96 pairs | **5/28** | 0/28 |
| Split-half r | **0.692** | 0.653 |
| ↔ hV4 Spearman | 0.353 (p=0.065) | **0.472 (p=0.011)** |
| Top distortion | magenta 관련 4쌍 (protan) | magenta 관련 3쌍 |

V1은 자체 신호가 강하고(5/28 sig), V2는 hV4 연결이 더 강함. Protan 왜곡이 V1에 집중되는 특성을 반영하여 V1+V2 모두 loss ROI로 시도.

**sub-10 (보상형)**: Filter 대상 제외 (왜곡 미미, 1/28 sig).

---

## 5. Primary Pipeline: V2 RDM Loss → hV4 LOCO Evaluation

### 5-1. 구조

```
[V2 SRM pair distances] ──loss──→ T_ψ filter ──eval──→ [hV4 LOCO per-color]
       28 pairs                   4 Fourier params         8 colors
       │                                                      │
       └── LOCO 취약 가중치 ←──────────────────────────────────┘
```

### 5-2. 가중 Loss 함수

**관찰**: V2 끝점 왜곡(SRM z)과 JND HYPO가 4/6 불일치 (notion.md §3-1). 끝점 과분리가 국소 보간 실패와 공존. 따라서 단순 HC 정상화가 아닌 **LOCO 취약 색 기반 가중**이 필요.

```python
# LOCO vulnerability: 1 - normalized voxel_corr (높을수록 취약)
vuln[c] = 1 - (loco_corr[c] - min) / (max - min)

# Pair weight: 양 끝 색 중 더 취약한 쪽
w[i,j] = max(vuln[i], vuln[j])

# Weighted RDM loss
L_rdm = Σ_{i<j} w[i,j] · [d_pred(i,j) - d_HC(i,j)]²
```

**근거**: LOCO 취약 색을 포함하는 pair(예: yellow-green, orange-yellow)에 높은 가중치 → 보간 실패 영역의 V2 왜곡 교정에 집중.

### 5-3. 필요 데이터

| 데이터 | 역할 | 소스 | 위치 |
|--------|------|------|:---:|
| V2 pair distances (HC, CVD) | Loss target 28 pairs | SRM pre-validation | 로컬 |
| hV4 LOCO per-color voxel_corr | Evaluation + vulnerability weight | Forward model validation | 로컬 |
| W₀ (HC group prior encoder) | d_pred 계산: C(T_ψ(θ)) @ W₀ | step1_build_model.py | **서버** |
| C(θ) basis (FE-6, 360×6) | Forward model basis | utils_forward_model.py | 로컬 (코드) |
| hc_rdm_mean | Loss target (HC 기준 RDM) | step1_build_model.py | **서버** |
| Behavioral JND | 해석/외부 검증 | behav_pilot | 로컬 |

### 5-4. 평가 기준

| Metric | 성공 조건 | 소스 |
|--------|----------|------|
| hV4 LOCO improvement | filter 적용 후 mean voxel_corr 증가 | per-color LOCO |
| V2 RDM Δ reduction | Σ(d_CVD - d_HC)² 감소 | loss 직접 |
| JND HYPO pair 방향 일치 | HYPO pair의 d_pred → d_HC 방향 | 행동 교차 검증 |

---

## 6. Alternative Pipeline: hV4 LOCO Loss → V2 RDM Evaluation

### 6-1. 근거

| 예측자 | JND HYPO 예측 정확도 |
|--------|:---:|
| **hV4 LOCO 취약성** | **3/3 (100%)** |
| SRM z-score (V2) | 2/6 (33%) |
| V2 distortion | r=0.50, underpowered |

LOCO가 행동과 가장 잘 수렴 → loss signal로서 더 직접적.

### 6-2. 구조

```
[hV4 LOCO per-color] ──loss──→ T_ψ filter ──eval──→ [V2 SRM RDM]
       8 colors                  4 params              28 pairs (FDR 12쌍)
```

### 6-3. 장단점

| | Primary (V2→hV4) | Alternative (hV4→V2) |
|---|:---:|:---:|
| Loss df | 28 pairs | 8 colors |
| Loss-행동 일치 | 33% (SRM z) | **100% (LOCO)** |
| Eval 신호 풍부도 | 8 colors | **28 pairs (12 FDR)** |
| Overfitting 위험 | 낮음 (28 » 4 params) | 높음 (8 ≈ 2× params) |

### 6-4. 현재 상태

**보류** — Primary pipeline 검증 후, hV4 LOCO loss의 df 부족(8 vs 4 params)이 문제인지 확인 필요. Primary 실패 시 전환 검토.

---

## 7. 출처

| 데이터 | 파일 |
|--------|------|
| V2/hV4 pair distances | `target_prevalidation/results/filter_pre_validation_results.json` |
| hV4 LOCO per-color | `future_phase1_forward_model/results/validation/sub-*_loco.json` |
| Behavioral JND | `data/behav_pilot/*_jnd_ses1_no_filter_summary.csv` |
| 행동-신경 교차분석 | `future_phase3_behavioral_analysis/notion.md` |
