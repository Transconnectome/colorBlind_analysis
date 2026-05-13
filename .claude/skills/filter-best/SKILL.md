---
name: filter-best
description: colorBlind Phase 2 filter optimization의 BEST loss 결정 및 시각화 워크플로우. V4-only LOCO policy 하에서 양 피험자 공통 best 파라미터 탐색, HC specificity 검증, 표준 시각화 집합 생성. "filter best", "filter-best", "phase2 best", "best filter visualize", "common loss search", "BEST 갱신" 요청 시 사용.
recommended-model: sonnet
---

> **Model hint**: Use `model: "sonnet"` for subagents (analytical: loss landscape + bootstrap + visualization).

# Filter BEST 결정 + 시각화 (filter-best)

## 목적

colorBlind Phase 2 filter optimization에서 양 피험자(sub-08 deutan, sub-09 protan) 공통으로 좋은 loss combination을 탐색하고, BEST 파라미터에 대한 표준 시각화 집합을 생성한다.

---

## 핵심 원칙 (CRITICAL — 변경 금지)

1. **V4 LOCO only policy**:
   - LOCO 지표는 V4에서만 사용 (V1, V2 LOCO 제외)
   - V1+V2 RDM (cross-ROI representational similarity)는 허용 — RDM ≠ LOCO
   - 허용: L_ccc(V4), L_vuln(V4), L_rank(V4), l_topk(V4), L_rdm(V1+V2 SRM), L_smooth
   - 제외: L_rank(V1), l_topk(V1), L_vuln(V1) 등 V1/V2 LOCO

2. **Simulator**: wretrained (shift_at_both) — V4-CCC wretrained current best과 일관

3. **§0 정합**: descriptive only, behavioral validation이 ground truth. Specificity claim 금지.

4. **β_s ≥ 0** (physical convention): forward model `δθ = β_s · cos(θ−90°) + β_c · cos(θ−150°)`, β_s 음수는 비물리적 (자세한 이론적 근거는 `results/SUMMARY.md` §"β_s 음수 배제 이론적 근거")

5. **Grid**: β_s ∈ [0, 50] step 2 × β_c ∈ [−50, 50] step 2 = 1326 cells

---

## 입력 — Current BEST 정보 + 새 candidate

- **Current BEST**: `results/BEST_summary.json` (V4-CCC + l_topk wretrained, sub-08 (44, +28), sub-09 (30, +46))
- **Current SUMMARY**: `results/SUMMARY.md` (전체 상태)
- **새 candidate loss formulation** (사용자 input):
  - Loss 정의 (e.g., V4-CCC + λ·l_topk + μ·L_rdm(SRM) + ε·L_smooth)
  - λ, μ, ε 등 weights
  - 데이터 caching 전략 (재사용 vs 신규 시뮬)

---

## 워크플로우

### Step 1 — Validate V4-only LOCO policy
- 제안된 loss에 V1/V2 LOCO 항이 있는지 확인
- 있으면 → reject + 대안 제시 (RDM으로 변환 가능 시)
- 없으면 → proceed

### Step 2 — Loss landscape 계산 (CVD)
- 기본: V4-CCC wretrained landscape의 cached vuln_sim 재사용 (`results/old_formula/sub-{08,09}_V4_V4ccc_landscape.json`)
- 새 loss component 추가 시 (e.g., L_rdm(V1+V2 SRM)):
  - SRM precompute 사용 (`results/diagnostics/srm_precompute/srm_V{1,2}.npz`)
  - Tier 2 runner 패턴: `scripts/tier2_v4ccc_srm_rdm_wretrained.py` 참고
- L_combined per cell 계산 → argmin 검색

### Step 3 — HC LOO 계산 (specificity 검증)
- HC pool: sub-01..06 (sub-07 V4 16 voxels → nan 위험)
- HC sanity landscape 재사용 (`results/fits/phase_a_2component_hc_sanity/sub-{01..06}_V4_2component.json`)
- 새 loss에 따라 per-cell L_combined 재계산
- 각 HC argmin norm 추출
- **두 specificity metric 모두 계산**:
  - **Norm-based**: bootstrap 10000 resamples of HC mean norm, boot_frac = P(HC mean < CVD norm)
  - **Δ_L-based**: Δ_L = L(0,0) − L(argmin), HC bootstrap of Δ_L, boot_frac
- Verdict: ✓✓ ≥0.975, ~~ 0.90-0.975, ✗ <0.90

### Step 4 — Compare with current BEST
- 각 후보의 sub-08 P2a, sub-09 P2a 계산 (`scripts/fixedW_onlyTest_p2a_ranking.p2a_compute` 사용)
- Verdict criteria:
  - **Better**: min(sub-08 P2a, sub-09 P2a) > current BEST min + 0.025
  - **Same**: within ±0.025 of current BEST
  - **Worse**: < current BEST min - 0.025

### Step 5 — BEST 갱신 (Better인 경우만)
- 이전 BEST → `results/CANDIDATE/<previous_loss_name>/` 이동
- 새 BEST → `results/BEST_*.png/pdf` 갱신
- `results/SUMMARY.md` 상단 BEST section 갱신

### Step 6 — 표준 시각화 집합 생성

**필수 figure** (`results/BEST_*` prefix):
- `BEST_F4_V4_<loss>.png/pdf` — F4-style 통합 (Panel A: vuln line + top-3 shading + V4-CCC alone overlay; Panel B: P2a bars; Panel C: combined L landscape)
- `BEST_4col_sub-{08,09}_V4_<loss>_bsB_bcB.png/pdf` — 4-column color rendering (Original / CVD perceives / Filtered / CVD(Filtered))
- `BEST_vuln_hue_sub-{08,09}_V4_<loss>_bsB_bcB.png/pdf` — LOCO vuln line graph
- `BEST_landscape_sub-{08,09}_V4_<loss>_bsB_bcB.png/pdf` — combined L heatmap, dynamic percentile vmin/vmax, blue=argmin
- `BEST_srm_rdm_combined.png/pdf` — V1/V2 SRM RDM (observed vs simulated at BEST argmin)
- `BEST_srm_rdm_sub-{08,09}_V{1,2}.png/pdf` — per-subject-ROI standalone

**Y-axis label convention** (Option A 적용):
```
"LOCO voxel_corr  (↑ preserved / HC-like  |  ↓ vulnerable / CVD-distorted)"
```
"vulnerability" 단어 사용 금지 (반직관적이라 명시).

### Step 7 — HC landscape 생성 (specificity 시각화)
- 6 HC × `BEST_hc_landscape_sub-{01..06}_V4_<loss>.png` — HC LOO landscape under new loss
- 저장 위치: `results/CANDIDATE/<loss_name>/`

### Step 8 — SUMMARY.md 갱신
- "🏆 CURRENT COMMON BEST" 표 갱신 (argmin, norm, P2a, ρ, CCC, l_topk, exact)
- "🔍 BEST 파라미터에서 각 loss 항의 상태" per-term breakdown 갱신
- "🔍 Active candidate list" 표 갱신
- "📁 File map" 경로 갱신

---

## 핵심 도구 스크립트

| Script | 역할 |
|---|---|
| `scripts/fixedW_onlyTest_p2a_ranking.py` | P2a 계산 (`p2a_compute(bs, bc, target_map)`) |
| `scripts/fixedW_onlyTest_ltopk_sweep.py` | l_topk λ sweep 패턴 |
| `scripts/tier2_v4ccc_srm_rdm_wretrained.py` | V1+V2 SRM RDM 계산 패턴 |
| `scripts/tier_hc_specificity_v4cccltopk.py` | HC LOO argmin + norm-based specificity |
| `scripts/fixedW_onlyTest_best_visualize.py` | BEST F4 + 4-col + vuln_hue + landscape |
| `scripts/best_srm_rdm_visualize.py` | V1/V2 SRM RDM 시각화 |
| `results/generate_best_viz.py` (pending sub-agent D) | Parametrized CLI viz |

---

## 데이터 소스

- **V4 amplitudes**: `analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals/sub-XX/V4/amplitudes_procrustes.npy` (6 runs × 8 colors × n_voxels)
- **V4-CCC landscape cached**: `results/old_formula/sub-{08,09}_V4_V4ccc_landscape.json`
- **HC sanity landscape**: `results/fits/phase_a_2component_hc_sanity/sub-{01..06}_V4_2component.json`
- **SRM precompute**: `results/diagnostics/srm_precompute/srm_V{1,2}.npz`, `delta_rdm_obs_srm_V{1,2}.npz`
- **CVD vuln target**: `load_cvd_loco_target(sid, 'V4')` from `scripts/old_formula_refit.py`

---

## P2a 계산 (raw_behav 기반 ground truth)

```python
from fixedW_onlyTest_p2a_ranking import p2a_compute, SUB09_ORIGINAL_HC_EQUIV
from phase3_candidate_analysis_v2 import SUB08_ORIGINAL_HC_EQUIV

# Forward model: δθ = β_s · cos(θ-90°) + β_c · cos(θ-150°), θ_conf=150°
# For each color θ ∈ {0, 45, ..., 315}:
#   theta_cvd = (θ + δθ) % 360
#   predicted_HC_name = hc_name(theta_cvd)
#   score = hc_match_score(predicted, target_HC_equiv_map[θ])
# P2a = mean(scores)
p2a, exact, per_color = p2a_compute(bs, bc, SUB08_ORIGINAL_HC_EQUIV)
```

Targets:
- `SUB08_ORIGINAL_HC_EQUIV`: {0:pink, 45:red, 90:yellow-green, 135:yellow, 180:yellow, 225:sky, 270:sky, 315:blue}
- `SUB09_ORIGINAL_HC_EQUIV`: {0:pink, 45:orange, 90:yellow-green, 135:yellow-green, 180:sky, 225:sky, 270:blue, 315:violet}

---

## Anti-patterns (CLAUDE.md §8와 일치)

- ❌ **V1/V2 LOCO loss 추가** (Cycle12-style cross-ROI) — V4-only policy 위반
- ❌ **Specificity claim** — HC FPR=100% 확인됨, descriptive만 허용
- ❌ **Selection rule reformulation** — Cycle 9-13에서 12회 시도 NET-zero
- ❌ **Sub-10 selection logic** — §A7 분석 제외
- ❌ **β_s < 0 grid 확장** without explicit theoretical justification
- ❌ **"vulnerability" 단어 사용** in y-axis labels (Option A label로 대체)
- ❌ **Cross-family fitting** (deutan에 protan params 적용)
- ❌ **fourier_warp model class** — §A2 위반
- ❌ **Background process zombie 방치** — task 종료 시 setsid 변종까지 확인 + kill

---

## 산출물 검증 체크리스트

새 BEST 갱신 후 확인:

- [ ] `results/BEST_summary.json` 갱신 (argmin, P2a, ρ, CCC, l_topk, srm_rdm)
- [ ] `results/BEST_F4_V4_<loss>.png/pdf` 생성 (Panel A 2-curve overlay + top-3 shading)
- [ ] `results/BEST_4col_sub-{08,09}_*.png/pdf` 갱신
- [ ] `results/BEST_vuln_hue_sub-{08,09}_*.png/pdf` 갱신
- [ ] `results/BEST_landscape_sub-{08,09}_*.png/pdf` 갱신 (dynamic vmin/vmax)
- [ ] `results/BEST_srm_rdm_combined.png/pdf` 갱신
- [ ] `results/BEST_srm_rdm_sub-{08,09}_V{1,2}.png/pdf` 갱신
- [ ] `results/CANDIDATE/<new_loss>/` 폴더 생성 + landscape JSON, sweep data
- [ ] `results/CANDIDATE/<new_loss>/hc_specificity.csv` (norm + Δ_L)
- [ ] `results/CANDIDATE/<new_loss>/hc_landscape_sub-{01..06}.png` (6 figures)
- [ ] 이전 BEST → `results/CANDIDATE/<previous_loss>/` 이동
- [ ] `results/SUMMARY.md` 갱신 (CURRENT BEST, per-term breakdown, file map)

---

## 사용 예시

사용자: "phase2 best 갱신해줘. 새 loss는 V4-CCC + 0.3·l_topk + 0.3·L_rdm(V1 SRM only)"

워크플로우:
1. **Step 1**: V1 SRM RDM ⊂ RDM (not LOCO) → policy ✓
2. **Step 2**: V4-CCC landscape cached 재사용, V1 SRM RDM 새로 계산 (V2 제외)
3. **Step 3**: HC LOO under new loss, bootstrap norm + Δ_L specificity
4. **Step 4**: P2a 계산 → current BEST와 비교
5. **Step 5-7**: Better인 경우 BEST 갱신 + 시각화 생성
6. **Step 8**: SUMMARY.md 갱신

---

## 출력 형식

작업 완료 후 Korean 보고서 (under 500 words):
- 새 candidate (β_s, β_c) per subject
- P2a comparison vs current BEST
- HC specificity verdict (norm + Δ_L)
- Verdict (Better / Same / Worse)
- 생성된 figure 목록
- SUMMARY.md 갱신 위치

---

## 관련 문서

- `analysis/future_phase2_filter_optimization/CLAUDE.md` §0 (Framework Decision)
- `analysis/future_phase2_filter_optimization/results/SUMMARY.md` (현재 상태)
- `analysis/future_phase2_filter_optimization/results/CANDIDATE/v4ccc_ltopk/hc_specificity.csv` (norm 기반 specificity 예시)
- `analysis/future_phase2_filter_optimization/raw_behav.md` (P2a ground truth)
