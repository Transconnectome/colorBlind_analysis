# Phase 2 Filter Optimization — Verification Closure

_Last updated: 2026-06-01_

## Context

Phase B v6 PCA 45° categorical RDM atom pipeline (`scripts/s10b_v6_pca_rdm.py`)
+ 2-component model class
(`δθ(c) = β_s·cos(θ_c − 90°) + β_c·cos(θ_c − θ_conf)`, θ_conf={protan:16°,
deutan:150°}) production fits per CVD subject:

| Candidate | (β_s, β_c) | Combo | Subject |
|---|---|---|---|
| **S08-stable**  | (+38, −10) | γALL\|RDMV1\|noLOCO | sub-08 deutan |
| **S08-robust**  | (+6,  −42) | γOY\|RDMV2\|noLOCO  | sub-08 deutan |
| **S09-primary** | (+2,  +24) | γALL\|RDMV1\|noLOCO | sub-09 protan |

Verification spans **4 tests**: (1) parameter identifiability at production
argmin + (2) three null/specificity tests.

---

## Test 1 — Parameter recovery at production argmin (identifiability)

| 항목 | 내용 |
|---|---|
| **내용** | GT = (production β_s, β_c) 에서 voxel-level synth (HC_k W + spatial PCA(20) + AR(1) noise) + **GT-consistent fake JND** (`synthesize_fake_jnd` in `scripts/forward_voxel_synth.py`: `pred = pool_baseline × (d_phys/d_perc(GT)) + N(0, pool_sd)`). 동일 pipeline 으로 (β_s, β_c) 재추정. |
| **목적** | production argmin 이 자기 자신 GT 를 재회수하는가 — 그 점 근처에서 식별가능(identifiable) 한가. |
| **표본** | n = 140 (7 HC donor × M=20 noise) per candidate, v2 (GT-consistent JND). |
| **평가 지표** | `f10°` (within 10° fraction, both axes), median bias per axis. **PASS** = f10° ≥ 0.5 AND \|bias\| < 10° both axes. |
| **결과** | **3 후보 모두 FAIL.** |

| Candidate | bias (β_s, β_c) | f10° | 판정 |
|---|---|---|---|
| S08-stable  | (−6, +19)  | 0.10 | FAIL |
| S08-robust  | (+16, −4)  | 0.26 | FAIL |
| S09-primary | (+11, −27) | 0.14 | FAIL |

**축-비대칭 식별가능성** (v1 → v2 fix 가 입증): 큰 \|GT\| 축 (S08-robust β_c=−42,
S08-stable β_s=+38) 은 일관된 합성 JND 에서 회수도 개선
(β_c bias 30.9°→4.7°, β_s bias 17.0°→7.6°). 작은 \|GT\| 축은 noise floor 아래.

---

## Test 2a — (0,0) recovery / algorithm validation at null

| 항목 | 내용 |
|---|---|
| **내용** | GT = (0, 0) 에서 voxel-level synth + donor 의 real JND. 영점에서는 donor real JND 가 본질적으로 GT=0 시그니처 → synth design contamination 없는 깨끗한 영점 테스트. |
| **목적** | 신호 없음 (영점) 으로부터 영점을 재회수하는가. Pipeline 의 noise floor / built-in bias 측정. **Load-bearing evidence** — 합성-디자인 잡음에서 자유롭기 때문 (donor real JND 와 GT=0 synth 가 동일 시그니처). |
| **표본** | n = 140 (7 HC donor × M=20 noise) per candidate (각 후보의 fitting cell). |
| **평가 지표** | median(\|β_s\|), median(\|β_c\|), p95, f10°_origin. **PASS** = \|bias\| < 5° both axes (clean zero recovery). |
| **결과** | **3 후보 모두 FAIL.** |

| Candidate | \|β_s\|_med (IQR) | \|β_c\|_med (IQR) | β_s p95 | β_c p95 | f10°_origin |
|---|---|---|---|---|---|
| S08-stable  | 20° (22)   | 26° (16)   | 42° | 46° | 0.00 |
| S08-robust  | 22° (40)   | 26° (10.5) | 50° | 44° | 0.00 |
| S09-primary | 16° (17.5) | 24° (9)    | 30° | 48° | 0.00 |

**모든 후보에서 f10°_origin = 0/140** — 영점 합성으로부터 단 한 번도 origin
10° 이내 안착 못함. Production argmin 의 **effective uncertainty 하한**이
~20° / ~25° 임을 직접 시사.

---

## Test 2b — HC as pseudo CVD / specificity (B1, Source B)

| 항목 | 내용 |
|---|---|
| **내용** | HC_k 의 **진짜** amplitudes 를 fake CVD 로 사용 (7 HC carriers, deterministic per candidate). 합성 아닌 실제 HC 데이터를 CVD 자리에 대입. |
| **목적** | production CVD 적합이 HC pseudo-CVD 분포보다 더 좋은가 — descriptive specificity. §0 framework: **descriptive only, selection criterion 아님.** |
| **표본** | 7 HC carriers per candidate. |
| **평가 지표** | `rank_distance` = production fit distance 가 HC pseudo-CVD 7 개 중 차지하는 percentile (one-sided high). **PASS** = rank = 1.0 (CVD 가 모든 HC 초과). |
| **결과** | **3 후보 모두 FAIL** (§0 에 따라 selection 기준은 아니지만 descriptive 도 약함). |

| Candidate | rank_distance | 판정 |
|---|---|---|
| S08-stable  | 0.500 | FAIL (HC 분포 한가운데) |
| S08-robust  | 0.875 | FAIL (HC 분포 안쪽 상위) |
| S09-primary | 0.875 | FAIL (HC 분포 안쪽 상위) |

---

## Test 2c — Color (label) permutation / within-subject SIG (Source C)

| 항목 | 내용 |
|---|---|
| **내용** | 실제 CVD 데이터의 trial label 을 무작위 셔플 (N=1000). HC pool 은 그대로 유지. |
| **목적** | within-subject 의 색-라벨 신호가 production loss 의 낮은 꼬리에 기여하는가 — label-shuffled null 대비 magnitude-based 유의성. |
| **표본** | N = 1000 permutations per candidate. |
| **평가 지표** | `p_perm = (#(perm_loss ≤ real_loss) + 1) / (N + 1)`, one-sided (lower = better). **PASS** = p_perm < 0.05. |
| **결과** | **3 후보 모두 FAIL.** |

| Candidate | real_loss | perm 5% 컷 | p_perm | 판정 |
|---|---|---|---|---|
| S08-stable  | −1.236 | −2.613 | 0.866 | FAIL |
| S08-robust  | −2.892 | −3.136 | 0.167 | FAIL |
| S09-primary | −1.681 | −3.053 | 0.471 | FAIL |

---

## 종합 verdict

FDR-corrected (BH α=0.05), 3 candidates × 3 main tests = 9 tests:
**유의한 것 없음.** 가장 무거운 증거는 **Test 2a (영점 회수 실패)** —
synth design contamination 으로부터 자유로운 깨끗한 noise floor 측정에서
~20°/25° bias.

(β_s, β_c) production argmin 의 허용 해석:
- **금지**: 절대값 physiological 해석 (cone-shift 정도, cortical rotation 각도)
- **허용**: 저차원 descriptive embedding 으로 사용
- **금지**: specificity claim (§0 framework decision)

## Source files

- Recovery v2 (Test 1): `results/redteam/param_recovery_voxel_v6_pca_v2.json`
- B1/B2 (Test 2a + 2b): `results/redteam/null_within_hc_loo_v6_pca.json`
- Source C (Test 2c): `results/redteam/null_label_permutation_v6_pca.json`
- Verdict matrix: `results/redteam/verdict_matrix_v6_pca_v2.json` / `verdict_matrix_v2.md`
- Uncertainty summary: `results/redteam/uncertainty_summary.json` / `uncertainty_summary.md`
