# Behavioral Alignment Report — Sub-08 LOCO-canonical Filter
**Date**: 2026-05-19  
**Subject**: sub-08 (deutan, moderate)  
**Filter**: 2-component LOCO-canonical (β_s=38°, β_c=−14°, axis=150°)  
**Status**: Pre-Phase-3 characterization; formal validation pending (pre-registered 2AFC)

---

## 1. Per-Hue Data Integration

### 1.1 완전 통합 테이블

| Hue | δθ (filter) | 8AFC acc | LOCO sig | JND pair | JND vs HC | 방향 |
|---|---|---|---|---|---|---|
| c1 red (0°) | +12.1° | 100% | NS | red–orange | 0.50× | HYPER |
| c2 orange (45°) | **+30.5°** | 87.5% | V1+V2 ★ | orange–yellow | 3.02× | **HYPO** |
| c3 yellow (90°) | **+31.0°** | **62.5%** | V1+V2 ★★ | yellow–green | 3.10× | **HYPO** |
| c4 green (135°) | +13.3° | **62.5%** | NS | yellow–green | 3.10× | **HYPO** |
| c5 cyan (180°) | −12.1° | 100% | NS | cyan–magenta | 0.95× | borderline |
| **c6 blue (225°)** | **−30.5°** | **100%** | **NS** | blue–purple | **0.73×** | **HYPER** |
| c7 purple (270°) | **−31.0°** | **62.5%** | V1 ★ | yellow–purple | 2.87× | **HYPO** |
| c8 magenta (315°) | −13.3° | 75% | NS | cyan–magenta | 0.95× | borderline |

**데이터 출처**:
- δθ: `BEST_summary.json` (LOCO-canonical, loco_distortion_fit.py)
- 8AFC: `data/behavior/sub-08_rsvp_8afc_ses1_run1.csv` (64 trials, session 1)
- LOCO sig: `results/cross_modal_concordance.json` (Crawford–Howell, V1/V2)
- JND: `results/jnd_summary.csv` (7-HC group reference, ses1 no-filter)

### 1.2 8AFC 혼동 행렬 (sub-08)

```
Stimulus → Response (오류만)
c2 orange  → c3 yellow ×1
c3 yellow  → c4 green ×1, c1 red ×1, c8 magenta ×1
c4 green   → c3 yellow ×2, timeout ×1
c7 purple  → c8 magenta ×3
c8 magenta → c7 purple ×2
```

**주요 혼동 쌍**: c3↔c4 (yellow–green, 3회), c7↔c8 (purple–magenta, 5회)  
**오류 없음**: c1, c5, c6 (red, cyan, blue)

---

## 2. 핵심 패턴: Warm-side 비대칭

### 2.1 세 독립 지표의 수렴

세 가지 독립적으로 수집된 측정치가 동일한 패턴으로 수렴:

| 지표 | Warm-side (c2/c3/c7) | Cool-side (c6) |
|---|---|---|
| LOCO (신경) | 유의 (p<0.023) | NS |
| 8AFC (행동) | 62.5–87.5% | 100% |
| JND | HYPO (2.87–3.10×) | HYPER (0.73×) |

### 2.2 Blue–purple JND의 해석

Purple (c7, δθ=−31°)이 blue 방향으로 neural representation이 이동하면, 
blue(c6)와 purple(c7)의 **지각 거리는 오히려 증가**해야 한다.

- 실제 JND: blue–purple = **0.73× HC (HYPER)** — HC보다 더 쉽게 변별
- 해석: c7 purple의 왜곡이 c6 blue와의 변별을 용이하게 만드는 방향으로 작용
- 이는 2-component 모델의 δθ 방향(c7이 blue 쪽으로 이동)과 **행동적으로 일치**

### 2.3 모델 예측 vs. 실제

2-component 모델은 β_s·cos(h−90°) 구조상 **blue(c6)와 orange(c2)에 대칭적 크기(±30.5°)를 예측**한다.

- Orange (c2): 8AFC 87.5%, LOCO V1+V2 sig, JND HYPO → **예측 일치**
- Blue (c6): 8AFC 100%, LOCO NS, JND HYPER → **예측 불일치**

→ 실제 왜곡은 warm-side(orange/yellow/purple)에 비대칭적으로 집중되며,
cool-side(blue/cyan)은 보존된다.

---

## 3. 모델 한계 — 2-component cosine의 구조적 비대칭 미포착

### 3.1 수학적 원인

δθ(h) = β_s·cos(h−90°) + β_c·cos(h−150°)

이 함수는 β_s 축(90°=yellow, 270°=purple)에 대해 점대칭 구조를 강제한다.
c2 orange(+30.5°)와 c6 blue(−30.5°)가 동일한 크기로 예측되는 것은
모델 기저함수의 대칭성에 기인하며, 실제 신경 왜곡의 특성이 아니다.

### 3.2 생물학적 근거

**Brettel, Viénot & Mollon (1997)**:
- 475 nm blue는 deuteranope와 정상 관찰자 모두에게 동일한 blue로 지각됨
- CVD 전체에서 보존되는 perceptual anchor

**Emery et al. (2021)**:
- AT 관찰자: blue–yellow 반응 범위 확장, red–green 범위 수축
- L–M 신호 감소가 warm-color 쪽에 편향됨을 직접 지지
- 선형 cosine 기저함수는 "too broad to characterize the responses" (cf. De Valois et al. 1997)

### 3.3 모델 한계 결론

비대칭 왜곡을 포착하려면 rectified 또는 power-law basis가 필요하나,
현재 8개 hue × 2-DOF 조건에서는 추가 자유도가 overfitting 위험을 초래한다.
이는 **fitting criterion이 아닌 model class의 구조적 한계**이다.

---

## 4. Sub-09 상황

Sub-09 (protan, moderate-severe)의 8AFC CSV 파일이 `data/behavior/`에 없음.
공식 혼동 행렬 보고 불가.

**δθ 프로파일** (LOCO-canonical, β_s=6°, β_c=−22°, axis=16°):

| Hue | δθ | 예측 손상 방향 |
|---|---|---|
| c1 red (0°) | −21.1° | L–M 축 (protan 예상 패턴) |
| c2 orange (45°) | −15.1° | |
| c3 yellow (90°) | −0.2° | 거의 없음 |
| c4 green (135°) | +14.8° | |
| c5 cyan (180°) | **+21.1°** | L–M 축 (largest) |
| c6 blue (225°) | +15.1° | |
| c7 purple (270°) | +0.2° | 거의 없음 |
| c8 magenta (315°) | −14.8° | |

→ Protan 패턴: red(c1)↔cyan(c5) 축에 집중 (L–M opponent axis)  
→ Sub-08 deutan과 **구조적으로 다른 필터 방향** (다른 위상의 비대칭 축)  
→ 8AFC 공식 데이터 없으므로 방향 일치 서술만 가능 (pending)

---

## 5. LOCO–JND Concordance (기존 결과 요약)

| 쌍 | LOCO-취약 hue 포함 | JND 방향 | 일치 |
|---|---|---|---|
| orange–yellow | orange(c2), yellow(c3) | HYPO | ✓ |
| yellow–green | yellow(c3) | HYPO | ✓ |
| yellow–purple | yellow(c3), purple(c7) | HYPO | ✓ |
| red–orange | — | HYPER | ✓ |
| green–blue | — | borderline | ✓ |
| blue–purple | — | HYPER | ✓ |

**LOCO–JND concordance: 6/6 (100%)**  
**SRM z–JND concordance: 2/6 (33%)**

→ LOCO만이 행동 변별 실패를 예측; SRM metric은 functional predictor가 아님

---

## 6. Paper §results:twocomp 서술 초안

```
Sub-08의 세 독립 지표(LOCO, 8AFC, JND)는 동일한 warm-side 비대칭으로 수렴한다.
세 LOCO-취약 hue (orange, yellow, purple; 모두 |δθ|≥30.5°)는
8AFC에서 각각 87.5%, 62.5%, 62.5%의 정확도를 보였으며 (HC 평균 97.3%),
이 hue를 포함하는 JND 쌍 3개 모두 HYPO 기준을 충족했다 (LOCO–JND 100% 일치).
모델의 두 왜곡 정점(yellow +31°, purple −31°)은 
각각 c3↔c4 (yellow–green), c7↔c8 (purple–magenta) 혼동 쌍에 대응된다.

Blue (c6, δθ=−30.5°)는 8AFC 100%, LOCO NS, JND HYPER(0.73×)로
3개 지표 모두에서 보존되었다. 
2-component 모델은 cosine 기저의 대칭성으로 인해
orange와 blue에 동일한 크기의 왜곡을 예측하지만,
실제 왜곡은 warm-side에 비대칭적으로 집중된다.
이는 475 nm blue가 red-green CVD 전체에서 perceptual anchor로 보존된다는
기존 문헌(Brettel et al. 1997)과,
AT에서 red–green 범위 수축과 blue–yellow 범위 확장이 관찰된다는
hue-scaling 증거(Emery et al. 2021)에 부합한다.
이 비대칭을 포착하려면 nonlinear basis가 필요하나
현재 8-hue × 2-DOF 조건에서는 추가 자유도가 overfitting 위험을 초래한다.
```

---

## 7. 추후 작업

- [ ] Sub-09 8AFC 데이터 수집 (Phase 3 세션)
- [ ] Sub-08 필터 적용 후 8AFC 재측정 (filter-on vs filter-off 비교)
- [ ] Blue-purple JND 재측정: 필터 후 HYPER 유지되는지 확인
  - 예측: purple δθ=−31° 보정 시 blue–purple JND가 HC 수준으로 이동
- [ ] 사전 등록 (OSF): warm-side HYPO 3쌍 개선 + blue-purple HYPER 유지 예측
