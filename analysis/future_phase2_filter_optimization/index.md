# Phase 2 — Literature Positioning & Paper Writing Reference

**Purpose**: 논문 작성 시 우리 연구의 literature positioning을 빠르게 참조하기 위한 single source. 우리 결과의 novelty와 prior work 대비 ablation 차원을 정리.

**Last updated**: 2026-05-04

---

## 1. Three-axis triangulation — 우리 위치

CVD post-receptoral compensation 가설은 세 가지 channel에서 검증되어 왔다. 우리는 세 번째 axis에 위치.

| Study | Channel | Stimuli | Observable | Compensation 측정 |
|---|---|---|---|---|
| **Emery 2021** (Vis Res) | **Behavior (psychophysics)** | MB cone-opponent space, 36 hue × 4 contrast | Hue scaling % per primary (R/G/B/Y) | Cosine fit phase rotation (BY: **21.4° toward S-axis**), 4-fold suprathreshold gain |
| **Tregillus 2021** (Curr Biol) | **fMRI univariate amplitude** | 2 cardinal axes × 4 contrasts | ROI-mean GLM β | Naka-Rushton CRF contrast scaling factor at V2v/V3v (V1 reduced as predicted) |
| **Our project** (Phase 2) | **fMRI multivariate pattern** | 8-hue CIELab L*=75 C*=40 ring × 6 runs | Voxel pattern (LOCO ρ, ΔRDM) | 2-component angular distortion (β_s, β_c) per ROI per subject |

## 2. 우리의 두 advantage (논문 framing 핵심)

### 2-1. vs Tregillus — **Pattern over amplitude**
Tregillus는 univariate ROI-mean β로 "V2v/V3v amplitude가 normal로 회복된다"는 보상량을 측정. 우리는 multivariate voxel pattern으로 **same compensation의 angular geometry**를 측정.

- **이점**: amplitude는 보상의 강도(scalar)만 잡지만, pattern은 보상이 어느 hue 방향으로 작용하는지(direction)까지 분해.
- **증거**: 우리의 cardinal-axis post-hoc (`results/cardinal_axis_amplitude/summary_raw.json`)은 Tregillus pattern (V1 reduced + V2v/V3v normalized)을 replicate **안 함**. sub-08/09 모두 a*-axis가 V1→hV4 hierarchy-wide reduced. 즉 **univariate level은 우리 8-hue paradigm에서 약한 observable**, multivariate가 본질.
- **논문 한 줄**: *"While Tregillus et al. (2021) demonstrated cortical compensation as univariate amplitude scaling on cardinal-axis stimuli, our multivariate pattern analysis reveals the directional structure (β_s, β_c) of this compensation across the full hue circle."*

### 2-2. vs Emery — **Neural over behavioral**
Emery는 hue scaling (perceptual report)을 cosine fit해서 behavioral phase rotation 21.4°를 보고. 우리는 **fMRI cortical pattern에서 같은 angular structure**를 직접 측정.

- **이점**: behavior는 decision-stage / language label이 섞여 있음 (Emery 본인 caveat: "compensation may depend crucially on the task"). Cortical pattern은 percept 형성 단계 직접 측정.
- **증거**: Emery 본인이 "scaling functions cannot be explained by underlying RG/BY opponent responses" — descriptor 모델은 mechanism 아님. 우리는 8 hue × ROI별 voxel pattern으로 **representation 자체**를 측정.
- **논문 한 줄**: *"Where Emery et al. (2021) inferred a 21.4° phase rotation from descriptive cosine fits to hue-scaling responses, we directly measure analogous cortical-representational rotation in V1–hV4 BOLD patterns, bypassing decision-stage and naming-stage confounds."*

**Functional form distinction (sharper)**:

Emery는 perceptual primary "축의 **위치**"가 어디로 이동했나(axis position rotation)를 측정. 우리는 a priori 고정된 reference frame을 두고 각 색이 angular하게 얼마나 휘었나(per-color 1st-harmonic warp)를 측정. 두 모델 다 1st-harmonic descriptor지만 functional form과 observation level이 다르다.

| 차원 | Emery 21.4° | 우리 (β_s, β_c) |
|---|---|---|
| 무엇이 움직이나 | perceptual primary **축의 위치** (axis position rotation) | 각 stimulus의 **representation 위치** (per-color shift) |
| 기준 frame | 없음 (axis가 unknown, 데이터로 fit) | S-axis 90°, confusion axis 16°/150° (a priori 고정) |
| Functional form | uniform shift within a perceptual dimension | 1st-harmonic cosine warp on the hue circle |
| Shift 균일성 | dimension 내 모든 stim에 같은 amount | 자극 각도 따라 달라짐 (cardinal=0, diagonal=max) |
| Observation level | behavioral category space | cortical representation space |

→ **Numerical 비교(21.4° vs β_s ≈ 20°)는 부적절** — 두 값이 다른 functional form, 다른 observation level의 출력. **Structural family identification (1st-harmonic compensation evidence)** 으로만 사용. 이 caveat은 project memory 2026-04-24 entry "Emery connection = STRUCTURE grounding, not VALUE convergence"의 mathematical 정당화.

## 3. Combined positioning — paper Introduction 한 단락

권장 framing (paper Introduction 또는 Discussion):

> Three converging lines of evidence support post-receptoral compensation in anomalous trichromacy: (1) suprathreshold appearance gain in psychophysical hue scaling (Emery et al., 2021), (2) cortical amplitude amplification in V2v/V3v BOLD response functions (Tregillus et al., 2021), and (3) — present study — directional rotation of cortical hue representation across V1–hV4 captured by a 2-component angular dilation model. Our work uniquely combines (a) **direct neural measurement** (avoiding behavioral decision-stage confounds inherent to Emery's hue-scaling descriptor) with (b) **multivariate pattern analysis** (avoiding the univariate-amplitude reduction of Tregillus's single CRF scalar per ROI). The result is a per-subject filter δθ(c) whose angular geometry is grounded in 1st-harmonic descriptors common to all three traditions but quantified in the cortical representation domain.

## 4. Critical caveats — 논문 reviewer가 잡을 포인트

| Caveat | 우리 대응 |
|---|---|
| n=2 actionable CVD (sub-08/09) | Bootstrap CI + behavioral validation. 통계적 specificity claim 포기 (Cycle 13 framework). |
| 8-color resolution은 Emery 36-hue / Tregillus continuous CRF에 비해 sparse | A priori physiological grounding (Emery S-axis, Stockman confusion axis)으로 free DOF를 2개로 제한. |
| 21.4° vs β_s ≈ 20° 수치 우연일 가능성 | 직접 비교 금지 (project memory 2026-04-24). STRUCTURAL grounding으로만 사용. 두 값이 다른 observable. |
| HC pool n: nominal 7 (sub-01~07) but cycle inventory uses **n=6** (sub-07 제외) — **두 다른 reasons** | (a) hV4: sub-07 voxel=16 → correlation distance NaN (real exclusion); (b) V1, V2: sub-07 사용 가능하나 cycle scripts (cycle 1~15)가 cross-ROI consistency 위해 모든 ROI에서 동일 HC pool 적용 → sub-07 통째로 빠짐. 결과적으로 inventory의 모든 HC sanity 평가 (V1/V2/hV4)에서 n=6. **논문 method**: "HC pool size n=6 (sub-07 excluded due to insufficient hV4 voxels [16 < threshold]; for cross-ROI consistency, sub-07 omitted across all ROIs)". Phase A canonical fits (loco_distortion_fit.py)는 n=7 사용 — sub-07이 hV4 NaN이지만 mean computation에서 자동 제외. |
| Tregillus stimuli ≠ our stimuli | Cardinal-axis post-hoc로 univariate-level 비교 시도 (`results/cardinal_axis_amplitude/`). 결과: 직접 replicate 안 됨 → multivariate가 우리 paradigm의 본질적 observable. |

## 5. Cross-reference

| 토픽 | 문서 |
|---|---|
| 2-component / R+C 수식 derivation | `mathematical_basis.md` §5, §5' |
| Behavioral validation (sub-08 PASS) | `behav_validation.md` §3 |
| LOCO-primary filter design | `LOCO_FILTER_PLAN.md` |
| 종합 model 비교 (Machado / R+C / 2-comp) | `COMPREHENSIVE_MODEL_RESULTS.md` |
| Cardinal-axis univariate post-hoc | `results/cardinal_axis_amplitude/summary_raw.json` |
| Project memory (Emery framing 정정 포함) | `~/.claude/projects/.../memory/MEMORY.md` (Behavioral 2026-04-24 entry) |
| Slide 6 Tregillus 비교 + 3-모델 functional form 표 | `presentation/claude_in_ppt_prompts_meeting.md` Slide 6 |
| L1–L5 문헌 연결 audit trail (2026-05-04 closed L2/L3) | `literature_math_link.md` (peer_review/에서 이동, 2026-05-04 업데이트 banner 포함) |

## 6. References (citation 시 직접 사용)

- **Emery, K. J., Kuppuswamy Parthasarathy, M., Joyce, D. S., & Webster, M. A. (2021).** Color perception and compensation in color deficiencies assessed with hue scaling. *Vision Research*, 183, 1–15. https://doi.org/10.1016/j.visres.2021.01.006

- **Tregillus, K. E. M., Isherwood, Z. J., Vanston, J. E., Engel, S. A., MacLeod, D. I. A., Kuriki, I., & Webster, M. A. (2021).** Color compensation in anomalous trichromats assessed with fMRI. *Current Biology*, 31(5), 936–942. https://doi.org/10.1016/j.cub.2020.11.039
  - OSF: https://osf.io/2sv9y (Figures 2B, 3 source data only)

**Open data status (2026-05-04 NotebookLM 확인)**:
- Tregillus: 부분 공개 (CRF용 β values, OSF). Raw fMRI volumes 비공개. Code 비공개.
- Emery: 미공개 statement. Individual data는 main text Fig. 4, 5에 plot으로만.
