# PI-feedback — Prior-work mapping & model validation plan

**Living tracker** for PI review thread on **Model & Loss Selection Validation (double-dipping concern)**.
Owner: 김지닐 · Started: 2026-05-20 · Source-of-truth for related decisions.

---

## §0. Context

PI 가 Phase 2 review 에서 **"Model selection criteria 가 evaluation criteria 와 동일 = double dipping"** 을 핵심으로 지적. 후속 분석 (2026-05-19 ~ 20) 에서 사용자가 직접 확인한 추가 사실:

> "R+C 는 아이디어만 같았고 (Tregillus 는 retina 이동 자체를 모델링 안 함, BOLD CRF amplification 만 다룸). 2-comp 는 아예 달랐다 (Emery 의 cosine 은 perceptual descriptive 모델, stimulus angular shift 가 아님). 우리의 기존 모델-문헌 mapping 은 잘못된 가정."

**(작은 정정)** 사용자 표현 "Emery 가 retina 함수를 행동 묘사로 표현" 은 부정확. Emery 의 cosine 은 retina 모델도 cortical 모델도 아닌 **purely descriptive perceptual** ("not intended as a mechanistic account" — Emery 2021 직접 인용). 결론 ("우리 2-comp 와 다르다") 은 정확.

이 문서가 추적할 것:
1. 잘못된 mapping 의 정정 (prior-works.md 와 cross-link).
2. PI 의 systematic comparison 요구를 *현재 데이터로* 답할 수 있는 정직한 plan.
3. Phase 3 acquisition 으로 가능해지는 추가 검증.
4. 진행 추적 (Living log).

---

## §1. The false binary — Option 1 vs Option 2 가 답이 아니다

사용자가 제시한 두 옵션:
- **Option 1** "기존 모델을 문헌에 맞게 업데이트" (Tregillus 식 ROI별 amplitude + 행동 threshold, 또는 Emery 식 R/G/B/Y 개별 cosine)
- **Option 2** "현재 모델 개선 + 문헌 맥락 업데이트" (현 모델 유지, 영감 source 만 표시)

**Advisor 의 외부 관점**: 이 둘은 false binary. 사실 점검 결과:

### Option 1 의 실현 가능성 — NotebookLM + 데이터 inventory 로 검증 (2026-05-20 정정)

| 요구 사항 | 우리 paradigm 에 있는가 |
|---|---|
| Contrast variation (Tregillus CRF fit) | **❌ 없음** — 8 colors at *fixed contrast*. CRF 의 4 자유 파라미터 (R_max, c50, p, q) 와 sc 를 분리 추정하는 것은 수학적으로 불가능 (NotebookLM 사실 점검 2026-05-20). |
| Hue scaling proportion (Emery cosine fit) | **❌ 없음** — P2a 는 categorical color naming. Emery 본인 명시: "color naming vs scaling 은 본질적으로 다른 개인차 패턴" (Emery 2021 Discussion). |
| Behavioral threshold / discrimination data (Tregillus-style null anchor) | **⚠️ Partial — sub-08 가용, sub-09 미수집** (2026-05-20 정정). sub-08 에 **JND** (8 hue pair, adaptive 2AFC staircase) + **8AFC** (64 trials, RSVP category discrimination) + HC reference n=7 모두 가용 (`future_phase3_behavioral_analysis/results/jnd_summary.csv`, `data/behavior/sub-08_rsvp_8afc_ses1_run1.csv`). sub-09 는 8AFC CSV 없음, 신속 acquisition 가능. **LOCO–JND concordance 이미 6/6 (sub-08)** — 행동-신경 anchor 가 *지금 강하게 존재*. |

→ Option 1 의 *Tregillus-style*: **sub-08 으로 즉시 prototype 가능**, sub-09 acquisition 1 session 으로 완성. Option 1 의 *Emery-style*: hue scaling paradigm 자체가 새로 필요 (Phase 3 acquisition).

→ 의미: Option 3 (test-structure inheritance) 가 **Phase 3 wait 없이 sub-08 으로 *지금* 시작 가능**. 이전 추정 ("Phase 3 acquisition 필수") 은 *부분적으로만* 정확.

---

## §2. Decisive facts (NotebookLM 2026-05-20 fact-check)

| 질문 | 답 | 출처 |
|---|---|---|
| Tregillus 외에 cone-shift Δλ 를 fMRI BOLD 에 직접 fit 한 선례 | **NONE** | NB query 2026-05-20, 노트북 116 sources |
| Emery 외에 stimulus-space angular distortion 의 수식 모델 | **NONE** (Robinson 2023 은 contrast 축 nonlinearity, hue angle 아님) | NB query 2026-05-20 |
| Fixed-contrast paradigm 에서 Tregillus 식 CRF 변형 적용 선례 | **NONE** (수학적으로 분리 불가) | NB query 2026-05-20 |
| Color naming 으로 Emery cosine fit 한 선례 | **NONE** (Emery 본인이 두 방식의 본질 차이 명시) | NB query 2026-05-20 |

**결론**: 우리의 angular dilation 모델 (β_s, β_c) 와 R+C (Δλ, g) 는 모두 **prior art 없는 novel 형태**. Tregillus/Emery 는 *concept-level 영감* 일 뿐, *equation/parameter level connection 없음*.

→ Novelty 가 큰 만큼 **biological-grounding 으로 paper-level 정당화**를 직접 해야 함. 문헌 의존 약함.

---

## §3. Option 3 — Advisor 가 제안한 정공법

**두 부분 동시 진행 (sprint 단위로 묶음)**:

### Part A — Honest reframe (paper-killing risk 즉시 차단)

1. **prior-works.md 작성** (separate file) — 우리 모델 vs Tregillus/Emery 의 mathematical structure 차이 명시.
2. **3 곳의 overclaim surgical removal**:
   - README L286-L289, L309 — "Within 0.1-3 deg" 표 제거 또는 강력한 qualifier
   - mathematical_basis.md L310 — "Emery framework borrow" → "S-axis 90°/270° 의 cardinal 위치 라는 *cardinal-axis 가설* 차용 (parameter convergence 아님)"
   - Any paper draft / supplementary text 검색 후 동일 정정
3. **CLAUDE.md §0 에 prior-works.md 참조 추가** — 향후 세션이 잘못된 mapping 으로 회귀하지 않도록.

### Part B — Tregillus 의 *test structure* 만 차용 (equation 아님)

PI 가 "기존 모델이 행동을 어떻게 썼는지" 라고 요구한 것의 정공 답은 **Tregillus 의 4 단계 null/free-parameter 분리** 차용 (2026-05-20 정정):

| Tregillus 단계 | Tregillus 의 실체 | 우리 변환 | sub-08 가용성 |
|---|---|---|:---:|
| 1. CN reference | CN 그룹 평균 β 에 4-param CRF fit | **HC mean LOCO ρ profile** (8-vec) + **HC group JND** (n=7 reference) | ✓ |
| 2. Behavioral anchor (Tregillus 의 t 등가물) | AT/CN contrast threshold ratio | **per-pair JND ratio** = sub-08 JND / HC group JND (= sub-08: 3.02× orange-yellow, 3.10× yellow-green, 2.87× yellow-purple, 0.73× blue-purple, …) **+ 8AFC accuracy** (62.5–100%) | ✓ (sub-08), ⚠️ (sub-09 미수집) |
| 3. 1-DOF amplification fit | sc 자유 파라미터 1 개 | **(β_s, β_c) reduction-null test**: H₀ 는 (0,0) "no shift"; *behavioral anchor 와의 일치* 가 alternative | ✓ (1326 grid 기존) |
| 4. 검정 | t-test on log(sc) vs 1 | **(a) Bootstrap test of L_fit(argmin) vs L_fit(0,0)** on HC pool; **(b) (β_s, β_c) 가 *behavioral anchor* 와 일치** — LOCO-vulnerable hue 와 JND-HYPO hue 의 set 일치 검정 | ✓ |

→ **Sub-08 으로 단계 1-4 *전부 즉시 시행 가능***. Tregillus 의 *literal t (contrast threshold ratio)* 는 우리에게 없지만, *behavioral anchor 의 정신* (행동으로 null/alternative 의 expected pattern 을 *외부에서* 못박는 것) 은 우리 JND ratio 와 8AFC pattern 으로 달성 가능.

→ **Sub-09 의 동일 데이터 acquisition 이 paper-completeness 의 first priority**. 이는 *새로운 paradigm 도입이 아니라* sub-08 에 이미 적용된 JND + 8AFC 의 *반복*.

→ 이전 "Phase 3 의 first priority 는 anomaloscope quotient 또는 8AFC threshold acquisition" 표현은 부정확. 정확한 표현: **"sub-09 의 sub-08-equivalent behavioral session 1 회 acquisition"**. Anomaloscope 는 nice-to-have (severity classification 의 gold standard).

---

## §4. Action items & status

| ID | Action | Status | Note |
|---|---|---|---|
| A1 | prior-works.md 작성 | **completed 2026-05-20** | §1 divergence table, §2 inheritance, §3 non-inheritance, §4 novelty justification, §5 Phase 3 crosswalk |
| A2 | README L286-L309 정정 | **pending** | 사용자 승인 후 surgical edit |
| A3 | mathematical_basis.md L310 정정 | **pending** | 동일 |
| A4 | future_phase2 CLAUDE.md §0 에 prior-works.md 참조 추가 | **pending** | A1 완료 후 |
| A5 | Tregillus 식 4-step test structure 의 우리 변환 — **reduction-null bootstrap test + behavioral-anchor concordance test** 코드 작성 | **pending** | scripts/reduction_null_test.py (제안). (a) 1326 grid 의 argmin L_fit vs (0,0) L_fit, HC pool 1000 bootstrap. (b) sub-08 의 (β_s=38°, β_c=−14°) argmin 의 LOCO-vulnerable hue set 이 8AFC <90% 또는 JND >2× HC 의 hue set 과 일치하는지 (set-intersection 검정). |
| A6 | **Sub-09 의 sub-08-equivalent behavioral acquisition** (JND 8 pair + 8AFC 64 trials, 1 session) | **pending** | future_phase3 의 paradigm 그대로 반복. Phase 3 의 first priority. |
| A7 | 행동-only baseline sim (PI Action Note 직접 답) — **새로운 정의**: sub-08 JND ratio + 8AFC pattern 으로 (β_s, β_c) fit → 신경-fit 과 일치 여부 | **pending** | sub-08 한정 (sub-09 acquisition 후 양쪽). 1326 grid 의 *behavioral-defined* loss 와 *neural-defined* L_LOCO loss 의 argmin 거리. |
| A8 | Paper draft / presentation 의 동일 overclaim 검색 정정 | **pending** | grep 후 |

---

## §6. Related files

- `prior-works.md` — Mathematical mapping (Tregillus/Emery vs ours), reviewer-ready.
- `pipeline_summary_for_PI_20260519.md` — Phase 2 pipeline + double-dipping risk map (§10).
- `literature_comparison_20260519.md` — Initial 4-question NB extraction (Machado/Tregillus/Emery method/data/loss/validation).
- `critique_double_dipping_20260519.md` — Reviewer-style critique (B1-B5, C1-C3, D1-D3).
- `CLAUDE.md` §0 — Framework decision (specificity claim 금지, P2a reporting policy).
- `raw_behav.md` — sub-08/09 의 categorical color naming (P2a primary input).
- `../future_phase3_behavioral_analysis/behavioral_alignment_2026-05-19.md` — **sub-08 의 per-hue JND/8AFC/LOCO/δθ 통합 표 + LOCO–JND 6/6 concordance** (Option 3 의 behavioral anchor source).
- `../future_phase3_behavioral_analysis/results/jnd_summary.csv` — 8 pair JND, HC n=7 reference.
- `data/behavior/sub-08_rsvp_8afc_ses1_run1.csv` — 8AFC 64-trial confusion matrix.

---

## §7. Decision log (immutable)

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-20 | Option 1 (model-to-literature) 기각 | 우리 paradigm 에 contrast variation 과 hue scaling 데이터 모두 없음. 수학적으로 불가능. |
| 2026-05-20 | Option 2 (literature framing only) 기각 | 3 곳의 quantitative overclaim 이 reviewer 에 catch 됨. paper-killing risk. |
| 2026-05-20 | Option 3 (honest reframe + test-structure inheritance) 채택 | NotebookLM fact-check + advisor 외부 관점 + 데이터 inventory 가 일치. |
| 2026-05-20 (정정) | ~~Phase 3 의 first priority 로 8AFC threshold acquisition 추가~~ → **sub-08 으로 즉시 prototype, sub-09 의 sub-08-equivalent behavioral session 1 회 acquisition 이 Phase 3 의 first priority** | 사용자 catch 로 sub-08 JND/8AFC 가용 확인. Tregillus inheritance 가 sub-08 으로 즉시 가능. sub-09 만 acquisition 필요. |
