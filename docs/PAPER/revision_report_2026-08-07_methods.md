# Revision Report — `Methods/methods_v2.tex` — 2026-08-07

Scope: Methods 전체 (L13–L362). 이번 세션에서 전 절을 코드 대조·개정한 직후 상태.
Rules: `~/.claude/writing/academic_writing_rules.md` §19, §20, §23, §26.
Build at scan time: `exit 0`, fatal 0, undefined 0, BibTeX warning 0, 83 pages.

---

## 1. Reverse outline

각 절의 topic sentence가 절 전체를 대표하는지 검사했다.

| 절 | 요약 | 판정 |
|---|---|---|
| 개관 (L16) | 분석은 특성화 → 모형 적합 → 역산 3단계로 진행된다 | ✓ |
| Participants (L37) | 13명 모집, HC 7 / CVD 2 분석, 단일사례 통계 | ✓ |
| fMRI stimuli (L44–48) | Lab 8색·RSVP·불균형 배분과 그 처리 | ✓ (3단락, 각 1역할) |
| Psychophysical (L55–67) | JND 계단법 + 8AFC | ✓ |
| MRI acq/preproc (L74–76) | 획득 파라미터, 4단계 파이프라인, 미적용 항목 | ✓ |
| ROI & response (L106–126) | 아틀라스 ROI → 2단계 GLM → Procrustes 정렬 | ✓ |
| SRM (L133–139) | 공유공간 추정과 직교성 제약 | ✓ |
| Forward encoding (L146–152) | FE-6 기저, 디코딩=OLS / 인코딩=ridge-GCV | ✓ |
| Two decoding schemes (L172–189) | LORO=런 제거 / LOCO=색 제거, hV4 primary, adjacent accuracy | ✓ |
| Representational geometry (L196–202) | Procrustes disparity와 두 추정량 | ✓ (ΔRDM 이전 후 단일 주제) |
| Candidate models (L226–246) | R+C 1자유도 vs 2-comp 2축 | ✓ |
| Inverse fitting (L253–295) | 3개 손실 원자 → z-합성 → 격자 탐색 | ✓ |
| Parameter selection (L302–313) | 3-gate | ✓ |
| Identifiability (L323–334) | 4개 사전지정 검정 | ✓ (이번 회차 두괄식 전환) |
| Stimulus-space filter (L341–343) | 역상 계산과 수치 검증 | ✓ |
| Filter evaluation (L350–354) | 2차 세션 지표와 단일사례 보고 | ✓ |
| Reproducibility (L361) | 소프트웨어·시드·가용성 | ✓ |

### Drift
Pre-draft 산출물(`pre_draft_<date>.md`)이 없다. 대신 지배 문서
[`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md) §2 흐름과 대조했다.

| 계획 §2 | 현재 | 판정 |
|---|---|---|
| `Methods §기하 → 규칙 선언 + S7 포인터` | L196–202, `Supplementary~\S S7` 포함 | ✓ |
| `Methods §손실 → disparity는 스칼라 → ΔRDM 도입 → 코사인` | L266 (§Inverse fitting 내) | ✓ |
| `PCA 축약 + SRM 일치도` | L279 | ✓ |

**drift 없음.**

### Subsection topic rollup
`[SPLIT?]` 후보 없음. `Two decoding schemes: cross-run classification and cross-color interpolation`은
제목이 두 항목을 나열하나 단일 주제(교차검증 스킴 두 가지)이고 §7 통과.

---

## 1.5 Long sentences (§2)

| 위치 | 길이 | 문제 | 조치 |
|---|---|---|---|
| **L234** | 43어, **세미콜론 2** | `at $g=1$ ...; at $g=2$ ...; at $g>2$ ...` | 열거이므로 유지 가능. 세미콜론을 문장 분할로 바꾸면 3문장 |
| **L253** | 36어, em-dash 2 + 세미콜론 1 | `A specific instance --- for example ... --- is a \emph{loss atom}; candidate objectives are ...` | **분할 권고**: 세미콜론 앞에서 절단 |
| **L256** | 42어 | `where` 절 3개 연쇄 | 수식 정의 문장. 유지 허용 |
| **L266** | 42어 | `and the per-pair difference was ...` | **분할 권고**: `and` 앞 |
| L27 / L133 / L149 / L221 / L246 | 14–23어 | 세미콜론 각 1 | 짧아 가독성 문제 없음. L246만 `; results are reported in` → 마침표 권고 |

---

## 2. §19 Vocabulary

### Tier A — 13 hits, **위반 0**

전부 false positive다. 문맥 확인 결과:

| 패턴 | 위치 | 판정 |
|---|---|---|
| `the first` | L37, L55(×2), L58(×2), L76, L119, L200 | `the first scanning session`, `the first two reversals`, `In the first stage`, `In the first, ...` — 전부 서수 |
| `novel` | L183 | `novel colors` = Brouwer & Heeger 2009의 기술 용어(훈련에 없던 색). 원문 확인 완료 |
| `always` | L58 | `The two discs always differed` — 설계 사실. 수량화 대상 아님 |
| `never` | L172 | `the held-out hue therefore never appeared in training` — 설계 사실 |
| `exhaustive` | L295 | `exhaustive grid` — 바로 뒤에 26×51=1,326셀을 **열거**하므로 §19A 요구 충족 |

### Tier B — 2 hits, **위반 0**

- L37 `The study was approved` — `stud` 정규식 오탐
- L44 `both presentation programs addressed their display in pixel units` — `address`가 소프트웨어 주소지정 의미. untestable verb 용법 아님

### Tier C — **0 hits**

이번 세션 개정으로 `robust`, `significant`(비통계), `accurate`, `effective` 전부 소거됨.

### Tier D — **0 hits**

---

## 3. §20 Citations

### Provenance honesty (§20 말미) — **이번 세션에서 1건 해결**

| 위치 | 이슈 | 상태 |
|---|---|---|
| §S6 | GCV를 `sklearn.linear_model.RidgeCV`에 귀속. `RidgeCV`는 `analysis/`에 **0회** 등장, 실제는 SVD 기반 자체 구현 | ✅ 삭제, 실제 구현·격자로 교체 |
| L361 | `pedregosa2011` 복원 후 Reproducibility 소프트웨어 목록에서 인용 | ✅ `LedoitWolf`/`PCA`/`CCA`/`LDA` 실사용 근거 |

### Method origin — 전수 확인

| 인용 | 주장 유형 | 판정 |
|---|---|---|
| `golub1979` (GCV) | method origin | ✓ 원논문 |
| `brouwer2009` (FE 기저, hV4 우선) | method origin + 특정 실증 | ✓ primary. 비교급 `the regions where their interpolation was strongest`는 **원문 대조 완료** — *"The highest decoding accuracies for novel colors were found for V4 and VO1"* |
| `crawford1998` | method origin | ✓ |
| `machado2009` | method origin (R+C) | ✓ |
| `stockman2000` (cone fundamentals) | method origin | ✓ |
| `wang2015` (아틀라스) | method origin | ✓ |
| `levitt1971` (계단법) | method origin | ✓ |
| `durnez2018` (Neurodesign) | method origin | ✓ (2026-08-06 저자·venue·DOI 정정 완료) |
| `hedges1985` | method origin | ✅ **이번 세션 이동** — LOCO 문단(실제 값은 $d_{cc}$)에서 Hedges' g가 실제 쓰이는 §S1로 |
| `levitas2024`, `dcm2bids` | 소프트웨어 | ✓ |

### Citation density
5+ 스택 **0건**. 최대 3 (`\cite{dale1999, brouwer2009, brouwer2013}` L119, `\cite{kay2008,naselaris2011}` L152).

### Suspect — 0건
비교 구문(`than`, `whereas`, `unlike`)이 인용에 붙은 사례 없음.

---

## 4. §26 Checklist

### Reverse outline
- [✓] 단락당 한 문장 요약 가능
- [✓] 지배 문서 §2 흐름과 일치 (drift 없음)
- [✓] 두 문장을 요구하는 단락 없음

### Claims
- [N/A] 중심 기여 문장 — Methods 범위 밖
- [✓] 수치 Δ에 baseline + metric — Methods의 수치는 파라미터·임계값이며 Δ 주장 없음
- [✓] `first / only / no X` — Tier A 실위반 0
- [✓] untestable verb — 실위반 0
- [✓] vague adjective — 0 hits
- [✓] self-praise — 0 hits

### Citations
- [✓] general → review / specific → primary / method origin → original
- [✓] 5+ 스택 없음
- [✓] provenance honesty (sklearn 허위 귀속 해결)

### Structure
- [✓] 단락당 1역할
- [✓] topic sentence 선두 — 17개 절 전부 통과
- [✓] 대명사 명확
- [**✗**] **용어 일관성 (§4) — 3건, 아래 §4.1**
- [✓] 관찰/해석/함의 분리

### Section-by-section (§23 Methods)
- [✓] Methods 순서가 Results 순서와 일치
  `LORO → LOCO → geometry → R+C → 2comp → identifiability → filter → filter_eval`
- [**✗**] **No results in Methods — 2건, 아래 §4.2**
- [✓] 확립 절차는 원논문 인용
- [✓] detail-altitude — 재현 전용 세부는 §S로 이동됨
- [✓] 변수 최초 등장 시 정의

---

## 4.1 §4 용어 불일치 (Serious, 3건)

| 용어 | Methods | Results | Discussion | 조치 |
|---|---|---|---|---|
| **control 명사** | `HC` 61 / **`control participant` 3** / `healthy control` 2 | `HC` 46 | `HC` 18 | `control participant` 3건 → **`HC participant`**. 이번 세션 §Identifiability 개정 시 유입 |
| **region 명사** | `region` 12 / `ROI` 6 | `ROI` 17 | `ROI` 1 / `region` 2 | 원고 지배 용어는 `ROI`. Methods의 `region` 다수는 이번 세션 유입 → **`ROI`로 통일** |
| **filter 명사** | `individualized filter` 2 / `per-subject filter` 1 | `individualized` 9 / `per-subject` 1 | `individualized` 7 | `individualized filter`로 통일 (Methods 1건, Results 1건) |

세 건 모두 **이번 세션 개정 과정에서 유입**된 것으로, 개정 전 원고는 `HC` / `ROI`로 일관되어 있었다.

---

## 4.2 §23 "No results in Methods" (Serious, 2건)

| 위치 | 문장 | 성격 |
|---|---|---|
| **L279** | `Across the 28 pairwise entries this estimate agreed with the SRM-aligned estimate ... at V1, V2 and hV4 ($r = 0.77$--$0.89$), and less closely at V3 ($r = 0.39$--$0.58$)` | 계획 문서 **M5**가 의도적으로 배치한 PCA 축약 정당화. 수치는 결과 |
| **L343** | `All eight hues resolved to within $10^{-3}$ degrees of their target for both deployed parameter sets` | 이번 세션 신설. 역상 존재가 보장되지 않으므로 검증 결과를 명시 |

둘 다 **의도된 배치**다. §23은 "무엇을 했는가"만 두라 하지만, 두 문장 모두 **방법 선택의 정당화**여서 Results로 옮기면 근거가 사라진다.

권고: 유지하되 결과 서술이 아니라 **검증 진술**로 읽히게 어미를 조정한다.
- L279 → `...so the reduction does not determine the pattern the loss fits` (이미 있음) 유지
- L343 → `and the procedure rejects a parameter set that leaves any hue unresolved` (이미 있음) 유지

**판정: 규칙 위반이나 의도적 예외. 사용자 확인 필요.**

---

## 5. Naive-reader check

**미실행.** 이번 스캔의 범위가 Methods이고, abstract·intro는 이번 세션에서 수정되지 않았다.
Phase 5.5는 abstract + intro를 대상으로 하므로 **전체 원고 대상 실행 시로 이월**한다.

---

## 6. Priority summary

총 이슈 **7건**.

| 등급 | 수 | 내역 |
|---|---|---|
| Fatal | **0** | Tier A 실위반 0, baseline+metric 누락 0 |
| Serious | **5** | 용어 불일치 3 (§4.1), Methods 내 결과 2 (§4.2, 의도적) |
| Minor | **2** | 긴 문장 분할 후보 L253, L266 |

### 권고 순서
1. **§4.1 용어 3건 일괄 치환** — `control participant`→`HC participant`, `region`→`ROI`, `per-subject filter`→`individualized filter`. 기계적이며 위험 낮음
2. **§4.2 2건 사용자 판정** — 유지 / Results 이관 / §S 이관
3. **§1.5 L253·L266 분할** — 세미콜론·`and` 앞 절단
4. L234 세미콜론 3연쇄, L246 세미콜론 — 선택

---

## 7. 이번 세션 코드 대조로 정정한 사실 오류 (참고)

이 리포트의 스캔 대상은 개정 **후** 상태다. 개정 과정에서 코드와 대조해 잡은 오류는 아래와 같다.
전체 근거는 [`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md) §7.

| 항목 | 성격 | Results 파급 |
|---|---|---|
| adjacent accuracy chance `3/8` → `0.25` | 귀무값 오류 | **주장 1건 역전** + 그림 3개 재생성 |
| GCV α `per voxel` → 스칼라 1개 | 추정 절차 | 없음 |
| §S6 sklearn `RidgeCV` 귀속 | 허위 귀속 | 없음 |
| `Hedges' d` → $d_{cc} = t\sqrt{(n+1)/n}$ | 효과크기 정체 | 없음 |
| `L_RDM` 식의 `/2` | 코드 불일치 | 없음 (z-정규화가 상수배 소거) |
| ΔRDM 45° 스냅 / composite z-표준화 | 미기재 절차 | 없음 |
| `L_γ` rank discordance → 표준화 제곱오차 + $\hat\gamma = \bar\gamma_{\rm HC}(d_{\rm phys}/d_{\rm perc})$ | **손실 정의 오류** | 없음 |
| `L_LOCO` HC-trained W → CVD 자체 W, MSE → `mean(1-ρ)` | **손실 정의 오류** | 없음 |
| Gate 1 `signed d` → `abs(d)` | 규칙 진술 (양방향 확정) | 없음 |
| collapse guard / 순위 기준 | 미기재 | 없음 |
| `trial labels` → `color labels`, `full pipeline` → grid search | 검정 절차 | 없음 |
| Brent `1e-3°` → `xtol=1e-9`, 역상 미보장 | 수치 절차 | 없음 |
| forward-tuning Spearman → Pearson, 대상 오류 | 지표 정의 | 없음 |
| seed 42 단일 → 42 / 31337 / 27182 | 재현성 | 없음 |
| `walther2016` 미등록 인용 | 서지 | 없음 |
