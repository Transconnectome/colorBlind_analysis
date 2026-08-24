# 추가 분석 현황 — 외부 검토 대응 (2026-08-15)

> **입력**: [`REVIEW_JOURNAL_STRATEGY_2026-08-15.md`](REVIEW_JOURNAL_STRATEGY_2026-08-15.md) (외부 검토 1차 원문) + 2차 검토 (2026-08-15 오후, intervention identifiability 제기) **선행 정본**: [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md), [`METHODS_REVISION_STATUS_2026-08-07.md`](METHODS_REVISION_STATUS_2026-08-07.md) **수치 정본**: `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`

---

## 0. 표기 규약 — 왜 문자 코드를 쓰지 않는가

선행 문서들은 `F1`, `U2`, `A`–`I` 같은 문자 코드를 쓴다. 그 코드는 **해당 문서 안에서만 뜻이 있고 무엇을 가리키는지 이름에 담겨 있지 않다.** 실제로 `U3` 는 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md:364` 에서 "색 특이성 35셀 BH-FDR" 로 이미 쓰이고 있어, 이 세션 초반에 필터 분석에 같은 코드를 붙였다가 충돌시켰다.

**이 문서는 코드 대신 분류축으로 부른다.** 모든 분석은 아래 네 축의 좌표 하나다.

### 축 1 — 세션 (어느 촬영인가)

| 이름 | 뜻 | 데이터 |
|---|---|---|
| `exp1` | 1차 촬영. 특성화·모형 적합·필터 유도 | `full_dataset_C010` |
| `exp2` | 2차 촬영. 동결 필터의 전향적 검증 | `full_dataset_C010_exp2{,_matched}` (서버 전용) |

### 축 2 — 전처리 arm (무엇을 흔드는가)

디스크·코드에 실재하는 이름을 그대로 쓴다 (`analysis/future_phase1_sensitivity/scripts/_perm_adjacent_arm.py:10-12`).

| 이름 | 무엇을 바꾸나 | 성격 | 상태 |
|---|---|---|---|
| `with_residuals` | 2단계 설계행렬에 drift 회귀자만 | **정본.** 논문 보고값의 출처 | 완료 |
| `motreg` | drift + MCFLIRT 12 회귀자 | **시간축.** 시계열에서 움직임 상관 성분을 뺀다. 복셀은 제자리 | 완료 |
| `motshift` | 같은 12 회귀자, **시간 정렬만 파괴** | `motreg` 의 **짝맞춘 대조.** 자기상관·스펙트럼은 같고 움직임은 하나도 제거 못 함 → 두 arm 의 차 = 움직임 제거분 | **완료** |
| `hmc` | 볼륨별 강체행렬을 BOLD→T1w 에 **합성**해 보간 1회로 재정렬 | **공간축(런 내부).** 복셀이 시점마다 담는 조직을 교정. 회귀로는 못 고치는 것 | 미실시 |
| `anat_harmonized` | 양 세션 해부 처리 통일 (exp2 도 ezBIDS) | **세션 간** 비교 가능성 | 미실시 |

**`motshift` 는 완료된 대조군이지 미실시 항목이 아니다.** 색 특이성 통과 셀이 `with_residuals` 7 · `motreg` 15 · `motshift` 3 으로, 회귀자 추가만의 순수 비용은 검출을 **낮추는**(7→3) 방향임을 보였다. 이것이 "7→15 증가는 회귀자 부산물" 해석을 기각한 근거이며 §S13 문안으로 확정되어 있다 (`REVISION_PLAN_PRESUBMISSION_2026-08-10.md` 항목 C).

**`motreg` 대 `hmc`.** `motreg` 는 값을 빼는 것이고 `hmc` 는 볼륨을 되돌리는 것이다. 문제의 본체 — 같은 복셀 인덱스가 시점마다 다른 조직을 담는 것 — 는 값을 빼서 고쳐지지 않는다. 그래서 `motreg` 는 대용품, `hmc` 가 본체다.

### 무엇이 표준 관행인가 (§S2 서술 순서를 정하는 사실)

| | 표준인가 | 어디서 |
|---|---|---|
| **HMC (재정렬)** | **거의 보편** | fMRIPrep, SPM `realign`, AFNI `3dvolreg`, FSL FEAT `MCFLIRT` |
| **motion regressors** | **표준 관행** | 다운스트림 GLM. fMRIPrep 은 confound 를 *계산만* 하고 회귀는 사용자 몫 |
| **`motshift`** | **비표준 — 우리 커스텀 대조군** | 순환이동 nuisance 대조는 방법론 문헌에 간간이 나오나 표준 파이프라인에 없음 |

**두 가지가 따라 나온다.**

1. **표준 관행에서 motion regressor 는 재정렬된 데이터 *위에* 얹는다.** 우리는 재정렬을 하지 않은 채 **재정렬 대신** 회귀자를 넣었다. 즉 `motreg` arm 은 "표준을 따랐다" 의 근거가 되지 못한다 — 표준의 **앞단이 빠진 채 뒷단만** 한 것이다. → **§S2 방어를 `motreg` 로 시작하면 안 된다.** fMRIPrep 을 아는 리뷰어는 즉시 본다.
2. **재정렬을 넣지 못한 이유(보간 2회)는 원리적 제약이 아니었다.** fMRIPrep 은 HMC·SDC·정합· 정규화를 **하나의 변환으로 합성해 보간을 1회로 유지**한다 — §3.3 이 제안하는 방식이 그것이다. 따라서 §S2 에 `fMRIPrep 과 동일한 single-interpolation 합성` 이라고 쓸 수 있고, 방어가 쉬워진다.

3. **`motshift` 는 처음 보는 물건이므로 §S 에서 반드시 설명과 함께 제시한다.** 그리고 `motreg` 의 전제가 아니다 — 독립 실행이며, `motreg` 결과를 *해석*하기 위한 사후 대조군이다.

### 축 3 — 분석 층위 (인과 사슬의 어느 칸인가)

| 이름 | 무엇이 흔들리는가 |
|---|---|
| `endpoint` | 신경 종점 — 보간 게이트, SRM disparity, 색 특이성 |
| `beta` | 적합 파라미터 $(\beta_s, \beta_c)$ |
| `filter` | **pre-image — 피험자가 실제로 본 물리적 변환** |

### 축 4 — 신경 기저

| 이름 | |
|---|---|
| `pca_rdm` | **정본.** PCA top-K=6 → 8×8 상관 RDM |
| `srm_rdm` | SRM 공간. BrainIAK 부재로 `pca_rdm` 이 정본화된 경위 있음 |

**한 분석 = 좌표 하나.** 예: `exp1 · motreg · beta · pca_rdm`. 선행 문서의 문자 코드가 필요할 때는 좌표와 함께 병기한다.

---

## 1. 현황 격자

행 = 전처리 arm(축 2), 열 = 분석 층위(축 3). 전부 `exp1 · pca_rdm` 기준. ✔ 통과 / ✘ 실패 / — 미실시

| arm | `endpoint` | `beta` | `filter` |
|---|---|---|---|
| `with_residuals` (정본) | — 기준 — | — 기준 — | — 기준 — |
| **`motreg`** | ✔ hV4 게이트 생존 ($p$=.013) | deutan ✔ / protan ✘ | deutan ✔ / protan ✘✘ |
| **`motshift`** | ✔ 생존 ($p$=.002) | 미실시 | 미실시 |
| **`hmc`** (올바른 구현) | **—** | **—** | **—** |
| 축 4 교체 `srm_rdm` | ✔ | deutan ✔ / protan ✘ | deutan ✔ / protan ✘ |
| **`exp2` 전 arm** | **—** | 해당 없음 | 해당 없음 |

**산출물 대응** (선행 문서 코드 ↔ 좌표)

| 좌표 | 선행 코드 | 산출물 |
|---|---|---|
| `exp1 · motreg/motshift · endpoint` | F1–F3 | `analysis/future_phase1_sensitivity/results/perm_adjacent_arm_*.json`, `color_specificity_arm_comparison.json` |
| `exp1 · motreg · beta` | U2 | `analysis/phase5_filter_optimization/U2_BETA_SIGN_PRESPEC.md` |
| **`exp1 · motreg · filter`** | *(신규)* | `analysis/phase5_filter_optimization/FILTER_ROBUSTNESS_ARMS.md` |
| `srm_rdm · filter` | *(기존)* | 메모리 `project_color_specificity_gap.md` |

### 격자에서 바로 읽히는 두 가지

**1. protan 필터 불안정은 두 축에서 독립 확인되었다.** `motreg` 만의 얘기가 아니다.

| | `pca_rdm` (정본) | `srm_rdm` | `pca_rdm` + `motreg` |
|---|---|---|---|
| deutan | $(6, -42)$ | $(8, -42)$ | $(20, -48)$ |
| protan | $(2, +24)$ | $(32, 0)$ | $(22, -24)$ |

protan 은 $\beta_c$ 가 **양수·0·음수를 모두 오간다.** deutan 은 셋 다 $-42 \sim -48$ 한 가족이다. 필터 수준 차이: deutan ΔE₀₀ 0.64 (자기 효과 10.7의 6%) / protan **ΔE₀₀ 11.7 > 자기 효과 4.4**.

**2. `hmc` 행이 세 칸 모두 비어 있다.** 그리고 `motreg` 라는 **더 약한** 교란이 이미 protan 필터를 6/8 뒤집었으므로, 공간축이 deutan 필터까지 흔들지 않는다는 보장은 없다. **deutan 강건성은 두 축에서만 검증된 것이지 일반 성질이 아니다.**

---

## 2. 실행 현황 (2026-08-15 종료 시점)

**정렬 기준 두 개.** ① 실패하면 하류가 무의미해지는 것 먼저(게이트) ② 한 산출물이 여러 칸을 채우면 앞으로(레버리지).

### 완료

| # | 작업 | 좌표 | 결과 | 산출물 |
|---|---|---|---|---|
| ✅ | **필터 강건성** | `exp1·motreg·filter` | deutan 0/8 반전 · protan **6/8 반전, 교차평가 무필터보다 악화** | `FILTER_ROBUSTNESS_ARMS.md` |
| ✅ | **SDC 크기 측정** (전 9명) | — | 미분 성분 0.05–0.38 복셀 → **미적용 정당화** | §3.4d–e, `roi_shift_summary.csv` |
| ✅ | **필드맵 정렬 QC** (전 9명) | — | header 정렬 정확, 정합 불량 0명 | `figures/sdc_cohort/` |
| ✅ | **sub-07 진단** | — | 왜곡 아닌 **슬랩 커버리지 실패** (hV4 16/70) | §(2b), `figures/coverage_diag/` |
| ✅ | **`hmc` 재전처리** | `exp1·hmc` | 10명 × 6런 = 60/60, 보간 1회 | `fmriprep_out_method3_hmc_v2` |
| ✅ | **품질 평가** | `exp1·hmc` | 겹침 +0.6% · tSNR −1.7~3.0% → **개선 없음** | §3.4g, `hmc_roi_comparison.json` |
| ✅ | **LOCO 종점** | `exp1·hmc·endpoint` | 게이트 유지 (.011→.023) · 단일사례 미유지 | §3.4h |
| ✅ | **disparity 종점** | `exp1·hmc·endpoint` | protan V1 .007→.077 · **deutan V2 .040→.825 역전** | `disparity_arm_*.json` |
| ✅ | **지표 신뢰도** | — | **ICC(2,1) hV4 0.825 / V1 −0.005** | §3.4i, `arm_agreement.json` |
| ✅ | **run-level bootstrap** | — | arm 간 CI 겹침 17–29% → 런 잡음 아님 | `boot_runs_*.json` |
| ✅ | **MAE 순열 귀무** | — | 이산화 인공물 **아님**; protan 은 어느 arm 도 above-null 아님 | `perm_mae_arm.json` |
| ✅ | **원고 수정안** | — | 본문 7곳 + §S2 문단·표 | [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) |

### 미완 — 우선순위 순

| # | 작업 | 상태 | 비고 |
|---|---|---|---|
| **1** | **`.tex` 실제 반영** (M1–M9, §S2, 표, Fig 4 캡션) | **착수 가능** | Q1–Q3 **결정 완료** (2026-08-16) → 차단 요인 없음 |
| **2** | 선행 정본 A–I 반영 | 미착수 | `REVISION_PLAN_PRESUBMISSION_2026-08-10` — 원고 준비 완료 상태 |
| **3** | 비교자 범위 문서화 | 미착수 | §5. 위 전부와 독립, 저비용 |
| **4** | 8AFC 독립 종점 격상 | 미착수 | §6. 문안, 비용 0 |
| **5** | `anat_harmonized` (ses-2 ezBIDS 디페이싱) | **완료 2026-08-17** | `colorBlind_data/data/2nd_exp/bids_2nd_defaced`. 0복셀 sub-08 30.9% · sub-09 35.1% (ses-1 30.9% / 33.0%). 중시상면 절단면 4장 동일, 뇌 조직 손실 없음. func 8런 + fmap 3종 정상 |
| **6** | `exp2 · anat_harmonized + hmc` | **완료 2026-08-17** | Stage A anat(job 168215) → QC 통과 → B 단일보간 HMC 16/16(168305, 볼륨수 292 전건 일치) → C 진폭 32(168338) → D 종점(168354). 방향 대비 arm 간 역전 = **native 10 중 8 · matched 10 중 5** (두 variant 는 독립이 아니므로 합산하지 않는다; 두 variant 끼리도 불일치). disparity 는 8 중 3 역전이고 사전지정 ROI 대비는 전부 유지. HC 기준은 LOCO 0.456→0.445 불변이나 disparity 는 0.429→0.481 이동 → **disparity 절대값 인용 금지, 순서만 사용** |
| ~~**7**~~ | ~~BBR 실패 QC 그림~~ | **제외 2026-08-17** | 사용자 결정. §S2·§S3 는 **서술 + 선제 공개**로만 간다 (채택 당시 기록 `notion.md:29-35` 근거). 방법 이력 진술이므로 그림 없이 성립 |
| **8** | `exp1·hmc·filter` (β 재적합) | **완료** | 2026-08-16 로컬. `U2_BETA_SIGN_PRESPEC` 절차·판정규칙 그대로, `COLORBLIND_AMP_ROOT` 만 교체 |
| — | 비필터 재검사 세션 | 보류 | 스캔 필요 |

### 결정 기록 (2026-08-16)

| # | 결정 |
|---|---|
| Q1 | **all-ROI sensitivity 표를 싣는다** + 표 아래 선제 문장 + Results §3.2 **해석 범위 진술**(본문이 딛고 서는 두 양만 명시) |
| Q2 | `fig:geometry` 별표를 **패널에서 제거하고 각주로 강등** |
| Q3 | **불요** — ses-2 디페이싱 후 exp2 종점을 재산출하므로 "미실시" 자체가 소멸 |
| 제목 | 후보 4안 기록(T1/T4/T2/T3). `hue-representation` → **`hue-geometry`** |
| 초록 | M7(중간) + **M8(마지막 문장 = 프로그램 + identifiability 한계)** |

문안은 [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) M8·M9·§3.2·§4, 설계 근거는 [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md) §2·§4.1.

### `exp1·hmc·filter` 실행 사양 (재현용)

```bash
conda activate srm
cd analysis/phase5_filter_optimization
export COLORBLIND_AMP_ROOT=$PWD/../phase1_procrustes_decoding/results/visualization/full_dataset_C010_hmc_v2
python scripts/s10b_v6_pca_rdm.py --subject sub-08 --combo-start 15 --combo-end 16
python scripts/s10b_v6_pca_rdm.py --subject sub-09 --combo-start 9  --combo-end 10
# → results/s10_inclusion/u2_hmc_v2/   (u2_baseline · u2_motreg 와 같은 규약)
```

**판정 규칙은 사전 확정된 것을 그대로 쓴다** — `U2_BETA_SIGN_PRESPEC.md` §6 의 주 판정 = $\hat\beta_c$ **부호**, 크기는 판정에 쓰지 않음(2성분 모형은 12/12 절대복구 실패로 descriptive embedding 으로 제한). 조합 전수 탐색·gate 재적용·ROI 재선정은 하지 않는다(selection-rule reformulation 금지). 세 arm 값을 나란히 보고하고 유리한 쪽만 싣지 않는다.

### 판정 — 무엇이 남았나

| 주장 | 상태 |
|---|---|
| HC 에서 hue 보간은 hV4 단독 지지 | **유지** — 4 전처리 arm + ICC 0.825 |
| 8색 식별은 CVD 에서 보존 | **유지** — 두 arm 모두 전 ROI 에서 chance(0.125) 크게 초과 |
| CVD hV4 보간이 HC 보다 유의하게 낮음 | **유지 안 됨** → 대체 서술 (a) |
| 개인마다 다른 ROI 에 왜곡이 편재 | **유지 안 됨** (deutan V2 방향 역전) → 대체 서술 (b) |

### 대체 서술 — 무너진 두 주장을 무엇으로 바꾸는가 (2026-08-17)

**(a) CVD hV4 보간 — "유의하게 낮음" 대신 순위 배치 + 집단/개인 비대칭**

| arm | HC 최소 | deutan | HC 이하 | protan | HC 이하 |
|---|---|---|---|---|---|
| `with_residuals` | 0.312 | 0.250 | **0/7** | 0.125 | **0/7** |
| `motreg` | 0.250 | 0.271 | 1/7 | 0.312 | 2/7 |
| `motshift` | 0.354 | 0.375 | 2/7 | 0.229 | **0/7** |
| `hmc_v2` | 0.333 | 0.354 | 2/7 | 0.271 | **0/7** |

> 네 arm 전부에서, 두 CVD 참가자 어느 쪽에 대해서도 그 이하인 통제군은 **7명 중 최대 2명**이다. 통제군은 네 arm 전부에서 보간 게이트를 통과하고($p$ = .002–.023), 두 CVD 참가자는 **어느 arm 에서도 통과하지 못한다.**

**⚠ 순열 기반 서술은 쓰지 않는다.** protan 은 네 arm 전부 귀무 평균 미만이나 deutan 은 2/4 뿐이고, 무엇보다 **개인 수준 색라벨 순열은 HC 도 5/7 이 실패**해 CVD 를 구분하지 못한다. "CVD 가 순열 미만" 이라고 쓰면 *HC 대부분도 그렇다* 한 문장에 무너진다. 쓸 수 있는 것은 **집단 통과 / 개인 미통과의 비대칭**뿐이다.

**(b) ROI 편재 — "각자 다른 ROI" 대신 상승의 존재 + 최대 영역의 부분적 안정성**

Crawford–Howell 개인 검정, disparity, $t$ ($p$).

| arm | | V1 | V2 | V3 | hV4 |
|---|---|---|---|---|---|
| 정본 | deutan | 1.1 (.157) | **2.1 (.040)** | 1.9 (.052) | 0.2 (.411) |
| 정본 | protan | **3.5 (.007)** | 1.0 (.181) | 0.1 (.466) | 1.1 (.150) |
| `hmc_v2` | deutan | **2.4 (.027)** | −1.0 (.825) | 0.6 (.293) | 0.4 (.351) |
| `hmc_v2` | protan | **1.6 (.077)** | 1.0 (.186) | 1.1 (.151) | 1.4 (.101) |

> 네 셀 전부에서 각 CVD 참가자는 초기 시각영역 **적어도 한 곳**에서 HC 대비 disparity 상승을 보이며($p<.10$), 각 셀의 최대 $t$ 는 **전부 양수**다. protan 에서는 최대 영역이 **두 arm 모두 V1** 로 일치한다. 바뀌는 것은 deutan 뿐이다(V2 → V1).

**deutan V2 는 살릴 수 없다** — $t$ 가 $+2.1 \to -1.0$ 으로 부호가 뒤집힌다. 그러나 *"deutan 에게 상승이 있다"* 는 두 arm 에서 유지된다.

**종합 결론.** 무너진 것은 **어느 영역이 왜곡을 지는가** 이지 **왜곡이 있는가** 가 아니다. 원고는 다음 세 층으로 진술한다.

| 층 | 진술 | 전처리 축 |
|---|---|---|
| 1 | 연속 hue 보간은 통제군에서 hV4 단독으로 지지된다 | **유지** (4 arm, ICC 0.825) |
| 2 | 두 CVD 참가자는 그 지표에서 통제군 분포 하단에 놓이고, 개인 게이트를 통과하지 못한다 | **유지** (순위 배치, 4 arm) |
| 3 | 두 CVD 참가자 모두 초기 시각영역 중 적어도 한 곳에서 기하 왜곡을 보이며, 어느 영역이 최대인지는 deutan 에서 분석 선택에 의존한다 | **부분 유지** |

**금지**: `significantly below controls`, `localized to a different area in each`, `individual-specific cortical distortion`.
| 필터 구성·역산 (수학) | 불변 |
| deutan 필터 강건성 | **유지** (시간·기저·**공간** 3축) — 단 교란 arm 에서 boundary_rate .09→.72 |
| protan 필터 강건성 | **유지 안 됨** (3축 모두 반전; 정본↔motreg 지지집합 부호 비중첩) |
| 심리물리 결과 | 불변 (전처리 무관) |

**8-way 확인 완료 (2026-08-15).** 전방 인코딩 모형 LORO 8-way 를 두 arm 에 직접 계산했다.

| ROI | HC 평균 | | deutan | | protan | |
|---|---|---|---|---|---|---|
| | primary | hmc | primary | hmc | primary | hmc |
| V1 | 0.571 | 0.515 | 0.562 | 0.229 | 0.562 | 0.521 |
| V2 | 0.574 | 0.512 | 0.521 | 0.521 | 0.562 | 0.333 |
| V3 | 0.589 | 0.560 | 0.375 | 0.479 | 0.458 | 0.500 |
| hV4 | 0.500 | 0.577 | 0.375 | 0.583 | 0.375 | 0.396 |

chance = 0.125. **최저 셀(deutan V1 hmc 0.229)도 chance 의 1.8배다.** `All eight colors remained decodable in both CVD participants` 는 **두 arm 에서 유지된다.**

*단서*: 발표 Figure 3A 는 SRM 공간 LORO 이고 위는 진폭 위 직접 계산이므로, 정확 재현이 아니라 **구조적 확인**이다. 정성 주장(전 ROI chance 초과)은 두 계산 모두에서 성립한다.

---
### 2.1 `exp1` 작업을 `anat_harmonized` 앞에 두는 근거

"파이프라인을 먼저 통일하고 민감도를 보는 것이 안전하다"는 원칙은 옳다. **다만 그 원칙이 적용되는 대상은 `exp2` 다.**

| | 지금 돌려도 되는가 | 왜 |
|---|---|---|
| `exp1 · hmc` | **된다** | `exp1` 은 이미 내부적으로 일관됨 — 9명 전원 ezBIDS + 디페이싱 + 동일 정합. **`exp2` 를 디페이싱해도 `exp1` derivatives 는 변하지 않는다** |
| `exp2 · hmc` | **안 된다** | 곧 폐기할 파이프라인 위의 숫자가 되고 재처리를 두 번 하게 된다 |

`exp1` 을 앞에 두는 이유는 하나다 — **`exp1·hmc` 만이 시나리오 C(핵심 세션-1 결과가 전처리에 민감)를 낼 수 있다.** 여기서 hV4 게이트가 무너지면 `exp2` 대칭화는 무의미해지므로, ezBIDS 업로드·재처리 비용을 쓰기 전에 확인한다.

§4.3 의 예비 분기(디페이싱이 `exp2` 정합을 오히려 나쁘게 만들면 공통 해부 기준으로 승격)로 가더라도 `exp1` 은 그대로다.

---

## 3. 작업 1 — 표준 단계 민감도 arm (정본 교체 아님)

**범위 확정 (2026-08-15 사용자 결정).** 정본 파이프라인과 본문은 **그대로 둔다.** 새 arm 은 §S2 에 싣는 **민감도 검사**이고, 목적은 표준 단계 미적용이 **측정으로 정당화되는지** 확인하는 것이다. 정본 교체·primary 승격은 이 작업의 범위가 아니다.

> `HMC_REANALYSIS_PRESPEC.md` 는 어시스턴트가 작성한 **내부 초안**이며 사전등록이 아니다. 그 §4 의 "Primary = HMC arm" 은 구속력이 없다. 다만 저장소 공개 시 사전등록으로 오독될 수 있으므로 파일 상단에 내부 초안 표시가 필요하다.

### 3.1 정본에서 실제로 빠진 것 (코드 실사, 2026-08-15)

`run_method3_header_mi_all_subjects.sbatch` + `run_full_dataset_C010.py`

| 단계 | 정본 | 근거 | 표준인가 |
|---|---|---|---|
| **HMC (재정렬)** | **없음** | `mcflirt` 0회. `applywarp --in=${BOLD_FILE}` = BIDS 원본 직접 (L218/394/446) | **보편** |
| **motion regressors** | **없음** | `MOTION_TISSUE = False` (L42) | 표준 관행 |
| **SDC** | **없음** | `topup`/`fugue` 0회. **필드맵은 취득했는데 미소비** | 데이터 있으면 표준 |
| slice timing | 없음 | `slicetimer`/`3dTshift` 0회 | 흔함 |
| smoothing | 없음 | `susan` 0회 | **MVPA 에선 정상** |
| drift 회귀자 | 있음 | | 표준 |

### 3.2 필드맵 — "적용해봤는데 실패했다"의 실체

기억이 흐릿했던 이유가 기록에 있다. **적용은 했으나 깨끗하게 시험된 적이 없다.**

| 트리 | deoblique | 필드맵 | 결과 |
|---|---|---|---|
| `fmriprep_out_deoblique` | header-only | 미적용 | sub-01 품질 문제 |
| `fmriprep_out_deoblique_v2` | header-only | **적용** | **sub-01 심각한 왜곡**, 일관성 부족 |
| `fmriprep_out_afni_deoblique` | AFNI 3dWarp | 적용 | v3 로 의도 |
| **정본 `method3_header_mi`** | 없음 | 미적용 | 채택 |

근본 원인은 필드맵이 아니라 **obliquity** 다 — 10명 전원 oblique 획득(25.8°–41.6°, 평균 29.5°), header-only deoblique 가 data–header mismatch 를 만들었고 fMRIPrep BBR 은 near-cardinal 을 가정해 실패했다 (`docs/PREPROCESSING_METHOD_UPDATE_2025-12-18.md`). 필드맵 적용 여부는 그 실패 **위에 얹힌** 변수였다.

→ **필드맵의 순효과는 한 번도 교란 없이 측정된 적이 없다.**

### 3.3 설계 — 정본 위에 한 단계씩, 보간은 1회 유지

fMRIPrep 실패의 원인(obliquity·BBR)을 건드리지 않는다. 정합은 현행 header-MI 그대로다.

| arm | 어떻게 | 보간 |
|---|---|---|
| 정본 | `applywarp(BOLD, premat=B→T1w, warp=T1w→MNI)` | 1회 |
| `+hmc` | MCFLIRT `-mats` 볼륨별 강체를 **premat 에 합성** | **1회** |
| `+sdc` | `fugue` → shiftmap → `convertwarp` 로 **warp 에 합성** | **1회** |
| `+hmc+sdc` | 둘 다 합성 | **1회** |

**이전 HMC arm 이 실패한 이유는 재정렬이 아니라 이중 보간이다** — `run_method3_hmc_all_subjects.sbatch:122` 가 MCFLIRT 로 한 번 굽고 `:145` 가 다시 구웠다 (split-half 신뢰도 HC $-0.048$ / CVD $-0.170$). 합성 방식은 그 문제를 만들지 않는다. fMRIPrep 이 HMC·SDC·정합·정규화를 하나로 합성해 보간 1회를 유지하는 것과 같은 설계다.

### 3.4 판정 — **시각화가 1차**, 수치는 보조

**결정적 실패 모드는 수치 지표로 잡히지 않는다.** 이 자료에서 실제로 문제가 되는 것은:

| 실패 모드 | 왜 수치로 못 잡나 |
|---|---|
| ROI 안에 **공백**(획득 슬랩 밖 / 신호 없는 복셀)이 들어감 | split-half·tSNR 은 남은 복셀로 계산되어 **높게 나올 수 있다** |
| 아틀라스가 **시각피질 외 영역**을 물음 | 봉쇄율·Dice 는 "뇌 안에 있는가" 만 보지 **"올바른 곳인가"** 를 안 본다 |
| 슬랩이 뇌 안 엉뚱한 위치에 안착 | 위와 동일 — 전뇌 중첩 지표는 위치 오류에 둔감 |

BBR 건에서 확인된 것과 같은 원리다 (§8.5) — Dice 0.50, 봉쇄율 0.97 이었지만 육안으로는 정합 실패였다. **따라서 이번에도 육안 확인이 판정의 1차 근거다.**

**1차 — 시각화 (arm × 피험자마다 생성)**

| 그림 | 무엇을 본다 |
|---|---|
| ROI 오버레이 (V1/V2/V3/hV4 × 축상·관상·시상) | 아틀라스가 **실제 후두 피질 위**에 놓이는가. 슬랩 밖으로 새는가 |
| BOLD 평균 + ROI 윤곽 | ROI 내부에 **공백·신호 없는 영역**이 있는가 |
| ROI 복셀별 tSNR 맵 | 저신호 구역이 ROI 어디에 몰려 있는가 |
| arm 간 차분 영상 (`+sdc` − 정본 등) | 왜곡 보정이 **어느 방향으로 얼마나** 밀었는가. R→L PE 이므로 x축 이동이 보여야 정상 |

**2차 — 수치 (시각 판정을 뒷받침하는 용도)**

| 지표 | 잡는 것 |
|---|---|
| ROI 내 **zero-variance / 결측 복셀 수** | 공백을 직접 센다. 위 실패 모드에 가장 민감한 수치 |
| ROI∩BOLD 커버리지 | 슬랩이 ROI 를 덮는 비율 |
| tSNR, DVARS | 전반 품질 |
| split-half 신뢰도 | **하한 확인용.** 이전 이중보간 arm 을 탈락시킨 기준이므로 승계하되, 이것만으로 통과 판정하지 않는다 |

**판정 규칙.** 시각 확인에서 공백 유입 또는 시각피질 외 영역 포함이 **정본보다 나빠지면** 그 단계는 이 자료에서 작동하지 않는 것으로 보고 미적용을 정당화한다. 나아지면 그대로 보고한다. **색 종점(hV4 게이트, 표적 ROI disparity)은 결과와 무관하게 전량 보고하되 판정에는 쓰지 않는다.**

### 3.4b 필드맵 사양 (BIDS 확인 완료, 2026-08-15)

경로: `/Users/jinilkim/LocalProj/colorBlind_data/bids/bids_editted`

| 항목 | 값 | 출처 |
|---|---|---|
| 필드맵 유형 | **GRE phasediff** — `magnitude1`, `magnitude2`, `phasediff` | `sub-*/fmap/` (sub-01·08·09 확인) |
| $\Delta$TE | $6.34 - 3.88 = $ **2.46 ms** | `phasediff.json` `EchoTime1/2` |
| `IntendedFor` | run-1~6 전부 연결됨 | 동일 |
| PE 방향 | **`i`** (x축) | `func/*_bold.json` |
| EffectiveEchoSpacing | **0.00039156 s** | 동일 |
| TotalReadoutTime | 0.0371982 s | 동일 |
| TR / TE | 1.5 s / 30 ms, 24 슬라이스, GRAPPA 2, multiband 없음 | 동일 |
| SliceTiming | 존재 (interleaved) | 동일 — STC 도 기술적으로 가능 |

**표준 `fugue` 경로가 그대로 성립한다.**

```
fsl_prepare_fieldmap SIEMENS phasediff magnitude1_brain fmap_rads 2.46
fugue --loadfmap=fmap_rads --dwell=0.00039156 --unwarpdir=x --saveshift=shift
convertwarp --ref=MNI --shiftmap=shift --shiftdir=x --premat=B→T1w --warp1=T1w→MNI --out=composed
applywarp --in=BOLD --warp=composed          # 보간 1회 유지
```

### 3.4c ⚠ PE 부호는 반드시 양방향으로 확인한다

`PhaseEncodingDirection` 이 **`i`** (부호 없음 = +x) 인데 Methods 는 **"PE R→L"** 로 적고 있다. `i` 는 영상 orientation 에 따라 L→R 일 수도 있으므로 **둘이 일치한다는 보장이 없다.**

**부호를 틀리면 왜곡을 반대로 밀어 두 배로 나빠진다.** SDC 는 부호가 맞아야만 이득이고, 틀리면 아무것도 안 한 것보다 나쁘다. 그리고 그 실패는 tSNR 로 잘 안 잡힌다 — 신호 강도는 비슷한데 위치만 더 틀어지기 때문이다. §3.4 의 논리가 여기에도 그대로 적용된다.

**조치**: `--unwarpdir=x` 와 `--unwarpdir=x-` 를 **둘 다 산출**하고 §3.4 의 시각 판정으로 고른다.

| 볼 것 | 옳은 부호 | 틀린 부호 |
|---|---|---|
| 후두 피질 윤곽 vs T1w | 해부 경계에 **가까워짐** | **더 멀어짐** |
| 차분 영상의 이동 방향 | 왜곡이 있던 쪽을 되돌림 | 같은 쪽으로 더 밈 |
| ROI 내 공백 | 줄거나 유지 | **늘어남** |

**부호 선택은 색 종점을 보지 않고 결정한다.** 해부 정렬만으로 판정하므로 selection 문제가 없다. 선택 근거(어느 부호를 왜 골랐는지)는 §S2 에 그림과 함께 남긴다.

두 부호 모두 정본보다 나쁘면 **SDC 미적용이 정당화된다** — 이 자료에서 GRE 필드맵이 24슬라이스 oblique 슬랩에 대해 신뢰할 만한 보정을 주지 못한다는 뜻이고, 그것이 §S2 에 쓸 문장이다.

### 3.4d 서버 파일럿 — 필드맵 실행 가능성 확인 (2026-08-15, sub-08)

작업 디렉터리 `node1:/storage/connectome/haba6030/pilot/sdc_check`. 도구 경로: FSL `/usr/local/fsl`, FreeSurfer `/usr/local/freesurfer/7.2.0` (로그인 셸 PATH 에 없으므로 스크립트에서 명시 export 필요). `tkregister2` 는 `SUBJECTS_DIR` 이 없으면 실패한다 — `fmriprep_work_method3_sub-XX/freesurfer_subjects` 를 지정한다.

#### 기하 — 필드맵과 BOLD 의 획득 방향이 크게 다르다

| | dim | voxel | 슬랩 |
|---|---|---|---|
| 필드맵 (`magnitude1`, `phasediff`) | 64×64×40 | 3×3×3.3 mm | **거의 축상** (obliquity ~7°) |
| BOLD | 96×96×24 | 2 mm iso | **크게 oblique** |

두 슬랩 법선 사이 각 **~69°**. 필드맵을 BOLD 공간으로 옮기는 재표본이 반드시 필요하다.

#### 커버리지 — **시각 ROI 는 100% 덮인다**

header(sqform) 정렬만으로 필드맵 뇌 마스크를 BOLD 공간에 넣고, 정본 변환으로 MNI 에 올려 ROI 와 교차한 결과 (sub-08):

| ROI | ROI 복셀 | BOLD 신호가 덮음 | **필드맵이 덮음** |
|---|---|---|---|
| V1 | 560 | 552 (98.6%) | **560 (100%)** |
| V2 | 400 | 373 (93.3%) | **400 (100%)** |
| V3 | 114 | 110 (96.5%) | **114 (100%)** |
| hV4 | 70 | 65 (92.9%) | **70 (100%)** |

BOLD FOV 전체로는 필드맵이 신호영역의 87.2% 만 덮지만(55,477 / 63,644), **부족분은 FOV 가장자리이고 시각 ROI 밖이다.**

**→ V1 위험(§3.7)이 크게 낮아진다.** 게다가 위 값은 **FLIRT 정합 없이 header 만으로** 나온 것이다. 필드맵과 BOLD 가 같은 세션의 스캐너 원본이고 deoblique 조작을 거치지 않았으므로 header 좌표가 서로 일치한다 — 과거 data–header mismatch 문제는 header-only deoblique 단계가 만든 것이었고 (§3.2), 이 경로는 그 단계를 타지 않는다.

**남은 검증**: `convertwarp --shiftmap` 적용 순서(V2)와 PE 부호(V3)는 여전히 미확인이며, 실제 unwarp 산출 후 §3.4 의 시각 판정으로 확인한다.

### 3.4e 결과 — SDC 미적용은 **측정으로 정당화된다** (2026-08-15)

파일럿을 sub-01(HC) · sub-08(deutan) · sub-09(protan) 로 확장했다. 산출: `node1:/storage/connectome/haba6030/pilot/sdc_check/{,sub-01,sub-09}`, 그림 `analysis/phase0_preprocessing/figures/sdc_pilot_sub-08/`.

#### (1) 필드맵–BOLD header 정렬은 정확하다

`figures/sdc_cohort/FMAPALIGN_sub-{01..09}.png` — **9명 전원**에서 필드맵 자기공명 강도 영상의 뇌 윤곽이 BOLD 뇌 경계를 그대로 따라간다. **FLIRT 정합 없이 header(sqform) 만으로 맞는다.** 두 영상이 같은 세션의 스캐너 원본이고 deoblique 조작을 거치지 않았기 때문이다 (§3.4d).

**정렬 불량 피험자는 없다.** SD 가 큰 sub-07 과 평균이 0 에 가까운 sub-04 도 정렬 자체는 정상이다 → 두 이상치의 원인은 정렬이 아니다 (sub-07 은 §(2b) 의 슬랩 커버리지). **→ V1 위험 해소.**

#### (2) 왜곡 이동량 — 분석 ROI 안에서 서브복셀, 그리고 거의 균일

`fugue --dwell=0.00039156 --unwarpdir=x` 의 shift 를 MNI 로 올려 ROI 별 집계 (단위 = 복셀, 1복셀 = 2 mm):

**전 피험자 산출 (sub-01~09, sub-10 제외).** `analysis/phase0_preprocessing/results/roi_shift_summary.csv` · 스크립트 `pilot/run_sdc_cohort.sh` 36 셀 (9명 × 4 ROI), 각 셀에 `mean, SD, P5, P25, P50, P75, P95, min, max` 전량 기록.

| ROI | mean 범위 | **SD 범위** | **95% range (P95−P5)** | IQR 범위 |
|---|---|---|---|---|
| V1 | $-0.64$ ~ $+0.03$ | $0.07$–$0.33$ | $0.22$–$0.93$ | $0.07$–$0.29$ |
| V2 | $-0.56$ ~ $-0.10$ | $0.09$–$0.38$ | $0.29$–$1.19$ | $0.07$–$0.43$ |
| V3 | $-0.75$ ~ $-0.17$ | $0.06$–$0.33$ | $0.21$–$1.02$ | $0.06$–$0.56$ |
| hV4 | $-0.76$ ~ $+0.41$ | $0.05$–$0.37$ | $0.15$–$1.19$ | $0.05$–$0.61$ |

전체 36셀: $|{\rm mean}|$ **0.01–0.76** · SD **0.05–0.38** · 95% range **0.15–1.19** · IQR 0.05–0.61

**⚠ 3명 표본에서 냈던 "SD 0.06–0.16" 은 폐기한다.** 전 코호트에서는 0.05–0.38 이다. 검토자가 전 피험자 산출을 요구한 이유가 이것이다.

**두 성분을 분리해서 읽어야 한다.**

| 성분 | 크기 | 패턴 기하에 미치는 영향 |
|---|---|---|
| **균일 성분** (ROI 평균) | 0.29–0.76 복셀 = **0.6–1.5 mm** | 거의 강체 평행이동이므로 **미분 성분보다 덜 우려스럽다.** 8색 전 조건에 같은 방향으로 걸리고, BOLD→T1w 정합이 왜곡된 데이터에 적합되었으므로 일부 흡수된다. **완전 상쇄를 단정하지는 않는다** |
| **미분 성분** (ROI 내 SD) | **0.05–0.38 복셀 = 0.10–0.76 mm** | **직접적인 pattern-distortion term.** 복셀 크기의 약 1/20–1/3 |

전뇌로는 shift 가 최대 9–10 복셀(약 20 mm)까지 가지만, 그 극단은 부비동·이도 인접부이고 **후두엽 ROI 는 자화율 경계에서 멀어** 크기가 작다. 물리적으로 예상되는 결과다.

**sub-07 이 유일한 이상치다.**

| | n_vox | mean | SD | 95% range | max−min |
|---|---|---|---|---|---|
| V1 | 330 | $-0.38$ | 0.33 | 0.93 | 2.75 |
| V2 | 258 | $-0.39$ | 0.38 | **1.19** | **3.27** |
| V3 | 59 | $-0.17$ | 0.33 | 1.02 | 1.36 |
| hV4 | **16** | $+0.41$ | 0.37 | 1.19 | 1.19 |

**sub-07 을 빼면 SD 0.05–0.21, 95% range 0.15–0.72** 로 전부 서브복셀이다. sub-07 의 hV4 는 복셀 16개짜리 축퇴 ROI 로, 이미 다른 맥락에서도 제외 사유가 문서화되어 있다 (상관 계산에서 nan). obliquity 36.7°(Severe 3명 중 하나)인 점도 같이 적어 둘 만하다.

#### (2b) sub-07 이상치의 원인 — **왜곡이 아니라 슬랩 커버리지 실패**

sub-07 의 큰 SD 는 자화율 왜곡이 심해서가 아니다. **BOLD 슬랩이 시각 영역을 덮지 못했다.**

**ROI 복셀 수 (func 마스크 적용 / 아틀라스 원본)**

| | V1 | hV4 |
|---|---|---|
| sub-03·04·05·06 | 858/858 (100%) | 70/70 (100%) |
| sub-09 | 692/858 (81%) | 70/70 (100%) |
| sub-01 | 568/858 (66%) | 67/70 (96%) |
| sub-08 | 560/858 (65%) | 70/70 (100%) |
| sub-02 | 405/858 (47%) | 69/70 (99%) |
| **sub-07** | **330/858 (38%)** | **16/70 (23%)** |

**sub-07 만 hV4 가 무너진다.** 다른 8명은 96–100% 인데 sub-07 은 23% 다. 시상면 그림(`figures/coverage_diag/SAG_sub-{03,07,08}_MNIbg_BOLDslab.png`)에서 슬랩이 sub-03·08 보다 **더 가파르게 기울고 전방으로 치우쳐** 복측 후두엽을 잘라낸 것이 보인다. obliquity 36.68°(Severe 3명 중 하나)와 일관된다.

**따라서 인과가 반대다.** 왜곡이 커서 SD 가 큰 것이 아니라, **살아남은 소수 복셀이 슬랩 가장자리에 몰려 있어** 그 위치에서 필드맵 유도 shift 의 변이가 큰 것이다. 획득 단계 문제이지 전처리 문제가 아니다.

**이미 알려진 사실과 일치한다.** `phase5_filter_optimization/CLAUDE.md §A6` 이 `hV4 effective n=6 (sub-07 16 voxels → nan)` 으로 기록하고 있다. 이번 산출은 **그 원인을 슬랩 처방으로 국소화**한 것이다.

**→ §S2 에서 sub-07 을 이상치로 병기할 때 이 사유를 함께 적는다.** "한 참가자에서 컸다" 로만 적으면 왜곡이 심한 것으로 오독된다.

#### (3) §S2 문안 — **"cannot" 을 쓰지 않는다** (2026-08-15 검토 반영)

**철회한 초안**:

> ~~이 규모에서는 왜곡 보정 미적용이 색 조건 간 표상 기하를 **만들거나 없앨 수 없다**.~~

**왜 못 쓰는가.** 우리가 한 것은 **필드맵에서 유도한 변위 크기 측정**이지, **SDC 를 실제 적용한 BOLD 에서 LOCO/RDM 을 재계산한 것이 아니다.** 측정이 직접 입증하는 것은 "왜곡이 후두 시각 ROI 에서 작고 ROI 내 공간 변이가 서브복셀"까지다. 거기서 "주 표상 소견이 자화율 왜곡으로 생성되었을 **가능성이 낮다**" 를 **추론**할 수 있을 뿐이며, hV4 처럼 작은 ROI 에서 **완전 무영향을 수학적으로 보장할 수는 없다.**

**채택 문안** — 숫자를 그대로 쓰고 추론 강도를 낮춘다:

> Field-map-derived susceptibility displacement was measured within each analyzed ROI in all nine participants. Mean displacement ranged from 0.01 to 0.76 voxels (0.02--1.52 mm). Within-ROI spatial variation, the component that distorts a pattern rather than translating it, was 0.05--0.21 voxels (0.10--0.42 mm) in eight participants, with a 5th--95th percentile range of 0.15--0.72 voxels; in the remaining participant it reached 0.38 voxels (0.76 mm) with a 5th--95th percentile range of 1.19 voxels. Susceptibility distortion within these posterior visual ROIs was therefore predominantly subvoxel and spatially smooth, making it unlikely to account for the observed differences in representational geometry across color conditions.

**어휘 규칙**

| 금지 | 허용 |
|---|---|
| `cannot alter relative geometry` | `is less likely to distort within-ROI representational geometry than spatially varying displacement` |
| `no effect` / `무시 가능` | `predominantly subvoxel and spatially smooth` |
| 균일 성분을 "상쇄된다" 로 단정 | 균일 성분은 **덜 우려스럽고**, **미분 성분이 직접적인 pattern-distortion term** 이라고 기술 |

**"적용하지 않았다"가 "크기를 재어 보고했다"로 바뀐다.** 이것이 이 작업의 목표이며, **`+sdc` arm 으로 종점을 재계산하지 않고도 달성된다** — 단 그 한계를 위와 같이 명시할 때만.

#### (4) 부수적으로 해소된 것

- **PE 부호(V3)**: ROI 내 이동이 거의 균일하고 서브복셀이므로, 부호를 어느 쪽으로 잡든 ROI 기하에 미치는 영향이 같은 규모다. 정당화 목적에는 부호 확정이 불필요하다. (`unwarp_x` − `unwarp_xm` 은 전뇌에서 SD 93 으로 다르지만, 그 차이는 ROI 밖에 있다.)
- **전역 정량 지표는 역시 무력했다** — T1w 와의 상관이 원본 0.43 / `x` 0.43 / `x-` 0.42 로 구분되지 않았고, 몽타주 육안으로도 세 영상이 구분되지 않았다. §3.4 의 전제가 재확인된다: **판정은 ROI 안에서 봐야 한다.**

#### (5) 남는 것

`+hmc` 는 별개다. 위 측정은 **자화율 왜곡**의 크기만 다룬다. 머리 움직임은 시점마다 달라 "전 조건 동일" 논증이 성립하지 않으므로, `+hmc` 는 여전히 실제로 돌려 확인해야 한다.

### 3.4f `+hmc` 파일럿 — 움직임 규모 (sub-08 run-1)

`fmriprep_out_method3_header_mi/sub-08/func/sub-08_task-rsvp_run-1_desc-motion.par` (288 볼륨)

| | 값 |
|---|---|
| 평행이동 범위 (x,y,z) | 0.42 / **1.12** / 0.64 mm |
| 회전 범위 | 0.66 / 0.27 / 0.60° |
| **기준 볼륨 대비 최대 평행이동** | **0.74 mm = 0.37 복셀** |
| FD 평균 / 중앙값 / 최대 | 0.321 / 0.249 / 1.726 mm |
| FD > 0.5 비율 | 18.8% |

**FD 와 "기준 대비 변위"를 구분해야 한다.** FD 는 프레임 간 변화량(추정 잡음 포함)이고, **재정렬이 실제로 되돌리는 것은 기준 볼륨 대비 변위**다. 후자는 최대 0.74 mm(0.37 복셀)로 §3.4e 의 자화율 미분 성분과 같은 규모다. 회전 0.66° 도 반경 60 mm 에서 0.69 mm 로 유사하다.

**다만 SDC 와 논증 구조가 다르다.** 자화율 왜곡은 전 조건에 동일하게 걸려 상대 기하를 못 바꾸지만, 움직임은 시점마다 달라 그 논증이 성립하지 않는다. 조건과 상관되지 않으면 잡음처럼 작용해 민감도를 깎을 뿐이지만, 그 전제 자체를 확인해야 한다. → 실제 `+hmc` arm 산출 필요.

### 3.4g `exp1 · hmc` 전 피험자 결과 (2026-08-15) — **품질 개선 없음**

산출: `fmriprep_out_method3_hmc_v2/` (9명 × 6런 = **54/54**), 보간 1회 합성. 집계 `analysis/phase0_preprocessing/results/hmc_summary.csv` (216행), 그림 `figures/hmc_full/` (27장).

> **⚠ 실행 함정 — 첫 시도의 절반이 조용히 실패했다.** 배열 54개가 전부 exit 0 인데 산출물은 30개였다. 원인: **노드마다 FSL 위치·버전이 다르다.** node1·node2 = `/usr/local/fsl` **6.0.5.1**(정본과 동일) + FreeSurfer 7.2.0; **node4 = `/usr/share/fsl/5.0`, FreeSurfer 없음.** node4 태스크는 명령을 못 찾고도 정상 종료했다. `--nodelist=node2` 로 고정해 재실행. **FSL 배열은 반드시 노드를 고정한다** — 안 하면 버전이 섞인 arm 이 만들어질 수 있고, 그 오염은 검출하기 어렵다.

#### (1) 아틀라스 ROI 겹침 — 주 기준

| ROI | 평균 Δ (복셀) | 아틀라스 대비 | 개선된 런 |
|---|---|---|---|
| V1 | $+4.48$ | $+0.52\%$ | 29/54 |
| V2 | $+2.35$ | $+0.42\%$ | 25/54 |
| V3 | $+0.31$ | $+0.27\%$ | 10/54 |
| **hV4** | $+0.15$ | $+0.21\%$ | **6/54** |

전체 합계 11,265 → 11,331 (**+0.6%**). 증가분은 커버리지가 부분적인 피험자 (sub-01·02·08·09)의 V1·V2 에 몰려 있고, 이미 100% 인 sub-03~06 은 변화 0 이다. **hV4 는 54런 중 6런에서만 바뀌었고 최대 +2 복셀이다.**

**⚠ 이 지표의 한계**: 뇌 마스크를 영상별 `mean > P40` 으로 정의했으므로, HMC 가 평균 영상을 바꾸면 임계값도 함께 움직인다. 0.2–0.5% 규모의 이득은 그 정의 변화로도 생길 수 있다. **이 크기를 실질적 개선으로 해석하지 않는다.**

#### (2) tSNR — 일관되게 나빠진다

| ROI | 평균 | 중앙값 | 개선된 런 |
|---|---|---|---|
| V1 | $-2.96\%$ | $-2.24\%$ | 15/54 |
| V2 | $-2.20\%$ | $-2.03\%$ | 13/54 |
| V3 | $-1.86\%$ | $-1.61\%$ | 14/54 |
| hV4 | $-2.05\%$ | $-2.28\%$ | 17/53 |

**기전이 설명된다.** 정본은 **모든 볼륨에 동일한 변환**을 쓰므로 보간 오차가 시간에 대해 일정해 tSNR 에서 상쇄된다. HMC 는 볼륨마다 변환이 달라 그 오차가 **시변 잡음**이 된다. 기준 볼륨 대비 변위가 최대 0.37 복셀뿐이라(§3.4f) 얻는 것보다 잃는 것이 조금 더 크다.

#### (3) sub-07 은 HMC 로 고쳐지지 않는다

hV4 겹침이 13.2/70 로 그대로다. **한 런에서는 hV4 tSNR 이 0** 이다(216셀 중 유일). §(2b) 의 진단대로 획득 단계 문제이며 전처리로 회복되지 않는다.

#### (4) 판정

**정본 유지.** 올바른 구현으로 재정렬을 적용해도 분석 ROI 에서 겹침은 0.5% 미만 변하고 tSNR 은 약 2% 낮아진다. §S2 서술이 **"적용하지 않았다"에서 "적용해 평가했고 이 자료에서는 개선되지 않았다"** 로 바뀐다.

#### (5) 남은 것 — 아직 하지 않은 것을 분명히 한다

위는 **품질 지표** 평가다. **색 종점(LOCO 게이트·disparity)을 HMC arm 에서 재계산하지 않았다.** 따라서 지금 말할 수 있는 것은 "재정렬이 데이터 품질을 개선하지 않는다" 까지이고, **"결과가 유지된다"는 아직 검증되지 않았다.** arm 이 전량 존재하므로 (`full_dataset_C010` 레시피의 `FMRIPREP_DIR` 만 교체) 원하면 바로 돌릴 수 있다.

### 3.4h `exp1 · hmc · endpoint` — 색 종점 재산출 결과 (2026-08-15)

진폭 `derivatives/full_dataset_C010_hmc_v2` (36/36, 실패 0). 동결 파이프라인을 import 만 하는 `run_c010_hmc.py` 래퍼로 경로 상수 2개만 교체 — GLM·drift·Procrustes 바이트 동일, **ROI 마스크도 `method3_header_mi` 그대로**라 두 arm 이 같은 복셀 집합을 쓴다.

**재현 게이트 통과.** 정본 arm 재실행이 발표값과 정확히 일치했다 (hV4 $p_{\rm perm}$ = .0110, deutan 0.250 / $p$ = .054, protan 0.125 / $p$ = .011). `verify: EXACT MATCH` (loco_canonical 과 1e-12).

#### LOCO adjacent accuracy — 기여 1 의 게이트

| ROI | 정본 HC | $p_{\rm perm}$ | **hmc HC** | $p_{\rm perm}$ |
|---|---|---|---|---|
| V1 | 0.393 | .164 | 0.283 | .922 |
| V2 | 0.357 | .424 | 0.381 | .228 |
| V3 | 0.339 | .586 | 0.316 | .810 |
| **hV4** | **0.456** | **.011** | **0.451** | **.023** |

**게이트는 살아남는다.** hV4 가 자기 색 라벨 순열 귀무를 넘는 유일한 ROI 라는 구조가 두 arm 에서 동일하다. HC 평균도 사실상 불변(0.456 → 0.451).

#### 단일사례 CVD 대비 — **살아남지 못한다**

| | 정본 | | **hmc** | |
|---|---|---|---|---|
| | acc | $p$ | acc | $p$ |
| deutan hV4 | 0.250 | .054 | **0.354** | **.242** |
| protan hV4 | 0.125 | **.011** | **0.271** | **.108** |

**`motreg` 때와 성격이 다르다.** 거기서는 HC 산포 팽창이 원인이었고 CVD 점추정은 거의 그대로였다. 여기서는 **CVD 값 자체가 크게 올라간다** — protan 0.125 → 0.271 (2배 이상), deutan 0.250 → 0.354. HC 는 불변(0.456 → 0.451)이고 SD 만 0.102 → 0.122 로 소폭 는다.

**기전이 정합적이다.** CVD 참가자의 FD 가 HC 보다 높고(0.338 vs 0.313), 재정렬은 움직인 사람에게 더 많이 작용한다. 즉 **측정된 CVD 보간 결손의 일부가 머리 움직임에 귀속된다.** FD 공변량 보정이 sub-08 V2 disparity 를 .040 → .137 로 떨어뜨린 것과 같은 방향이다.

#### 이것이 뜻하는 것

| 진술 | 상태 |
|---|---|
| hV4 가 보간을 지지하는 유일한 ROI (HC, 자기 순열 대비) | **유지** (3 arm + hmc, 4개 전처리에서) |
| 두 CVD 참가자가 hV4 에서 HC 분포 아래 (단일사례 유의) | **유지되지 않음** — 재정렬 후 $p$ = .242 / .108 |

**정본 유지 결정과 별개로, 이 결과는 보고해야 한다.** §3.4g 의 품질 지표는 재정렬이 데이터를 개선하지 않는다고 말하지만, **종점은 개선 여부와 무관하게 달라진다.** "품질이 안 좋아졌으니 무시한다" 는 논거로 쓸 수 없다 — 품질 판정과 종점 민감도는 별개 사안이다.

#### disparity — 미해결

`disparity_frozen_permutation.py` 를 두 arm 에 돌렸으나 (`analysis/validation/results/disparity_frozen_permutation_hmc_v2.json`), **이 스크립트의 출력이 논문 발표값(sub-09 V1 $p$=.007, sub-08 V2 $p$=.040)을 재현하지 않는다** (정본 arm 에서 각각 .038 / .644). 논문 추정량은 `rerun_loo_consistent.py` 계열이므로 **그 스크립트로 재현 게이트를 먼저 통과시킨 뒤에야 arm 간 비교가 의미를 갖는다.** 현재 산출된 숫자는 해석하지 않는다.

### 3.4i LOCO 지표 자체의 전처리 민감도 (2026-08-15)

`exp1 · hmc` 결과를 해석하려면 **지표가 전처리에 얼마나 민감한지** 를 먼저 알아야 한다. 세 분석을 했다. 코드 `analysis/future_phase1_sensitivity/scripts/{_boot_runs_arm,_arm_agreement,_perm_mae_arm}.py`, 산출 `boot_runs_*.json` · `arm_agreement.json` · `perm_mae_arm.json` · 그림 `fig_delta_loco_vs_motion.png`.

#### (1) arm 간 일치도 — ICC 가 게이트와 같은 순서를 낸다

두 arm 을 두 평정자로 보고 참가자 9명의 adjacent accuracy 일치도:

| ROI | Pearson $r$ | Spearman $\rho$ | **ICC(2,1)** | 색 라벨 순열 게이트 |
|---|---|---|---|---|
| V1 | $-0.006$ | $+0.267$ | $\mathbf{-0.005}$ | 통과 못함 |
| V2 | $+0.465$ | $+0.300$ | $+0.471$ | 통과 못함 |
| V3 | $+0.641$ | $+0.700$ | $+0.662$ | 통과 못함 |
| **hV4** | $\mathbf{+0.837}$ | $\mathbf{+0.817}$ | $\mathbf{+0.825}$ | **통과** |

**게이트를 통과하는 유일한 ROI 가 전처리 재현성도 유일하게 높다.** 두 독립적 기준이 같은 결론을 준다. V1 의 ICC $\approx 0$ 은 "V1 LOCO 는 잡음" 을 순열검정과 무관하게 확인한다.

**§S2 에 쓸 자산이다** — "hV4 에서 LOCO 는 전처리 arm 간 ICC = 0.83 으로 재현된다" 는 지표 신뢰도 진술이며, 종점 결과와 독립이다.

#### (2) Bland–Altman — deutan 은 HC 일치도 범위 안, protan 만 밖

$x = (\text{primary}+\text{hmc})/2$, $y = \text{hmc}-\text{primary}$. 기저값에 변화량을 회귀하면 평균회귀로 편향되므로 이 형태를 쓴다.

| ROI | HC bias | HC SD | LoA | deutan | protan |
|---|---|---|---|---|---|
| hV4 | $-0.005$ | 0.068 | $[-0.137, +0.128]$ | $+0.104$ ($z=+1.61$) **안** | $+0.146$ ($z=+2.22$) **밖** |
| V1 | $-0.110$ | 0.057 | $[-0.222, +0.002]$ | $-0.188$ ($z=-1.35$) 안 | $+0.250$ ($z=+6.28$) 밖 |

**HC 는 hV4 에서 계통적으로 움직이지 않았다** (bias $-0.005$). 즉 CVD 의 이동을 "모두가 움직였다" 로 설명할 수 없다. 다만 **deutan 은 HC 일치도 범위 안에 있다** — 이례적인 것은 protan 하나다.

**움직임으로 설명되지 않는다.** sub-09(protan)의 기준 대비 최대 변위는 0.729 mm 로 9명 중 7번째(작은 쪽)인데 $\Delta$ 는 최대다. sub-08 은 변위 1.699 mm 로 1위여서 그쪽만 정합적이다. $\Delta \sim$ 기저값 상관이 $-0.57$(hV4) / $-0.64$(V1) 로 움직임 상관보다 일관되게 강하다 — **평균회귀** 양상.

#### (3) 색별 분해 — 소수 색의 경계 통과다

**protan hV4 (0.125 → 0.271)**

| hue | primary | hmc | $\Delta$ |
|---|---|---|---|
| red | 0.000 | 0.667 | $+0.667$ |
| orange | 0.500 | 0.000 | $-0.500$ |
| green | 0.000 | 1.000 | $+1.000$ |
| 나머지 5색 | | | $0.000$ |

**8색 전반의 개선이 아니라 3색만 변했고 그중 둘은 0↔1 극단 이동이다.** adjacent accuracy 는 45° 임계의 이분법이라 예측이 한 칸 이동하면 색당 1/8 씩 점프한다. deutan 은 5/8 색이 변했다(red $-0.667$, green $+0.833$).

#### (4) 연속 각오차의 순열 귀무 — **"chance level" 을 쓰려면 필요했다**

MAE(평균 절대 원형 오차)는 adjacent accuracy 와 **다른 통계량**이므로 자체 귀무가 필요하다. 동일한 per-subject 색 라벨 순열(N = 1000, seed 42)로 구성했다.

**hV4**

| | primary | hmc |
|---|---|---|
| HC 관측 | $69.0 \pm 9.2°$ | $64.4 \pm 14.2°$ |
| deutan | $82.8°$ (null 76.3, $z=+0.42$, $p=.688$) | $78.6°$ (null 78.0, $z=+0.03$, $p=.500$) |
| protan | $99.1°$ (null 79.2, $z=+1.24$, $p=.873$) | $66.2°$ (null 76.3, $z=-0.62$, $p=.298$) |
| **protan C–H vs HC** | $\mathbf{p = .0111}$ | $\mathbf{p = .4537}$ |
| deutan C–H vs HC | $p = .1036$ | $p = .1931$ |

**판정 — 검토자가 제시한 시나리오 중 A 는 기각된다.** 연속 오차도 $99.1° \to 66.2°$ 로 33° 움직였다. 경계 통과만의 문제였다면 연속 지표는 거의 불변이어야 했다. **이산화 인공물로 설명할 수 없다.**

**그러나 진술을 둘로 나누면 하나는 살아남는다.**

| 진술 | arm 강건성 |
|---|---|
| protan 은 hV4 에서 **above-null 보간을 보이지 않는다** | **강건** ($p$ = .873 / .298, 둘 다 비유의) |
| protan 은 hV4 에서 **HC 보다 유의하게 나쁘다** | **강건하지 않음** ($p$ = .011 → .454) |

**부수 소견**: HC 개인 중 자기 귀무를 유의하게 넘는 사람이 거의 없다(최선 $p$ = .018–.026). hV4 게이트는 **집단 수준** 결과이며 개인 수준 보간의 증거가 아니다 — 원고 서술과 일치한다.

### 3.5 보고 뉘앙스 — 이 작업의 실제 산출

**Methods 본문은 건드리지 않는다.** 사실 진술이고 정확하다.

바뀌는 것은 §S2 다. 현행은 단계 목록을 **하지 않았다**로 나열해, 시도조차 안 한 것처럼 읽힌다.

| 현행 | 교체 방향 |
|---|---|
| `No slice-timing correction, motion realignment, susceptibility distortion correction, or spatial smoothing was applied.` | 사실 진술은 유지하고, **§S2 에 민감도 문단을 신설**해 각 단계를 실제로 적용한 arm 의 품질 지표와 종점을 보고 |

§S2 신설 문단의 형태 (수치는 산출 후 확정):

> The functional data were additionally reconstructed with head-motion realignment and with susceptibility distortion correction, each folded into the same single-interpolation transform chain used by the primary pipeline, and the neural endpoints were recomputed on both. [품질 지표]. [종점 결과]. The primary pipeline is reported throughout, with these arms tabulated here.

이러면 §S2 가 **"안 했다"에서 "적용해보고 그 결과를 보고한다"**로 바뀐다. 그리고 이것이 이 작업의 유일한 목표다 — 정본은 그대로다.

---
### 3.7 실행 방식 — 코드 점검 결과 (2026-08-15)

#### 재실행하지 않아도 되는 것 — **정합은 그대로 쓴다**

`run_method3_header_mi_all_subjects.sbatch:136,256,327,346` 이 변환을 **영구 보존**한다:

```
${OUTPUT_DIR}/sub-XX/transforms/
   sub-XX_run-N_bold_to_t1w.lta        # 런별 BOLD→T1w (FreeSurfer LTA)
   sub-XX_t1w_to_mni_affine.mat
   sub-XX_t1w_to_mni_warp.nii.gz
```

→ **`bet2` / `mri_coreg` / FLIRT / FNIRT 전부 재실행 불필요.** Step 4(적용)만 다시 돌린다. 민감도 arm 이 시간·위험 양쪽에서 싸진다. 정합이 정본과 **비트 단위로 동일**하므로, arm 간 차이가 정합 변동에서 올 가능성도 원천 차단된다.

#### 재구성해야 하는 것 — WORK_DIR 은 휘발성

`WORK_DIR=/storage/.../fmriprep_work_method3_sub-XX` 에 있던 것들은 남아 있지 않을 수 있다. 전부 결정론적으로 복원 가능하다.

| 파일 | 복원 | 비고 |
|---|---|---|
| `boldref.nii.gz` | `fslroi BOLD ref $((NVOLS/2)) 1` | 정본과 동일 규칙 (L410-417) |
| `T1w_brain.nii.gz` | `bet2 T1w -f 0.5` | tkregister2 `--targ` 의 **기하 참조용**. 마스크 내용이 아니라 dims/affine 만 쓰이므로 재실행해도 동일 결과 |
| `bold_to_t1w.mat` (FSL) | `tkregister2 --lta ... --fslregout` (L432-438) | 보존된 `.lta` 에서 재생성 |

#### arm 별 추가 단계

**`+hmc`** — `-mats` 가 **필요한데 지금 없다.** `add_motion_correction.sbatch:119-126` 은 `-mats` 를 주석에만 적고 실제로는 `-plots` 만 전달했다. 정렬본도 삭제했다(`:152` "Cleanup motion-corrected BOLD"). 남은 건 `.par` 뿐이다. → `mcflirt` 를 **`-mats` 로 재실행**한다. 빠르고 결정론적이다.

**참조 볼륨이 일치한다는 점이 중요하다.** 정본 Step 4 의 `REF_VOL=$((NVOLS/2))` (L417) 와 `add_motion_correction.sbatch:112` 의 `REF_VOL` 이 같은 볼륨이다. 따라서 보존된 `.lta` 는 MCFLIRT 정렬 후에도 그대로 유효하다 — 재정합이 필요 없는 근거가 여기 있다.

```
mcflirt -in BOLD -refvol $((NVOLS/2)) -mats -plots -out mc     # MAT_0000..MAT_0287
for v in $(seq 0 287); do
  convert_xfm -omat M_$v -concat BOLD_TO_T1W.mat mc.mat/MAT_$(printf %04d $v)
  fslroi BOLD vol_$v $v 1
  applywarp --in=vol_$v --ref=MNI --premat=M_$v --warp=T1W_TO_MNI_WARP --out=out_$v
done
fslmerge -t BOLD_MNI out_*                                      # 보간 1회
```

**`+sdc`**

```
bet2 magnitude1 mag_brain -f 0.5
fsl_prepare_fieldmap SIEMENS phasediff mag_brain fmap_rads 2.46
flirt -in mag_brain -ref boldref -omat fmap2bold.mat            # ← 새 정합 단계 (§주의)
flirt -in fmap_rads -ref boldref -applyxfm -init fmap2bold.mat -out fmap_in_bold
fugue --loadfmap=fmap_in_bold --dwell=0.00039156 --unwarpdir=x --saveshift=shift_x
convertwarp --ref=MNI --shiftmap=shift_x --shiftdir=x \
            --premat=BOLD_TO_T1W.mat --warp1=T1W_TO_MNI_WARP --out=composed_x
applywarp --in=BOLD --ref=MNI --warp=composed_x                  # 보간 1회
```

#### ⚠ 실행 전 검증 3건

| # | 항목 | 왜 |
|---|---|---|
| V1 | **필드맵→BOLD 정합이 새로 필요하다** | shiftmap 은 필드맵 공간에서 나오므로 BOLD 공간으로 옮겨야 한다. **이 자료는 정합 자체가 취약한데 단계를 하나 더 넣는 것**이다. §3.4 시각 확인의 최우선 대상 |
| V2 | `convertwarp --shiftmap` **적용 순서** | 입력(BOLD) 공간에서 `--premat` 보다 **먼저** 적용되어야 맞다. FSL 문서·소액 테스트로 확인한 뒤 본 실행 |
| V3 | **PE 부호** `x` vs `x-` | §3.4c. 둘 다 산출 후 시각 판정 |

#### 비용

| arm | 규모 | 비고 |
|---|---|---|
| `+sdc` | 런당 `applywarp` 1회 | 정본과 동일. 저렴 |
| `+hmc` | 288 vol × 6 run × 9 명 = **15,552 `applywarp`** | 볼륨당 ~1s → 피험자당 ~30분. SLURM array 로 병렬 |

`applyxfm4D` 는 아핀만 지원해 비선형 warp 를 못 태우므로, 볼륨 루프가 **보간 1회를 지키는 유일한 경로**다. 두 단계로 나누면 보간이 2회가 되어 이전 arm 의 실패를 반복한다.

## 4. 작업 4 — `anat_harmonized` (세션 간 대칭화)

### 4.1 비대칭의 실체 (코드 대조 완료)

| | `exp1` | `exp2` |
|---|---|---|
| 드라이버 | `run_method3_header_mi_all_subjects.sbatch` | `run_method3_header_mi_2nd.sbatch` |
| BIDS 변환 | ezBIDS (**디페이싱됨**) | dcm2bids 3.2.0 (**디페이싱 안 됨**) |
| 해부 기준 | `exp1` T1w | **`exp2` 자체 T1w** (L156) |
| BOLD→T1w | `mri_coreg --regheader` | 동일 |
| T1w→MNI | FLIRT 12-DOF → FNIRT | 동일 |
| 표준 공간 | `MNI152NLin2009cAsym_res-2` | 동일 |

**비대칭은 두 겹이다** — 디페이싱, 그리고 **서로 다른 해부 영상**. 원고는 이미 이 사실을 공개하고 있다 (`methods_v2.tex:76`).

**정량 확인 (2026-08-16)** — sub-08 T1w, 동일 shape (224, 512, 512), 동일 RAS.

| | ses-1 `bids/bids_editted` | ses-2 `bids_2nd` |
|---|---|---|
| 0 복셀 비율 | **30.9%** | 13.1% |
| 파일 크기 | 40.4 MB | 44.8 MB |

**디페이싱이 파이프라인에 들어가는 지점 — 두 곳** (`run_method3_header_mi_all_subjects.sbatch`)

| 줄 | 호출 | 얼굴 노출 |
|---|---|---|
| `:192` | `bet2 ${T1W_FILE} -f 0.5 -m` | **원본 T1w 위에서 뇌 추출** → CoG 추정·마스크가 얼굴 유무에 영향받음 |
| `:331` | `flirt -in <T1w_brain> -ref <MNI brain>` | 뇌 추출본 사용 → 마스크가 같다면 불변 |
| `:371` | `fnirt --in=${T1W_HEAD_NII}` (`orig.mgz`) | **전체 머리가 moving image** |

즉 `bet2` 마스크와 FNIRT 입력이 두 세션에서 서로 다른 조건으로 계산되었다. **검토자 지적이 코드 수준에서 확인된다.** `--refmask` 는 reference 쪽만 제한하므로 moving 쪽 얼굴 유무를 상쇄하지 못한다.

**저비용 부수 검사 (선택)** — ses-1 비디페이싱 원본이 DICOM 에서 복원 가능하다 (`colorBlind_data/data/CVD-01/T1_MPRAGE_SAG_p2_22_MR`). 한 명분을 `dcm2niix` 후 디페이싱본/원본 두 벌로 동일 `bet2 → flirt → fnirt` 를 통과시켜 **ROI 중심 변위를 복셀 단위로 측정**하면 §S2 에 SDC 와 같은 형식의 숫자가 하나 더 생긴다 (0.5 복셀 미만 → 무시 가능이 근거와 함께 서술됨 / 이상 → 재전처리 필요성이 입증됨).

### 4.2 방식 — ezBIDS 양쪽 통일 (사용자 결정 2026-08-15)

`exp1` 이 ezBIDS(디페이싱 포함)로 확정되었으므로, `exp2` 도 ezBIDS 를 통과시킨다. **도구 불일치 문제가 아예 없어진다** (`mri_deface` vs `pydeface` 대조 불필요).

| | 산다 | 못 산다 |
|---|---|---|
| | 9.4 mm 지배항 제거. Methods 한 문장으로 종결 | **절차 대칭이지 공간 대응이 아니다** — `exp2` 도 자기 변위가 생기고 방향이 `exp1` 과 같다는 보장이 없다. 각자의 T1w·각자의 T1w→MNI 는 그대로 |

잔차는 독립 정규화 2회의 불일치(통상 1–2 mm)로 **이미 있는 런간 흔들림 이하**다. "런간 잡음을 넘던 항만 제거했고 잔차는 그 이하" 로 쓸 수 있다.

**남은 실무 고려**: `exp2` DICOM 을 brainlife.io 에 업로드하는 데이터 거버넌스. `exp1` 선례 있음.

### 4.3 prespec 에 미리 넣을 것

**디페이싱이 `exp2` 정합을 더 나쁘게 만들 수 있다.** §3.1 이 보여준 것이 그것이고 어느 쪽이 옳은지 모른다. 대칭성 논증을 위해 **개입 데이터를 열화시키는** 결과가 될 수 있다.

→ 사전 확정: *디페이싱 후 `exp2` 정합 QC 가 이전보다 나쁘면, 그것이 공통 해부 기준 (`exp2` BOLD → `exp2` T1w → `exp1` T1w → MNI) 으로 승격하는 근거다.* 나중에 붙이면 사후 도피구로 보인다.

### 4.4 재산출 종점 (14칸, 추가 금지)

| 종점 | 셀 |
|---|---|
| hV4 LOCO adjacent accuracy | 2 피험자 × {unfiltered, deployed, individualized} = 6 |
| SRM disparity (사전지정 표적: deutan V2, protan V1) | 6 |
| RDM similarity (동일 셀) | 6 |
| forward-tuning 부호 (secondary) | 2 |

**판정 = 3조건 순위와 Δ 부호.** 크기는 descriptive 로만.

| 패턴 | 원고 조치 |
|---|---|
| 순위·부호 전부 유지 | §3.10/§4.3 불변, §S 에 민감도표 1개 |
| protan hV4 순위만 변동 | §3.10 protan 문장 재작성 |
| deutan 방향까지 반전 | §4.3 개입 서사 축소 |
| **`exp1` 종점 변동** | **실행 오류** — 이 작업은 `exp1` 을 건드리지 않는다 |

---

## 5. 작업 5 — 비교자 범위

`Supplementary/supplementary.tex:815` 는 `OS-level post-display transform` vs `rendered directly in PsychoPy` 로 **비대칭 자체는 공개**한다. 빠진 것은 **범위와 GLM 함의**다.

확정해서 적을 것: macOS 필터가 바꾸는 화면 요소 전체(OS 레벨이므로 원반·주시점·문자열·회색 filler·배경 **전부**) / 개인화 필터가 바꾸는 요소(PsychoPy 렌더, 원반만인지) / **회색 filler 가 조건 간 달라지는가** / 주시점·문자 요소.

**왜 중요한가**: `exp2` 종점은 조건별 Procrustes 를 거친 진폭 위에서 계산된다. filler 가 배포 조건에서만 바뀌면 **그 조건의 GLM 암묵 기준선이 다르다**. 배포 필터의 신경값(protan hV4 0.19)에 개입 효과가 아닌 성분이 들어갈 수 있다.

**방향은 우리에게 불리하지 않다** — 배포 조건이 오염되었다면 protan 에서 배포가 개인화보다 높게 나온 결과의 신뢰도가 낮아지는 쪽이다. 정직하게 적을수록 위치가 나아진다.

**선택**: `data/color_screenshot/` 필터 on/off 스크린샷에서 회색 filler 픽셀값 비교 — 한 줄로 확정 가능.

---

## 6. 작업 6·7 — 문안

### 8AFC 독립 종점 격상

현재 8AFC 는 JND 문단 끝에 붙어 있다(`results_v4.tex:195,197`). **적합 손실에 들어가지 않은 유일한 행동 종점**이다. JND 는 $L_\gamma$ 원자로 적합에 기여했으므로 전향적이지만 독립은 아니다.

| protan | unfiltered | 개인화 | 배포 |
|---|---|---|---|
| 8AFC | 1.00 [0.94, 1.00] | **0.98** [0.92, 1.00] | **0.86** [0.75, 0.92] |

적합에 안 쓰인 종점에서 배포 필터가 정상 수준 식별을 떨어뜨렸고 개인화는 유지했다. 가장 방어하기 쉬운 전향적 결과인데 한 문장에 묻혀 있다. → 독립 서술 + `held out from the fitting loss` 명시.

### 주장 위계

| 금지 | 허용 |
|---|---|
| `individual-specific effect` | `individually derived filter` / `within-person prospective effect` |
| `restores / normalizes cortical representation` | `produced measurable changes in` |
| `outperforms deployed filters` | `differed from the deployed comparator in ...` |
| protan: `robustly identified distortion 의 inverse 검증` | `preprocessing-contingent production model 에서 파생되어 사전 동결된 필터의 전향적 시험` |

`CLAUDE.md` 의 "specificity claim 금지" 와 같은 방향이며 충돌하지 않는다. 4문 구조(Describe → Summarize → Correct → Validate)는 유지, 4번의 정의만 교체.

---

## 7. 이미 종결 — 중복 착수 금지

| 외부 검토 우려 | 좌표 | 결과 |
|---|---|---|
| 일반 전처리 강건성 (§15 #2) | `exp1 · motreg/motshift · endpoint` | hV4 게이트 3 arm 전부 생존 (.011/.013/.002). 색 특이성 7→15 증가는 **실제 움직임 분산 제거**에서 옴 (`motshift` 3 으로 회귀자 부산물 해석 기각). **공간축은 미검정** |
| 파라미터 식별성 (§13) | `exp1 · motreg · beta` | deutan 부호 300/300 유지, protan 반전. 외부 검토 §13 결론과 일치 |
| — (2차 검토가 제기) | `exp1 · motreg · filter` | **deutan 필터 강건 / protan 6-8 반전 + 무필터보다 악화.** 아래 §8 |
| protan JND 이상 (§7) | 행동 | 단일 트랙 lapse. 208 staircase 전수 스캔. 렌더링·gamut 결함 아님 |
| 색측·휘도 (§15 #6) | — | Discussion 한계 문단 반영 완료 |

---

## 8. 필터 강건성 요약 (`exp1 · motreg · filter`)

전문: [`FILTER_ROBUSTNESS_ARMS.md`](../../analysis/phase5_filter_optimization/FILTER_ROBUSTNESS_ARMS.md)

| | deutan | protan |
|---|---|---|
| 색별 부호 반전 | **0/8** | **6/8** |
| Pearson $r$ | $+0.955$ | $\mathbf{-0.567}$ |
| mean $|\Delta|$ | 7.4° | 29.8° (max 52.1°) |
| 교차평가 vs 무필터 | 26.09° → **7.80°** (개선) | 17.77° → **29.26°** (**악화**) |
| 대안 모형 기각 가능? | **가능** (boundary 0.73 > 사전지정 0.5) | **불가** (boundary 0.00) |

**두 피험자가 정반대다.** deutan 의 대안 모형은 원고 자신의 적합성 기준으로 버릴 수 있고, 버리지 않아도 필터가 살아남는다. protan 의 대안은 깨끗해서 버릴 명분이 없다.

**held-out test loss 로 우열을 가릴 수 없다** ($-1.539$ vs $-1.384$) — 서로 다른 전처리 데이터 위의 손실이라 비교 불가. 가장 먼저 떠오르는 탈출구인데 성립하지 않는다.

---

## 8.5 파이프라인 채택 근거 — 쓸 것과 절대 인용하면 안 되는 것

현행 `methods_v2.tex:76` 은 header-initialized MI 를 **썼다**고만 적어, 독자에게는 더 나은 방법을 시도조차 안 한 것처럼 읽힌다. 실제로는 두 층위에서 시도했고 실패했다.

| 층위 | 시도했고 실패한 것 | 정당화하는 것 |
|---|---|---|
| 파이프라인 | **fMRIPrep 정합 전 시도 실패** (사용자 확정 2026-08-10) | 커스텀 파이프라인을 쓴 것 |
| 정합 방법 | **BBR 육안 실패** — partial FOV 에서 잘못된 경계 스냅 (`notion.md:29-35`, 채택 당시 기록: 10 mm 오차 위험 vs MI ~1 mm) | 커스텀 안에서 MI 를 고른 것 |

두 논거는 층위가 다르므로 **같이 써야** §S2·§S3 가 완성된다 — "표준을 안 썼다" 가 아니라 **"표준을 시도했고, 이 취득에서 실패한 측정된 이유를 보고한다"** 가 된다.

### ⚠ 움직임 보정은 이 목록에 넣을 수 없다 (2026-08-15 정정)

한때 세 번째 줄로 `HMC arm 신뢰도 붕괴 (HC −0.048, CVD −0.170)` 를 넣으려 했으나 **철회한다.** 코드를 보면 붕괴 원인이 재정렬 자체가 아니라 **구현**이다.

```
run_method3_hmc_all_subjects.sbatch:122   mcflirt -in BOLD_RAW -out bold_mc ...      ← 보간 1회
run_method3_hmc_all_subjects.sbatch:145   applywarp --in=bold_mc --premat= --warp=   ← 보간 2회
```

`HMC_REANALYSIS_PRESPEC.md:69` 은 "재샘플링은 여전히 1회다" 라고 적었으나 **사실과 다르다.** MCFLIRT 출력은 이미 재샘플된 영상이고 거기에 `applywarp` 가 한 번 더 들어간다. `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md:119` 이 지적한 "재샘플링 2회" 가 이것이다.

**올바른 구현은 시도된 적이 없다.** MCFLIRT `-mats` 로 볼륨별 강체행렬을 받아 `BOLD→T1w` 아핀과 `convert_xfm -concat` 으로 합성한 뒤, 볼륨마다 그 합성 premat 으로 `applywarp` 를 한 번 호출하면 **보간 1회**가 된다 (fMRIPrep 방식).

→ §S2 에 `재정렬을 적용했더니 신뢰도가 음수가 되었다` 고 쓰면 **리뷰어가 한 문장으로 해체한다** ("이중 보간 탓이지 재정렬 탓이 아니다"). 이 논거는 쓸 수 없다. 대신 **올바른 구현으로 재전처리 arm 을 만드는 것**이 정답이다 → §3.
### ⚠ 함정 — 아카이브 정량 지표는 BBR 을 지지한다

`_archive/registration_method_selection/` :

| | BBR | MI |
|---|---|---|
| Dice (sub-01/03/06) | 0.33–0.50 | 0.27–0.36 |
| overlap_frac_bold | 0.96–0.97 | 0.71–0.78 |
| ROI coverage (sub-06) | 99.95% | 85.4% |

**이 지표들은 "슬랩이 뇌 안에서 잘못된 위치에 안착"하는 실패 모드에 둔감하다.** 봉쇄율이 높아도 해부학적 대응은 틀릴 수 있고, 그건 육안으로만 잡힌다. 두 번째 이유로도 인용 불가 — 아카이브의 method3 는 **FSL MNI152 (91×109×91)** 로 돌았고 현행 정본은 **MNI152NLin2009cAsym res-2** 다 (`run_method3_header_mi_all_subjects.sbatch:308-311`).

**따라서 §S2 의 근거는 QC 그림이어야 하고, Dice 표를 넣으면 자기 반박이 된다.** 리뷰어가 직접 계산하면 BBR 이 이기므로, **"전뇌 중첩 지표는 BBR 을 선호하나 슬랩 오위치에 둔감하다"** 를 선제 공개하는 편이 안전하다 — 움직임 arm 에서 이미 쓴 전략.

---

## 9. 분석 실행 결정 — 전부 종결 (2026-08-16)

> 이 표는 **분석 실행** 결정이다. **원고 문안** 결정은 §미완 앞의 「결정 기록 (2026-08-16)」 표에 따로 있다. 두 표의 번호는 서로 다른 계열이므로 인용할 때 반드시 표 이름으로 지칭한다.

| # | 질문 | 결정 | 상태 |
|---|---|---|---|
| A1 | `exp1 · hmc` 를 돌릴 것인가 | 돌린다. `motreg` 는 시간축 대용품이고 공간축은 미지 | **완료** — 60/60 런 |
| A2 | `anat_harmonized` = ezBIDS 양쪽 | 채택 | **완료 2026-08-17** |
| A3 | filler 실측을 넣을 것인가 | 넣는다 (비용 ≈ 0) | 미착수 |
| A4 | 저널 결정 시점 | 필터 강건성 + 정합 결과 이후 | 프레이밍 확정, 최종 결정은 일정에 달림 |
| A5 | 선행 정본 A–I 반영 시점 | 먼저. 원고 준비 완료 상태이고 나머지와 독립 | 미착수 |
| A6 | `exp1·hmc·filter` (β 재적합) | 돌린다. `U2_BETA_SIGN_PRESPEC` 판정규칙 그대로 | **완료** — 분기 B |
