# 투고 체크리스트 — Imaging Neuroscience (2026-08-16)

> 근거: Imaging Neuroscience *Guide for Authors* + MIT Press *Journal Publication Ethics* (2026-08-16 공고문 기준).
> 대조 대상: `main.tex`, `Introduction/introduction_v2.tex`, `Methods/methods_v2.tex`, `Results/results_v4.tex`,
> `Discussion/discussion_v3.tex`, `Results/appendix_alternative_models.tex`, `Supplementary/supplementary.tex`
> (= `main.tex` 가 실제로 `\input` 하는 파일만).
>
> 프레이밍·제목·초록 문안은 [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md),
> 내용 잔여는 [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md) §10(I1–I4) 이 정본이다.
> **이 문서는 형식·행정 요건만 다룬다.**
>
> 범례: ✅ 충족 · ⚠ 확인 필요 · ❌ 미충족(제출 차단) · ▫ 해당 없음

---

## 0. 요약

> **rev.5 (2026-08-17)** — **C 항목(형식) 일괄 처리 완료**: P10 IN style file 전환 · P6 american · P7 lineno · P8 Supplementary 번호 분리 · P9 그림 폰트 8/9. 앞선 rev.4 = back matter 실문장 확정(CRediT 4인·Funding·이해충돌·Ethics 절·AI 진술·응답기한 8주), 구 Methods 사본 9개 아카이브(R2), §S 번호표 정정 및 본문 참조 17/17 재검증(R4), 심사자 후보 7인(B6). **빌드 72쪽 클린, undefined 0, citation warning 0**, `\todo` 3건 잔여.

| | 개수 | 항목 |
|---|---|---|
| ❌ **차단** | **2** | B5 커버레터 블록 1·2·4 · B6 추천 심사자 **충돌 확인**(후보 초안은 완료) |
| 🟡 잠정 | 2 | B7 AI 사용 진술(그림 번호·투고 직전 재확인) · B2c back matter 잔여 `\todo` 3건(Zenodo DOI·감사 문구·AI 그림 번호) |
| 🔴 **정확성** | **1** | **X1 — `Supplementary/supplementary.tex:46` 이 현재 사실과 다른 문장을 담고 있다.** 형식 항목이 아니라 원고 내용 오류이며, 두 개의 미반영 수정계획(§10.3 P0)에 함께 걸려 있다 |
| ⚠ 확인 | 4 | W5 그림 폰트(**8/9 완료**, 잔여 2건은 수작업 합성물) · W6 코드 공개 상태 · W7 PDF 최신성 · W8 scope 논증 · W10 공저자 승인·CC BY 동의 |
| ✅ 충족 | 23 | 윤리·동의·키워드·절 번호·본문 순서·부록 분량·표 서식·참고문헌 · 저자/교신 정보 · back matter 구성 · 데이터 가용성 문안 · **파생데이터 공개 가부 판정(W9)** · **Funding 지원기관** |

**핵심**: 원고 본문(§1–§4)은 형식상 준비되어 있다. 남은 차단은 전부 **제출 시스템 입력물(커버레터·심사자)** 과
**본문에 넣을 진술 3건(CRediT 역할·이해충돌·AI 사용)** 이다.

---

## 1. Scope & Article Type

| # | 요건 (공고문) | 상태 | 근거 / 조치 |
|---|---|---|---|
| 1.1 | Article type 선택 | ✅ | **Research**. Data Resource·Software Toolbox·Technical Note·Registered Report 모두 해당 없음 |
| 1.2 | Registered Report 경로 | ▫ | PCI RR 경유 트랙. 본 원고는 이미 데이터 수집 완료 → 해당 없음 |
| **W8** | "질환 효과를 보고하는 일반 투고는 **생리학적 뇌기능 이해를 높이거나 유의한 방법론적 진전**을 제시할 때만 scope 내" | ⚠ | 아래 §1.1 참조. 프레이밍 축을 **representation geometry** 로 고정해야 scope 안에 들어온다 |
| 1.3 | 제목 | ⚠ | 현행 `main.tex:63` 은 `Individual-specific distortion … informs personalized color correction`. IN 용 권고는 **T4** = `From cortical hue-geometry distortion to individualized stimulus-space correction in color vision deficiency` (`REVISION_PLAN_HMC_DISCLOSURE` M9). `Individual-specific` 은 HMC arm 에서 유지되지 않는 주장이라 금지어로 지정되어 있다 → **교체 필요** |

### 1.1 Scope 논증 — representation geometry 축으로 고정

IN 의 scope 문장은 임상군 연구를 **질환 효과 보고**로 읽는 순간 triage 로 보낸다. 본 연구를 그 범주에서 빼내는 것은 표본 크기 방어가 아니라 **분석 대상의 재정의**다. 우리가 측정한 것은 환자군의 결손 크기가 아니라 **피질 색 표상의 기하 구조**이며, CVD 는 그 기하를 관측 가능하게 만드는 조건으로 들어온다.

**커버레터·서론이 세워야 할 논증 (`REVISION_PLAN_HMC_DISCLOSURE` §0 의 생존 목록에만 의존한다)**

| 축 | 진술 | 근거 (arm 전부 생존) |
|---|---|---|
| **정상 생리** | 연속 hue 보간은 시각피질 전역이 아니라 **hV4 단독**에서 지지된다 | 4 arm 전부 통과 ($p$ = .011 / .013 / .002 / .023), 지표 신뢰도 ICC(2,1) = 0.825 (V1 = −0.005) |
| **표상 해리** | 같은 복셀 패턴에서 **8색 범주 식별은 보존**되고 **연속 hue 기하만 이탈**한다 | 식별: 두 CVD·전 ROI 에서 chance 1.8배 이상. 기하: hV4 보간이 HC 평균 아래, 4 arm 방향 보존 |
| **CVD 특성 제안 (노블티)** | 따라서 CVD 는 망막 수준 기술에 **더하여** 피질 hue 기하의 왜곡으로 기술될 수 있다 — 선행 CVD fMRI 는 magnitude/gain(Tregillus 2021)·activation(Rina 2024) 층위에 머물러 이 층위를 다룬 적이 없다 | 초록 교체안 M8 의 `alongside its established retinal characterization` |
| **방법론적 진전** | 개인의 피질 표상에서 역산한 자극공간 필터 — 8색 exact, 2차 세션 전 **동결 후 전향 평가** | 역산 8/8 exact(수학, 전처리 무관), 심리물리 전량 전처리 무관 |

**금지 프레이밍**: `CVD 환자에서 hV4 보간이 유의하게 감소했다` — 사실도 아니고(단일사례 검정은 primary arm 에서만 유의) scope 밖으로 읽힌다. **허용 프레이밍**: `hue 기하는 hV4 에서 측정 가능한 성질이며, CVD 는 그 성질이 개인 수준에서 이탈하는 조건이다.`

**첫 문장 수준의 차이가 결정적이다.** 서론과 커버레터를 색각이상 유병률·불편으로 열면 임상 논문으로 분류된다. **피질 색 표상 기하가 어디서 어떻게 조직되는가**로 열고 CVD 를 그 물음의 검증 조건으로 도입해야 한다.

**승인 문서가 이 프레이밍을 문서로 뒷받침한다 (2026-08-16 확인).** IN 이 scope 판정에서 묻는 것이 "임상 연구인가"이므로, 승인기관 스스로 아니라고 판정한 기록은 커버레터에 쓸 수 있는 1차 자료다.

| 근거 | 원문 (`docs/archive/final_IRB.pdf`) |
|---|---|
| 취약군 해당 없음 판정 + 질환 아님 명시 | p.2 — "취약한 연구참여자 범주: 해당 없음 (**색각 이상은 의학적 질환으로 간주되지 않음**)" |
| 연구 성격 자체를 비임상으로 선언 | p.7 — "※ 본 연구는 **임상 연구가 아니며**, 추후 본 연구의 결과보고 심의를 서울대 IRB 에 요청하지 않을 것임을 밝힌다" |
| 대상군 정의가 환자군이 아님 | p.2 — "연구대상군: **일반 성인** (정상인 및 색각이상 조건 포함)" |

**커버레터 문장으로**: 승인 프로토콜이 색각이상을 의학적 질환이 아닌 정상 성인의 변이로 분류했고, 본 연구의 종점은 질환 지표가 아니라 피질 색 표상의 기하라는 취지를 한 문장으로 넣는다. 이 진술은 IN scope 문장의 "apparent effects of disease" 범주에서 원고를 직접 빼낸다.

---

## 2. Before Submitting

| # | 요건 | 상태 | 근거 / 조치 |
|---|---|---|---|
| **B5** | 커버레터 (significance + fit, **자기 분야 밖 에디터를 독자로 상정**) | 🟡 | [`COVER_LETTER_DRAFT.md`](COVER_LETTER_DRAFT.md) 4블록 중 **블록 3(B8) 완료**. 잔여 = 블록 1(scope, §1.1 기반, P1·P2 후)·2(요약)·4(AI 진술) |
| 2.1 | 원저성 확인 (타 학술지 동시 투고 없음) | ✅ | 현재 타 저널 심사 중 아님 |
| ~~B8~~ | **밀접 관련 투고/발표는 에디터에게 고지**. preprint 는 허용·권장 | ✅ | **초안 확정** — [`COVER_LETTER_DRAFT.md`](COVER_LETTER_DRAFT.md) 블록 3. 고지 3건(ICML SD4H **non-archival** 논문+포스터 / 랜딩페이지 / 2027 예정 학사 졸업논문, 미제출). 문면 중복 실측: **동일 문장 0개, 8-gram 0.32%**(14/4,435, 대부분 소속 문자열). 워크숍 논문은 필터 평가를 보고하지 않으며 초록이 그것을 `defined next test` 로 명시 → 기여 경계가 워크숍 논문 자체 문장으로 확정됨 |
| 2.2 | 키워드 ≤ 6 | ✅ | `main.tex:68` — 5개. 단, 제목을 T4 로 바꾸면 `hue geometry`, `single-case` 반영 검토 |
| **B6** | **추천 심사자 ≥ 5인** (많을수록 유리), 이해충돌 회피 | 🟡 | **후보 7인 초안 작성** — [`REVIEWER_SUGGESTIONS_DRAFT.md`](REVIEWER_SUGGESTIONS_DRAFT.md). 방향별로 원고의 세 취약점(선행 대비·개인차 주장·기하 통계)에 대응하도록 선정. **배제 1건 확정**: `ryu2024` 공저자 Lee Sang-Hun 은 서울대 소속. **잔여 = 충돌 확인 C1–C4**(공저 이력·현 소속·이메일·과제 관계). 확인 전 제출 금지 |
| 2.3 | 표절 검출 통과 / 방법 문안 재사용 시 명시 | ⚠ | Methods 문안이 졸업논문과 겹칠 수 있음 → B8 고지로 커버 |
| ~~W2~~ | 영어 변종 **일관성** | ✅ | **`american` 으로 통일.** 본문 철자가 이미 전부 미국식이었으므로(`color` 405 / `colour` 0, 미국식 -ize 만) 텍스트는 손대지 않고 선언만 맞췄다 |
| 2.4 | 문법·오탈자 수준 (심각하면 심사 전 반송) | ⚠ | `/revise-draft` ↔ `/apply-draft` 수렴 사이클 완료 여부 확인 |
| 2.5 | 포용적 표현, **sex vs gender** 용어 정확성 | ✅ | `methods_v2.tex:37` — `3 female`, `both male` (= sex, 문맥상 정확). `gender` 오용 없음 |
| ~~B4~~ | 전 공저자 승인 + 이름·소속·이메일, **교신저자 명시 + 이메일** | ✅ | **해소.** ICML SD4H(`SD4H_cameraready_pathB.tex:61-73`)와 **순서까지 동일**하게 확정: Jinil Kim → Albert Minkue Cho → Jungwoo Seo → Jiook Cha. `main.tex` 에 `\fourauthors`/`\fouraffiliations`/`\authornote` 로 반영. 교신 2인(Jinil Kim `haba6030@snu.ac.kr`, Jiook Cha `connectome@snu.ac.kr`), PI = Jiook Cha 를 데이터 관리자로 명기 |
| **W10** | 전 공저자의 **투고본 승인 + CC BY 동의**, 펀딩 정보 수집 | ⚠ | 저자 확정으로 요건은 명확해졌으나 **3인의 명시적 승인·CC BY 동의·과제번호 회신은 미수령**. CC BY 는 무제한 재사용 허용 라이선스임을 고지할 것 |
| 2.6 | AI 도구를 저자로 등재 금지 | ✅ | 해당 없음 |
| 2.7 | byline 에 그룹/컨소시엄 금지 | ✅ | 해당 없음 |
| ~~B2a~~ | CRediT 진술 | ✅ | **4인 전원 역할 확정 (2026-08-17).** 실제 IN 게재 서식(이니셜·세미콜론, doi:10.1162/IMAG.a.55)을 따랐다. 매핑 2건 적용: `result interpretation` → **Formal analysis**(CRediT 에 해당 역할 없음), `data collection`/`recruitment` → **Investigation**. Funding acquisition 은 4인 전원 |
| 2.8 | **1차 제출 = 단일 PDF**, 그림·표를 본문 해당 위치에 통합, 페이지 번호, 가급적 줄 번호 | 부분 | 아래 §4 |
| ~~B2b~~ | 이해충돌 선언 | ✅ | 이해충돌 없음. 필터 특허 미출원·상용 안경/디스플레이 소프트웨어 업체와 무관함을 명시적으로 부인 |
| 2.9 | 전 저자가 **CC BY** 출판에 동의 | ⚠ | = W10. 공저자 3인 회신 대기 |
| 2.10 | 전재 그림/문구의 원저자도 CC BY 동의 | ⚠ | Ishihara plate 이미지 등 외부 자산 사용 여부 확인. 현재 `Figures/` 는 전부 자체 생성으로 보이나 `fig1_paradigm` 계열 자극 도해 재확인 |
| 2.11 | 데이터셋/툴을 **본문 인용 + 참고문헌 등재**, 영구 식별자(DOI) 권장 | ⚠ | 신규 GitHub 리포지토리 생성 → Zenodo DOI 후 반영. **투고 직전 단계** (§10.4 R1·R3) |

---

## 3. Paper Organization

| # | 요건 | 상태 | 근거 |
|---|---|---|---|
| 3.1 | Title / Authors / Affiliations / **Corresponding author info** / Abstract(**단일 문단**) / Keywords | ✅ | Abstract 단일 문단 · 저자 4인 + 소속 · `\authornote` 에 교신 2인 이메일 및 PI 데이터 관리자 표기 |
| 3.2 | 본문 순서 Introduction → Methods → Results → Discussion | ✅ | `main.tex:86-95` |
| 3.3 | **모든 절·소절 번호 부여, `1 Introduction` 부터** | ✅ | `main.tex:28,80-83` — apa6 `man` 모드가 번호를 안 붙이는 문제를 `secnumdepth=2` + front matter 구간 임시 해제로 해결. Introduction = 1 로 시작 |
| 3.4 | **윤리 진술이 적절한 위치(예: Methods 서두)에 명확히** | ✅ | `methods_v2.tex:37` — SNU IRB No. 2510/002-023, Declaration of Helsinki, written informed consent, 제외 사유까지 기술 |
| 3.5 | Methods/Results 병합은 지양 | ✅ | 분리되어 있음 |
| 3.6 | **부록은 조판 2쪽(≈1500 단어) 이내**, 초과분은 Supplementary 로 | ✅ | `Results/appendix_alternative_models.tex` = **335 단어** |
| ~~B3~~ | 말미 절 구성·순서: **Data and Code Availability**(필수) → **Author Contributions**(필수) → Funding(선택) → **Declaration of Competing Interests**(필수) → Acknowledgements(선택) → Supplementary → **References (APA)** | ✅ | **해소.** 기존 Elsevier 배열(`CRediT` → `Competing` → `Acknowledgements` → `Data availability`)을 IN 규격 5절로 전면 교체하고 `Funding` 절을 신설했다 (`main.tex` back matter) |
| 3.7 | 참고문헌 APA 형식 | ✅ | `main.tex:138` `apacite` + `bibliography.bib` (87 entries) |
| ~~W3~~ | Supplementary 가 본문 번호를 받지 않을 것 | ✅ | `\section*{Supplementary Methods}` 로 변경. 이전에는 `5 Supplementary Methods` 로 Discussion 다음 번호를 받고 있었다. 내부는 이미 `\subsection*` + 수동 S1–S21. **개정 단계에서 별도 파일 분리는 여전히 필요** |

---

## 4. First Submission (형식)

| # | 요건 | 상태 | 근거 / 조치 |
|---|---|---|---|
| 4.1 | 전 요소 통합 **단일 PDF** | ⚠ | 현재 `main.pdf` = **72쪽**(클래스 전환으로 92 → 72). `colorblind_main.pdf` 는 2026-08-08 빌드로 stale — **W7: 본문 P0–P5 반영 후 최종 재빌드** |
| 4.2 | 그림·표를 의도 위치에 인라인 | ✅ | 본문 그림 8개(Methods 3 / Results 5), Supplementary 그림 2 · 표 17. 전 `\includegraphics` 대상 파일 실존 확인 완료 |
| 4.3 | 페이지 번호 | ✅ | apa6 `man` 모드 기본 출력 |
| ~~W1~~ | 줄 번호 (ideally) | ✅ | **적용.** `lineno` + `\linenumbers`. amsmath 패치를 함께 넣어 numbered display equation 8개(Methods 6 · Supplementary 2)가 전부 살아남는 것을 (1)–(8) 번호로 확인 |
| ~~W4~~ | **IN 제공 style file** 사용 | ✅ | **전환 완료 (2026-08-17).** `apa6[man,british]` → `imag-ms-template`(리포지토리 내 `imaging_neuro_tex/` 에 있던 저널 제공 클래스). 서지는 apacite/BibTeX → **biblatex/biber(style=apa)**, 인용 93건 remap(`\cite`→`\parencite` 33, `\citep` 37 은 natbib=true 로 무변경, `\citeA`→`\textcite` 13, `\citeNP`→`\citealp` 10). 저자 블록은 apa6 전용 `\fourauthors`/`\authornote` 대신 위첨자 소속 + correspondence 줄로 재작성. `secnumdepth` 우회 코드는 예상대로 불필요해져 삭제 |
| 4.4 | Editorial Manager 제출 | ❌ | https://www.editorialmanager.com/imag/ 계정 생성 필요 |

---

## 5. Revision 단계 (지금 준비해 둘 것)

| # | 요건 | 상태 |
|---|---|---|
| 5.1 | Word 또는 LaTeX 원본 제출 (+ 컴파일된 PDF 동봉), TeX 패키지 전 요소 포함 | ⚠ Overleaf 패키지 `overleaf_upload.zip` 갱신 필요 |
| 5.2 | 그림을 **본문 인라인 + 개별 파일**로 동시 제공. PDF/EPS/JPG/PNG/TIFF, 개당 ~10MB 이하 | ✅ 최대 `fig3_workflow_composited.pdf` 3.3MB — 전 파일 10MB 이하 |
| **W5** | 그림 내부 폰트 **Arial 또는 Helvetica** | 🟡 **8/9 완료.** `MATPLOTLIBRC` 로 Arial + mathtext 강제 후 전 그림 재생성·육안 검증. 방법과 근거는 [`Figures/scripts/FONT_POLICY.md`](Figures/scripts/FONT_POLICY.md). **잔여 2건은 수작업 합성물**: `fig1_generated_v2`(생성 스크립트 부재), `fig3_workflow`(PowerPoint 합성, 글꼴 Aptos) |
| 5.3 | 표는 표 객체로(탭/콤마 텍스트 금지), **음영·색상 글자 금지** | ✅ Supplementary 17개 표 전부 `booktabs`, `\rowcolor`/`\cellcolor`/`\textcolor` 사용 0건. (주의: `main.tex:31` 의 `\todo{}` 가 빨간 글자 — B2 해소 시 함께 제거) |
| 5.4 | Supplementary ≤ 100MB, 설명 텍스트(제목·캡션) 동반 → PDF 권장 | ✅ 텍스트·표 위주 |

---

## 6. Data & Code Availability (최우선 차단)

> 공고문 원문: *"'Available upon request' is not acceptable without further detailed explanation."*
> 허용되는 사유 예시 = 정식 데이터 공유 협약 필요 / 요청자 소속 IRB 승인 필요 / 공식 연구계획서 제출 요구 / 공저자 등재 요구.

### 6.0 판정 — "공개 불가, 요청 시 제공"은 관례로 인정되는가

**결론: 인정된다. 단, 지금까지 쓰던 문구 형태로는 인정되지 않는다.** 두 가지는 다른 문제다.

IN 공고문은 제한적 접근 **자체**를 금지하지 않는다. 금지하는 것은 *사유 없는* `available upon request` 이고, 같은 문단에서 **허용되는 사유를 명시적으로 열거**한다.

| IN 이 열거한 허용 사유 | 본 연구 해당 여부 |
|---|---|
| The need for a formal data sharing agreement | ✅ 기관 간 DUA 로 구성 가능 |
| The need for approval from the requesting researcher's local ethics committee | ✅ IRB 조건과 직접 대응 |
| The need to submit a formal project outline | ✅ 이용 목적 심사로 구성 가능 |
| Requirements for co-authorship | ✅ **요구하지 않음** (요구했다면 IN 이 부정적으로 본다) |

즉 본 연구의 IRB 조건(PI 단독 접근 암호화 저장)은 IN 이 **예시로 든 사유 유형에 정확히 들어맞는다.** 관례에 해당하느냐는 물음의 답은 예이지만, 그 관례를 성립시키는 것은 "요청 시 제공"이라는 말이 아니라 **접근 통제자·조건·절차를 문서에 적어 두는 것**이다. `on reasonable request to the corresponding author` 한 문장은 그 요소를 하나도 담고 있지 않아서 거부 대상이 된다.

**함께 고쳐야 했던 사실관계 오류 2건**

1. **접근 통제자 불일치.** IRB 상 접근권은 PI(Jiook Cha)에게만 있는데 원고는 `corresponding author` 로 보내라고 적혀 있었다. 교신저자는 2인이고 제1저자는 접근권자가 아니다 → **PI 를 명시적으로 지목**하도록 수정.
2. **코드까지 함께 제한된 것처럼 읽힘.** 코드에는 IRB 제약이 없다. IN 은 코드 공개를 강하게 요구하므로 **데이터와 코드를 분리 진술**해야 한다 → 코드는 `openly available`, 데이터는 조건부로 분리.

| # | 요건 | 상태 | 근거 / 조치 |
|---|---|---|---|
| ~~B1~~ | 데이터·코드 가용성 진술 (공유 여부와 무관하게 **필수**) | ✅ | **해소.** `main.tex` 의 `Data and Code Availability` 절에 (i) 코드 공개, (ii) IRB 근거·암호화 저장·PI 단독 접근, (iii) 5년 최소 보관 + 이후 PI 관리 하 계속 보관, (iv) 요청 경로(PI 이메일) 와 3개 조건(DUA / 요청자 IRB 승인 / 이용계획서), (v) 공저자 요구 없음을 기술. `Methods/methods_v2.tex:362` 은 해당 절을 가리키도록 축약 |
| 6.1 | 권장: 공개 리포지토리 + **영구 식별자(DOI)** | ⚠ | **코드**: GitHub 공개 전환 + release 를 Zenodo 에 연결해 **DOI 발급**(IN 이 persistent ID 를 요구). **데이터**: 아래 W9 판정에 따라 기탁 불가 |
| ~~W9~~ | **파생데이터만 별도 공개** 가능한지 | ✅ | **판정: 불가.** 근거는 §6.4. `main.tex` 의 조건부 블록을 삭제하고 제한 문안으로 확정했다 |
| 6.2 | 데이터/툴을 **본문 인용 + 참고문헌 등재** | ⚠ | Zenodo(코드) / OSF(파생, W9 결과에 따라) DOI 확정 후 `bibliography.bib` 에 dataset·software entry 추가하고 본문에서 인용 |
| 6.3 | 5년 보관 규정과 진술의 정합 | ✅ | 무기한 제공을 약속하지 않고 「서울대학교 연구윤리 지침」 제16조 제3항 문언 그대로 "5년 + 이후 PI 관리 가능 범위"로 진술했다 |

### 6.4 파생데이터 공개 가부 — 판정 근거 (2026-08-16, IRB 원문 대조)

대조 문서: `docs/archive/final_IRB.pdf`(47쪽 연구계획서), `docs/archive/[변경2차] IRB No. 2510_002-023.pdf`(20쪽, 참여자 서명 동의서 포함).

**결론: 현행 승인 문서로는 파생데이터를 포함해 어떤 형태의 공개 기탁도 불가하다.** 근거가 세 겹으로 겹친다.

| # | 근거 | 원문 |
|---|---|---|
| 1 | 접근권을 **PI 단독**으로 못박음. 파생/원자료 구분 없이 "데이터" 전체에 걸린다 | 계획서 §이익 및 보상, 개인정보 보호대책 — "데이터는 연구책임자에게만 접근 권한이 있는 암호화된 저장소에 보관되며" |
| 2 | **동의서에 2차 이용·제3자 제공·공개 기탁 조항이 없다.** 참여자가 서명한 문서에 데이터 공유 항목 자체가 존재하지 않으며, 제공이 언급되는 유일한 경우는 법적 요청과 IRB·점검요원의 검증 열람뿐 | 동의서 p.2 — "만일 법이 요구하면 귀하의 개인정보는 제공될 수도 있습니다", "모니터 요원, 점검 요원, 생명윤리위원회는 … 자료의 신뢰성을 검증하기 위해 연구 결과를 직접 열람할 수 있습니다" |
| 3 | 「생명윤리 및 안전에 관한 법률」 제18조상 제3자 제공은 **동의 범위 내**에서만 가능하다. 2번에 따라 그 범위가 비어 있다 | — |

**"익명화되었으니 개인정보가 아니다"는 논거는 여기서 쓸 수 없다.** 1번 조항이 익명화 여부와 무관하게 저장소와 접근권 자체를 지정하고 있고, 동의서는 그 조항을 참여자에게 고지한 상태로 서명을 받았다. 익명화 논거로 기탁하면 **참여자에게 고지한 내용과 다른 처리**가 된다.

**공개를 원한다면 경로는 하나뿐** — 신규 IRB 심의다. 다만 **연구수행기간이 2025-12-19 로 이미 종료**되었으므로(계획서 p.2) 통상적인 변경심의(amendment)가 아니라 2차적 이용에 대한 별도 심의 신청이 되고, 기수집 참여자 재동의 필요 여부는 IRB 판단 사항이다. **논문 일정과 분리해 진행할 것.** 투고는 제한적 접근 문안으로 간다.

**부수 확인 2건**

- 계획서 §이익 및 보상 문단에 **내부 모순**이 있다 — "익명처리되어 보관되어 **분석 종료 후 1년 이내에 파기**"와 "**5년간 의무보관**"이 연속된 두 문장에 함께 있다. 원고는 참여자 동의서에 실제로 기재된 **5년 조항**을 인용했다(동의서 p.2 문언과 일치). 1년 파기 문장은 인용하지 않는다.
- 동의서상 데이터 접근 허용 범위는 **연구책임자 차지욱 + 연구담당자 서정우·김진일·조민규** 4인으로, **본 원고의 저자 4인과 정확히 일치**한다. 저자 외 인원의 데이터 접근이 없었다는 점이 문서로 뒷받침된다.
| **W6** | 심사·에디터가 **1차 제출 시점에 접근** 가능해야 하고, 채택 시점에 **공개** | ⚠ | `https://github.com/Transconnectome/colorBlind_analysis` 의 **public/private 여부 확인 필수**. private 이면 심사자가 볼 수 없다. 공개 시 `REVISION_PLAN_PRESUBMISSION` **I4**(Methods 중복본 6개가 참가자 수를 `Twelve`/`Thirteen` 으로 상충 기술)가 그대로 노출된다 → 공개 전 정리 |
| 6.3 | 외부 출처 데이터의 취득 경로 기술 | ▫ | 전량 자체 취득 |

---

## 7. 연구·출판 윤리 (MIT Press)

| # | 요건 | 상태 | 근거 |
|---|---|---|---|
| 7.1 | IRB/윤리위 승인 + Declaration of Helsinki 준수 명시 | ✅ | `methods_v2.tex:37` — SNUIRB No. 2510/002-023 |
| 7.2 | Methods 에 동의 취득 진술 (권장 문안: *"Informed consent was obtained from all participants for being included in the study."*), **서면/구두 여부 명시** | ✅ | "Ten volunteers provided **written** informed consent" — 서면 명시. 요구 문안의 "suitable modification" 범위 내 |
| 7.3 | 식별 정보 공개 시 별도 동의 | ▫ | 개인 식별 정보 없음(연령·성별·Ishihara 점수만). 단, **CVD 참가자 2인은 subtype+연령+점수 조합으로 사실상 특정 가능** — 소속 집단 규모를 고려하면 재식별 위험 낮음, 그러나 데이터 기탁(6.1) 시에는 재검토 |
| 7.4 | 요청 시 IRB 승인서 제출 가능 | ⚠ | 승인서 사본 확보해 둘 것 |
| 7.5 | 동물 연구 | ▫ | 해당 없음 |
| 7.6 | 이해충돌 — 재정적 관계뿐 아니라 개인적 관계·학문적 경쟁·지적 신념까지. ICMJE Disclosure of Interest 양식 | ❌ | B2 와 동일. **필터 관련 특허/출원, EnChroma 등 상용 제품과의 관계 유무**를 명시적으로 확인할 것 |
| **B7** | **AI 도구로 텍스트/이미지/데이터를 생성한 경우 본문과 커버레터에 명확히 설명**. 저자는 AI 생성 부분까지 전적으로 책임 | ❌ | 본 프로젝트는 초안 작성·수정에 LLM 을 사용했다. 미기재는 MIT Press 윤리 규정 위반이다. **조치**: ① Acknowledgements 또는 Methods 말미에 사용 범위(작성 보조/코드 보조/그림 생성 여부)를 1–2문장으로 기술, ② 커버레터에 동일 내용 반복. `Figures/*_generated*.png` 계열이 생성형 이미지라면 **그림 생성 사용도 별도 명시** |
| 7.7 | 표절·조작 없음 | ✅ | B8 고지로 자기표절 리스크 관리 |

---

## 8. 행정 (Fees / 기타)

| # | 항목 | 상태 |
|---|---|---|
| 8.1 | **APC $1,400** (채택 시 청구) | ⚠ 예산 확보 확인. **교신저자 주 소속국이 한국 → LMIC 면제 대상 아님** (면제국 목록에 Republic of Korea 없음) |
| 8.2 | Comment/Perspective 면제 (<3,000 단어, 그림+표 ≤2) | ▫ Research 투고 → 해당 없음 |
| 8.3 | 문의처 `editorial-manager@imaging-neuroscience.org` | — |
| 8.4 | 심사 방식: single-blind, 저자 신원 공개, 리뷰어 ≥3 목표 | — 참고 |
| 8.5 | 채택 후 'Just Accepted' DOI 부여, ~3주 내 최종본 | — 참고 |
| 8.6 | **출판 후 수정 불가**(중대 사안만 correction article) | — 교정 단계에서 수치 최종 검증할 것 |

---

## 9. 참고 — 분량 현황

| 파일 | 단어수 | 비고 |
|---|---|---|
| `Introduction/introduction_v2.tex` | 1,286 | |
| `Methods/methods_v2.tex` | 5,919 | |
| `Results/results_v4.tex` | 3,407 | |
| `Discussion/discussion_v3.tex` | 1,914 | |
| **본문 합계** | **≈12,526** | IN 은 Research 에 상한 없음. 다만 Methods 가 본문의 47% — 일부를 §S 로 옮기는 편이 읽힌다 |
| `Results/appendix_alternative_models.tex` | 335 | 부록 한도 ~1,500 이내 ✅ |
| `Supplementary/supplementary.tex` | 6,342 | 별도 파일화 대상 (W3) |

---

## 10. 남은 할 일 (running board)

> 이 절이 진행 상황의 정본이다. 항목이 끝날 때마다 여기서 상태를 갱신한다. 최종 갱신 2026-08-16.

### 10.1 완료

| # | 항목 | 반영 위치 |
|---|---|---|
| ✔ | 저자 목록·순서·소속·교신 2인·PI 지정 | `main.tex` `\fourauthors`/`\fouraffiliations`/`\authornote` |
| ✔ | back matter 를 IN 5절 규격·순서로 전면 교체 | `main.tex` back matter |
| ✔ | Data and Code Availability 본문 작성 (IRB 조건·PI 경로·3개 접근 조건·5년 보관) | `main.tex` |
| ✔ | Methods 데이터 문장을 해당 절 포인터로 축약 (`on reasonable request` 제거) | `Methods/methods_v2.tex:362` |
| ✔ | scope 논증 축을 representation geometry 로 고정 + IRB 비임상 판정 근거 확보 | 본 문서 §1.1 |
| ✔ | **D1 판정** — IRB 원문·동의서 대조 결과 파생데이터 공개 불가. 조건부 블록 삭제, 제한 문안 확정 | 본 문서 §6.4, `main.tex` |
| ✔ | Funding 절 1차 기재 (서울대 학부대학 독립연구지원 프로그램) | `main.tex` |

### 10.1a Author Contributions — 실제 IN 논문 서식 (2026-08-17 확인)

가이드는 "CRediT statement"만 요구하고 서식을 지정하지 않는다. 게재된 논문 2편을 확인한 결과 **두 계열**이 공존하며, 가이드 문언에 맞는 것은 A 다.

| 계열 | 실례 | 특징 |
|---|---|---|
| **A. CRediT 역할 나열** (권장) | doi:10.1162/IMAG.a.55 — "J.Y.: Conceptualization; Data curation; Formal analysis; Funding acquisition; Visualization; Methodology; and Writing—original draft. Y.S.W. and C.H.A.B.: Validation; Investigation; and Writing—review & editing." | **이니셜** 사용, 역할은 **세미콜론** 구분, 마지막 앞에 `and`, 역할이 같은 저자는 **묶어서** 표기 |
| B. 서술형 문장 | doi:10.1162/imag_a_00455 — "S.D.H.-C. and N.K contributed equally. J.B., G.C., and D.V.D.V jointly supervised this work. S.D.H.-C., … performed experiments and analyzed data." | 기여를 문장으로 서술. 동등기여·공동지도 표기에 유리하나 CRediT 역할명을 쓰지 않음 |

**A 를 채택했다.** `main.tex` 에 이니셜 서식으로 반영했고, 표기는 `Writing---original draft` / `Writing---review \& editing` (em-dash) 로 실례와 맞췄다.

**CRediT 14개 역할 — 공저자에게 제시할 선택지**

| 역할 | 뜻 | 본 연구에서 해당할 만한 일 |
|---|---|---|
| Conceptualization | 아이디어·연구 목표 설정 | 피질 역산 필터 착상, 연구 설계 방향 |
| Methodology | 방법론 개발·설계 | SRM/LOCO 설계, 2-성분 모델, 필터 역산 수식 |
| Software | 코드 작성·구현 | 분석 파이프라인, PsychoPy 자극 프로그램, 필터 렌더링 |
| Validation | 결과 재현성·검증 | 4-arm 민감도, 순열검정, 재현 스크립트 대조 |
| Formal analysis | 통계·수리 분석 | 단일사례 통계, RDM, disparity |
| Investigation | **실험 수행·데이터 수집** | 참가자 모집, MRI 세션 진행, 심리물리 측정 |
| Resources | 장비·시료·계산자원 제공 | MRI 장비 사용, 서버 |
| Data curation | 데이터 관리·정제·주석 | BIDS 변환, 전처리, 디페이싱, QC |
| Writing---original draft | 초고 작성 | — |
| Writing---review \& editing | 검토·수정 | — |
| Visualization | 그림·시각화 | Figure 제작 |
| Supervision | 지도·감독 | PI |
| Project administration | 과제 운영·일정 관리 | IRB 행정, 세션 스케줄링 |
| Funding acquisition | 연구비 확보 | 학부대학 독립연구지원 프로그램 |

**확정된 부분** — 승인 프로토콜이 공저자 3인(서정우·김진일·조민규)을 **연구담당자**로 기재하고 모집·데이터 수집 담당으로 명시하므로 **Investigation 은 3인 모두 확정**이다. 차지욱은 연구책임자·개인정보관리책임자·연구비 수혜자이므로 Supervision·Resources·Project administration·Funding acquisition 이 확정된다.

**회신받아야 할 부분** — Albert Minkue Cho(전기정보공학부)와 Jungwoo Seo(뇌인지과학과)가 Investigation 외에 Software / Data curation / Validation / Methodology 중 어디에 해당하는지. `main.tex` 에는 잠정안(A.M.C.: Software; Investigation; Writing---review \& editing / J.S.: Investigation; Data curation; Writing---review \& editing)을 `\todo` 로 넣어 두었다.

**부수 확인 — back matter 에 `Ethics` 절이 있다.** 가이드 목록에는 없으나 확인한 2편 모두 짧은 `Ethics` 절을 두고 있어 `main.tex` 에 추가했다. Methods 의 상세 진술은 그대로 둔다. 또한 두 편 모두 heading 이 `Declaration of Competing Interest`(단수)로, 가이드 문언(복수)과 다르다 — 조판 단계에서 정규화되므로 가이드 문언을 유지한다.

> **참고 (권고를 바꾸지는 않음)**: doi:10.1162/imag_a_00455 의 데이터 진술은 "Data and code will be made available upon reasonable request to the corresponding author." 하나뿐이다. 가이드가 명시적으로 금지한 형태가 게재된 사례이므로 집행이 완전하지는 않다. 그러나 우리 문안(§6)은 이미 더 강하므로 낮출 이유가 없다.

### 10.2 사용자 결정·회신 대기 (다른 작업의 선행 조건)

| # | 항목 | 막고 있는 것 |
|---|---|---|
| **D2** | 공저자 2인(A.M.C., J.S.)의 **CRediT 역할** 회신 — 선택지·확정분은 §10.1a | B2(Author Contributions) |
| ~~D3~~ | ✅ **해소 (2026-08-17)** — 과제번호 없음, 이해충돌 없음. `main.tex` Funding·Competing Interests 실문장 반영 | — |
| **D4** | 🟡 **잠정 반영** — 코드 첨삭 + 파이프라인 그림 제작으로 기재. **① 어느 Figure 인지 번호 확정, ② 투고 직전 재확인**(남은 수정에서 산문 작성에 사용하면 문안을 넓혀야 함) | B7 |
| **D5** | 공저자 3인의 **투고본 승인 + CC BY 동의** | W10 |
| **D6** | 데이터 요청 **응답 기한** (예: 8주) | `main.tex` 의 `[CONFIRM]` |
| **D7** | (선택, 논문 일정과 분리) 파생데이터 공개를 위한 **2차적 이용 IRB 신규 심의** 착수 여부 | 향후 데이터 공개. 투고 자체는 막지 않는다 |

### 10.3 원고 작업 — **어느 것도 사용자 회신을 기다리지 않는다.** 승인된 문안이 있고 아직 `.tex` 에 넣지 않았을 뿐이다

#### P0 — 미반영 수정계획 2건 (2026-08-16 실측 확인)

두 계획 모두 문안이 확정되어 있고 자체적으로 "착수 가능"으로 종결되어 있으나, **`.tex` 에는 하나도 반영되지 않았다.**

| 계획 | 자체 상태 | 실제 반영 |
|---|---|---|
| [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md) A–H | 대부분 "원고 준비 완료 / **필수**" | **0건** — `tab:motion_loco` 없음, §S13 순환이동 확장 없음, Discussion U10 없음, β_c 부호 §S 신설 없음 |
| [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) M1–M9 등 | §7 "남은 차단 요인 없음. `.tex` 착수 가능" | **0건** — 아래 P1–P4 가 전부 미적용 |

**X1 — 지금 원고에 있는 사실과 다른 문장.** `Supplementary/supplementary.tex:46` 은 현재 이렇게 적혀 있다.

> Every neural endpoint was recomputed with the six motion parameters and their temporal derivatives added to the second-level design matrix.

presubmission 계획 §2 가 **"현행 §S2 L46 은 사실과 다르다"** 로 명시한 문장이다. 실제 재산출된 것은 disparity·동결 투영 순열·split-half 신뢰도뿐이었고 hV4 LOCO adjacent accuracy 는 그 시점에 재산출된 적이 없었다. 이후 산출했으므로 1차 세션에 한해서는 참이 되었으나 **exp2 종점은 여전히 재산출되지 않았으므로 범위 한정 문구가 필요**하다. 계획 §2 에 교체 문안이 있다. **형식 항목보다 우선한다.**

**주의 — 계획 H 의 슬롯 충돌.** presubmission 계획은 β_c 부호 강건성을 "§S16 신설"로 적었으나, 현재 S16 은 이미 `Comparison with Retinal-Family Distortion Models` 이고 supplementary 는 S21 까지 차 있다. **신설 번호는 S22 가 되어야 한다** (= 계획 I3 이 지적한 번호표 stale 의 실제 영향).

#### P1–P10 — 개별 항목

| # | 항목 | 대상 | 근거 문서 |
|---|---|---|---|
| **P1** | 제목 T4 교체 | `main.tex:63` (현행 `Individual-specific distortion…` 그대로) | `REVISION_PLAN_HMC_DISCLOSURE` M9 |
| **P2** | 초록 교체 (M7 + M8 IN 판, `differently in each individual` 제거) | `main.tex` abstract | 동 M7·M8, `FRAMING…` §4 |
| **P3** | 본문 HMC disclosure 6곳 (M1–M6) | `results_v4.tex:40,56,60`, §3.3, `discussion_v3.tex:33,69` | 동 §1 |
| **P4** | Discussion 한계 문단 확장 + §S2 문단·표(`tab:hmc_robustness`) + 그림 캡션 별표 강등 | `discussion_v3.tex:60`, `supplementary.tex`, Fig 3 | 동 §2·§3·§4 |
| **P5** | 서론 첫 문단을 §1.1 의 허용 프레이밍으로 재작성 | `introduction_v2.tex` | 본 문서 §1.1 |
| ~~P6~~ | ✅ `american` 통일 완료 |
| ~~P7~~ | ✅ `lineno` + amsmath 패치. 수식 8개 생존 확인 |
| ~~P8~~ | ✅ `\section*` 로 분리 완료 |
| **P9** | 🟡 8/9 완료 + fig2 레이아웃 결함 1건 수정. 잔여 = fig1_generated_v2 · fig3_workflow (수작업 합성물) |
| ~~P10~~ | ✅ `imag-ms-template` 전환 + 인용 93건 remap 완료. 72쪽 클린 |

### 10.4 공개·인프라

| # | 항목 |
|---|---|
| **R1** | GitHub repo **public 전환** 확인 (private 이면 심사자가 코드 접근 불가) |
| ~~R2~~ | ✅ **완료 (2026-08-17)** — 구 Methods/Supplementary 사본 9개를 `archive/methods_superseded_2026-08-17/`(README 포함)로 이동. `Methods/` 에는 정본 `methods_v2.tex` 만 남음. 빌드 92쪽 유지 |
| **R3** | release 태그 → **Zenodo DOI 발급** → `main.tex` 및 `bibliography.bib` 반영 |
| ~~R4~~ | ✅ **완료 (2026-08-17)** — 표를 실제 S1–S21 로 교체하고 신설 2절(S11 Alignment Robustness, S15 Session-1 Thresholds)을 표기. **본문 `\S S…` 참조 17건 전수 재검증 결과 17/17 정상** — stale 한 것은 표뿐이었고 원고 수정은 불요했다 |

### 10.5 제출 시스템 입력물

| # | 항목 |
|---|---|
| **S1** | **커버레터** — 4블록 구조. 초안 [`COVER_LETTER_DRAFT.md`](COVER_LETTER_DRAFT.md). **블록 3(B8) 확정 — SD4H non-archival 확인(2026-08-16)으로 선행 출판물 아님.** 블록 1(scope, P1·P2 후)·2(요약)·4(AI 진술, D4) 미작성 |
| **S2** | **추천 심사자 ≥ 5인** — 서울대 소속 배제, 최근 공저·협업 이력 배제. 저자 4인 전원 기준으로 충돌 개별 검증 |
| **S3** | Editorial Manager 계정 생성 및 제출 |
| **S4** | APC $1,400 예산 확인 (한국은 면제 대상국 아님) |
| **S5** | 최종 재빌드 → 페이지·상호참조·수치 검증 (`colorblind_main.pdf` 는 2026-08-08 빌드로 stale) |

### 10.6 의존 관계

```
D1 ─→ 6.1 / 6.2 / main.tex 데이터 절 확정 ─┐
D2·D3·D4 ─→ back matter \todo 3건 해소 ────┤
D5 ─────────────────────────────────────────┼─→ S5 최종 빌드 ─→ S3 제출
P1·P2·P3·P4·P5 (원고 본문) ────────────────┤
P6–P10 (형식) ──────────────────────────────┤
R1·R2·R3 ──→ 코드 접근성 ───────────────────┘
                    S1·S2 는 P1·P2 확정 후 착수 (제목·초록 문안을 인용하므로)
```

**임계 경로는 D1 이다.** 파생데이터 공개 가부가 정해지지 않으면 Data and Code Availability 절이 확정되지 않고, 그 절이 확정되지 않으면 최종 빌드에 들어갈 수 없다.
