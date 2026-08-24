# FINDINGS — future_phase3_geometry_synthesis

> **Q**: SRM와 FE-6 forward model이 같은 색 기하(embedding)를 복원하는가? 필터 조건 포함.
> **작성**: 2026-07-14 · **데이터**: C010 (exp1 nofilter + exp2 window/optimal), sub-08/09, matched
> **재현 앵커**: git `c9ff902` · scripts `p4_overlay_viz.py` / `p4_geometry_decomposition.py` / `p4_percolor_loco.py`
> **입력(소비, recompute 안 함)**: `../phase6_behavioral_analysis/exp2_neural/results/exp2_embeddings_sub-{08,09}_matched.json` (Stage 1 coords), `exp2_geometry_derived_*.json` (Stage 2)

이 문서는 **탐색적/기술적(descriptive)** 결과다. N=2 CVD, 8점. **유의성 주장 아님**, metric-shopping 방지 위해 metric 3종·subject 2명을 모두 병기한다.

---

## 0. 한 줄 결론
두 파이프라인(SRM=피험자간 정렬 / FE=단일피험자 인코딩)은 **robust하게 수렴하지 않으며**, 8색은 **정연한 hue 링을 복원하지 못하고**(2D·3D 공통), exp2 조건별 **interpolation도 우연 수준**이다. 유일하게 hue 구조가 살아있는 곳은 **V1 nofilter**뿐. → exp2 필터검증의 기하학적 열화를 **정량 기술**하는 자료이지, 복원/수렴을 입증하는 자료가 아니다.

---

## 1. SRM↔FE 수렴 — metric 의존적, robust 아님 (GAP1)

RDM(metric)→classical MDS 2D→Procrustes 정렬, **label-permutation null이 primary 판별자**(n=8 원형이라 M²만으론 부족). 유의(perm p<0.05) 셀 수 / 12:

| subject | corr metric | eucl metric | 두 metric 공통 유의 셀 |
|---|---|---|---|
| sub-08 | **2/12** (V1-opt, hV4-nofi) | **6/12** (V1/V2/V3/hV4 산재) | **0** |
| sub-09 | **6/12** (V1/V2/V3/hV4 산재) | **5/12** (V1/V2/V3/hV4 산재) | ~1 (V2-opt 근접) |

**핵심**: (i) eucl가 corr보다 유의 셀 많음(스케일 민감), (ii) **두 metric이 유의한 셀이 거의 겹치지 않음** → 수렴이 metric 선택에 robust하지 않다. 안정적으로 "SRM=FE"라 말할 (ROI×조건)이 없다.
- 참고(Stage 2 Pearson, 28-vec): `srm~procrustes`는 매우 높음(V1 eucl 0.98) = SRM은 voxel 기하와 수렴하나, **FE_latent(채널공간)만 분리**. 두 표상이 다른 공간에 살기 때문.

## 2. Hue 링 — 어디에도 없음, 3D 무효 (GAP1 파생)

192 패널(2 sub×4 ROI×3 cond×2 repr×2 metric) 원형-순서(circR)·완전링 검사:
- **완전 순환 링 = 0/192.**
- |circR|>0.6은 6패널뿐, **전부 V1**. 최고 = sub-09 V1 nofilter·FE·corr **+0.79**, sub-08 V1 optimal·SRM·corr +0.75.
- **3D 무효**: top-2 MDS 분산비 v2 = 0.86–0.96, v3 = 0.95–1.00 → 기하 ~90%가 이미 2D. 링은 3번째 축에 숨은 게 아니라 **실재하지 않음**.

## 3. Interpolation — 우연 수준, 링과 역상관 (GAP5)

exp2 조건별 LOCO(디코딩측), nofilter:
- adj_acc **0.10–0.44** (우연 ≈0.375), exact **0.02–0.35** (우연 0.125) → 대부분 우연 근처/이하.
- decoded_hue vs true_hue 원형상관 ≈ 0 (sub-08 +0.04~+0.15, sub-09 −0.45~+0.46) → 매끄러운 hue 매핑 없음.

**링 품질 ⟂ interpolation (역상관)**:

| | circR(FE링) | adj_acc |
|---|---|---|
| sub-09 V1 | **+0.79 (최고)** | 0.19 (우연↓) |
| sub-08 V1 | +0.26 | **0.44 (최고)** |

→ **FE 채널의 "링"은 basis 아티팩트**: 채널이 cos² hue-튜닝으로 설계상 고리형이라, 데이터 적합이 나빠도 링처럼 보임. circR은 fe_latent에서 과대평가됨. (SRM/voxel 링은 낮음.)

## 4. 필터 효과 — HC 복원 없음 (Stage 2 재확인)

SRM displacement(raw-coords Procrustes): 필터 조건 vs_hc가 nofilter의 vs_hc보다 **같거나 큼**(멀어짐). sub-09만 일부 미세 감소(V1 0.76→0.62, V2 0.59→0.52). vs_nf 0.79–1.16 = 필터가 기하를 크게 바꾸되 **HC 방향 아님**.

---

## 5. 해석 (descriptive)
1. exp2 per-condition 데이터는 **저해상도**(조건당 4–6런): 링·interpolation·수렴이 **함께 약함**. 상호 모순 아님.
2. 프로젝트의 강한 interpolation 주장(Phase-1 hV4 GO, perm p=0.044)은 **다른 데이터(풀 exp1)·다른 지표(인코딩 rho)**이지, 이 조건별 디코딩이 아니다. **인코딩 rho ≠ 디코딩 acc ≠ 2D 링** — 규제 강도 다름.
3. hue 구조가 유일하게 살아있는 V1 nofilter는 **초기영역=물리 hue 충실 인코딩(stimulus-driven, 리뷰 §A)**과 정합.

## 6. Caveat
- N=2 CVD, 8점 → 모든 수치 descriptive. metric 3종 병기 필수(단일 metric 인용 금지).
- fe_latent 링/circR은 **basis-imprinted** → 신경 구조 지표로 단독 사용 금지. voxel/SRM 또는 인코딩 rho로.
- perm-p 유의 셀은 metric 간 불일치 → "수렴 확립" 서술 금지.

## 7. 논문 편입 (다음 단계 = 리프레이밍 §C)
- **characterization(강)**: "두 CVD 모두 hue 링 미복원 + SRM↔FE 비robust" (per-subject 확증).
- **limitation**: 조건별 디코딩 우연 수준 = N=2 underpowered의 기하적 증거.
- **method/caveat**: 인코딩/디코딩/링 구분, FE 채널 basis 아티팩트.
- 이 결과는 ResearchNOTE/METHODS에 **리프레이밍 단계에서 편입**(여기선 원본 보존).

## 8. 결정
- **임베딩 추가 굴착 중단** (한계효용 낮음 + metric-shopping policy 리스크).
- 잔여 positive 여지 분석은 **자극-구동 colorimetry Lab 검증(리뷰 §A)** 하나 — 별건.

---

## 산출물 (figures/, results/)
- overlay: `overlay_sub-{08,09}_matched_{corr,eucl}_2d.png` (+ `results/p4_overlay_*.json`)
- decomposition: `decomposition_sub-{08,09}_matched_{srm,fe_latent}.png` (+ `results/p4_decomposition_*.json`)
- per-color: `percolor_{error,confusion}_sub-{08,09}_matched.png` (+ `results/p4_percolor_*.json`)
