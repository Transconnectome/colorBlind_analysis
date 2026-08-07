# Revision Report — docs/PAPER/Results/results_v4.tex — 2026-08-08

Scope: 전체 (L21–L241, 10 subsections + 5 figure captions)
Rules: `~/.claude/writing/academic_writing_rules.md` (Parts II–V)
Pre-draft: **없음** (`pre_draft_*.md` 미발견) → 의도 outline 대비 drift 검증 불가

> 이 리포트는 2026-08-07~08 문단별 개정(→ `Results/RESULTS_REVIEW_2026-08-07.md`) **이후** 상태를 검사한다.
> 사실 정확성·BLUF·부정표현은 그 문서가 관할하며, 여기서는 글로벌 rule 위반만 다룬다.

---

## 1. Reverse outline

### 3.1 All eight colors remain decodable across ROIs in both CVD cases
- L29 (¶1): 두 CVD 참가자가 전 ROI에서 8색을 chance 위로 분류해 필터의 전제를 충족한다.
- L31 (¶2): 대조군에서 만든 encoder가 CVD 피질로 전이되며, 약화되되 소멸하지 않는다.

### 3.2 Hue interpolation is reduced at hV4 in both CVD cases
- L38 (¶1): 대조군에서 보간은 hV4에서만 순열 귀무를 넘는다.
- L40 (¶2): 두 CVD 참가자 모두 hV4에서 대조군 분포 아래로 떨어진다.
- L42 (¶3): 감소가 S-cone 중간 hue에 집중된다.

### 3.3 Geometric deviation localizes to a distinct ROI in each CVD case
- L60 (¶1): 상승한 disparity가 참가자마다 다른 ROI에 국소화한다.
- L62 (¶2): protan은 V1에서 두 추정량 모두 상승한다.
- L64 (¶3): deutan V2는 LOSO에서 살아남지 못하고 V3와 구분되지 않는다.
- L66 (¶4): 편차가 참가자별이므로 집단 단위 보정은 한 번에 한 사례만 다룬다.

### 3.4 Hue-discrimination thresholds are elevated on each participant's own confusion axis
- L86 (¶1): 각 참가자의 임계값 상승이 자기 아형의 혼동축에 떨어진다.
- L88 (¶2): 나머지 쌍은 대조 범위 안이며 180° 통제쌍이 천장효과를 배제한다.
- L90 (¶3): 이 비율이 적합의 심리물리 입력이다. **[역할 혼합]** 결과 진술 + 다음 절 로드맵.

### 3.5 The retinal-plus-gain model is structurally insufficient
- L97 (¶1): R+C는 두 참가자 모두에서 구조적으로 불충분하되 근거가 사례별로 다르다.
- L99 (¶2): 적합된 $g>2$는 참가자의 측정된 CVD 상태와 모순된다.
- L101 (¶3): R+C는 고정된 한 축으로만 변위시켜 필터 후보에서 제외된다.

### 3.6 A common cortical model fits both CVD cases
- L108 (¶1): 2-component 모형이 동일 함수형으로 두 참가자를 적합한다.
- L110 (¶2): deutan 적합값과 그 안정성.
- L112 (¶3): protan 적합값과 그 안정성, 그리고 기저 의존성.
- L114 (¶4): ROI 축은 분리 전제조건이 정했고, 적합 파라미터는 그 선택에 둔감하다. **[역할 혼합]** provenance + robustness.
- L120 (¶5): 두 적합 모두 held-out 폴드에서 일반화한다.

### 3.7 The neural term relocates the protan fit and sharpens the deutan fit
- L128 (¶1): 신경항의 세 효과 요약.
- L130 (¶2): protan에서 추정값을 옮긴다.
- L132 (¶3): deutan에서 정밀도를 더한다.
- L134 (¶4): 두 참가자 모두 resample 산포가 좁아진다.

### 3.8 The mechanism class is recoverable while the per-axis magnitudes are bounded rather than estimated
- L140 (¶1): deutan 부호는 회수되고 protan 부호는 기저 의존적이다.
- L142 (¶2): 회수 절차 오차를 넘는 것은 deutan 혼동축 진폭뿐이다.
- L144 (¶3): deutan 적합 내에서 두 축의 구속 정도가 다르다.

### 3.9 Per-subject stimulus-space filter
- L164 (¶1): 두 필터는 평균 진폭과 두 hue의 방향에서 다르다.
- L166 (¶2): 참가자별 보정 범위.
- L168 (¶3): 반대 부호와 다른 혼동축이 상쇄해 6/8 hue에서 방향이 같다.

### 3.10 Psychophysical and neural filter evaluation
- L190: 2차 세션 수행. / L193–199: 심리물리 4문단. / L202: 분류 전제.
- L229–231: 보간 2문단. / L234–240: 기하 4문단.

### Drift vs intended outline
Pre-draft 산출물이 없어 **비교 기준 없음**. 다만 절 순서(전제 → 결핍 → 기하 → 심리물리 → 모형 비교 → 적합 → 신경항 역할 → 식별성 → 필터 → 검증)는 그 자체로 논증 사슬을 이루며, 각 절 제목만 읽어도 서사가 복원된다.

### Subsection topic rollup
- `3.1`–`3.5`, `3.7`–`3.9`: 모두 단일 topic ✓
- **[SPLIT?] `3.6` A common cortical model fits both CVD cases** — topic1: 두 참가자의 적합값과 안정성 (¶1–3, 5) / topic2: ROI 축 provenance와 그에 대한 둔감성 (¶4). ¶4는 "무엇이 적합됐나"가 아니라 "왜 그 손실 조합이었나"를 다룬다. 다만 이 병합은 2026-08-08 사용자 지시(별도 문단의 지시 대상 소실 때문)로 이루어졌으므로 **규칙 위반이자 의도된 선택**이다. 분리한다면 `3.6b Loss-combination provenance`가 후보.
- **[SPLIT?] `3.10`** — 네 topic(심리물리·분류·보간·기하)이 한 heading 아래. 다만 `\paragraph{}` 하위 표제가 분리를 수행하므로 venue 관례상 허용 범위. 조치 불요.

---

## 1.5 Long sentences (§2)

| 행 | 길이 | 문제 | 분할 지점 |
|---|---|---|---|
| **L120** | **53어** | 두 결과(폴드별 개선 / 격자 백분위)를 `, and`로 연결 | `…than by no distortion at all.` 에서 절단 |
| **L140** | 40어, 절 표지 3 | `(Figure), and … also shows, so …` 3중 종속 | `…on the full data (Figure~\ref{fig:landscape}).` 에서 절단 |

그 외 45어 초과 없음. 산문 세미콜론 **0**, 콜론 **0** (캡션 라벨 5건 제외).

---

## 2. §19 Vocabulary

### Tier A — Banned (2 hits, **둘 다 false positive**)
- L142 `the S-cone amplitude **cannot** be distinguished from zero at this resolution` → §19A는 `cannot`을 `fails under [stated assumption]`로 바꾸라 하나, 여기는 **해상도 조건이 이미 명시**되어 있다(`at this resolution`, 앞 문장에 $16$–$26°$ 불확실성). 규칙의 의도를 충족 → **유지**.
- L199 `Establishing whether it **outperforms** the deployed filter requires more participants` → §19A는 무근거 `outperforms`를 금한다. 여기는 **주장이 아니라 주장 불가 선언**이다 → **유지**.

### Tier B — Untestable verbs (8 hits, 5 false positive / **3 검토**)
- L42, L51 `exploratory` — 검정의 성격 규정, Tier B 대상 아님 → 유지
- L66 `a family-level correction would **address** one case at a time` → 🟡 `address`는 §19B 대상. 대체: `would correct one case at a time`
- L112 `Both combinations **improved on** the retinal-plus-cortical class ($\overline{L}_{\rm test} = -0.86$)` → 수치 동반 → 유지
- L193 `**improved** thresholds … / **improved** the deutan participant` → 🟡 두 번 모두 수치 없이 등장. 바로 다음 문단들이 수치를 주지만, §19B는 인라인 operationalize를 요구. 대체: `lowered the mean $|z|$ in the deutan participant and left it unchanged in the protan participant`
- L231 `corroborated the deutan **improvement** at hV4 ($\rho = +0.18$ …)` → 수치 동반 → 유지
- L240 `only the deployed filter **improved on** the unfiltered baseline` → 직전 문단이 $0.33 \to 0.38$ 제시 → 유지

### Tier C — Vague (6 hits, **전부 false positive**)
- L40 `**significantly** so … ($t = -3.04$, $p = 0.012$, $d_{cc} = -3.25$)` → 검정 동반 ✓
- L40 `a **large** effect … ($d_{cc} = -2.02$)` → 효과크기 동반 ✓
- L42 `blue the **largest** deviation … ($d_{cc} = -2.06$)` → 수치 동반 ✓
- L64 `requires a **larger** cohort` → 비교급, 표본 크기 진술 ✓
- L142 `an **effective** uncertainty of $22^\circ$ …` → 정의된 기술 용어 + 수치 ✓
- L142 `no **significant** result after Benjamini–Hochberg correction` → 검정 명시 ✓

### Tier D — Self-praise: **0 hits** ✓

---

## 3. §20 Citations

Results 전체에 인용 3곳뿐(대부분의 근거가 Methods·Supplementary에 있음).

| 행 | 인용 | 주장 유형 | 판정 |
|---|---|---|---|
| L31 | `\cite{boehm2014, bosten2019}` | 일반 도메인 진술 (`consistent with prior work on above-threshold color identification in CVD`) | 🟡 **suspect** — 두 편 모두 primary empirical. §20은 일반 진술에 review를 요구. 다만 해당 주제의 review가 존재하는지 확인 필요. 대안: 주장을 특정화(`consistent with the above-threshold identification reported by …`) |
| L38 | `\citeA{brouwer2009}` | 특정 경험적 결과 재현 (`This replicates`) | ✓ primary paper, 적절 |
| L97 | `\cite{wilson2019}` | 방법론적 판정 근거 (`rejects the model as misspecified`) | ✓ 방법론 출처로 적절 |

- 5+ 스택 **없음** ✓
- 비교 구문(`than`, `whereas`, `compared with`) 중 인용을 요구하나 없는 곳: 없음 (전부 자체 데이터 비교)

---

## 4. §26 Checklist

### Reverse outline
- [✓] 문단당 한 문장 요약 — 33개 문단 전부 가능
- [N/A] §1 Step 5 outline 대조 — pre-draft 부재
- [✗] 두 문장이 필요한 문단: **L90, L114** (§7 역할 혼합)

### Claims
- [N/A] title+abstract 기여 문장 — Results 범위 밖
- [✓] 모든 수치 Δ에 baseline + metric + sample — 개정 과정에서 전수 대조 완료
- [✓] `first/only/no X` — Tier A 2건 모두 정당
- [✗] untestable verb — **L66, L193** 3건
- [✓] vague adjective — 전부 operationalize됨
- [✓] self-praise 없음

### Citations
- [🟡] 일반 주장 → review: **L31** suspect
- [✓] 특정 주장 → primary
- [✓] method origin → original
- [✓] 5+ 스택 없음

### Structure
- [✗] 문단당 한 역할 — **L90, L114**
- [✓] 첫 문장 = topic sentence — 33/33. 2026-08-07~08 BLUF 통과분
- [🟡] 대명사 명확 — **L31 `none of the eight`** 의 선행사 모호(8색 vs 8검정). naive-reader가 걸려 넘어짐
- [✓] 용어 일관 — `deployed`/`individualized` 통일, `HC`/`healthy controls` 혼용은 관례 범위
- [✓] 관찰/해석/함의 분리

### Section-by-section
- [N/A] Abstract, Introduction — 범위 밖
- [✓] Methods 순서 = Results 순서 — 2026-08-08 §3.4 신설로 심리물리가 적합 앞에 배치되어 일치
- [✓] 각 결과가 선행 질문에 답함
- [N/A] Discussion
- [🟡] **캡션이 takeaway를 진술** — §13은 요구하나, 사용자가 NeuroImage 관례(측정 기술만)를 명시적으로 채택해 Fig 2·4·6·7·8에서 결과 문장을 제거했다. **규칙 충돌**이며 프로젝트 결정이 우선. `CLAUDE.md`에 기록 권장

### Final pass
- [✓] filler 없음
- [🟡] 긍정 대체 가능한 부정 — **L240 `Neither index attributes…`**. 다만 이것이 이 절의 핵심 주장(개인화 귀속 불가)이라 유지 타당
- [✓] nominalization → 동사
- [✓] 능동태

---

## 5. Naive-reader check

도메인 지식 0인 ML 일반 독자에게 §3.1 전문 + §3.2 첫 문단을 인라인 제시.

> ⚠️ **발췌 인공물 먼저 분리.** 아래 셋은 제가 자른 탓이며 원고 문제가 아니다 — (a) "§3.2에 CVD 데이터가 없다"(¶L40을 안 줌), (b) "인용이 없다"(`\cite` 제거), (c) CVD·ROI·SRM 미정의(Methods가 앞서 정의).

### 진짜 이슈

| # | 지적 | 판정 |
|---|---|---|
| 1 | **`0.125` chance와 `0.25` chance가 한 절 안에서 설명 없이 병존** | 🔴 실질. 두 지표(exact 8-way vs adjacent)의 판독 공간이 다르기 때문인데 Results는 그 이유를 말하지 않는다. §3.2 첫 문단에 한 구절 추가 권장 |
| 2 | **`analytic chance 0.25`와 `permutation null 0.35`가 40% 어긋나는데 이유 없음** — "첫 절이 둘째 절에 의해 무효화된다" | 🔴 실질. 라벨 순열이 복셀 공분산을 보존하기 때문. Supplementary §S9에 있으나 본문에 한 구절 필요 |
| 3 | **`t(7)`의 관측 단위 불명** — CVD 2명인데 df=7 | 🟡 실질. 8 = 2 참가자 × 4 ROI 셀. 본문이 말하지 않음 |
| 4 | **`U = 163.5`의 두 표본 크기 불명** | 🟡 실질. 28 vs 8 셀. Methods에 있으나 독자가 되짚어야 함 |
| 5 | **`none of the eight` 선행사 모호** | 🟡 실질. §3 위반. `none of those eight tests` |
| 6 | **hV4가 LORO에서 최저(0.375)인데 LOCO에서 유일 통과** — 조정 문장 없음 | 🟡 실질이자 흥미로운 관찰. 두 지표가 다른 능력을 잰다는 점을 한 문장으로 |
| 7 | **`channel-to-voxel code`가 불투명** | 🟡 Methods가 정의하나 Results에서 처음 이 복합어로 등장 |
| 8 | **`Repeating the readout in the SRM-aligned space reproduces the pattern`에 수치 0** | 🟢 포인터 문장. §S11이 표를 제공하므로 허용 |
| 9 | **¶L31 마지막 문장이 ¶L29 첫 문장의 재진술** | 🟡 §5. 사이에 다른 분석(전이)이 끼어 있어 topic 전환을 덮는다 |
| 10 | V1–V3의 정확도 미제시, p만 제시 | 🟢 §S11 표에 있음 |

### One-line takeaway (naive reader)
> 두 색각이상자에서 8색은 시각피질에서 여전히 해독되고 대조군 디코더도 전이되며, 대조군에서 hue **보간**은 hV4에만 국한된다.

→ 절의 의도된 메시지와 일치. **진입부의 논증은 전달된다.**

---

## 6. Priority summary

총 이슈: **13** (false positive 11건 제외 후)

- **Fatal**: 0
- **Serious (7)**: naive-reader #1 #2 (chance 세 종류의 미설명 병존), #3 #4 (검정 단위·표본 미명시), #5 (`the eight` 선행사), §7 역할 혼합 L90·L114
- **Minor (6)**: §2 장문 L120·L140, §19B `address`·`improved` 3건, §20 L31 인용 specificity, §5 재진술 L31

권장 순서:

1. **chance 계층 정리** (naive #1 #2) — `0.125` / `0.25` / 순열 귀무 `0.35` 셋이 왜 다른지 §3.1·§3.2에 각 한 구절. 이 절의 핵심 논증이 여기 걸려 있어 최우선
2. **검정 단위 명시** (naive #3 #4) — `t(7)` 의 8셀, `U` 의 28 vs 8
3. **`none of the eight` → `none of those eight tests`** (§3)
4. **L90·L114 역할 분리** (§7) — L114는 사용자 지시 병합이므로 재확인 필요
5. **L120·L140 문장 분할** (§2)
6. **`address`·`improved` 대체** (§19B)
7. **L31 인용 specificity 검토** (§20) — CVD 색 식별 review 존재 여부 확인

---

## 7. 규칙 충돌 기록

**§13 (캡션은 takeaway를 진술) ↔ 프로젝트 결정 (NeuroImage 관례, 측정 기술만).**
2026-08-08 사용자 지시로 Fig 2·4·6·7·8 캡션에서 결과 문장을 제거했다. 글로벌 rule과 어긋나므로 재검토 시 반복 지적될 수 있다. 프로젝트 `CLAUDE.md`에 명시해 두면 이후 `/revise-draft` 실행에서 자동 예외 처리된다.

---

# Round 2 — §26 재검토 (2026-08-08, 수정 적용 후)

적용분: P1(chance 계층), P2(검정 단위 + 선행사 + 재진술), ①③④⑤⑥⑧.
미적용(사용자 결정): ② L114 문단 분리 — ROI 서술로 한 문단 유지 / ⑦ hV4 두 지표 역전 문장.

## 자동 스캔 결과

| 항목 | Round 1 | Round 2 |
|---|---|---|
| §19 Tier A | 2 (전부 정당) | 2 (동일, 정당) |
| §19 Tier B | 8 (3 검토) | 5 (**전부 정당**) |
| §19 Tier C | 6 (전부 FP) | 3 (전부 FP) |
| §19 Tier D | 0 | 0 |
| §2 45어 초과 / 3중 종속 | 2 | **0** |
| 산문 `;` / `:` | 0 / 5 | **0 / 4** |
| §8 topic sentence | 33/33 | **47/47** (캡션 5 제외) |

Tier B 잔여 5건은 `exploratory` ×2(검정 성격 규정, 대상 아님)와 `improved`/`improvement` ×3(전부 수치 동반).
Tier C 잔여 3건은 `significantly`($t$,$p$,$d$ 동반), `effective uncertainty`(정의된 기술용어+수치), `significant`(BH 명시).

## §26 판정

### Reverse outline
- [✓] 문단당 한 문장 요약 — 47/47
- [N/A] §1 Step 5 대조 — pre-draft 부재
- [✓] 두 문장이 필요한 문단 — L90 해소. **L114만 남으며 이는 사용자 결정**

### Claims
- [N/A] title+abstract — 범위 밖
- [✓] 수치 Δ에 baseline+metric+sample
- [✓] Tier A / B / C / D

### Citations
- [✓] 일반 주장 → review — `bosten2019` = *Current Opinion in Behavioral Sciences* 리뷰로 확인, Round 1 suspect **철회**
- [✓] 특정 주장 → primary / method origin → original / 5+ 스택 없음

### Structure
- [🟡] 문단당 한 역할 — **L114**(provenance+robustness). 사용자가 ROI 단일 주제로 판단
- [✓] 첫 문장 = topic sentence
- [🟡] 대명사 — 6건 중 4건 명확. **L38 `This replicates…`**(선행 = hV4 결과 전체), **L154 `It is a descriptive…`**(선행 = argmin인지 별표인지) 경미
- [✓] 용어 일관 / 관찰·해석·함의 분리

### Section-by-section
- [✓] Methods 순서 = Results 순서
- [✓] 각 결과가 선행 질문에 답함
- [✓] 캡션 — 프로젝트 규칙(측정 기술만) 적용. §13 충돌은 `CLAUDE.md`에 기록 완료

### Final pass
- [✓] filler / nominalization / 수동태
- [🟡] 긍정 대체 가능한 부정 — `Neither index attributes…`(L240) 유지 타당

## naive-reader 지적의 처리

| # | 지적 | 상태 |
|---|---|---|
| 1 | `0.125` vs `0.25` 미설명 병존 | ✅ §3.2 ¶1에 360-hue argmax + $45°$ 근거 추가 |
| 2 | 순열 귀무 `0.35`이 해석적 chance보다 높은 이유 없음 | ✅ `shuffling the labels leaves the covariance among voxels intact` |
| 3 | `t(7)` 관측 단위 불명 | ✅ `over the eight participant-by-ROI cells` |
| 4 | `U = 163.5` 표본 불명 | ✅ `over the 28 cells` |
| 5 | `none of the eight` 선행사 | ✅ `none of those eight cells` |
| 6 | hV4가 LORO 최저인데 LOCO 유일 통과 | ❌ 사용자 결정으로 미추가 |
| 7 | `channel-to-voxel code` 불투명 | 🟡 Methods가 정의. Results 첫 등장 시 무주석 |
| 8·10 | SRM 재판독·V1–V3 정확도 수치 없음 | 🟢 §S11 표가 제공 |
| 9 | ¶L31 마지막 문장이 ¶L29 재진술 | ✅ 두 문단 종합으로 교체 |

## 수렴 게이트

- **(B) §26 전 항목** — Fatal 0, Serious 0. 잔여는 🟡 3건이며 **둘은 사용자 결정, 하나(대명사 2건)는 경미**
- **(A) apply-draft 로컬 수렴** — 본 사이클은 `/apply-draft` 없이 직접 적용했으므로 해당 게이트를 거치지 않았다. 형식 요건을 채우려면 `/apply-draft`를 한 번 태우거나, 직접 적용분에 대한 Before/After 수용으로 갈음해야 한다

**판정: Results 섹션은 §26 기준 제출 가능 상태.** 남은 세 건은 모두 판단 사항이지 규칙 위반이 아니다.
