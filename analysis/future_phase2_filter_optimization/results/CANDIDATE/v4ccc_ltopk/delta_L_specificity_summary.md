# Δ_L specificity — V4-CCC + l_topk (descriptive diagnostic)

**Loss**: `L = 1·L_ccc + 0.5·l_topk(V4, K=3) + 0.1·L_smooth`  
**L_smooth normalization**: `(β_s² + β_c²) / 32400` (HC sanity의 cached `l_smooth`는 ~0.5008 factor 차이 — 양쪽을 같은 공식으로 재계산함)  
**Simulator**: wretrained (vuln_sim cached per cell, 재시뮬레이션 없음)  
**HC pool**: sub-01..06 (sub-07 V4 16 voxels → nan 위험으로 제외)  

## 1. 정의

`Δ_L = L(β_s=0, β_c=0) − L(argmin)` — fitting이 baseline 대비
얼마나 loss를 줄였는지. norm metric (parameter magnitude)이 random walk
편향에 취약했던 한계를 보완하기 위한 보조 지표.

**§0 compliance**: 이 metric은 *descriptive diagnostic*이며,
selection criterion이나 새 specificity claim의 근거가 아니다.
HC FPR 100% (`hc_specificity/`)와 baseline_ρ confound (Cycle 13)는
measurement family 한계로 확정되어 있다.

## 2. 피험자별 Δ_L (argmin 기준)

| subject | role | argmin (β_s, β_c) | L_baseline | L_min | Δ_L |
|---|---|---|---|---|---|
| sub-01 | HC | (24, +44) | 1.0215 | 0.1744 | **0.8471** |
| sub-02 | HC | (42, +42) | 0.8688 | 0.6496 | **0.2192** |
| sub-03 | HC | (24, +44) | 1.0918 | 0.6859 | **0.4059** |
| sub-04 | HC | (4, -50) | 1.0761 | 0.6479 | **0.4282** |
| sub-05 | HC | (48, -10) | 1.0633 | 0.7220 | **0.3412** |
| sub-06 | HC | (50, +42) | 0.8812 | 0.5203 | **0.3609** |
| sub-08 | CVD (deutan) | (44, +28) | 0.8298 | 0.4560 | **0.3738** |
| sub-09 | CVD (protan) | (30, +46) | 0.9546 | 0.6074 | **0.3472** |

**HC Δ_L 분포 (n=6, argmin)**: mean=0.4338, std=0.2152, range [0.2192, 0.8471]  
**HC bootstrap mean Δ_L 95% CI** (n_boot=10000): [0.3051, 0.6086]  

**CVD argmin Δ_L**:
- sub-08: Δ_L = 0.3738
- sub-09: Δ_L = 0.3472

## 3. Candidate filter Δ_L vs HC bootstrap

Δ_L_candidate = L_baseline − L(β_s, β_c). boot_frac = P(HC bootstrap mean Δ_L < CVD candidate Δ_L), CVD가 HC의 best-possible improvement 분포를 얼마나 초과하는지 (conservative bar).

| Filter | subject | β=(β_s, β_c) | Δ_L_cand | boot_frac | Verdict | note |
|---|---|---|---|---|---|---|
| BEST V4-CCC+l_topk | sub-08 | (+44, +28) | +0.3738 | 0.2651 | ✗ inside HC CI | argmin of subject under primary loss |
| BEST V4-CCC+l_topk | sub-09 | (+30, +46) | +0.3472 | 0.1407 | ✗ inside HC CI | argmin of subject under primary loss |
| V4-CCC alone argmin | sub-08 | (+16, +40) | +0.0189 | 0.0000 | ✗ inside HC CI | V4-CCC alone (λ_topk=0) |
| V4-CCC alone argmin | sub-09 | (+30, +46) | +0.3472 | 0.1407 | ✗ inside HC CI | V4-CCC alone (λ_topk=0) |
| Phase A LOCO canonical | sub-08 | (+38, -14) | +0.1030 | 0.0000 | ✗ inside HC CI | §3 canonical, behav-PASS for sub-08 |
| Phase A LOCO canonical | sub-09 | (+6, -22) | -0.1242 | 0.0000 | ✗ inside HC CI | Phase A LOCO V4 2-component |
| Tier 2 V4-CCC+SRM RDM | sub-08 | (+50, +24) | +0.1458 | 0.0000 | ✗ inside HC CI | Tier 2 argmin (V4-CCC+SRM RDM) |
| Tier 2 V4-CCC+SRM RDM | sub-09 | (+34, +44) | +0.3451 | 0.1322 | ✗ inside HC CI | Tier 2 argmin (V4-CCC+SRM RDM) |
| Cycle 14 cross-ROI | sub-08 | (+58, -36) → (+50, -36) [PROXY] | -0.0608 | 0.0000 | ✗ inside HC CI | OUT OF GRID (bs∈[0,50]); using nearest (50,-36) as proxy |
| Cycle 14 cross-ROI | sub-09 | (+32, +22) | +0.0095 | 0.0000 | ✗ inside HC CI | cycle 14 cross-ROI RDM |

## 4. 해석

- **sub-08 (deutan) argmin Δ_L = 0.3738** vs HC range [0.2192, 0.8471]. boot_frac vs HC bootstrap mean = 0.2651.
- **sub-09 (protan) argmin Δ_L = 0.3472** vs HC range [0.2192, 0.8471]. boot_frac vs HC bootstrap mean = 0.1407.

### 4-1. Δ_L vs norm metric — 어느 쪽이 더 분리적인가?

이전 norm metric (`hc_specificity.csv`)에서는 BEST 후보들이 모두 `boot_frac < 0.90`으로 HC CI 내부에 묶였다. Δ_L metric에서는:

| 후보 (β_s, β_c) | subject | norm boot_frac | Δ_L boot_frac |
|---|---|---|---|
| BEST V4-CCC+l_topk (44, +28) | sub-08 | 0.1323 | **0.2651** |
| BEST V4-CCC+l_topk (30, +46) | sub-09 | 0.5439 | **0.1407** |
| Tier 2 (50, +24) | sub-08 | 0.6328 | 0.0000 |
| Tier 2 (34, +44) | sub-09 | 0.6372 | 0.1322 |
| V4-CCC alone (16, +40) | sub-08 | 0.0000 | 0.0000 |
| §3 canonical (38, -14) | sub-08 | 0.0000 | 0.0000 |
| Phase A LOCO (6, -22) | sub-09 | 0.0000 | 0.0000 |

- **양 CVD 모두 boot_frac < 0.90** — Δ_L 역시 HC와 분리에 실패.
- **균등하게 더 좋지는 않다.** sub-08은 norm 0.13 → Δ_L 0.27로 약간 상승,
  sub-09는 norm 0.54 → Δ_L 0.14로 *떨어진다*. 두 metric은 서로 다른 ranking을
  주지만 어느 쪽도 0.90 문턱을 넘기지 못한다.
- 공통 원인 추정: HC도 1326-cell 공간을 자유롭게 탐색해 random walk로 자기
  vuln_obs에 우연히 fit하는 cell을 찾아낸다 — HC sub-01 Δ_L = 0.847이 그 예
  (다음으로 큰 HC sub-04 = 0.428의 약 2배). 이 outlier가 bootstrap mean을
  끌어올려 CVD argmin이 분포 *아래*에 위치하게 만든다.

> **Note (HC sub-01 outlier)**: 6개 HC bootstrap resample 중 sub-01이 약 63%에
> 포함되어 CI 상한을 지배. sub-01 제외 시 CI는 더 좁아져 CVD가 더 distinct하지
> *못한* 방향으로 강해질 가능성이 큼 — bootstrap이 사례적으로 CVD에 유리하지
> 않은 outlier 효과.

### 4-2. 피험자별 후보 비교

**sub-08** (Δ_L 큰 순):
- `BEST V4-CCC+l_topk` β=(+44, +28): Δ_L=+0.3738, boot_frac=0.2651, ✗ inside HC CI
- `Tier 2 V4-CCC+SRM RDM` β=(+50, +24): Δ_L=+0.1458, boot_frac=0.0000, ✗ inside HC CI
- `Phase A LOCO canonical` β=(+38, -14): Δ_L=+0.1030, boot_frac=0.0000, ✗ inside HC CI
- `V4-CCC alone argmin` β=(+16, +40): Δ_L=+0.0189, boot_frac=0.0000, ✗ inside HC CI
- `Cycle 14 cross-ROI` β=(+58, -36): Δ_L=-0.0608, boot_frac=0.0000, ✗ inside HC CI

**sub-09** (Δ_L 큰 순):
- `BEST V4-CCC+l_topk` β=(+30, +46): Δ_L=+0.3472, boot_frac=0.1407, ✗ inside HC CI
- `V4-CCC alone argmin` β=(+30, +46): Δ_L=+0.3472, boot_frac=0.1407, ✗ inside HC CI
- `Tier 2 V4-CCC+SRM RDM` β=(+34, +44): Δ_L=+0.3451, boot_frac=0.1322, ✗ inside HC CI
- `Cycle 14 cross-ROI` β=(+32, +22): Δ_L=+0.0095, boot_frac=0.0000, ✗ inside HC CI
- `Phase A LOCO canonical` β=(+6, -22): Δ_L=-0.1242, boot_frac=0.0000, ✗ inside HC CI

### 4-3. 행동 검증 권고 (descriptive)

§0에 따라 Δ_L은 model class / filter selection을 결정하지 않는다. 아래는 *descriptive* 해석으로, ground truth는 행동 검증이다 (§A4, §A9).

- **sub-08 (deutan)**: Δ_L 상위 후보는 `BEST V4-CCC+l_topk` β=(+44, +28)
  (Δ_L=+0.3738, boot_frac=0.2651). **그러나 boot_frac이 0.90 미만이므로 HC
  distribution 내부 위치 — Δ_L 기준 상위라 해도 통계적으로 distinct 아님.**
  sub-08의 §3 canonical (β_s=38, β_c=−14) [behav-PASS, behav_validation §3]
  결정은 그대로 유지된다. Δ_L은 selection rule이 아니다.
- **sub-09 (protan)**: Δ_L 상위 후보는 `BEST V4-CCC+l_topk` β=(+30, +46)
  (Δ_L=+0.3472, boot_frac=0.1407). 역시 0.90 미만. 행동 검증 (Track A 진행 중)
  이 model class 결정의 ground truth로 남으며, Δ_L은 보조 정보로만 기록.
- **`Cycle 14 cross-ROI sub-08` proxy (50, -36)** Δ_L = −0.06 — baseline보다
  *나빠진다*. (50, -36)은 proxy가 아닌 실제 그리드 점이며 (58, -36)에서
  bs만 잘렸을 뿐. 이 결과는 그 자체로 의미 있음: V4-CCC + l_topk loss 공간에서
  Cycle 14 후보 방향이 sub-08의 vuln_obs와 부합하지 않는다는 신호.

## 5. Files

- `delta_L_per_subject.csv` — 8 피험자(HC 6 + CVD 2) argmin Δ_L 원자료
- `delta_L_specificity.csv` — candidate filter별 Δ_L_cand + boot_frac
- `delta_L_distribution.png/.pdf` — HC bootstrap 분포 + CVD 수직선
- 본 문서

## 6. Caveats

- **L_smooth normalization 통일**: HC sanity landscape의 cached `l_smooth`는 사용하지 않고 `(β_s² + β_c²)/32400`로 양쪽 재계산. cached 값은 ~0.5008 factor 차이로 두 그룹 간 비교가 비뚤어졌었음.
- **Out-of-grid candidate**: Cycle 14 sub-08 (58, -36)은 V4-CCC 그리드 (bs∈[0,50]) 밖. 가장 가까운 그리드점 (50, -36)을 proxy로 사용.
- **Discrete top-K**: l_topk Jaccard는 K=3에서 4개의 이산값만 가짐. HC도 1326 cell 중 어디선가 우연히 top-3을 맞출 수 있어 random-walk sensitivity가 norm metric과 유사할 가능성.
- **HC pool n=6**: bootstrap CI는 작은 표본으로 wide. sub-04 outlier 효과는 6×6 resample에서 평탄화됨.
