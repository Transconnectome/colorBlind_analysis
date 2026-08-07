# `results_v4.tex` 전수 검사 (2026-08-07)

> 문단별 개정의 지배 문서. 진행 방식: 문단 단위 수정안 제안 → 확인 → 반영 → 컴파일 검증.
> 상위 결정은 [`../REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](../REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md)가 지배한다.
> Methods 개정 현황은 [`../METHODS_REVISION_STATUS_2026-08-07.md`](../METHODS_REVISION_STATUS_2026-08-07.md).

## 서술 제약 (전 문단 공통)

- 한 문장 길이 억제, 삽입구 최소화 — 특히 `:` 와 `;`
- academic vocabulary, rigorous verbs, direct meaningful expressions
- **두괄식**: 각 문단은 핵심 결과·주장·해석으로 시작. 배경·절차·양보로 시작하지 않는다
- **부정 표현 최소화**: `not` A 보다 관측된 B 를 직접 서술. null result 는 실패가 아니라 효과크기·불확실성·재현성으로 보고. 정확한 보고에 필요한 부정형은 유지

---

## 1. 사실 오류 — 즉시 수정

### A-1 🔴 `L38` "V2 and V3 below chance"

**현재**

> V1--V3 did not significantly exceed chance even though the colors remained decodable across runs (V1 $p = 0.164$; V2 and V3 below chance).

**근거** — `exp2_hc_likeness_sub-08_matched.json`, HC 6-run adjacent accuracy:

| ROI | HC adjacc | vs chance 0.25 |
|---|---|---|
| V1 | 0.393 | **위** |
| V2 | 0.357 | **위** |
| V3 | 0.339 | **위** |
| hV4 | 0.465 | 위 |

**네 ROI 모두 해석적 chance 위**다. 2026-08-07 의 chance $3/8 \to 0.25$ 정정(계획 문서 §7a)에서 `3/8` 문자열이 든 8 곳은 고쳤으나, 이 문장은 숫자 없이 단어로만 표현해 누락되었다.

**논리는 유지된다.** hV4 를 가르는 것은 해석적 chance 가 아니라 **색 라벨 순열 귀무**이며, 이는 이미 Methods 에 반영되어 있다("tested against an empirical null of 1,000 random color-label permutations rather than against the analytic chance level").

**대체 방향** — 네 ROI 모두 해석적 chance 를 넘지만 순열 귀무를 넘는 것은 hV4 뿐이라는 구조로 재작성. 순열 검정이 판별자임이 본문에서 보이게 한다.

### A-3 🔴 `L31` "sat inside the healthy-control distribution at every ROI" — **[해결 2026-08-07]**

전수 검사 이후 `DECODER_AUDIT_2026-08-07.md` §8 과 대조하며 추가 발견. Crawford–Howell 재산출표:

| ROI | HC 평균±SD | sub-08 $d_{cc}$ | sub-09 $d_{cc}$ |
|---|---|---|---|
| V1 | 0.542±0.106 | +0.59 | +0.79 |
| V2 | 0.545±0.077 | −1.11 | −1.38 |
| V3 | 0.449±0.065 | −1.15 | **−2.12** |
| hV4 | 0.423±0.072 | −0.95 | −0.95 |

$d_{cc} = -2.12$ 는 HC 분포 안이 아니다. 감사 문서의 경고와 정면 충돌한다 — *"|d_cc|가 최대 2.12다. '차이없음'으로 강하게 쓰면 검정력 부족을 유의성 부재로 바꿔 읽는 것이 된다. 본문은 유의성만 진술한다."* 또한 Supplementary §S19 의 FE 전이 비교는 $p = 0.052$, $r_{rb} = 0.46$ 으로 방향이 반대다.

**조치** — 분포 포함 주장 삭제. 최소 $p$ 와 $|d_{cc}|$ 범위로 대체하고, Mann–Whitney $p = 0.052$ 를 본문에 노출.

### A-4 🔴 정렬 공간 불일치 — **[해결 2026-08-07]**

§3.1 검토 중 발견. 세 겹의 불일치가 있었다.

1. **정본 공간은 Procrustes.** `utils_forward_model.load_amplitudes()` (`:46-61`) 는 `amplitudes_procrustes.npy` 만 읽으며 SRM 경로가 없다. 이 함수를 쓰는 `loco_canonical.py` 와 `permutation_test_loco.py` 가 §3.2 의 근거이므로 **LOCO 와 순열 검정은 Procrustes**다. LORO 만 SRM 이었다.
2. **Fig 2 가 패널 내부에서 공간을 섞었다.** `generate_fig2.py` 의 LOCO **HC** 는 `results/loco_srm`(SRM), LOCO **CVD** 는 `loco_decoding_comparison`(Procrustes). 헤드라인 비교의 두 항이 다른 공간이었다.
3. **본문 통계와 그림의 출처가 달랐다.** 본문의 $t=-2.91/-1.84$, $d_{cc}=-3.14/-1.99$ 는 Procrustes/Procrustes $n=6$ 단측과 일치하며, 그림이 그리던 값과 다르다.

**결정 (사용자 승인 2026-08-07)**

| 분석 | 공간 | 근거 |
|---|---|---|
| LORO, LOCO (피험자 내) | **Procrustes**, $n=7$ | Phase-1 정본. 공통 공간 불필요 |
| 교차피험자 전이 | **SRM** | 공통 공간이 필수인 분석 |
| Procrustes disparity · RDM 기하 | SRM | 상동 |
| SRM LORO/LOCO | **Supplementary §S20** | 정렬 강건성 |

**sub-07 포함.** hV4 16 복셀(나머지 여섯은 67–70), V3 59(나머지 106–115). 포함해도 결론 불변이며 오히려 강해진다 (Procrustes LOCO hV4 단측: 제외 $n=6$ → sub-08 $p=.063$ / sub-09 $p=.017$, 포함 $n=7$ → $p=.055$ / $p=.012$). `generate_fig2.py:45` 는 이미 전 ROI 에서 $n=7$ 로 그리고 있어 캡션의 "$n=6$ at hV4" 와 모순이었다.

**교차 전이는 LOCO 판본이 없다.** `cross_subject_generalization()` 은 8색을 모두 훈련에 넣고 exact accuracy 를 보고한다. `loso_zero_shot` config note 는 *"no LOCO/LORO on ZS"*, `fe_cross_decoding` 도 색을 빼지 않는다. LORO 하위 배치가 옳다.

### A-2 🟡 `L217` 보간 문단 — ROI 미명시 + 미보고 결과

hV4 수치는 JSON 과 **전부 일치**한다(sub-08 0.231 / 0.25 / 0.3125, sub-09 0.1375 / 0.1875 / 0.0625). 문제는 두 가지다.

**① 문단 어디에도 `hV4` 가 없다.** 전 ROI 결과처럼 읽힌다.

**② protan 의 V1·V2 는 방향이 반대다.**

| sub-09 | no-filter | deployed | **individualized** | HC |
|---|---|---|---|---|
| V1 | 0.179 | 0.125 | **0.406** | 0.401 |
| V2 | 0.123 | 0.219 | **0.375** | 0.373 |
| hV4 | 0.138 | 0.188 | 0.063 | 0.456 |

protan 은 V1·V2 에서 개인화 필터가 **HC 수준에 도달**한다. 본문은 hV4 만 보고하며 "the lowest of the three conditions" 라고 쓴다. Fig 8D 에는 네 ROI 가 모두 있으므로 독자가 불일치를 본다.

hV4 가 사전지정 ROI 인 것은 정당하다(HC 가 순열 귀무를 넘는 유일한 ROI). 다만 **ROI 를 명시하고 V1/V2 방향이 반대임을 한 문장으로 밝히는 편**이 안전하다. 숨기면 selective reporting 으로 읽힌다.

---

## 2. [TODO: BLUF] — 미괄식 문단

| 행 | 현재 첫 문장 | 판정 | 첫 문장으로 올릴 것 |
|---|---|---|---|
| **29** | `A corrective stimulus-space filter is valid only if...` | 🔴 배경·전제 | `Both CVD participants exceeded the 0.125 exact-accuracy chance level at every ROI` (L31) |
| **38** | `We next tested whether continuous hue interpolation fails in CVD, using...` | 🔴 절차 | `Only hV4 supported hue interpolation above its permutation null in the healthy controls` |
| **64** | `To characterize the geometric basis..., we compared...` | 🔴 목적·절차 | `The ROI of elevated disparity differs between the two CVD participants` (L66) |
| 99 | `The 2-component cortical model fit both participants...` | ✅ | — |
| 120 | `Fitting psychophysical and neural loss atoms independently reveals three benefits...` | ✅ | — |
| **186** | `We evaluated the two filters in a second session..., using...` | 🔴 절차 | 심리물리 결과가 헤드라인. 로드맵 문장은 두괄 뒤로 |
| 189 | `Both filters improved hue-discrimination thresholds and color identification in the deutan participant.` | ✅ | — |
| 217 | `For color interpolation (LOCO decoding), the two participants gave opposite results.` | ✅ | — |
| 220 | `Neither filter fully restored the representational geometry to the HC level, and...` | 🟡 부정 시작이나 **결과 자체가 그것** → BLUF 충족, NEGA 로 이월 | — |

**L29·L64·L186 이 모두 "우리는 ~을 하기 위해 ~했다" 형태**다. L38 까지 네 절이 연속이라 Results 전반부가 절차 나열로 읽힌다.

---

## 3. [TODO: NEGA] — 부정 프레이밍

### 3a. 수정 권고

| 행 | 표현 | 문제 | 대체 방향 |
|---|---|---|---|
| 38 | `whether continuous hue interpolation **fails**` | 가설을 실패형으로 | `whether interpolation is reduced` |
| 38 | `**did not** significantly exceed chance` | A-1 과 함께 | 순열 귀무 대비 결과를 직접 |
| 42 | `the reduction was **not** uniform across hues` | | `the reduction concentrated on particular hues` |
| 42 | `reached significance at **no** individual hue` | 필요한 보고 | **유지**, 단 문단 끝으로 |
| 66 | `with **no** elevation at V2, V3, or hV4` (×2) | 정확한 보고 | **유지** |
| 68 | `Because the deviation is **not** shared, a family-level correction **cannot** serve both.` | 이중부정 | `Because each deviation is participant-specific, a family-level correction would address one case at a time.` |
| 82 / 86 | 제목·첫 문장 `structurally **insufficient**` | 비교 모형 평가 | **유지** |
| 90 | `the saturated boundary is a model **failure**, **not** a valid parameter estimate` | | `the saturated boundary indicates misspecification rather than a parameter estimate` |
| 103 | `the choice among neighboring cells was therefore **weakly** determined` | | `neighboring cells were nearly equivalent on held-out loss` |
| 107 | `For **neither** participant did the LOCO loss family enter` | 도치 + 부정 시작 | `Both winning combinations paired a JND atom with a $\Delta$RDM atom, and the LOCO family entered neither.` |
| 116 | 제목 `Neural data identifies what psychophysics alone **cannot**` | 심리물리 폄하로 읽힘 | `Neural data resolves a direction psychophysics leaves open` |
| 122 | `the psychophysical loss **cannot** resolve` / `**cannot** detect` | 2 회 반복 | `leaves unresolved` / `the RDM term recovers a direction the psychophysical loss leaves open` |
| 129 | 제목 `per-axis magnitude **not**` | | `mechanism class recoverable, per-axis magnitude bounded` |
| 133 | `Parameter recovery **fails** across all pre-specified checks (0/6 ...)` | null result 를 실패로 | `All six pre-specified identifiability checks returned non-significant results after FDR correction, which bounds the per-axis magnitude claim.` |
| 133 | `are **not** recoverable` | | `fall within the procedure's uncertainty floor` |
| 135 | `sign stability under the SRM-basis loss was **not** verified` | 정확한 보고 | **유지** |
| 189 | `**neither** leaving a significant deviant pair` / `**no** significant baseline deviant pair` / `produced **no** deviant pair` / `introduced **no** new significant deviation` | 4 회 | 앞 3 개는 `every pair stayed within the HC range` 계열로, **마지막은 핵심 주장이므로 유지** |
| 217 | `the effect **did not** replicate in the protan participant` | | `the effect was specific to the deutan participant` |
| 220 | `**Neither** filter fully restored...` | 절 첫 문장 | 결과가 그것이므로 **유지**. 참가자별 반대 방향이 정보량이 크므로 병렬 배치 |

### 3b. 유지 (정확한 과학적 보고에 필요)

`no elevation at V2, V3, or hV4` · `sub-07 excluded` · `sign stability not verified` · `0/6 significant` 수치 · `introduced no new significant deviation`(핵심 주장)

---

## 4. 문장 길이 · 삽입구

| 행 | 최장 문장 | 문제 |
|---|---|---|
| 31 | 47 어절 | 세미콜론 2 개 든 괄호 |
| **88** | **58 어절** | 🔴 세미콜론 1 + 괄호 3 |
| 90 | — | 콜론 1 개 (`with confirmed CVD status: the model claims...`) |
| **103** | **62 어절** | 🔴 세미콜론 1 + 괄호 3 |
| **109** | **62 어절** | 🔴 콜론 1 개 (`a free term in the search:`) |
| **189** | **61 어절**, 12 문장 문단 | 🔴 세미콜론 2 개. 심리물리 문단이 최고 밀도 |
| 217 | 44 어절 | 세미콜론 1 개 |
| 220 | 48 어절 | 세미콜론 2 개 |

전체 `;` **11 개**, `:` **3 개**. Methods 를 0 개로 정리한 것과 대비된다.

---

## 5. 검증 완료 — 문제 없음

| 항목 | 대조 결과 |
|---|---|
| exp2 hV4 adjacc 6 개 값 | `exp2_hc_likeness_sub-{08,09}_matched.json` 과 **전부 일치** |
| Fig 4(A) LORO chance $1/8$ | ✓ |
| 필터 파라미터 (6, −42) / (2, +24) | `s10b_v6_pca_rdm.py:SUBJECTS` 와 일치 |
| sub-09 ROI 사전지정 공개 (L109) | 요구된 조치 **이행 완료** |
| 8/8 pre-image 정확, residual < 0.001° (L174) | `exp2_compute_preimage.py` closure invariant 과 일치 |

---

## 6. 진행 순서 — 소절 단위

소절 하나마다 A-항목 · BLUF · NEGA · 길이를 **동시에** 처리한다. 항목별 일괄 처리보다 문단 재작성이 겹치지 않는다.

| # | 소절 | 동시 처리 항목 | 상태 |
|---|---|---|---|
| 1 | `3.1` All eight colors remain decodable | A-3, A-4, BLUF L29, 길이 L31 | ✅ 2026-08-07 |
| 2 | `3.2` Hue interpolation reduced at hV4 | A-1, A-4, BLUF L38, NEGA L38·L42, Fig 2 캡션 | ✅ 2026-08-07 |
| 3 | `3.3` Geometric deviation | **B-1**, BLUF, NEGA | ✅ 2026-08-07 |
| 3b | **`3.4` 심리물리 기저 (신설)** | §S21 신설 | ✅ 2026-08-07 |
| 4 | `3.5` 모형 비교 (structurally insufficient) | **C-1**, NEGA, 길이 | ✅ 2026-08-07 |
| 5 | `3.6` 2-component 적합 | **D-1**, 길이, NEGA | ✅ 2026-08-07 |
| 6 | `3.7` 신경항의 역할 | **F-1 F-2**, 제목 NEGA, BLUF | ✅ 2026-08-07 |
| 7 | `3.8` Identifiability | **B C E H J**, 제목 NEGA | ✅ 2026-08-08 |
| 8 | `3.9` 필터 구성 (pre-image) | **F**(캡션 오참조), BLUF, 신규사실 6/8 | ✅ 2026-08-08 |
| 9 | `3.10` 필터 평가 | **A**(run-match), **G**(Fig 8 캡션), BLUF, NEGA, 길이 | ✅ 2026-08-08 |
| 10 | 전체 | 최종 정확성 · 주장 범위 · `;`/`:` 잔여 재점검 | ✅ 2026-08-08 |

> 소절 번호는 §3.4 신설로 한 칸씩 밀렸다.

### 완료 기록

**1. `3.1` (2026-08-07)** — A-3 해소(분포 포함 주장 삭제), Mann–Whitney $p=0.052$ 본문 노출, 두괄식 전환, `;` 2→0. 단일사례 8검정은 §S19 포인터 한 문장으로 축소하고 ¶2를 전이 결과로 시작하도록 재편(사용자 지시). Procrustes 재산출로 최소 $p$ 0.189 · $|d_{cc}|$ 0.25–1.58.

**2. `3.2` + Fig 2 (2026-08-07)** — A-1 해소. 네 ROI 순열을 $n=7$ Procrustes 단일 설계로 재산출:

| ROI | 관측 | 순열 귀무 | $p_{perm}$ |
|---|---|---|---|
| V1 | 0.393 | 0.346±0.047 | 0.164 |
| V2 | 0.357 | 0.349±0.045 | 0.424 |
| V3 | 0.339 | 0.347±0.043 | 0.586 |
| **hV4** | **0.456** | 0.346±0.042 | **0.011** |

V1은 커밋된 `_perm_v1.log`(0.3929, p=0.1638) 정확 재현. 순열 귀무가 **0.346**으로 해석적 chance 0.25보다 훨씬 높다는 점이 A-1의 핵심 — "chance를 넘는가"와 "귀무를 넘는가"가 다른 진술이다.

hV4 단일사례 $n=7$ 단측: deutan $t=-1.89$, $p=.054$, $d_{cc}=-2.02$ / protan $t=-3.04$, $p=.012$, $d_{cc}=-3.25$. 색별은 blue $p=.051$이 최대 편차이나 유의 아님.

**구현 통일.** `phase3_decoder_comparing`의 저장 JSON은 `test_decoding_methods.py → loro_baseline.loco_cv`라는 별개 구현이며 정본 `loco_canonical`과 36셀 중 35셀 일치, sub-07 hV4만 $\Delta=0.0042$. Fig 2가 정본 함수를 직접 호출하도록 변경해 그림·본문·순열이 한 구현을 쓴다.

**속도.** 정본 함수는 V1 한 draw에 29.2초(1000 draw ≈ 8시간). `_perm_adjacent_n7.py`가 두 가지 정확한 최적화(`decode_hue`의 360회 `np.corrcoef` 루프 → 단일 matmul, 폴드마다 불변인 `lstsq` 설계행렬의 `pinv` 호이스팅)로 0.0089초까지 단축. 60개 조건에서 1e-12 일치 검증 내장. 4 ROI 3분 21초. **서버 불필요.**

**Fig 2 캡션**을 NeuroImage 관례에 맞춰 측정 방법 기술만 남기고 결과 수치를 제거(사용자 지시). 유의성 표기는 게이트 통과 ROI로 제한(`PERM_PASS_ROIS`), Panel A 단일사례는 Methods와 맞춰 양측.

**3. `3.3` (2026-08-07)** — 결과를 첫 문장으로, 참가자별 문단 분리, `not shared`+`cannot serve` 이중부정 제거, em-dash 삽입구 분할, `capture` → `offset`, `The two cases` → `The two CVD participants`. LOSO 추정량 서술의 중복 절 삭제(사용자 지적).

**B-1 공개.** `tab:disparity_loso`의 deutan 행은 V2 $p=.040$ ($d_{cc}=2.26$) 과 **V3 $p=.052$ ($d_{cc}=2.05$)** 가 사실상 구분되지 않고, LOSO에서는 .116 vs .143으로 둘 다 비유의하다. 기존 `with no elevation at V1, V3, or hV4`는 성립하지 않아 삭제하고 `V2 and V3 are not separable here`를 명시했다. protan은 V1 .007/.045 대 차순위 hV4 .150/.228로 깨끗하다.

**B-2 해결.** `tab:disparity_loso`에 LOSO $d_{cc}$ 열 추가(deutan V1 .51 / V2 1.42 / V3 1.25 / hV4 .07, protan V1 2.16 / V2 .82 / V3 .06 / hV4 .86). 본문의 1.42가 이제 표에 있다. Supplementary의 `attenuates to a non-significant trend under LOSO` → `does not survive under LOSO` 로 교체하고 deutan V3 미분리도 같이 명시 — R3가 본문에서 "trend"를 삭제한 근거가 Supplementary에도 동일하게 적용된다.

**Supplementary 재배열 (2026-08-07).** S20·S21을 말미에 덧붙이면서 본문 서사와 어긋난 것을 바로잡았다. 두 절을 이동하고 21개 절을 재번호:

| 이동 | 옛 → 새 | 근거 |
|---|---|---|
| Alignment Robustness | S20 → **S11** | 디코더 절(S10) 직후, LORO/LOCO 판독을 다루므로 |
| Session-1 JND | S21 → **S15** | 기하 보충(S12–S14) 뒤, 모형 적합 보충(S16–) 앞 = 본문 §3.3→§3.4→§3.5 순서 |
| 나머지 | S11–S19 → S12–S14, S16–S21 | 상기 삽입에 따른 이동 |

`\subsection*`가 무번호라 절 번호가 제목에 하드코딩되어 있고 참조도 `\S S<n>` 리터럴이다. 17개 참조를 매핑 적용 후 전수 검증했다(전부 의도한 절 지시). 백업: `scratchpad/supplementary_before_reorder.tex`.

**3b. `3.4` 신설 + §S21 (2026-08-07)** — $L_\gamma$가 §3.6에 등장하는데 그 입력인 Session-1 JND가 본문에 없고 §3.10(2차 세션)에 가서야 처음 나오는 구조적 공백을 해소(사용자 지적). 상승 쌍이 각자 subtype 혼동축과 정확히 일치:

| pair | 축 | deutan $\gamma$ ($z$) | protan $\gamma$ ($z$) |
|---|---|---|---|
| orange–yellow | deutan | **3.02 (+4.15)** | 0.69 (−0.63) |
| yellow–green | deutan | **3.10 (+4.32)** | 1.42 (+0.87) |
| green–blue | protan | 0.98 (−0.06) | **1.95 (+2.36)** |
| yellow–purple | S-cone | **2.87 (+6.70)** | 1.26 (+0.94) |
| red–cyan | 통제 | 0.45 (−1.23) | 0.45 (−1.23) |

**4. `3.5` (2026-08-07)** — 길이(protan 58어절 → 3문장), `;` 1개·`:` 1개 제거, `is a model failure, not a valid parameter estimate` → `indicates misspecification rather than a parameter estimate`, `(below)` ×2 삭제 후 세 근거를 한 문장에 나열.

**C-1 $\Delta\lambda$ anchor 미공개 → 해소.** Methods L234는 R+C를 `carries a single free parameter`라고만 쓰지만, $\Delta\lambda$는 자유 파라미터가 아니라 아형별 문헌값 **세 개에 고정**되어 각각 적합된다 (`s8_loo_train_test.DELTA_LAMBDA_BY_FAMILY`: deutan 6.0/6.5/8.0 nm, protan 1.5/3.0/10.0 nm). 선택된 config에서 anchor별 편차가 크다:

| | anchor | boundary | $g$ | $\overline{L}_{\rm test}$ |
|---|---|---|---|---|
| deutan `γOY\|RDMV2\|noLOCO` | JND_Lamb | 1.00 | 3.0 | **0.185** |
| | Boehm_mid | 0.71 | 3.0 | 0.193 |
| | DPS_lit | 1.00 | 3.0 | 0.428 |
| protan `γALL\|RDMV1\|noLOCO` | **Boehm_low** | **0.41** | **2.95** | **−0.859** |
| | JND_Lamb | 1.00 | 0.0 | −0.637 |
| | DPS_lit | 0.00 | 0.5 | +0.166 |

본문의 100%/g=3.0 과 41%/g=2.95 는 각각 held-out loss 최선 anchor의 값으로 **정확**하다. 2-comp 값(−2.359 / −1.539)과 배포 파라미터 $(6,-42)$ / $(2,+24)$ 도 일치해 config 식별이 확정된다. protan은 anchor에 따라 boundary 가 0–100% 로 갈리므로 공개가 필수. Results 2번째 문장 + Methods L234 + S16 `Fits` 문단에 각각 반영.

> ⚠️ 남은 문체 위반: Methods L234 의 `The gain $g$ parameterizes cortical compensation:` 문장이 콜론 1 + 세미콜론 2. 이 문단을 이번에 건드렸으므로 함께 정리 권장.

**3b 계속.** 이 표가 Methods의 사전지정 $\gamma$ 원자(deutan OY·YG·YP / protan GB)를 그대로 재현한다 — 원자 선택 근거가 본문에 생겼다. 평균 $|z|$ 2.24 / 0.90은 §3.10 기저값과 일치. **기술통계만 제시하고 검정은 §3.10에 유지**(사용자 선택 1안) — §3.10이 이미 green–blue를 `trending p=.070` 양측으로 보고하므로 이중 보고를 피한다. 출처: `behav_loss.load_jnd_per_pair` + `s8_loo_train_test.jnd_baseline_from_pool`, HC pool = sub-01~07.


---

# 2026-08-08 — §3.6–§3.10 및 최종 점검

## 서브에이전트 전수 검증

§3.8–§3.10 의 61개 주장을 별도 에이전트가 대조. 대부분 MATCH, 아래가 불일치.
검증된 소스: `closure/{selection,validation,specificity,gate}`, `s10_inclusion`,
`exp2_preimage`, `exp2_behavior`, `exp2_neural/results`. sub-10 미사용, hV4=디스크 `V4` 확인.

## 적용한 정정

| # | 절 | 내용 | 근거 |
|---|---|---|---|
| **D-1** | 3.6 | `87.7% recovered the same 45° bin` → **정확히 같은 격자 칸** 263/300, 나머지 37은 `(32°,0°)` | resample 원자료 집계. 45° bin 은 300/300 동일이라 87.7% 가 아님 |
| **E-1** | 3.6 | `closest grid competitor −1.52 → neighboring cells weakly determined` | −1.52 는 이웃 칸이 아니라 **다른 γ 조합**(`γGB`)이고 파라미터는 `(2,+24)` 동일. 주장이 반대였음 |
| **C-1** | 3.5 | R+C 의 `Δλ` 가 자유 파라미터가 아니라 **아형별 문헌값 3개 고정** | `s8_loo_train_test.DELTA_LAMBDA_BY_FAMILY`. 본문 100%/41% 는 held-out loss 최선 anchor 값으로 정확하나 미공개였음 |
| **F-1** | 3.7 | deutan 심리물리 단독 argmin `(6,−42)` → **`(16,−44)`** | §3.6 의 `dropping the RDM atom returns (16,−44)` 와 모순이었음 |
| **F-2** | 3.7 | `ΔL=+0.01, 3/7` 은 심리물리 단독 fit 이 아니라 **선택 파라미터 고정 평가** | `loo7-fixedparam.json` |
| **B** | 3.8 | `disperse along the β_c axis` → 방향 반전 | β_c IQR 2° (−42:118, −44:84), β_s IQR 8° 이며 0–14° **균일**. L133 의 `IQR (8,2)` 와 모순이었음 |
| **C** | 3.8 | `sign stability under SRM not verified` → **검증됐고 음성** | SRM modal argmin `(32,0)` 171/300, β_c>0 17.3% / <0 25.7%. Results·Supplementary §S18 양쪽 수정 |
| **E** | 3.8 | `consistently returns β_c > 0` | 37/300 은 정확히 0 |
| **H** | 3.8 | `Parameter recovery fails across 6 checks` | 6 개 중 recovery 는 2 개 |
| **J** | 3.8 | `recovered β_c deviates by 4.7°` — **deutan 만** | protan 은 26.4°. 불확실성 대비: deutan β_c 42° > 26°(초과), protan 24° = 24°(동률) |
| **F** | 3.9 | Fig 7 캡션이 심리물리를 `\cref{fig:filter_eval}` 로 보냄 | Fig 8 에 심리물리 패널 없음 |
| — | 3.9 | 두 필터가 **8개 중 6개 hue 에서 같은 방향**, r=+0.66 | δθ 프로파일 직접 계산. `differ in direction` 이 오해를 부름 |
| **G** | 3.10 | Fig 8 캡션 과일반화 | `gray bars n=7` 이 C/F 에 거짓(`hc_sd=NaN`), chance 점선 A/D 만, 검정 단측 미표기 |

## 🔴 A — exp2 기하 run-count 불일치 (해결)

`exp2_convergent.py` 확인: `window`/`optimal` 4 run, `nofilter` 6 run(`:215`), HC 6 run(`:212`).
`nofilter_n4`(`:166-169`)는 계산돼 있었으나 **미사용**, RDM 은 n4 변형 자체가 없었음.
Supplementary L821 은 `For every neural index … subsampled to four` 라고 **반대로** 진술.

**조치**: `exp2_runmatched_geometry.py` 신설 — $\binom{6}{4}=15$ 부분집합 전수, 각 부분집합마다
HC 평균 재구성 + SRM 재적합 + nofilter 재구성, 필터 조건은 불변(원래 4 run). SLURM 165262
(node1 제출 → node2 실행, `mpirun -np 1`). 산출 `exp2_runmatched_geometry_sub-0{8,9}_matched.json`.

| | 발표값 | run-matched |
|---|---|---|
| deutan V2 disparity | HC .49 / .72 / .84 / .77 | HC **.44** / **.68** / **.87** / .77 |
| deutan V2 RDM | HCself .50 / .57 / .15 / **−.13** | **.59** / **.42** / .16 / **+.05** |
| protan V1 disparity | HC .45 / .76 / .63 / .62 | HC **.43** / **.70** / **.66** / **.63** |
| protan V1 RDM | HCself .66 / .25 / .49 / .30 | .66 / **.33** / **.38** / **.26** |

순서는 네 지표 모두 보존. 두 과장이 제거됨 — deutan 개인화의 RDM 반상관(−.13→+.05),
protan 개인화의 RDM 개선(+.05 → **−.07**, 즉 개선이 아니라 악화). 본문의 원 주장
`not specific to the individualized filter` 는 오히려 강화됨.

`generate_fig8.py:189` 가 미정합 JSON 을 읽고 있어 **그림도 교체**. 재생성 앵커가 본문과 일치.
Supplementary §S19 는 거짓 진술을 삭제하고 두 지표군의 처리를 구분해 재작성.

## ❌ 철회 — A-2

`3.10` 이 protan V1/V2 회복(.406/.375)을 누락한다는 지적을 **철회**. Methods 사전지정 규칙상
V1–V3 는 HC 자신이 순열 귀무를 넘지 못하므로(§3.2: V1 p=.164, V2 p=.424) 그곳의 CVD 변화는
해석 대상이 아니다. 대신 **hV4 명시 + 나머지 ROI 가 해석 대상이 아닌 이유**를 본문에 추가.

## 최종 점검 결과

- 교체 전 수치 잔존: **0** (`0.72→`, `0.57→`, `HC 0.49`, `87.7`, `disperse along`, `3/8`, `n=6 HC`, `p=0.008` 전부 소거)
- `\S S<n>` 참조 17건 → 대상 절 전수 확인, missing **0**
- Results·Discussion 산문 세미콜론 **0**. 잔여 5건은 Fig 4·6 캡션의 범례 나열형과 괄호 안 참조 구분자
- Abstract 는 개정 결과와 정합 (4쌍 임계값, 방향 불일치, HC 미도달 모두 유지)
- 부수 수확: `fidaner2005` 의 `note` 필드가 apacite 에서 컴파일을 깨뜨림(로컬 PDF 경로) → 제거.
  `main.bbl` 을 재생성한 적이 없어 잠복해 있었음

**최종 빌드**: pdflatex → bibtex → pdflatex ×2, exit 0, fatal 0, undefined 0, multiply-defined 0, 89 pages.

## 남은 항목

| 항목 | 상태 |
|---|---|
| Fig 4·6 캡션 문체 (범례 세미콜론, 결과 서술 포함 여부) | 미착수 — Fig 2·7·8 과 같은 기준 적용 필요 |
| `docs/PAPER/repro/` 의 `.npy` 커밋 판단 | `perm_n7_null_*.npy` 4 개 신규. 프로젝트 규칙상 `*.npy` 스테이징 차단 대상이나 기존 `perm_definitive_hv4_null.npy` 는 커밋돼 있음 |
| `exp2_runmatched_geometry.py` 리포 반영 | 현재 서버에만 존재. `analysis/future_phase3_behavioral_analysis/exp2_neural/scripts/` 로 가져와야 재현 가능 |
