# Neural-primary Filter Design — α_neural sweep + Dissociation Map

**작성**: 2026-05-13
**Paper 주제**: "fMRI-informed CVD filter design"
**Framework 방향**: Neural-primary filter selection with physiological regularization
(literature prior는 implausible 영역만 차단)

---

## Loss formulation

```
L = α_neural · L_neural_composite
  + α_phys   · L_physiological_prior
  + α_amp    · 50 · Tikh

  α_phys = (1 − α_neural) · 0.67
  α_amp  = (1 − α_neural) · 0.33

L_neural_composite =
    0.3 · L_V1ΔRDM_anchor(β_s)        ← retinal cone-shift, V1 ΔRDM bootstrap
  + 0.3 · L_V4LOCO2c_anchor(β_c)      ← cortical confusion-axis, V4 LOCO 2-comp
  + 0.2 · L_V4_RDM_shape              ← V4 vuln_sim ↔ vuln_cvd cosine (scale-invariant)
  + 0.2 · L_local_vulnerability       ← l_topk Jaccard (top-K vulnerable colors)

L_physiological_prior =
    0.5 · weak_sign(β_c, family)       ← Brettel sign — very low weight (sanity check only)
  + 0.5 · weak_norm_plausibility       ← Tregillus ceiling — penalize ‖β‖ > 50°

Tikh = (β_s² + β_c²) / 32400          ← amplitude regularizer
```

각 항 정의:
- `L_V1ΔRDM_anchor(β_s) = ((β_s − β_s^V1ΔRDM[subject]) / 10)²`
- `L_V4LOCO2c_anchor(β_c) = ((β_c − β_c^V4LOCO2c[subject]) / 15)²`
- `L_V4_RDM_shape = (1 − cos(vuln_sim, vuln_cvd)) / 2`
- `L_local_vulnerability = 1 − |top-3(vuln_sim) ∩ top-3(vuln_cvd)| / 3`
- `weak_sign(β_c, family) = max(0, −β_c · s_fam / 50)²` (s_fam: deutan +1, protan −1)
- `weak_norm_plausibility = max(0, (‖β‖ − 50)/10)²`

---

## α_neural sweep — empirical 결과

### sub-08 deutan (V1 anchor=20°, V4 anchor=−14°)

| α_neural | argmin (β_s, β_c) | P2a | exact | ‖β‖ | dist→P2a-max | dist→anchor |
|---:|---|---:|---:|---:|---:|---:|
| 0.3 | (14, −8) | **0.400** | 1/8 | 16.1 | 43.7° | 8.5° |
| 0.5 | (18, −10) | 0.362 | 1/8 | 20.6 | 44.7° | 4.5° |
| 0.7 | (18, −12) | 0.362 | 1/8 | 21.6 | 46.7° | 2.8° |
| 0.9 | (20, −14) | 0.263 | 1/8 | 24.4 | 48.4° | 0.0° |

### sub-09 protan (V1 anchor=23°, V4 anchor=−22°)

| α_neural | argmin (β_s, β_c) | P2a | exact | ‖β‖ | dist→P2a-max | dist→anchor |
|---:|---|---:|---:|---:|---:|---:|
| 0.3 | (16, −12) | 0.787 | 4/8 | 20.0 | 11.3° | 12.2° |
| 0.5 | (20, −16) | **0.887** | **6/8** | 25.6 | 5.7° | 6.7° |
| 0.7 | (22, −18) | **0.887** | **6/8** | 28.4 | **2.8°** | 4.1° |
| 0.9 | (22, −22) | **0.887** | **6/8** | 31.1 | **2.8°** | 1.0° |

→ **α_neural ≥ 0.5에서 sub-09 BEST 수렴 + P2a-max에 2.8° 도달**

---

## Three-model comparison (α_neural=0.7)

| Subject | Model 1 Bayesian (α=0.3) | Model 2 Neural-primary (α_n=0.7) | Model 3 P2a-max oracle |
|---|---|---|---|
| **sub-08** | (22, +18) P2a=0.550 | (18, **−12**) P2a=0.362 | (26, +34) P2a=0.613 |
| **sub-09** | (22, −16) P2a=0.887 | (22, **−18**) **P2a=0.887** | (24, −20) P2a=0.950 |

### Sub-09 — CONVERGE (filter validated)

- Neural-primary (22, −18) ≈ Bayesian (22, −16) ≈ P2a-max (24, −20)
- 모두 같은 quadrant, 모두 같은 sign, distance ≤ 6°
- **신경 데이터가 행동 optimum을 (literature prior 없이) 독립적으로 회복**
- Per-color: c1 red, c2 orange, c3 yellow, c6 sky, c7 blue, c8 magenta — 6/8 exact

### Sub-08 — DIVERGE (dissociation finding)

- Neural-primary (18, **−12**): β_c<0 (V4 LOCO anchor 방향)
- Bayesian (22, **+18**): β_c>0 (Brettel prior 방향)
- P2a-max (26, **+34**): β_c>0 (behavioral target 방향)
- **신경 데이터 일관되게 β_c<0, 행동 데이터는 β_c>0** → real dissociation
- α_neural 어떤 값에서도 sub-08 P2a-max 도달 불가

---

## Sub-08 dissociation의 5가지 가능한 원인 (배제 작업 필요)

1. **Verbal report semantic bias** — `SUB08_ORIGINAL_HC_EQUIV`는 verbal report 기반, neural과 다른 layer
2. **V4 LOCO 2-comp overfit** — sub-08 hV4 voxel count 작음 (small ROI)
3. **Axis convention 180° flip** — Sign artifact 가능성 (Stockman/CIELab 모두 같은 결과지만 third convention 확인 필요)
4. **Atypical CVD profile** — sub-08이 non-canonical deutan일 가능성 (anomalous trichromat?)
5. **Post-V4 transformation** — 5th-layer (LO, VO) processing이 V4 representation을 reverse

→ **검증 단계 (a)/(b)/(d) 권장** (UNIFIED_LOSS_RECOMMENDATION.md §8):
   - (a) V4 LOCO 2-comp β_c CI bootstrap — sign 안정성
   - (b) Axis 180° flip 독립 test — convention artifact 배제
   - (d) Bayesian-vs-Neural-primary HC-permutation specificity 비교

---

## Paper narrative (사용자 권장 기반)

### Primary claim (sub-09)
> "fMRI neural geometry로부터 individualized CVD correction filter를 직접 추정.
> sub-09 protan의 V1 ΔRDM + V4 LOCO 신경 anchor가 어떤 literature constant 없이도
> behavioral P2a-restoration target을 2.8° 이내로 회복."

### Secondary finding (sub-08)
> "동일 framework가 sub-08 deutan에서는 신경-perceptual dissociation을 드러냄.
> V1/V4 신경 측정 모두 β_c<0를 일관되게 가리키나 P2a-restoration target은 β_c>0.
> 이는 deutan-specific neural-vs-perceptual representation divergence 가능성을 시사
> (검증 단계 (a)/(b)/(d) 후행 필요)."

### Framework claim
> "신경 기반 filter는 행동 optimum을 항상 맞추는 게 아니라,
> 행동 optimum이 신경 표상 복원과 일치하는지 여부를 판별한다."

---

## 권장 Path 결정

| 옵션 | 채택 시 paper 구조 |
|---|---|
| **Path A — Bayesian framework 유지** | Sub-08 filter 작동 (P2a 0.550), 단 Brettel prior가 신경 evidence 반전. Reviewer 공격 surface 큼. |
| **Path B — Neural-primary 채택** (권장) | Sub-09 filter 작동 + literature 복원. Sub-08은 dissociation finding으로 보고. Paper 주제가 "filter design + dissociation discovery"로 확장. |
| **Path C — 세 모델 모두 보고 (recommended)** | Bayesian / Neural-primary / P2a-max oracle 비교. Filter는 Neural-primary primary, Bayesian은 alternative analysis. Sub-08 dissociation은 framework-independent finding. |

→ **Path C가 가장 honest + scientific impact 강함**.
   사용자 권장 narrative와 정확히 일치.

---

## Next steps (사용자 결정 대기)

### 즉시 가능 (Path C 채택 시)
1. SUMMARY.md primary BEST = Neural-primary (α_n=0.7)으로 갱신 권장
2. Bayesian framework는 "alternative analysis"로 강등
3. Dissociation map figure를 paper main figure로 채택

### 후행 (검증 필요)
1. V4 LOCO 2-comp β_c CI bootstrap (sub-08 sign 안정성)
2. Axis 180° flip 독립 검증
3. HC-permutation specificity 비교
4. Phase 3 behavioral validation 트리거 (sub-09 Neural-primary BEST (22, −18))

### 보류
- 새 BEST 즉시 선언 보류 (사용자 명시적 승인 대기)
- Phase 3 trigger 보류 (검증 단계 완료 후)

---

## 산출

- `results/neural_primary/neural_primary_results.json` — α_neural sweep raw data
- `results/neural_primary/dissociation_map.{png,pdf}` — 6-panel 시각화
- `results/neural_primary/REPORT.md` — 이 문서
