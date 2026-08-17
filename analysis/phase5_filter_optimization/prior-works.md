# Prior-works mapping — what we DID and did NOT inherit

**Purpose**: 우리의 R+C model 과 2-Component model 이 Tregillus 2021 (Curr Biol) 와 Emery 2021 (Vis Res) 에 대해 *정확히 무엇을 빌려왔고, 무엇이 다른지* 를 reviewer-ready 형태로 명시. 향후 paper draft / presentation 의 단일 source-of-truth.

**Why this exists**: 2026-05-20 PI review 에서 표면적 유사성에 근거한 mapping (예: "β_s ≈ Emery 21.4° within 0.1°") 이 active misinformation 임을 확인. NotebookLM fact-check (2026-05-20) 로 우리의 angular dilation 형태는 *prior art 없는 novel formulation* 임이 확인됨. 본 문서가 *공식 정정* 의 single source.

> 📎 **사용 규칙**: paper draft, presentation, README, mathematical_basis 의 prior-works 관련 claim 은 모두 본 문서와 일치해야 함. 불일치 시 본 문서가 우선.

---

## §1. Honest divergence table — mathematical structure side-by-side

각 axis 별로 (Tregillus, Emery, 우리) 의 정확한 형태를 비교. "same as" / "different from" / "no analog" 만 사용 (softening 표현 금지).

### 1.1 Generative formulation

| 차원 | **Tregillus 2021** | **Emery 2021** | **Ours (R+C)** | **Ours (2-Component)** |
|---|---|---|---|---|
| Generative form | $R(c) = R_{max} \cdot \dfrac{(sc \cdot t \cdot c)^{p+q}}{(sc \cdot t \cdot c)^q + c_{50}^q}$ | $f(\theta) = A \cdot \max(0, \cos(\tfrac{180°}{W}(\theta - \phi)))$ | $\theta' = \theta + \Delta\lambda_{\text{Machado-mapped}} + g \cdot \delta_{RG}$ | $\theta' = \theta + \beta_s \cos(\theta - 90°) + \beta_c \cos(\theta - \theta_{conf})$ |
| Output domain | BOLD β (contrast response) | hue-scaling proportion (%) | shifted hue angle (°) | shifted hue angle (°) |
| Input domain | Stimulus contrast $c$ (4 levels) | Stimulus chromaticity angle $\theta$ (36 angles) | Original hue $\theta$ (8 angles) | Original hue $\theta$ (8 angles) |
| Variable that compensates | $sc$ (cortical amplification on contrast) | $A_R, A_G$ (R/G response amplitude) | $g$ (R-G opponent gain) | $\beta_s, \beta_c$ (angular dilation) |
| Mechanistic claim | "Cortical CRF amplification" | "Descriptive, *not* mechanistic" (저자 명시) | Retinal Δλ + cortical R-G gain (cascade) | Cortical opponent rotation (post-hoc hypothesis) |

### 1.2 Per-row "same / different / no analog" verdicts

| Aspect | Ours (R+C) vs Tregillus | Ours (R+C) vs Emery | Ours (2-Comp) vs Tregillus | Ours (2-Comp) vs Emery |
|---|---|---|---|---|
| Output domain | **different** (hue angle vs BOLD β) | **different** (hue angle vs proportion) | **different** | **different** |
| Input domain | **different** (hue angle vs contrast) | **same** (both hue angle, 다른 색공간) | **different** | **same** (different color space) |
| Free DOF | 2 vs 1 | 2 vs 6 | 2 vs 1 | 2 vs 6 |
| Null model | **no analog** (우리는 reduction-null 정의 안 함) | **no analog** | **no analog** | **no analog** |
| Mechanism layer | **partial overlap** (both invoke cortical compensation) | **no overlap** (Emery 명시 non-mechanistic) | **no overlap** (BOLD CRF vs angular shift) | **no overlap** |
| Behavioral anchor | **different** (우리 sc-등가 없음, t 도 없음) | **different** (Emery proportion, 우리 categorical) | **different** | **different** |

---

## §2. What we DID inherit — 정확한 inheritance map

문헌에서 차용한 것은 **concept-level** 이지 **equation/parameter-value level** 아님.

### 2.1 From Tregillus 2021

| 차용 항목 | 어떤 형태로 | 우리 implementation |
|---|---|---|
| **Cortical compensation 가설** | R+C 의 $g$ 가 *cortical opponent gain* 을 표현 (V1 이후 amplification) | `retinal_cortical.py:machado_with_opponent_gain` |
| **Hierarchy 가설** (V1 < V2v < V3v compensation 강도) | hV4 를 primary fit ROI 로, V1 을 secondary 로 둔 forward LOCO gate | `future_phase1_forward_model/results/loco_reinforcement/` |
| **Test structure (4-step null/free-parameter separation)** ⭐ | **현재 partial** — reduction-null bootstrap test 미구현 (A5 pending) | TBD `scripts/reduction_null_test.py` |

⭐ Test structure 차용이 **paper-level inheritance 중 가장 강한 것**. PI 가 요구한 "기존 모델이 행동을 어떻게 썼는지" 의 정공 답.

### 2.2 From Emery 2021

| 차용 항목 | 어떤 형태로 | 우리 implementation |
|---|---|---|
| **Opponent-axis framework** (S-cone axis vs L-M confusion axis 의 cardinal 위치) | 2-Component 의 $\beta_s$ (S-axis 90°), $\beta_c$ (confusion axis θ_conf) anchor 위치 | `forward_models/two_component.py` |
| **Compensation magnitude framing** ("threshold ratio ÷ suprathreshold ratio = gain") | **부분 차용** — Emery 4.1× gain 의 *수학 자체* 는 우리 paradigm 에 적용 불가 (contrast variation 없음). *논리* 만 차용. | N/A as direct measurement |
| **Specificity logic (k-means classifier on fitted params)** | 우리 HC pool n=7 로는 k-means 통계 검정 불가. *Descriptive percentile* 만 사용. | `hc_specificity_check.py` (descriptive only) |

---

## §3. What we did NOT inherit — explicit non-inheritance

다음은 우리 모델에 **들어가지 않은 것**. paper 에서 "Emery/Tregillus-derived X" 같은 표현이 등장하면 본 §3 와 충돌. 모두 제거 대상.

| 항목 | 정정 표현 |
|---|---|
| **β_s ≈ Emery 21.4° (B-Y rotation) within 0.1°** | ❌ **정정**: β_s 는 stimulus-space angular dilation 의 amplitude (degrees of hue shift), Emery 21.4° 는 hue-scaling cosine fit 의 B-Y phase rotation. **다른 quantity, 다른 색공간, 다른 layer**. 우연한 수치 일치. **paper 에서 제거.** |
| **R+C derived from Tregillus** | ❌ **정정**: Tregillus 는 retinal shift 를 *모델링하지 않음*; t (행동 threshold ratio) 만 *입력으로* 사용. 우리 R+C 의 Δλ 는 Machado 2009 에서, g 는 *우리가 새로 도입한* opponent gain. **Tregillus 는 conceptual motivation 만 제공**, generative form 아님. |
| **2-Component grounded in Emery framework** | ❌ **정정**: Emery 의 cosine 은 *descriptive perceptual* (저자 명시 non-mechanistic), stimulus angular shift 아님. 우리 2-Comp 의 angular dilation 은 *우리가 도입한 generative hypothesis*. Emery 와 공유하는 것은 *cardinal axis 선택* (S-axis at 90°/270°) 뿐. **"Emery-derived"는 overclaim, "Emery framework 의 cardinal-axis convention 차용"으로 정정.** |
| **g = -1.10 within Tregillus range** (sub-09) | ❌ **정정**: Tregillus 의 sc 는 BOLD CRF 의 contrast scaling factor (단위: contrast multiplier). 우리 g 는 R-G opponent linear gain (단위: dimensionless mixing coefficient). **두 양은 단위와 layer 가 다름.** Tregillus 의 "20-40% overcompensation" 같은 수치 범위 비교는 부정확. **"both invoke cortical compensation, but quantities are not commensurate"로 정정.** |
| **Three converging lines of evidence** (index.md L53) | ⚠️ **부분 정정**: "converging" 표현 OK 단 "*mechanism-level convergence*" 표현은 부정확. "*Three independent observations consistent with post-receptoral compensation, each measured in a different domain (psychophysics, univariate BOLD, multivariate pattern)*" 로 정정. |

---

## §4. Why our model exists at all — novelty cost

§1-§3 의 결론: **우리의 angular dilation 형태 (2-Comp) 와 retinal+cortical cascade (R+C) 는 둘 다 prior art 없는 novel formulation**. NotebookLM 2026-05-20 fact-check 4 항목 모두 NOT STATED IN SOURCES.

이 novelty 의 *cost* — paper 가 직접 정당화해야 할 것:

### 4.1 R+C 의 정당화 (paper-level)

- **A priori 가설**: CVD 의 색 인지는 두 단계 변형의 cascade — (i) retinal cone shift (Machado), (ii) cortical R-G opponent gain. 두 단계 분리는 *cone fundamental 의 wavelength shift* 와 *opponent contrast 의 ratio amplification* 가 *physically distinct events* 이라는 가정.
- **Falsifier**: R+C 가 데이터를 fit 못 하거나, $g$ 가 non-physiological range (sub-08 g=-2.25, project memory) 로 가면 cascade 가정 의심.
- **현 상태**: sub-08 g=-2.25 (non-physiological), sub-09 g=-1.10 (Tregillus-range). R+C 의 *형태* 가 sub-08 에 부적합 — paper 에 명시.

### 4.2 2-Component 의 정당화 (paper-level)

- **A priori 가설**: Cortical opponent representation 의 *angular distortion* 은 *post-receptoral* 보상 메커니즘. S-axis (90°) 와 confusion axis (θ_conf) 가 cardinal 두 축.
- **Cardinal axis 선택의 근거**:
  - **S-axis at 90°**: Krauskopf, Williams, Heeley 1982 의 cone-opponent cardinal axes. Emery 2021 의 BY-axis fit 도 동일 cardinal 위치를 confirm.
  - **Confusion axis θ_conf** (protan 16°, deutan 150°): Stockman & Sharpe cone fundamentals 에서 유도된 isochromatic confusion line.
- **Falsifier**: pre-image bijectivity 실패 (2-Comp 는 sub-08/09 모두 8/8 exact ✓), 또는 HC pool 에 적용 시 statistical specificity 부재 (HC FPR=100%, project memory — 우리가 이미 paper-level 한계로 인정).

### 4.3 Cost summary

- ✅ **Reviewer-positive**: 형태가 novel, 명확히 falsifiable.
- ⚠️ **Reviewer-negative**: prior-art absence 가 "ad hoc fit" 의심 트리거. **Phase 3 의 behavioral acquisition 으로 reduction-null test 통과** 가 유일한 강한 답.

---

## §5. Behavioral anchor — what's already gathered vs what's needed

> **정정 2026-05-20**: 초안에서 "behavioral threshold 없음" 으로 기록했으나, 데이터 inventory 의 표면적 검증 (`raw_behav.md` 만 확인) 으로 인한 잘못된 결론. 사용자 catch 후 정정.

### 5.1 이미 가용 — Sub-08 (즉시 사용 가능)

| 측정 | 위치 | 우리 paradigm 에서의 위치 |
|---|---|---|
| **JND** (8 hue pair, adaptive 2AFC staircase) | `future_phase3_behavioral_analysis/results/jnd_summary.csv` | HC group reference n=7. sub-08 vs HC 의 *per-pair ratio* = Tregillus 의 t 등가물. |
| **8AFC accuracy** (64 trial, RSVP color category discrimination) | `data/behavior/sub-08_rsvp_8afc_ses1_run1.csv` | per-hue confusion structure. LOCO-vulnerable hue 와의 set-intersection 검정 가능. |
| **Per-hue integration table** | `future_phase3_behavioral_analysis/behavioral_alignment_2026-05-19.md` | δθ filter / 8AFC acc / LOCO sig / JND vs HC / 방향 의 통합 표. **LOCO–JND 6/6 concordance** 이미 추출됨. |

→ **Tregillus 식 test-structure inheritance 가 sub-08 으로 *지금 가능***. Phase 3 acquisition wait 불필요.

### 5.2 신규 acquisition 필요 — Sub-09 (사용자가 신속 가능 확인)

| 측정 | 우선순위 | 비고 |
|---|---|---|
| **JND 8 hue pair** (sub-08 과 동일 protocol) | **HIGH** — first priority | adaptive 2AFC staircase, 0.8 / 0.5 수렴, 8 pair 검사 |
| **8AFC 64 trial** (sub-08 과 동일 protocol) | **HIGH** — first priority | RSVP, 1 run, 1 session |
| **Anomaloscope quotient** | MEDIUM (nice-to-have) | severity classification gold standard. 측정 가능하면 추가, 없어도 paper 진행 가능. |
| **Filter vs sham vs control 3-way discrimination** | MEDIUM | Independent behavioral validation. Phase 3 본실험. |

→ **Phase 3 의 first priority = sub-09 의 sub-08-equivalent behavioral session 1 회**. 새로운 paradigm 도입이 아니라 *기존 protocol 의 반복*.

### 5.3 PI 의 "행동 데이터를 어떻게 썼는지" 요구의 정확한 답

Tregillus 의 *literal* contrast threshold ratio (t) 는 우리에게 없음 (contrast variation paradigm 아님). 하지만 **behavioral anchor 의 정신** (행동으로 null/alternative pattern 을 외부에서 못박기) 은 우리 JND ratio + 8AFC pattern 으로 달성 가능:

| Tregillus 단계 | sub-08 의 우리 실현 형태 |
|---|---|
| 1. CN reference fixed | HC n=7 LOCO ρ profile + HC group JND |
| 2. Behavioral anchor (외부에서 못박힘) | sub-08 의 *per-pair JND ratio* + *8AFC per-hue accuracy* |
| 3. 1-DOF amplification fit | (β_s, β_c) = (38°, −14°) reduction-null test, H₀ = (0,0) |
| 4. Independent validation | LOCO-vulnerable hue (orange, yellow, purple, |δθ|≥30.5°) 와 JND-HYPO hue / 8AFC-low hue 의 set-intersection. **현재 6/6 concordance**. |

→ **이 inheritance 가 PI 의 정확한 답**. equation copy 가 아니라 *test-logic copy*.

### 5.4 Cost paid by literature divergence

Tregillus 의 *수치* (sc, V2v=6.39, V3v=7.82) 와 직접 비교는 불가능. **하지만** structure-level inheritance 가 강하므로 reviewer 가 "다른 모델이지만 비슷한 검정 논리" 로 받아들일 가능성 높음. paper Methods 에서 명확히 명시 필요:
> "We adopt the *test structure* of Tregillus et al. (2021) — behavioral anchor + reduction null + 1-DOF amplification — but with substitutions appropriate to our paradigm: per-pair JND ratio replaces contrast threshold ratio, (β_s, β_c) = (0, 0) replaces sc = 1, and LOCO-vulnerable hue set replaces V2v/V3v ROI. The substitutions preserve the null/free-parameter separation but produce values that are not directly commensurate with Tregillus's sc."

---

## §6. Quick reference — paper drafting 시 dos and don'ts

| ✅ DO | ❌ DON'T |
|---|---|
| "Motivated by Tregillus's cortical compensation framework" | "Tregillus's R+C model" |
| "We adopt Emery's cardinal-axis convention (S at 90°)" | "Emery-derived 2-component model" |
| "Both our β_s and Emery's B-Y rotation are 1st-harmonic descriptors of post-receptoral compensation" | "β_s converges with Emery's 21.4° within 0.1°" |
| "Three independent lines of evidence each in a different measurement domain" | "Three converging mechanism-level findings" |
| "Our model is a novel angular-dilation formulation; no prior art in the surveyed literature performs cone-shift Δλ on multivariate fMRI patterns" | "Our model extends Tregillus/Emery" |
| "We inherit Tregillus's *test structure* (CN-reference → behavioral t → 1-DOF amplification → t-test vs reduction null)" | "We replicate Tregillus's sc t-test" (we cannot — no t) |

---

## §7. Living change log

| Date | Change | Reason |
|---|---|---|
| 2026-05-20 | Initial draft | PI review 의 Option 1 vs Option 2 false binary 확인 후 |

다음 update 가 필요한 trigger:
- Phase 3 behavioral acquisition 완료 → §5 의 measurement 가 actually 수집됨
- 새 prior-art 발견 (semantic-scholar 검색 또는 PI 추천)
- Paper draft 의 reviewer pushback
