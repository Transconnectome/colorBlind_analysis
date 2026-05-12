# Phase 3 후보 필터 평가 보고서 — sub-08 deutan

**작성일**: 2026-05-11
**목적**: 손실함수별 후보 + HC specificity + 행동 데이터 기반 예측으로 Phase 2→3 전환 단계 후보 필터 평가.
**범위**: sub-08 deutan, V4, CURRENT Stockman-corrected 2-component formula.

---

## 1. 방법론

### 1.1 후보 풀 (17개)

| 출처 | 후보 |
|---|---|
| 기존 검증된 (3) | Canonical, V4-only_CURRENT, Cycle14 |
| Loss inventory (9) | l_rank, l_dir, norm_resid, l_mag, sign_agree, phase_a_V1, cycle12_xroi, cycle15_opt3, cycle15_opt4 |
| 제안 (5) | scaled_canonical, mid_canonical_cycle14, soft_canonical, wide_canonical, S_dominant |

### 1.2 평가 기준

| 지표 | 정의 | 채점 방식 |
|---|---|---|
| **P2a** | col2 HC 명명 ↔ sub-08 원본 verbal의 HC 등가 색 | HC color naming function (15 bin) + adjacency partial |
| **P1**  | col4(sub-08 지각) ↔ HC 목표 색 | perception map nearest-k=3 → HC name 변환 후 adjacency |
| **P2b** | col4 HC name == HC 목표 (clean only) | 1.0/0.0 (인접 점수 없음) |
| **Collapse penalty** | c5-c8 pre-image 압축 + sub-08 지각 family 중복 | span<60° / gap<12° / unique families<4 모두 감점 |
| **c8 anomaly penalty** | c8 col2의 HC name이 magenta/pink/red면 sub-08 verbal "deep blue"와 충돌 | -0.5 fixed |
| **HC spec** | bootstrap fraction (HC mean < CVD norm) | hc_specificity_check.py |

### 1.3 P2a 정의

col2는 STIM_LAB에서 θ_cvd로 렌더링됨 → **HC가 보는 색**. 좋은 필터는 HC가 col2 보고 verbal naming한 색이 sub-08 원본 verbal과 같은 HC color family여야 함.

예: sub-08이 c8 원본을 "진파랑"으로 보고 → HC 등가 = "blue" (260-280°). 따라서 θ_cvd(c8) ≈ 260-280° 영역에 들어와야 함.

### 1.4 c8 magenta anomaly와 collapse penalty 근거

**c8 magenta anomaly**: Sub-08은 c8(magenta, 315°)을 "진파랑"으로 봄. CVD가 c8에 가하는 실제 변환은 약 **−45° 회전**. 그러나 2-component CURRENT formula는 c8(h_base 변환 후)에서 +5°~+10° 작은 양의 δθ만 생성 → θ_cvd(c8) ≈ 320-340° (magenta-pink). MEMORY 2026-04-06 sub-09 c8 z=−5.59 magenta anomaly와 일관.

**Collapse penalty**: raw_behav.md §Cycle 12 (β_s=68, β_c=−38) 행동 보고: C5/C6/C7 "하늘"로 수렴 → 3-way collapse (sub-08 명시: "c5 c6 c7 filter 색이 같음"). c5-c8 pre-image가 좁은 영역(36° span)에 압축됨 → **β_s가 클수록 압축 심해짐**.

수정 채점:
- span < 60° → 감점
- 인접 gap < 12° → 추가 감점
- c5-c8 sub-08 지각의 unique HC family 수 < 4 → 추가 감점

---

## 2. 전체 결과

집계: `0.3·P2a/8 + 0.3·P1/8 + 0.3·P2b/8 + 0.1·boot_frac + (collapse_pen + c8_anomaly_pen)/8`

| 순위 | 후보 | β_s | β_c | P2a | P1 | P2b | span | gap | fam | col_pen | c8! | spec | agg |
|:-:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | **sign_agree** | 10 | +58 | 4.30 | 3.40 | 2.00 | 316.7 | 18.2 | 3 | −0.50 | − | ✓✓ | **+0.401** |
| 2 | **soft_canonical** | 42 | −16 | 3.30 | 5.30 | 4.00 | 61.8 | 12.6 | 1 | −1.50 | **Y** | ~~ | +0.319 |
| 3 | **mid_canonical_cycle14** | 48 | −25 | 3.30 | 5.30 | 4.00 | 54.1 | 12.2 | 1 | −1.70 | **Y** | ✓✓ | +0.298 |
| 4 | Canonical | 38 | −14 | 3.30 | 5.30 | 4.00 | 68.5 | 13.7 | 1 | −1.50 | **Y** | ✗ | +0.274 |
| 5 | scaled_canonical | 50 | −20 | 3.30 | 5.30 | 4.00 | 50.5 | 10.9 | 1 | −1.96 | **Y** | ✓✓ | +0.265 |
| 6 | phase_a_V1 | 50 | −14 | 3.30 | 5.30 | 4.00 | 49.0 | 10.0 | 1 | −2.11 | **Y** | ✓✓ | +0.246 |
| 7 | wide_canonical | 36 | −22 | 2.30 | 5.70 | 3.00 | 74.4 | 16.0 | 1 | −1.50 | **Y** | ✗ | +0.236 |
| 8 | cycle15_opt3 | 58 | −28 | 3.30 | 5.30 | 4.00 | 42.7 | 10.0 | 1 | −2.32 | **Y** | ✓✓ | +0.220 |
| 9 | l_mag | 44 | +58 | 2.90 | 2.70 | 2.00 | 138.2 | 9.2 | 2 | −1.34 | − | ✓✓ | +0.218 |
| 10 | Cycle14 | 58 | −36 | 3.10 | 5.10 | 3.00 | 43.3 | 10.9 | 1 | −2.19 | **Y** | ✓✓ | +0.184 |
| 11 | cycle12_xroi | 68 | −38 | 3.10 | 5.30 | 4.00 | 36.0 | 8.5 | 1 | −2.74 | **Y** | ✓✓ | +0.160 |
| 12 | V4-only_CURRENT | 38 | +7 | 3.50 | 4.30 | 3.00 | 76.8 | 9.8 | 1 | −1.78 | **Y** | ✗ | +0.150 |
| 13 | S_dominant | 56 | −14 | 3.70 | 4.30 | 3.00 | 41.8 | 8.8 | 1 | −2.51 | **Y** | ✓✓ | +0.136 |
| 14 | l_rank | 74 | −60 | 2.10 | 5.10 | 3.00 | 34.2 | 7.5 | 1 | −2.93 | **Y** | ✓✓ | +0.054 |
| 15 | cycle15_opt4 | 70 | −52 | 2.40 | 4.10 | 2.00 | 35.8 | 8.0 | 1 | −2.81 | **Y** | ✓✓ | +0.005 |
| 16 | l_dir | 78 | −60 | 2.90 | 4.10 | 2.00 | 32.4 | 7.1 | 1 | −3.04 | **Y** | ✓✓ | −0.005 |
| 17 | norm_resid | 76 | −60 | 2.10 | 3.30 | 2.00 | 33.3 | 7.3 | 1 | −2.98 | **Y** | ✓✓ | −0.058 |

전체 raw 데이터: `results/phase3_candidates/candidates_summary_v2.json`

**핵심 발견**:
- 17개 후보 중 **14개에서 c8 anomaly 발생** (Y 표시)
- c8 anomaly 없는 후보 3개: sign_agree, l_mag (둘 다 β_c=+58 큰 양수), V4-only는 β_c=+7로 작은데 anomaly 있음 (θ_cvd(c8) = 300.8° = magenta bin)
- 음의 β_c 강할수록 c5-c8 collapse 심함 (Cycle14, cycle12_xroi, l_rank 등 모두 collapse_penalty ≤ −2.0)
- 행동검증된 Canonical도 c8 anomaly + collapse penalty 적용으로 4위

---

## 3. 핵심 트레이드오프

| 영역 | β_c > 0 (예: sign_agree) | β_c < 0 (예: Canonical) |
|---|---|---|
| **c8 col2 매칭** | ✓ (blue family) | ✗ (magenta anomaly) |
| **c1-c7 col2 매칭** | ✗ (대부분 wrong family) | △ (partial, deutan signature 일부) |
| **col4 (P1/P2b)** | weak (3.40 / 2.00) | strong (5.30 / 4.00) |
| **c5-c8 collapse** | mild (3 family) | severe (1 family) |

**단일 (β_s, β_c)로 c8 + c1-c7 + collapse 모두를 잡을 수 없음**. 2-component formula의 구조적 한계.

---

## 4. 추천 Top 3 (시각화)

### Top 1 — `sign_agree` (β_s=10°, β_c=+58°)

![v2 Top 1 sign_agree](results/phase3_candidates/visualizations/v2_top1_sign_agree.png)

| 지표 | 값 |
|---|---|
| norm | 58.9° |
| HC spec | ✓✓ (boot_frac=1.000) |
| P2a / P1 / P2b | 4.30 / 3.40 / 2.00 |
| c5-c8 span | 316.7° |
| Unique families (c5-c8) | 3 |
| **c8 anomaly** | **없음** (θ_cvd(c8)=258°, blue) |
| 집계 | **+0.401 (1위)** |

**해석**: β_s 작고 β_c가 큰 양수 → c8을 large 음의 δθ로 밀어 blue 영역 안착. c8 col2가 진파랑 영역에 정확히 들어와 사용자가 지적한 "col2 cvd 일치" 만족.

**하지만**: c1-c7 col2 대부분 wrong family, col4가 원본과 거의 동일 → 보정 효과 미미 (P1=3.40, P2b=2.00).

**적합도**: c8 단독 검증용으로 적합. 종합 필터로는 부적합.

---

### Top 2 — `soft_canonical` (β_s=42°, β_c=−16°)

![v2 Top 2 soft_canonical](results/phase3_candidates/visualizations/v2_top2_soft_canonical.png)

| 지표 | 값 |
|---|---|
| norm | 44.9° |
| HC spec | ~~ (boot_frac≈0.93, marginal) |
| P2a / P1 / P2b | 3.30 / 5.30 / 4.00 |
| c5-c8 span | 61.8° |
| Unique families | 1 |
| c8 anomaly | **있음** (θ_cvd(c8)=322°, magenta) |
| 집계 | +0.319 (2위) |

**해석**: Canonical(38,−14)을 1.1배 스케일링. Canonical과 거의 동일한 col4 패턴 유지하며 specificity를 marginal까지 올림.

**Pre-image**: c1=18.7°, c2=70.8°, c3=120.7°, c4=168.8°, c5=216.6°, c6=236.5°, c7=249.1°, c8=278.4°
- c5/c6 둘 다 sky family에서 만남 → C5≡C6 collapse 위험 (Canonical과 동일)
- c8 anomaly 유지 (Canonical과 동일)

**적합도**: Canonical 행동 PASS의 안전한 점진 확장.

---

### Top 3 — `mid_canonical_cycle14` (β_s=48°, β_c=−25°)

![v2 Top 3 mid_canonical_cycle14](results/phase3_candidates/visualizations/v2_top3_mid_can_cyc14.png)

| 지표 | 값 |
|---|---|
| norm | 54.1° |
| HC spec | ✓✓ (boot_frac=1.000) |
| P2a / P1 / P2b | 3.30 / 5.30 / 4.00 |
| c5-c8 span | 54.1° |
| Unique families | 1 |
| c8 anomaly | **있음** (θ_cvd(c8)=329°, magenta) |
| 집계 | +0.298 (3위) |

**해석**: Canonical과 Cycle14의 중간점. β_c를 −25°로 강화해 ✓✓ specificity 확보.

**Pre-image**: c1=14.3°, c2=68.8°, c3=120.6°, c4=170.4°, c5=221.5°, c6=238.1°, c7=250.2°, c8=275.7°
- c5-c8 span 54.1° (soft_canonical보다 압축) → collapse 위험 약간 증가
- c6-c7 gap 12.2°로 임계 근처

**적합도**: Canonical 방향 확장 + ✓✓ specificity. soft_canonical 대비 specificity 강하지만 collapse 위험도 큼.

---

### 참고 — Canonical (β_s=38°, β_c=−14°)

![Ref Canonical](results/phase3_candidates/visualizations/ref_canonical.png)

| 지표 | 값 |
|---|---|
| norm | 40.5° |
| HC spec | ✗ (boot_frac=0.517) |
| P2a / P1 / P2b | 3.30 / 5.30 / 4.00 |
| c5-c8 span | 68.5° |
| **행동검증** | **CURRENT formula PASS (behav §3, 2026-04-17)** |

ranking 4위. c5/c6 collapse는 raw_behav.md에서 sub-08이 명시 보고 ("filter C6와 같은 하늘"). 행동 검증된 유일 후보.

---

## 5. 2-Component 한계의 원인과 대안 (이론적 검토)

NotebookLM ColorBlind_comprehensive (110 sources, Machado 2009 / Emery 2021 / Tregillus 2021 / Boehm 2014 / Webster post-receptoral gain / Krauskopf 1982 등 참조)를 통해 검증하여 (h) Two-channel opponent gain 권고.

### 5.1 c8 magenta anomaly의 진짜 원인

**경험적 사실 (raw_behav.md 검증)**:
- Sub-08 자극 315° (magenta) → **진파랑** 지각
- Sub-08 자극 336.9° (pink-magenta, OLD V4-only pre-image) → **핑크빛 보라** 지각 = magenta-family
- 즉 collapse zone은 **305-325° 좁은 영역**에만 국한. 그 밖은 sub-08 지각 보존.

**생리적 원인**: opponent process에서 magenta는 +L−M (red)와 +S 신호 균형 필요. Deutan은 L−M 신호 약화로 magenta에서 **L−M이 작아지고 S가 dominate** → S-pole(deep blue) 방향으로 끌림 (Boehm 2014, Tregillus 2021).

**왜 2-component이 못 잡는가**: 2-component는 **hue 각도 공간에서의 axis-aligned dilation/compression** (S-축 90°와 confusion-축 150°에 정렬된 비균일 압축). hue 각도에만 의존하고 chroma 정보는 무시. 실제 메커니즘은 opponent 2D 평면에서 **L−M 진폭 감소 + S 진폭 보존**이라는 **cartesian amplitude scaling** → hue 각도 변화가 chroma 의존적으로 발생. 1D hue dilation으로는 chroma 의존 효과 표현 불가.

### 5.2 권고 모델 (h) Two-channel opponent gain

**구조** (단일 일관 파이프라인):
```
CIElab θ → LMS (Stockman + Machado Δλ) → opponent [RG, YB]
                                          ↓ gain
                                       [g_LM·RG, g_S·YB]
                                          ↓ atan2
                                       θ_perceived
```

**직관**: 색을 (RG, YB) 2D 벡터로 보고 두 축의 amplitude를 독립적으로 scale. Deutan은 RG 신호가 약하므로 cortex가 g_LM>1로 보상하지만 불완전 → magenta처럼 RG/YB가 모두 큰 색은 RG가 더 약화되어 S축(blue) 쪽으로 끌림 → **c8=진파랑 자동 emerge**, override 불필요.

**핵심 장점**:
- 단일 forward 함수 (patchwork 아님)
- Positive gain은 elliptical scaling → angular sequence 보존 → c5-c8 collapse 구조적 차단
- Closed-form invertible → 기존 pre-image pipeline 그대로 작동
- 생리 근거 강함: Krauskopf 1982 (channel-specific gain) + Tregillus 2021 (BOLD 4× amp) + Boehm 2014 (RG 선택적 expansion) + Webster

**파라미터**: (g_LM, g_S) 자유, Δλ=14 nm 고정 (deutan population prior).

상세 수학·예시·검증 체크리스트: `results/phase3_candidates/opponent_gain_fit/REPORT.md`

### 5.2.1 Sub-08 피팅 결과 — v1 (hue-only) vs v2 (joint hue+chroma)

| | v1 (hue-only loss) | v2 (joint vector loss, Δλ free) |
|---|---|---|
| Best params | Δλ=14 fixed, (g_LM, g_S)=(0.45, 1.15) | Δλ=0, (g_LM, g_S)=(0.90, 1.00) |
| Scale identifiability | ✗ (27 cells tied, ratio만 식별) | ✓ (unique optimum) |
| Joint loss | 0.0177 | **0.0069** (v1 대비 60% 감소) |
| c8 col2 → sub-08 actual | violet → 진파랑 (family partial ✓) | magenta → 진파랑 (mismatch ✗) |
| c4 col2 → sub-08 actual | yellow-green → 노랑 (mismatch) | green → 노랑 (mismatch) |
| c1 col2 → sub-08 actual | magenta → 분홍빨강 (mismatch) | red → 분홍빨강 (close, 7° off) |
| Cardinal 색 보존 | 약함 | 강함 (near-identity) |
| Anomaly (c8) 처리 | 강함 | **실패** |

![v2 fit](results/phase3_candidates/opponent_gain_fit/visualization_v2.png)

**v2 결과 해석**: Joint loss는 chroma 정보까지 활용해 scale identifiability 회복했지만, **최적 fit이 near-identity (Δλ≈0, g≈1)로 수렴**. 이는 39 anchor 중 대다수가 sub-08의 "정상 인지" 영역(c1·c2·c3·c6·c7 등 sub-08 verbal이 HC equivalent와 가까운 색)에 분포하기 때문. 소수의 anomaly anchor (c4 노랑, c5 아이보리, c8 진파랑)는 평균 loss에 묻혀 fit을 끌어당기지 못함.

**구조적 발견 — 2-param diagonal gain의 fundamental limit**:

두 fit이 정반대 방향으로 수렴한 것이 핵심 진단:
- v1 (hue-only, anchor 무가중): anomaly 강조, cardinals 희생 (g_LM=0.45)
- v2 (joint, anchor 무가중): cardinals 강조, anomaly 희생 (g_LM=0.90)

같은 모델·같은 데이터에서 loss 함수 변경만으로 결과가 극단으로 바뀜 → **두 요구(cardinal 보존 + anomaly 처리)가 single (g_LM, g_S)로 동시 만족 불가**. Path A의 scale 식별 자체는 성공했으나 **모델 자체의 표현력 부족**이 노출됨.

**Filter 관점 함의**:
- v1 filter: c8 보정 가능성 있으나 c1/c4 distort
- v2 filter: cardinals 보존되나 c8 보정 효과 없음
- 둘 다 Canonical 2-comp 대체 부적합

**다음 경로**:
- **경로 B (h+ extension)**: bias 항 또는 full 2×2 matrix로 자유도 추가. cardinal + anomaly 동시 fit 시도. 단 4-param이 8색 데이터에 overfit 위험.
- **경로 C (direct filter optimization)**: forward fit 포기, pre-image perception matching 직접 최대화. 8개 데이터 포인트만 사용해도 filter quality에 직접 튜닝.
- **경로 D (model class 종결)**: Path A 결과가 (h)의 표현력 한계를 증명 → Canonical 유지, (h)는 mechanism diagnostic까지로 정리.

상세 데이터: `results/phase3_candidates/opponent_gain_fit/{fit_result_v2,score_grid_v2}.json`

### 5.3 권고

**Phase 2 closure**: Canonical (β_s=38, β_c=−14) 유지. 행동 PASS 보유, 2-comp 한계 명시 후 Phase 3 진입.

**Phase 3 모델 확장**: **Model (h)는 mechanism diagnostic으로 활용** (Phase 2 canonical 필터 교체 아님).
- 피팅 결과(§5.2.1): sub-08의 cortical g_S/g_LM ≈ 2.5 (S-channel 우세) 정량 추정
- c8 anomaly mechanism 검증: gain 비대칭이 magenta→blue 끌림을 emergent하게 재현
- 한계: cardinal 색 (c1/c4/c6) 정합성 떨어짐, hue-only loss로 scale identifiability 없음 → filter 교체 후보 아님

**Phase 3 추가 검증 옵션**:
- (h) hue-amplitude joint loss (chroma 손실 항 추가) — scale identifiability 회복 시도
- 행동 검증: c8 variant viz (290°/300°/310°/337°/351°)로 sub-08 perception 직접 측정 → (h) S-dominance 가설 falsification

---

## 6. 한계

- HC naming function bin 경계(예: 295° = magenta vs violet)는 STIM_LAB 8-anchor 보간 — 정밀 측정값 아님
- collapse penalty 가중치(span<60°/30, gap<12°/8, family<4×0.5)는 자의적
- sub-08 verbal의 HC 등가 색 매핑(예: "더 진한 하늘" → sky)도 정성적
- 17개 후보의 절반 이상이 c8 anomaly Y로 동일 등급이라 ranking 분해능 낮음
- L−M threshold squashing 제안은 NotebookLM 이론적 검토에 의존 — 실제 fit으로 검증 필요
- **결정적 근거는 여전히 행동 검증**

---

## Appendix — Files

| 파일 | 내용 |
|---|---|
| `scripts/phase3_candidate_analysis_v2.py` | 채점 로직 (HC naming + collapse + c8 anomaly) |
| `scripts/phase3_render_top_candidates.py` | Top 3 + Canonical 4-column 시각화 |
| `scripts/forward_models/opponent_gain.py` | (h) Two-channel opponent gain 모델 |
| `scripts/phase3_fit_opponent_gain.py` | sub-08 (g_LM, g_S) 격자 피팅 |
| `scripts/phase3_render_opponent_gain.py` | (h) 모델 4-column 시각화 |
| `results/phase3_candidates/candidates_summary_v2.json` | raw 점수 + per-color predictions |
| `results/phase3_candidates/perception_map_v2.json` | 39 (각도, 지각) anchor |
| `results/phase3_candidates/visualizations/v2_top{1,2,3}_*.png` | Top 3 시각화 |
| `results/phase3_candidates/visualizations/ref_canonical.png` | Reference |
| `results/phase3_candidates/opponent_gain_fit/{fit_result,score_grid}.json` | (h) v1 hue-only fit |
| `results/phase3_candidates/opponent_gain_fit/{fit_result_v2,score_grid_v2}.json` | (h) v2 joint hue+chroma fit |
| `results/phase3_candidates/opponent_gain_fit/visualization.png` | v1 4-column 시각화 |
| `results/phase3_candidates/opponent_gain_fit/visualization_v2.png` | v2 4-column 시각화 (near-identity 결과) |
| `scripts/phase3_fit_opponent_gain_v2.py` | Joint hue+chroma loss fit script |
| `scripts/phase3_render_opponent_gain_v2.py` | v2 시각화 |

## References (NotebookLM citations)

- Emery KJ et al. (2021). *Color perception and compensation in color deficiencies assessed with hue scaling*. Vision Research 183:1-15. (Hue scaling, AT phase rotation 21.4° "merely descriptive")
- Machado G et al. (2009). 1-way cone-shift CVD simulation; Stockman LMS → opponent transform.
- **Tregillus K et al. (2021)**. BOLD signal 4× amplification for L-M contrast in V2/V3 of AT observers. (Channel-specific post-receptoral gain)
- **Boehm AE, MacLeod DI, Bosten JM (2014)**. Deuteranomal threshold restoration 38% vs color difference 86% → selective RG axis expansion. (Independent gain on RG vs YB)
- Basim et al. (2025). Multiplicative sensory gain modeling for AT compensation.
- **Krauskopf, Williams, Heeley (1982)**. Chromatic contrast adaptation: independent threshold elevation per cardinal axis. (Foundational evidence for two-channel dissociable gain)
- Webster et al. Post-receptoral gain control framework for adaptive color vision.
- Stockman & Sharpe (2000). L/M cone fundamentals; ~30nm peak separation in normal trichromat.
- Conway (2001). V1 neuron S−LM / L−SM channel modeling.
- Ingling & Tsou (1977). LMS → opponent suprathreshold 변환.
