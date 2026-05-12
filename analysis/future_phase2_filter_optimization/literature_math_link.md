# 문헌 연결 — 수학 기반 재시도

> **목적**: 본 연구의 추정 파라미터(β_s, β_c, Δλ, g)와 선행 문헌(Emery 2021, Tregillus 2021, Machado 2009, Brettel 1997)의 수치 사이에 어떤 수학적 비교가 가능한지/불가능한지를 동료에게 공유하기 위한 정리.
>
> **배경 모순** (당시): 두 내부 문서가 서로 다른 입장을 취하고 있음.
> - `future_phase2_notion.md` §6-3, §9 → "다른 물리량 → 수치 비교 무의미"
> - `simulation_recoverability_behavior.md` Abstract → "mean β_s 21.5° ≈ Emery 21.4°"
>
> 본 문서는 **수학적 도출과 검증 가능 조건을 명시**하여 두 입장 중 어느 쪽이 옳은지 판가름하는 기준을 제공.

> ## ⚠️ 2026-05-06 업데이트 — L2 부분 수정 (수치 비교는 여전히 부적절, 구조 일치만 강화)
>
> **[L2 부분 수정]** NotebookLM 재확인(2026-05-06)으로 다음 두 사실 확인:
>
> - **Factor 4의 실제 구조**: R/G 축(0°/180°) loading≈0, S축(90°/270°) loading 최대, B와 Y 반위상 → **β_s·sin(θ)와 구조적으로 동일**. 이전 2026-05-04 box의 "uniform rotation" 특성화는 부정확.
> - **Emery 2021은 CVD 연구**: 10 AT (7 deutan + 3 protan) vs 26 NT 비교. 우리 연구와 동일 대상군.
>
> **그러나 수치 비교(21.4° vs β_s mean 21.5°)의 부적절성은 별개 이유로 여전히 유효**:
>
> 1. **β_c 효과 무시 문제**: "mean β_s = 21.5° ≈ Emery 21.4°"는 forward 유도식 `|Δφ_BY| = |β_s + β_c·sin(θ_conf)|`에서 β_c 항을 제거한 결과. β_c를 포함하면:
>    - sub-08 V4 (β_s=38, β_c=−14): |Δφ_BY| = **31°** (Emery 대비 +9.6°)
>    - sub-09 V4 (β_s=6, β_c=−22): |Δφ_BY| = **0.06°** (β_c가 β_s를 거의 상쇄, Emery 대비 −21.3°)
>    - 평균 V4 = 15.5° ≠ 21.4°
> 2. **ROI 의존성**: V4 LOCO 평균 15.5°, V1 LOCO 평균 **43.5°** — 동일 피험자에서 ROI 선택만으로 예측이 28° 변동. 좌표계 보정으로는 해결 불가 (rotation은 magnitude 보존).
> 3. **Group vs individual**: Emery 21.4°는 10 AT의 group mean. 우리는 2 CVD individual. 개체 분산을 고려하면 비교 자체의 통계적 의미 약함.
>
> **결론 (수정)**:
> - ✅ **구조 일치** (Factor 4 구조 = β_s·sin(θ)): 확인. **physiological grounding 근거**로 유지.
> - ❌ **수치 수렴** (21.4° ≈ 21.5°): β_c 무시한 우연. forward model 정확히 적용하면 ROI에 따라 0.06°~44°로 산포.
> - **Status**: 2026-05-04 "Closed — Structural family only"가 결론적으로 옳음. 단 그 근거는 "functional form 차이"가 아니라 "β_c 항 + ROI 의존성"으로 정정.
>
> **이 결론은 project memory `feedback_physiological_grounding.md`("literature connection = model STRUCTURE grounding, not parameter VALUE convergence")와 일치.**
>
> 2. **L3**: Tregillus 자극은 **2 cardinal axes (L-vs-M, S-vs-LM) modulation only**, 우리 자극은 8-hue ring → **stimulus space가 다름**. 또한 Tregillus DV는 univariate ROI-mean β (CRF Naka-Rushton scalar), 우리 DV는 multivariate voxel pattern. **세 가지 dimensional mismatch (자극 공간 + observable + functional form)**로 직접 비교 불가능. 본 문서의 "변환 불가" 결론은 유효하나 **Tregillus 자극이 hue manifold가 아니라는 점이 누락**되어 있음 — `AF = f(g)` 같은 conditional 가정 자체가 구조적으로 부적절.
>
> 3. **새 framework**: `index.md` §2-2의 "Functional form distinction" 표 + `presentation/claude_in_ppt_prompts_meeting.md` Slide 6의 "Three different mathematical observables" 비교가 현재 정본. 본 문서는 그 결론에 도달한 **derivation 기록 (audit trail)**로 보존.

---

## 0. Status 매트릭스

| 연결 시도 | 본 연구 양 | 문헌 양 | 직접 비교 가능? | 가정하 비교 가능? | 현 상태 | 다음 액션 |
|---|---|---|:---:|:---:|---|---|
| **L1. Machado Δλ** | sub-08 2.0 nm / sub-09 13.5 nm | severity range 1–14 nm | ✅ | — | **확정 — 범위 일치** | 추가 작업 없음 |
| **L2. β_s ↔ Emery 21.4°** | V4 LOCO: sub-08=31°, sub-09=0.06° (β_c 포함). V1 LOCO: 43°/44° | B-Y phase shift Δφ_BY = 21.4° (CVD vs NT, 10 AT group mean) | ❌ | ❌ (β_c 포함 시 ROI에 따라 0~44° 산포) | **Closed (2026-05-04) — 결론 유지, 근거 정정 (functional form 동일, 그러나 β_c·sin(θ_conf) + ROI dependence가 수치 수렴 차단)** | 없음 (구조 일치는 §L2 본문, physiological grounding) |
| **L3. g ↔ Tregillus AF** | sub-08 hV4 g=+2.25, sub-09 g=−1.10 | AF V1=2.94, V2v=6.39, V3v=7.82 | ❌ | ❌ | **Closed — 변환 불가** (자극 공간 + observable + 비선형성 3중 mismatch) | 없음 |
| **L4. β_c ↔ Brettel confusion** | sub-08 β_c=−14°, sub-09 β_c≈0 | confusion line angle 16°/150° | △ (축 정렬) | — | **구조적 근거만** | severity-dependent 검증 |
| **L5. hV4 ROI ↔ B&H 2009 / Kuriki 2025** | V4가 LOCO 유일 통과 | V4/VO1만 novel-color 재구성 | ✅ (정성적) | — | **확정** | — |

**핵심 결론 미리보기 (2026-05-06 업데이트)**: L1, L5만 직접 비교 가능. **L2는 부분 수정** — Factor 4 구조가 β_s·sin(θ)와 동일 (✓) + Emery는 CVD 연구 (✓). 그러나 **수치 비교(21.4° vs 21.5°)는 β_c·sin(θ_conf) 항을 무시한 결과**, 정확한 forward 적용 시 ROI에 따라 0.06°~44° 산포. "구조 일치는 grounding evidence, 수치 수렴은 우연" — closed 결론은 유지하되 근거 정정. L3는 closed. L4는 모델 구조 근거.

---

## L1. Machado Δλ — 유일한 직접 비교

### 수학 형태
같은 모델: `θ' = machado_shifted_hue(Δλ, family)` ← 본 연구와 Machado 2009가 동일 cone fundamental interpolation. **단위, 의미, 산출 방식 모두 동일**.

### 비교
| Subject | 본 연구 Δλ (LOCO fit) | Machado severity range | 판정 |
|---|:---:|---|:---:|
| sub-08 deutan | 2.0 nm | very mild 1–4 nm | ✅ 범위 내 |
| sub-09 protan | 13.5 nm | moderate–severe 9–14 nm | ✅ 범위 내 |
| sub-10 normal | 0 nm | normal | ✅ 정상 |

### 한계
- Rayleigh match에서의 Δλ ≠ fMRI LOCO에서 추정한 Δλ. **개인 정확값 일치는 주장 불가, 범위 일치만 주장**.
- sub-09는 §5-6 pre-image에서 4/8 FAIL → 적합도 ρ=0.762이지만 invertibility 실패. severity classification은 정합하나 모델 적용 가능성은 별개.

### Status
**Closed.** notion.md §6-1 표현이 그대로 유효.

---

## L2. β_s ↔ Emery 21.4° — 가장 논쟁적

### 두 양의 정의

**본 연구 (cortical mapping)**:
$$\theta'(\theta) = \theta + \beta_s \cos(\theta - 90°) + \beta_c \cos(\theta - \theta_{conf})$$

→ β_s [°] = stimulus θ가 percept θ'로 매핑될 때 **B-Y 축(90°) 부근에서의 displacement amplitude**.

**Emery 2021 (PMC8058247) — half-rectified cosine response fit**:
$$r_k(\theta) = A_k \max\!\left(0,\ \cos\!\left(\tfrac{2\pi}{P_k}(\theta - \phi_k)\right)\right),\quad k\in\{R,G,B,Y\}$$

→ B-Y 채널 phase parameter $\phi_{BY}$: normal 127.5° → AT 106.1°, 차이 **Δφ_BY = 21.4°**. 이는 **stimulus → response peak의 위치 회전**.

### 비교 가능 조건 (forward derivation)

Emery 함수가 percept 공간에서 fixed cosine bank ($\phi_k^{percept}$ 고정)라는 가정 하에:
$$r_k(\theta) = \max(0,\ \cos(\theta'(\theta) - \phi_k^{percept}))$$

피크 위치 $\phi_k^{stim} = \theta'^{-1}(\phi_k^{percept})$ → small-angle approximation:
$$\phi_k^{stim} \approx \phi_k^{percept} - \beta_s \cos(\phi_k^{percept} - 90°) - \beta_c \cos(\phi_k^{percept} - \theta_{conf})$$

B-Y 채널 ($\phi^{percept} = 90°$):
$$\boxed{\Delta\phi_{BY} = -\beta_s - \beta_c \sin(\theta_{conf})}$$

### 본 연구 추정값 대입

| Subject | β_s | β_c | θ_conf | β_c·sin(θ_conf) | 예측 Δφ_BY | Emery 21.4° 일치? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| sub-08 deutan | 20° | −14° | 150° | −14·sin150° ≈ −7.0° | **−13.0°** | 부분 (β_c 보정 후 약 38% 작음) |
| sub-09 protan | 23° | +3° | 16° | +3·sin16° ≈ +0.83° | **−23.8°** | ✅ 21.4° 매우 근접 |

**관찰**:
1. **sub-09에서만 β_s ≈ |Δφ_BY| 단순 근사 성립** (β_c 기여 < 1°).
2. sub-08은 β_c·sin(θ_conf) 기여가 7°로 무시 불가 → 단순 "β_s ≈ Emery 21.4°" 비교는 misleading.
3. Mean 21.5°가 21.4°에 일치하는 것은 sub-08·sub-09가 우연히 평균낸 결과이며, 두 명 각자에 대한 검증을 통과하지 않음.

### 검증 절차 (forward simulation)

```
입력: 추정 (β_s, β_c, θ_conf) per subject
1. 360 stimulus θ에 대해 θ'(θ) generate
2. percept 공간에 4-channel half-rectified cosine bank 배치 (φ_k^percept = R 0°, Y 90°, G 180°, B 270°)
3. r_k(θ) = max(0, cos(θ'(θ) - φ_k^percept)) 계산
4. r_BY(θ) = r_B - r_Y 에 cosine least-squares fit → φ_BY^sim 추출
5. Δφ_BY^sim = φ_BY^sim(이 subject) - φ_BY^sim(β_s=β_c=0)

귀무가설 검정:
  (β_s, β_c) ~ Uniform[-30°,30°]² 무작위 1000회 → φ_BY^sim 분포
  본 연구 추정값의 percentile p < 0.05면 본질적 일치, 그 외 우연
```

### Status (2026-05-06 부분 수정 — 결론 유지, 근거 정정)
**Closed 결론은 유지, "functional form 차이" 대신 "β_c + ROI 의존성"으로 근거 정정.**

**확인된 사실 (NotebookLM 2026-05-06)**:
- Factor 4는 R/G(0°/180°) loading≈0, B/Y(90°/270°) peak, Blue↔Yellow 반위상 → β_s·sin(θ)와 **동일한 1st-harmonic non-uniform warp 구조**.
- Emery 2021은 CVD 연구 (10 AT: 7 deutan + 3 protan vs 26 NT).

**그러나 수치 비교(21.4° vs 21.5°)는 부적절 — 새로운 정량 분석으로 확정**:

| 피험자/ROI | β_s | β_c | θ_conf | β_c·sin(θ_conf) | 예측 \|Δφ_BY\| | Emery 21.4° |
|---|---:|---:|---:|---:|---:|---|
| sub-08 V4 LOCO (canonical) | 38° | −14° | 150° | −7.0° | **31.0°** | +9.6° (above) |
| sub-08 V1 LOCO | 50° | −14° | 150° | −7.0° | **43.0°** | +21.6° (above) |
| sub-09 V4 LOCO (Phase A) | 6° | −22° | 16° | −6.06° | **0.06°** | −21.3° (below) |
| sub-09 V1 LOCO | 38° | +22° | 16° | +6.06° | **44.06°** | +22.7° (above) |
| **V4 LOCO mean** | — | — | — | — | **15.5°** | −5.9° |
| **V1 LOCO mean** | — | — | — | — | **43.5°** | +22.1° |

**관찰**:
1. **β_c 항이 결정적**: "mean β_s = 21.5°"는 β_c·sin(θ_conf) 항을 빼고 계산한 값. forward 유도식의 핵심 항(β_c)을 포함하면 sub-09 V4는 거의 완전히 cancel(0.06°), sub-08 V4는 31°로 9.6° 위.
2. **ROI 의존성**: 동일 피험자가 V4와 V1에서 28-44° 차이의 예측을 내놓음. 좌표계 보정(rotation invariance)으로는 해결 불가능.
3. **Group vs individual**: Emery 21.4°는 10 AT 평균. 우리는 2 individual. 개체 분산을 고려하면 "21.5° vs 21.4° 일치"는 통계적 의미 약함.

**물리적으로 가능한 해석**: "Emery 21.4°는 (β_s, β_c) 평면 위의 한 등고선 (|β_s + β_c·sin(θ_conf)| = 21.4°)에 대응하는 한 점이고, 우리 두 피험자는 그 등고선과 다른 위치에 있다." 이는 구조는 같으나 개체별 파라미터가 다르다는 의미일 뿐 — Emery 평균값과의 직접 수치 비교는 불가능.

### 권고 (2026-05-06)
- `simulation_recoverability_behavior.md` Abstract의 "≈ Emery 21.4°" 문구는 **삭제 또는 다음으로 교체**:
  > *"β_s shares the same 1st-harmonic non-uniform warp structure as Emery's Factor 4 (zero at LvsM, antiphase peak at S-axis). However, the numerical proximity reported in earlier drafts (mean β_s = 21.5° vs Emery Δφ_BY = 21.4°) results from omitting the β_c·sin(θ_conf) term required by the forward derivation. Including β_c gives subject-level predictions of 0.06°–44° depending on ROI choice (V4 LOCO mean 15.5°, V1 LOCO mean 43.5°). The structural correspondence remains as physiological grounding evidence; the numerical convergence does not."*
- **Forward simulation은 deferred 유지**: 좌표계 보정으로는 ROI 의존성이 해결되지 않으므로 simulation null test는 의미 없음. Phase 3 행동 검증에서 우리 피험자들의 직접 hue scaling 측정값과 비교가 필요 — Emery group mean 비교는 우회로.

---

## L3. g (R+C) ↔ Tregillus AF — 변환 불가

### 두 양의 차원

| | 본 연구 g | Tregillus AF |
|---|---|---|
| 정의 | rg' = rg_base + (1+g)(rg_ret − rg_base) ← chromaticity 평면에서 RG 축 linear gain | BOLD CRF 진폭 비율 ATs/CNs (V1, V2v, V3v 각 ROI별) |
| 측정 함수공간 | 2D opponent vector | scalar (CRF amplitude) |
| 비선형성 | 없음 (linear gain on rg) | CRF의 sigmoid form 포함 |
| 단위 | dimensionless ratio (실제로는 vector rescale factor) | dimensionless ratio |

### 변환 시도

가설: AF가 BOLD 응답의 RG-axis 변별 강도를 의미한다면, AF = (1+g) 인지 직접 검증해야 함. 그러나:

1. AF는 univariate CRF amplitude 비율 → 우리 g는 vector rescale factor가 RG axis에만 작용. 같은 single-channel rescale로 보더라도, **CRF 비선형성 통과 후의 AF**는 stimulus-space rescale의 단순 함수가 아님 (`AF = f(g)` where f involves sigmoid).
2. AF는 ROI별 측정 (V1=2.94, V2v=6.39, V3v=7.82). 우리는 hV4 LOCO에서 g 추정 → ROI 차원 mismatch.
3. AF > 1 = 보상 초과 vs g < −1 = 보상 초과: 부호 규약이 다름 (g는 −1이 정확 보상점, +∞는 *증폭이 retinal 방향과 같은 방향*으로 과다).
4. **(2026-05-04 추가)** Tregillus 자극은 **2 cardinal axes (L-vs-M, S-vs-LM) modulation only**, hue manifold 자극이 아님. 따라서 위 가설 "AF가 RG-axis 변별 강도" 자체가 stimulus-space 차원에서 부적절 — Tregillus는 cardinal-axis 응답의 contrast scaling만 측정. `AF = f(g)` 같은 conditional 가정도 자극 공간이 다르므로 처음부터 ill-posed.

### 정성적 일치만 주장 가능
- "둘 다 cortical compensation이 존재함을 시사한다" + "방향이 over-compensation이다" — 이게 끝.
- 본 연구 sub-08 hV4 g=+2.25 (3.25× 증폭)는 Tregillus AF 어떤 ROI에도 매핑되지 않음.
- Tregillus 20–40% 범위와 sub-08 g=+2.25(225%)의 비교는 단위가 다른 척도의 산술 비교 → 무의미.

### Status
**Closed (negative).** notion.md §6-4 입장이 옳다. R+C `g` 해석에서 "Tregillus 범위 초과"는 **물리량 차이**이지 모델 거부 근거가 아님 — `simulation_recoverability_behavior.md` §1.6도 같은 입장 ("we treat R+C's large g as effective description").

### 권고
- 두 문서 모두 표현 통일: g는 *opponent rescale*이고 AF는 *BOLD CRF amplitude ratio*. 변환 불가능.
- Phase 3 행동 검증에서 R+C와 2-Component 필터를 동시에 적용했을 때 sub-08의 응답을 보고 어느 모델이 옳은지 판단 (이미 §3 진행 중).

---

## L4. β_c ↔ Brettel confusion line — 구조적 근거

### 정의
- Brettel 1997: cone-level spectral convergence에서 유도된 protan 16° / deutan 150° confusion axis.
- 본 연구: $\beta_c \cos(\theta - \theta_{conf})$의 θ_conf을 Brettel 수치로 *고정*. β_c는 그 축 방향의 modulation amplitude.

### 직접 비교
없음. Brettel은 axis 정의만 제공, β_c와 같은 amplitude 양을 제공하지 않음.

### Severity-dependent 패턴 검증
- sub-08 deutan β_c=−14° (CI excludes 0) → confusion line 잔존
- sub-09 protan β_c=+3° (CI includes 0) → 큰 Δλ로 confusion axis 붕괴

이는 Brettel/Machado의 severity 의존 예측과 정합:
- Mild deutan: confusion axis 잔존 (β_c ≠ 0)
- Severe protan: dichromat 한계로 axis 붕괴 (β_c → 0)

### Status
**Closed (구조적 근거).** notion.md §6-3 입장 유효.

---

## L5. hV4 primary ROI ↔ Brouwer & Heeger 2009 / Kuriki 2025

### 정성 일치
- B&H 2009: V4/VO1만 novel-color reconstruction 성공, V1–V3 유의 저하. → 본 연구도 hV4만 LOCO permutation null 초과 (forward_phase1 §gate). **방법론·결론 모두 일치**.
- Kuriki 2025: hV4/VO1 cRDM이 perceptual RDM과 partial correlation. → 본 연구 hV4 ΔRDM이 행동 JND 100% 예측 (`MEMORY` §"LOCO→JND: 100%").

### Status
**Closed.** notion.md §6-2 입장 유효. 가장 강한 문헌 정합.

---

## 동료 공유용 정리표

| 문헌 연결 | 본 연구 양 | 검증 방법 | 결론 | 추가 작업 |
|---|---|---|---|---|
| Machado Δλ severity | Δλ point estimate | 표 비교 | ✅ 범위 일치 | 없음 |
| Emery Δφ_BY (CVD연구) | β_s, β_c, θ_conf | forward 적용 \|Δφ_BY\| = \|β_s + β_c·sin(θ_conf)\|; ROI별 비교 | ✅ 구조 일치 / ❌ 수치 수렴 (V4 mean 15.5°, V1 mean 43.5° vs Emery 21.4°, ROI에 따라 0.06–44° 산포) | 없음 (행동 hue scaling 직접 측정 필요) |
| Tregillus AF | g (R+C) | 차원 비교 | ❌ 변환 불가 | 표현 분리 |
| Brettel confusion | β_c, θ_conf | severity-dependent 패턴 | ✅ 구조 정합 | 없음 |
| B&H 2009 / Kuriki 2025 hV4 | LOCO ρ, ΔRDM | 정성 비교 | ✅ 강한 일치 | 없음 |

---

## 다음 액션 (우선순위) — 2026-05-04 업데이트

1. **[L2 부분 수정] Forward Simulation — DEFERRED 유지** (2026-05-06). NotebookLM으로 (a) Factor 4 = β_s·sin(θ) 구조 일치 (b) Emery는 CVD 연구 확인. **그러나 정량 분석 결과 β_c 항 + ROI 의존성으로 수치 수렴 불가** (V4 mean 15.5° / V1 mean 43.5° vs Emery 21.4°). 좌표계 보정으로는 해결 불가 (rotation은 magnitude 보존). Phase 3에서 sub-08/09 본인의 hue scaling 직접 측정이 진정한 brain-behavior 검증.

2. **[Doc — pending]** `simulation_recoverability_behavior.md` Abstract 정정 — Emery 21.4° 비교 문구를 §L2 권고의 boxed 잠정 표현으로 교체 (structural-grounding only).

3. **[Doc — pending]** `future_phase2_notion.md` §6-4 명료화 — Tregillus AF와 g가 변환 불가하다는 점을 한 문단으로 명시 (현재 표만 있음). §L3 본문 4번째 항목 (자극 공간 mismatch)도 같이 반영.

4. **[Optional]** L4 Severity-dependent 표 추가 — sub-08/09 β_c 차이를 Brettel/Machado severity prediction과 매칭하는 정량 표를 `future_phase2_notion.md` §6-3에 추가.

5. **[Done — 2026-05-04]** `index.md` §2-2 + `claude_in_ppt_prompts_meeting.md` Slide 6에 Emery axis-position vs ours per-color warp + Tregillus univariate vs ours multivariate 표 반영.

---

## References

> **2026-05-04 정정**: 본 문서가 처음 cite한 "Emery 2021 PMC8058247"은 실제로는 Emery et al. (2017) *Variations in normal color vision* 시리즈의 한 편 (저자: Volbrecht, Peterzell). 본 프로젝트가 21.4° rotation으로 인용하는 정확한 논문은 **2021 Vision Research hue-scaling 논문 (저자: Kuppuswamy Parthasarathy, Joyce, Webster 공저)**. 두 논문은 분리되어야 함.

- **Emery, K. J., Kuppuswamy Parthasarathy, M., Joyce, D. S., & Webster, M. A. (2021).** Color perception and compensation in color deficiencies assessed with hue scaling. *Vision Research*, 183, 1–15. <https://doi.org/10.1016/j.visres.2021.01.006> ← **21.4° BY phase rotation의 source**
- (선행 방법론) Emery, K. J., Volbrecht, V. J., Peterzell, D. H., & Webster, M. A. (2017). Variations in normal color vision series. *J Vision*, 17(1) etc.
- Tregillus, K. E. M. et al. (2021). *Curr Biol*, 31(5):936–942. OSF: <https://osf.io/2sv9y> (Figures 2B, 3 source data only)
- Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). *IEEE TVCG*, 15(6):1291–1298.
- Brettel, H., Viénot, F., & Mollon, J. D. (1997). *JOSA A*, 14(10):2647–2655.
- Brouwer, G. J., & Heeger, D. J. (2009). *J Neurosci*, 29(44):13992–14003.
- Kuriki et al. (2025) — internal memory note.

내부 답변 문서: [`answers/Q6_betas_emery_math.md`](answers/Q6_betas_emery_math.md)
관련 framework 문서: [`index.md`](index.md) §2 (현재 정본), [`presentation/claude_in_ppt_prompts_meeting.md`](presentation/claude_in_ppt_prompts_meeting.md) Slide 6.
