# future-phase2 REWRITE OUTLINE (2026-06-01)

**목적**: 현재 논문 초고(`docs/PAPER/`, `results_v4.tex`)의 future-phase2 부분(§2-component fit → filter → eval)을 다시 쓰기 위한 문장 골격.

**위치**: 현 draft 구조 = MRI 촬영 → LORO(discrimination 보존) → LOCO(interpolation 손상) → geometry(ΔRDM, CVD별 distinct ROI)까지가 "CVD 특징 파악". **그 이후**가 future-phase2 = 본 문서의 대상.

---

## 0. Locked decisions (이 outline의 전제)

| # | 결정 | 근거 |
|---|---|---|
| D-spine | Proof-of-concept spine 유지 (full-pipeline 방법론 논문 아님) | 사용자 2026-05-31 |
| D-machinery | 논리=본문, 기계(Phase A→D, resample, loss inventory)=Supplement, 검색 연대기=비노출 | 사용자 2026-05-31 |
| D-truth | **`closure.md`(05-31, 4-test FDR) > `PIPELINE_2_CLOSURE.md`(Exp17/22).** closure.md가 후자의 Exp17/22 partial-pass를 명시적으로 supersede. 수치/내용 불일치 시 closure.md 우선, 그 다음 PIPELINE_2_CLOSURE, draft 최후 | 사용자 2026-06-01 + closure.md line 31–37 |
| D-sub08 | sub-08 **βc-dom (6,−42) primary**; βs-dom (38,−10)은 Appendix parallel/rejected 목록 | 사용자 2026-06-01; 근거=parameter stability (specificity 아님, 셋 다 0/3 FAIL) |
| D-sub09 | sub-09 **βc-rot (2,+24) primary** (β_c **+24**, draft −22 폐기). cortical rotation, retinal-dominant 서사 폐기 | CLOSURE |
| D-etiology | 두 사례 **모두 cortical**. R+C(retinal)는 *제안 근거 + 위치 진단*까지만, 우리 결과엔 부적합으로 기각 | 사용자 2026-06-01 |
| D-common | "공통 cortical 모델, 개인별 파라미터"가 핵심 contribution 서사 (two-mechanism보다 강함) | 사용자 2026-06-01 |
| D-priorworks | 2-comp는 **prior art 없는 novel formulation**. 문헌에서 빌린 건 cardinal-axis convention뿐. "Emery-derived" 금지, g vs literature 직접 비교 주의 | `prior-works.md` §3·§6 |

**숫자 표기**: `‹값›` = CLOSURE canonical, S7 sprint supersede 시 교체 자리. 골격 구조는 숫자 비의존.

---

## 1. METHODS

### M1 — Distortion models: two candidate classes

- **¶1 (R+C = Candidate Model 1, 형식 제시)**: 필드의 표준은 망막 수준 — cone-spectral shift (Machado 2009) + 선택적 cortical compensation gain g (R+C; δθ=(2−g)·δθ_Machado, g=1 무보상, g>2 과보상; Boehm 2014, Tregillus 2021). 이 retinal-plus-gain 관점은 forward modelling의 출발점이며, confusion-axis와 cardinal-axis를 vocabulary로 제공한다. *(어느 모델이 데이터에 적합한지는 Results 영역 — Methods에서 rejection 예고 금지.)*
- **¶2 (2-comp = Candidate Model 2, novel form)**:
  > The 2-Component cortical model is a generative formalisation of the representational distortion identified above (impaired LOCO interpolation, §LOCO; elevated ΔRDM disparity, §geometry). Its form is novel; we adopt only the cardinal-axis convention from the colour-opponent literature — the S-cone axis at 90° (Krauskopf 1982) and the family-specific confusion axis from cone fundamentals (Stockman & Sharpe; θ_conf protan 16°, deutan 150°). It is not derived from any prior generative model.
  - δθ(θ) = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)
  - 다만, 결과는 직접적으로 방법에 작성하지 말고, 우선 모델 두 개 제시하는 것에 집중 
- **§S1로**: β_s≥0 생물학적 근거(Emery 2021/2023 cardinal rotation), 격자, forward 수식 전개, A13 canonical forward(`two_comp.py` raw nominal-θ).

### M2 — Inverse fitting: structural distortion estimation

> We cast distortion estimation as an inverse problem: given observed neural and behavioural signals, find model parameters (β_s, β_c) whose forward prediction best accounts for CVD–HC differences. Three loss families, measuring distinct aspects of the distortion, serve as the objective: (i) behavioural JND ratios (per-pair γ_focal and aggregate γ_all), (ii) representational ΔRDM cosine in SRM/PCA space, and (iii) hV4 LOCO voxel-prediction. **Only the LOCO loss couples to the forward encoding model (ridge-GCV); the JND and RDM losses operate directly on behaviour and on representational distance.** Parameters were estimated by grid search over (β_s, β_c) ∈ [−90°, 90°]², minimising the selected loss combination (§S2).

- 역문제 framing이 핵심: 관측된 신경·행동 신호로부터 (β_s, β_c)를 추정. forward(encoder)는 3개 loss 중 LOCO 1개에만 필요.
- Pre-image computation (M4)은 이 inverse fit의 결과로부터 stimulus-space 보정 필터를 도출한다 — 모델 추정과 필터 도출이 하나의 파이프라인임을 강조.

### M2.5 — Model / parameter selection criteria (신규)

> Model class and parameters were selected by a pre-specified procedure on held-out HC subsets (5-train / 2-test resample, N=‹300›, plus strict 7-fold HC leave-one-out). **A precondition gate admitted only cells where the CVD distortion exceeded the HC distribution in the expected direction (signed Cohen's d ≥ +0.5).** Among admitted cells, **grid-boundary saturation (>50%) and collapsing cells were rejected as a gate, and the primary criterion was parameter stability** (HC-resample IQR and σ-bin mode share; strict-LOO range). The reported (β_s, β_c) is the representative of the selected 45°-categorical σ-bin, not a global point estimate. **The directional precondition (축 2: CVD vs HC distinguishability) is distinct from statistical specificity (HC false-positive rate), which we report descriptively and do not use as a selection criterion** (§framework).

- selection = **두 축**:
  - 축 1 (parameter stability): boundary gate + HC-resample IQR + σ-bin mode share + strict LOO range
  - 축 2 (CVD–HC distinguishability): precondition signed Cohen's d ≥ +0.5 방향성 admission (CVD가 HC보다 큰 distortion 보이는 cell만 진입)
- ⚠️ **§0 경계**: 축 2(precondition 방향성 게이트)는 selection의 일부 ✓. 그러나 specificity/FPR(HC와 통계적 구별 주장)은 selection 아님, descriptive only ✗ (HC FPR 100%, Exp22 per-realisation는 descriptive). 이 두 역할을 흐리면 §0 위반.
- 정정: boundary = gate / primary = parameter stability (CLOSURE Step 3.3). (이전 "median test loss primary" 서술 폐기.)
- §S2로: cell enumeration(71/11), atom 정의, precondition gate 상세, Phase C는 deprecated(미언급).

### M3 — Identifiability and recovery

> To establish which quantities are identifiable at our sample size (2 CVD, 7 HC), we ran three pre-registered checks: matched-grid leave-one-HC-out synthetic-null tests, a real-vs-synthetic loss-landscape depth comparison, and a forward parameter-recovery simulation under category-consistent injection (§S3).

### M4 — Pre-image (corrective filter)

> The 2-Component map is bijective: each hue θ_k has an exact pre-image θ̃_k with T(θ̃_k)=θ_k, giving a correction filter δθ^filt_k = θ̃_k − θ_k. Pre-images were computed by Brent refinement and required 8/8 exact (residual <0.001°); failure rejects the subject–model pairing.

---

## 2. RESULTS

(현 `results_v4` 앞 3 subsection LORO/LOCO/geometry 유지, 그 뒤 전면 교체)

### R1 — The retinal-plus-gain model is structurally insufficient for both cases

- **¶1 (primary: DOF 부족)**: R+C 1-DOF가 두 참가자 모두 구조적으로 실패. gain이 grid ceiling에 saturate — sub-09 g=‹2.95›, boundary ‹41%›; sub-08 g=‹3.0›, boundary ‹100%› — misspecification 신호이지 fitted optimum 아님 (Wilson & Collins 2019). δθ=(2−g)·δθ_Machado는 confusion-axis DOF가 없어 off-axis 왜곡을 어떤 g로도 표현 불가. R+C는 diagnostic decomposition(Appendix)으로만 유지, filter form 아님.
- **¶2 (보조: g가 문헌 범위 초과)**:
  > Beyond this structural limit, the fitted gains (sub-08 g=‹3.0›, sub-09 g=‹2.95›) exceed the cortical-compensation range reported behaviourally (g≈1.0–1.3; Boehm, Tregillus); although these quantities are not strictly commensurate across paradigms (§S), the direction reinforces that the 1-DOF retinal-plus-gain form is the wrong model class for these data.
  - 주의(prior-works.md §3): g 직접 비교는 단위·layer 다름 → "not strictly commensurate" 조건절 필수. 주 논거는 DOF, g는 방증.

### R2 — A single cortical model fits both CVD cases (공통 모델 = 강점)

- **¶1 (unified framing)**: 단일 2-Component cortical 모델이 두 참가자 모두 적합; deutan/protan 차이는 두 파라미터가 전담, 별개 메커니즘 아님.
- **¶2 (sub-08 primary, βc-dom)**: (β̂_s, β̂_c)=‹(6°, −42°)› (γ_OY+RDM_V2), 모든 후보 중 가장 reproducible — HC-resample IQR ‹(8,2)›, strict 7-fold LOO β_c range ‹[−46°,−38°]› (0 미교차). argmin은 RDM이 선택한 σ-plateau의 γ-driven sub-bin representative이며 global point estimate 아님.
- **¶3 (ROI 연결 — 포인트 6, 강한 카드)**:
  > The RDM atom entering each subject's selected loss is taken at the ROI where that participant showed significant disparity in §geometry — V2 for sub-08 (p=‹0.040›) and V1 for sub-09 (p=‹0.007›) — so the loss is anchored to each individual's independently identified distortion locus, not chosen post hoc.
- **¶4 (sub-09)**: βc-rot ‹(2°, +24°)› (γ_all+RDM_V1) — protan locus(θ_conf 16°)와 정렬된 confusion-axis rotation. σ-bin이 refit에 걸쳐 **highly reproducible** (mode share ‹87.7%›, strict LOO IQR ‹(0,0)›). ⚠️ **어휘**: "deterministic/identified"는 *재현성*을 뜻하지 *참값 식별*이 아님 (R3: 영점회수 실패 → descriptive embedding). "reproducible across refits" / "the descriptive fit places"로 쓰고 "identified"는 금지. 이 위치는 metric-dependent (Appendix‹X›). ← L9 본문 포인터(한 절).
- **¶5 (unification statement)**: 두 subtype이 동일 cortical opponent-rotation 모델로 기술됨 — deutan은 큰 confusion-axis rotation, protan은 자기 축의 작은 rotation, 차이는 model class가 아니라 (β_s, β_c)에 있음.
- ~~**¶6 (behavioral)**: [8AFC HC/sub-08/sub-09]~~ → **제거**. 행동 데이터는 model fitting 근거도, filter evaluation도 아님. 참가자 특성 서술은 §intro 또는 R5(filter eval) baseline으로 이동.
- **Appendix로(D-sub08)**: βs-dom (38,−10)=S08-stable은 parallel/rejected 후보 목록에 — 소거 이유(parameter stability 열위: mode share ~50% vs βc-dom ~70%, boundary 개선 적음, Test1 β_c bias high)와 함께. R+C variants 등 다른 소거 후보도 소거 이유 명시. **주의: specificity(0/3 모두 FAIL)는 βs-dom 소거 근거 아님** — 셋 다 FAIL이므로 변별 안 됨. βc-dom primary 선택 근거는 순전히 parameter stability.

### R2.5 — Neural data identifies what behaviour cannot (신규 — 포인트 8, 본 논문 의의)

> Including the neural (RDM/LOCO) losses alongside behaviour materially improved parameter identification over a behaviour-only fit: the grid-boundary rate fell from ‹23%› to ‹9.3%›, and the parameter IQR tightened from ‹(18,6)› to ‹(8,2)› (CLOSURE RQ4a/b). Most consequentially, for sub-09 the behaviour-only fit placed β_c≈0 — an invisible confusion-axis rotation — whereas adding the neural loss revealed β_c=‹+24°›. The cortical mechanism is therefore identifiable from neural representation but not from behaviour alone, which is the central justification for the fMRI-based approach.

- 출처: CLOSURE RQ4 (line 106–134). (a) boundary, (b) IQR, (c) sub-09 β_c behav≈0 → +neural=+24.

### R3 — Identifiability: model class robust, precise per-axis value not (plain 재작성 — 포인트 7)

용어 주의: 본 outline 전체에서 "magnitude"는 본문에 쓰지 않는다. 대신 **"precise per-axis value (β_s, β_c)"** / **"dominant-axis direction"** / **"mechanism class"**로 분해해 쓴다. (사용자 질문 2026-06-01: magnitude 모호 — (a)축별 절댓값 (b)벡터 ‖β‖ (c)direction과의 대비, 세 의미 섞임 → 분해.)

- **¶1**: 우리 표본이 무엇을 pin down할 수 있는지 물음.
- **¶2 (class yes)**: mechanism class와 filter direction은 안정 — 세 representational-distance variant(PCA, SRM-cos, SRM-dis)에서 sub-08 fit이 동일 (β_s>0, β_c<0) quadrant 유지 (Appendix‹A.3›).
- **¶3 (precise value no)**: 정확한 (β_s, β_c) 값은 비식별 — HC 참가자를 재조합해 만든 surrogate "CVD"들을 refit하면 fitted 값이 넓게 흩어져 실제 CVD fit이 그 분포 안에 묻힘 (point-level NS).
- **¶4 (what IS identifiable — axis-asymmetric; injection = voxel-level synth)**:
  > Parameter recovery used a voxel-level forward synthesis (donor-HC encoder W_k re-projection + realistic spatially-correlated, AR(1)-temporal residual noise; GT-consistent fake JND), not a loss-level row-swap. Under this synthesis, recovery was axis-asymmetric: the dominant (larger-|GT|) axis of each fit was recoverable (e.g. sub-08 β_c, |GT|=42°, bias →4.7°), whereas the non-dominant smaller-|GT| axis (e.g. β_s, |GT|=6°) fell below the noise floor. The identifiable quantities are therefore the mechanism class and dominant-axis direction; the precise two-parameter value is not.
  - 출처: `closure.md` Test 1 + `scripts/forward_voxel_synth.py`.
  - ⚠️ **Method C 완전 제거**: 이전 outline의 "Exp18 Method C, sub-09 한 점 exact recovery" 폐기. `forward_voxel_synth.py` docstring(line 4–7): voxel-level synth가 Method C(loss-level injection, exp14/15/18/21/22)를 **supersede** — Method C는 W·ε 부재로 insufficient. 현재 방식엔 "exact recovery" 주장 자체가 없음.
  - injection 구성: `Y_synth[run,c,:] = W_k @ C(θ_c + δθ_2comp) + ε`; W_k=donor HC encoder(CVD 자기 W 금지=circular 방지), ε=HC residual spatial-cov top-20 PC + AR(1) ρ=0.3; JND는 `synthesize_fake_jnd` GT-consistent.
- **¶5 (honest specificity — 0/3, FDR)**:
  > Under per-realisation, FDR-corrected null testing (origin-recovery, within-HC pseudo-CVD, and label-permutation), none of the candidate point estimates exceeded the null distribution (0/3). The decisive check was origin recovery: even when zero distortion was injected, the fitting argmin landed ~20–25° from the origin, indicating grid attraction rather than recovered signal. We therefore report all (β_s, β_c) as descriptive low-dimensional embeddings of each subject's distortion, not as physiological parameter estimates. This is consistent with our framework: specificity is not a selection criterion, and the selected candidates stand as descriptive fits.
  - 출처: `closure.md` (2026-06-01) Test 2a/2b/2c, FDR BH α=0.05 → **0/3 defensible**. Test 2a(영점회수 f10°=0/140)가 load-bearing.
  - ⚠️ **폐기**: 이전 "S08-βc-dom p=0.0149 통과" (PIPELINE_2_CLOSURE Exp22, single-metric)는 closure.md가 supersede.
  - 이 보수적 verdict가 §0("specificity 금지, descriptive only")과 완전 일관.

### R4 — Per-subject stimulus-space filter

- **¶1**: pre-image 8/8 exact (residual <0.001°). sub-08 primary βc-dom 필터(βs-dom은 Appendix), sub-09 βc-rot 필터.
- **¶2 [실행 필요]**: 필터 signature — **pre-image 재계산 후 숫자 주입**. CLOSURE (6,−42)/(2,+24) 기준, **sub-09는 draft((6,−22)) 방향 뒤집힘**. `two_comp.py:forward_2comp` 호출 필요.
- **¶3**: model-class 상한 |δθ(45°)| ≤ |0.71β̂_s − 0.26β̂_c|, ~51° 초과는 class 밖 (현 draft 유지).

### R5 — Filter evaluation (efficacy 주장 없음)

- [현 draft §filter_eval 유지: (1) 2AFC behavioral, (2) 2nd-session neural vs generic filter. behavioral P2a-restoration **대기 중**. "Results to be added once data collected."]

---

## 3. DISCUSSION

### D1 — Summary

- 두 CVD 성인이 hV4에서 8-class discrimination 보존하나 continuous-hue interpolation 상실; 잔여 왜곡이 **단일 2-Component cortical 모델**로 포착되고 pre-image가 두 참가자 8 hue 모두 exact. 왜곡 site = 역변환 site.

### D2 — Neural representation reveals what behaviour cannot: rationale for fMRI-based filter design

- **핵심 novelty**: behaviour-only fitting이 잡지 못한 cortical component(sub-09 β_c≈0 → +24° with neural loss, R2.5)를 fMRI-based loss가 드러낸다. Commercial chromatic filter가 행동 측정만으로 개인화되는 것과 architecturally distinct.
- **Filter design justification**: LOCO loss는 단순히 CVD–HC gap을 정량화하는 게 아니라, 어떤 방향으로 stimulus를 shift해야 neural representation이 HC-normal에 가까워지는지를 지정한다 — corrective target의 직접 식별.
- Population-average retinal filter(Machado) vs. individualized cortical filter의 차이를 이 문맥에서 서술.
- ~~LOCO 100% vs SRM ΔRDM 33% JND concordance~~ → 이미 R2¶3(ROI 연결) + R2.5에서 다뤄짐, Discussion에서 반복 불필요.

### D3 — Etiology: proposed retinally, found cortically (압축 — R1이 structural 내용 담당)

- ⚠️ R1이 structural insufficiency를 이미 다룸. Discussion에서는 **"cortical 발견이 기존 retinal-dominant 문헌과 어떤 함의를 갖는가"만** 짧게 서술 (2¶ 이내).
- **¶1 (1문장)**: The standard retinal-plus-gain framework (Machado, Boehm, Tregillus) motivates our forward modelling approach but proves structurally insufficient for both cases (R1) — pointing to a cortical locus of representational distortion.
- **¶2 (1문장)**: Both subjects require a cortical opponent-rotation formulation, consistent with post-receptoral plasticity accounts (Emery 2021/2023 cardinal convention 수준만; "Emery 21.4°와 일치" 금지 — prior-works.md §3).
- 구조적 왜곡의 구체적 수치·소거 논리는 D3에서 반복하지 않는다 — R1으로 pointer만.

### D4 — A common cortical model, individualized (포인트 D-common = headline)

- **¶1**: 핵심 결과 = 하나의 cortical 모델이 두 CVD subtype 설명; deutan/protan은 (β_s, β_c) 차이이지 메커니즘 차이 아님.
- **¶2**: two-mechanism 설명보다 강함 — 단일 model family를 개인별로 적합하면 subtype 가로질러 보정 필터 도출 가능, population-average retinal 필터(subtype 내 균일 적용)는 불가.
- **¶3 (포인트 8 해석)**: 행동만으론 보이지 않는 cortical 성분(sub-09 β_c)을 neural representation이 드러냄 → fMRI 기반 개인화 필터의 정당성. 행동 기반 상용 필터가 못 잡는 cortical 성분.

### D5 — Detection–correction dissociation: falsifiable prediction (압축 — 독립 논의 아님)

- ⚠️ 이 섹션의 주제("CVD geometry capture → filter design")의 핵심 논의가 아님. Phase 3 예측 statement로서 1-2문장. D8(Conclusion) 또는 D7(Limitations) 내 통합을 고려.
- All candidate models detect the same two participants' distortion — their prescribed correction vectors diverge. Phase-3 2AFC만이 cortical 2-comp filter가 실제 JND를 감소시키는지 검증한다.
- 정량(sign, ρ) 증거는 R3로 이동 완료 — 여기선 *falsifiable prediction*만, 수치 반복 금지.

### D6 — Upstream-input alternative (유지 — reviewer preemption 필수)

- ⚠️ "hV4 LOCO 손상이 V1-V3 input cascade의 passive downstream effect가 아닌가?"는 reviewer가 반드시 제기할 alternative explanation. 짧더라도 삭제 불가.
- hV4 LOCO 손상이 V1–V3 input variance 감소의 수동적 반영 아님 — LORO 보존이 직접 반증: discrimination이 보존되므로 V1-V3 입력이 온전히 전달됨. hV4에서 selective하게 continuous-hue interpolation이 손상됨. Brouwer/Bannert.

### D7 — Limitations (CLOSURE L1–L9 정렬, 2줄 추가)

- N=2 CVD; single-case 통계만, population claim 보류 (유지).
- **(추가) Magnitude non-identifiability**: mechanism class·direction robust하나 unique (β_s,β_c) magnitude는 N=7 하 비식별; per-realisation specificity 1/3 후보만 통과 (R3).
- **(추가) OOS·focal disclosure**: OOS 축은 HC normalization뿐 (CVD pair당 N=1); held-out focal pair CVD 관측치 재사용은 individualized-filter framing 하 leakage 아니나 명시 (§S, L2/L3).
- effective HC n=6 (sub-07 제외); ‖β̂‖ LOO 분포는 magnitude anchor, 가설검정 아님 (유지).

### D8 — Conclusion (현 draft 유지+갱신)

- individualized hV4 color geometry를 fMRI LOCO로 측정·역변환하여 population-average retinal 접근과 architecturally 구별되는 보정 도출. **단일 cortical 모델이 subtype 가로질러 작동.** Phase 3가 sole verification path.

---

## 4. SUPPLEMENT (§S — 기계 전부)

- **§S1**: forward 수식, β_s≥0 근거, A13 canonical forward (`two_comp.py`)
- **§S2**: selection 파이프라인 — Phase A precondition gate, cell enumeration(sub-08 71 cells, sub-09 11 cells), 5/2 resample N=‹300› + s17 strict 7-fold LOO, selection metric 표. (Phase C deprecated — L7 각주만)
- **§S3**: 식별성 — **canonical = `closure.md` 4-test (voxel-level synth)**: Test 1 (axis-asymmetric recovery), Test 2a (origin-recovery, load-bearing), Test 2b (HC pseudo-CVD), Test 2c (label-permutation), FDR BH → 0/3. **Method C / Exp14-22 (loss-level injection)는 superseded — 보고 안 함.**
- **§S4**: R+C diagnostic decomposition (competing fit 아님)
- **§S5 (=Appendix A)**: cross-atom robustness (PCA/SRM-cos/SRM-dis) + **L9 sub-09 metric-dependence 전체** (cosine 0.350, 3/8 sign-flip c4/c5/c8, max |Δδθ| 32.8°) + rejected/parallel candidate 목록 (βs-dom 등, 소거 이유 포함). *(전체 appendix section 불필요 — βs-dom 소거 이유 1-2줄 + 테이블 한 줄로 압축. scientific transparency 목적, elaboration 아님.)*

---

## 5. 남은 실행 항목

| # | 항목 | 비고 |
|---|---|---|
| E1 | **R4 ¶2 pre-image 재계산** | `two_comp.py:forward_2comp`로 sub-08 (6,−42) / sub-09 (2,+24) δθ 8-vec. sub-09는 draft 방향 뒤집힘 |
| E2 | `‹›` 숫자 최종 확정 | S7 sprint 결과 도착 시 교체. 현재는 CLOSURE canonical |
| E3 | 섹션별 LaTeX 확장 | 골격 → 실제 문장. M/R/D 순 (PAPER_OUTLINE §9 drafting order 참고) |
| E4 | prior-works.md cross-check | 모든 prior-art claim을 prior-works.md §6 dos/don'ts와 대조 |

---

## 6. 출처 추적 (reviewer-ready)

| 본문 주장 | CLOSURE 근거 |
|---|---|
| selection 축 2: precondition d≥+0.5 (CVD-HC distinguishability, admission gate) | CLOSURE Step 1 / PAPER_OUTLINE §S3; specificity≠selection은 §0 |
| R+C structural insufficiency, g ceiling | RQ1, L6 (line 45–67, 506–510) |
| sub-08 βc-dom (6,−42), IQR (8,2), LOO [−46,−38] | line 86, 329, 379 |
| sub-09 βc-rot (2,+24), mode 87.7%, LOO (0,0) | line 79, 330, 395 |
| RDM ROI = geometry 유의 ROI (sub-08 V2, sub-09 V1) | results_v4 geometry (p=0.040/0.007) ↔ CLOSURE combo (RDM_V2/RDM_V1) |
| identifiability 0/3 defensible (FDR), all descriptive | **`closure.md` (05-31) Test 2a/2b/2c** — supersedes Exp17/22 |
| axis-asymmetric recovery (large-|GT| 축만) | `closure.md` Test 1 (GT-consistent v2 synth) |
| origin-recovery artifact (zero signal에도 argmin ~20–25°) | `closure.md` Test 2a (load-bearing) |
| ~~loss landscape 2.1–5.5×, Exp22 p=0.0149~~ (폐기) | PIPELINE_2_CLOSURE Exp17/22 → closure.md가 single-metric artifact로 supersede |
| neural inclusion 이점 (boundary 23→9.3%, IQR 18,6→8,2, sub-09 β_c 0→+24) | RQ4 (line 106–134) |
| 2-comp novelty, cardinal convention only | prior-works.md §3, §4.2, §6 |
| B→C 누수는 최종 selection 무관 (Phase C deprecated) | L7 (line 512–515) |
