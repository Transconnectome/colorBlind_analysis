# ICML 2026 · SD4H — 포스터 텍스트 초안 (v3, **이 파일이 포스터 단일 소스** — build_poster.py 삭제됨, 수동 복붙)

> 규칙: 모든 항목 **개조식 · 한 줄 · 공백포함 ~90자**. 한국어(의미) + 영문 draft(포스터 최종형) 병기.
> 근거: `SD4H_cameraready_pathB_0624_A.pdf`(§1–3, Table 1, Fig 2), `ResearchNOTE.md` §6(2026-07-04). (fig1_prompt.md는 폐기 문서 — 미참조.)
> v3 변경: ⑤ **FE-6 basis 복원**(B-1, 논문 해리 제거) + mechanism 표·역변환 규칙 이관 · ⑥A disparity_roi 제거→통계 bullet화 · ⑥C fig 재생성(N=2 exploratory) · build_poster.py 삭제.
> **모든 수치 camera-ready/ResearchNOTE 대조 완료.** 유일 잔여 해리: Result C(exp2)는 논문에 없는 신규 데이터(논문상 "defined next test") → preliminary 라벨로 정합.

---

## ① Key Claim  — 상단 navy 스트립, 한 줄  *(A안 · 영문 2안 중 택1)*

- 개인의 구조화된 신경 왜곡을 읽어, 개인 맞춤 보정으로 역변환한다.

**안 1 (님 구조 유지, "by…by" 중복 제거):**
```
By reading an individual's structured neural distortion, we invert it into a personalized correction.
```
`(≈99자 — Key Claim strip은 full-width 큰 글씨라 무리 없음)`

**안 2 (≤90 압축):**
```
From an individual's structured neural distortion, we invert a personalized correction.
```
`(86자)`

---

## ② Background & Gap  — 좌열  *(cochlear를 1번 줄에 통합, 4→ 유지)*

- 많은 건강 phenotype(심장¹, 유전자발현²)은 정보의 *소실*이 아니라 *구조적 왜곡*이다.
- 이 왜곡은 같은 진단명 안에서도 **개인마다 다르다**.
- 기존 방법은 왜곡을 *시뮬레이션*하거나 **집단 수준 보정**에 그침 — **개입을 위해** 개인의 왜곡을 *역변환*하는 접근은 **덜 탐구됨**.

```
Health phenotypes (cardiac¹, gene-expression²) are often structured distortions, not signal loss.
Such distortion varies across individuals even within a diagnostic category.
Prior work simulates the loss or applies population-level fixes; inverting a person's own distortion for intervention is under-explored.
```
> line 1: 예시 inline + 위첨자(¹ Biffi, ² Lotfollahi). line 3 대안: `population-level`↔`generic`(camera-ready)/`one-size-fits-all`; 완화어 `under-explored`↔`remains open`.

---

## ③ Contribution  — 좌열, 3줄  *(We-voice, 직관화, loss=조합 반영)*

- **We represent** CVD를 뇌 hue-표상 기하의 *측정 가능한 왜곡*으로 재정의 (RDM + 보간).
- **We fit** 개인마다 2-component 피질 모델을 — 행동(JND)+신경(fMRI) 손실 결합.
- **We invert** 적합 모델을 그 사람의 **색보정 필터**로 뒤집는다.

```
We represent CVD as a distortion of the brain's hue-representation geometry.
We fit a 2-component cortical model per person by combining behavioral & neural (fMRI) losses.
We invert each person's fitted model into their color-correction filter.
```
> naive-reader 반영: `neural→neural (fMRI)`(모달리티 명시). 모델명은 ③④⑤ 전부 **"2-component"** 통일(그림 라벨 정합; 파라미터 수는 ⑤ 표의 β_s·β_c로 노출). CVD·geometry·filter는 제목/④/⑤가 맥락 제공 → 유지.

---

## ④ Framework  — 우열 대형 그림 (`fig1_pipeline_revise.png`, **현행 렌더본**)  *(caption 없이, 메인 한 줄)*

> fig1_prompt.md(REV-3)는 폐기 문서 — 참조 안 함. 아래는 **실제 렌더된 그림** 기준.

**그림(실제)**: 상단 = STRUCTURAL distortion(HC→CVD) + 2-component cortical model(behavioral JND · neural pairwise · component 1/2 축).
하단 파이프라인 4박스: **Response(fMRI hue, V1–hV4) → Diagnose(LOCO + pairwise RDM) → Simulate(distortion simulator) → Correct(color-correction filter)**.

- 메인 한 줄:
```
Diagnose each person's hue distortion, fit a 2-component cortical model as a deficiency simulator, then invert it into a color-correction filter.
```
> 산출물 명시: fit → "deficiency simulator", invert → "color-correction filter". (그림 박스는 "Distortion Simulator" — minor 표기차.)

### FRAMEWORK & MODEL — LOSS  *(프레임워크 그림 하단 배치)*

| Mechanism | DOF | Form |
|---|:-:|---|
| Retinal cone-shift (Machado) | 1 | Δλ |
| Retinal + cortical (R+C) | 1 | δθ = (2−g)·δθ_Machado |
| **Cortical 2-Component** | **2** | θ′ = θ + β_s cos(θ−90°) + β_c cos(θ−θ_conf) |

- **β_s** = S-cone 축, **β_c** = confusion 축 (θ_conf = 16° protan / 150° deutan).
- **Loss atoms** = 행동 JND(γ) + 신경 ΔRDM(per ROI) + hV4 LOCO (z-scored); per-subject 조합을 **held-out 일반화**로 선택 → **γ + ΔRDM 승리** (LOCO는 gate/진단, loss 항 아님).
- **Invert**: 2-Component 사상 bijective → per-hue pre-image θ̃_k (root-finding), δθ_k = θ̃_k − θ_k.

```
Three candidate mechanisms — cone-shift (1-DOF), R+C (1-DOF), 2-component cortical (2-DOF):
  θ′ = θ + β_s cos(θ−90°) + β_c cos(θ−θ_conf)   [β_s S-cone axis, β_c confusion axis].
Loss atoms = behavioral JND (γ) + neural ΔRDM (per ROI) + hV4 LOCO, z-scored.
Per-subject combination selected by held-out generalization → γ + ΔRDM wins (LOCO is a gate/diagnostic).
Invert: the 2-component map is bijective → an exact per-subject color-correction filter.
```

---

## ⑤ Methods — Experiment & Analysis  — 좌열  *(모델·손실은 ④로 이동)*

- Participants (N=10): 7 HC + 3 CVD (2 deutan, 1 protan), Ishihara 확인.
- fMRI: 8 isoluminant hue (CIE L\*a\*b\*, L\*=75), 6 runs, ROI V1–hV4.
- **LOCO** (leave-one-color-out): 뇌가 나머지 7개로 held-out hue를 복원하나? → Forward-Encoding(hue→6 channels→neural responses); **연속 hue 구조** 검사.
- **RDM** (relative distances): hue 쌍이 뇌 표상에서 얼마나 떨어졌나? → SRM(HC·CVD를 **shared low-dim k=3–4** 공간에 투영); **ΔRDM = CVD − HC** = 어느 쌍이 merged/split.

```
Participants (N=10): 7 healthy controls (HC) + 3 CVD (two deutan, one protan).
fMRI: 8 isoluminant hues, 6 runs, ROIs V1–hV4.
LOCO (leave-one-color-out): can the brain rebuild a held-out hue from the other seven?
  Forward-encoding model maps hue → 6 channels → neural responses; tests continuous hue structure.
RDM (relative distances): how far apart are hue pairs in the brain representation?
  SRM projects HC & CVD into a shared low-dim (k=3–4) space; ΔRDM = CVD − HC = which pairs merged/split.
```

---

## ⑥ Results  — 하단 full-width navy 밴드, 3패널 *(헤더 = ③ 대응: Represent · Fit · Validation)*

### A — **Represent · A structured distortion** (exp1)
> **fig** = `srm_wheels.png` (크롭본, 통계 없음, 기하만). 패널 헤더(HC / Sub-08 deutan·V2 / Sub-09 protan·V1)는 포스터 텍스트박스로. `disparity_roi.png` 미사용(세로 부족) → 통계는 아래 bullet.

- 판별(category)은 보존: LORO pooled **p=0.668** — 모든 hue 여전히 decodable.
- 연속 보간은 손상: hV4 adj-acc HC **0.47** (p=.044 >chance) → deutan **0.25** (p=.082) / protan **0.13** (p=.024).
- 왜곡이 **피험자별 다른 ROI**에 국재: sub-08 V2 **p=0.040**, sub-09 V1 **p=0.007** (Crawford–Howell).

```
Category discrimination preserved (LORO pooled p=0.668) — every hue stays decodable.
But continuous interpolation collapses: hV4 adj-acc HC 0.47 (p=.044 vs chance) → deutan 0.25 (p=.082) / protan 0.13 (p=.024).
The distortion localizes to a subject-specific ROI: sub-08 V2 p=0.040, sub-09 V1 p=0.007.
```

### B — **Fit · Deficiency modeling** (exp1)  *(fit + 역변환/필터 포함 — 옵션1)*
- **대안이 실패하므로 2-Component가 유일 타당**: R+C는 overcompensate(saturation gate), retinal-only는 protan에서 non-invertible(4/8 hue) → 2-Component만 격자내부 적합 + 정확 역변환.
- Table 1 (hV4): sub-08 **(+6°,−42°)** L=γ_OY+ΔRDM_V2, sub-09 **(+2°,+24°)** L=γ_all+ΔRDM_V1; exact 역변환(잔차 <0.001°).
- **sub-08**: 신경 항이 **파라미터 안정성**을 부여 — β_c ∈ [−46°,−38°] 전 fold 0 미교차 (신경 7/7 vs 행동 5/7 folds).
- **sub-09**: 신경 항이 결정적 — 행동만이면 3/7 folds, 신경 ΔRDM 추가 시 **7/7 folds**.

```
- Alternatives fail: R+C overcompensates, retinal-only is non-invertible at protan (4/8 hues) —
  so only the 2-Component model both fits and inverts exactly.
- hV4 fits — sub-08 (+6°, −42°): L = γ_OY + ΔRDM_V2 ; sub-09 (+2°, +24°): L = γ_all + ΔRDM_V1. Exact inversion (residual < 0.001°).
- Sub-08: the neural term delivers parameter stability — β_c ∈ [−46°, −38°], no zero-crossing (neural 7/7 vs behavior 5/7 folds).
- Sub-09: the neural term is decisive — behavior alone clears 3/7 folds, adding neural ΔRDM clears 7/7.
```

### C — **Validation** (2nd-MRI, N=2 — **exploratory**) · **fig에 상세 위임, 텍스트 최소**
- 행동(HC-disparity, ↓=HC근접): **Optimal이 Window 이상으로 HC 근접**; sub-09는 **Window가 악화, Optimal이 보존** (marginal, ns).
- 신경 A (hV4 LOCO, 보간): sub-08 Optimal 상승하나 **chance(0.375) 미달**; sub-09 floored.
- 신경 B (V1/V2 SRM-RDM, 기하): sub-09 두 필터 **모두** HC 방향 회복(Window≈Optimal = **filter-general**, 개인화 특이 아님); sub-08 둘 다 악화(자극-구동 초기영역 가설).
- 신경 지표 혼재 → 가설-생성적 (LOCO는 hV4, RDM은 V1/V2에서 신뢰 = 지표별 신뢰 ROI).
- Scope: **descriptive proof-of-concept, N=2** (한계는 ⑦에서).

```
Behavior (HC-disparity, ↓ = HC-like):
Optimal ≥ Window in HC-likeness
For Protan, Window harms, Optimal preserves (marginal, ns)
Neural (hV4 LOCO):
Deutan rises at Optimal but below chance
Protan remains floored
Neural (V1/V2 SRM-RDM):
Protan recovers toward HC under both filters (Window ≈ Optimal)
Deutan shifts away (stimulus-driven early area)
Descriptive proof-of-concept, N=2 · reliable ROI: LOCO hV4, RDM V1/V2
```

---

## ⑦ Conclusion  — 좌열  *(Key Claim 재진술 금지 — 한계+다음, Next 재정의)*

- **framework을 end-to-end 시연**: 구조적 왜곡 → 2-DOF 적합 → 해석적 역변환 → 필터.
- 행동 HC-disparity는 개인화 필터를 지지(marginal, N=2); 신경 효과는 exploratory.
- 한계: N=2, 지표·피험자 간 이질성(통합 기하 read-out 미비), confound(run-position · rendering).
- **다음**: (1) raw geometry를 통합한 **unified geometry target** 확립, (2) 지표·ROI **해리 원인 규명**, (3) 큰 N.

```
End-to-end framework shown: structured distortion → 2-DOF fit → analytic inversion → filter.
Behavioral HC-disparity favors the personalized filter (marginal, N=2); neural effects exploratory.
Limits: N=2; heterogeneous results across metrics/subjects; run/rendering confounds.
Next: a unified geometry target (integrating raw geometry across metrics/ROIs); resolve the dissociation; larger N.
```

---

## Figure 배치 맵 (24×36 세로 2단)

```
┌─────────────────────────────────────────────────────┐
│ HEADER: 제목 · 저자 4인 · QR(랜딩페이지)               │
│ ① KEY CLAIM   (navy strip, full-width)               │
├───────────────────────┬─────────────────────────────┤
│ COL 1 (텍스트)         │ COL 2                        │
│ ② Background & Gap    │ ④ FRAMEWORK                  │
│ ③ Contribution        │   [fig1_pipeline_revise.png] │
│ ⑤ Methods (+mech 표)  │   대형, 열 세로로 span         │
├───────────────────────┴─────────────────────────────┤
│ ▌▌  RESULTS 밴드 (full-width, 3 패널)  ▌▌             │
│ ┌──────────────┬──────────────┬───────────────────┐ │
│ │ A 존재        │ B 역변환      │ C 작동(2nd MRI)    │ │
│ │[srm_wheels]  │[fig2_land-   │[fig_validation]   │ │
│ │ +헤더텍스트   │ scape_filter │  N=2 exploratory  │ │
│ │ +통계 bullet │ -1]          │                   │ │
│ └──────────────┴──────────────┴───────────────────┘ │
├───────────────────────┬─────────────────────────────┤
│ ⑦ Conclusion          │ ⑧ References                │
└───────────────────────┴─────────────────────────────┘
```

**파일 → 슬롯**

| 파일 | 슬롯 | 위치 | 비고 |
|---|---|---|---|
| `fig1_pipeline_revise.png` | ④ Framework | COL2 상단, 대형 | 현행 ring본 |
| `srm_wheels.png` | ⑥A | RESULTS 좌 | 크롭본 + 패널 헤더 텍스트박스(HC/Sub-08·V2/Sub-09·V1), 통계는 bullet |
| `fig2_landscape_filter-1.png` | ⑥B | RESULTS 중 | loss landscape + Orig/Filt swatch |
| `fig_validation.png` | ⑥C | RESULTS 우 | 재생성본 (N=2, adj-acc + HC-disparity) |
| ~~`disparity_roi.png`~~ ~~`srm_wheels_ohbm_full.png`~~ ~~`fe_encoder.png`~~ ~~`loco_cartoon.png`~~ | — | 미사용 | 세로부족/수치충돌/드롭 |

> QR = 랜딩페이지(`haba6030.github.io/colorblind_ICML/`) → 헤더에 1개.

---

## ⑧ References  — 좌하단

1. Biffi C et al. IEEE Trans Med Imaging 39, 2088–2099 (2020).
2. Lotfollahi M et al. Nat Methods 16, 715–721 (2019).
3. Brouwer G, Heeger D. J Neurosci 29, 13992–14003 (2009).
4. Kriegeskorte N et al. Front Syst Neurosci 2, 4 (2008).
5. Bannert M, Bartels A. J Neurosci 38, 3657–3668 (2018).
6. Machado G et al. IEEE Trans Vis Comput Graph 15, 1291–1298 (2009).
7. Somers L et al. Vision Res 218, 108390 (2024).
8. Tregillus K et al. Curr Biol 31, 936–942 (2021).

---

## 남은 확인 (텍스트 확정 후 포스터 빌드 단계)

1. **⑤ 분량**: data 2 + 표상/read-out 3 + mechanism 표 + 손실 2 → 좌열에서 가장 김. 공간 부족 시 read-out 3줄을 1줄로 합칠지(내용 손실 없음).
2. **⑥A wheels 헤더**: 크롭본에 헤더 없음 → 포스터에서 텍스트박스로 HC / Sub-08 deutan·V2 / Sub-09 protan·V1 얹기 (수동).
3. **⑧ 레퍼런스**: 현재 6개 확정안. (cochlear Irino는 ②에서 언급 삭제 → Tregillus 유지가 정합.)

## 완료 (해리 검증)
- ✅ Results A/B 전 수치 camera-ready 일치 (LORO 0.668 · adj-acc 0.47/0.25/0.13 · disparity .040/.007 · Table 1 (+6,−42)/(+2,+24) · |δθ| 26.3/16.2 · 3/7→7/7).
- ✅ Result C fig = `fig_validation.png` 재생성 (N=2, adjacent-acc + HC-disparity, exploratory, 폐기문구 제거).
- ✅ B/C figure(`fig2_landscape_filter-1.png`, `fig_validation.png`) 시각 검증 통과.
- ✅ FE-6 basis 복원으로 ⑤ ↔ camera-ready §2.2 해리 해소.
- ⚠️ 유일 잔여: Result C는 논문 미수록 신규 데이터 → **"preliminary/exploratory" 라벨 유지 필수**.
