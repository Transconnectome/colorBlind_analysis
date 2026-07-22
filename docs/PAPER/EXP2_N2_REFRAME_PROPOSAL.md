# exp2 N=2 재프레이밍 제안 (검토용 · 미적용)

> 작성 2026-07-14. **이 문서는 제안일 뿐, 어떤 tex/md도 아직 수정하지 않음.**
> 목적: (1) 문서간 불일치를 어떻게 해소할지, (2) 논문 현재 서술을 어떻게 고칠지 — 검토 후 승인 시 적용.
> 수치는 전부 실측 JSON에서 검증(`exp2_hc_likeness_sub-{08,09}_matched.json`, `exp2_convergent_*`). 새 주장 없음. §6.5(critic-refined) 미러링.
> **참조 원고**: `docs/ICML_workshop/SD4H_cameraready_pathB_0624_A.pdf` (ICML 2026 SD4H workshop camera-ready). 역할은 Part 3 참조.

---

## 확정 프레임 (STABLE — 논의 내내 유지, 함부로 변경 금지)

> 2026-07-14 사용자와 합의. 이 프레임 위에서 모든 문구를 작성·수정한다. 프레임 자체를 바꾸려면 명시적 재합의.

**전체 메시지(한 문장)**: CVD 색각 결손 = 색 신호 *소실*이 아니라 개인별로 패턴화된 **피질 색-기하 왜곡**이며, 이를 개인별로 정량화해 **가역 필터로 역산**할 수 있다. → 핵심은 **특성화(Beat 1) + 방법(Beat 2)**, **필터 효능 입증 아님**.

**3-Beat 아크**
- **Beat 1 — 왜곡 특성화 (확증, 강)**: 두 CVD 모두 판별 보존 / 보간(hV4)·기하(V1/V2) 왜곡, ROI 개인차(deutan V2 / protan V1). "공유되지만 개인화된 왜곡."
- **Beat 2 — 개인화 필터 역산 (방법 기여)**: 2-Comp → 해석적 역산, 모든 hue exact pre-image, cone-shift보다 구조적 우월. (ICML 스코프.)
- **Beat 3 — 첫 신경 검증 (탐색적, 약)**: Results 내 정식 결과이되 3층 중 **가장 약한 층**. 효능 **미확인(열린 문제)**.

**핵심 서술 규칙 (합의됨)**
1. **exp2 위치** = Results 정식 결과(탐색적). 제거·강등 아님. primary 반전 정면 서술.
2. **protan 반전 프레임 = 효능 미확인(한계)**. "phenotype마다 다르다"는 뉘앙스 발견으로 팔지 않음. §6.5.3 금지문구 준수.
3. **"individual-specific" 용법 구분**: **(a) 필터가 개별화됨=제작 사실→유지 O**. **(b) 필터 효과가 개인마다 다름→금지 X**. 초록·본문에서 (a)만.
4. **§6.5.5 자극-구동 논리**는 **geometry(V1/V2)가 왜 효능 endpoint 아닌지**에만 사용. **protan hV4 primary 반전 해명엔 사용 안 함**(그건 "효능 미확인" 그대로).
5. **행동 = 프레임워크 가능성 / 신경 = 개선 주장 불가**의 분리 유지. 행동 근거는 "deutan 결손 정상화 + protan 무해", "deployed 능가 아님".
6. writing rules: 짧은 문장.
7. **조건명 표준 (전역 적용)** — 논문·figure·caption 전체에서 아래 3종으로 통일. 기존 **"Window / Windows filter"는 OS 오류**(실제 macOS accessibility filter)이므로 **전면 교체**: `methods.tex`(+변형 methods_*), results/discussion, figure 라벨("Window (macOS)"→"Deployed") 포함. 내부 JSON 토큰 `window`/`optimal`은 유지(코드 불변).
   - **no-filter** (= unfiltered baseline)
   - **deployed accessibility filter** (첫 등장 "deployed macOS accessibility filter", 이후 "deployed filter") ← 기존 "Window(s) filter"
   - **individualized filter** ← 기존 "Optimal" / "personalized" (제목 "individualized color correction filter"와 통일; **전 논문·figure·드래프트에서 "personalized"→"individualized"**)

---

## Part 0 — 왜 불일치가 생겼나 (근본 원인)

- live 논문(`main.tex` abstract, `results_v4`, `discussion_v3`)은 exp2를 **deutan 단독**으로 서술하고, `results_v4:189`·`discussion_v3:34`에 **"the protan participant was not collected"**라 명시.
- 그러나 sub-09(protan) exp2는 신경·행동·QC·figure까지 **전부 수집·분석 완료**(6/30–7/5, 디스크 확인).
- 결정적 증거: `discussion_v3:44`에 저자 본인 TODO —
  `% TODO: protan (sub-09) second-session experiment pending --- revisit the "single deutan case" scope when collected.`
- **결론: 부정행위 아님. 논문이 sub-09 수집 이전에 쓰인 stale 상태이고, TODO가 미이행된 것.** 수정 = 미이행 TODO 이행.

### 정정 (제 이전 오류 철회)
- 이전 세션에 저는 "§6.5.2의 SRM-RDM 자기일치도 `V1/V2 = 0.66/0.50`이 stale, 실제는 0.509/0.345"라 주장했음.
- **틀림.** `0.66/0.50`은 `srm_rdm_paper._hc.spearman_self_loo_mean`(V1 0.663 / V2 0.500) — fig8 패널 D가 쓰는 **논문-canonical RDM 자기일치도(SRM공간 Spearman self-LOO)**와 정확히 일치.
- 0.509/0.345는 *다른 estimator*(loo_consistent correlation-RDM)였음. → **§6.5.2는 정확. 정정 대상 아님.**

---

## Part 1 — 문서간 불일치 해소 방안

### 진실 기준 (single source)
- **실측 N=2** = 기준. `exp2_hc_likeness/*`, `exp2_convergent/*`.
- 서술 프레이밍 기준 = **ResearchNOTE §6.5**(2026-07-04 critic-refined). 이미 N=2·3층·금지문구 확정 상태.
- 즉 **논문을 §6.5/실측에 맞추는 방향**. 반대 방향(논문에 맞춤)은 stale를 전파하므로 불가.

### 문서별 현재 상태 → 목표

| 문서 | 현재 exp2 서술 | 불일치? | 조치 |
|---|---|---|---|
| `ResearchNOTE §6.5` | N=2, 3층, 금지문구 | 기준 | **유지** (0.66/0.50 포함 정확) |
| `exp2_neural/RESULTS.md` | N=2 (sub-08+09) | 정합 | 유지 (endpoint correction 헤더 이미 존재) |
| `future_phase4/FINDINGS.md` | N=2 | 정합 | 유지 |
| memory 4건 | N=2 | 정합 | 유지 |
| **`main.tex` abstract** | **deutan 단독** | ❌ | Part 2-A |
| **`results_v4.tex` filter_eval** | **deutan 단독, "not collected"** | ❌ | Part 2-B |
| **`discussion_v3.tex` filter-eval** | **deutan 단독, TODO 미이행** | ❌ | Part 2-C |
| **`METHODS_RESULTS_SUMMARY`** | line 66 1줄(구식) + PV-3 | △ 빈약 | Part 2-D |
| **`fig8_filter_eval`** | deutan 패널만 | ❌ | Part 2-E (2행 재생성) |

### 원칙
1. 세 tex(논문 본문)를 **동시에 N=2로** 고침. 하나만 고치면 abstract↔본문 새 불일치 발생.
2. figure는 본문과 함께 재생성(deutan+protan 2행).
3. §6.5 **금지문구**를 그대로 준수: "개인화 필터가 신경을 HC로 회복", "피험자별 다른 지표 개선을 강점으로" 등 금지.

---

## Part 2 — 수정 방향 + 수정안 (old → new)

### 검증된 핵심 수치 (matched)

**hV4 LOCO adjacent accuracy** — 논문 primary endpoint. chance 0.375, HC 0.46±0.11.

| | NF(baseline) | Window(deployed) | **Optimal(personalized)** |
|---|---|---|---|
| sub-08 deutan | 0.23 | 0.25 | **0.31** (최고, 부분개선) |
| sub-09 protan | 0.14 | 0.19 | **0.06** (최저, d_cc=−3.70) |

→ **primary endpoint에서 두 피험자 정반대.** deutan 개선 / protan 역전.

**hV4 LOCO forward-tuning ρ** — secondary. HC +0.21.
- sub-08: NF −0.27 / Win −0.39 / Opt **+0.18**(≈HC).
- sub-09: NF −0.02 / Win −0.02 / Opt −0.02 (**세 조건 ≈0, 분리 없음**).

**SRM disparity (↓HC), HC V1 0.45 / V2 0.49** · **RDM→HC Spearman (↑HC), HC-self V1 0.66 / V2 0.50** — geometry, V1/V2에서 신뢰(§6.5.1).

| | SRM disp V1 | RDM→HC V1 | 요약 |
|---|---|---|---|
| sub-08 NF/Win/Opt | 0.55 / 0.75 / 0.69 | 0.67 / 0.19 / 0.25 | NF가 HC-like(ceiling), **필터가 멀어짐** |
| sub-09 NF/Win/Opt | 0.76 / 0.63 / 0.62 | 0.25 / 0.49 / 0.30 | NF 왜곡(floor), **양 필터 회복(Win≈Opt)** |

→ geometry도 phenotype-특이. sub-08은 필터로 악화, sub-09는 양 필터로 회복(개인화-특이 아님). 둘 다 **완전 HC 기하 미달**.

**LORO 8-way (신호 보존, chance .125):** V1 — sub-08 NF/Win/Opt 0.79/0.84/0.72; sub-09 0.79/0.91/0.66. **양 피험자·전 조건 chance 훨씬 위** → 색 신호 보존.

**행동 (§6.5.4, HC-disparity):**
- sub-08: 기저 HC-deviant 3쌍 → 양 필터 정상화(|z| 2.24→Win 0.85/Opt 0.78). 8AFC 0.81→0.97 양쪽. Opt vs Win 순위불가(Wilcoxon p=0.84).
- sub-09: 기저 HC-deviant 0쌍. **Window가 protan쌍 왜곡 생성**(green-blue p=.003, cyan-magenta p=.001), Optimal 생성 0. mean|JND−HC| z: NF 0.90 ≈ Opt 0.93 ≪ Win 1.78.
- 통합: HC-disparity에서 **Optimal ≤ Window(양 피험자)**. 단 유의 우월 아님(N=2).

---

### 2-A. abstract (`main.tex:71`) — 전체 재구성

**결정 (2026-07-14):**
- 구조 = 모범초록(Nature Neurosci, `Best_abstract_모범초록.pdf`) **6블록**: Gap → Here we show(finding+framework+goal **병합**) → 특성화(brain-decoding, geometry 뭉뚱) → 필터 method → exp2(1문장 inconsistent) → 의의.
- 필터 명칭 = **"individualized filter"** 전 논문 통일(제목 일치). → 조건 라벨 "Personalized"도 **"Individualized"**로(figure 재라벨 필요).
- 통계·per-subject 세부 삭제. 2AFC 삭제.

**6블록 구조**
1. **Gap**: generic(집단-평균) 필터 한계 + 피질 색표상이 개인별로 다르게 왜곡될 가능성(미지) → 필터 setup.
2. **Here we show**: 피질 색표상 = 신호소실 아니라 **개인별 기하 왜곡** + 이를 **역산해 individualized 필터로** 만들 수 있음(goal "toward HC" 병합).
3. **특성화(brain-decoding)**: cortical decoding → 색 분별 보존하나 **연속 기하 왜곡(개인차)**. (V1/V2·hV4 뭉뚱 = "distorted in cortical geometry")
4. **필터 method**: 2-component 모델 요약 → 해석적 역산 → 모든 hue exact.
5. **exp2**: 두 개인에서 필터 효과 **inconsistent**, HC 기하 미달, decodability 보존; 효능·일반화 미결.
6. **의의**: CVD = 개별 패턴 피질 기하 왜곡, 감각 결손을 자기 표상의 가역 왜곡으로 개인 단위 교정 template.

**NEW 초안 v2 (전체 abstract) — 피드백 반영. ⚠ abstract는 무인용(관례) — 아래 대괄호 인용 마커는 텍스트에 넣지 않고 Introduction에서 인용:**
> Color vision deficiency (CVD) is typically corrected with generic filters designed for a population-average retina, which alter how colors appear but do little to improve discrimination. Yet the cortical color representation that perception reads out is distorted differently in each person, and whether an individualized correction read from each person's own cortex could do better is unknown. Here we show, using fMRI in two adults with CVD, that the cortical representation of color is not reduced in overall signal but individually distorted in its geometry, and that this distortion can be inverted into an individualized stimulus-space correction filter. From brain decoding, both participants still represented all displayed colors --- the chromatic signal was intact --- yet the continuous geometry relating those colors was distorted, differently in each individual. We summarized each person's distortion with a compact two-component cortical model and inverted it into an individualized filter that is exact for every displayed hue. When evaluated in a second session, the filter's effects on the cortical hue representation were inconsistent across the two individuals and did not reach the healthy reference, although categorical color decodability was preserved. Whether the correction improves perception, and whether these patterns generalize, remains open. These findings recast CVD as an individually patterned distortion of cortical color geometry --- a sensory deficit that can, in principle, be read out and corrected individually.

**피드백 반영 요약:**
- **Gap** — NotebookLM 검증 반영: generic 필터가 "appearance만 바꾸고 discrimination 개선 미미"[Somers 2024] + subtype 내 개인차로 group-level 부적절[Bosten 2019; Tian 2022]. (인용은 Intro에서 확장; abstract는 개념만.)
- **Here we show** — "analytically" 삭제 + "designed to move ... healthy observer"(필터의 자명한 목적) 삭제 → 단축.
- **③** — "Decoding hue from cortical responses"(뜬금) → **"From brain decoding"** + "chromatic signal intact / geometry distorted" 대비 강조. *(당신 제안 "From brain-to-hue decoding"은 다소 생경 → "From brain decoding"으로. 원하면 원안 복원 가능.)*
- **⑤** — "In second sessions in both participants"(methods투) → **"When evaluated in a second session"**. *("In evaluation"은 너무 모호해 배제.)*
- "preserved."에서 **문장 끊음** (당신 지적).
- 결말 → **"read out and corrected one individual at a time"** ("corrected" 채택 + "one individual at a time"으로 idiomatic 보정; 당신 "individually at a time"은 어색).

**OLD** = 현재 main.tex:71 전문(deutan 단독 exp2, 장황, 2AFC 포함) — 위 v2로 전면 교체.

**Intro 인용 뒷받침** → 별도 파일 **`INTRO_CITATION_SUPPORT.md`** 참조 (현 intro가 이미 뒷받침; 선택적으로 Tian 2022 추가 제안).

**Downstream 영향 (tex 적용 시):**
- **"personalized filter" → "individualized filter" 전역** — 이 제안서의 2-B/2-C 드래프트 + 기존 results_v4/discussion_v3/methods 모두. (STABLE 규칙 7 갱신)
- **figure 범례 "Personalized" → "Individualized"** 1단어 재렌더(fig8 + figS).
- `results_v4.tex:179` 2AFC 절 삭제("; replication in more individuals remains for future work." 또는 절 삭제).

---

### 2-B. results_v4 filter_eval (`results_v4.tex:189–216`)

#### ✅ 확정 초안 (재구성 · 새 순서: 서두 → 행동 → LORO → 보간 → 기하)

> 반영: 구조 재배열(긍정=행동·전제=LORO 먼저 → 신경 뒤) · naming(deployed/personalized) · forward-tuning ρ→appendix · geometry에 disparity+RDM 수치 · "favored"→"was lower" · d_cc·rendering-confound 유지 · **해석은 Results 아님(§6.3 Discussion)**. 아래 (i)~(vi)는 첨삭 원본(참고용, 이 확정본으로 대체).
> ⚠ "second experiment" 표기 — methods는 "session". 전역 일관성 위해 논문 전체에서 experiment/session 중 택1 필요(별도 결정).

**[서두]** (읽기 순서 signpost; RDM은 geometry의 측정도구로 표기)
> We evaluated the two filters in a second session in both CVD participants, using the same two neural read-outs as the first session: hue interpolation (hV4 LOCO accuracy) and representational geometry (SRM-aligned disparity and RDM). We report, in turn, the behavioral outcome, the discrimination precondition, and the two neural read-outs.

**[행동]** (deutan 개선 foreground + protan green-blue trending 정정 + 긍정표현)
> Behaviorally, both filters improved discrimination in the deutan participant. The baseline deficit (JND mean $|z| = 2.24$; the orange--yellow, yellow--green, and yellow--purple pairs each exceeded the HC maximum) was removed by both the deployed ($|z| = 0.85$) and the personalized ($|z| = 0.78$) filter, neither leaving a significant deviant pair. 8AFC color identification rose from $0.81$ to $0.97$ under both. The two filters could not be ranked (Wilcoxon $p = 0.84$). The protan participant had no significant baseline deviant pair, though one (green--blue, a protan confusion-axis pair) was trending ($p = 0.070$). Under the deployed filter green--blue became significantly deviant ($p = 0.003$) and a second pair appeared (cyan--magenta $p = 0.001$), whereas the personalized filter normalized green--blue ($p = 0.44$) and produced no deviant pair; mean $|$JND$-$HC$|$ (in HC SD units) was lower under the personalized filter (no-filter $0.90 \approx$ personalized $0.93 \ll$ deployed $1.78$). Of the two filters, only the personalized filter introduced no new significant deviation in either participant. Whether it is superior to the deployed filter remains to be established with more participants.

> ✅ **[D] rendering-confound 문장 완전 삭제 (결정).** `future_phase3_behavioral_analysis/CLAUDE.md` §33 정책 철회 완료(2026-07-14): deployed·personalized 모두 동일 층위 모니터 색변환으로 간주 → rendering-stage confound를 논문에 서술하지 않음. 위 행동 문단 말미의 "different rendering stages..." 문장 삭제됨(Limitation 이동도 안 함).

**[LORO — 전제]**
> Color classification survived both filters in both participants. LORO eight-way accuracy stayed well above the $0.125$ chance level at every ROI and in every condition (all cells $\geq 0.50$; HC $0.71$--$0.77$; Table~S\ref{tab:exp2_loro}). The color signal was intact in both.

**Supplementary table 초안 (Table S — exp2 LORO 8-way accuracy):** chance = 0.125.

| ROI | HC | \multicolumn{3}{c}{deutan (sub-08)} | \multicolumn{3}{c}{protan (sub-09)} |
|---|---|---|---|---|---|---|---|
|  |  | no-filter | deployed | personalized | no-filter | deployed | personalized |
| V1 | 0.71 | 0.79 | 0.84 | 0.72 | 0.79 | 0.91 | 0.66 |
| V2 | 0.71 | 0.79 | 0.69 | 0.62 | 0.83 | 0.75 | 0.72 |
| V3 | 0.77 | 0.67 | 0.78 | 0.69 | 0.81 | 1.00 | 0.69 |
| hV4 | 0.75 | 0.73 | 0.88 | 0.50 | 0.71 | 0.84 | 0.69 |

**[보간]**
> For color interpolation (LOCO decoding), the two participants gave opposite results. In the deutan participant, the personalized filter partially improved adjacent accuracy (no-filter $0.23 \to$ personalized $0.31$; HC $0.46 \pm 0.11$), whereas the deployed filter did not (deployed $0.25$). The accuracy stayed below both the HC level and the $3/8$ chance threshold ($d_{cc} = -1.35$ vs.\ HC; deployed $d_{cc} = -1.94$). In the protan participant the trend reversed. Interpolation accuracy under the personalized filter was below the unfiltered baseline (no-filter $0.14$, deployed $0.19$, personalized $0.06$; personalized $d_{cc} = -3.70$), the lowest of the three conditions. The personalized filter thus improved interpolation in the deutan participant only, and the effect did not replicate in the protan participant.

**[기하]** (disparity + RDM 수치; "neither"·"increased the difference" 반영; 해석문 §6.3)
> Neither filter fully restored the representational geometry to the HC level, and the two participants moved in opposite directions. In the deutan participant the unfiltered baseline was the closest to HC of the three conditions, while both filters increased the difference from HC (V2 SRM disparity no-filter $0.72 \to$ deployed $0.84$ / personalized $0.77$, HC $0.49$; V2 RDM similarity to HC no-filter $0.57 \to$ deployed $0.15$ / personalized $-0.13$, HC-self $0.50$). In the protan participant the unfiltered baseline was the most distorted of the three, while both filters reduced the difference from HC (V1 SRM disparity no-filter $0.76 \to$ deployed $0.63$ / personalized $0.62$, HC $0.45$; V1 RDM similarity no-filter $0.25 \to$ deployed $0.49$ / personalized $0.30$, HC-self $0.66$). This protan recovery was comparable between the two filters, so it was not specific to the personalized filter.

> *(geometry ROI = 각 피험자 affected ROI: sub-08 **V2** / sub-09 **V1** — exp1/Fig2와 일치. figure는 전 ROI 표시.)*

**[caption]** "Second-session filter evaluation in both CVD participants. Filter effects on hV4 interpolation **differed between the two participants** (deutan improved, protan reversed); neither filter reproduced an HC-like color geometry." · "Single case per subtype, descriptive." (규칙 3: "individual-specific"(효과) 회피 → "differed"; "personalized filter:" 제거.) forward-tuning ρ → appendix figure.

**[forward-tuning ρ]** → appendix (본문 secondary 문단 삭제).

---

<details><summary>아래 (i)~(vi): 첨삭 원본 (참고용 — 위 확정본으로 대체됨)</summary>

#### (i) primary — :189 전체 교체

**OLD** (요지): deutan만. "protan not collected". personalized 0.23→0.31 partway, deployed 0.25.

**NEW**
> We evaluated the personalized filter in second sessions[Change: experiment] in both CVD participants. The primary endpoint was the metric validated in Session~1: hV4 LOCO adjacent accuracy. [Change: We evaluated with identical metrics with the first experiment: hV4 LOCO decoding accuracy and SRM RDM] This was the only ROI where HC interpolation exceeded chance. [Delete - check whether already written in the first result] The two participants gave opposite results. In the deutan participant, the personalized filter moved [Change: moved -> partially improved] interpolation partway [Change: partway -> accuracy] toward the HC reference (baseline $0.23 \to$ personalized $0.31$; HC $0.46 \pm 0.11$). The deployed macOS accessibility filter did not (deployed $0.25$). This recovery was partial. [Delete: partial is in the previous sentence] It [Change: It -> The accuracy] stayed below both the HC level and the $3/8$ chance threshold ($d_{cc} = -1.35$ vs.\ HC; deployed $d_{cc} = -1.94$) [Delete: 괄호 필요?]. 

[+ 여기에 representational geometry 추가하기, 구체적인 통게값 추가하기, The personalized filter ~ than either 지우기]

> In the protan participant, the ordering [Change: ordering -> trend - as SRM RDM is included] reversed. The personalized filter did not restore interpolation. It drove interpolation below the unfiltered baseline (baseline $0.14$, deployed $0.19$, personalized $0.06$; personalized $d_{cc} = -3.70$ vs.\ HC). [Change: Interpolation accuracy under filter condition was below the unfiltered baseline 으로 + d_cc가 필요할까요?] This was the lowest of the three conditions. The personalized filter thus improved the primary index in the deutan case only, and the effect did not replicate in the protan case.

[+ However, under both filter, representational geometry moved V1/V2 geometry toward HC. This protan recovery was not specific to the personalized filter: the deployed and personalized filters were comparable (Window $\approx$ Optimal).]

[Discuss: 해석을 어디에 넣을지 고민 + sub 별로 두 결과를 동시에 제시할지, 결과별로 따로 제시할지도 고민]

#### (ii) secondary — :191 끝에 protan 문장 추가

deutan 서술(현행)은 유지. 마지막 문장 앞에 삽입:

> In the protan participant, this secondary index did not separate the conditions. At hV4 all three were near zero (baseline $-0.02$, deployed $-0.02$, personalized $-0.02$), so the deutan corroboration did not generalize.

[Change: voxel prediction은 appendix로]

#### (iii) LORO — :211 "both participants"로 확장

**OLD**: "...the second-session color signal was intact." (deutan 함축)

**NEW**
> Color decodability survived both filters in both participants. LORO eight-way classification stayed far above the $0.125$ chance level in every condition (e.g. V1 $\approx 0.66$--$0.91$; HC $\approx 0.79$). The second-session color signal was intact in both.

[Change: e.g. 보다 모든 ROI 명시 + 2명 * 4 ROI니까 모두 제시 가능함]

#### (iv) geometry — :213 per-subject 분기

**OLD** (요지): "no-filter baseline had the lowest disparity", "neither filter more HC-like than no filter", deutan 서술.

**NEW**
> Representational geometry was not fully restored to the HC level by either filter, in either participant. The two participants differed in direction, however. In the deutan participant, the unfiltered baseline was already the most HC-like (lowest V1/V2 SRM disparity, highest RDM similarity), and both filters moved the geometry away from HC. 

> In the protan participant, the unfiltered baseline was the most distorted, and both filters moved V1/V2 geometry toward HC. This protan recovery was not specific to the personalized filter: the deployed and personalized filters were comparable (Window $\approx$ Optimal). Because early areas encode the physical stimulus, a recolored stimulus is expected to reshape V1/V2 geometry; this measure is therefore not the bar a corrective filter must clear.

#### (v) behavioral — :215–216 both participants

**OLD**: deutan만.

**NEW**
> Both filters improved behavior in the deutan participant. The baseline deficit (JND mean $|z| = 2.24$; orange--yellow, yellow--green, and yellow--purple pairs exceeding the HC maximum) was removed by both the deployed ($|z| = 0.85$) and the personalized ($|z| = 0.78$) filter. 8AFC accuracy rose from $0.81$ to $0.97$ under both. The two filters could not be ranked (Wilcoxon $p = 0.84$).
>
> The protan participant showed no baseline deviant pair. Here the deployed filter introduced new deviations (green--blue and cyan--magenta, both $p < .01$), whereas the personalized filter introduced none. Mean $|$JND$-$HC$|$ favored [Change: favored is not academic vocabulary] the personalized filter ($z$: no-filter $0.90 \approx$ personalized $0.93 \ll$ deployed $1.78$).
>
> Across both participants, the personalized filter was the only condition that introduced no new behavioral deviation, and it was no worse than the deployed filter on HC-disparity. It was not, however, significantly superior (N=2). [Change: 효과크기 제시를 앞 문장에서 가능성을 위해 제시, 이후에 N=2이기 때문에 statistical significancy를 주장할 수 없다로 명시] The single-session, cross-session design with a shared-pipeline confound precludes a behavioral ranking. [Delete: 이 문장 필요할까요?]

*(주: 이 문단은 "Optimal 우월"이 아니라 "Optimal 안전/무해" 주장 — 규칙 5의 "행동=프레임워크 가능성" 근거. 정량 개선 주장 아님.)*

#### (vi) caption — :196 title 중립화

**OLD**: "The personalized filter partially restores hue interpolation toward HC but not an HC-like color geometry (the deutan participant, second session)."

**NEW**: "Second-session filter evaluation in both CVD participants. Filter effects on hV4 hue interpolation were individual-specific (personalized filter: deutan improved, protan reversed), and neither filter reproduced an HC-like color geometry."
- "Single subject, descriptive"(:206) → "Single case per subtype, descriptive."
- fig8 = 2행(deutan/protan) 재생성 필요 → Part 2-E.

</details>

---

### 2-C. discussion_v3 filter-eval (`discussion_v3.tex:33–44`) — §6.3

**방향**: 소제목 "Filter evaluation in the deutan case" → **"Filter evaluation"**. **:44 TODO 삭제.** forward-tuning ρ 언급 appendix로. 기존 :34/:36 문단을 아래 3 para로 교체.

#### 2-C(해석·초안 확정). §6.3 filter-eval Discussion — 전체 초안 (첨삭 반영)

> 반영: 첨삭 대로 "behaved as intended"·"controversial"·"helped"·deployed-우위 제거. "controversial"→"inconsistent improvement"(의미 정정, 부정표현 회피하되 방향 ↑/↓ 명시). 문장 분할. "Session-1" 표기 제거(공통 metric). placement=§6.3 서두. naming=deployed/personalized.

**[para 1 — 해석 서두: 두 도메인 분기]**
> The two evaluation domains diverged. Behaviorally, the personalized filter normalized the deutan participant's baseline discrimination deficit and introduced no new deviation in the protan participant. However, it did not outperform the deployed accessibility filter in the deutan participant. A behavioral benefit of the personalized filter over the deployed filter remains to be evaluated. Neurally, the filter produced an inconsistent improvement. On the interpolation metric it increased adjacent accuracy in the deutan participant ($0.23 \to 0.31$) but decreased it in the protan participant ($0.14 \to 0.06$), and it reproduced a control-like geometry in neither. Filter efficacy therefore remains unproven and is the framework's immediate next test.

**[para 2 — 기하 해석: V1/V2와 hV4는 다른 층위]**
> Neither filter reproduced the full control geometry, and the two participants moved in opposite directions. In the deutan participant the unfiltered baseline was the closest to HC of the three conditions, and both filters moved the geometry away from it. In the protan participant both filters moved the distorted baseline toward the controls, but comparably (deployed $\approx$ personalized), so the shift was not specific to the personalized filter. This early-visual geometry and the hV4 interpolation read-out lie at different levels of the visual hierarchy. Early areas encode the physical stimulus, so a recolored stimulus necessarily reshapes V1/V2 geometry, whereas hV4 reflects a later, perceptual stage. The two levels therefore need not change together, and their divergent filter effects are consistent with this hierarchical difference.

**[para 3 — 스코프 closer]** (next-step: 추가 피험자만; 2AFC 삭제)
> This evaluation rests on one deutan and one protan case. The primary-endpoint effect appeared in the deutan participant and reversed in the protan participant. Whether either pattern generalizes cannot be determined from two cases; replication in more individuals, within each subtype, is the primary requirement.

**[구조]** 소제목 "Filter evaluation in the deutan case" → **"Filter evaluation"**. **:44 TODO 주석 삭제.** 위 3 para로 기존 :34/:36 문단 교체(forward-tuning ρ 언급은 appendix로 이동).

#### 2-C(한계). Limitations에 5번째 항목 추가 (규칙: 사실 정정판)

> ⚠ 재정정 (사용자 지적): LOCO는 "gate-only(설계상 제외)"가 아니라 **후보 fitting 항이었으나 선택에서 탈락**(results_v4:110 "For neither participant did the LOCO loss family enter the selected combination"). 탈락 사유 추정 = hV4 채널공간·복셀 수 차이로 인한 통합 미비. basis-dependence(SRM/PCA) 혼입 제거.

**NEW** (Discussion Limitations, 기존 4개 뒤 5번째)
> A further limitation concerns the fitting objective. The interpolation (LOCO) signature was included among the candidate fitting terms, but for neither participant did it survive model selection; both winning combinations were the behavioral JND loss plus the neural $\Delta$RDM. The LOCO atom is defined in a forward-encoding channel space at hV4 --- a smaller voxel set on a different representational basis than the RDM --- which may have made it difficult to integrate stably with the geometry loss. As a result, the fitted filter is not directly optimized on the interpolation deficit. A loss that stably incorporates the interpolation signature alongside the geometry is left to future work.

*(정정: LOCO는 후보였으나 미선택. 탈락 원인은 채널공간·복셀수 차이로 인한 통합 미비로 추정 — 단정 아님. exp2 신경 미개선의 부분적 원인까지 정직하게 연결.)*

---

### 2-D. METHODS_RESULTS_SUMMARY (`analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`)

- **line 66** `- Exp2 (deutan only): Wilcoxon p=0.84; 8AFC 0.81 → 0.97` →
  `- Exp2 filter validation: N=2 (sub-08 deutan, sub-09 protan), 단일 세션·4 runs/조건 → descriptive only. 상세 = 아래 exp2 블록 · exp2_neural/RESULTS.md · ResearchNOTE §6.5.`
- **신규 블록**(line 59 뒤): §6.5 3층 + primary 역전표 + geometry 분기 + 금지문구. (2-B 수치 사용, 압축판)
- **PV-3**: "재프레이밍 ✅ 완료(2026-07-14). 잔여: 사전등록 target metric + 추가 피험자/촬영."

---

### 2-E. fig8 재생성 (승인 시)

- `docs/PAPER/Figures/scripts/generate_fig8.py`: 현재 sub-08만 로드(2×2 A–D).
- 변경: **2행(deutan 위 / protan 아래) × 4열(A–D)** 또는 각 패널 subject 병기. sub-09 JSON 구조 동일 확인됨.
- `--variant matched` 재실행 → `fig8_filter_eval.{png,pdf}` 갱신. PSYCH_THESIS 사본도 동기화 검토.

---

## Part 3 — 참조 원고: ICML 워크샵 camera-ready

**포인터**: `docs/ICML_workshop/SD4H_cameraready_pathB_0624_A.pdf`
(제목: *Inferring Individualized Color-Vision Distortions from fMRI Hue-Representation Geometry*. ICML 2026 SD4H workshop. Kim, Cho, Seo, Cha.)

### 스코프 경계 (중요)
- ICML 원고는 **진단 → 2-Comp 피팅 → 필터 역산까지만** 다룸. **exp2(필터 검증)는 의도적으로 제외.**
- Abstract: "whether it improves perception is the framework's **defined next test**."
- Limitations: "we have **not shown** that the correction improves perceptual discrimination; a behavioral advantage and broader validation **remain to be established**."
- → **exp2 결과 문구의 직접 템플릿 아님.** 아래 3개 용도로만 참조.

### 차용할 것
1. **N=2 완전 대칭 서술 형식.** Sub-08(deutan)·Sub-09(protan)를 Table 1·Fig 3·본문에서 대칭 취급. main paper의 exp2를 이 형식으로.
2. **proof-of-concept + descriptive 한계 문장.** "single-case (N=2)", "mechanism-class = sign quadrant, not magnitudes", "0/3 null 통과", "per-axis floor ~20°/25°" 등 정제된 표현 톤 차용.
3. **일관성 앵커.** distortion·filter-derivation 쪽 수치(Sub-08 V2 p=0.040 / Sub-09 V1 p=0.007; baseline hV4 0.25/0.13; (βs,βc) (+6,−42)/(+2,+24); mean|δθ| 26.3/16.2)는 이 원고와 **일치해야** 함.

### 정합성 체크 포인트
- **baseline 표기 차이**: ICML hV4 baseline = Sub-08 0.25 / Sub-09 0.13 (**n6-full**). exp2 문서 = 0.23 / 0.14 (**n4-matched**, HC와 run수 정합). 모순 아님. 두 논문 나란히 인용 시 각주로 n6 vs n4 명시.
- **primary endpoint 반전은 ICML엔 없음**: ICML은 exp2 미포함이라 반전을 언급 안 함. main paper가 exp2를 넣는 순간 반전(Part 2-B(i))을 반드시 함께 서술해야 공개기록과 모순 안 됨.

### 전략적 시사 (검토 요청)
ICML은 공개 camera-ready에서 **"필터 검증 = 다음 과제, 아직 미제시"**로 커밋함. main paper가 exp2를 넣고 "personalized 필터 부분복원"을 주장하면 **워크샵 기록보다 강한 주장**이 됨. protan 반전을 고려하면, main paper의 exp2 톤을 **ICML 수준(예비적·미결)에 근접**시키는 것이 정합적 선택지. → Part 2 초안이 이미 그 방향("did not replicate", "hypothesis-generating")이나, 더 낮출지(예: exp2를 결과가 아닌 "preliminary validation, inconclusive"로) 판단 필요.

---

## 적용 순서 (승인 후)
1. 세 tex 동시(2-A/B/C) → 2. fig8 재생성(2-E) → 3. 위성(2-D) → 4. 컴파일 확인.
2-C 전체 문단은 2-B 문구 확정 뒤 작성(중복 방지).
