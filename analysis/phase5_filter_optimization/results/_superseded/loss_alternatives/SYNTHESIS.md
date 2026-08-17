# Loss Alternatives — 종합 분석

**작성**: 2026-05-13
**기준**: CLAUDE.md §0 갱신 반영 (behavioral discriminability-PASS 보류, P2a-restoration 기준)

---

## 3개 핵심 finding

### 1. L_Brettel 신경 복원 불가 — **parameterization conflict**

| Quantity | Space | Convention | sub-08 value | sub-09 value |
|---|---|---|---|---|
| Forward filter β_c | stimulus-space | θ_conf = 150° fixed | +12° (BEST) | −10° (BEST) |
| V1 ΔRDM β_c (2-comp bootstrap) | cortical opponent | phase fitted | −18° (CI excl 0) | +3° (CI incl 0) |
| 2-comp hV4 LOCO β_c | cortical opponent | phase fitted | −14° | −22° |

**두 quantities는 같은 이름이지만 incompatible parameterization**. Direct anchor 시 sub-08 P2a 0.263 폭락 (V4 V1ΔRDM anchor, V5 cortical anchor 모두 sub-08 wrong sign).

→ **"신경 데이터로 L_Brettel 복원" narrative는 부정확**. V1 ΔRDM β_c는 forward filter β_c의 proxy가 아니라 independent cortical measurement.

### 2. V6 (Family-asymm Tikh) ≡ V1 FULL — **notational equivalence**

**13개 variant sweep 결과** (joint P2a 순위):

| 순위 | Variant | sub-08 (β_s, β_c) | sub-09 (β_s, β_c) | joint P2a |
|---|---|---|---|---|
| 1 | **V1 FULL** (current BEST) | (22, +12) | (22, −10) | **0.719** |
| 1 | **V6 Family-asymm Tikh (no Brettel)** | (22, +12) | (22, −10) | **0.719** |
| 3 | V7 Single L_lit | (22, +10) | (22, +10) | 0.656 |
| 4 | V12 Family-asymm + Emery only | (20, 0) | (20, 0) | 0.644 |
| 8 | V5 2-comp cortical anchor | (22, −14) | (20, −18) | 0.575 |
| 12 | V4 V1 ΔRDM anchor | (20, −18) | (22, +4) | 0.525 |
| 13 | V10 Pure neural-only | (0, −18) | (0, +2) | 0.494 |

**V6와 V1 FULL은 동일한 BEST 좌표 + 동일 P2a 산출**:
- V6 = `0.3·L_ccc + 0.7·(0.5·L_E + 0.5·L_T) + 0.1·50·Tikh_asymm`
- Tikh_asymm: wrong-sign β_c에 4× heavier penalty (family-aware)
- V1 FULL은 explicit L_Brettel 항으로 같은 효과 달성

**그러나**:
- V6의 Tikh_asymm도 **implicit Brettel-direction assumption** 내장 (deutan β_c>0 favored)
- 같은 family-aware 정보, 다른 표현 — citation overhead만 감소
- "Brettel 의존성 제거"는 **부정확한 주장**

→ V6 채택은 **notational refactor**: citation 정리 + 다른 axis 규약 의존 회피. Performance는 same.

### 3. Tregillus 28° — **sub-08 P2a-max 도달 불가의 structural ceiling**

P2a-max coordinates (CLAUDE.md §3, 갱신된 truth target):

| Subject | P2a-max (β_s, β_c) | norm | Bayesian BEST norm | gap |
|---|---|---|---|---|
| sub-08 | (26, +34) | **40.3°** | 25.1° (FULL) | **−15° 미달** |
| sub-09 | (24, −20) | 31.2° | 24.2° (FULL) | −7° 미달 |

- Tregillus anchor `‖(β_s, β_c)‖ ≈ 27.82°` → 모든 variant BEST norm이 ~25–28°에 cluster
- **sub-08 P2a-max norm 40°는 framework 구조적으로 도달 불가능**
- sub-09 P2a-max norm 31°는 Tregillus 근처 → 도달 가능 (FULL P2a=0.887 vs P2a-max 0.950)

**Sign agreement at P2a-max** (Brettel valid):
- sub-08 P2a-max β_c=+34 > 0 → Brettel deutan expected
- sub-09 P2a-max β_c=−20 < 0 → Brettel protan expected
- → **Brettel direction은 P2a-max에서 valid**; BEST는 sign 맞지만 magnitude 부족

---

## 권장사항 + open decisions

### 채택 검토 가능 (notational)

1. **V6 swap** (FULL → Family-asymm Tikh)
   - Citation 부담 감소 (Brettel 1997 직접 인용 회피)
   - Axis convention 의존성 회피
   - Performance same
   - **단**: family-aware 가정 동일 → "Brettel 의존 제거" 주장 금지

### 사용자 의사결정 필요

2. **Tregillus anchor widening** vs **Bayesian compromise 유지**
   - (a) Tregillus 1.5× = 32° 또는 1.8× = 38° → sub-08 P2a-max에 더 접근
     - 단 Tregillus 2021 literature 범위 (20–40%) 상한 근처
     - sub-09는 over-pull될 위험
   - (b) 현재 framework 유지 → sub-08 P2a 0.550 cap 인정
     - Honest: "Bayesian framework는 양 피험자에 정확한 P2a-max 도달이 아니라 literature-anchored 좌표를 선택"
     - sub-08 P2a-max (26, +34)는 framework가 도달 못함을 paper에 explicit 명시

### 거부 (이미 확인)

3. **L_Brettel을 V1 ΔRDM β_c로 대체** — parameterization conflict, sub-08 P2a 폭락
4. **Brettel sign REVERSED** — Tregillus cortical overshoot 가설, empirical 불일치
5. **Pure neural-anchor (literature prior 제거)** — joint P2a 0.494, framework 작동 안 함

---

## Scientific impact + validity 평가

| Formulation | Citations | Narrative clarity | Sub-08 P2a | Sub-09 P2a | Validity 우려 |
|---|---|---|---|---|---|
| V1 FULL | Emery + Tregillus + Brettel + Tikh | Standard CVD literature path | 0.550 | 0.887 | Brettel axis convention 의존 |
| **V6 Family-asymm Tikh** | Emery + Tregillus + Tikh | family-aware design, less citation overhead | 0.550 | 0.887 | implicit family prior (same info, less explicit) |
| V5 2-comp cortical anchor | Emery + Tregillus + 2-comp model | hV4 신경 anchor 활용 | 0.263 | 0.887 | **sub-08 fail** |

→ **V1 FULL or V6 둘 다 valid choice**. V6가 narrative cleaner이나 scientific content 동일.

---

## 결정적 한계 (paper에 명시 필요)

1. **Sub-08 P2a-max (26, +34) 도달 불가**: Bayesian framework는 norm을 Tregillus 28°로 anchor → sub-08 norm 40°에 미달
2. **V1 ΔRDM β_c sign과 forward filter β_c sign 직접 비교 부적절**: parameterization 다름
3. **Brettel sign penalty의 axis convention 의존성**: OLD 150° vs CIELab 175.7°/11.8° 결과 동일하지만 reviewer가 axis 선택 정당화 요구 시 부담

---

## 산출

- `results/loss_alternatives/loss_alternatives_results.json` — 13 variant raw data
- `results/loss_alternatives/SYNTHESIS.md` — 이 문서

Sources:
- [Tregillus 2021 Current Biology — Color Compensation in Anomalous Trichromats Assessed with fMRI](https://www.sciencedirect.com/science/article/pii/S0960982220317516)
- [Tregillus 2021 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7946702/)
- [Brouwer & Heeger 2009 — Decoding and Reconstructing Color](https://pmc.ncbi.nlm.nih.gov/articles/PMC2799419/)
- [Bannert & Bartels 2018 — Neural representations of perceptual color experience PNAS](https://www.pnas.org/doi/10.1073/pnas.1911041117)
