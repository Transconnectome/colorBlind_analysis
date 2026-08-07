# Revision Report — `Discussion/discussion_v3.tex` — 2026-08-06

Scope: 파일 전체
Rules: `~/.claude/writing/academic_writing_rules.md` (Parts II–V)
Pre-draft reference: `Discussion/discussion_structure_v3.md` (§2 갱신 2026-08-06)

> **Round 1** — 14문단 대상. Fatal 4 / Serious 8 / Minor 8 검출. 아래 §1–§7이 Round 1 기록입니다.
> **Round 2** — 17문단 대상 재실행. 결과는 문서 말미 §8 참조.

---

---

## 1. Reverse outline

### (no subsection) — Executive summary
- **L15 (¶1)**: 두 CVD 참가자의 피질 색 표상에서 개인별 필터를 역산했고, 그 표상은 균일 감쇠가 아닌 구조적 기하 왜곡을 담고 있었으며, 2인 평가에서 행동 역치는 정상화되었으나 피질 보간 효과는 참가자마다 달랐다.

### A geometric distortion of cortical color representation
- **L18 (¶2)**: 결손은 참가자마다 다른 영역에 국재한 구조적 기하 왜곡이며, RDM(구조)과 LOCO(기능적 귀결)가 이를 각각 드러낸다.

### A neurally grounded, individualizable correction filter
- **L21 (¶3)**: 적합된 2성분 모델의 역함수가 교정 필터를 정의하며, 평균 회전량은 deutan 26.3°, protan 16.2°다.
- **L23 (¶4)**: 이 필터는 망막 모델이 아니라 개인의 피질 색 표상에서 도출된 최초 사례이며, 선행 피질 인코딩 역산 연구는 색의 배열이 아니라 반응 크기를 조작했다.
- **L25–27 (¶5)**: 신경 항은 적합에 세 가지 기여를 했다(행동만으로 못 찾은 회전 회수, 기존 해의 강화, argmin 산포 축소).
- **L29 (¶6)**: **[2문장 필요]** 두 적합 왜곡의 부호가 갈리고 그 부호는 HC 재표집에 안정적이나 기저 공간에 의존하며, 축별 크기는 식별 불가이고 아형/개인 차이는 교란되어 있다.
- **L31 (¶7)**: 망막+이득 대안은 자유도가 하나뿐이라 confusion 축 밖 변위를 표현하지 못하고, 적합에서 $g>2$로 포화하여 실패했다.

### Filter evaluation
- **L34 (¶8)**: **[2문장 필요]** 개인화 필터는 모든 행동 쌍을 대조군 범위에 두었고 배치 필터는 그러지 못했으나, 신경 판독치는 참가자 간에 갈렸고 2사례로는 결론이 나지 않는다.
- **L36 (¶9)**: 필터 효과는 참가자·지표별로 달랐고, 기하 변화는 각 참가자에서 보간과 반대 방향이었으며, 두 판독치는 위계가 달라 독립적으로 변할 수 있다.

### Limitations
- **L39 (¶10)**: CVD 표본이 $N=2$이고 HC 대조군도 7명이라 모집단 수준 주장과 유의성 검정이 불가하다.
- **L41 (¶11)**: 보고된 추정치 두 개(deutan V2 disparity, 축별 $\hat\beta$)가 분석 선택에 의존한다.
- **L43 (¶12)**: **[2문장 필요]** 자극이 단일 등휘도·등채도 궤적에 한정되어 필터 적용 범위가 좁고, 두 신경 손실항이 서로 다른 양을 재기 때문에 공통 표상으로 통합해야 단일 목적함수가 가능하다.

### Conclusion
- **L46 (¶13)**: 각 참가자 자신의 피질 표상에 적합한 모델을 역산해 자극공간 교정을 도출했고, 결손은 2축 hue 회전 형태였으며 교정은 개인별 변환이다.
- **L48 (¶14)**: 후속 대규모·체계적 연구가 CVD 피질 왜곡을 정량화하고 개인화 필터 클래스를 산출할 수 있으며, 일반화 가능한 개선 여부는 그 연구가 확립할 문제다.

### Drift vs intended outline (`discussion_structure_v3.md` §2)

| 계획 | 현행 | 판정 |
|---|---|---|
| ¶4 individualization / ¶5 caveat bounding ¶4 (**별도 2문단**) | L29 **한 문단으로 병합** | **drift** — §7 위반과 동일 지점 |
| ¶6 = C3 performance, **Phase 3 forward-looking TODO** | `Filter evaluation` 소절 = **실제 수행된 2인 평가** | drift 아님. Phase 3 데이터가 확보되어 상위 갱신됨 → **구조 문서가 stale** |
| ¶7 Limitations "Four considerations" | 6개 항목 3문단 | 정당한 확장 |
| ¶8 Synthesis + broader impact | Conclusion 2문단 | 대응 |

> **조치 권고**: `discussion_structure_v3.md`가 2026-06-08판이라 현행 원고보다 두 세대 뒤처져 있습니다. 다음 revise 사이클 전에 갱신하지 않으면 outline drift 판정 기준이 계속 무효입니다.

### Subsection topic rollup

- ✓ `A geometric distortion of cortical color representation` — topic: "결손의 정체 = 기하 왜곡"
- **[SPLIT?] `A neurally grounded, individualizable correction filter`** — topic1: 필터 도출과 개인성 (¶3–¶6) / topic2: 망막+이득 대안의 배제 (¶7) → 후자는 모델 클래스 비교로 별도 story. 소제목이 두 topic을 묶고 있음
- ✓ `Filter evaluation` — topic: "필터가 작동했는가"
- ✓ `Limitations`
- ✓ `Conclusion`

---

## 1.5 Long sentences (§2)

**none over threshold.** 45어 초과·em-dash 2개 이상·세미콜론 포함 문장 **0건**. 최장 문장 약 36어(L15). 이번 세션의 §2 작업이 전 문단에 반영되어 있습니다.

---

## 2. §19 Vocabulary — **종결 (2026-08-06)**

전 항목 해소. Tier D 0건, §5 filler 0건.

- L15 `In a first two-person evaluation` → `In a two-person evaluation` **적용 완료**
- L18 `more robust sources` → `between-observer variability in hue scaling is 3.4 times the within-observer variability` **사용자 재작성 완료** (수치 동반으로 §19C 충족)
- L23 `To our knowledge ... the first` — 프로젝트 `CLAUDE.md` 명시 승인 형태, **유지 확정**
- 잔여 경미 2건(L48 `improvement` 미조작화, L15·L48 `larger` 무수치)은 Priority summary Minor로만 보유

---

## 3. §20 Citations

총 6개 인용 지점, 5+ 스택 **0건** (최대 3).

### General-claim ↔ specific-cite mismatches

- **L18 RDM 정의** — `kriegeskorte2019` **삭제 완료 (2026-08-06)**. `kriegeskorte2008`(RSA 원전) 단독으로 method-origin 인용 성립.

- **L18 일반 특성화** — `This pattern aligns with prior characterizations of CVD as a multidimensional deformation of color space rather than a uniform attenuation \cite{boehm2014, ohkoba2021, emery2021}`

  **리뷰 존재 여부 조사 (2026-08-06, Consensus 검색)**

  | 후보 | 유형 | 판정 |
  |---|---|---|
  | Bosten 2019, *The known unknowns of anomalous trichromacy* (Curr Opin Behav Sci) | review | **주장의 후반부만 지지** — cone 분광민감도와 색변별의 상관이 예상보다 약함, postreceptoral 보상. 즉 "uniform attenuation이 아니다"는 뒷받침하나 "multidimensional deformation of color space"는 명시하지 않음. **`bosten2019`로 이미 bib에 존재하며 Introduction·Results에서 사용 중** |
  | Emery & Webster 2019, *Individual differences and their implications for color perception* (Curr Opin Behav Sci) | review | 개인차 일반론. 기하 왜곡 프레이밍 미지원. bib 미등록 |
  | Simunovic 2010 (Eye), Yang 2024 (Front Neurosci) | review | 임상·유전·치료 중심. 색공간 기하 미지원 |

  **결론: 기하 왜곡 프레이밍을 직접 주장하는 리뷰는 없음.** 이 문장의 명제는 선행 primary들에서 저자가 종합한 것입니다.

  §20 표의 anti-pattern은 "일반 진술 + **단일** primary"이며 현행은 primary 3편입니다. 또한 `prior characterizations`라는 표현이 특정 선행 연구를 지목하므로 primary가 오히려 적합합니다. **규칙 위반 아님 — 변경 불요.**

  보강을 원할 경우 `bosten2019`를 추가해 `rather than a uniform attenuation` 절을 리뷰가 담당하게 할 수 있습니다(비용 0, bib·본문에 이미 존재). 다만 4-key 스택이 되고 리뷰가 기하 주장을 지지하지 않으므로 **권고하지 않습니다.**

### Specific-claim ↔ review-cite mismatches (0)

✓ `brouwer2009`(hV4 보간, 특정 경험 주장→primary), `emery2021`(개인차, →primary), `bashivan2019`/`shinkle2025`(선행 역산 특성화, →primary) 모두 정합.

### Method origin (0 issue)

✓ `crawford1998`(단일사례 통계), `kriegeskorte2008`(RSA) 모두 원전.

### Density warnings

✓ 없음.

---

## 4. §26 Checklist

### Reverse outline
- [✓] 문단당 한 문장 요약이 순서대로 서사를 구성
- [✗] §1 Step 5 outline 일치 — 계획 ¶4/¶5가 L29로 병합(drift). 단 구조 문서 자체가 stale(§1 표 참조)
- [✗] **두 문장 필요 문단 3건: L29, L34, L43** → §7 분할 대상

### Claims
- [N/A] title+abstract에서 한 문장 기여 추출 — 검토 범위 밖 (Discussion 단독). 다만 L15가 그 역할을 수행하며 첫 문장에서 회수 가능 ✓
- [△] 모든 수치 Δ에 baseline+metric+dataset — L34의 `$0.23 \to 0.31$` / `$0.14 \to 0.06$`는 지표(adjacent accuracy)와 baseline은 있으나 chance(3/8)·HC 기준이 없음. 이번 세션에서 chance를 `results_v4.tex:222`로 이관한 결정에 따른 것. **정책적 통과**, 단 아래 §5 naive-reader 항목과 연계 판단 필요
- [△] `first/only/no X` — 2건, 프로젝트 정책 승인분 1건 + 축약 권고 1건 (§2 참조)
- [△] untestable verb — 1건 경미 (L48)
- [✗] vague adjective 조작화 — **L18 `more robust sources` 실패**
- [✓] self-praise 없음

### Citations
- [△] general → review — L18 3-primary 스택 (low priority)
- [✓] specific → primary
- [✓] method origin → original
- [✓] 5+ 스택 없음
- [✗] **인용이 주장을 뒷받침하는가** — `kriegeskorte2019`

### Structure
- [✗] **문단당 한 역할 — L29, L34, L43 위반**
- [✓] 첫 문장 = topic sentence (14/14)
- [✗] **대명사 명확 — L36 `In the deutan participant both filters moved it away`**: `it`의 선행사는 두 문장 전 `the early-visual geometry`인데, 직전 문장이 `shifted in the direction opposite to interpolation`으로 끝나 `interpolation`을 집을 수 있음. 명사 반복 권고
- [✗] **용어 일관성 (§4)** — 동일 대상에 4개 변형:
  | 표현 | 위치 |
  |---|---|
  | `healthy-control geometry` | L15 |
  | `control range` | L15, L34 |
  | `control cohort` | L18 |
  | `control reference` | L34, L46 |
  | `HC reference` | L29(×2), L36(×2), L39 |
  L18에서 `healthy-control (HC)`를 정의하므로 **정의 이후 전 구간 `HC reference`로 통일** 권고. `control range`는 행동 역치의 정상 범위를 뜻해 별개 개념일 수 있으므로 분리 판단 필요
- [✓] observation / interpretation / implication 분리

### Section-by-section (§25 Discussion)
- [✗] **gap 회수** — §25 첫 항목 `How the gap was filled. Tie back to §22.` Discussion 어디에도 Introduction의 gap을 명시 회수하는 문장이 없습니다. L15는 수행 내용으로 곧장 시작
- [✓] 선행연구 맥락 배치 (L18, L23)
- [✓] 한계 진술 (L39–L43)
- [✓] field impact로 종결 (L48)
- [✓] Discussion에 신규 결과 없음 — 모든 수치가 Results/Supplementary 참조를 동반

### Final pass
- [✓] filler 없음
- [✓] 부정형 → 긍정 등가 (잔존 부정형은 정책 필수 문구 `not specific to the individualized filter` 및 필수 범위 진술)
- [△] nominalization — `Establishing an advantage ... is the immediate next test.`(L15), `Establishing the filter's neural effect requires ...`(L34). 동일 분사 주어가 두 번 문두에 옴
- [✓] 능동태

---

## 5. Naive-reader check (Phase 5.5)

> 대상: L15 executive summary 문단 단독. 도메인 지식 0 독자 근사. **본문 중간 문단이므로 앞 절에서 정의된 용어를 모르는 것은 예상된 위양성**입니다. 아래는 위양성을 걸러낸 뒤 남은 항목입니다.

### 위양성으로 처리 (앞 절에서 정의됨)
`CVD`, `deutan`/`protan`, `ROI`, `the deployed accessibility filter`, `adjacent-hue accuracy`, `hue-discrimination thresholds`, `control range` — Abstract·Introduction·Methods·Results에서 도입됩니다.

### 처리 결과 (2026-08-06)

| # | 이슈 | 결정 |
|---|---|---|
| 1 | `exact pre-image`를 구성적 성질→결과로 서술 | **적용** — gamut 등 구체 서술 대신 "색별 단일 보정색 배정"으로 재프레이밍 (L15·L21·L46) |
| 2 | 개회 주장 vs 적합 입력 불일치 | **적용** — 첫 두 문장에서 신경·행동 양쪽 입력 명시. `one deutan and one protan` 동격은 사용자 지시로 제거 |
| 3 | 두 축 순환 정의 | **적용** — `Both axes were fixed before fitting` + confusion-line direction / S-cone modulation으로 실체 정의 |
| 4 | $n=2$ 반대 방향 결과 | **현행 유지** (사용자 판단: 현 서술로 의미 전달 충분) |
| 5 | L15 마지막 문장 | **현행 유지** (사용자 판단) |

> 5를 유지함에 따라 §6의 재현 요건 5회 반복은 그대로 남습니다.

### 원 진단 (5건)

1. **`exact pre-image`가 결과인가 구성적 성질인가 — 가장 중요.**
   > "I cannot tell whether this is a nontrivial result … or a restatement that the model is invertible."

   **확인 결과 후자입니다.** `Results/appendix_alternative_models.tex` §A.2: *"The angular form of the 2-component model is **bijective by construction**: a stimulus-space pre-image exists for any target hue."* 그런데 Discussion은 이를 **세 곳에서 결과처럼 서술**합니다.
   - L15 `The fitted model inverted to an exact stimulus-space pre-image for all eight hues in both participants.`
   - L21 `Each participant's fitted two-component model admitted an exact inverse over all eight hues.`
   - L46 `the model inverted to an exact stimulus-space pre-image at all eight hues`

   §10(주장을 명시하라)·§12(과대주장 금지) 위반입니다. 구성상 보장되는 성질을 참가자별 성취처럼 읽히게 합니다. **비자명한 부분이 무엇인지 특정해야 합니다** — 예: pre-image가 디스플레이 gamut 안에 들어왔는가, 8색 모두에서 물리적으로 실현 가능했는가. 그 부분만 결과로 서술하고, 전단사성은 구성적 성질로 명시할 것.

2. **개회 주장과 적합 입력의 불일치.**
   > L15 첫 문장 `from the cortical color representation` vs 여섯 번째 문장 `from behavioral hue-discrimination thresholds and cortical representational geometry`

   헤드라인 신규성이 "피질 기반"인데 적합에 행동 데이터가 함께 들어갑니다. 다섯 문장 뒤에야 밝혀지므로 독자가 배신감을 느낍니다. 첫 문장에서 두 입력을 함께 밝히거나, `derived from` 대신 `grounded in`류로 강도를 조정할 것. **`CLAUDE.md`의 novelty 스코프 정의와도 직결되는 사안입니다.**

3. **confusion axis의 순환 정의.**
   > `The confusion axis is the classical direction of CVD color confusion.`

   용어를 그 용어로 정의합니다. §23(모든 변수는 first mention에 한 절 gloss) 위반. 실체적 정의 필요 — 예: 해당 아형에서 혼동되는 색쌍을 잇는 색공간 방향, Stockman & Sharpe cone fundamental에서 도출(`stockman2000`, Methods §twocomp에 이미 존재).

   같은 문제가 S-cone axis에도 있습니다: `the S-cone axis is where the interpolation deficit concentrated` — 설명 대상인 데이터로 모델 축을 정의하는 형태라 **순환 적합으로 읽힙니다.** S-cone 축은 $90^\circ$로 사전 정의된 축이라는 점을 명시하면 해소됩니다.

4. **$n=2$ 반대 방향 결과의 정보량.**
   > `the filter's effect varied by participant, with adjacent-hue accuracy increasing in the deutan and decreasing in the protan`

   1↑1↓ 분할은 잡음과 구분되지 않는데 ¶1은 이를 중립적 소견처럼 제시합니다. L36·L39·L41이 뒤에서 범위를 제한하지만, **가장 많이 읽히는 문단(§18)에 그 한정이 없습니다.**

5. **L15 마지막 문장의 내용 부재 + 앞 문장과의 긴장.**
   > `Establishing an advantage over the deployed filter in a larger sample is the immediate next test.`

   `a first two-person evaluation`에서 이미 추론되는 내용이고, 두 문장 앞에서 배치 필터 대비 우위를 보고한 직후에 "우위는 아직 확립되지 않았다"고 조용히 인정합니다. **삭제 시 손실 없음** — 아래 §6 중복 항목과 함께 처리 권고.

### 수치 부재에 대한 지적 — 정책 충돌로 판단

naive-reader는 ¶1에 수치가 전무하다고 강하게 지적했습니다. 이는 이번 세션의 "수치는 Results로 반환" 결정(P7 선례)과 충돌합니다. **다만 ¶1은 §18 기준 가장 높은 노출을 갖는 문단**이므로, 앵커 수치 2–3개(예: HC hV4 adjacent accuracy, 두 필터의 deviant pair 수)를 되살리는 절충을 검토할 가치가 있습니다. 나머지 문단은 현행 정책 유지.

---

## 6. 규칙 참조 항목 (§17 zig-zag)

**재현 요건 진술이 5회 반복됩니다.**

| 위치 | 문구 |
|---|---|
| L15 | `Establishing an advantage over the deployed filter in a larger sample is the immediate next test.` |
| L34 | `Establishing the filter's neural effect requires more participants or a systematically designed evaluation.` |
| L36 | `Replication in more individuals within each subtype, on a refined neural endpoint, is required to establish whether either pattern generalizes.` |
| L39 | `population-level claims ... require replication with more participants.` |
| L48 | `Larger and systematic studies can now quantify ...` |

L34·L36은 신경/일반화로 대상이 다르고 L39는 Limitations 고유, L48은 전망이므로 각각 근거가 있습니다. **L15가 가장 잉여**입니다(위 §5-5와 동일 결론). 삭제하면 4회로 줄고 `Establishing` 문두 중복도 해소됩니다.

**anomaloscope 초출 미정의.** L39 `grading their severity with an anomaloscope rather than the Ishihara plates used here` — `anomaloscope`는 **원고 전체에서 이 한 곳에만** 등장합니다(전수 검색 1건). §23 first-mention gloss 필요, 또는 Methods에 Ishihara 사용 근거와 함께 배치. 또한 이 절은 표본 크기 한계 문장 안에 **중증도 등급 도구라는 별개 한계**를 삽입하고 있어 §7 관점에서도 어색합니다.

---

## 6-A. 잔여 이슈 수정안 — **F1·F2·F3·S1·S2 적용 완료 (2026-08-06)**

> 사용자 지시: 필수(Fatal·Serious)만 적용. **M1·M4 미적용**, M2·M3는 변경 불요 확정.
>
> 적용 후 문단 수 14 → **17**. 아래 §1 reverse outline의 줄 번호는 **superseded** — 다음 `/revise-draft` 재실행 시 재생성 필요.
>
> | 신규 줄 | 문단 |
> |---|---|
> | L29 / L31 | F1 분할 (개인화 결과 / 식별가능성 한계) |
> | L36 / L38 / L40 | F2 재분배 (행동 / 신경 결과 / 신경 해석·범위) |
> | L47 / L49 | F3 분할 (자극 범위 / 손실항 통합) |
>
> 검증: `control range`·`control reference`·`control cohort` 잔여 **0건**(L15의 정의 지점 `healthy-control (HC)`만 유지), 대명사 `moved it` 잔여 **0건**.


### F1. L29 분할 — 개인화 결과 / 식별가능성 한계

구조 문서 §2가 **¶4(individualization) / ¶5(caveat bounding ¶4)** 로 계획한 지점입니다.

**¶4 (결과 + 그 해석)**

> The two fitted distortions diverge, with $\hat\beta_c = -42^\circ$ in the deutan participant against $+24^\circ$ in the protan participant. The sign of $\hat\beta_c$ remained stable when the HC reference set was resampled. Leaving out each of the seven HC reference participants in turn confined $\hat\beta_c$ to $[-46^\circ, -38^\circ]$ in the deutan participant and returned an identical argmin on every fold in the protan participant. The fitted signs record displacement at two different anchor directions in a shared hue frame, and the two confusion axes lie $134^\circ$ apart ($\theta_{\rm conf} = 150^\circ$ and $16^\circ$).

**¶5 (한계)**

> The per-axis magnitudes are not separately identifiable, with 0 of 6 recovery checks surviving FDR correction. What the fits recover is the sign of the dominant confusion-axis term. In the protan participant that sign is basis-dependent. The fit used an RDM loss computed in a PCA-reduced space, and computing the same loss in the SRM-aligned space moves the argmin (Supplementary~\S\ref{app:identifiability}). With one participant per subtype, individual and subtype differences remain confounded.

¶4가 "부호는 HC 재표집에 안정"이라 하고 ¶5가 "기저 교체에는 불안정"이라 하는 긴장은 **실제 상태 그대로**입니다. 분할이 이를 은폐하지 않고 드러냅니다.

### F2. L34–L36 재분배 — 행동 / 신경

L34가 행동·신경·범위 3역할을 담고, L36도 신경입니다. **L34의 신경 문장을 L36으로 옮겨 행동 1문단 + 신경 2문단**으로 재편합니다.

**¶8 (행동)** — L34에서 신경 3문장 삭제, 나머지 유지

> ... This behavioral advantage appeared in the protan participant only.

로 종결. (`Adjacent accuracy on hue interpolation ...` / `The representational geometry ...` / `These neural readouts remain inconclusive ...` / `Establishing the filter's neural effect ...` 4문장 이동·병합)

**¶9 (신경 결과)**

> The filter's effect on the neural readouts varied by participant and by measure. Adjacent accuracy on hue interpolation separated the two participants, rising in the deutan participant ($0.23 \to 0.31$) and falling in the protan participant ($0.14 \to 0.06$). In each participant the early-visual geometry shifted in the direction opposite to interpolation. In the deutan participant both filters moved the geometry away from the HC reference. In the protan participant both filters moved the geometry toward the HC reference. So, that recovery was not specific to the individualized filter. SRM disparity was lower under the individualized filter in the deutan participant and nearly equal between filters in the protan participant. RDM similarity to HC was higher under the deployed filter in both participants. The geometry of both participants remained displaced from the HC reference.

**¶10 (신경 해석 + 범위)**

> Early-visual geometry and hV4 interpolation lie at different levels of the visual hierarchy and can vary independently. These neural readouts remain inconclusive in a two-case sample. Replication in more individuals within each subtype, on a refined neural endpoint, is required to establish whether either pattern generalizes.

이 재편으로 ⑪(대명사 `it`)과 재현 요건 중복 1건이 함께 해소됩니다. 2문단(행동/신경)으로 합치는 안도 가능하나 신경 문단이 175어가 되어 권하지 않습니다.

### F3. L43 분할 — 자극 범위 / 손실항 통합

**¶13 (자극 범위)**

> The stimulus set was confined to a single isoluminant, iso-chroma locus ($L^{*} = 75$, chroma $= 40$). The correction is therefore untested for stimuli that vary in lightness or chroma, including natural scenes. Extending it to those stimuli requires refitting the model at additional levels of both dimensions.

**¶14 (손실항 통합)**

> The fitting objective combined the behavioral thresholds with the $\Delta$RDM term, and the interpolation term competed as a candidate without being selected in either participant. The two neural terms are evaluated on different quantities at different ROIs. Interpolation uses an eight-element per-hue decoding profile at hV4, whereas $\Delta$RDM uses a 28-element vector of pairwise representational distances at V1 or V2. Expressing both on a shared quantity would let one objective weight interpolation against geometry, and would supply the joint neural endpoint this evaluation lacked.

### S1. 용어 통일 (§4)

`(HC)` 정의를 **L18 → L15로 이동**하고, 이후 전 구간에서 수식어를 `HC`로 고정합니다. 명사는 지시 대상이 달라 유지합니다.

| 현행 | 수정 | 지시 대상 |
|---|---|---|
| `healthy-control geometry` (L15) | `healthy-control (HC) geometry` | 기하 기준 (정의 지점) |
| `control cohort` (L18) | `HC cohort` | 대조군 집단 |
| `control range` (L15, L34) | `HC range` | 행동 역치 정상 범위 |
| `control reference` (L34, L46) | `HC reference` | 기하 기준 |

L18의 `healthy-control (HC) geometry`는 정의가 앞으로 이동하므로 `HC geometry`로 축약합니다.

### S2. anomaloscope 초출 정의 + 항목 분리 (L39)

현행은 표본 크기 한계 문장 안에 **중증도 등급 도구라는 별개 한계**를 삽입하고, `anomaloscope`가 원고 전체 유일 등장인데 gloss가 없습니다.

> Separating a per-person correction from a subtype-average one requires testing several individuals \emph{within} a single subtype. It also requires grading severity on a continuous scale. The Ishihara plates used here classify subtype but do not quantify severity. An anomaloscope, which measures the red--green mixture an observer accepts as a match to a reference yellow, would supply that grading.

+약 30어.

### M1. `a larger sample` (L15)

> `Establishing an advantage over the deployed filter in **a larger sample** is the immediate next test.`
> → `... in **more than two participants** is the immediate next test.`

L48의 `Larger and systematic studies`는 전망 문장이므로 유지.

### M2. `improvement` (L48) — **변경 불요 판단**

`a generalizable improvement in color perception`. §19B는 untestable verb 대체를 요구하나, 이 문장은 **후속 연구가 정의할 종점**을 서술합니다. 특정 지표(`reduction in hue-discrimination thresholds` 등)로 좁히면 실제보다 협소한 약속이 됩니다. 유지 권고.

### M3. §25 gap 회수 — **부분 충족으로 판단**

L23(`derived from an individual's cortical color representation rather than from a retinal model` + `whereas population-average corrections apply a fixed subtype-average spectral shift`)이 Introduction L65의 gap(`A retinal parameter ... does not describe the cortical representation`)과 대응합니다. 명시적 회수 문장을 원할 경우 Conclusion 첫머리에 한 문장 추가가 자리이나, **필수 아님**.

### M4. 구조 문서 갱신 (`discussion_structure_v3.md`)

2026-06-08판이 ¶6을 여전히 "Phase 3 forward-looking TODO"로 규정합니다. §2 skeleton을 현행 구조(위 분할 반영 시 17문단)로 갱신하거나, 헤더에 supersede 주석을 달아야 다음 사이클의 drift 판정이 유효해집니다.

---

## 7. Priority summary

**Total 20건** (false positive 8건 제외) → **해소 9 / 유지 결정 4 / 승인 대기 7**

| # | 항목 | 등급 | 상태 |
|---|---|---|---|
| ① | `exact pre-image` 결과 프레임 (L15·L21·L46) | Fatal | ✅ 해소 — 색별 단일 보정색으로 재프레이밍 |
| ② | §7 위반 L29 | Fatal | ✅ F1 적용 |
| ③ | §7 위반 L34 | Fatal | ✅ F2 적용 |
| ④ | §7 위반 L43 | Fatal | ✅ F3 적용 |
| ⑤ | L18 `more robust sources` | Serious | ✅ 해소 — 사용자 재작성 |
| ⑥ | 개회 주장 vs 적합 입력 불일치 | Serious | ✅ 해소 |
| ⑦ | 두 축 순환 정의 | Serious | ✅ 해소 |
| ⑧ | 용어 4변형 | Serious | ✅ S1 적용 |
| ⑨ | 재현 요건 5회 중복 | Serious | ✅ F2로 4회로 감소. ⑱ 유지 결정에 따른 잔여분은 수용 |
| ⑩ | `kriegeskorte2019` | Serious | ✅ 해소 — 키 삭제 |
| ⑪ | L36 대명사 `it` | Serious | ✅ F2에서 `the geometry`로 교체 |
| ⑫ | anomaloscope | Serious | ✅ S2 적용 |
| ⑬ | `a first two-person evaluation` | Minor | ✅ 해소 |
| ⑭ | L18 3-primary 스택 | Minor | ✅ 변경 불요 확정 (리뷰 조사 완료) |
| ⑮ | `larger` 무수치 | Minor | ⛔ 미적용 (필수 아님) |
| ⑯ | L48 `improvement` | Minor | ✅ 변경 불요 판단 (M2) |
| ⑰ | §25 gap 회수 | Minor | ✅ 부분 충족 판단 (M3) |
| ⑱ | L15 마지막 문장 | Minor | ⛔ 사용자 유지 결정 |
| ⑲ | `Establishing` 문두 중복 | Minor | ⚠️ F2로 해소(L34 측 삭제) |
| ⑳ | 구조 문서 stale | Minor | ⛔ 미적용 (원고 외 파일) |

### 종결 상태

**Fatal 4/4 · Serious 8/8 해소.** 잔여는 Minor 2건(⑮ `larger` 무수치, ⑳ 구조 문서 갱신)이며 모두 사용자 판단으로 미적용, ⑱은 유지 결정입니다.

⑳은 원고 자체에 영향이 없으나, `discussion_structure_v3.md`를 갱신하지 않으면 **다음 `/revise-draft` 사이클의 outline drift 판정 기준이 계속 무효**입니다(현행 17문단 대 문서상 8문단 skeleton). 재실행 전 처리 권고.

### 이번 세션 작업의 검증 결과

§2(문장 길이·구두점) **전 문단 통과**, §5(filler) **0건**, §19 Tier D **0건**, 인용 밀도 **0건**, topic sentence **14/14**. 표현 층위는 수렴했습니다. 남은 이슈는 **문단 역할 분해(§7)와 주장 범위(§10/§12)** 라는 상위 층위에 집중되어 있습니다.

---

# §8. Round 2 — 재실행 (2026-08-06, 17문단)

Round 1의 F1·F2·F3·S1·S2 적용 후 재스캔.

## 8-1. 자동 스캔

| 검사 | Round 1 | Round 2 |
|---|---|---|
| §2 장문 (45어 초과 / em-dash 2+ / 세미콜론) | 0 | **0** |
| §5 filler | 0 | **0** |
| §19 Tier A | 2 | **1** (L23, 프로젝트 정책 승인분) |
| §19 Tier B | 1 + FP 2 | **1** (L54 `improvement`, 변경 불요 확정) + FP 2 |
| §19 Tier C | 2 + FP 5 | **1** (L15·L54 `larger`, 미적용 결정) + FP 5 |
| §19 Tier D | 0 | **0** |
| §20 5+ 스택 | 0 | **0** |
| §17 재현 요건 반복 | 5회 | **4회** |
| 대명사 미해결 (`moved it`) | 1 | **0** |
| 용어 변형 (`control-*`) | 4종 | **1** (L15 정의 지점만) |

## 8-2. §26 Checklist

### Reverse outline
- [✓] 문단당 한 문장 요약 — 17/17 (`discussion_structure_v3.md` §2)
- [✓] §1 Step 5 outline 일치 — 구조 문서 §2를 현행 구조로 갱신 완료
- [✓] 두 문장 필요 문단 없음 — F1·F2·F3로 해소

### Claims
- [N/A] title+abstract 기여 회수 — 검토 범위 밖
- [✓] 수치 Δ에 baseline+metric — chance 기준은 `results_v4.tex:222`로 위임 (정책)
- [✓] `first/only/no X` — 1건, `CLAUDE.md` 승인 형태
- [⛔] untestable verb — L54 `improvement` 1건, **변경 불요 확정** (후속 연구가 정의할 종점)
- [⛔] vague adjective — L15·L54 `larger` 2건, **미적용 결정**
- [✓] self-praise 없음

### Citations
- [✓] general → review (조사 완료: 기하 프레이밍 리뷰 부재, primary 3편이 적합)
- [✓] specific → primary
- [✓] method origin → original
- [✓] 5+ 스택 없음

### Structure
- [✓] **문단당 한 역할** — Round 1의 3건 해소
- [✓] 첫 문장 = topic sentence — 17/17
- [✓] 대명사 명확 — 잔여 대명사 5건 모두 직전 문장에 선행사
- [✓] 용어 일관 — `HC` 수식어로 통일
- [✓] observation / interpretation / implication 분리

### Section-by-section (§25)
- [△] gap 회수 — L23이 Introduction L65의 gap과 대응, **부분 충족 판단**
- [✓] 선행연구 맥락 / 한계 / field impact / 신규 결과 없음

### Final pass
- [✓] filler / 부정형 / 능동태
- [⛔] nominalization — L15 `Establishing ... is the immediate next test`, **사용자 유지 결정**. F2로 L36의 중복 `Establishing`은 제거됨

## 8-3. 판정

**규칙 위반으로 남은 항목 없음.** 잔여 `[⛔]` 4건은 전부 **사용자가 명시적으로 유지·미적용을 결정한 항목**이며, 검출 실패나 미처리가 아닙니다.

- ⑮ `larger` ×2 — 필수 아님으로 미적용
- ⑯ L54 `improvement` — 특정 지표로 좁히면 협소한 약속이 되므로 변경 불요
- ⑱ L15 마지막 문장 — 유지 결정 (⑲ nominalization·§17 잔여 1회가 여기 종속)

**게이트 (B) §26: 사용자 결정분을 제외하고 전 항목 ✓.**
게이트 (A) apply-draft 로컬 수렴은 별도 확인 필요.

## 8-4. Naive-reader 재검 (Phase 5.5, Round 2)

대상: 개정된 ¶1(L15) 단독. 위양성 필터 후 결과.

### Round 1 대비 해소 (3건)

| Round 1 지적 | Round 2 |
|---|---|
| `exact pre-image`가 결과인지 구성적 성질인지 불명 | **해소** — 재언급 없음 |
| 개회 주장(`from the cortical representation`)과 적합 입력(행동+신경) 불일치 | **해소** — 모순 지적 사라짐 |
| confusion axis 순환 정의 | **해소** — 순환 지적 사라짐 (잔여는 도메인 용어 미정의 수준) |

### 위양성 (앞 절에서 정의됨)

`CVD`, `deutan`/`protan`, `ROI`, `HC range`, `adjacent-hue accuracy`, `baseline threshold deficit`, `representational disparity` — Introduction·Methods·Results에서 도입.
`The deployed accessibility filter` — `methods_v2.tex:300`이 `a deployed macOS accessibility filter`로 명명. Discussion 단독 열람 시에만 불명.
`Both axes were fixed before fitting` — 실제 본문은 `(Methods~\S\ref{sec:methods:twocomp})`를 동반. 검증 가능.

### 신규 이슈 3건 — 2건은 Round 1 수정이 유발한 **회귀**

**N1 (회귀). L15 1–2문장 중복.**
> `We derived a per-person color-correction filter ...` / `Each filter inverts a model of one participant's cortical color representation, **fitted independently to that participant's** ...`

`per-person`과 `fitted independently to that participant's`가 같은 내용을 두 번 전달합니다. ②(개회 주장 불일치) 수정 과정에서 발생.

**N2 (회귀). `single replacement color`가 8-entry lookup table로 읽힘.**
> "I also can't tell whether 'single replacement color' means the filter is literally an 8-entry lookup table (which would be a surprisingly coarse 'filter'), or whether the 8 colors are samples of a continuous map. The word 'filter' implies the latter; the sentence says the former."

`appendix_alternative_models.tex` §A.2는 **연속 사상**임을 명시합니다 — `a pre-image exists for any target hue` / `The filter ... is that pre-image, evaluated at the eight stimulus hues`. ①(구성적 성질→결과 프레임 제거) 수정에서 `for all eight hues`를 `each of the eight hues`로 바꾸며 연속성이 소실됐습니다.

같은 지적의 더 무거운 절반: **신경 표상공간 → 자극공간 다리가 서술되지 않음.** "the brain's representation is rotated"에서 "therefore show this person magenta instead of red"로 가는 연결이 ¶1에 없습니다. L21이 `the displayed hue that the participant's own cortical transformation maps onto the intended color`로 이를 수행하나, ¶1에는 대응 문장이 없습니다.

**N3. `The S-cone axis is the direction of S-cone modulation` 준동어반복.**
정보를 담은 절(`where the interpolation deficit concentrated`)이 후행 수식절에 묻혀 있습니다. ③ 수정에서 발생.

### 사용자 결정으로 잔존 (재확인됨)

- `n=2` 1↑1↓를 중립 서술 — ④ 유지 결정
- 마지막 문장의 내용 부재 및 앞 문장과의 긴장 — ⑱ 유지 결정
- ¶1 수치 전무 — 정책 결정(수치는 Results)
