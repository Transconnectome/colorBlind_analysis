# Redteam 중화 실험 결과 — 2026-05-28

문서 수정 없음. 모든 결과는 `results/redteam/exp{1..4}_*.json` 에 저장.

---

## Exp 1 — A13 forward 함수 audit

**스크립트**: `exp1_a13_forward_audit.py`
**JSON**: `exp1_a13_forward_audit.json`

### Active import 경로

| Forward | Active 사용 | Archived 사용 |
|---|---|---|
| **raw** (`two_comp.forward_2comp`, closure-canonical) | **6 files** | 27 |
| **frozen** (`forward_models.two_component`) | **2 files** | 5 |

**Frozen active users 상세**:
- `scripts/forward_models/__init__.py` (단순 re-export)
- `scripts/forward_models/three_component.py` (별개 모델 — 2-component 사용 안 함)

→ **활성 2-component 코드 경로는 전부 raw forward 사용**. CLAUDE.md A13의 "frozen은 `loco_distortion_fit.py` 전용 alternative entry"가 `_archive_pre_closure/older_forwards/loco_distortion_fit.py`로 archive된 상태와 일관.

### Forward 간 δθ 수치 차이 (3 candidate × 8 hues)

| Candidate | family | max\|Δ\| | sign match | cos(raw, frozen) |
|---|---|---|---|---|
| **S08-βs-dom** (38, −10) | deutan | **64.76°** | **2/8** | **−0.65** ← 거의 anti-correlated |
| S08-βc-dom (6, −42)      | deutan | 55.50°    | 4/8       | +0.29 |
| S09-βc-rot (2, +24)      | protan | 17.79°    | 6/8       | +0.74 |

S08-βs-dom 예시:
- raw    : [+8.66, +29.46, +33.00, +17.21, −8.66, −29.46, −33.00, −17.21]
- frozen : [−16.00, −23.71, −28.67, −31.75, −33.76, −6.72, +31.76, +15.56]

CLAUDE.md A13에 기록된 "c1 raw +8.66° vs frozen −16.0°"가 정확히 재현됨.

### 비판 #2 갱신 결론

- **수치 차이는 거대** (특히 S08-βs-dom은 두 forward가 8-vec 부호 6/8 반대, cosine −0.65)
- **그러나 활성 코드 경로에 frozen 2-comp 사용처 없음** — 발견 직후 archive된 viz 스크립트들 (`_archive/visualize_phase3_preimage.py` 등)에만 잔존
- **잔여 risk**: Closure 문서 자체에 "어떤 forward가 어디서 쓰였는가" provenance section이 없음. Phase 3 자극 합성 plan이 향후 frozen을 잘못 import할 risk는 남아 있음 — paper Methods에 명시 필요
- **#2 severity**: "FATAL until resolved" → **"Severe addressable, partly resolved by archiving"**

---

## Exp 2 — Round 3 noise-floor excess test (Mann-Whitney one-sided)

**스크립트**: `exp2_round3_excess_test.py`
**JSON**: `exp2_round3_excess_test.json`

각 candidate의 fit-GT recovery 분포가 null-GT 분포에 비해 *GT 방향으로 통계적으로 이동했는가* 를 50-iter resample (Round 3 출력) 위에서 검정.

### 결과 요약

| Candidate | Axis | GT | null_med | fit_med | signed shift toward GT | MW p (one-sided) | fit within ±10° of GT | null within ±10° of GT | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **S08-βs-dom** | β_s | +38 | +26 | +32 | **+6** | **0.000** | 0.36 | 0.38 | ✓ shifted |
| **S08-βs-dom** | β_c | −10 | −16 | **+26** | +42° (반대 방향) | 0.000 | **0.00** | 0.42 | "✓ shifted" 라벨링은 *부호* 한정 — 실제는 **GT(−10)와 정반대로 +26 가까이 이동** |
| **S08-βc-dom** | β_s | +6  | +46 | +34 | +12 | 0.000 | 0.14 | 0.00 | ✓ shifted |
| **S08-βc-dom** | β_c | −42 | −26 | −26 | −0 | 0.515 | 0.26 | 0.24 | ✗ NOT shifted |
| **S09-βc-rot** | β_s | +2  | +26 | +22 | +4  | 0.029 | 0.42 | 0.24 | ✓ shifted (marginal) |
| **S09-βc-rot** | β_c | +24 | +10 | **−10** | −20° (반대 방향) | 0.562 | 0.42 | 0.24 | ✗ NOT shifted |

### 핵심 발견 — Round 3 framing 강화

1. **S08-βs-dom β_c의 부호 반전이 통계적으로 확정**: GT=−10인데 fit-median이 +26이고 fit-recovery가 GT의 ±10° 안에 들어오는 비율 **0.00 (zero)**. null GT 분포가 오히려 GT에 더 가까움 (0.42 vs 0.00). 이는 "noise floor 안이라 비식별성 미확정"이 아니라 **추정이 GT와 능동적으로 반대 방향으로 끌려간다**는 더 강한 증거.

2. **S09-βc-rot β_c 도 동일 패턴**: GT=+24인데 fit-median=−10 (반대 부호). MW p=0.56 → null과 fit가 통계적으로 구별 안 됨.

3. **β_s 축은 모두 통계적으로 GT 방향 이동**: 그러나 fit가 GT의 ±10° 안에 들어오는 절대 비율은 0.14–0.42 수준 — 통계적 shift가 *실용적 식별성*을 보장하지 않음.

4. **S08-βc-dom β_c**: signed shift = 0, fit_med = null_med = −26 → β_c 추정에서 fit 신호와 noise floor가 완전히 일치. 비식별성 확정.

### 비판 #1 갱신 결론

- 원안: "fit-GT recovery offset이 null GT noise floor와 같은 자릿수 → 비식별성 미확정 OR noise floor 우세"
- **실측**: 3 candidate 6 축 중 *β_s 축 3개만 GT 방향 통계적 shift*. **β_c 축은 모두 GT 방향 검정 실패**, 특히 두 candidate (S08-βs-dom, S09-βc-rot)에서 GT의 반대 부호로 이동.
- **β_s 축은 통계적 검출 가능하나 ±10° 정밀도 미달**. β_c 축은 통계적 검출도 실패.
- **#1 severity**: "Fatal" 유지 강화. 비판 본문의 "noise floor와 같은 자릿수" 표현은 *너무 약했고* 실제는 *β_c 축에서 GT 반대 방향으로 끌려가는 능동적 mis-identification*. Paper에 "the procedure systematically inverts β_c sign under null-perturbed bootstrap" 명시 권고.

---

## Exp 3 — Sub-09 PCA vs SRM RDM-atom disagreement quantification

**스크립트**: `exp3_sub09_atom_disagreement.py`
**JSON**: `exp3_sub09_atom_disagreement.json`

각 RDM atom (PCA, SRM-cos, SRM-dis) × 2 combo (γALL+RDMV1, γGB+RDMV1) × 300 resample 의 fit 분포를 두 attractor (PCA-claim (2,+24) vs SRM-claim (32,0)) 의 ±15° disk 비율로 분해.

### γALL + RDMV1 combo (sub-09 primary)

| Atom | n | (β_s, β_c) median | β_c IQR | PCA-attractor % | SRM-attractor % | outside both % |
|---|---|---|---:|---:|---:|---:|
| **PCA**     | 300 | (+2,  +24) | 0  | **88%** | 12% | 0% |
| **SRM-cos** | 300 | (+32,  0)  | 2  | 4%      | **79%** | 16% |
| **SRM-dis** | 300 | (+32,  0)  | 2  | 0%      | **97%** | 3% |

### γGB + RDMV1 combo (alternative sub-09)

| Atom | n | (β_s, β_c) median | β_c IQR | PCA-attractor % | SRM-attractor % | outside both % |
|---|---|---|---:|---:|---:|---:|
| PCA     | 300 | (+2,  +24) | 0  | 88% | 12% | 0%  |
| SRM-cos | 300 | (+32,  0)  | 10 | 4%  | 67% | 28% |
| SRM-dis | 300 | (+32,  0)  | 10 | 0%  | 87% | 13% |

### 핵심 발견

1. **두 SRM family는 sub-09에서 동일 결과**: SRM-cosine과 SRM-disparity의 fit 분포가 87–97% 가 (32,0) attractor 내. 즉 **2 independent atom families가 (32, 0) 으로 강하게 수렴**.

2. **PCA-RDM 은 outlier**: 88% 가 (2, +24) attractor. SRM-family에 대한 disagreement가 *통계적 잡음이 아닌 atom 정의의 systematic difference* 임을 확정.

3. **closure §A.2 에서 보고한 single-median 값이 underestimate한 disagreement**: closure는 PCA (2,+24) vs SRM (32,0) median만 보고했지만 본 audit는 *300 resample 의 90% 이상이 각 attractor에 안정적으로 모인다*는 사실을 추가로 보여줌. **두 atom family가 정말로 두 다른 mechanism을 가리킴**.

### 비판 #4 갱신 결론

- **#4 severity**: "Severe addressable" 유지. PCA-RDM이 outlier라는 증거가 *단일 median 비교*가 아니라 *300-resample distributional concentration* 으로 강화됨.
- Sub-09 mechanism interpretation을 SRM family 우선 (S-cone shift primary, (32, 0)) 으로 변경하면 *PCA-RDM은 alternative descriptive fit*으로 보고할 수 있음 — currently closure 의 inverse 우선순위.
- 동시에 paper claim "neural geometry uniquely identifies cortical confusion-axis rotation invisible to behavior" (RQ5)는 *PCA-RDM atom 선택의 함수*. 이 claim은 retract 또는 atom-conditional로 명시 필요.

---

## Exp 4 — Step 4 (38, −10) rescue audit

**스크립트**: `exp4_step4_rescue_audit.py`
**JSON**: `exp4_step4_rescue_audit.json`

### Direct evidence — cycle6b output 자체가 classification 제공

`cycle6b_extended_composite_sub-08.json` 안에 두 list가 명시:
- `cycle6_baseline_keys` = Step 3 (composite z-score) 에서 surface된 candidates → **14개**
- `new_candidates_keys`  = Step 4 (raw-weight) 에서 *추가로* surface된 candidates → **8개**

| Step 3-visible (cycle6_baseline) | Step 4-only (new_candidates) |
|---|---|
| `2C\|bs=0,bc=0` | `2C\|bs=36,bc=-14` |
| `2C\|bs=14,bc=-46` | **`2C\|bs=38,bc=-10`** ← closure βs-dom |
| `2C\|bs=14,bc=-48` | `2C\|bs=40,bc=40` |
| `2C\|bs=16,bc=-10` | `2C\|bs=44,bc=28` |
| `2C\|bs=16,bc=-44` | `2C\|bs=44,bc=36` (excluded later) |
| `2C\|bs=18,bc=-36` | `2C\|bs=45,bc=-24` |
| `2C\|bs=32,bc=0` | `2C\|bs=46,bc=24` |
| `2C\|bs=36,bc=-26` | `RC\|g=2.25` |
| `2C\|bs=4,bc=-26` | |
| `2C\|bs=50,bc=-34` | |
| `2C\|bs=50,bc=-36` | |
| **`2C\|bs=6,bc=-42`** ← closure βc-dom | |
| `RC\|g=0.70` | |
| `RC\|g=1.10` | |

**Verdict (데이터 자체에서)**: `STEP4_ONLY` — (38, −10)은 Step 4 raw-weight reranking에서만 emerge.

### Step 3 re-ranking 재현

71 개 2-component combo × test_loss_median ASC 정렬:

| Rank | Combo | (β_s, β_c) | test_loss ± IQR | bdy |
|---:|---|---|---|---:|
| 1 | γ_\|RDM_\|LOCO    | (+50, +50) | −3.43 ± 0.00 | 100% |
| 2 | γ_\|RDMV1\|LOCO   | (+50, +24) | −3.40 ± 1.01 | 100% |
| 3 | γ_\|RDMV3\|LOCO   | (+50, +24) | −3.20 ± 0.78 | 100% |
| ... | (모두 boundary saturate) | | | |
| **45** | γ_\|RDMV4\|noLOCO | (+36, −14) | −1.20 ± 2.81 | 28% |
| **46** | **γALL\|RDMV1\|noLOCO** | **(+38, −10)** | **−1.14 ± 0.86** | **0%** |

Step 3 metric (test_loss_median) 단독으로는 (38, −10)이 **46위/71** 이며, top-10은 모두 boundary-saturated (bdy=100%) cells. Closure §3.5의 Supplementary collapse criterion (`boundary_rate < 0.5`)을 적용하면 top-10이 모두 제거되어 (38, −10)이 더 위로 올라오긴 하나, *closure 본문의 단순 "test_loss_median ASC primary"* 만으로는 (38, −10)이 비-top이다.

### Step 4가 (38, −10)을 surface시키는 schemes (12/47)

모두 `γALL|RDMV1|noLOCO` combo + γ_focal + γ_all 동시 가중:

| Scheme | Weights [focal, all, RDM] | Rank in scheme |
|---|---|---:|
| 2γfocal+1γall            | [2, 1, 0]   | 3 |
| 2γfocal+1γall+25RDM      | [2, 1, 25]  | 3 |
| 2γfocal+1γall+50RDM      | [2, 1, 50]  | 3 |
| 2γfocal+1γall+100RDM     | [2, 1, 100] | 3 |
| 2γfocal+1γall+200RDM     | [2, 1, 200] | 3 |
| 2γfocal+1γall+400RDM     | [2, 1, 400] | **2** |
| 5γfocal+1γall            | [5, 1, 0]   | **2** |
| 5γfocal+1γall+25RDM      | [5, 1, 25]  | **2** |
| 5γfocal+1γall+50RDM      | [5, 1, 50]  | **2** |
| 5γfocal+1γall+100RDM     | [5, 1, 100] | **2** |
| 5γfocal+1γall+200RDM     | [5, 1, 200] | **2** |
| 5γfocal+1γall+400RDM     | [5, 1, 400] | **2** |

핵심: (38, −10) 이 top으로 surface 하려면 **(i) γ_focal AND γ_all 가중치 동시에 양수** AND **(ii) γ_focal ≥ 2** 가 필요. **γ_all=0 또는 γ_focal=0 schemes 에서는 surface 안 됨**.

### 비판 #5 갱신 결론

- **#5 severity**: "Severe addressable" → **확정**.
- **Cycle6b output 자체가 (38, −10)을 `new_candidates_keys`로 분류** — Step 4-only emergence가 외부 비판이 아니라 *문서의 자체 출력에 기록된 사실*. Closure §4 narrative 의 "기존 cell을 다른 weight 로 보면 surface" 표현은 cycle6b output 의 class 명칭 (`new_candidates`)과 일관성 없음.
- Closure 가 (38, −10) 을 final candidate 로 보고하려면 **Step 4를 primary selection path 로 promote** 하거나, "Step 3 cell-level primary metric 미달이지만 Step 4 raw-weight robustness 기준 추가 통과" 형식의 **dual-criterion selection rule을 사전 등록된 것처럼 본문에 명시** 해야 함.
- Sub-08 "two parallel mechanism hypotheses (βs-dom vs βc-dom)" claim 의 한 축이 Step 4-only emergence 이라는 사실은 **paper Methods/Discussion에 explicit disclosure 필요**.

---

## 통합 verdict — 비판 5개 갱신

| # | 원안 severity | 실험 후 갱신 |
|---|---|---|
| 1 | Fatal | **Fatal 유지 강화** — Round 3 β_c 축이 GT의 반대 부호로 능동적으로 끌려감 (S08-βs-dom, S09-βc-rot). "Noise floor 같은 자릿수"는 너무 부드러운 표현. |
| 2 | Fatal until resolved | **Severe, partly resolved** — A13 수치 차이는 거대 (cos −0.65, max\|Δ\|=64.8°)나 active 코드 경로에 frozen 2-comp 사용처 없음. Closure에 provenance section만 추가하면 충분. |
| 3 | Fatal framing | 변동 없음 (실험 대상 아님) |
| 4 | Severe addressable | **확정 강화** — PCA 단독 outlier, SRM 2 family 90%+ concentration on (32, 0). Single-median이 아닌 distributional 증거. |
| 5 | Severe addressable | **확정 완료** — cycle6b output 자체가 (38, −10)을 `new_candidates_keys`로 분류. 외부 비판이 아닌 self-documented 사실. |

### 다음 단계 권장 (사용자 결정 사항)

1. **Closure §5.2 Round 3 noise-floor caveat 재작성**: β_c 축은 noise floor 이내가 아니라 *GT 반대 방향으로 active mis-identification*. β_s 축은 통계적 shift은 있으나 ±10° 정밀도 미달. (해석 수정만, 2h)
2. **Closure 본문에 forward-function provenance section 추가**: 모든 active script가 `two_comp.py` 사용하고 frozen variant는 archive 처리됨을 명시. Phase 3 자극 스크립트도 동일 forward 사용함을 lock. (2h)
3. **Sub-09 §A 결과를 본문 §5.1로 promote**: PCA-RDM (2,+24) vs SRM-family (32,0)의 90%+ distributional disagreement를 §5.1 Mechanism interpretation에 명시. RQ5 cortical-rotation claim 의 atom-conditional 단서 추가. (2h + 2d)
4. **Step 4 (38, −10) rescue를 §4에서 explicit disclosure**: cycle6b output의 `new_candidates_keys` 라벨링을 본문에 인용. (38, −10)이 dual-criterion (Step 3 cell-level + Step 4 raw-weight)에서만 통과한 candidate임을 명시. (2h)
5. **선택**: JND-perturbation을 포함한 Round 4 재실행 (`s13_round3.py` 에 perturbed JND 추가). γ 항이 GT-aware 되어 β_c 식별성이 개선되는지 검증. (2d)

본 보고서는 closure 문서를 *수정하지 않는다*. 위 권장은 사용자 결정 후 별도 revision 패스에서 적용 가능.

---

## Files

| File | Role |
|---|---|
| `exp1_a13_forward_audit.py` / `.json` | Forward function audit + δθ comparison |
| `exp2_round3_excess_test.py` / `.json` | Round 3 fit-GT vs null-GT excess test |
| `exp3_sub09_atom_disagreement.py` / `.json` | PCA vs SRM distributional concentration |
| `exp4_step4_rescue_audit.py` / `.json` | Step 4 (38, −10) rescue confirmation |
| `2026-05-28.md` | Original redteam report (5 criticisms) |
| `2026-05-28_experiments.md` | 본 문서 (실험 결과 요약) |
