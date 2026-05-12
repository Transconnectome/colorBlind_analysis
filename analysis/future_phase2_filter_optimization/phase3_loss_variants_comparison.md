# Loss Variant 4종 비교 — OLD-formula 2-component refit

**Date**: 2026-05-11
**Question**: 원본 simplified L_fit (`1.0·L_vuln + 0.5·L_rank`)이 노출한 두 paradox — (i) sub-08 V4 평탄한 sim 인데 ρ=0.83, (ii) sub-09 V4 진폭 일치하나 ρ=0.50 — 를 해소하는 loss 정의가 존재하는가?

**4 variants 평가**:
- V1: Demeaned MSE — offset 영향 제거
- V2: + Pearson r — magnitude-sensitive correlation 추가
- V3: Rank weight 감소 (β: 0.5 → 0.3 → 0.2)
- V4: CCC — Pearson + variance + offset 통합

**Cache**: `results/old_formula_vulnsim_cache/sub-{08,09}_V4_cache.json` (1326 cells × 2 subjects, 미리 계산된 vuln_sim 재사용)

---

## §1 — 4 variant 최적점 비교

| Variant | Loss 정의 | sub-08 V4 optimum | sub-09 V4 optimum |
|---|---|---|---|
| **Original** | `1.0·L_vuln + 0.5·L_rank` | (10, −32) ρ=0.83 | (30, +46) ρ=0.50 |
| **V1** | `1.0·L_vuln_dm + 0.5·L_rank + 0.1·L_smooth` | (10, −32) ρ=0.83 — **불변** | (30, +46) ρ=0.50 — **불변** |
| **V2** | `+ 0.5·L_pearson` 추가 | (10, −32) ρ=0.83 — **불변** | (30, +46) ρ=0.50 — **불변** |
| **V3-β0.3** | β: 0.5 → 0.3 | (10, −32) ρ=0.83 — **불변** | (30, +46) ρ=0.50 — **불변** |
| **V3-β0.2** | β: 0.5 → 0.2 | (10, −32) ρ=0.83 — **불변** | (30, +46) ρ=0.50 — **불변** |
| **V4** | `1.0·L_ccc + 0.1·L_smooth` | **(16, +40)** ρ=0.38 ← **부호 반전** | (30, +46) ρ=0.50 — **불변** |

**놀라운 결과**: V1, V2, V3 모두 원본과 정확히 같은 optimum 산출. **V4 (CCC)만 sub-08에서 부호 반전 (β_c −32 → +40)**.

---

## §2 — 각 variant의 진단

### V1 — Demeaned MSE (NULL)
- Offset² = sub-08의 L_vuln 52% 차지 (원본)
- 그러나 demean해도 같은 cell이 winner
- 이유: demeaned MSE의 gradient도 sub-08 평탄 winner cell을 가리킴
- **Grid 전체에서 max σ_sim = 0.247** — 어떤 cell도 obs σ=0.444에 못 미침
- **결론**: 모델 클래스 (HC-mean LOCO 회전 기반) **천장이 진폭 한계**. Loss 수정만으론 극복 불가.

### V2 — Pearson r 추가 (NULL)
- Pearson과 Spearman 모두 **scale-invariant** — 둘 다 평탄한 sim에 penalty 부과 못 함
- L_pearson term이 L_rank와 **redundant** (다른 ranking이지만 같은 cell 선호)
- sub-08 (10, −32): L_pearson=0.0827 (39%) — 39% 비중인데도 optimum 이동 못 함
- **결론**: scale-invariant 항을 weight 0.5로 추가해도 평탄-sim cell의 인기를 깨지 못함.

### V3 — Rank weight 감소 (NULL, 그러나 trend 일치)
- β: 0.5 → 0.3 → 0.2 — 모두 같은 optimum
- High-dynamic 대안 (40, +26) rank: 10 → **2** → 2 (가까워지지만 못 따라잡음)
- gap to winner: 0.026 → 0.011 → 0.004 (점점 좁아짐)
- 추정: **β < 0.06**까지 줄여야 (40, +26)이 이김 — 비현실적 가중치
- 이유: (40, +26)이 σ_sim 높지만 **Pearson r=0.188으로 낮음** → L_rank/L_pearson 모두 punish

### V4 — CCC (단독 sign-flip)
- **CCC formula**: `2·r·σ_sim·σ_obs / (σ_sim² + σ_obs² + (μ_sim−μ_obs)²)`
- 분자가 r·σ_sim·σ_obs로 **진폭 매칭을 직접 보상**
- 분모가 σ_sim² 포함 → 작은 σ_sim에 penalty
- sub-08 결과: optimum (10, −32) → **(16, +40)** — β_c **부호 반전**
- sub-08 σ_sim: 0.067 → **0.156** (2.32× 증가)
- sub-08 ρ: 0.83 → **0.38** (rank 정보 희생)
- CCC: 0.10 → 0.19 (80% 개선)
- 그러나 σ_sim/σ_obs 비율: 15% → 35% — 여전히 천장 (3× 작음)
- sub-09: unchanged (이미 진폭 양호한 영역)

---

## §3 — 결정적 발견

### Pattern: scale-invariant vs scale-aware
- **Scale-invariant losses** (Spearman, Pearson, demean-MSE-with-fixed-NORM): 모두 같은 cell 선호
- **Scale-aware loss** (CCC): 다른 cell 선택, 부호 반전까지 발생
- **이유**: 평탄 winner (10, −32)의 Pearson r=0.669는 이미 **높음** (rank가 잘 맞음) — scale-invariant 어떤 측도도 punishment 안 됨

### Two paradoxes 해소 정도

| Paradox | V1 | V2 | V3 | V4 |
|---|:-:|:-:|:-:|:-:|
| sub-08: 평탄해도 ρ 높음 | ❌ | ❌ | ❌ | ⚠️ (paradox 제거, ρ 희생) |
| sub-09: 진폭 일치하나 ρ 낮음 | ❌ | ❌ | ❌ | ❌ |

**V4만 sub-08 paradox를 옮겨놓음 (eliminate)**. 그러나 paradox를 "옮긴다"는 것이 정답인지는 별개 — V4는 ρ=0.38로 다른 valley 선택, **rank 정보 자체를 포기**하는 trade-off.

### sub-09는 어떤 variant로도 해소 안 됨
- sub-09의 (30, +46)이 **rank-tied at ρ=0.500** plateau에 있음
- 2° grid 해상도에서 ρ가 정확히 0.500인 cells 다수 존재
- Pearson r=0.504도 비슷한 ceiling
- sub-09 c6 (sky)의 obs/sim rank flip (obs rank 6 → sim rank 1)이 모델 클래스로 fixable 한지 의문

---

## §4 — 모델 천장의 정량 확인

### Grid 전체 통계 (V1 agent 보고)
- 1326 cells 전체에서 **max sim_std = 0.247**
- obs_std (sub-08) = 0.444
- **어떤 (β_s, β_c)도 obs std에 도달 못 함**

### HC-mean LOCO의 본질적 한계
- HC mean LOCO ρ는 양수 영역 (~+0.15)에 머무름
- CVD voxel_corr = −0.76 (sub-08 c7)는 모델 구조상 재현 불가
- 회전 기반 (2-component) 단독으로는 HC의 부호를 뒤집을 수 없음

### 해결 가능한 경로 (4 variant 밖)
1. **모델 클래스 확장**: amplitude attenuation term 추가 → sim이 음수 영역까지 도달 가능. 자유도 +1, overfit 위험.
2. **다른 simulator**: 단순 HC-mean LOCO 외 (예: R+C 모델, 비선형) 사용. 그러나 §0 의해 model class 추가 금지.
3. **Loss 자체 변경**: V4 같은 scale-aware loss 채택. ρ-기반 historical 검증과 단절.
4. **Target 변환**: vuln_cvd에 monotonic transform 적용 (예: tanh로 squash). artificially 천장 끌어내림 — 과학적 정당성 약함.

§0 framework 내에서 (1)-(3)은 모두 정책상 제약. (4)는 ad-hoc. **현재 framework가 본질적으로 이 paradox를 안고 있음**.

---

## §5 — 시각화

각 variant의 F4-style figure (sub-08 V4 + sub-09 V4 panel, simplified F4_twocomp 디자인 따름):
- `results/old_formula_loss_variants/V1_demeaned_mse/fig_V1_demeaned_mse.png`
- `results/old_formula_loss_variants/V2_pearson_added/fig_V2_pearson_added.png`
- `results/old_formula_loss_variants/V3_rank_w03/fig_V3_rank_w03.png`
- `results/old_formula_loss_variants/V3_rank_w02/fig_V3_rank_w02.png`
- `results/old_formula_loss_variants/V4_ccc/fig_V4_ccc.png`

**비교 시 V4만 sub-08 sim 진폭이 가시적으로 증가** (sim_std 0.067 → 0.156). 그러나 ρ는 떨어짐.

---

## §6 — 함의 및 권장

### Loss 수정 4종 모두 §0-framework 내에서 결정적 개선 못 함
- V1, V2, V3: 원본 optimum 유지 → 어떤 정보도 못 더함
- V4: 다른 family 선택하지만 ρ 희생, paradox 옮길 뿐 해소 아님
- **모든 단일 8-color metric은 모델 천장에 부딪힘**

### §0 framework가 인정하는 path
- Loss redesign으로 selection 바꾸는 시도는 §0 anti-pattern (Cycle 9-13 패턴 재진입)
- 본 분석은 **descriptive only** — model behavior 진단용
- Filter 선정은 행동 검증 P1/P2 기준으로 유지

### Behavioral validation의 중요성 재확인
- V4가 sub-08을 (16, +40)으로 옮긴 것은 V4-only OLD (38, +7)의 positive-β_c family와 정성적으로 유사
- 두 후보 모두 **행동 데이터로 검증되어야** §0-compliant 결정 가능
- 현재 행동 검증 완료된 sub-08 V4 후보:
  - **V4-only OLD (38, +7)**: P1 = 2+3p/8 ✓
  - **Canonical CURRENT (38, −14)**: P1 = 2+2p/8 ✓
  - (16, +40) [V4 CCC]: 미검증

### Sub-08 모델 천장에 대한 honest 평가
- sub-08의 vuln_cvd (mean −0.275, range 1.33)는 단순 회전 sim으로 못 재현
- ρ=0.83은 "rank만 맞춤"; magnitude는 천장에 막힘
- 이는 **모델의 한계**이지 loss의 한계 아님
- 진정한 해결: 더 표현력 있는 forward model (현재 §0가 금지) 또는 다른 target metric

---

## §7 — 산출물

- `phase3_loss_variants_comparison.md` (본 문서)
- `scripts/phase3_loss_variant_helpers.py` — 공통 helper
- `scripts/phase3_cache_vulnsim_old.py` — vuln_sim cache 생성
- `scripts/phase3_loss_variant_V{1,2,4}_*.py` — 각 variant 스크립트 (sub-agent 생성)
- `results/old_formula_vulnsim_cache/sub-{08,09}_V4_cache.json` — 1326-cell vuln_sim cache
- `results/old_formula_loss_variants/V{1,2,3_w03,3_w02,4}/sub-{08,09}_V4_{summary,landscape}.json` — variant별 landscape
- `results/old_formula_loss_variants/V{1,2,3_w03,3_w02,4}/fig_V*.{png,pdf}` — 5 figures
- `results/old_formula_loss_variants/V{1,2,3_weight,4}/ANALYSIS.md` — variant별 분석
