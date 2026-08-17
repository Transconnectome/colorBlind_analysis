# 커버레터 초안 — Imaging Neuroscience

> 체크리스트: [`SUBMISSION_CHECKLIST_IMAGING_NEURO.md`](SUBMISSION_CHECKLIST_IMAGING_NEURO.md) §10.5 S1 (= B5).
> 커버레터는 4개 블록으로 구성한다. 현재 **블록 3(B8)만 작성됨.**
>
> 1. Scope & significance — 체크리스트 §1.1 의 4단 논증 + IRB 비임상 판정. **P1·P2(제목·초록) 확정 후 착수.**
> 2. Article type & 요약 — Research article, 자기 분야 밖 에디터를 독자로 상정.
> 3. **Prior and related dissemination (B8)** — 아래 작성 완료.
> 4. AI 도구 사용 진술 (B7) — 본문 Acknowledgements 와 **동일 문구**. D4 회신 대기.

---

## 블록 3 — Prior and related dissemination (B8)

### 근거로 삼은 사실 (2026-08-16 확인)

| 항목 | 확인 내용 | 출처 |
|---|---|---|
| 워크숍 논문 | ICML 2026 SD4H, "Inferring Individualized Color-Vision Distortions from fMRI Hue-Representation Geometry", 9쪽 | `docs/ICML_workshop/SD4H_cameraready_pathB.{tex,pdf}` |
| 저자 | 4인, **순서까지 본 원고와 동일** | 동 `:61-64` |
| 겹치는 것 | 동일 참여자·동일 1차 세션 데이터, 2-parameter 피질 모델, 해석적 역산 | 동 abstract |
| **겹치지 않는 것** | 워크숍 논문은 **필터 평가를 보고하지 않는다** — 초록이 그것을 `the framework's defined next test` 로 명시 | 동 abstract 마지막 문장 |
| 본 원고 신규분 | 2차 세션(영상+심리물리) 전량, 4-arm 전처리 민감도, 지표 신뢰도 ICC, 전체 Methods | — |
| 포스터 | 동일 워크숍 포스터에 2차 세션 패널 1개를 **preliminary/exploratory 라벨**로 추가 게시 | `POSTER_TEXT_DRAFT.md:6,140` |
| **문면 중복** | 동일 문장 **0개**. 8-gram 중복 **0.32%** (4,435 중 14), 그중 10/14 가 소속 문자열 | 실측 |
| 랜딩페이지 | `https://haba6030.github.io/colorblind_ICML/` 공개 중 | `docs/ICML_workshop/index.html` |
| 졸업논문 | 서울대 심리학과 학사 졸업논문(2027 전기 예정), **미제출·미기탁** | `docs/PSYCH_THESIS`, 지도교수 날인 대기 |

### 초안 (영문, 그대로 붙여넣기 가능)

> **Prior and related dissemination.** In line with the journal's policy on closely related work, we disclose the following. Part of this work was presented at the Structured Data 4 Health (SD4H) workshop at ICML 2026, as a workshop paper titled "Inferring Individualized Color-Vision Distortions from fMRI Hue-Representation Geometry" together with an accompanying poster, authored by the same four authors in the same order. That contribution and the present manuscript draw on the same participants and the same first-session data, and both describe the two-parameter cortical model and its analytic inversion into a stimulus-space filter. They differ in what they establish. The workshop paper reports no evaluation of the fitted filters; its abstract names that evaluation as the framework's next test. The present manuscript reports the second imaging and psychophysical session in full, together with the four-arm preprocessing sensitivity analysis, the cross-arm reliability of the interpolation measure, and the complete methods, none of which appear in the workshop contribution. The workshop poster additionally displayed a single panel of second-session data from the two CVD participants, labelled as preliminary and exploratory. The workshop was non-archival: the paper did not appear in published proceedings, and the contribution is therefore not a prior publication. There is no reuse of text between the two documents: we find no sentence in common, and the eight-word-sequence overlap is 0.3%, of which the majority consists of the author affiliation strings. A summary page describing the workshop contribution is publicly available at https://haba6030.github.io/colorblind_ICML/. Finally, a version of this manuscript will serve as the first author's undergraduate degree thesis at Seoul National University, expected in 2027; the thesis has not yet been submitted or deposited. The work reported here is not under consideration at any other journal, and no preprint has been posted.

### 압축본 (커버레터 분량이 빠듯할 때)

> **Prior and related dissemination.** Part of this work appeared at the SD4H workshop at ICML 2026 ("Inferring Individualized Color-Vision Distortions from fMRI Hue-Representation Geometry"), by the same four authors in the same order, drawing on the same participants and first-session data. The workshop was non-archival and the paper did not appear in published proceedings. That contribution reports no evaluation of the fitted filters and names that evaluation as its next test; the present manuscript reports the second imaging and psychophysical session in full, along with the preprocessing sensitivity analysis, the reliability of the interpolation measure, and the complete methods. No text is reused between the two documents (no shared sentence; 0.3% eight-word-sequence overlap, mostly author affiliations). A public summary page is at https://haba6030.github.io/colorblind_ICML/, and a version of this manuscript will serve as the first author's undergraduate degree thesis at Seoul National University in 2027, not yet submitted. The work is not under consideration elsewhere and no preprint has been posted.

### 확인 완료

**SD4H 는 non-archival** (사용자 확인, 2026-08-16). 따라서 워크숍 기여는 **선행 출판물이 아니고**, 이 문단은 원저성 심사의 대상이 아니라 투명성 고지에 해당한다. 두 판본 모두 해당 문장을 반영했다. 원고 본문·참고문헌에 워크숍 논문을 인용할 의무는 없다.

### 쓰지 말아야 할 것

- **중복을 축소하는 표현.** "minor overlap", "largely different" 같은 어휘는 검출 소프트웨어 결과와 대조되는 순간 신뢰를 잃는다. 실측치(0 문장, 0.3%)를 그대로 적는 편이 강하다.
- **졸업논문을 숨기는 것.** 학위논문은 어느 저널에서도 선행 출판으로 보지 않으므로 고지 비용이 0 이다. 적지 않을 이유가 없다.
- **랜딩페이지 비공개 전환.** 이미 색인되었을 수 있고, 내리는 행위 자체가 은폐로 읽힌다. 공개 상태로 두고 고지한다.
