# Methods 재편 제안 (검토용 · 미적용)

> 작성 2026-07-14. 대상 = `docs/PAPER/Methods/methods_v2.tex`.
> **이 문서는 서술 흐름 제안일 뿐, tex 미수정.** 검토·합의 후 적용.
> 범위 = Methods 단독. abstract/results/discussion의 N=2 reframe은 **다른 작업창에서 진행 중**이므로, 여기서는 Methods에서 두 CVD 복수 서술을 **단독으로** 반영해도 됨(사용자 승인).

---

## 확정된 합의 (이 위에서 문구 작성)

1. **8AFC** = Session-1 same-day baseline + Session-2 재실시. 기능 구분 유지: **JND = 피팅 loss(L_γ) 공급 / 8AFC = 검증 전용**.
2. **4.2 개명** = "Stimuli and task" → **"fMRI stimuli and task"**.
3. **행동과제 분리** = 4.2 마지막 JND 취득 문단 제거 → 신설 **"Behavioral tasks"**(복수)로 JND+8AFC 도구 기술을 이동.
4. **4.14** = JND 문단 빠지면 **"Filter evaluation"**만 남김.
5. **§4.8** = geometry 분석 섹션으로 유지. **disparity = 집단차 검정(유의성+효과크기) / ΔRDM = 기술적 특성화(+ loss 대상임을 명시)**. ΔRDM은 §4.8에서 **1회만 정의**, §4.10은 재정의 제거 후 참조.
6. **N=2** = Methods 내 "deutan 단독 / protan not collected" 서술 전부 두 CVD로.

---

## 섹션 구조 (before → after)

| 현재 § | 현재 제목 | 후 § | 후 제목 | 변경 |
|---|---|---|---|---|
| 4.1 | Participants | 4.1 | Participants | 무변 |
| 4.2 | Stimuli and task | 4.2 | **fMRI stimuli and task** | 개명 + 마지막 JND 문단 제거 |
| — | — | **4.3** | **Behavioral tasks** (신설) | JND(4.14) + 8AFC 도구 기술 |
| 4.3 | MRI acquisition and preprocessing | 4.4 | (동) | 뒤로 밀림 |
| 4.4 | ROI definition and response estimation | 4.5 | (동) | |
| 4.5 | Shared Response Model | 4.6 | (동) | |
| 4.6 | Forward encoding model | 4.7 | (동) | |
| 4.7 | Two decoding schemes | 4.8 | (동) | |
| 4.8 | Between-group representational dissimilarity | 4.9 | **Representational geometry (disparity and ΔRDM)** | 제목·역할 정리, ΔRDM=단일정의 |
| 4.9 | Candidate CVD distortion models | 4.10 | (동) | |
| 4.10 | Inverse fitting | 4.11 | (동) | L_RDM에서 ΔRDM 재정의 제거 → §geometry 참조 |
| 4.11 | Parameter selection | 4.12 | (동) | |
| 4.12 | Identifiability and recovery | 4.13 | (동) | |
| 4.13 | Stimulus-space filter | 4.14 | (동) | |
| 4.14 | Behavioral tasks | 4.15 | **Filter evaluation** | JND 문단 제거, N=2, "not collected" 제거 |
| 4.15 | Reproducibility | 4.16 | (동) | |

> 배치 근거: "무엇을 수집했나"(fMRI 자극·과제 → 행동 → MRI 취득)를 앞에 묶고, 그 뒤 전처리·분석. 행동과제를 fMRI 패러다임 직후·MRI 취득 앞에 두어 same-day 데이터 수집을 한 블록으로.

---

## 변경 상세 (서술 흐름)

### 4.2 fMRI stimuli and task

- 제목 `Stimuli and task` → `fMRI stimuli and task`.
- **line 47–48 문단 삭제** (JND 취득 타이밍 문단). JND 절차·8AFC는 4.3으로 이관.
- 남는 내용(line 44–46): 8색 자극 정의 + gray filler + RSVP 과제 + Neurodesign + 세션/런 구조(무변).

**수정 초안(제목 + 삭제):**

```latex
\subsection{fMRI stimuli and task}   % ← 개명
\label{sec:methods:stimuli}

% [line 44–46 무변 유지]

% ▼▼▼ 아래 문단(현행 line 47–48) 전체 삭제 ▼▼▼
% All participants completed JND behavioral testing in the same scanning
% session ... alongside a second fMRI acquisition (see the \nameref{...}).
% ▲▲▲ 삭제 — 취득 정보는 §Behavioral tasks 서두 공통문장으로 대체 ▲▲▲
```

### 4.3 Behavioral tasks (신설)

취득 시점은 **섹션 서두 공통 문장**으로 한 번 제시하고, 이후 JND·8AFC 각 문단은 절차만.

**수정 초안:**

```latex
% ──────────────────────────────────────────────────────────────────────────────
\subsection{Behavioral tasks}
\label{sec:methods:behavioral}
% ──────────────────────────────────────────────────────────────────────────────

Two behavioral tasks --- a just-noticeable-difference (JND) discrimination task
and an eight-alternative forced-choice (8AFC) color-identification task --- were
administered on the same day as the main scanning session (Session~1) for all
participants. Both CVD participants additionally repeated both tasks under each
filter in the second session (see the \nameref{sec:methods:filter_eval} section).

\paragraph{Just-noticeable difference (JND).}
Color discrimination thresholds were estimated for eight hue pairs using
two-interleaved 1-up/1-down adaptive staircases, each terminating after eight
reversals \cite{levitt1971}. Pairs spanned three categories: (i) three pairs
hypothesized as universally difficult for both CVD types (yellow--purple,
blue--purple, red--orange), (ii) two pairs probing the deutan confusion axis
(orange--yellow, yellow--green), (iii) two pairs probing the protan confusion
axis (cyan--magenta, green--blue), and (iv) one control pair (red--cyan). For
each pair, the JND ratio $\gamma = \gamma_{\rm CVD} / \bar{\gamma}_{\rm HC}$ was
computed, where $\bar{\gamma}_{\rm HC}$ is the HC mean threshold. Ratios
$\gamma > 1$ indicate elevated discrimination difficulty relative to HC. These
ratios enter the fitting loss as described in \S\ref{sec:methods:twocomp}.

\paragraph{8AFC color identification.}
On each trial a circular chromatic patch was presented, and participants selected
the matching hue from eight options identical to the scanner stimulus set.
Identification accuracy served as an independent behavioral readout and did not
enter the fitting loss. It was compared to Ishihara classifications post-hoc.
```

- JND 문단 = 현행 4.14(line 259–260)에서 취득 타이밍 제거 후 이동.
- 8AFC = 구버전(`methods_v2_HYBRID_backup:321`) 복원 + "검증 전용, 피팅 미사용" 명시.
- `\label{sec:methods:behavioral}`을 이 신설 섹션으로 이동(현재는 구 4.14에 있음) → intro line 16의 `\nameref{sec:methods:behavioral}`가 여기를 가리키게 됨. Filter eval은 새 라벨 `sec:methods:filter_eval`.

### 4.9 Geometric analysis of color representations — 구 4.8

제목 확정: **"Geometric analysis of color representations"**. 역할 정리:

- **disparity = 검정 담당**(무변): RDM(8×8 상관거리) → 상삼각 28 평균 → Crawford–Howell(p + d_cc). all-HC primary + LOSO sensitivity.
- **ΔRDM = 기술적 특성화 + loss 대상 명시**: §4.9에서 **1회 정의**. per-pair 편차(Fig 3A) 기술 + "이 편차구조가 L_RDM 손실 대상"을 한 문장 명시.
- **orphan Spearman ρ 문장 완전 삭제**(확정).

**수정 초안:**

제목·라벨:

```latex
\subsection{Geometric analysis of color representations}   % ← 개명
\label{sec:methods:rdm}   % 라벨 유지(모든 \ref{sec:methods:rdm} 보존)
```

intro 문단(현행 line 138) — 마지막 절의 model-correspondence 함의 제거:

```latex
% OLD:
% ... The between-group RDM difference, $\Delta$RDM, captures which color pairs
% drive the deviation and tests whether a cortical model of the CVD distortion
% accounts for the pattern.
% NEW:
To characterize the representational geometry in SRM-aligned
space, we computed two measures. Mean pairwise disparity captures whether CVD
geometry is globally more dispersed than HC. The between-group RDM difference,
$\Delta$RDM, captures which color pairs drive the deviation and provides the
per-pair geometry read-out that the inverse fit targets (§\ref{sec:methods:twocomp}).
```

"Geometric deviation from HC" 문단(현행 line 143–144) — 재정의는 유지(단일 정의처로 확정), orphan ρ 문장 삭제, loss 연결문 추가:

```latex
\paragraph{Geometric deviation from HC.}   % ← "and model correspondence" 제거
The per-pair deviation of each CVD participant's RDM from the HC mean was
$\Delta\text{RDM} = \text{RDM}_\text{CVD} - \overline{\text{RDM}}_\text{HC}$,
where $\overline{\text{RDM}}_\text{HC}$ is the grand mean RDM over the seven HC
participants (the per-pair pattern is shown as a heatmap, Figure~\ref{fig:geometry}A).
This per-pair deviation structure is the target of the representational loss
$L_{\rm RDM}$ used in the inverse fit (§\ref{sec:methods:twocomp}).
% ▼ 삭제: "Correspondence between the observed ΔRDM and the prediction of the
%          two-component ... Spearman ρ ..." (orphan, forward-ref)
```

> 순환성 차단은 현행 line 68 톤 유지("disparity tests amplitude; ΔRDM shows directional pattern") — Results 쪽 문구라 Methods에선 손대지 않음.

### 4.11 Inverse fitting — 구 4.10 (L_RDM 문단)

- **line 200–201의 ΔRDM 재정의 제거** → §4.9 참조로 교체.
- L_RDM 코사인 손실 수식(eq:lrdm)·나머지 무변.
- 결과: ΔRDM 정의는 문서 전체에서 §4.9 1회.

**수정 초안:**

```latex
% OLD (line 200–201):
% The between-group geometry difference $\Delta\text{RDM} = \text{RDM}_{\rm CVD}
% - \overline{\text{RDM}}_{\rm HC}$ captures which color pairs drive the CVD--HC
% representational deviation (\S\ref{sec:methods:rdm}). For a candidate
% distortion, $\Delta\text{RDM}_{\rm sim}$ is obtained by applying $\delta\theta$
% to the HC mean RDM.
% NEW:
For a candidate distortion, a simulated deviation $\Delta\text{RDM}_{\rm sim}$ is
obtained by applying $\delta\theta$ to the HC mean RDM and comparing it to the
observed $\Delta\text{RDM}$ (\S\ref{sec:methods:rdm}). The loss is the cosine
dissimilarity between the observed and simulated 28-element upper-triangle
vectors:
```

(이후 eq:lrdm 무변)

### 4.15 Filter evaluation — 구 4.14

**"결과맥락을 작성할 게 있나?" → 없음.** Methods 4.15는 **설계·분석 절차만** 담고 결과 수치(0.23→0.31 등)는 전부 Results 소관(다른 작업창). 현행 262–267 문단은 이미 수치 없는 설계/분석 서술이라 그대로 두고, 아래만 바꾸면 됨:
- 제목 `Behavioral tasks` → `Filter evaluation` + 새 라벨.
- JND 문단(259–260) 제거(4.3 이동).
- N=2 반영 + "not collected" 제거.

**수정 초안:**

제목·라벨:

```latex
\subsection{Filter evaluation}
\label{sec:methods:filter_eval}   % ← 신규 라벨 (intro/4.3에서 \nameref로 참조)
```

filter-eval 첫 문단(현행 262–263) — N=2:

```latex
% OLD:
% \paragraph{Filter evaluation (the deutan participant).}
% The deutan participant completed a second scanning session that compared the
% personalized filter and a deployed macOS accessibility filter against the
% unfiltered Session-1 baseline; the protan participant was not collected. ...
% NEW:
Both CVD participants completed a second scanning session that compared the
personalized filter and a deployed macOS accessibility filter against the
unfiltered Session-1 baseline. The personalized filter was the per-subject
2-component stimulus-space pre-image, with parameters frozen from the main
analysis and therefore out-of-sample. Acquisition, comparator, run-count, and
single-case-inference details are given in Supplementary~\S\ref{app:filter_eval}.
```

> 삭제 근거: "different rendering pipelines"는 S16 §Comparator, "movement toward/away from HC reference" 해석 프레임은 S16 §Run-count adequacy에 이미 존재. "corrective mechanism 아님"은 reframe 전역 프레이밍과 중복. → Methods에서 제거, 손실 없음.

재계산 지표 문단(현행 265) = 무변. Cohen's d 문단(현행 267) — behavioral 재실시를 두 CVD로:

```latex
% OLD 마지막 문장:
% Behavioral testing (JND staircases and an 8AFC color-identification task) was
% repeated under both filters, each compared to the unfiltered Session-1 baseline
% and to the HC distribution; this interleaved, cross-session behavioral
% comparison is descriptive.
% NEW:
In both CVD participants, the JND and 8AFC tasks (\S\ref{sec:methods:behavioral})
were repeated under each filter, each compared to the unfiltered Session-1
baseline and to the HC distribution; this interleaved, cross-session behavioral
comparison is descriptive.
```

---

## N=2 서술 지점 체크리스트 (Methods 내)

| line | 현행 | 조치 |
|---|---|---|
| 48 | "The deutan participant additionally completed a second session…" | 삭제(문단째) — 정보는 4.3/4.15로 |
| 16 (intro para) | "evaluated in a repeat fMRI session and a behavioural … battery" | 유지(피험자 수 미명시라 OK). intro 3-stage 문단 Option B는 별도 |
| 262–263 | "the protan participant was not collected" | 제거 + "both CVD participants" |
| 267 | "repeated under both filters" | 두 CVD 명시 |

## 라벨 정합 (grep 확인됨)

- `sec:methods:behavioral` 참조처 = **line 16(intro), line 198(§L_γ)** — 둘 다 **JND/8AFC 내용**을 가리킴 → 라벨을 신설 **4.3에 유지**하면 두 참조 모두 그대로 유효. ✅
- **삭제되는 line 48**도 이 라벨 사용 → 문단째 삭제라 무관.
- Filter eval에는 **기존 `\ref` 없음** → 신규 `sec:methods:filter_eval` 부여 안전(현재는 4.3 서두 `\nameref`만 참조). ✅
- `sec:methods:rdm` 라벨 유지 → 제목만 바뀌고 모든 `\ref{sec:methods:rdm}`(line 16, 179 등) 보존. ✅
- `app:filter_eval`(Supplementary S16)는 무관한 별개 라벨.

---

## intro 3-stage 문단(line 16) — 처리 옵션별 차이

현행 line 16 관련 절: *"…the between-group RDM difference (ΔRDM) captured the per-pair geometric deviation of CVD representational geometry from the HC mean (§rdm)."*

**Option A — 그대로 둠(최소 변경).**
- 여전히 사실 정확(ΔRDM이 per-pair 편차를 포착). `\ref{sec:methods:rdm}` 라벨 유지되니 링크도 안 깨짐.
- 단점: §4.9를 "geometric analysis(=disparity 검정 + ΔRDM)"로 재편하는데, intro는 ΔRDM만 언급 → intro가 disparity(검정 담당)를 안 비춤. 미세한 강조 불일치.

**Option B — disparity+ΔRDM 병기(§4.9 재편과 정합).**
```latex
% NEW:
... and a geometric analysis of the color representations quantified how CVD
representational geometry deviates from the HC mean --- its global dispersion
(pairwise disparity) and its per-pair structure ($\Delta$RDM)
(\S\ref{sec:methods:rdm}).
```
- 장점: intro가 §4.9의 두 측정(검정용 disparity + 특성화용 ΔRDM)을 모두 예고 → 섹션 재편과 완전 정합.
- 비용: intro 문장 1개 재작성(라벨 무변이라 링크 영향 없음).

**차이 요약**: 기능은 A/B 동일(링크·수치 영향 없음). **B는 "geometry를 검정+특성화 두 방식으로 분석했다"는 §4.9 메시지를 intro에서 미리 예고**해 일관성↑. 단순 유지가 목적이면 A. → **확정: Option B** (2026-07-14 사용자 선택, §4.9 개명·역할정리와 한 세트).

*(주의: intro 뒤 "evaluated in a repeat fMRI session and a behavioural … battery (§behavioral)"의 `\nameref{sec:methods:behavioral}`는 라벨이 신설 4.3으로 이동하므로 자동으로 4.3을 가리킴 — OK. 필요 시 "in both CVD participants" 삽입 검토.)*

---

## 해소된 결정사항 (확정)

1. **§4.9 제목** = "Geometric analysis of color representations". ✅
2. **orphan Spearman ρ 문장** = §4.9에서 완전 삭제. ✅
3. **4.3/4.15 8AFC 중복** = 도구 기술은 4.3에만, 4.15는 "the … 8AFC tasks (§Behavioral tasks)"로 참조만. ✅
4. **8AFC 취득 시점** = 4.3 서두 공통 문장(Session-1 전원 + Session-2 두 CVD). ✅

---

## 적용 순서 (합의 후)

1. 4.2 개명 + JND 문단 삭제
2. 4.3 Behavioral tasks 신설(JND 이동 + 8AFC 복원)
3. 4.9 역할 정리(ΔRDM 단일정의 + orphan 제거 + loss 연결문)
4. 4.11 L_RDM 재정의 → 참조로 교체
5. 4.15 제목 변경 + N=2 + not-collected 제거
6. `\ref`/`\nameref`/label 정합 확인 + 컴파일
