# 문헌 연결 — 수학 기반 재시도

> **목적**: 본 연구의 추정 파라미터(β_s, β_c, Δλ, g)와 선행 문헌(Emery 2021, Tregillus 2021, Machado 2009, Brettel 1997)의 수치 사이에 어떤 수학적 비교가 가능한지/불가능한지를 동료에게 공유하기 위한 정리.
>
> **배경 모순**: 두 내부 문서가 서로 다른 입장을 취하고 있음.
> - `future_phase2_notion.md` §6-3, §9 → "다른 물리량 → 수치 비교 무의미"
> - `simulation_recoverability_behavior.md` Abstract → "mean β_s 21.5° ≈ Emery 21.4°"
>
> 본 문서는 **수학적 도출과 검증 가능 조건을 명시**하여 두 입장 중 어느 쪽이 옳은지 판가름하는 기준을 제공.

---

## 0. Status 매트릭스

| 연결 시도 | 본 연구 양 | 문헌 양 | 직접 비교 가능? | 가정하 비교 가능? | 현 상태 | 다음 액션 |
|---|---|---|:---:|:---:|---|---|
| **L1. Machado Δλ** | sub-08 2.0 nm / sub-09 13.5 nm | severity range 1–14 nm | ✅ | — | **확정 — 범위 일치** | 추가 작업 없음 |
| **L2. β_s ↔ Emery 21.4°** | β_s = 20° (sub-08), 23° (sub-09), mean 21.5° | B-Y phase shift Δφ_BY = 21.4° | ❌ | ⚠️ 3 가정 시 | **모순 진행 중 — 우연 가능성 높음** | forward simulation으로 검증 |
| **L3. g ↔ Tregillus AF** | sub-08 hV4 g=+2.25, sub-09 g=−1.10 | AF V1=2.94, V2v=6.39, V3v=7.82 | ❌ | ❌ | **변환 불가 — 개념적 수렴만** | 명시 분리 |
| **L4. β_c ↔ Brettel confusion** | sub-08 β_c=−14°, sub-09 β_c≈0 | confusion line angle 16°/150° | △ (축 정렬) | — | **구조적 근거만** | severity-dependent 검증 |
| **L5. hV4 ROI ↔ B&H 2009 / Kuriki 2025** | V4가 LOCO 유일 통과 | V4/VO1만 novel-color 재구성 | ✅ (정성적) | — | **확정** | — |

**핵심 결론 미리보기**: L1, L5만 직접 비교 가능. L2는 forward simulation 검증 필요(우연 가능성 높음). L3은 변환 불가. L4는 모델 구조 근거.

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

### Status
**미해결 — 모순 진행 중.** Forward simulation 1회로 결론 가능. notion.md 입장이 옳다고 잠정.

### 권고
- `simulation_recoverability_behavior.md` Abstract의 "≈ Emery 21.4°" 문구를 **검증 시뮬레이션 후 재서술**.
- 잠정 표현: *"β_s falls in the same order of magnitude as Emery's Δφ_BY = 21.4°. Quantitative comparability requires (i) small-angle, (ii) fixed percept-space cosine bank, (iii) θ_conf orthogonal to B-Y assumptions; sub-09 satisfies these approximately, sub-08 does not (β_c·sin(θ_conf) ≈ 7° contribution). Forward-simulation convergence test is left for future validation."*

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
| Emery Δφ_BY | β_s, β_c, θ_conf | forward-pass simulation, percentile vs random null | ⚠️ sub-09만 잠정, sub-08 β_c 보정 필요 | **forward sim 작성** |
| Tregillus AF | g (R+C) | 차원 비교 | ❌ 변환 불가 | 표현 분리 |
| Brettel confusion | β_c, θ_conf | severity-dependent 패턴 | ✅ 구조 정합 | 없음 |
| B&H 2009 / Kuriki 2025 hV4 | LOCO ρ, ΔRDM | 정성 비교 | ✅ 강한 일치 | 없음 |

---

## 다음 액션 (우선순위)

1. **[Critical] L2 Forward Simulation** — `scripts/validate_betas_emery_phase.py` 작성. 입력: 추정 (β_s, β_c, θ_conf) per subject. 출력: `results/lit_link/betas_emery_simulation/sub-0X.json`에 `delta_phi_BY_sim`, `delta_phi_BY_random_null` (n=1000), `percentile`. 비용: local 실행 5분 이내, batch 불필요.

2. **[Doc] simulation_recoverability_behavior.md Abstract 정정** — Emery 21.4° 비교 문구를 검증 후 재서술. notion.md 입장으로 통일.

3. **[Doc] notion.md §6-4 명료화** — Tregillus AF와 g가 변환 불가하다는 점을 한 문단으로 명시 (현재 표만 있음).

4. **[Optional] L4 Severity-dependent 표 추가** — sub-08/09 β_c 차이를 Brettel/Machado severity prediction과 매칭하는 정량 표를 §6-3에 추가.

---

## References

- Emery, K. J., Volbrecht, V. J., Peterzell, D. H., & Webster, M. A. (2021). *J Vision*, 21(2):4. [PMC8058247](https://pmc.ncbi.nlm.nih.gov/articles/PMC8058247/)
- Tregillus, K. E. M. et al. (2021). *Curr Biol*, 31(5):936–942.
- Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). *IEEE TVCG*, 15(6):1291–1298.
- Brettel, H., Viénot, F., & Mollon, J. D. (1997). *JOSA A*, 14(10):2647–2655.
- Brouwer, G. J., & Heeger, D. J. (2009). *J Neurosci*, 29(44):13992–14003.
- Kuriki et al. (2025) — internal memory note.

내부 답변 문서: [`answers/Q6_betas_emery_math.md`](../answers/Q6_betas_emery_math.md)
