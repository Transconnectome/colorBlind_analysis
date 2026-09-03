# 투고 실행 TODO — Imaging Neuroscience (MIT Press) · 2026-09-01

> **근거**: Imaging Neuroscience *Guide for Authors*. **원문 페이지(`https://direct.mit.edu/imag/pages/guide_for_authors`) 직접 접근 실패 (WebFetch → HTTP 403).** 따라서 본 문서의 가이드 조항은 **사용자 제공 원문 발췌를 기준**으로 한다. 발췌에 없는 조항(예: Appendix 를 본문 어느 위치에 두는지, Supplementary 의 조판 시점 세부)은 「미확인」으로 표기했다.
>
> **대조 대상**: `main.tex`(2026-09-01 기준 274행), [`SUBMISSION_CHECKLIST_IMAGING_NEURO.md`](SUBMISSION_CHECKLIST_IMAGING_NEURO.md)(rev.5, 2026-08-17), [`COVER_LETTER_DRAFT.md`](COVER_LETTER_DRAFT.md), [`REVIEWER_SUGGESTIONS_DRAFT.md`](REVIEWER_SUGGESTIONS_DRAFT.md).
>
> **이 문서의 범위**: 저자 가이드 **조항별 실행 단위**만 다룬다. 형식·행정 요건의 전체 판정은 `SUBMISSION_CHECKLIST_IMAGING_NEURO.md` 가 정본이고 이 문서는 그것을 대체하지 않는다 — 완료 항목은 그 체크리스트의 해당 행을 근거로 인용만 한다. **원고 본문 문안 수정은 [`MANUSCRIPT_EDITS_CONSOLIDATED.md`](MANUSCRIPT_EDITS_CONSOLIDATED.md) 가 정본**이므로 여기에 옮겨 적지 않고 참조만 한다.
>
> 등급: **완료** · **진행 필요**(투고 자체를 막지는 않음) · **투고 차단**(해소 전 제출 불가)

---

## 0. 요약 — 지금 투고를 막고 있는 것

| 등급 | 개수 | 항목 |
|---|---|---|
| **투고 차단** | **4** | ~~A1 AI 진술~~ ✅ · ~~A2 Funding~~ ✅ · A3 코드 공개 저장소 미생성(URL·DOI 미확정) · A4 커버레터 블록 1·2 미작성 + 블록 4 재작성 · A5 심사자 충돌 확인 · A6 Editorial Manager 계정 |
| 진행 필요 | 4 | ~~B1 말미 절 순서 재배열~~ ✅ (2026-09-01) · B2 키워드 재검토 · B3 공저자 승인·CC BY 동의 · B4 `\todo` 해소(**AI 도구 버전 · Funding 과제번호 2건 추가**) · B5 최종 재빌드 |
| 완료 | 8 | 제목·초록·저자/교신 정보·본문 순서·절 번호·Appendix 분량·CRediT·이해충돌·윤리 진술 |

> **✅ 2026-09-01 반영: A1 · A2 해소.** `main.tex` 에 `\section*{Declaration of the use of AI}` 를 말미 절 **첫머리**(`Data and Code Availability` 앞)에 신설하고, Acknowledgements 뒤에 라벨 없이 붙어 있던 옛 문단과 그 주석 블록을 삭제했다. Funding 문안도 확정본으로 교체했다. 남은 것은 아래 Q1·Q2 의 `\todo` 두 건이며 **투고 차단은 아니다**. 아울러 `ImagingNeuro_cha.pdf`(본 저널 게재 논문) 의 배열을 따라 **Ethics 를 Funding 앞으로** 옮겼다. 현재 순서 = AI → Data and Code Availability → Author Contributions → Ethics → Funding → Competing Interests → Acknowledgements.

~~**가장 위험한 한 건은 A1 이다.**~~ `main.tex:245-250` 의 현행 AI 문장은 `No figure, text, statistical result, or numerical value in this article was produced by an AI tool` 라고 단언하는데, 사용자가 확정해 준 실제 사용 범위에는 **초고 문장 다듬기(reword)** 가 포함된다. 즉 현행 문장은 **가이드가 요구하는 공개를 하지 않을 뿐 아니라 사실과 다른 진술**이며, 이 상태로 제출하면 MIT Press 윤리 규정 위반에 해당한다.

> 별건이지만 함께 걸린다 — 체크리스트 §10.3 이 🔴 로 올린 **X1**(`Supplementary/supplementary.tex:46` 의 사실과 다른 문장, `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:315-319`)은 형식이 아니라 본문 내용 오류이고 `MANUSCRIPT_EDITS_CONSOLIDATED.md` 가 정본이다. 본 문서는 그 항목을 다루지 않으나, **최종 빌드 전에 해소되어야 한다는 점만 여기 기록한다.**

---

## 1. 가이드 조항 → 현재 상태 → 해야 할 일

### 1.1 말미 절 (Back matter)

| # | 가이드 조항 (발췌) | 현재 상태 | 등급 | 근거 | 해야 할 일 |
|---|---|---|---|---|---|
| ~~A1~~ ✅ | 말미에 독립된 절 **"Declaration of the use of AI"** 를 둘 것. 연구의 기획·수행에서 AI 가 한 역할, 사용 도구와 **버전 번호**, 그림 생성에서의 역할을 기술 | **절이 존재하지 않는다.** AI 문장은 `Acknowledgements` 절 안에 제목 없는 문단으로 붙어 있고, 내용도 `코딩 보조만` 으로 좁게 적혀 있어 실제 사용 범위(reword·맞춤법/문법·코드 검증)와 어긋난다. 도구명·버전 번호 없음 | **투고 차단** | `main.tex:227-250` (Acknowledgements 227행, AI 문단 245-250행). 체크리스트 B7 도 ❌ 로 기록: `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:206`, D4b: 동 `:299` | §2.1 의 영문 초안으로 **`\section*{Declaration of the use of AI}` 를 신설**하고 Acknowledgements 안의 현행 문단을 삭제. 절 위치는 §4 대조표에 따라 back matter **최상단**(Data and Code Availability 앞). 도구명·버전은 사용자 입력(§3 Q2) |
| ~~A2~~ ✅ | Funding 정보를 준비할 것 (말미 절, 선택) | 절은 있으나 문안이 사용자 확정본과 **다르다** — 현행은 `Independent Research Support Program of the College of Liberal Studies` 단일 지원처, 사용자 확정본은 **지원 2건**(2025 SNU Student-directed Education Undergraduate Research Program / 2026 Undergraduate Social Science Research Grant) | **투고 차단** | `main.tex:198-206`. 체크리스트는 이 절을 ✅ 로 기록하고 있으나(`:252`, `:297` D3) 그 판정은 구 문안 기준이므로 **이 항목에서 무효화된다** | §2.2 의 문안으로 `main.tex:200-201` 을 교체. 함께 `main.tex:182-183` 의 주석(`the award is a university undergraduate programme` — 단수 전제)과 `:202-206` 의 출처 주석도 2건 기준으로 갱신 |
| **A3** | **Data and Code Availability** — 데이터나 코드를 쓴 이상 필수 | 절은 완성되어 있고 데이터 제한 사유·접근 절차까지 IN 이 허용하는 형태로 기술됨. 단 **코드 URL 이 분석 리포지토리(`Transconnectome/colorBlind_analysis`)로 하드코딩**되어 있고 Zenodo DOI 가 `\todo` 로 비어 있다 | **투고 차단** | `main.tex:131-164`(URL 134행, `\todo` 135-137행). 체크리스트 B1 ✅ `:165`, 6.1 ⚠ `:166`, W6 ⚠ `:191`, R1/R3 `:350,352` | 아래 §1.1a 참조 |
| **A4** | **Author Contributions** 필수 | 4인 전원 CRediT 역할 확정, IN 게재 서식(이니셜·세미콜론) 준수 | 완료 | `main.tex:166-196`. 체크리스트 B2a ✅ `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:88` | 없음. 단 체크리스트 §10.2 D2(공저자 2인 역할 회신)가 미해소로 남아 있으므로(`:296`) 회신본과 대조 1회 |
| **A5** | **Declaration of Competing Interests** 필수 | 실문장 작성 완료(특허 미출원·상용 안경/디스플레이 업체 무관 명시) | 완료 | `main.tex:208-214`. 체크리스트 B2b ✅ `:90` | 없음 |
| **A6** | Acknowledgements (선택) | 절은 있으나 `\todo{[CONFIRM]}` 이 남아 빨간 글자로 조판된다 | 진행 필요 | `main.tex:227-232` | 비저자 기여 확인 후 `\todo` 제거 (§3 Q5) |
| **A7** | Supplementary Material — 제작 단계에서 온라인 자료 링크로 생성 | 1차 제출용 단일 PDF 안에 `\section*{Supplementary Methods}` 로 포함, 본문 절 번호는 받지 않음 | 완료 | `main.tex:270-272`. 체크리스트 W3 ✅ `:109` | 없음(개정 단계에서 별도 파일 분리는 체크리스트 W3 이 이미 기록) |
| **A8** | (가이드 발췌에 없는 절) | `Ethics` 절이 Competing Interests 와 Acknowledgements 사이에 추가되어 있다 | 진행 필요 | `main.tex:220-225`. 근거: 게재 논문 2편의 house practice, 체크리스트 `:288` | 유지 판단은 이미 문서화되어 있다. **가이드 권장 배열에 없는 절이므로 §4 대조표에서 위치만 확정**하면 된다 |

#### 1.1a A3 — 코드 저장소 판정, 체크리스트와의 어긋남

**사용자 확정 사항**: 코드는 공개하되 그 저장소는 **이 분석 리포지토리가 아니라 논문 공개용 별도 저장소**다.

**체크리스트와 대조한 결과, 어긋나는 항목이 4개 있다.** 체크리스트 §6 은 전부 현재 분석 리포지토리를 전제로 쓰여 있다.

| 체크리스트 항목 | 원문 | 어긋나는 지점 |
|---|---|---|
| W6 (`SUBMISSION_CHECKLIST_IMAGING_NEURO.md:191`) | `https://github.com/Transconnectome/colorBlind_analysis` 의 **public/private 여부 확인 필수** … 공개 시 I4(Methods 중복본 참가자 수 상충)가 그대로 노출된다 → 공개 전 정리 | **별도 저장소로 가면 이 항목의 전제가 사라진다.** 분석 리포지토리를 공개할 이유가 없어지고, I4 노출 위험도 별건이 된다. 대신 **별도 저장소에 무엇을 담을지**가 새 결정사항이 된다 |
| R1 (동 `:350`) | GitHub repo **public 전환** 확인 | `전환`이 아니라 **신규 생성**이다 |
| B1 (동 `:165`) | `main.tex` 의 Data and Code Availability 절 = **해소 ✅** | 절 구조는 해소되었으나 **URL 이 잘못 가리키고 있다.** 이 판정은 URL 교체 전까지 부분 유효 |
| 6.1 (동 `:166`) | 코드: GitHub 공개 전환 + release 를 Zenodo 에 연결해 DOI 발급 | Zenodo 연동 대상이 **신규 저장소**로 바뀐다 |

**해야 할 일 (순서 고정)**

1. 논문 공개용 저장소를 새로 만들고, `main.tex` 가 약속한 범위 — *"All analysis and preprocessing code needed to reproduce the reported results"* (`main.tex:133`) — 를 실제로 담는다. 담을 대상의 판단 근거는 `repro/` 및 각 phase 폴더이며, **무엇을 넣을지는 사용자 결정 항목**(§3 Q3)이다.
2. 저장소를 public 으로 두고 **1차 제출 시점에 심사자·에디터가 접근 가능**한 상태로 만든다(체크리스트 W6 의 요구는 저장소가 바뀌어도 그대로 살아 있다).
3. release 태그 → Zenodo 연동 → DOI 발급.
4. `main.tex:134` 의 URL 을 신규 저장소로 교체하고, `:135-137` 의 `\todo` 를 실제 DOI 문장으로 대체.
5. 가이드가 요구하는 **본문 인용 + 참고문헌 등재**(체크리스트 6.2, 동 `:168`)를 위해 `bibliography.bib` 에 software entry 를 추가하고 Data and Code Availability 절에서 인용.

**데이터 측은 손대지 않는다.** IRB 제약으로 공개 불가라는 판정과 그 근거(계획서·동의서 원문 대조)는 체크리스트 §6.4(`:171-190`)에 확정되어 있고, `main.tex:147-164` 의 제한 문안은 IN 이 열거한 허용 사유 4개 중 3개에 정확히 대응한다. **어긋나는 부분 없음.**

### 1.2 본문 구성

| # | 가이드 조항 (발췌) | 현재 상태 | 등급 | 근거 |
|---|---|---|---|---|
| C1 | Title / Authors / Affiliations / Corresponding author information / Abstract(**단일 문단**) / Keywords | 전부 존재. 초록은 단일 문단 234 단어 | 완료 | `main.tex:75,82-89,97,99-101`. 체크리스트 3.1 ✅ `:101`, B4 ✅ `:84`, P2 ✅ `:336` |
| C2 | Introduction → Methods → Results → Discussion and/or Conclusions | 순서대로 `\input` | 완료 | `main.tex:104,107,110,113`. 체크리스트 3.2 ✅ `:102` |
| **B2** | 키워드/구를 **최대 6개** | 5개 — 상한 내 | 진행 필요 | `main.tex:97`. 체크리스트 2.2 `:78` 이 **제목을 T4 로 바꾸면 `hue geometry`·`single-case` 반영 검토**를 조건으로 달아 두었고, **제목 교체는 2026-09-01 에 완료되었다**(동 `:335` P1 ✅). 즉 이 조건은 지금 발동 상태다 → 키워드 1회 재검토 후 확정 |
| C3 | Appendix 는 본문 일부로 조판되며 **최종 조판 PDF 기준 최대 2쪽**(≈1500 단어, 그림·수식 있으면 그보다 적음) | `Results/appendix_alternative_models.tex` = 335 단어 | 완료 | 체크리스트 3.6 ✅ `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:106`, 분량표 동 `:233` |
| C4 | Appendix 의 **본문 내 위치** | 현재 `\printbibliography` **뒤**에 배치 (`main.tex:263-264`) | **미확인** | 사용자 제공 발췌는 "본문의 일부로 조판된다"고만 적고 References 와의 전후 관계를 명시하지 않는다. → 가이드 원문 또는 게재 논문 1편에서 Appendix–References 순서를 확인할 것 |

### 1.3 투고 시스템 입력물

| # | 가이드 조항 (발췌) | 현재 상태 | 등급 | 근거 / 해야 할 일 |
|---|---|---|---|---|
| **A4'** | 1차 투고 시 **짧은 커버레터**, significance 와 저널 적합성 언급, **자기 세부 전공이 아닌 편집자를 수신자로 상정** | 4블록 중 블록 3(선행 발표 고지) 완료. **블록 1(scope·significance)·2(요약) 미작성**, 블록 4(AI 진술)는 **본문 A1 과 함께 재작성 필요** | **투고 차단** | `COVER_LETTER_DRAFT.md:4-9`(블록 정의), `:31`(블록 3 확정본), `:75`(블록 4 초안 B — **현행 본문과 같은 좁은 문안이라 폐기 대상**). 체크리스트 B5 🟡 `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:75`. 블록 1 은 체크리스트 §1.1(동 `:42-67`)의 4단 논증 + IRB 비임상 판정을 그대로 쓴다 |
| **A5'** | 잠재적 심사자 **최소 5인** | 후보 7인 초안 완료, **충돌 확인 C1–C4 미수행** | **투고 차단** | `REVIEWER_SUGGESTIONS_DRAFT.md:26-33`(후보), `:43-48`(확인 절차). 체크리스트 B6 🟡 동 `:79`. IN 문언: 충돌 심사자 지정 시 **심사 없이 반려 + 재투고 불가**(`REVIEWER_SUGGESTIONS_DRAFT.md:5`) → 확인 전 제출 금지 |
| **A6'** | Editorial Manager 제출 | 계정 없음 | **투고 차단** | 체크리스트 4.4 ❌ `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:122` |
| **B3** | (가이드 전제) 전 공저자 승인 · CC BY 동의 | 3인 회신 미수령 | 진행 필요 | 체크리스트 W10 ⚠ 동 `:85`, D5 동 `:300` |
| D1 | **프리프린트(arXiv·bioRxiv) 공개는 허용·권장** | 미공개. 커버레터 블록 3 이 `no preprint has been posted` 로 진술 | 진행 필요 | `COVER_LETTER_DRAFT.md:31` 마지막 문장. **공개 여부는 사용자 결정**(§3 Q4) — 공개하면 커버레터 그 문장을 함께 고쳐야 한다 |
| **B5'** | (제출물) 단일 PDF, 그림·표 인라인, 페이지 번호, 줄 번호 | 형식 요건 충족. **단 `main.pdf` 는 2026-08-18 빌드로 그 이후 제목·초록 교체가 반영되지 않았다** | 진행 필요 | 체크리스트 4.1–4.3 `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:117-120`, S5 동 `:363`. 위 A1–A3 반영 후 최종 재빌드 |
| **B4'** | (조판) 색상 글자 금지 | `\todo` 2건이 빨간 글자로 남아 있다 | 진행 필요 | `main.tex:135`(Zenodo DOI), `:231`(Acknowledgements 확인). 체크리스트 5.3 주의 동 `:133` |

---

## 2. 즉시 붙여넣을 수 있는 영문 문안

### 2.1 Declaration of the use of AI

**채울 곳**: `<도구명 vX.Y>` 3곳. **가이드가 버전 번호를 명시적으로 요구하므로 도구 이름만으로는 요건 미충족이다** — 사용 시점에 그 도구가 표시하던 제품명과 버전(예: 대화형 어시스턴트라면 모델/제품 버전, 편집 도구라면 애플리케이션 버전)을 그대로 적는다. 세 곳에 같은 도구를 썼다면 같은 문자열을 반복해 넣는다.

```latex
\section*{Declaration of the use of AI}

Artificial intelligence tools played no part in the conception, design, or
execution of the research itself. The study design, the data collection, the
analyses, the statistical tests, and every numerical value reported in this
article were produced by the authors and by the analysis code released with the
paper. We used AI-based assistants at three points in preparing the manuscript.
First, we used <도구명 vX.Y> to reword draft text that the authors had already
written; the authors reviewed every resulting sentence and are responsible for
its content. Second, we used <도구명 vX.Y> to check spelling and grammar. Third,
we used <도구명 vX.Y> to review the analysis code for correctness; the authors
verified the code, and every reported number was regenerated by running it. No
figure or figure panel in this article was generated by an AI tool: all figures
were produced by the analysis and figure-generation scripts released with the
paper, and the composite figures were assembled by hand from those outputs. The
authors take full responsibility for the content of this article, including any
part prepared with the assistance of these tools.
```

**이 문안이 가이드의 세 요구를 어떻게 덮는가** — ① 연구 수행에서의 역할: 첫 두 문장이 "없음"을 명시하고 무엇이 저자 산출물인지 열거한다. ② 도구와 버전: 세 용도마다 개별 자리표시자를 둔다. ③ 그림 생성에서의 역할: 마지막에서 두 번째 문장이 "없음" + 검증 가능한 근거(공개 스크립트)를 함께 진술한다.

**함께 처리할 것 세 가지.** (1) `main.tex:245-250` 의 기존 문단을 **삭제**한다 — 남겨 두면 같은 PDF 안에 상충하는 두 진술이 생긴다. (2) `main.tex:234-244` 의 주석 블록도 갱신한다. 그 주석은 `Scope as of 2026-08-18: coding assistants only` 로 적혀 있어 새 문안과 어긋난다. (3) **커버레터 블록 4 를 같은 문안으로 교체**한다 — MIT Press 규정과 `COVER_LETTER_DRAFT.md:83`("본문과 커버레터 문안을 다르게 쓰지 말 것") 양쪽의 요구다.

**Figure 1 관련 주의.** 과거 Figure 1 은 AI 이미지 생성물이었으나 `generate_fig1_v3.py` 로 재작성되어 원고에서 사라졌다(체크리스트 W5 `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:132`, D4a 동 `:298`, `main.tex:238-241` 주석). 위 문안의 그림 관련 문장은 **재작성된 현행 Figure 1 을 전제로 한다** — 최종 빌드에 들어가는 Figure 1 이 재작성본이 맞는지 한 번 더 확인한 뒤 제출한다.

### 2.2 Funding

사용자 지정 문안이므로 **그대로** 싣는다.

```latex
\section*{Funding}

This work was supported by SNU Student-directed Education Undergraduate
Research Program through the SNU college, Seoul National University (2025). and
Undergraduate Social Science Research Grant through the College of Social
Sciences, Seoul National University (2026)
```

> **문장부호 확인 필요** — `(2025). and` 에서 마침표와 접속사가 겹치고 문장 끝에 마침표가 없다. 사용자 지정 문안이므로 임의로 고치지 않았다.

**부수 조치**: `main.tex:202-206` 의 출처 주석은 지원처를 「학부대학 독립연구지원 프로그램」 단일 건으로 기록하고 `The programme does not issue grant numbers.` 라는 본문 문장을 달고 있다. 지원이 2건이 되었으므로 **주석 갱신 + 과제번호 문장 유지 여부 결정**이 필요하다(§3 Q1). `main.tex:182-183` 의 CRediT 주석(`the award is a university undergraduate programme applied for jointly`)도 단수 전제다.

---

## 3. 사용자 판단·정보 입력이 있어야 진행되는 항목

| # | 물어야 할 것 | 무엇이 막혀 있는가 |
|---|---|---|
| **Q1** | 새 Funding 문안에서 **과제번호를 적을 것이 있는가?** 2025 Student-directed Education Undergraduate Research Program, 2026 Undergraduate Social Science Research Grant 각각에 대해 확인이 필요하다. 없다면 현행 본문 문장 `The programme does not issue grant numbers.` 를 **2건 모두를 가리키도록 고칠지, 아니면 삭제할지**도 함께 정한다 | A2 Funding 절 확정 |
| **Q2** | AI 도구 **이름과 버전 번호 3건** — (a) 초고 문장 다듬기(reword)에 쓴 도구, (b) 맞춤법·문법 점검에 쓴 도구, (c) 코드 정확성 검증에 쓴 도구. 같은 도구라면 그렇게 답하면 된다. **가이드가 버전 번호를 명시적으로 요구**하므로 "ChatGPT", "Claude" 같은 제품명만으로는 부족하고, 사용 시점의 버전 문자열이 필요하다 | A1 AI 진술 절, 커버레터 블록 4 |
| **Q3** | 논문 공개용 **신규 저장소의 이름·소유 계정**(개인 계정인지 `Transconnectome` 조직인지)과 **담을 범위** — `main.tex:133` 이 약속한 것은 "보고된 결과를 재현하는 데 필요한 전체 분석·전처리 코드"다. `repro/` 만인지, phase 스크립트 전체인지, 전처리 스크립트까지인지 | A3 코드 공개, Zenodo DOI, `main.tex:134-137` |
| **Q4** | **프리프린트를 공개할 것인가** (arXiv / bioRxiv). 가이드는 허용·권장한다. 공개한다면 커버레터 블록 3 의 `no preprint has been posted`(`COVER_LETTER_DRAFT.md:31` 끝문장)를 프리프린트 DOI 고지로 바꿔야 한다 | 커버레터 블록 3 확정 |
| **Q5** | **커버레터 블록 1 의 significance 문단** — 편집자가 색각·표상기하 비전공자라는 전제에서, 이 연구가 왜 IN 에 맞는지를 저자 본인의 언어로 한 문단. 체크리스트 §1.1 의 4단 논증(정상 생리 / 표상 해리 / CVD 특성 제안 / 방법론적 진전, `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:48-53`)과 IRB 비임상 판정(동 `:61-67`)이 재료로 준비되어 있으나, **어느 축을 첫 문장에 둘지는 저자 판단**이다 |  커버레터 블록 1·2 |
| **Q6** | **심사자 5인 확정** — 후보 7인(`REVIEWER_SUGGESTIONS_DRAFT.md:26-33`) 중 누구를 낼지, 그리고 C1–C4 확인(공저 이력·현 소속·이메일·과제 관계, 동 `:43-48`)을 **저자 4인 전원 기준으로** 누가 수행할지. 이 확인은 문헌만으로 대신할 수 없다 | A5' 심사자 명단 |
| **Q7** | Acknowledgements 의 **비저자 기여자**가 있는가, 그리고 서울대 뇌영상센터가 선호하는 사사 문구가 있는가 | `main.tex:231-232` `\todo` 해소 |
| **Q8** | 공저자 3인의 **투고본 승인 + CC BY 동의** 회신 (CC BY 는 무제한 재사용 허용 라이선스임을 함께 고지) | B3, 최종 제출 |

---

## 4. 말미 절 순서 — 가이드 권장 배열 vs `main.tex` 현재 배열

| 가이드 권장 순서 (발췌) | `main.tex` 현재 순서 | 줄 | 판정 |
|---|---|---|---|
| 1. **Declaration of the use of AI** | 1. Declaration of the use of AI | 143 | ✅ **신설 완료 (2026-09-01)** |
| 2. **Data and Code Availability** (필수) | 1. Data and Code Availability | 131 | 순서만 한 칸 밀림 |
| 3. **Author Contributions** (필수) | 2. Author Contributions | 166 | 일치 |
| 4. Funding (선택) | 3. Funding | 198 | 일치 (문안은 A2) |
| 5. **Declaration of Competing Interests** (필수) | 4. Declaration of Competing Interests | 208 | 일치 |
| — (가이드 목록에 없음) | 5. **Ethics** | 220 | 가이드 외 절. house practice 근거로 유지 결정됨(체크리스트 `:288`) — **Competing Interests 와 Acknowledgements 사이 = 현 위치 유지** |
| 6. Acknowledgements (선택) | 6. Acknowledgements | 227 | 일치 |
| 7. Supplementary Material (제작 단계 생성) | 8. Supplementary Methods | 271 | 1차 제출 단일 PDF 이므로 현행 유지 |
| (References) | 7. References | 256 | 일치 |
| (Appendix — 본문 일부로 조판, 2쪽 이내) | References **뒤**, Supplementary **앞** | 263-264 | **미확인** — 발췌가 Appendix 의 전후 위치를 명시하지 않는다 (§1.2 C4) |

**조치 항목**

1. ~~`\section*{Declaration of the use of AI}` 신설~~ ✅ **완료 (2026-09-01)** — `main.tex:143`. 실제로 넣은 문안은 §2.1 초안을 바탕으로 하되, 연구·본문·그림 세 층위를 문단으로 나누고 도구명과 버전만 `\todo` 로 남겼다.
2. ~~기존 AI 문단과 낡은 주석 삭제~~ ✅ **완료 (2026-09-01)** — 주석은 삭제하지 않고 새 절 머리로 옮겨, 옛 문장이 왜 부정확했는지를 기록으로 남겼다.
3. Appendix 의 위치(References 앞/뒤)를 가이드 원문 또는 게재 논문 1편으로 확정한다. 확인 전에는 현행 배치를 유지한다 — 발췌에 근거가 없으므로 **추측으로 옮기지 않는다.**
4. 위 1–2 는 `.tex` 수정 작업이며 **본 문서 작성 범위 밖이다.** 별도 작업으로 착수한다.

---

## 5. 착수 순서 (의존 관계)

```
Q2 (도구·버전) ─→ A1 AI 절 신설 ─┐
Q1 (과제번호)  ─→ A2 Funding 교체 ─┤
Q3 (저장소)    ─→ A3 저장소 생성 → Zenodo DOI → main.tex URL/DOI ─┤
                                                                   ├─→ B5 최종 재빌드 ─→ A6 Editorial Manager 제출
MANUSCRIPT_EDITS_CONSOLIDATED (X1 포함 본문 수정) ─────────────────┤
B1 절 순서 재배열 · B2 키워드 · B4 \todo 제거 ────────────────────┤
Q8 공저자 승인·CC BY ─────────────────────────────────────────────┘

Q5 ─→ 커버레터 블록 1·2   |   A1 확정 ─→ 커버레터 블록 4   |   Q4 ─→ 커버레터 블록 3 재확인
Q6 ─→ 심사자 5인 확정 (C1–C4 확인 완료 전 제출 금지)
```

**임계 경로는 A3 이다.** 저장소 생성 → 정리 → 공개 → Zenodo DOI 발급까지가 유일하게 외부 시스템 지연을 포함하고, 그 결과가 `main.tex` 본문 문장으로 들어가 최종 빌드를 막는다. A1·A2 는 사용자 회신만 있으면 각 10분 내에 끝난다.

---

## 6. 논문 양식의 기준 문서 — `ImagingNeuro_cha.pdf` (2026-09-01 채택)

저자 가이드가 규정하지 않는 조판·구성 관례는 **본 저널에 실린 `ImagingNeuro_cha.pdf`**(Kwon et al., *Imaging Neuroscience* 3, 2025, doi:10.1162/imag_a_00440) 를 기준으로 삼는다. 가이드는 1차 투고에 특정 형식을 요구하지 않으므로, 관례가 갈리는 자리에서는 이 논문의 실제 지면을 따른다.

| 관찰 | 우리 원고에 대한 함의 |
|---|---|
| `2. METHODS` 가 오버뷰 문단 없이 곧바로 `2.1 Experimental setup` → `2.1.1 Data` 로 들어간다 | **조치 없음 (2026-09-01 판정).** 우리 원고의 오버뷰 문단은 **존치한다.** 삭제해 보니 그 문단이 `fig:pipeline`(Figure 3)의 **유일한 콜아웃**이어서 본문에서 한 번도 불리지 않는 그림이 생겼다. 가이드가 요구하는 사항도 아니므로 되돌렸다 |
| 말미 절 배열이 Data and Code Availability → Author Contributions → **Ethics Statement** → Declaration of Competing Interest → Acknowledgements | Ethics 를 Competing Interests 앞으로 옮겼다. 가이드는 Ethics 를 열거하지 않으므로 이 배열이 가이드와 충돌하지 않는다 |
| **Funding 이 독립 절이 아니라 Acknowledgements 안에 들어 있다** | 우리는 가이드가 Funding 을 선택 절로 열거하므로 **독립 절을 유지**한다. 다만 조판 단계에서 편집부가 합칠 수 있다 |
| **"Declaration of the use of AI" 절이 없다** | 그 논문은 2024년 투고분이라 해당 요건 이전이다. **관례 근거로 쓸 수 없으며, 이 항목은 가이드를 따른다** |
| 절 번호가 `2.1.1.1` 까지 내려간다 | 우리 원고는 `secnumdepth=2` 라 소절까지만 번호가 붙는다. 가이드가 `1.1.1` 을 허용하므로 위반은 아니다. **변경 불요** |
| 2단 조판 | 게재본 조판 결과이지 투고 요건이 아니다. 1차 투고는 단일 컬럼으로 낸다 |
