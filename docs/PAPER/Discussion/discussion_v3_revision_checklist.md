# discussion_v3.tex — BLUF / NEGA revision checklist

> Target: `discussion_v3.tex` (2026-08-05 검토, P7 이후 재작성).
>
> 진행 방식: 문단별 수정안 제안 → 확인·피드백 → 개선 → 수락 후 `.tex` 적용 → **해결된 문단 항목은 이 파일에서 삭제**.
>
> 기준: (1) 두괄식 — 각 문단은 핵심 결과·주장·해석으로 시작. (2) 부정 프레이밍 최소화 — null은 효과크기·불확실성·재현성으로 보고. (3) 문장은 짧게, 삽입구 최소, 콜론·세미콜론 최소, academic vocabulary와 rigorous verbs.

---

## 0. 잔여 구간(P7–P13) 전역 스캔

| 문단 | 줄 | 어수 | em-dash | 콜론 | 세미콜론 | BLUF | NEGA |
|---|---|---|---|---|---|---|---|
| P7 Machado class | L31 | 112 | 2 | 1 | 0 | **위반** | 5 |
| P8 Filter evaluation | L34 | 134 | 0 | 0 | 0 | **위반** | 6 |
| P9 Hierarchical level | L36 | 124 | 0 | 0 | 0 | **위반** | 3 |
| P10 N=2 scope | L38 | 45 | 0 | 0 | 1 | **위반** | 1 |
| P11 Limitations | L41 | 324 | 4 | 0 | 1 | 통과 | 6 |
| P12 Conclusion ¶1 | L44 | 135 | 1 | 1 | 0 | **위반** | 2 |
| P13 Conclusion ¶2 | L45 | 55 | 0 | 0 | 0 | **위반** | 2 |

BLUF 위반 6/7. 부정 표현 25건. 콜론 2건(L31, L44), em-dash 삽입구 7개(L31 ×1, L41 ×3, L44 ×1의 마크 수 기준 7).

**해결 완료**: P1 (L15), P2 (L18), P3 (L21), P4 (L23), P5 (L25–27), P6 (L29), P7 (L31), P8 (L34), P9 (L36), P10 (삭제) — 2026-08-05 적용. P11 (L39–43), P12 (L46), P13 (L48) — 2026-08-06 적용. **전 문단 해결 완료.**

- P12/P13: P12 첫 문장을 절차 서술에서 파이프라인 귀결(`We derived a stimulus-space color correction ...`)로 교체, 콜론·em-dash 제거. 이중부정(`need not present as ... It can instead be ...`)을 긍정 대비(`a hue rotation about two axes ... rather than a uniform attenuation`)로 통합. `individually patterned, multidimensional` → 모델 자체 서술 + `The fitted parameters differed between the two participants.` `structured enough to invert`/`admits an explicit inverse` → `the model inverted to an exact stimulus-space pre-image at all eight hues`(P1·P4 기존 표현). 마지막 문장 병렬 구조 교정. 135 → 115어. P13은 `However` 개시 제거, `metrics` → `measures`(초록 `main.tex:71`·P9와 통일), 마지막 두 절 병합. 55 → 53어.
- **사용자 결정 (2026-08-06)**: `departed from` 유지(초록과 일치, 동반 수정 불요). `at a different cortical area in each` 유지 — §8-1/§8-5 반영 여부와 무관하게 현행 문안 확정.

- P11: 324 → 279어, 단일 문단 → 표본 / 추정의 강건성 / 범위·목적 3문단. 리드 문장 `Five considerations bound the proof-of-concept scope` 삭제(내용 없는 예고 문장). `First`–`Fifth` 서수 제거. P6와 중복된 2문장(β_c 부호 회수 가능성, 아형 간 차이 교란) 삭제. HC 코호트 항목을 CVD N=2 바로 뒤로 이동해 표본 문단 통합. §8-1(deutan V2 LOSO 감쇠) 신규 항목 채택. 마지막 항목을 한계 진술에서 **지표 불일치 → 공통 표상공간 통합** 제안으로 전환(P9의 `refined neural endpoint` 회수). 어휘: `gauge`→`reported descriptively`(methods_v2.tex:277 용례), `awaits`(2회)→`requires`, `magnitude anchor`→`a reference for the magnitude ... rather than as a significance test`, `arbitrate`/`decisive`/`gaps ... close` 제거. em-dash 4·세미콜론 1 → 0.
- **P11 사실 정정 (2026-08-06)**: 원문의 `The LOCO atom is defined in a forward-encoding channel space at hV4 --- a smaller voxel set on a different representational basis than the RDM`는 부정확. `methods_v2.tex:241–257` 기준 실제 차이는 공간이 아니라 **측정량과 ROI** — $L_{\rm LOCO}$ = hV4의 8원소 per-hue vulnerability profile MSE, $L_{\rm RDM}$ = deutan V2 / protan V1에서 SRM 정렬 패턴 $8\times8$ 상관거리 행렬의 28원소 상삼각 벡터 코사인 비유사도. 최종 문안은 이 정의로 서술. 최종 어수 279 → 312(구체화에 따른 증가).

- P9/P10: P10 삭제 후 그 취지(subtype 내 재현 요건)를 P9 마지막 문장으로 흡수 → Filter evaluation 소절이 2문단으로 축소. BLUF를 초록 `differed across participants and measures`(`main.tex:71`)에 정렬. §8-4 정확성 수정 반영(protan 회복의 `comparably` → SRM/RDM 지표별 분리, deutan 기하 비교 추가). 위계 문장에서 `readout index` → `lie at`. `primary-endpoint`(논문 내 유일 사용, 사전 지정 근거 없음) 소멸. Results 동반 수정 3건: `results_v4.tex` 방향 표현·`comparable`·protan chance 구절.
- P8: 8AFC 결과 추가(§8-6 해소). 배치 필터 deviant 서술 중복 제거. 마지막 문장을 `These neural readouts remain inconclusive in a two-case sample …`로 교체(재현 요건 3중 등장 해소를 위해 중간 문장은 `appeared in the protan participant only.`로 축약). P1과 중복된 `immediate next test` 삭제.
- P7: arc-compression 문장 삭제(§8-3 A안 확정). 수치 4건을 Results로 반환(구체성 수준 조정). `no value of` / `cannot represent` → `along the confusion axis alone` / `omits`. `orthogonal` 회피(§8-7). 112 → 90어.

---

## 0-A. 전역 어휘 정책 — 비유·비학술 표현 금지 목록

원문과 1차 수정 제안 양쪽에 걸린 표현. **대체안은 전 문단 공통 적용.**

| 금지 표현 | 위치 | 대체 |
|---|---|---|
| `ceases to be decodable` | 1차 제안 (철회) | `falls to chance` |
| `most vulnerable` | L31 | `where the interpolation deficit is largest` |
| `rules it out` | L31 | `precludes` |
| `implausibly implying` | L31 | `implying ..., which is inconsistent with` |
| `moved in opposite directions` | L36 | `reversed in direction between participants` |
| `move together` / `need not change together` | L36 | `covary` / `can vary independently` |
| `arbitrate population-level distortion patterns` | L41 | `resolve population-level distortion patterns` |
| `gaps that denser stimulus sampling would close` | L41 | `denser sampling along these axes would extend the domain of validity` |
| `the decisive follow-up experiment` | L41 | `the critical follow-up experiment` |
| `structured enough to invert` | L44 | `a distortion that admits an explicit inverse` |

동사 정책: `show` 남용 대신 `localize`, `resolve`, `recover`, `constrain`, `preclude`, `replicate`, `converge on`, `admit` 사용.

---


## 8. 정확성·주장 범위 재점검 (표현 수정과 별개)

### 8-1. deutan V2 disparity의 LOSO 감쇠 — **부분 해결 (2026-08-06)**

Results `results_v4.tex:66,68,80`은 deutan V2를 common-space $p = 0.040$이나 대칭 LOSO 대조에서 $p = 0.116$ 경향으로 기술한다. protan V1은 LOSO에서도 유지된다($p = 0.045$).

**조치**: P11 Limitations 2문단에 신규 항목으로 명시 완료. P2(L18)·P12(L46)의 국재화 서술은 **사용자 결정(2026-08-06)으로 현행 유지** — Limitations 명시로 충분하다고 판단.

### 8-2. specificity 표현 보존

P8·P9의 `not specific to the individualized filter`는 프로젝트 정책 준수 문구다. 수정 과정에서 소실되지 않도록 확인.

### 8-3. arc-compression 문장과 Appendix~A — **A안 확정 (2026-08-05)**

**결정**: 제거. **2026-08-06 완료** — Discussion 문장 삭제, `Results/appendix_alternative_models.tex` §A.2 후반부(retinal-shift 압축) 삭제. 첫 절(2성분 전단사) 유지 + pre-image가 Section~filter의 필터임을 명시하는 문장 1개 추가.

**근거**: 압축 조건은 $1 + (2-g)\,\delta\theta'_{\rm Mach} \le 0$. 해당 구간에서 $\delta\theta'_{\rm Mach} \approx -1$ 이므로 $g \le 1$ 에서만 성립한다. 적합값 $g = 3.0$ / $2.95$ 에서 $(2-g) \approx -0.95$ 이고 그 구간의 미분은 $1.95$ 로 확장이다. §A.2는 클래스의 구조적 성질이 아니라 적합이 선택하지 않는 $g = 1$ 구성원의 성질을 기술한다. B안(적합 gain 재계산)에서 보고된 임계 $g = 2.13 / 2.04$ 는 $|\delta\theta'_{\rm Mach}| \approx 8$ 을 요구하며 이는 무채색점 근방의 `arctan2` 조건수 인공물이다. R+C 배제는 §A.1 + §A.3 + Results §rc_insufficient로 유지된다.

**원 문제 기록 (참고용)**

P7의 `it even compresses three distinct displayed hues into a narrow arc, leaving no exact pre-image (Appendix~A)` 는 네 가지 문제를 안는다.

1. **범위 초과.** Appendix §A.2는 주장을 `the $g = 1$ retinal-only case`로 명시 제한하나, Discussion은 `even when scaled by a cortical gain`으로 일반화한다.
2. **폐기된 앵커.** §A.2의 $26^\circ/96^\circ$ 수치는 $\Delta\lambda = 13.5$ nm에서만 재현된다. live protan R+C 적합은 $\Delta\lambda = 3.0$ nm이다(`PIPELINE_2_CLOSURE.md`). $\Delta\lambda$는 본문 어디에도 없다.
3. **좌표계 불일치.** §A.2는 Stockman opponent-hue 좌표에서 가역성을 평가하나, Methods §5는 pre-image를 nominal CIELab $\theta$에서 정의한다. 두 규약이 반대 결론을 준다.
4. **protan 특이성 미성립.** 붕괴는 심도 구동이며 deutan이 동등하거나 더 크다.

**선택지**: (A) Discussion 문장과 §A.2 역산 문단을 모두 제거하고 자유도 논거만 유지 — 자유도 논거는 좌표계·$g$·심도와 무관하며 Results §rc_insufficient에 이미 확립되어 있으므로 R+C 배제는 유지된다. (B) §A.2를 Methods 규약과 live 적합값으로 재계산하여 참가자별 실패 색 수로 재진술. **단 B는 수치 조건 점검 통과가 전제** — protan $\Delta\lambda = 3.0$, $g = 2.95$에서 비단조 구간의 opponent 크기가 원 평균의 0.95%로 `arctan2`가 ill-conditioned이다. (C) 현행 유지는 불가.

어느 쪽이든 **현행 Discussion 문장은 제거 대상**이다.

미해결 부수 사항: deutan $\Delta\lambda$가 조사 결과 8.0 nm, `PIPELINE_2_CLOSURE.md` 6.5 nm로 불일치. B 채택 시 선행 확정 필요.

### 8-5. 정렬 인공물 소견과 단일 ROI 국재화 주장

프로젝트 메모(2026-08-05, `project_alignment_manufactures_correspondence.md`)는 투영을 동결하면 진짜 색 대응이 V1/V2/V3에 남고 hV4에는 없으며, protan V1은 $p = .079$ 경향으로 약화되고 **deutan V2는 방향이 역전($p = .882$)** 된다고 기록한다. 이는 현재 P1·P2·P12에 적용된 `localized to a different area in each` 주장을 약화시킨다.

**결정 필요**: (a) 이 소견을 Limitations 항목으로 명시, (b) P2의 국재화 서술을 완화, (c) 별도 검증 후 결정.

### 8-6. P8의 8AFC 결과 누락

§2 참조. 개인화 필터 우위의 두 번째 독립 행동 지표가 Discussion에 반영되어 있지 않다.

### 8-7. `orthogonal to the confusion axis` 부정확 — **수정 완료 (2026-08-06)**

2성분 모델의 두 번째 축은 S-cone 축($90^\circ$)이고 $\theta_{\rm conf}$ 는 deutan $150^\circ$ / protan $16^\circ$ 다. 각각 $60^\circ$, $74^\circ$ 떨어져 있어 직교가 아니다.

**조치**: `results_v4.tex`를 Discussion P7과 동일한 `displacement away from that axis` 표현으로 통일. `No value of $g$` 구문도 함께 제거(§0-A 어휘 정책).

### 8-8. `appendix_alternative_models.tex` §A.3 내부 오류 — **수정 완료 (2026-08-06)**

§A.3은 cortical gain이 생성하지 못하는 항으로 $\beta_c \cos(\theta - \theta_{\rm conf})$ 를 지목했다. 그러나 $\beta_c$ 는 confusion 축 성분이며 R+C가 작용할 수 있는 바로 그 방향이다. 대상을 $\beta_s \cos(\theta - 90^\circ)$(S-cone 축)로 교정하고, 이격각($\theta_{\rm conf}$ 기준 deutan $60^\circ$ / protan $74^\circ$)을 명시했다. 근거 없는 LOCO 경험 주장(`no value of $g$ matches the observed hV4 LOCO vulnerability pattern`)은 삭제 — A.1의 적합 결과와 중복.

**잔여 쟁점 — 종결 (2026-08-06, (a)안 적용)**. 세 주장의 근거 강도가 달라 분리했다.

1. *R+C는 confusion 축을 벗어난 변위를 표현할 수 없다* — **성립**(클래스의 대수적 성질, 적합 기준 무관).
2. *데이터가 그 축을 벗어난 변위를 요구한다* — **성립하되 근거는 $\hat\beta_s$가 아니라 LOCO per-hue vulnerability**. 결손이 S-cone 중간색(blue/purple/magenta)에 집중된다는 관찰은 $\hat\beta_s$ 식별가능성과 독립이며, 원고가 P1·P7에서 이미 쓰는 논리다.
3. *이 결손이 A.1 실패의 `structural cause`다* — **불성립**. A.1의 실패는 deutan $g \to 3.0$ 경계 포화와 protan held-out 열세인데, 경계 포화는 confusion 축 위의 **진폭·부호** 문제다. 빠진 S-cone 성분이 포화를 일으켰다는 논증은 없다. 진폭 제약이 더 단순한 설명일 가능성은 $|\delta\theta_{\rm Mach}|$ 크기가 원고에 부재하여(§8-3 note 2: deutan $\Delta\lambda$ 8.0 대 6.5 nm 불일치) 확인 불가.

**조치**: 주장 1·2 유지, 3 제거. A.3 마지막 문장을 LOCO 근거 + 클래스 성질 진술로 교체. `results_v4.tex`의 동일 인과 주장(`The structural cause is a degree-of-freedom deficit.`)도 `The R+C family also carries a degree-of-freedom restriction.`로 완화하여 A.1의 경험적 실패와 병렬 배치. R+C 배제는 A.1 + Results §rc_insufficient가 지탱하므로 결론 불변. Discussion P7의 `Fitting the class registered this misspecification.`은 `registered`가 충분히 약하고 뒤 문장이 실제 실패 내용을 제시하므로 **현행 유지**.

### 8-9. `methods_v2.tex:134` dangling 참조 — **TODO 문서화 완료 (2026-08-06), 본문 작성 대기**

작업 지시서: `Supplementary/TODO_decoder_comparison.md`. 참조 대상 절 자체가 부재하므로 신규 작성이 필요하며, 수치는 `analysis/phase3_decoder_comparing/`에서 재산출해야 한다.

**원 진단**

`Alternative decoders evaluated during model selection are described in Appendix~A.` 그러나 Appendix A(`appendix_alternative_models.tex`)에는 디코더 내용이 없고, PopVec / GaussML / RidgeReg 등 대체 디코더를 기술한 절이 논문 전체에 존재하지 않는다(`supplementary_content.tex`, `Supplementary/` 전수 검색 0건). 제출 전 처리 필요.
