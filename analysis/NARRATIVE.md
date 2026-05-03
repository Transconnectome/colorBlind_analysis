# colorBlind_analysis — Project Narrative

> 생성: 2026-05-03 · 현재 상태 종합. Manuscript narrative는 Phase 3 결과 후 확정.

## 0. Big-picture goal

CVD 피험자가 HC와 유사한 색 인지를 하도록 개인화된 **inverse stimulus filter**를 도출하고, 행동/뇌영상으로 효과를 검증한다.

## 1. Evidential chain (현재 단계)

```
[차이 존재] → [모델 적합] → [필터 도출] → [통계적 specificity] → [행동 검증]
   Phase 0~2      Phase 1-FM     Phase 2-FO       Phase 2-FO         Phase 3
                  (Forward)     Cycles 1~10                          (planned)
```

각 단계의 **포지셔닝**:

### Stage A — 차이 존재 (Phase 1, 2 SRM/RDM/Procrustes)

**현재 포지셔닝**: HC와 CVD 사이에 신경 표상 차이가 존재함을 *descriptive* 수준에서 확인. 본 paper에서 RDM/SRM은 **"차이 확인"** 역할만 부여하고, mechanistic role 또는 fitting target으로 활용하지 않음.

근거:
- LOCO→JND 100% concordance, SRM z→JND 33% concordance (2026-03-22)
- "Geometric distortion ≠ behavioral sensitivity" — RDM 차이가 행동 차이로 직결되지 않음
- → RDM/SRM은 motivation/baseline, fitting/필터 도출에는 직접 미사용

저장 위치: `phase1_procrustes_decoding/`, `phase2_procrustes_cvd_hc/`, `phase2_SRM_across_between/`, `phase3_decoder_comparing/`

향후 RDM/SRM의 broader role (예: cross-validation으로 활용, 또는 mechanism evidence로 재해석)은 Phase 3 결과 후 검토.

### Stage B — Forward 모델 적합 (future_phase1_forward_model)

**역할**: HC primary percept → CVD primary percept 변환의 mechanistic 모델 후보 평가.

3개 모델 비교:
- **Machado 1-way**: 단일 cone-shift Δλ 파라미터
- **R+C (retinal + opponent gain)**: cone shift + cortical gain g
- **2-Component**: stimulus-space dilation (β_s, β_c) — retinal + cortical 두 축

핵심 결과:
- **2-Component만 dual-validated** (LOCO + xnobis 양쪽 통과) for sub-08 deutan: hV4 LOCO p=0.004**
- Sub-09 protan: V1 xnobis p=0.007**, V2 p=0.036*, joint p=0.044*
- Pre-image 8/8 colors exact (bijective for both subjects)

**한계**:
- HC LOCO FPR=100% (Job 96600): 모델이 baseline_rho confound 통제 못함
- Gen-4 task #22: Machado가 family-specific (protan vs deutan) 구별 못함
- → "모델이 신호를 잡는다"는 기술적 사실이지만 specificity는 별도 검증 필요

저장 위치: `future_phase1_forward_model/results/validation/`

### Stage C — 필터 도출 + Specificity (future_phase2_filter_optimization, 현재)

**역할**: Forward 모델의 numerical inverse → stimulus-space pre-image filter, 그리고 도출된 filter가 진짜 CVD signal을 잡는지 통계적 검증.

#### 필터 도출 (Cycle 1~8)

Selection rule (Cycle 7 확정):
```
z_combined(R) = z_set(R) + z_vox-axis(R, c_family)
  z_set      = [l_topk_jaccard(k=3) + 0.2·Tikh]_min  (forward 모델 set match)
  z_vox-axis = -[sign·z_mean + |z_rdm-row| + |z_runc|]  (voxel-pattern signature)
ROI: V1+V4 z_sum, family: deutan/protan 수동 지정
```

Pre-image: 2-component forward 모델의 numerical inverse, 8/8 colors exact.

| 피험자 | ROI | 필터 파라미터 | Pre-image example |
|---|---|---|---|
| sub-08 | V4-only | β_s=38, β_c=7 | yellow −32°, green −42° |
| sub-08 | V1+V4 avg | β_s=19, β_c=3.5 | (V1 degenerate β=0,0) |
| sub-09 | V4-only | β_s=0, β_c=2 | near-trivial (no compensation) |
| sub-09 | V1+V4 avg | β_s=30.5, β_c=12 | yellow −34°, green −30° |

시각화: `future_phase2_filter_optimization/results/figures/filter_visualization_phase3/`

#### Specificity 검증 (Cycle 9~10f, 종결)

탐색된 reformulation:
- Cycle 9: l_signed_jaccard fitting loss → **REJECTED** (HC도 noise direction 매칭 가능)
- Cycle 10: z_vox-axis 단순화 → **NET 개선 없음** (FP 다른 HC로 이동)
- Cycle 10b: sub-04 제외 sensitivity → **TRADE-OFF** (CVD↑, HC FP↑, n=6 fundamental data limit)
- Cycle 10c: server bootstrap n=200 도착, threshold envelope
- Cycle 10d: 정확한 z_combined CI 계산 (z_set point + z_vox CI)
- Cycle 10e: HC group distribution (n=6) vs CVD bootstrap CI
- Cycle 10f: per-term cross-ROI selection rule (untested 제안)
- Cycle 11: per-term cross-ROI 실행 → sub-09 V1|V4 best 발견 (FP 0/6, CI disjoint)
- **Cycle 11b**: 이론적 검증 → V1|V4는 post-hoc selection bias, 이론적 V4|V1는 specificity 더 나쁨 → **V1|V4 권장 철회**, sub-09는 exploratory
- Cycle 11c: Loss에 cross-ROI 적용 가능성 (사용자 제안) — 결정 보류 (Phase 3 후 reformulation)

**최종 정확한 z_combined CI 결과 (HC distribution 기준)**:

| 피험자/Cell | HC range | CVD pt | CVD CI95 | 결론 |
|---|---|---:|---|---|
| **sub-08 V4 deutan** | [−1.57, +1.07] | **−31.30** | [−94.85, −27.58] | **27 unit gap, robust** |
| **sub-08 V1+V4 deutan** | [−4.40, +8.71] | **−35.08** | [−108, −31] | **27 unit gap, robust** |
| sub-09 V4 protan | [−3.98, +4.49] | −3.14 | [−7.92, −2.87] | sub-02(-3.98)이 더 extreme — **NOT specific** |
| sub-09 V1+V4 protan (same-ROI sum) | [−5.09, +13.52] | −6.54 | [−18.85, −5.80] | 0.71 unit gap — **marginal** |
| **sub-09 V1\|V4 protan (cross-ROI, Cycle 11)** | [−1.57, +10.71] | −4.25 | [−9.03, −3.99] | **2.42 unit gap, CI disjoint** ✓ |

**Phase 3 trigger 권장 (Cycle 11b 정정 반영)**:
- **sub-08 deutan filter (V4|V4 same-ROI)**: PRIMARY — robust specificity (27 unit gap), dual-validated
- **sub-09 protan filter**: **EXPLORATORY only** — same-ROI rule (V4|V4) 사용 (marginal but principled)
  - Cycle 11에서 V1|V4 cross-ROI가 더 좋은 specificity 보였으나 **post-hoc selection bias** (18 tests에서 best)
  - 이론적 cross-ROI (V4|V1: LOCO-V4 + RDM-V1)는 specificity 오히려 *악화* (FP 2/6)
  - → cross-ROI rule은 manuscript에서 "exploratory finding requires Phase 3 validation"으로만 reporting

### Stage D — 행동/뇌영상 검증 (future_phase3_behavioral_analysis, 예정)

**역할**: 도출된 필터를 CVD 피험자에게 적용했을 때 (a) 색 구분 (JND), (b) 색 명명 (naming), (c) 신경 normalization (fMRI repetition suppression)이 개선되는지 검증.

**Pre-registered hypothesis 권장**:
- **Primary**: sub-08 filter 적용 시 deutan-axis colors (yellow-green discrimination) JND 개선 (effect size d≥0.5)
- **Secondary**: sub-09 filter 적용 시 protan-axis colors discrimination 개선 (exploratory, effect size 미정)
- **Sham control**: sub-10 + 무작위/null filter

## 2. Manuscript narrative (잠정, Phase 3 후 확정)

### 본 paper의 contribution

**핵심 claim**: "신경 차이 → mechanistic 모델 → invertible filter → (Phase 3에서) 행동 검증"

**not the claim**:
- "RDM/SRM 차이가 직접 perceptual loss를 의미한다" (LOCO→JND concordance만 100%)
- "현 selection rule이 specific HC FP rate 통제한다" (n=6 fundamental limit, 2/6 ~ 33% FP at z<-2)
- "어떤 CVD subject에게도 작동한다" (sub-08만 robust, sub-09는 행동 검증 의존)

### 이전 phase의 본 paper에서의 역할

| Phase | 역할 | manuscript 위치 |
|---|---|---|
| Phase 0 (preprocessing) | 데이터 준비 | Methods |
| Phase 1 (procrustes/SRM/RDM) | **HC-CVD 차이 존재 확인** (descriptive) | Introduction, Background; **본 paper의 mechanism claim에는 미사용** |
| Forward model (LOCO) | 모델 적합 → 2-comp 선정 | Results §1 (model selection) |
| Phase 2 cone-shift v2 | 1-DOF baseline (Machado) | Results §1 (alternative models) |
| 2-Component | **본 paper primary forward 모델** | Results §2 (validated model) |
| Phase 2 filter optimization | Selection rule + pre-image + specificity | Results §3 (filter derivation), §4 (specificity) |
| Phase 3 behavioral | 행동/뇌영상 검증 | Results §5 (causal evidence) |

## 3. 알려진 한계와 해결 미정

1. **n=6 HC pool fundamental data limit** — selection rule 정교화로 해결 안 됨 (Cycle 10b 확인)
2. **sub-04 BOLD outlier** — yellow z_mean +1.98, magenta z_mean +1.83. HC인지 mild CVD인지 행동 데이터로 검증 필요
3. **sub-09 V1 forward fit degenerate** (β=0,0) — V1에 specificity 있으나 filter 추정 불가
4. **Family-specificity** — Machado/2-comp 모두 protan vs deutan을 강하게 구별 못함 (Gen-4 #22)
5. **Per-term cross-ROI 미검증** — z_set(V4) + z_vox(V1) 등 변형 시도 미수행 (Cycle 11 후보)
6. **HC LOCO FPR=100%** — baseline_rho confound 통제 부재. specificity claim에서 conservative reporting 필수

## 3.5. Cycle 12 plan — Pre-registered cross-ROI LOSS

**동기**: Cycle 11c에서 검토했던 옵션 A를 사용자가 결정 진행.

**Pre-registered (a priori) loss formula**:
```
L_cross(β_s, β_c) = α · l_topk_jaccard(V4, β_s, β_c)   ← LOCO-derived, V4 (forward gate)
                  + β · l_rank(V1, β_s, β_c)            ← RDM-like (1 − Spearman), V1 (SRM 강한 ROI)
                  + λ · Tikh(β_s, β_c)
```

**근거 (모든 CVD에 동일하게 적용, post-hoc 아님)**:
- l_topk(V4): forward LOCO p=0.044 (sub-08 V4 2-comp p=0.004, sub-09 V4 2-comp p=0.035)
- l_rank(V1): SRM 개인 sub-09 V1 p=0.007, sub-08 V2 p=0.040 → V1/V2 RDM 차이 강함. xnobis cosine과 동일 family (rank correlation of vulnerability structure)
- λ=0.2 Tikh: Cycle 1~10 동일

**왜 가능한가**: landscape JSON에 9개 metric × 2501 grid 모두 저장됨 → 재계산 비용 0.

**검증 항목**:
1. (β_s, β_c) joint minimum이 same-ROI loss와 다른가?
2. 새 (β_s, β_c)로 specificity (cycle 7 selection rule) 평가 — sub-09 robust 회복?
3. Pre-image filter 형태 변화 — 행동 효과 예측 다른가?
4. HC LOO에서 같은 cross-ROI loss로 FP 발생률

**우려 (anti-sycophancy)**:
- α=β=1 default — 정당화 약함, sensitivity sweep 필요
- l_rank와 l_topk 단위 다름 (둘 다 [0,1] 범위지만 분포 다를 수 있음)
- Phase 3 전 filter parameters 재유도 = "Phase 2 종결" 번복

**진행 여부**: 사용자 결정 → 진행. 결과는 Cycle 12로 기록.

### Cycle 13 결과 (CRITICAL — baseline_sp confound 정량)

**Family assignment 검증** (cone-test 가정 옳은가?):
- sub-08 deutan: data-driven으로도 deutan win, margin +11~+15 ✓
- sub-09 protan: data-driven으로도 protan win, V1+V4 sum margin −5.79 ✓
- 단 sub-09 단일 ROI margin 약함 (−1.76)

**Baseline_sp 회귀 보정 결과**:
| Cell | HC corr(baseline_sp, z) | sub-08 z_residual | sub-09 z_residual |
|---|---:|---:|---:|
| **V4|V4 deutan** | **−0.968** | **−58.93 ✓✓** | −3.49 |
| V4|V4 protan | −0.439 | −1.39 NOT | **−1.25 NOT** |
| **V1|V4 deutan** | −0.542 | **−2.74 ✓** | −0.80 NOT |
| V1|V4 protan | −0.594 | +0.65 NOT | **−1.01 NOT** |

**결정적 발견**:
1. HC V4 z_combined는 거의 baseline_sp가 결정 (r=−0.968)
2. sub-08 deutan만 baseline 보정 후 robust specific
3. **sub-09 protan은 어떤 cell에서도 baseline 보정 후 NOT specific** — Cycle 11 V1|V4 specificity 회복 주장은 baseline 우연 일치
4. → Phase 3 primary는 sub-08만

### Cycle 12 결과 (실행 완료)

**Filter parameter shift**:
- sub-09 V4-only: **(0, 0) degenerate** → cross-ROI: **(30, 26) non-trivial** ✓ degeneracy 해소
- sub-09 cross-ROI (30, 26)이 cycle8_preimage V1+V4 avg (30.5, 12)와 거의 일치 → 독립 derivation 수렴
- sub-08: (58,-28) → (68,-38), 같은 방향 강화
- HC sub-04 (64,-36)→(18,2), sub-06 (62,36)→(0,0): null 방향 ✓

**Specificity (L_cross 직접 비교)**:
- sub-08 z=-4.78 (V4-only -4.54보다 강화) ✓
- sub-09 z=-0.46 (V4-only +0.59보다 개선이지만 여전히 within HC range) — miss
- HC sub-02 FP 해소 (-3.80 → -0.83) ✓
- HC sub-06: cross-ROI에서 매우 나쁜 fit (z=+3.92)

**핵심 분리**:
- ✓ Cross-ROI loss = **더 좋은 parameter estimator** (sub-09 degeneracy 해소)
- ✗ Cross-ROI loss = **specificity 지표는 아님** (sub-09 z=-0.46)

**Phase 3 함의**:
- sub-09 filter parameters가 두 독립 derivation에서 수렴 → confidence 향상
- 단 specificity 자체는 여전히 marginal — 행동 검증 결정적
- Pre-image viz: `phase3_sub-09_cross_roi_loss_cycle12.png`, `phase3_sub-08_cross_roi_loss_cycle12.png`

## 4. 다음 작업

| 우선순위 | 작업 | 예상 영향 |
|---|---|---|
| 1 | (완료) Cycle 11 cross-ROI specificity → 11b 이론 검증 → 11c loss 변경 보류 | sub-09 same-ROI exploratory 유지 |
| 1.5 | **Cycle 12 — Pre-registered cross-ROI LOSS** (사용자 결정 진행) | sub-09 filter parameters 재유도 |
| 2 | Phase 3 design pre-registration | sub-08 primary, sub-09 exploratory |
| 3 | sub-04 행동 데이터 검토 (Ishihara, anomaloscope) | HC 가정 검증 |
| 4 | Manuscript skeleton (Cycle 11 후) | Phase 3 trigger 직전 |

---

## 부록: 폴더별 핵심 결과 위치

| 폴더 | 주요 결과 |
|---|---|
| `phase1_procrustes_decoding/` | HC-CVD voxel correlation (sub-08 V4 +0.118) |
| `phase2_procrustes_cvd_hc/` | RDM 차이 (descriptive only) |
| `phase2_SRM_across_between/` | sub-09 V1 p=0.007*, sub-08 V2 p=0.040* (descriptive) |
| `phase3_decoder_comparing/` | Pooled W LOCO/LORO 결과 |
| `future_phase1_forward_model/results/validation/` | LOCO json (ridge_gcv) |
| `future_phase2_filter_optimization/action_plans/` | PLAN04, NARRATIVE 등 |
| `future_phase2_filter_optimization/results/cycle_filter_refinement/` | Cycle 1~10f 결과 |
| `future_phase2_filter_optimization/results/figures/filter_visualization_phase3/` | **Phase 3 candidate filters viz** |
| `future_phase3_behavioral_analysis/` | (planning, 미작성) |
