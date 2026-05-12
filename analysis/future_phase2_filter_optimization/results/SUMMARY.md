# Phase 2 Filter Optimization — Consolidated Summary

**Date**: 2026-05-12
**Scope**: fixedW_onlyTest cycle — V4-CCC variant + cross-ROI exploration
**Policy**: **V4 LOCO only** (V1 LOCO metrics excluded; V1+V2 RDM allowed)

---

## 🏆 CURRENT COMMON BEST (단일 loss, 양 피험자 적용)

### **V4-CCC + λ·l_topk(V4) wretrained** (λ ≥ 0.25)  ← updated 2026-05-12

**Loss formula**: `L = 1.0·L_ccc + λ·l_topk(V4, K=3) + 0.1·Tikh` (λ ∈ {0.25, 0.5, 1.0, 2.0} 동일 argmin)
**Simulator**: wretrained (shift_at_both)
**Policy compliance**: V4 LOCO only ✓

| Subject | (β_s, β_c) | norm | **P2a** | Spearman ρ | CCC | l_topk | exact/8 |
|---|---|---|---|---|---|---|---|
| **sub-08 deutan** | **(44°, +28°)** | 52.2° | **0.575** | 0.619 | 0.105 | **0.000** ✓ | **4/8** |
| **sub-09 protan** | **(30°, +46°)** | 54.9° | **0.650** | 0.500 | 0.304 | 0.500 | 3/8 |

---

## 🔍 BEST 파라미터에서 각 loss 항의 상태 + V1+V2 SRM RDM dissociation

### Data sources
- `results/BEST_summary.json` — sub-08 (44, +28), sub-09 (30, +46) BEST values
- `results/CANDIDATE/tier2_v4ccc_srm_rdm/sub-{08,09}_V4_V4CCC_SRMRDM_landscape.json` — V1+V2 SRM RDM cosine values at the **BEST** argmin coordinates (not Tier 2 argmins)
- `results/CANDIDATE/v4ccc_ltopk/hc_specificity.csv` — HC bootstrap norm distribution

### Per-term breakdown at BEST argmin

Loss formula: `L_combined = 1.0·L_ccc + 0.5·l_topk(V4, K=3) + 0.1·L_smooth` (λ_topk representative=0.5)

| Term | sub-08 (44, +28) | sub-09 (30, +46) | Note |
|---|---|---|---|
| L_ccc | 0.4476 | 0.3481 | CCC-based loss = (1 − CCC)/2 family |
| l_topk(V4, K=3) | 0.000 | 0.500 | top-K Jaccard distance (sub-09 = 0 cells with l_topk=0) |
| L_smooth (raw) | 0.0839 | 0.0931 | δθ smoothness penalty |
| **L_combined** | **0.4560** | **0.6074** | total (BEST argmin minimum) |
| CCC (V4) | 0.105 | 0.304 | from BEST_summary.json |
| Spearman ρ (V4) | 0.619 | 0.500 | V4 LOCO |
| **cos_V1 (SRM RDM)** | **+0.436** | **+0.639** | derived at BEST argmin from tier2 landscape |
| **cos_V2 (SRM RDM)** | **−0.021** | **+0.393** | derived at BEST argmin from tier2 landscape |
| L_rdm_avg (V1+V2) | 0.396 | 0.242 | = mean((1−cos_V1)/2, (1−cos_V2)/2) |
| P2a (behavioral) | 0.575 | 0.650 | from BEST_summary.json |
| exact/8 | 4/8 | 3/8 | per-color hit count |

**Note (data correction)**: Initial task spec referenced cos_V1=0.103, cos_V2=0.121 (sub-08) and cos_V1=0.747, cos_V2=0.479 (sub-09). Those values do not appear in the tier2 landscape at the BEST argmin coordinates. The table above uses the **actual** landscape values at (44, +28) and (30, +46). The Tier 2 argmins themselves (sub-08: (50, 24), sub-09: (34, 44)) yield different cos values still — those are listed in `tier2_summary.json`.

### Interpretation

- **sub-08 deutan**: V4 LOCO 측면에서 cone-shift signal이 localized (CCC=0.105, ρ=0.619, l_topk=0). V1+V2 SRM RDM은 V1 cos=+0.436 (moderate), V2 cos=−0.021 (near zero) — V1에서는 일부 정합, V2에서는 무신호. Filter (44, +28)는 V4 voxel-level top-K vulnerable set을 정확히 reproduce하는 위치로 수렴.
- **sub-09 protan**: V4 LOCO에서 ρ=0.500, l_topk=0.5 (top-3 set 부분 미스). V1+V2 SRM RDM에서 V1 cos=+0.639 (strong) / V2 cos=+0.393 (moderate)으로 V4보다 RDM signal이 큰 값. Filter (30, +46)는 V4 + V1 RDM 둘 다에서 reasonable trade-off 위치.
- 두 피험자의 cone-shift signature가 dominant한 ROI/representation level이 다르다 (sub-08은 V4 voxel-level 우세, sub-09는 V1+V2 RDM-level 우세). Single ROI/metric으로 양쪽 capture 불가, **V4-CCC + l_topk이 V4 alone에서 cross-subject common loss로 작동**하되 V1+V2 SRM RDM은 sub-09에서 보조 evidence 제공.

#### vs prior best (V4-CCC alone)

| Subject | V4-CCC alone | V4-CCC + l_topk | Δ P2a |
|---|---|---|---|
| sub-08 | (16, +40) P2a=0.537 (3/8) | **(44, +28) P2a=0.575 (4/8)** | **+0.038** |
| sub-09 | (30, +46) P2a=0.650 (3/8) | (30, +46) P2a=0.650 (3/8) | 0 (unchanged) |
| **min** | **0.537** | **0.575** | **+0.038** |
| avg | 0.594 | 0.613 | +0.019 |

### Why this works
- **Sub-08**: 4 cells in wretrained landscape achieve l_topk=0 (perfect top-3 vulnerable set reproduction). l_topk weight pulls argmin to (44, +28) — **still positive β_c family (sign-flip preserved)**, just shifted toward higher β_s within the topk=0 plateau. CCC drops (0.190→0.105) but P2a improves (3→4/8 exact).
- **Sub-09**: 0 cells with l_topk=0. λ has no effect. V4-CCC argmin retained.
- → **Strictly dominating**: sub-08 improves, sub-09 unchanged.

### Per-color predictions (V4-CCC argmin)

**Sub-08 deutan (16, +40)**:
| | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|
| Target (sub-08 보고) | pink | red | yellow-green | yellow | yellow | sky | sky | blue |
| V4-CCC predict | magenta | orange | yellow-green ✓ | cyan | sky | sky ✓ | sky ✓ | violet |
| Score | 0.5 | 0.3 | **1.0** | 0.0 | 0.0 | **1.0** | **1.0** | 0.5 |

**Sub-09 protan (30, +46)**:
| | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|
| Target (sub-09 보고) | pink | orange | yellow-green | yellow-green | sky | sky | blue | violet |
| V4-CCC predict | magenta | orange ✓ | green | sky | sky ✓ | sky ✓ | sky | blue |
| Score | 0.5 | **1.0** | 0.6 | 0.0 | **1.0** | **1.0** | 0.6 | 0.5 |

---

## ⚠️ Current limitation — Specificity is descriptive only

**상단의 모든 CVD vs HC 비교는 "descriptive percentile" 기반 보고**이며, formal specificity claim 아님.

### 검증된 specificity metric 모두 실패 (boot_frac < 0.90)

| Metric | sub-08 boot_frac | sub-09 boot_frac | Verdict |
|---|---|---|---|
| Norm-based (CVD norm vs HC bootstrap mean norm) | 0.13 | 0.54 | ✗ |
| Δ_L-based (loss improvement from β=0,0) | 0.27 | 0.14 | ✗ |
| HC LOO norms range [49.0°, 65.3°], mean 54.8° — CVD BEST norms (52.2°, 54.9°)이 CI [50.5, 60.1] 안 |

### 한계의 구조적 원인 (CLAUDE.md §0/§8)

1. **HC FPR = 100%** under label-permutation null (`results/baseline_delta_rho/`)
2. **baseline_ρ confound** (HC corr = −0.894) — regression-to-mean
3. **n=6 HC pool** statistical power limit
4. **Voxel-prediction L_LOCO measurement family** 내 어떤 selection-rule reformulation도 specificity 만들 수 없음 (Cycle 9-13, 12회 시도 NET-zero)

### §0-compliant reporting framework

- ✗ **금지**: "CVD is specific from HC at p<0.05"
- ✗ **금지**: norm-based or Δ_L-based "significant" claims
- ✓ **허용**: "CVD's BEST norm falls within HC LOO CI" (descriptive)
- ✓ **허용**: "behavioral validation (P2a 0.575/0.650) provides primary evidence"
- ✓ **허용**: "two losses (V4-CCC alone, V4-CCC+l_topk) yield consistent positive β_c family for sub-08 — descriptive robustness"

### 결정 기준

**§0 line 7**: "Filter selection = LOCO-best descriptive fit per subject + behavioral validation"

→ specificity는 **selection criterion이 아님**. Behavioral test (P2a)가 ground truth. 본 BEST는 P2a 기반으로 채택되었고, specificity reporting은 descriptive supplement.

### 시도된 specificity alternatives (모두 fail or §0 위반)

| Alternative | 결과 |
|---|---|
| Norm bootstrap | ✗ inside HC CI |
| Δ_L bootstrap | ✗ inside HC CI |
| Profile likelihood CI width | σ² confound (Phase 2 prior, fail) |
| Argmin angle clustering | partial — 2/6 HC negative β_c family, 나머지 cluster overlap |
| Cross-loss replication (CCC vs CCC+l_topk) | sub-09 same argmin / sub-08 same family → ✓ descriptive robustness |
| Behavioral concordance (P2a) | ✓ §0 ground truth, sole valid metric |

→ **Phase 2 closure 권장**: 본 BEST 채택 + behavioral validation (Track A: sub-09 protocol 진행) + paper에서 specificity는 descriptive-only로 보고.

---

## 📋 V4-only LOCO policy

### 허용 metrics

| Metric | 허용? | 이유 |
|---|---|---|
| L_ccc(V4) | ✓ | V4 LOCO based |
| L_vuln(V4) | ✓ | V4 LOCO based |
| L_rank(V4) | ✓ | V4 LOCO based |
| l_topk(V4) | ✓ | V4 LOCO based |
| L_rdm(V1+V2 SRM) | ✓ | RDM ≠ LOCO; cross-ROI 정보 |
| L_smooth, Tikh | ✓ | regularization |
| **L_rank(V1)** | ✗ | V1 LOCO — excluded |
| **l_topk(V1)** | ✗ | V1 LOCO — excluded |
| **L_vuln(V1)** | ✗ | V1 LOCO — excluded |

### Excluded candidates (under new policy)

- **Cycle12 (V4 l_topk + V1 l_rank)** — V1 LOCO 사용 → 제외
- **Cycle12 wretrained recompute (sub-agent #1)** — **CANCELLED** (V4-only policy 적용)

---

## 📐 Parameter range 설정 — β_s 음수 배제 이론적 근거

### Grid bounds (project-wide convention)
- β_s ∈ [0, 50] step 2 — **positive only**
- β_c ∈ [−50, 50] step 2 — both signs

### 이론적 근거 (β_s ≥ 0)

Forward model: `δθ = β_s · cos(θ − 90°) + β_c · cos(θ − 150°)`

#### Reason 1: Physical cone-shift interpretation
- β_s는 S-cone (or M-cone for protan) spectral sensitivity shift magnitude
- Machado-Tregillus literature convention: shift는 wavelength 방향 단일 (toward longer or shorter λ)
- Project §A1, §A12: "2-component은 CIElab opponent space 작동, β_s = retinal-level shift" → 음수 정의 모호

#### Reason 2: Mathematical analysis of negation
`−β_s · cos(θ − 90°) = β_s · cos(θ − 90° + 180°)`
→ β_s 부호 반전 = θ_conf=90°가 270°로 회전 (180° phase shift)
→ β_s < 0는 "S-cone gain reversal" — 비물리적

#### Reason 3: Degeneracy avoidance
- β_c가 both signs 허용 → 어떤 cortical rotation 방향이든 표현 가능
- β_s 양수 + β_c 양/음 조합으로 cone-shift × cortical rotation 전체 공간 spans
- β_s 음수 추가 시 redundant (β_s>0과 β_c<0 조합이 같은 prediction 가능)

### 함의 — β_s ≥ 0 제약이 검증 결과에 미치는 영향

- 본 cycle의 모든 BEST (V4-CCC, V4-CCC+l_topk, Tier 2)가 β_s ∈ [0, 50] 범위 내 sharp argmin 보유
- HC LOO도 같은 grid 사용 — 양 그룹 동일 condition
- 만약 β_s < 0 영역에 더 좋은 fit이 있다면 발견 못함 (그러나 physical interpretation 약함)
- **선택적 확장**: 필요시 β_s ∈ [−50, 50]로 grid 확대 가능 (compute 2배 증가)

---

## 🔍 Active candidate list (V4-only policy 적용)

| # | Loss | Status | sub-08 P2a | sub-09 P2a |
|---|---|---|---|---|
| 1 | V4-CCC alone | ✓ done | 0.537 | 0.650 |
| 2 | V4-CCC + V1+V2 SRM RDM | untested (wretrained) | TBD | TBD |
| **3** | **V4-CCC + λ·l_topk(V4)** (NEW BEST, λ≥0.25) | ✓ done | **0.575** | 0.650 |
| 4 | l_topk(V4) + V1+V2 SRM RDM (cycle14-like) | untested | TBD | TBD |

---

## ⚠️ Key findings (descriptive)

### W-fixed (A1) vs wretrained simulator
- σ_sim ceiling: wretrained 0.264, wfixed 0.155 (wretrained absorbs shift into W)
- sub-10 wretrained ρ=0.41 (FP), wfixed ρ=0.02 (proper null)
- **Decision**: wretrained 사용 (best P2a evidence) + caveat 명시

### Sub-08 sign-flip (positive β_c family)
- V4-CCC wretrained: (16, +40), P2a=0.537
- SRM+V1+V2 RDM cross-family wretrained: (32, +48), perm_p=0.0002
- **2 다른 framework에서 positive β_c family 수렴** — robust evidence
- § canonical (10, −32) negative β_c와 정반대 방향

### Sub-09 V4 weak signal
- V4 l_topk(V4)=0 cells: **0개** (top-3 vulnerable set unreproducible)
- 이유: sub-09 vuln_cvd top-3 = {c5, c6, c8} — asymmetric pattern, HC LOCO + 2-param 표현 불가
- Native family 2-component (34, +4) ρ=0.119 — weak fit
- → **sub-09 V4 alone은 signal weak**, V1+V2 SRM RDM 보조 필요할 가능성

### Cache drift (cycle12)
- Cached cycle12 argmins (sub-08 (68, −38), sub-09 (30, +26)) **재현 안 됨**
- Fresh wfixed recompute → (22, −14), (34, +44) — 다른 위치
- Cycle12 wretrained recompute **CANCELLED** (V4-only policy 적용)
- → 결론: Cycle12 cached argmin은 stale code/wretrained artifact일 가능성

### l_topk(V4) 적용성 차이
| Subject | l_topk(V4)=0 cells | 의미 |
|---|---|---|
| sub-08 | 162 (large plateau) | 다중 filters가 top-3 vulnerable 재현 가능 |
| sub-09 | **0** | 어떤 filter도 top-3 set 정확히 재현 불가 |

→ l_topk는 sub-08-specific 정보, sub-09에 영향 거의 없음

---

## 🎯 Next steps (좁힘)

### Tier 1 (IN PROGRESS) — l_topk weight sweep on V4-CCC
- Loss: `L = 1·L_ccc + λ·l_topk(V4) + 0.1·Tikh`, λ ∈ {0, 0.25, 0.5, 1.0, 2.0}
- Compute: ~1분 (cached vuln_sim 사용, numpy only)
- 결과: λ별 argmin trace, P2a, sub-08 sign-flip 보존 여부

### Tier 2 (pending Tier 1 결과)
- V4-CCC + V1+V2 SRM RDM (cross-ROI augmentation)
- Compute: ~30분-1시간 (SRM precomputed 활용)

### Tier 3 (사용자 결정 대기)
- Sub-09 behavioral protocol (3 candidates 시험)
- Phase 2 closure document 작성

---

## 📁 File map (재정리됨 2026-05-12)

### 🏆 BEST — `results/` root에 즉시 visible
- `results/BEST_F4_V4_V4CCCltopk.png/pdf` — F4-style combined (sub-08+09)
- `results/BEST_4col_sub-{08,09}_V4_V4CCCltopk_*.png/pdf` — 4-column color rendering
- `results/BEST_vuln_hue_sub-{08,09}_V4_V4CCCltopk_*.png/pdf` — LOCO vuln line graph
- `results/BEST_landscape_sub-{08,09}_V4_V4CCCltopk_*.png/pdf` — combined L colormap
- `results/BEST_summary.json` — argmin + P2a + per-color details
- `results/SUMMARY.md` — 본 문서

### 📂 CANDIDATE folder — loss combination 별 exploration
- `results/CANDIDATE/v4ccc_alone/` — V4-CCC wretrained alone (previous best, V4-only policy ✓)
- `results/CANDIDATE/v4ccc_ltopk/` — **CURRENT BEST loss combo** sweep results
- `results/CANDIDATE/tier2_v4ccc_srm_rdm/` — Tier 2 V4-CCC + V1+V2 SRM RDM (PENDING)

### 📚 Raw data sources
- `results/old_formula/sub-{08,09}_V4_V4ccc_landscape.json` — V4-CCC wretrained 1326 cells
- `results/old_formula/sub-{08,09}_V4_V4ccc_summary.json` — argmin + params
- `results/old_formula/sub-{08,09}_V4_4term_landscape.json` — 4-term baseline

### 🔬 Diagnostic / supporting analysis
- `results/fixedW_onlyTest/` — wfixed (A1) 진단 (sub-10 FP, σ_sim ceiling, cycle12 wfixed)
  - `p2a_ranking.{csv,md}` — 17+16 entries 전체 ranking
  - `cycle12_landscape_recompute.md` — cache drift evidence
  - `fig_F4_V4V1_cycle12.png` — wfixed cycle12 viz
- `results/diagnostics/srm_integrated_loco/` — SRM-integrated existing (wfixed-based)
- `results/diagnostics/srm_precompute/srm_V{1,2}.npz`, `delta_rdm_obs_srm_V{1,2}.npz` — SRM precomputed
- `results/inventory/loss_inventory.{csv,md}` — 모든 loss argmins

---

## 🚫 Anti-patterns (V4 LOCO only policy 추가)

(기존 §0/§8 anti-patterns에 추가)
- **V1 LOCO metrics in loss** (l_rank_V1, l_topk_V1, etc.) — V4-only policy 위반
- **Cycle12 (V4 l_topk + V1 l_rank) in selection** — V1 LOCO 포함
- **cross-family fitting as primary** (sub-08 deutan with protan params)
- **fourier_warp model class** (§A2 3-model 외)
