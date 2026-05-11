# Title

**SC-AIRL: State-Conditional Adversarial Inverse Reinforcement Learning for Imitating Human Behavior under Bounded Foresight**

- v1 title (`CogAIRL: Cognitive-based AIRL better imitates human behavior`) → updated
- **v1.2 changelog (2026-04-28)** — Use-Inspired track refit:
  - §1.1 reframed: 3-step structure (Significance + Challenge + First-trial limits) → Lee 2024 deep-AIRL precedent → infinite-horizon limit; pedestrian dataset moved to §5.1 testbed status (no longer the §1 spotlight). Original-voice framing replaces earlier Hybrid Hook draft (avoids over-mimicking Binz 2022).
  - §1.2 reframed around **bounded rationality** (Simon 1955; Russell 1997; Lieder & Griffiths 2020) as principled correction; **Barnes 2023 RHIP** added as production-scale empirical anchor (H=10 outperforms H=∞ on Google Maps driver trajectories); cognitive MoE motivation retained.
  - §5.2 baselines: Option B+ scoping — "data-driven IRL" as the contribution scope; non-ML generative models (Helbing & Molnár 1995) excluded by IRL objective, not by hand-waving; Lee 2024 cited *only* for §6.3 mechanism-validation context (avoiding category error of equating Social Force with summary statistics).
  - **C1/C2/C3/C4 4-contribution structure (v1.2 final, calibrated wording; C3 reframed 2026-04-29)**: split v1.1's combined C2 (imitation+reward) into separate **C2 (imitation)** and **C3 (depth-invariant reward recovery + task-goal absorption)**; original C3 (clinical convergent validity) renumbered to **C4** (Binz template, ~10% paper share). C3 wording reframed 2026-04-29 from "preliminary task-alignment" to "task-goal absorption + decoupling" after refined 3×2-cell analysis (vehicle imminent-proximity × is_road) revealed both methods recover near-identical context-action argmax structure (100% concordance in 5/6 cells; only `offroad_close` partial at 65.4%), with the contextual decision heterogeneity (most cleanly: expert unanimous NOOP in `offroad_close` while reward UP-dominant) living in the policy/router rather than in the reward — *negation-style* evidence directly supporting the architectural commitment.
  - **§5/§6 restructure (v1.2 final, 2026-04-28)**: previous §5 *Theoretical Analysis* (Prop 1/2) moved to Appendix A; §6 reorganized as 4 result sections + 1 ablations, narratively aligned with C1/C2/C3/C4 (1:1 mapping with new contribution structure):
    - **§6.1** Imitation Fidelity under Bounded Foresight (**C2** + C1 architectural mechanism + train-test generalization)
    - **§6.2** Depth-Invariant Reward Recovery and Task-Goal Absorption (**C3**)
    - **§6.3** Convergent Cognitive Validity of the Inferred Planning Depth (**C4**, Binz template)
    - **§6.4** Robustness under Covariate Shift (supplementary; behavioral monotonicity + per-attempt decomposition; dynamic clinical OOD → Appendix L.2 exploratory)
    - §6.5 Ablations
  - **OOD + Train-test integration**:
    - §6.1 includes Table 1b: held-out-seed generalization placeholder; pre-registered T1–T4 in Appendix J.5.
    - §6.4 supplementary: behavioral graded-caution monotonicity (×2/×5/×10) + per-attempt collision decomposition. Trait × stakes-sensitivity is reported as *exploratory* in Appendix L.2 only (BH-FDR q=.10 over the full 324-cell family yields 0 survivors; static convergent validity is already covered in §6.3 / Appendix L). 2026-04-30 reframed: previous "Bonferroni-passing replicated leads" claim retracted after reanalysis revealed two sweeps share the same frozen posthoc router → cross-sweep agreement is deterministic recomputation, not statistical replication.
    - §7.2 Limitations: pre-registration note for train-test execution + ×100 collapse boundary note + **posthoc-router architectural disclosure** (OOD evaluates the gating object refit on baseline expert under frozen per-h policies, not trained router weights) + seed-1 only + no OOD baselines + dynamic clinical OOD scan BH-FDR survivors = 0 at q=.10.
    - Appendix J.5 (Train-test pre-registered plan) and Appendix L (OOD multiplier curve, per-attempt collision decomposition, exploratory clinical leads with BH-FDR honest disclosure, failure-mode diagnostics — promoted from §9.I.5).
  - Bibliography: +Lee 2024, Simon 1955, Russell 1997, Lieder & Griffiths 2020, Helbing & Molnár 1995, Daw 2011, Ng & Russell 2000.
- **Primary framing**: Better human behavior imitation through state-conditional modeling of bounded planning depth, cast as a **cognitive mixture-of-experts** whose gating over per-depth decision systems shifts with the current state
- Positioning: **method paper** with human behavioral validation, cognitive science as motivation
- Depth-invariant reward recovery is treated as a *core assumption* (A3, §3.1) that we verify empirically, **not** as a claimed theoretical contribution of this paper

---

# Abstract (≤250 words, target structure — aligned with draft §1.3 contributions)

- **[Hook]** AIRL assumes infinite-horizon Boltzmann-rational experts, but human demonstrations reflect bounded-foresight suboptimality that working-memory limits make unavoidable (Cowan 2001; Laidlaw 2022 BPD).
- **[Gap]** Existing remedies fall on three axes — softened rationality, discount rescaling (Yao 2024), trajectory-level expertise (IRLEED, DTIL) — none of which model a *state-varying physical horizon cutoff*. Single-horizon AIRL therefore underestimates the behavioral ratio of efficiency-limited suboptimal actions and collapses within-participant horizon variation.
- **[Method]** **SC-AIRL** introduces three structural replacements of Standard AIRL, each licensed by one assumption:
  1. **Truncation (A1)**: $h$-step return $G_t^{(h)} = \sum_{k=0}^{h-1}\gamma^k r_\theta$ — *physical* lookahead cutoff (Prop. 1: not reproducible by any $\gamma'$).
  2. **Multi-policy (A2)**: per-depth family $\{\pi^h\}_{h\in\mathcal{H}}$ composed by a state-conditional router $p_\phi(h|s)$ into $\pi_\text{mix}$.
  3. **No shaping (A3)**: $f_\theta = r_\theta$, $\Phi\equiv 0$, $V_\text{tail}\equiv 0$ — depth heterogeneity absorbed by planner family, not by reward (Prop. 2: GAE-$h$ has no boundary residue).
- **[Results]** On N=56 human pedestrian crossing (113-dim state, 5 actions):
  - **C1 (architecture)**: first AIRL with state-conditional bounded-foresight inference; physical cutoff (Prop. 1).
  - **C2 (behavior)**: 2.15× behavioral imitation over Std AIRL; recovery of NOTHING-action ratio; recovery of within-participant state-dependent reward variation.
  - **C3 (convergent validity)**: router output correlates with independently-predicted clinical scales — BIS $r{=}{-}0.38$ ($p{=}0.020$), CRA $r{=}{-}0.44$ ($p{=}0.006$), $N{=}51$.
  - Reward identifiability anchor: cross-correlation $r{=}0.77$ between bounded and near-infinite-horizon training.
- **[Impact]** Bounded foresight as a first-class architectural feature — *not* a discount knob, *not* a per-trajectory tag — substantially improves human-behavior imitation and yields a router whose output is consistent with an interpretable cognitive construct.

> **Review note (2026-04-24, NeurIPS reviewer perspective)**
> 1. **Claim calibration**: Results 블록에 실험 숫자 4개(top-1 accuracy 0.585→0.762, KL 44% 감소, cross-corr r=0.77, BIS/CRA)가 명시되어야 리뷰어가 contribution 규모를 즉시 판단 가능.
> 2. **Method 블록 압축**: 3개 structural replacement 나열이 Abstract에서는 과도 — 2문장으로 압축 권장 (e.g., "물리적 h-step 절단 + 상태조건부 라우터 + 무shaping 공유보상" 한 문장 + Prop 1 결과 한 문장).
> 3. **Proposition in Abstract**: NeurIPS 리뷰어는 Abstract에서 이론 결과보다 empirical headline 중시 → "physical cutoff that no discount can reproduce" 정도의 함축 표현이면 충분, 수식 제거 권장.
> 4. **"2.15×" 검증 필요**: 실험 데이터 기준 top-1 개선은 +30% (0.585→0.762), KL은 44% 감소. "2.15×"의 출처/계산 근거 확인 후 Abstract 반영.

---

# Target: NeurIPS 2026 — **Use-Inspired Contribution Track** (9 pages + appendix)

See `GUIDE_REVIEW.md` for full track guidelines and §10 Decision Block (re-evaluated under Use-Inspired track).

---

# 1. Introduction (1.25–1.5 pages)

## 1.1 Computational modeling of human decisions meets bounded rationality
- **Significance + Challenge + First-trial limits (Para 1)**: Modeling human decision-making is crucial in AI-applied contexts (autonomous driving, HRI, decision-support systems) where artificial agents must anticipate naturalistic human behavior; yet faithfully imitating human behavior remains challenging. Cognitive psychology has approached this through computational models — parametric reward functions fit to controlled lab tasks (DDT, GNG) — representing a foundational first attempt that captures stylized choice but fails to generalize to high-dimensional dynamic real-world behavior (Daw 2011; Lieder & Griffiths 2020).
- **IRL bridge + Lee 2024 precedent (Para 2)**: Inverse RL (Ng & Russell 2000; Ziebart 2008; Fu 2018) infers rewards from observed behavior. Lee et al. (2024) demonstrated this in cog-psych: deep AIRL on real-time driving recovers BIS impulsivity ($r{=}.72$) where summary statistics ($r{=}.48$) and combined-feature models add no incremental variance.
- **Shared limitation (Para 3)**: Lee (2024) + standard AIRL inherit MaxEnt IRL's *infinite-horizon Boltzmann-rationality* — implausible for humans (working memory $4{\pm}1$, Cowan 2001; Miller 1956); Boltzmann-rational AIRL absorbs bounded-foresight suboptimality only as noise (Laidlaw 2022, BPD).
- Pointer: SC-AIRL replaces this assumption with *state-conditional bounded foresight* (§4).

## 1.2 Bounded rationality and state-conditional planning depth (cognitive MoE)
- **Bounded rationality framing (Para 4)**: Simon 1955, 1991; Russell 1997; Lieder & Griffiths 2020 — humans plan under cognitive resource constraints. **Empirically at scale, finite-horizon IRL (H=10) outperforms infinite-horizon prediction of real driver trajectories at Google Maps scale (Barnes 2023, RHIP)** — bounded horizon is not merely computational convenience but empirically optimal for human-behavior modeling. Depth is *not fixed* per individual: deepens with expertise (Opheusden 2023 *Nature*), shortens state-dependently under time pressure/branching complexity (Huys 2012; Otto 2013; Callaway 2022).
- **Cognitive MoE motivation (Para 5)**: Bounded depth + state-conditional pruning → behavior arises from multiple per-depth decision systems gated online by state.
- **Existing remedies are partial**: softened rationality (BPD), $\gamma$-rescaling (Yao 2024; Schultheis 2022), trajectory-level expertise (IRLEED; DTIL) — none model a *state-varying physical horizon cutoff*. (Motivation, not contribution.)

## 1.3 Contributions

- **C1 (propose) — SC-AIRL: State-Conditional Bounded-Foresight AIRL.** We propose the first AIRL algorithm that infers state-conditional planning depth $h$ by jointly learning per-depth policies $\{\pi^h\}_{h\in\mathcal{H}}$ and a state-dependent router $p_\phi(h|s)$ from demonstrations alone. Unlike per-agent discount rescaling (Yao 2024), SC-AIRL imposes a *physical* $h$-step computational cutoff via GAE-$h$ — a bounded-support temporal weighting that no rescaled discount can reproduce (formal results in **Appendix A**).

- **C2 (demonstrate) — Improved Human Behavior Imitation under Bounded Foresight.** SC-AIRL's cognition-motivated structure substantially improves imitation fidelity over single-horizon AIRL, instantiating a concrete remedy for Boltzmann-rationality suboptimality absorption failure (Laidlaw 2022, BPD): **2.13× tighter $|\Delta SR|$** vs Std AIRL, **~30% reduction** in NOTHING-action gap (−13.6%p → −9.5%p), and Top-1 accuracy **0.585 → 0.762** (LogGauss). The state-conditional router does not collapse, exhibiting statistically robust state-zone adaptation (SAFE/DANGER ratio 1.089 ± 0.110, $p{<}.05$ across all PIDs) — depth heterogeneity is recovered from behavior alone (§6.1).

- **C3 (demonstrate) — Depth-Invariant Reward Recovery and Task-Goal Absorption.** By absorbing depth heterogeneity into the planner family $\{\pi^h\}$, SC-AIRL preserves a single shared reward that encodes the *task goal* rather than the *contextual decision strategy*: (i) cross-correlation $r{=}0.784\pm 0.043$ between SC-AIRL and Std AIRL reward functions verifies (A3) shared-reward commitment empirically; (ii) on a 3×2 contextual cell grid (`{off-road, on-road} × {none / medium / close imminent vehicle proximity}` based on per-lane head-closeness `max(obs[77,81,89,93])`) both methods learn the *same* per-cell reward argmax-action — UP-dominant across all 6 cells with **100% cross-method concordance in 5/6 cells** (only `offroad_close` shows partial divergence at 65.4%); (iii) this UP-dominant reward systematically dissociates from expert behavior in cells requiring *deliberate waiting*: in `offroad_close` (safe zone but vehicle imminent) **expert action is unanimously NOOP across all 52 PIDs** while reward argmax is UP-dominant (73–90% reward-vs-expert dissociation), and in `offroad_medium` expert is NOOP-dominant (43/52) at 88.5% dissociation — the contextual decision heterogeneity exhibited by humans is therefore *not* in the reward but is absorbed by the bounded-foresight policy / router. This *negation-style* dissociation directly verifies the architectural commitment that depth heterogeneity lives in $\{\pi^h\}$ rather than $r_\theta$ (§6.2).

- **C4 (show) — Convergent Cognitive Validity of the Inferred Planning Depth.** The inferred router output is consistent with an interpretable cognitive construct (Binz 2022 template, ~10% paper share). Three converging lines of evidence (full audit: `EXP_ROUTER_CLINICAL.md`, 2026-04-30):
  - *(i) Router-invariant signal map (state-resolved router posthoc, 3-router robustness, N=52)*: 22 metrics × 25 clinical = 550 cells under 3 main routers (`sc_categorical`, `stickbreaking`, `hspace_gaussian`); **20 cells reach all-3-router significance with sign agreement, 0 cells show all-3-sig with sign disagreement**. Headline signals: $E[h]$ mean × DDT log(k) mean $r{=}+0.40$; $E[h\mid\text{road}]$ × UPPS-P premeditation mean $+0.40$; state-adaptation $E[h\mid\text{SAFE}]{-}E[h\mid\text{DANGER}]$ × **BIS Motor mean $+0.34$ robust 3/3 routers** (same shift × BIS-total partial-sig 2/3, mean $+0.29$, motor facet drives trait-level); $\sigma_s(E[h\mid s])$ × DDT log(k) $+0.31$ robust 3/3. **Distribution-shape KL** (`flex_kl_*` family, pairwise symmetric KL between aggregated $p(h\mid\text{zone})$ across {safe, danger, goal}): × BIS-total mean $+0.29$ (first robust main-scale signal in the entire 550-cell grid); × DDT log(k) mean $-0.32$ (opposite sign to level-metric × DDT — distribution-shape divergence is a distinct cognitive cut from depth level); × jaywalking $+0.36$.
  - *(ii) Within-domain in-task bridge (added 2026-04-30)*: latent depth predicts in-task behavior the model was *not* trained on — `shift_road_danger × action_Nothing_ratio` mean $r{=}+0.46$ (top of the entire 550-cell table); `E_h_time_low × jaywalking_ratio` mean $-0.41$; `E_h_safe / E_h_mean × jaywalking` $-0.37$ / $-0.36$ — all robust 3/3 routers. Combined with the cross-domain DDT cluster, this gives **two independent bridges from depth construct to behavior** (cross-domain via DDT lab task, within-domain via gameplay signatures).
  - *(iii) Global-aggregate Pillar 5 EM E[h]* (uniform-prior, state-independent — distinct from router output; $r_s{=}0.21$ ns vs router): UPPS-P facets — Sensation Seeking $+0.48$, Positive Urgency $+0.49$, UPPS Total $+0.45$ ($p{<}.001$). Different cognitive cut from router output (whole-task discounting vs state-conditional planning); reported separately.
  - *Dynamic (OOD)*: not reported as C4 evidence in main body to avoid double-counting against the static cuts above; trait × stakes-sensitivity scan moved to Appendix L.2 as exploratory only (BH-FDR q=.10 over 324 cells = 0 survivors; previous "Bonferroni-passing" claim retracted 2026-04-30 — see §6.4 supplementary disclosure).
  - *Reported as null (honest)*: STAI-total / CES_D-total / most DOSPERT cells are uniformly non-significant across all 3 routers — the depth construct does not align with these broader trait totals at N=52. Specifically: the legacy `sc_depth_flexibility_clinical.png` figure (STAI_S × Depth Flexibility r=−0.32, p=.019; DOSPERT_FIN × Depth Flexibility r=−0.32, p=.021; both 2026-03-26) **does not reproduce at canonical N=52** (current `flex_kl × STAI_S` pearson r=−0.149 p=.293; spearman r=−0.119 p=.402) and the v4 distribution-shape KL family (`flex_kl_mean / max / safe_danger`) also does not recover STAI/DOSPERT_FIN signals — max |r| across STAI = 0.28 (one router partial-sig only). Figure should not be cited without regeneration; full audit in `EXP_ROUTER_CLINICAL.md` §4.7.

> Verb discipline: *propose* (C1, architecture/algorithm) — *demonstrate* (C2, C3, empirical) — *show* (C4, empirical alignment with a priori cognitive prediction).
> C3 (depth-invariant reward) was treated as A3-verification only in the v1.1 3-contribution structure; promoted to standalone contribution in v1.2 to reflect §6.2's distinct empirical claims and to enable §6.x ↔ C-numbering 1:1 mapping.

## 1.4 Results preview
- **C2 (§6.1)**: 2.13× tighter $|\Delta SR|$ vs Std AIRL; NOTHING gap −13.6%p → −9.5%p (~30% reduction); Top-1 0.585 → 0.762 (LogGauss); state-conditional router adaptation (SAFE/DANGER 1.089, $p{<}.05$ all PIDs); held-out generalization placeholder (Appendix J.5).
- **C3 (§6.2)**: reward identifiability $r{=}0.784\pm 0.043$ verifies A3; cross-method 3×2 argmax concordance 100% in 5/6 cells; **continuous 5×2 heatmap** shows reward UP−NOOP varies in narrow ~0.4 range across all cells while policy UP−NOOP swings ~1.1 range (off-road: +0.53→−0.61; on-road: +0.89→−0.21) — quantitative visualization of bounded-foresight modulation localized to policy channel; SC-AIRL-Cat's policy modulates more strongly than Std AIRL at high proximity (`offroad×closeness>0.75`: π=−0.61 vs −0.36; `onroad×closeness>0.75`: π=−0.21 vs +0.00) while rewards differ ≤0.06 in all 10 cells.
- **C4 (§6.3)**: 20 / 550 (metric × clinical) cells robust across 3 main routers (`sc_cat`, `stickbreaking`, `hgauss`); 0 / 550 mixed-sign. Top robust signals: `shift_road_danger × NOTHING_ratio` r=+0.46 (within-domain bridge); `E_h_time_low × jaywalking` −0.41; DDT cluster mean +0.40; state-adaptation × BIS_motor +0.34 robust 3/3; `flex_kl_max × BIS-total` +0.29 (distribution-shape KL → first robust main-scale signal). Pillar 5 EM E[h] (distinct global-aggregate cut) UPPS-P facets +0.45–0.49. ⚠️ Legacy `sc_depth_flexibility_clinical.png` figure (STAI/DOSPERT_FIN r=−0.32) does not reproduce at canonical N=52 — flagged for regeneration before submission.
- **Supplementary (§6.4)**: behavioral graded-caution monotonicity (×5/×10) + per-attempt collision decomposition (commit/abort separation); ×100 collapse boundary diagnosed in Appendix L. Dynamic trait × stakes-sensitivity reported as exploratory in Appendix L.2 (no Bonferroni claim; BH-FDR q=.10 = 0 survivors).
- *MAP synthetic depth recovery → Appendix.*

---

# 2. Related Work (0.5 page)

> Organized as a **three-stage logical flow** (source of truth: `PAPER_prior_structure.md`):
> **S1** Why bounded horizon at all → **S2** Yao 2024 critical reception (two missing axes) → **S3** State-conditional routing + multi-depth mixed policy.
> Placed after Introduction (as in Yao 2024) to establish context before technical content.

## 2.1 S1 — Why bounded horizon: cognitive necessity and empirical validation
- **[Binz & Schulz 2022, NeurIPS 2022]** "Modeling Human Exploration Through Resource-Rational RL"
  - Infinite-horizon / Bayes-optimal RL is computationally intractable; imposing a description-length computational limit *directly on the model* reproduces vmPFC-lesion-like patient behavior (impulsive risky commitment under inability to compute complex futures).
  - **Role in our argument** — *architecture-level precedent, not symptom-level mapping*: bounded rationality should be built into the model's structure, the way Binz applied a resource constraint to the RR-RL2 model itself — *not* treated post-hoc as noise or suboptimality. Binz's specific behavioral result is participant-level and is **not** mapped onto our model's failures (which are model-level and live in a different hierarchy). Binz §4.1 is separately our mechanism-validation template at §6.3 (depth × clinical correlation).
- **[RHIP — Barnes et al. 2023]** "Receding Horizon Inverse Planning" (Google Maps)
  - Infinite-horizon MaxEnt IRL is infeasible at global scale; with H=10 receding horizon, predictions of real driver trajectories *improve* over H=∞.
  - **Role in our argument**: billion-scale empirical evidence that bounded horizon fits human behavior better than infinite — h-step truncation is not merely computational convenience.
- **[Tian et al. 2021]** "Bayesian Inference of Latent Intelligence Level"
  - Each agent's unknown cognitive bound modelled as a latent intelligence level, jointly inferred with reward via Bayesian inference over trajectories.
  - **Role in our argument**: methodological precedent for treating the cognitive bound (here: planning depth) as a *latent variable inferred from behavior*, not a fixed hyperparameter.
- **[Lee et al. 2024, *Psychol. Sci.*]** "Bridging the Gap Between Self-Report and Behavioral Laboratory Measures: A Real-Time Driving Task With Inverse Reinforcement Learning"
  - Closest real-time-IRL precedent on cognitive-psychology-grade human data. Applies deep AIRL to a real-time driving task (N=47); IRL-inferred latent reward predicts BIS impulsivity ($r{=}.72$), substantially outperforming behavioral summary statistics ($r{=}.48$) and absorbing all incremental variance.
  - **Role in our argument**: (i) immediate methodological precedent — same lab lineage and IRL paradigm as our pedestrian dataset; (ii) inherits the *infinite-horizon Boltzmann-rational* assumption that SC-AIRL relaxes; (iii) source of the "summary statistics insufficient at the latent-mechanism level" claim cited in §5.2 baseline scoping and §6.3 mechanism validation.
- Supporting cognitive evidence: working-memory limits (Cowan 2001; Miller 1956); bounded rationality (Simon 1955, 1991; Russell 1997; Lieder & Griffiths 2020); state-dependent truncation of lookahead (Otto et al. 2013; Huys et al. 2012); rational resource allocation (Callaway et al. 2022).

## 2.2 S2 — Yao 2024: critical reception and the two missing axes
- **[Yao et al. 2024, NeurIPS 2024]** "IRL with Multiple Planning Horizons"
  - Formalizes the horizon–reward non-identifiability (short-h-large-r ≡ long-h-small-r). Solution: per-agent discount $\gamma_i$ jointly inferred with a shared reward in tabular 5×5 settings.
  - **Closest prior work**. SC-AIRL's differentiation is on two axes:
- **Axis 1 — γ-rescaling ≠ physical h-step truncation.** Yao 2024 modulates the *discount* but the planner still performs infinite-lookahead value computation. SC-AIRL instead sets $V_\text{tail}\!\equiv\!0$ and physically truncates the advantage via GAE-h ($A_t^{(h)}$), reflecting working-memory computational cutoff rather than value rescaling.
- **Axis 2 — per-agent fixed vs. state-conditional.** Yao 2024 assigns one fixed horizon per expert; van Opheusden 2023 (§2.3) shows the same individual's depth shifts with state. SC-AIRL learns $p_\phi(h|s)$ at per-state granularity.
  - **Practical advantage in driving/pedestrian domains**: the *Trajectory-level (Yao) → State-level (SC-AIRL)* shift is not a marginal refinement but a functional necessity — at a crosswalk the effective horizon collapses (h small), on an empty sidewalk it expands (h large). A per-trajectory fixed horizon cannot represent this within-episode variation that dominates real human navigation.
- **Identifiability context**: Cao et al. 2021 characterizes reward–horizon non-identifiability theoretically; Schultheis et al. 2022 motivates non-exponential discounting. Bounded-rationality theoretical work (DCPPO — Li 2023; Mazumdar 2024) analyzes bounded agents but does *not* learn the bound from demonstrations.
- **Heterogeneity-as-noise alternatives**: IRLEED (Beliaev & Pedarsani 2024) and DTIL (Seo & Unhelkar 2025) treat demonstrator variation as suboptimality/expertise; SC-AIRL instead treats it as a structural bounded-foresight property.

## 2.3 S3 — State-conditional routing and multi-depth mixed policy

### (A) State-dependent depth is real; latent state-conditional factors are identifiable from behavior
- **[van Opheusden et al. 2023, *Nature*]** "Expertise increases planning depth in human gameplay"
  - Combines reaction times, eye-tracking, and heuristic-search models to back out decision trees. Planning depth is *not fixed per individual*: it deepens with expertise but immediately shortens under time pressure.
  - **Role in our argument**: direct empirical refutation of "one fixed depth per person" — motivates $p(h|s)$ rather than $p(h|i)$.
- **[IDIL — Seo & Unhelkar 2024]** "Imitation Learning of Intent-Driven Expert Behavior"
  - EM over a latent state-dependent intent with factored distribution matching; explicitly avoids end-to-end adversarial latent inference as unstable.
  - **Role in our argument**: methodological basis for SC-AIRL's E-step posterior $q(h|s,a)$ + M-step KL distillation to $p_\phi(h|s)$ (§4.5). Addresses reviewer concern about router training stability: we cite IDIL as the precedent for factored rather than end-to-end latent-variable learning.
- **[MMICRL — Qiao et al. 2023]** "Multi-Modal Imitation under Constraints with RL"
  - Conditional density estimator clusters mixed-demonstrator data by agent type before imitation; single-policy averaging causes severe constraint violation.
  - **Role in our argument**: ML-level justification that heterogeneous behavior modes *must* be separated into a multi-policy family — supports SC-AIRL's $\{\pi^h\}_{h\in\mathcal{H}}$ over a single-policy baseline. **SC-AIRL's own contribution over MMICRL** is to move the heterogeneity unit from trajectory level (one type per demonstrator) to state level (depth assignment varies within a single trajectory), matching the cognitive property that planning depth shifts with the current state.

### (B) Multi-policy mixture-of-experts architecture avoids mode averaging
- **[IMC — Blessing et al. 2023, NeurIPS 2023]** "Information Maximizing Curriculum"
  - MoE gating for multimodal expert data. Routing form $p(a|o)=\sum_z g_\phi(z|o)\,p_{\theta_z}(a|o,z)$ maps directly onto SC-AIRL's $\pi_\text{mix}(a|s)=\sum_h f_\phi(s)_h\,\pi^h(a|s)$.
  - **Role in our argument**: architectural precedent for mixture-over-latent-mode imitation; "NOTHING-gap" closure is our instance of IMC's mode-averaging pathology.
- **[PEMMFIRL / Meta-IRL-MFG — Chen et al. 2025]** "Meta-IRL for Mean Field Games via Probabilistic Context"
  - Probabilistic context variable $m$ inferred via $q_\psi(m|\tau)$ + mutual-information regularization; jointly recovers heterogeneous rewards from mixed trajectories.
  - **Role in our argument**: theoretical backing for posterior-distilled latent-context learning; planning depth $h$ is our analogue of $m$.
- **[MoDE — Reuss et al. 2024]** "Efficient Diffusion Transformer Policies with MoE Denoisers"
  - Noise-conditioned router routing tokens to specialized sub-experts; 90% FLOPs reduction + SOTA on 134 robot-manipulation tasks.
  - **Role in our argument**: state/context-conditional MoE routing is the current SOTA architectural direction; $p_\phi(h|s)$ is the depth-axis instance, not an ad-hoc heuristic.
- **[MH-AIRL — Chen et al. 2023]** "Multi-task Hierarchical AIRL"
  - Closest architectural neighbor: hierarchical AIRL with per-task latent context. Same backbone, different gating axis (task vs. depth).

---

> **Logical flow summary** (mirrors `PAPER_prior_structure.md`):
> (1) Infinite horizon is neither cognitively plausible (Binz) nor empirically best-fitting (RHIP) — planning depth is already treated as latent (Tian). (2) Yao 2024 partially addresses horizon heterogeneity via per-agent γ but misses (i) physical h-step truncation and (ii) within-individual state-dependency. (3) Real human depth shifts with state (van Opheusden); latent state-conditional factors can be stably identified via factored inference (IDIL, PEMMFIRL) and aggregated by MoE routing (IMC, MoDE, MH-AIRL). SC-AIRL = $V_\text{tail}\!\equiv\!0$ GAE-h + Bayesian $p_\phi(h|s)$ router over $\{\pi^h\}_{h\in\mathcal{H}}$.

---

# 3. Preliminaries & Problem Formulation (0.75 page)

> *Notation is inlined in §3.0 (no dedicated sub-section). Full notation table in Appendix §9.A.*

## 3.0 Preliminaries (1 paragraph)
- MDP $(\mathcal{S}, \mathcal{A}, P, r^\star, \gamma)$, trajectory $\tau = (s_0, a_0, \ldots)$
- MaxEnt IRL recap (Ziebart 2008): policy $\pi^\star \propto \exp(Q^\star)$
- Standard AIRL (Fu et al. 2018): $D_\theta(s,a,s') = \sigma(f_\theta - \log \pi_\phi)$, infinite-horizon $V_\pi$
- One sentence: "We now state the assumptions that differentiate our setting from standard AIRL."

## 3.1 Assumptions
- **(A1) Bounded foresight (physical, not discount rescaling).** Each expert decision at $s$ is produced by an $h$-step policy with $h\in\mathcal{H}=\{2,3,5,10\}$; the planner performs lookahead over exactly $h$ steps and contributes *no value beyond it* (no bootstrap past $h$, §4.3). Departs from Yao 2024 whose per-agent $\gamma_i$ rescales but leaves infinite lookahead intact.
  - $\mathcal{H}$ brackets the working-memory capacity $4{\pm}1$ (Cowan 2001; Miller 1956): from below ($h{=}2,3$), through capacity ($h{=}5$), to beyond ($h{=}10$); also matches the typical $\sim$10-step horizon of pedestrian-crossing decisions.
  - Behavioral support: Opheusden 2023; Callaway 2022; Huys 2012; Otto 2013.
- **(A2) State-conditional depth (cognitive MoE).** Depth is drawn from $p(h|s)$ that varies *within* a trajectory as a function of the current state, not once per trajectory or once per expert. This realizes a cognitive mixture-of-experts view: behavior arises from several decision systems whose relative influence is gated online by state.
  - Distinction from MH-AIRL (Chen 2023): task skill is fixed within a trajectory; our router conditions on state and varies *over the course of a single trajectory*.
- **(A3) Shared reward (structural modeling commitment).** All experts share a single ground-truth $r^\star$; heterogeneity is confined to the planner family $\{(h,\pi^h)\}$. Architectural realization: a single approximator $r_\theta$ shared across depths, **no potential shaping** ($\Phi\equiv 0$) — separates "what agents value" from "how deeply they plan." Verified empirically in §6.3 (cross-correlation $r{=}0.784$); formal identifiability discussion in Appendix A.

## 3.2 The heterogeneous-foresight imitation problem
> *Single narrative: the imitation gap. Identifiability is treated as support in §5, not a separate technical "challenge".*

- **Setup.** Given $N$ demonstration trajectories from experts with unknown $h_i(s) \in \mathcal{H}$, recover $r^\star$ (up to IRL equivalence) and $p(h \mid s)$.
- **The imitation gap.** Standard AIRL, which assumes a single effective horizon, cannot reproduce human *suboptimal* action patterns — in particular deliberate no-ops (waiting / hesitation) and short-sighted committals.
  - Concretely on pedestrian data: Std AIRL drives $P(\text{NOTHING})$ toward zero (over-committing) — see Fig. 1c (preview)
  - Finite-horizon planning is already known to matter in large-scale IRL: RHIP (Barnes et al. 2023, Google Maps) uses a tunable receding horizon but treats it as a fixed global hyperparameter — we learn a *per-state, per-agent* depth distribution.
- **Why this is hard.** Two confounds couple: (i) a short-horizon rational agent and a long-horizon agent with suboptimal reward can produce the same action, so reward learning is non-identifiable without structural constraints (formal discussion in Appendix A; empirical verification in §6.3); (ii) p(h|s) must be inferred from behavior alone.

---

# 4. State-Conditional AIRL (sc-AIRL) (2.5 pages) ← main contribution section

> **Naming (resolved 2026-04-17).** Model name is **SC-AIRL** throughout — title, abstract, §1–§9, and Figure 1. Matches code-side `sc_categorical`/`sc_poisson`. The two variants are referred to as *SC-AIRL-Cat* (categorical router, default) and *SC-AIRL-Poi* (Poisson router, ablation).

> **Figure 1 (required, first figure of paper).** sc-AIRL system diagram:
> expert trajectories ⇄ **D_mix discriminator** (top) ← **mixed policy π_mix** ← **multi-policy {π^h, V^h}_{h∈H}** (center) ← **router p_φ(h|s)** (bottom). Shared reward $r_\theta$ feeds $D_\text{mix}$; GAE-h truncated advantage $A_t^{(h)}$ feeds each $(\pi^h, V^h)$; Bayesian posterior $q(h|s,a,s') \propto p_\phi(h|s) D_\theta(\cdot,h)$ closes the router loop.

## 4.1 Overview — three structural replacements (Table 1)
- One narrative sentence: "We introduce **SC-AIRL**, a State-Conditional AIRL algorithm that trains a per-depth policy family $\{\pi^h\}_{h\in\mathcal{H}}$ against a shared reward $r_\theta$; a state-conditional router $p_\phi(h|s)$ composes them into a mixed policy $\pi_\text{mix}$, which serves both as the generator for $D_\text{mix}$ and as the inference-time action distribution."
- **Three-axes table (Table 1, §4.1)** — each row replaces a Standard AIRL object and is licensed by one assumption (A1/A2/A3):

  | Axis | Standard AIRL | SC-AIRL | Licensed by |
  |---|---|---|---|
  | Truncation | $G_t = \sum_{k=0}^{\infty}\gamma^k r$ | $G_t^{(h)} = \sum_{k=0}^{h-1}\gamma^k r_\theta$ | A1 |
  | Multi-policy | single $\pi$ | $\{\pi^h\}_{h\in\mathcal{H}}$ mixed by $p_\phi(h\|s)$ | A2 |
  | Shaping term | $f_\theta = r_\theta + \gamma\Phi(s') - \Phi(s)$ | $f_\theta = r_\theta$; $\Phi\equiv 0$; no $h$-boundary bootstrap | A3 |

- **Coupling paragraph**: the three replacements are *mutually supporting* — unshaped reward prevents both leakage of truncation into $r_\theta$ and re-introduction of an infinite-horizon tail through a boundary bootstrap; truncation is what creates the horizon heterogeneity that the router composes. Identifiability discussion in Appendix A; empirical verification in §6.3.

## 4.2 Depth-invariant reward parameterization (Eq. 1–3)
- **Eq. 1 (AIRL reward form, general):** $f_\theta(s,a,s') = r_\theta(s,a) + \gamma\Phi(s') - \Phi(s)$
- **Eq. 2 (H-step telescoping identity):**
  - $\sum_{k=0}^{h-1}\gamma^k [f_\theta(s_{t+k},a_{t+k},s_{t+k+1}) - r_\theta(s_{t+k},a_{t+k})] = \gamma^h\Phi(s_{t+h}) - \Phi(s_t)$
- **Design choice — $\Phi \equiv 0$.** Under (A1) the boundary term $\gamma^h\Phi(s_{t+h})$ is absorbed by the per-depth value bootstrap $V^h(s_{t+h})$ at the truncation (§4.3); making $\Phi=0$ removes the redundancy and leaves $r_\theta$ as the sole learnable reward component shared across depths.
- **Eq. 3 (effective shared reward used by the discriminator):** $f_\theta(s,a,s') = r_\theta(s,a)$
- **Why this ordering first**: all subsequent components ($\pi^h$, $D_\text{mix}$, router) are defined against one reward $r_\theta$ — depth-invariance is baked in from the start rather than bolted on.
- (Identifiability discussion → Appendix A)

## 4.3 Multi-policy architecture (Eq. 4–6)
- Per-depth actor $\pi^h_\omega$ and critic $V^h_\xi$ (shared encoder, depth-indexed heads)
- **Eq. 4 (H-step truncated return):** $G_t^{(h)} = \sum_{k=0}^{h-1}\gamma^k r_\theta(s_{t+k}, a_{t+k})$  (no bootstrap beyond $h$)
- **Eq. 5 (GAE-h TD residual):** $\delta_t^{(h)} = r_\theta(s_t, a_t) + \gamma V^h(s_{t+1}) - V^h(s_t)$
- **Eq. 6 (GAE-h advantage):** $A_t^{(h)} = \sum_{k=0}^{h-1}(\gamma\lambda)^k \delta_{t+k}^{(h)}$
- **Architectural commitment — $V_\text{tail} \equiv 0$**: bounded foresight is *architectural*, not a training heuristic. Prevents the $V_\text{tail}$ double-counting pathology (Appendix §9.D.7).
- $\mathcal{H} = \{2, 3, 5, 10\}$ (log-spaced): covers working-memory limits and pedestrian-task horizon.

## 4.4 Mixed-policy discriminator (Eq. 7–9)
- **Eq. 7 (mixed policy):** $\pi_\text{mix}(a|s) = \sum_h p_\phi(h|s)\,\pi^h(a|s)$ — same object as inference-time density (§4.3)
- **Eq. 8 (D_mix — AIRL with mixed-policy denominator):**
  $D_\text{mix}(s,a,s') = \dfrac{\exp f_\theta(s,a,s')}{\exp f_\theta(s,a,s') + \pi_\text{mix}(a|s)}$
  - The depth $h$ is latent on the expert side; marginalization lives inside $\pi_\text{mix}$, not on the expert log-density. Router weights $p_\phi(h|s)$ act as a learned per-state responsibility.
- **Eq. 9 (adversarial loss):**
  $\mathcal{L}_D = \mathbb{E}_{\pi_E}[-\log D_\text{mix}] + \mathbb{E}_{\pi_\text{mix}}[-\log(1 - D_\text{mix})]$
- **Eq. 9' (entropy bonus to prevent early mixture collapse):** $-\lambda_\text{ent}\,\mathbb{E}_{\pi_E}[\mathbb{H}(q_D)]$ where
  $q_D(h|s,a) \propto p_\phi(h|s)\,\pi^h(a|s)\,\dfrac{\exp f_\theta}{\exp f_\theta + \pi^h(a|s)}$
  - Why: a single $D_\text{mix}$ delivers gradient through $\pi_\text{mix}$ as a whole; if router collapses early, dominant depths absorb the signal and the rest lose differentiation gradient. $\lambda_\text{ent}=10^{-2}$; sharpens automatically once $\{\pi^h\}$ specialize.
- **Training schedule (EM-style)**:
  - Warmup $0 \le t < T_\text{warm} = 10{,}000$: $p_\phi(h|s)=1/|\mathcal{H}|$ (frozen uniform) — defers router fit until $\{\pi^h\}$ stabilize.
  - Main phase $t \ge T_\text{warm}$: re-estimate $p_\phi$ every $\Delta_\text{router}=10$ rounds.
  - Rationale: stability analysis on $n{=}47$ `sc_categorical` runs (Appendix §9.B.3).

## 4.5 State-dependent depth router (Eq. 10–12)
- **Router objective — mixture NLL against expert (factored, not end-to-end).**
  $\mathcal{L}_\text{router}(\phi) = -\mathbb{E}_{(s,a)\sim\pi_E}\Big[\log\sum_{h\in\mathcal{H}} p_\phi(h|s)\,\pi^h(a|s)\Big]$
  - Per-depth policies $\{\pi^h\}$ held *frozen* during the router update; router never sees the discriminator gradient directly.
  - Equivalent (up to constant) to $\mathbb{E}[\text{KL}(q(h|s,a) \,\|\, p_\phi(h|s))]$ where $q(h|s,a)\propto p_\phi(h|s)\,\pi^h(a|s)$ — Appendix §9.A derivation.
  - The same trained $p_\phi$ feeds $D_\text{mix}$ (§4.4) — single router governs both inference mixture and discriminator denominator.

- **Two output-distribution variants (shared backbone: 2 hidden layers, LeakyReLU, dropout).** Differ only in final projection + output map, so any gap isolates the *structural prior* effect rather than capacity.
  - **Categorical (default):** $p_\phi(h_k|s)=\text{softmax}(g_\phi(s))_k$ — *no shape prior*.
  - **Gaussian kernel (ablation):** $p_\phi(h_k|s)\propto\exp\!\bigl(-(k-\mu_\phi(s))^2/(2\sigma^2)\bigr)$ where $\mu_\phi(s)\in[0,|\mathcal{H}|-1]$ is a single bounded scalar output and $\sigma$ is fixed. Encodes **unimodality over depth index**: nearby depths share probability; far-apart depths cannot jointly dominate.

> **Note (revised from v1.2)**: Poisson variant deprecated in favor of **Gaussian-kernel** unimodal prior — same unimodality assumption, simpler parameterization (single bounded scalar instead of rate $\lambda$). Matches code `gaussian_kernel_router` and draft §4.5 directly.

- **Why factored / E-M decoupling, not end-to-end.** End-to-end joint training of $p_\phi$ through $D_\text{mix}$ and per-depth policies is reported unstable for latent-variable imitation (IDIL, Seo & Unhelkar 2024; also PEMMFIRL, Chen 2025). SC-AIRL's factored objective fits $p_\phi$ to the expert marginal under frozen $\{\pi^h\}$, yielding stable and interpretable routing.

## 4.6 Training algorithm (Algorithm 1 → Appendix A.6)
> **Moved to Appendix A** (page-budget reason, v1.2 revision 2026-04-28). Main-body §4.4–§4.5 already specify per-step training objectives ($D_\text{mix}$ adversarial + PPO inner loop + mixture-NLL router). Full pseudocode (warmup phase, EM-style alternation, EMA log-prior update, state/reward/return normalization, checkpoint/eval hooks) lives in **Appendix A.6** alongside the formal results, and detailed implementation is in **Appendix C**.
- **Pointer to Appendix A.6**: 1-line summary in main-body — "Each round: (i) on-policy rollout from $\{\pi^h_{\omega_h}\}$; (ii) $D_\text{mix}$ update on $r_\theta$; (iii) PPO update on $A_t^{(h)}$; (iv) router update on Eq. 12 (every $\Delta_\text{router}=10$ rounds, post-warmup)."
- **Ablation conditions (2×2)** — investigated in §6.5:
  - Router parameterization: Categorical softmax vs. Gaussian kernel.
  - Router–discriminator update loop: "no-loop" (router enters $D_\text{mix}$ only via $\pi_\text{mix}$ assembly) vs. "loop" (router additionally re-weights generator samples by $p_\phi(h|s_\text{gen})$ — closes EM feedback as both prior + responsibility).

---

# 5. Experimental Setup (1 page)

> **Restructure note (v1.2, 2026-04-28)**: previous §5 *Theoretical Analysis* (Propositions 1–2 + Remark) **moved to Appendix A** — prior works (Yao 2024; MH-AIRL; IDIL) similarly do not include such formal results in the main body, and the propositions' role here was vague (no empirical claim depended on them). Main-body space reallocated to behavioral / reward-superiority / mechanism-validation results (new §6).

## 5.1 Non-standard Real-World Pedestrian Dataset (Use-Inspired emphasis)
- **N=52 participants** (P904 + P1000–P1054, excluding 6 outliers — see canonical N=52 policy)
- **State**: 113-dim (ego position 2 + velocity 2 + heading 1 + task context 3 + surrounding 4 vehicles × 25 features + lane structure 5)
- **Actions**: 5 discrete — NOTHING, UP, DOWN, LEFT, RIGHT
- **Use-Inspired framing**: not a standard ML benchmark; real-time real-world pedestrian decision data carrying human cognitive limitations (deliberate waiting under risk, shifting risk thresholds, asymmetric lateral preferences). Same lab/paradigm lineage as Lee et al. (2024) — pedestrian-crossing variant of the highway-IRL pipeline.
- **Depth grid** $\mathcal{H}=\{2,3,5,10\}$: brackets working-memory capacity $4{\pm}1$ (Cowan 2001) and matches typical pedestrian-decision horizon (~10 steps from far-side observation to crossing commit).

## 5.2 Baselines — Ablation Ladder & Triangulation
> **Scoping (Option B+, see §13.3)**: contribution is at the *data-driven IRL* level. Non-ML generative models (Helbing & Molnár 1995) and behavioral summary statistics excluded by IRL objective and Lee 2024 dominance argument respectively. The 5-baseline ladder below isolates *each design axis* — supervised vs adversarial; horizon ∞ vs finite; per-trajectory vs per-state.

| ID | Name | Reward learning | Horizon | Heterogeneity unit | Role |
|----|------|----------------|---------|-------------------|------|
| **B1** | **Behavioral Cloning** | ✗ (supervised) | n/a | none | Surface-imitation upper bound |
| **B2** | **Std AIRL** (Fu 2018) | ✓ | $h{=}\infty$ | none | Infinite-horizon AIRL (primary baseline) |
| **B3** | **GAIL** (Ho & Ermon 2016) | ✗ (no reward net) | $h{=}\infty$ | none | Adversarial IL without reward |
| **B4** | **Single-$h$ AIRL** | ✓ | $h\in\{2,3,5,10\}$ fixed | none | Isolates depth choice |
| **B5** | **EM-depth AIRL**† | ✓ | episode-level $h$ | per-trajectory | Trajectory-level horizon mixture |
| **OURS** | **SC-AIRL** (Cat / Gauss / LogGauss) | ✓ | $p_\phi(h|s)$ | **per-state** | Full state-conditional bounded foresight |

- **Triangulation logic**: B1 vs B2 isolates *adversarial reward learning* effect; B2 vs B4 isolates *finite vs infinite horizon*; B4 vs B5 isolates *fixed vs trajectory-mixed h*; B5 vs Ours isolates *state-conditional vs trajectory-conditional*.
- **† EM-depth — positioning vs Yao 2024**: B5 is an *episode-level baseline that extends the core insight of Yao et al. (2024) — that planning-horizon heterogeneity should be jointly inferred with reward — to our physical-truncation setting*. It does **not** reproduce Yao 2024's algorithm; Yao modulates a per-agent discount $\gamma_i$ while keeping infinite-lookahead value computation, whereas our B5 keeps physical $h$-step truncation but lets $h$ be inferred per episode rather than per state. Hence B5 isolates the *trajectory-level vs state-level granularity* axis cleanly, without conflating it with the discount-vs-truncation axis already addressed by B4 vs B2.

## 5.3 Evaluation Metrics — Domain-Aligned, beyond Success Rate
- **Behavioral imitation + state-conditional routing** (§6.1):
  - Top-1 accuracy, action distribution TV/KL/JS, per-action recall (NOTHING/UP/DOWN/LEFT/RIGHT)
  - **NOTHING-gap** (rollout): closure of the deliberate-waiting under-representation that single-horizon AIRL produces
  - Success-rate matching: $|\Delta SR|$ (rollout − expert) — *closer is better* (we do not want to overshoot expert; bounded humans, not optimal agents)
  - Router quality: inter-individual entropy CV%, within-participant entropy σ, depth ratio SAFE/DANGER, peak-h distribution
  - In-distribution generalization (T1–T4 acceptance criteria, held-out map seeds — Appendix J.5)
  - MAP synthetic-data depth recovery → Appendix sanity
- **Reward recovery + task-goal absorption** (§6.2):
  - Cross-correlation $r{=}0.784\pm 0.043$ between SC-AIRL and Std AIRL rewards (verifies A3 shared-reward)
  - 3×2 contextual-cell argmax-action concordance: per-cell mean reward argmax under both methods (`{off-road, on-road} × {none / medium / close vehicle proximity}` based on `max(obs[77,81,89,93])` head-closeness)
  - Reward-vs-expert action-mode dissociation (negation-style decoupling evidence): reward UP-argmax in 6/6 cells; expert unanimously NOOP in `offroad_close` (52/52 PIDs) vs reward UP-dominant — 73–90% dissociation in off-road × {medium, close}
- **Convergent cognitive validity** (§6.3): depth ↔ DDT log(k) / BIS Motor / UPPS-P correlations (per Binz 2022 template)
- **Robustness & dynamic adaptation under covariate-shift OOD** (§6.4 supplementary): graded-caution monotonicity at ×2/×5/×10; trait-conditional dynamic adaptation (S_UPPS_P, CES_D); ×100 collapse boundary (Appendix L)

---

# 6. Results (3 pages)

> **Restructure rationale (v1.2 / 2026-04-28)**: §6 is reorganized into 4 result sections + 1 ablations, with **1:1 mapping** to v1.2's calibrated 4-contribution structure (C1/C2/C3/C4):
> - **§6.1 ↔ C2** (+ C1 architectural mechanism + train-test): SC-AIRL achieves improved imitation fidelity via state-conditional MoE routing; train-test placeholder demonstrates not-memorization.
> - **§6.2 ↔ C3**: depth-invariant reward recovery (verifies A3) + task-goal absorption (cell-level argmax concordance + reward-vs-expert dissociation).
> - **§6.3 ↔ C4**: convergent cognitive validity with clinical phenotypes (Binz template).
> - **§6.4 (supplementary)**: covariate-shift OOD robustness; dynamic OOD leads provide converging evidence for C4.
> - Theoretical theorems (Prop 1/2) and Algorithm 1 live in Appendix A (A.1, A.2, A.6); OOD heavy details (multiplier curve, ×100 collapse, failure modes) in Appendix L.

## 6.1 Imitation Fidelity under Bounded Foresight (C2)
> **Research question**: how well does SC-AIRL imitate human pedestrian behavior under bounded foresight, and does the imitation generalize beyond trained trajectories?

### Imitation result — SC-AIRL recovers human-aligned action distributions
- **Headline metrics** (full-data, N=52): Top-1 accuracy **0.762** (SC-LogGauss) / **0.725** (SC-Cat); $|\Delta SR|$ to expert **0.069 / 0.093**; NOTHING-action gap reduced from −13.6%p (Std AIRL) to **−9.5%p** — closing ~30% of the deliberate-waiting deficit relative to single-horizon baselines.
- **Comparison anchor (Table 1)** — pinpointing where each baseline class fails the bounded-rational human signal:

  | Model | Top-1 ↑ | Rollout SR | $\|\Delta SR\|$ ↓ | NOTHING (rollout) | NOTHING gap |
  |---|---|---|---|---|---|
  | **B1 BC** | 0.887 | 0.474 ✗ | 0.166 | TBD | TBD |
  | **B2 Std AIRL** | 0.585 ✗ | 0.823 | 0.187 | 0.270 | −13.6%p |
  | **B5 EM-depth** | TBD | TBD | TBD | TBD | TBD |
  | **OURS SC-Cat** | 0.725 | 0.706 | 0.093 | 0.312 | −9.5%p |
  | **OURS SC-LogGauss** | **0.762** | 0.705 | **0.069** | 0.311 | −9.5%p |
  | Expert | 1.000 | 0.640 | 0.000 | **0.407** | 0.0%p |

  - BC over-fits step-level surface and fails task; Std AIRL over-commits beyond expert SR; trajectory-level horizon mixture (B5) cannot capture moment-to-moment hesitation. SC-AIRL is the only model that simultaneously matches expert Top-1, expert SR, and expert NOTHING-rate.

### Mechanism — state-conditional planning depth captures within-trajectory variation (C1)
- The router does **not** collapse to a single mode: inter-individual $E[h]$ ranges 3.94–6.19 (SC Cat); entropy CV% = 14.2% (vs fixed-σ Gaussian 2.4%) — captures person-level variation.
- **State-conditional adaptation** (statistically robust, p<.05 across all PIDs):

  | Zone | $E[h]$ (SC Cat) | $E[h]$ (LogGauss) |
  |---|---|---|
  | SAFE | 5.10 ± 0.45 | 5.55 |
  | DANGER | 4.70 ± 0.35 | 5.19 |
  | Ratio (SAFE/DANGER) | **1.089 ± 0.110** | 1.077 |

  Deeper deliberation in safe zones, reactive shallow planning under danger — recovers within-individual depth shift (van Opheusden 2023, *Nature*) from behavior alone, consistent with rational resource allocation (Callaway 2022) and time-pressure pruning (Huys 2012; Otto 2013). This per-state deliberation/reaction switch is the structural feature absent in single-horizon AIRL and trajectory-mean horizon mixtures, and is the proximate mechanism for the imitation improvements above.
- *MAP synthetic-data sanity → Appendix.*

### Generalization — held-out map seeds confirm imitation is not memorization
- **Pre-registered held-out evaluation (Table 1b, stratified 8/40)** — *placeholder; pending server execution per Appendix J.5*:

  | Model | Train Top-1 | Held-out Top-1 | Generalization gap | T1–T4 status |
  |---|---|---|---|---|
  | **B1 BC** | 0.887 | TBD | TBD | n/a |
  | **B2 Std AIRL** | 0.585 | TBD | TBD | TBD |
  | **B4 Single-h (h=5)** | TBD | TBD | TBD | TBD |
  | **OURS SC-Cat** | 0.725 | TBD | TBD | TBD |

- Acceptance criteria pre-registered (T1–T4, Appendix J.5); execution status: code/launcher/dry-run ✅, 53-PID retraining ⏸ pending.
- **Claim contingent on execution**: state-conditional bounded-foresight imitation generalizes to held-out environments — depth routing is a learned cognitive policy, not trajectory memorization.

- **Figures**: `P2_5action_barplot.pdf`, `router_state_zone_depth.pdf`, `router_individual_differences.pdf`.

## 6.2 Depth-Invariant Reward Recovery and Task-Goal Absorption (verifies A3, supports C1)
> **Research question**: does separating depth heterogeneity into the planner family $\{\pi^h\}$ leave behind a single shared reward that encodes only the *task goal* — with all *contextual decision heterogeneity* absorbed by the bounded-foresight policy/router? (A3 verification + decoupling thesis.)

- **(i) Reward landscape preservation (anchor)**: per-PID Pearson $r{=}0.784 \pm 0.043$ between SC-AIRL and Std AIRL on the (s,a) reward landscape across N=52 (51/52 with $r{>}0.6$; Fisher-z one-sample test against $r{=}0$ yields $p{<<}10^{-50}$). Per-action $r \in [0.598, 0.703]$. We do **not** claim formal AIRL identifiability-class membership; the empirical claim is that the architectural commitment (A3, shared reward) is realized.
- **(ii) Cross-method 3×2-cell argmax-action concordance (visual A3)**: on a contextual cell grid `{off-road, on-road} × {none, medium, close}` (vehicle imminent **closeness** $C = \max(\text{obs}[77,81,89,93]) \in [0,1]$ — head-closeness of the nearest car in the same row and one row ahead, on left and right; max over the 4 imminent-vehicle proximity channels — binned at $0$ / $(0,0.5]$ / $>0.5$), per-cell mean reward argmax-action is **UP-dominant across all 6 cells in both methods**. Cross-method concordance is **100% in 5/6 cells**; only `offroad_close` (safe-zone but vehicle imminent) shows partial divergence (65.4% = 34/52 PIDs agree; SC-AIRL-Cat: 37 UP / 14 NOOP / 1 RIGHT vs Std AIRL: 47 UP / 5 NOOP).
- **(iii) Reward-vs-Expert dissociation (decoupling — *negation-style* evidence)**: while reward argmax is UP-dominant in 6/6 cells, expert mode shifts dramatically by context. In `on-road × {none, medium}` expert is also UP-unanimous (52/52) → 0% dissociation. In `off-road × medium` expert is NOOP-dominant (43/52) → 88.5% dissociation. In **`off-road × close` (safe zone with imminent vehicle) expert is UNANIMOUSLY NOOP across all 52 PIDs** — the cleanest possible expression of bounded-rational deliberate waiting — yet the reward remains UP-dominant (73.1% dissociation under SC-AIRL-Cat, 90.4% under Std AIRL). The reward thus encodes only the *task goal* (cross by going UP); the contextual decision heterogeneity exhibited by humans (waiting, observation, cautious approach) is absorbed by the bounded-foresight policy/router rather than by the reward — directly verifying the architectural commitment that $\{\pi^h\}$ carries the depth heterogeneity, not $r_\theta$. Consistent with the §6.1 NOTHING-gap closure (rollout NOTHING 0.312 vs expert 0.407, mixture 0.232).
- **(iv) Cell-level preference confidence (supplementary)**: $|r(\text{argmax}) - r(\text{runner-up})|$ shows a coherent pattern — SC-AIRL-Cat is sharper than Std AIRL in `offroad_none` (paired $d{=}+0.85$, $p{=}1.4{\times}10^{-7}$), `offroad_medium` ($d{=}+0.48$), and `onroad_close` ($d{=}+0.40$); but **less sharp** in `offroad_close` ($d{=}-0.28$, $p{=}0.05$), consistent with the partial NOOP-encoding observed in (ii). The two-direction signal (less concordance + less sharpness in `offroad_close`) provides convergent evidence that SC-AIRL-Cat's reward exhibits weak but measurable contextual modulation in the most extreme threat cell — though main claim rests on (i)–(iii).
- **(v) Reward-policy decoupling (continuous 5×2 heatmap, refined 2026-04-29)**: refining the X-axis to 5 equal-width **closeness** bins ($C \in \{0,\,(0,0.25],\,(0.25,0.5],\,(0.5,0.75],\,(0.75,1]\}$, where $C$ is defined in (ii) above) and computing softmax(reward) UP−NOOP probability vs policy π(UP|·)−π(NOOP|·) per cell yields a *quantitative visualization of the decoupling thesis*: across all 10 cells, **reward UP−NOOP varies in a narrow band (off-road: +0.44 → +0.04; on-road: +0.69 → +0.34, ~0.4 range)** while **policy UP−NOOP swings dramatically (off-road: +0.53 → −0.61; on-road: +0.89 → −0.21, ~1.1 range)**. The reward−policy gap grows monotonically with closeness (off-road: 0 → 0.65), directly measuring the magnitude of contextual modulation absorbed by the bounded-foresight policy. SC-AIRL-Cat's policy modulates more strongly than Std AIRL in the highest-closeness cells (off-road × closeness>0.75: SC π=−0.61 vs Std π=−0.36; on-road × closeness>0.75: SC π=−0.21 vs Std π=+0.00), while the rewards differ by ≤0.06 in all 10 cells.
- **Figures**: `analysis/REWARD_COMPARISON/figures/reward_policy_heatmap_5bin.{pdf,png}` (4-panel 5×2 continuous heatmap, paper §6.2 main figure; PDF for LaTeX, PNG for slides/Notion), `fig4_3x2_argmax.pdf` (2-panel categorical 3×2 supplementary), `fig4_recovery.pdf` (per-PID r=0.784 distribution).

## 6.3 Convergent Cognitive Validity of the Inferred Planning Depth (C3)
> **Research question**: does the latent depth that SC-AIRL infers from behavior alone correspond to a meaningful cognitive construct, as predicted by independent psychometric measures? (Binz 2022 template; model-mechanism prediction, not a clinical-utility claim; ≤ 0.5 page)

- **Hypothesis** (a priori, from Huys 2012; Otto 2013): if depth captures real bounded foresight, then individual differences in $E[h]$ should correlate with self-reported cognitive traits in trait-predicted directions.

- **Two complementary cuts of the depth construct.** We report router-conditional (state-resolved $p_\phi(h\mid s)$ posthoc) and global-aggregate (Pillar 5 EM E[h] under uniform prior) separately. They are weakly correlated at the participant level ($r_s{=}0.21$, ns) — i.e., they index *different* facets of "depth" — and each contributes a distinct cluster of clinical signals.

### Cut A — Router-conditional metrics (3-router robustness; canonical for §6.3 headline)

> Three main routers used: `sc_categorical` posthoc, `stickbreaking` (already posthoc), `hspace_gaussian` posthoc. All three loaded from per-participant posthoc-quality checkpoints; per-depth policies and shared reward held fixed across routers. **22 metrics × 25 clinical × 3 routers = 1650 correlations** (consistency-tagged: `analysis/results/router_consistency_main3.csv`, 550 unique cells). Metrics include level (`E_h_*`), state-shift (`shift_*`), state-divergence in level-space (`σ_s(E[h\|s])`), state-divergence in distribution-shape space (`flex_kl_*` — pairwise symmetric KL between aggregated `p(h\|zone)`), and time-pressure (`E_h_time_low/high`); clinical groups span main scales, sub-scales, behavioral lab tasks (DDT/CRA), and **in-task gameplay** (jaywalking, NOTHING, success rate).

- **Cross-router consistency audit (headline filter)**: **20 / 550** cells reach all-3-routers significant with sign agreement; **0 / 550** cells reach all-3-sig with sign disagreement; 47 cells partial-sig. Per group: in-task 6/66 robust, behavioral 6/44, sub-scale 7/352, main 1/88 (`flex_kl_max × BIS-total` is the lone main-scale robust cell). Cross-metric per-PID rank-correlation across router pairs is ≥0.86 for all level/shift metrics (entropy alone drops below 0.85 — flagged caveat).

- **Headline robust signals (top 8 by mean |r|)**:

  | Depth Metric | Clinical | Group | sc_cat | stickbreak | hgauss | mean |
  |---|---|---|---:|---:|---:|---:|
  | `shift_road_danger`     | `action_Nothing_ratio_cleansed` | in-task  | +0.415 | +0.512 | +0.467 | **+0.464** |
  | `E_h_time_low`          | `jaywalking_ratio_total`        | in-task  | −0.338 | −0.478 | −0.424 | **−0.413** |
  | `E_h_mean`              | `DDT_mean_log_k`                | behav    | +0.370 | +0.418 | +0.404 | **+0.397** |
  | `E_h_road`              | `S_UPPS_P_premeditation`        | sub      | +0.377 | +0.384 | +0.428 | **+0.396** |
  | `E_h_safe`              | `DDT_mean_log_k`                | behav    | +0.352 | +0.424 | +0.371 | **+0.382** |
  | `E_h_safe`              | `jaywalking_ratio_total`        | in-task  | −0.350 | −0.365 | −0.401 | **−0.372** |
  | `flex_kl_max`           | `jaywalking_ratio_total`        | in-task  | +0.383 | +0.385 | +0.305 | **+0.358** |
  | `flex_kl_mean`          | `DDT_mean_log_k`                | behav    | −0.382 | −0.323 | −0.327 | **−0.344** |
  | **`flex_kl_max`**       | **`BIS`** (total)               | **main** | +0.275 | +0.278 | +0.318 | **+0.290** |

  All p < .01, N=52. Full 20-row table in `EXP_ROUTER_CLINICAL.md` §4.3. Note: `flex_kl_*` correlations with DDT and jaywalking have *opposite signs* to `E_h_*` correlations with the same variables — distribution-shape divergence and depth level index different cognitive cuts.

- **Two independent bridges from depth construct to behavior**:
  - *Cross-domain (lab tasks)*: DDT cluster — `E_h_mean / E_h_safe / E_h_time_high / σ_s(E[h\|s]) × DDT log k`, 4 robust cells, mean r ≈ +0.31 to +0.40.
  - *Within-domain (gameplay)*: NOTHING / jaywalking cluster — 4 robust cells, top |r| = 0.46. The latent depth variable predicts in-task behavior signatures the model was *not* optimized for. Internal cross-validation evidence.

- **State-adaptive metrics carry their share of the signal**: 6 of the 15 robust cells are state-shift / state-divergence metrics (`shift_road_danger × NOTHING` +0.46; `E_h_time_low × jaywalking` −0.41; `shift_safe_danger / shift_safe_road × BIS_motor` +0.34, +0.32; `shift_road_danger × premeditation` +0.32; `state_h_sigma × DDT log k` +0.31) — by construction unavailable to a uniform-horizon baseline; directly supports **C3** state-conditional architecture.

- **State-adaptation × BIS Motor robust 3/3** (`shift_safe_danger × BIS_motor`: cat +0.375, stick +0.283, hgauss +0.362, mean **+0.340**); replicated under broader road zoning (`shift_safe_road × BIS_motor` mean +0.323). Trait-level convergence: same shift × BIS-total partial-sig 2/3 (mean +0.29, consistent direction in 3/3) — motor facet drives the trait-level signal.

- **Premeditation cluster (5 robust cells)** — `E[h\|road] / E[h\|road_clear] / E[h] mean / E[h\|goal] × UPPS-P premeditation` and `shift_road_danger × premeditation` all flag together (mean r ≈ +0.32 to +0.40). UPPS-P "lack of premeditation" is the facet most directly (almost tautologically) tied to planning depth; we report this as face-validity rather than deep-construct discovery.

- **Time-pressure metric (Huys 2012; Callaway 2022 textbook lever) — mixed**: `E_h_time_low × jaywalking` robust (r=−0.41); `E_h_time_high × DDT log k` robust (+0.35); but `shift_time_press` itself does not robustly correlate with any clinical variable — the *delta* between pressed and relaxed states is too noisy at N=52 because most participants spend few states in the time-pressed regime. Level under time pressure is informative; the differential is not.

- **Reported as null (honest) + figure provenance audit**: STAI-total / CES_D-total / most DOSPERT cells are uniformly non-significant across all 3 routers. **The legacy paper figure `sc_depth_flexibility_clinical.png`** (caption: "Depth Flexibility Correlates with Anxiety and Risk Attitudes (N=52)"; STAI_S × Depth Flexibility r=−0.324 p=.019\*; DOSPERT_FIN × Depth Flexibility r=−0.320 p=.021\*; generator `scripts/generate_sc_clinical_paper_figures.py`, 2026-03-26) **does not reproduce at canonical N=52**: re-running the same correlation against the same `merged_participant_data_with_sc.csv` column the figure script reads, with the canonical post-2026-04-28 outlier set, yields pearson r=−0.149 p=.293 / spearman r=−0.119 p=.402 for STAI_S and pearson r=+0.058 p=.681 / spearman r=−0.176 p=.212 for DOSPERT_FIN — magnitudes ~half of the figure's claim and not significant. The v4 distribution-shape KL family (`flex_kl_mean / max / safe_danger`, our 3-router-robust analog) also fails to recover STAI/DOSPERT_FIN signals (max |r| across STAI = 0.28 stickbreaking-only partial-sig; max |r| across DOSPERT_FIN = 0.26 all_ns). **Figure should be regenerated from current data or removed before submission.** Full audit: `EXP_ROUTER_CLINICAL.md` §4.7.

### Cut B — Global-aggregate Pillar 5 EM E[h] (state-independent, uniform-prior)

> Anchor: `merged_participant_data.csv["E[h]"]` with `e_h_source = pillar_5_em_weights` — global EM mixture weights on $\mathcal{H}$ given uniform per-step prior. State-INdependent. Distinct from router output ($r_s{=}0.21$ between the two anchors at PID level, ns).

- **UPPS-P facets (strong)**: Sensation Seeking $r_s{=}+0.481$ (p<.001), Positive Urgency $+0.486$ (p<.001), UPPS Total $+0.453$ (p<.001), Premeditation $+0.429$ (p=.0015). N=52.
- These signals do *not* live in the router posthoc output (where the same UPPS facets reach only $r_s \in [0.23, 0.29]$, partial-sig at best). They live in the global EM-weighted aggregate, which captures whole-task discounting tendency rather than state-conditional planning.
- Reporting decision: **keep both cuts**. The global EM cut answers "does the whole-task aggregate depth align with self-reported impulsivity?"; the router-conditional cut answers "does the *state-resolved* router output align, and is this alignment robust to router family?". Different mechanistic claims; both true.

- **What we do NOT claim**: diagnostic utility, individual-level screening, clinical decision support. Population-level mechanism validation only (Binz 2022 §4.1 template).

> ✅ **Resolved 2026-04-30**: original v1.1 "BIS r=−0.38, CRA r=−0.44" not reproducible at canonical N=52; replaced by router-conditional 3-robust-signal table (Cut A) + Pillar 5 EM UPPS-P cluster (Cut B). Full audit: `docs/paper_related/EXP_ROUTER_CLINICAL.md`. UPPS-P numbers re-attributed from "SC Categorical only" (v1.1) to "Pillar 5 EM E[h] (router-independent global aggregate)" — same numbers, correct provenance.

## 6.4 Robustness under Covariate Shift (Supplementary Analysis)
> **Research question (supplementary)**: does the bounded-foresight imitation extrapolate coherently to amplified-stake environments outside the training distribution, at the level of *behavioral* trajectory metrics? (setup + heavy details → Appendix L)
>
> *Posthoc-router architectural disclosure (paper-framing)*: OOD evaluation throughout §6.4 / Appendix L uses a post-training-refit categorical router fitted on baseline expert under frozen per-h policies (objective identical to the in-training router loss `L_router(φ) = −E_{π_E}[log π_mix(a|s)]`). What is tested is the *architectural gating object*, not the trained router weights; trained-router OOD generalization is deferred to future work. The same posthoc checkpoint is reused across all OOD conditions per PID — cross-condition agreement is therefore deterministic recomputation under different env interventions, not statistical replication.

- **Graded caution under stake amplification (population mean, N=52)**: at multiplier ×5 / ×10 (`obs[14]` scaled outside trained [0,1] range), the policy responds with monotone increases in episode length, NOTHING-fraction, crosswalk usage, and router depth — qualitatively human-like prudence rather than collapse. Boundary at ~×10; ×100 enters policy-collapse regime (state-norm distortion + partial compound rollout dynamics; full failure-mode analysis in Appendix L.3, briefly noted in §7.2 Limitations).
- **Per-attempt collision decomposition (NEW; from `experiments/ood/multsweep_2026-04-26_*/per_attempt_table.csv`)**: separates two decisions — *abort* (NOTHING-stack → timeout) and *commit* (per-attempt collision = collision / (success + collision)). Abort rate scales gracefully with stakes (0.00 → 0.21 at ×5 → 0.48 at ×10 → 0.77 at ×100), while *commit-conditional* collision spikes (0.38 → 0.57 at ×5 → 0.88 at ×10 → 0.99 at ×100). Two-stage decision separation: the bounded-foresight policy's risk recognition (NOTHING-abort) is preserved under OOD, but the commit-stage car-avoidance degrades — clarifying the headline collision-rate increase as *commit-stage misalignment* rather than abort-stage failure.
- **Dynamic clinical OOD**: not reported in §6 main body — would double-count against §6.3 static cuts (which already report DOSPERT/STAI/CES_D as null and BIS Motor / DDT log(k) / UPPS-P as significant convergent validity). The trait × stakes-sensitivity scan is reported as *exploratory only* in **Appendix L.2** (162 × 2 sweep cells, BH-FDR q=.10 over the full 324-cell family yields 0 survivors; previous "Bonferroni-passing replicated leads" claim retracted 2026-04-30 — both sweeps share the same frozen posthoc-refit router and seed-1 setup, so cross-sweep agreement is deterministic recomputation, not statistical replication).
- **Interpretation**: behavioral graded caution is consistent with *some* extrapolation beyond the trained input range, but the per-attempt decomposition shows commit-stage misalignment grows non-linearly with stakes. We do not claim that the architectural gating object provides *clinical* convergent validity in OOD beyond what §6.3 already reports for the in-distribution behavior.
- *Multiplier curve, per-attempt table, exploratory clinical leads with BH-FDR honest disclosure, and ×100 collapse diagnostics → Appendix L.*

## 6.5 Ablations
- **2×2 router grid (per §4.6)**: Categorical / Gaussian / LogGaussian × no-loop / loop. Categorical and LogGaussian match on imitation; Gaussian (fixed σ) loses 6× expressivity (entropy CV 2.4% vs 14.2%) — *unimodal-shape prior is too restrictive*.
- **Component ablation**: no truncation (=Std AIRL) / no router (=Single-h) / no multi-policy → isolates which structural replacement drives which metric.
- **Sensitivity to $\mathcal{H}$**: $\{3,5\}$ vs $\{2,3,5,10\}$ vs $\{2,5,10,20\}$ — Appendix.

---

# 7. Discussion, Limitations, Broader Impact (0.5 page)

## 7.1 Discussion
- Why shared reward + heterogeneous depth is a *structural* assumption about humans, not a modeling convenience
- Connection to hierarchical RL and bounded rationality literatures
- Implications for interpretable AV perception and personalized decision support

## 7.2 Limitations
- Single task domain (pedestrian crossing only); multi-task generalization deferred
- Categorical depth grid (4 values); continuous depth remains open
- Router is trained end-to-end with discriminator → sensitive to D_mix quality early in training
- Clinical correlations are population-level, not diagnostic-grade; mechanism validation only
- Assumes depth is state-dependent but not history-dependent; longer-horizon temporal router is future work
- **In-distribution generalization (held-out map seeds)**: full pre-registered evaluation pipeline (Appendix J.5: stratified 8/40 holdout, T1–T4 acceptance criteria, retrained models on held-out-excluded splits) is in place; Table 1b values are placeholders pending the ~5h × 3-server retraining execution. The supplementary OOD stake-amplification analysis (§6.4, Appendix L) provides the *complementary* generalization axis (out-of-distribution along the stakes dimension) and is reported with completed data; ×100 collapse boundary is a known IRL+state-norm failure mode and not specific to bounded-foresight architecture (Appendix L.3).

## 7.3 Broader impact
- Positive: interpretable driver/pedestrian models → safer AV systems; individual-profile screening for cognitive decision support
- Risk: depth inference could be misused for surveillance or actuarial scoring — we do not release per-participant depth profiles, and we framed depth as a population-level mechanism, not an individual biomarker

---

# 8. References (placeholder)

**ML / IRL methodology**:
- Ng & Russell 2000 (Algorithms for IRL — foundational)
- Ziebart 2008 (MaxEnt IRL)
- Fu et al. 2018 (AIRL)
- Ho & Ermon 2016 (GAIL)
- Ng et al. 1999 (potential-based shaping)
- Schulman et al. 2016 (GAE)

**IRL with planning horizon / heterogeneity**:
- Yao et al. 2024 (NeurIPS 2024) — multi-horizon IRL via $\gamma_i$
- Barnes et al. 2023 RHIP (Google Maps)
- Cao et al. 2021 (reward–horizon non-identifiability)
- Schultheis et al. 2022 (non-exponential discounting)
- Tian et al. 2021 (latent intelligence level)
- Li et al. 2023 DCPPO; Mazumdar et al. 2024 (bounded-rationality theory)

**Mixed/hierarchical/heterogeneous-demonstrator IL**:
- Chen et al. 2023 MH-AIRL
- Seo & Unhelkar 2024 IDIL; 2025 DTIL
- Beliaev & Pedarsani 2024 IRLEED
- Chen et al. 2025 Meta-IRL-MFG (PEMMFIRL)
- Blessing et al. 2023 IMC
- Reuss et al. 2024 MoDE
- Wang et al. 2024 MoE-AR-IL
- Qiao et al. 2023 MMICRL

**Real-time IRL on cognitive-psychology data (precedent)**:
- **Lee, Song, Oh, & Ahn (2024)** *Psychological Science*, DOI: 10.1177/09567976241228503 — deep AIRL on real-time driving; closest cog-psych-grade IRL precedent
- Binz & Schulz 2022 (NeurIPS 2022) — resource-rational RL; Iowa Gambling Task vmPFC re-analysis

**Cognitive science of planning depth / bounded rationality**:
- Simon 1955 ("A Behavioral Model of Rational Choice"); Simon 1991
- Russell 1997 ("Rationality and intelligence")
- Lieder & Griffiths 2020 (resource-rational analysis)
- Daw 2011 (model-based vs model-free RL)
- Cowan 2001 (working-memory $4{\pm}1$); Miller 1956 ($7{\pm}2$)
- van Opheusden et al. 2023 *Nature* (planning depth in human gameplay)
- Callaway et al. 2022 *Nat. Hum. Behav.* (rational resource allocation)
- Huys et al. 2012; Otto et al. 2013 (state-dependent pruning)
- Keramati et al. 2016 *PNAS*
- Griffiths et al. 2015
- Laidlaw et al. 2022 (Boltzmann-rational policy distance / BPD)

**Domain (non-IRL pedestrian/driving baselines, scoping reference)**:
- Helbing & Molnár 1995 (social force model — out-of-scope baseline; cited in §5.2 scoping paragraph)

---

# 9. Appendix

> **NeurIPS convention**: Appendix length is unlimited. Defer all non-essential derivations, implementation details, and extended results here so main body fits in 9 pages. NeurIPS 2026 requires sections F (compute) and K (checklist) explicitly.

## 9.0 Main vs Appendix Scoping Table

| Content | Main | Appendix § | Rationale |
|---|---|---|---|
| Theorem 1, Proposition 1 statements | — (moved v1.2) | **A** | Prior works do not include in main; role was vague |
| Proof sketches (1 paragraph) | — (moved v1.2) | **A** | Co-located with full proofs |
| **Full proofs** | — | **A** | ~2 pages of derivation |
| Method equations (Eq. 1–19 from THEORY §0) | ✓ (§4) | — | Core contribution |
| Telescoping derivation | — | A | Space |
| Algorithm 1 (training pseudocode) | — (moved v1.2) | **A.6** | Page-budget; main-body §4.6 reduced to 1-line pointer |
| **Full pseudocode with warmup/loop/EM** | — | **C** | Implementation-level detail (deeper than A.6) |
| Architecture overview (1 sentence) | ✓ (§4.2) | B | Reader intuition |
| **Full hyperparameter table** | — | **B** | NeurIPS reproducibility |
| Main results Table 1, Figs 1–3 | ✓ (§6.1–6.3) | — | Primary claim |
| 2–3 headline ablations | ✓ (§6.5) | — | Support main claim |
| **Full ablation grid** (H, router, λ_ent, warmup, V_tail) | — | **D** | Completeness |
| Mechanism validation (0.5 pg, N=52) | ✓ (§6.3) | I (full tables) | Binz 2022 template |
| Per-participant depth profiles | — | I | Scale |
| **OOD stake-amplification (behavioral graded-caution + per-attempt decomposition + multiplier curve)** | ✓ (§6.4 supplementary) | **L** | Use-Inspired domain-fusion + robustness; clinical OOD → exploratory only in L.2 (BH-FDR q=.10 = 0 survivors) |
| OOD exploratory leads (16 acw-only, FDR-controlled) | — | L.2 | Exploratory; not main-body |
| **OOD ×100 collapse — failure-mode diagnostics** | brief note (§7.2) | **L.3** | Honesty signal; State-norm + compound dynamics |
| **Train-test split — pre-registered T1–T4** | ✓ (§6.1 Table 1b placeholder) | **J.5** | Reproducibility commitment; results pending execution |
| **V_tail = 0 / Φ = 0 justification** | 1 sentence (§4.2) | D.7, D.8 | Technical depth |
| **Normalize-then-shape invariance** | — | D.8 | Technical subtlety |
| Entropy reg detail (per-depth $D_h$) | — | B | Implementation nuance |
| Baseline adaptation details | — | G | Per-baseline specifics |
| Dataset overview (1 paragraph) | ✓ (§5.1) | E | Context |
| Dataset preprocessing, splits, clinical exclusions | — | E | Reproducibility |
| **Compute cost statement** | — | **F** | **NeurIPS checklist — required** |
| **Reproducibility statement** | — | **J** | **NeurIPS — required** |
| **Broader impact (extended)** | 1 paragraph (§7.3) | H | Depth on misuse risk |
| **NeurIPS paper checklist** | — | **K** | **Required at end** |

---

## 9.A Theoretical Analysis (moved from main-body §5 in v1.2)

> **Self-contained presentation**. With the v1.2 restructure, the main body no longer has a §5 *Theoretical Analysis*. Both proposition *statements* and *proofs* now live here. Cross-references in the main body (§4.2 telescoping identity; §6.3 reward identifiability anchor) point to this section.

### A.0 Two formal questions raised by (A1) + (A3)
1. (Q1) Is $h$-step truncation a genuinely new horizon-control axis or just a discount rescaling? (→ **Proposition 1**)
2. (Q2) Does GAE-$h$'s per-step TD bootstrap silently re-introduce an infinite-horizon tail at the truncation cutoff, undoing (A1)? (→ **Proposition 2**)

Both answered in the negative.

### A.1 Proposition 1 — Bounded-support weighting ≠ discount-rescaling
- **Statement.** $\sum_{k=0}^{h-1}\gamma^k r_\theta(s_{t+k},a_{t+k}) = \sum_{k=0}^{\infty}\gamma^k\,\mathbb{1}[k<h]\,r_\theta(s_{t+k},a_{t+k})$. The temporal weighting has bounded support $\{0,\dots,h-1\}$. No geometric discount $\gamma'\in(0,1)$ reproduces this weighting since $\gamma'^k > 0$ for every $k\ge 0$.
- **Proof.** Identity follows from splitting the geometric series at $k=h$; indicator weighting has bounded support $\{0,\dots,h-1\}$. For any $\gamma'\in(0,1)$, $\gamma'^k > 0$ for all $k\ge 0$ → no $\gamma'$ matches the identically-zero weighting at $k\ge h$. Hence $h$-step truncation is *not equivalent* to any geometric-discount rescaling. ∎
- **Implication.** Separates SC-AIRL from any single-$\gamma$ rescaling, per-agent $\gamma_i$ (Yao 2024), non-stationary $\gamma_k$, or hyperbolic schedules — all of which retain infinite-lookahead value computation and only re-weight summands.

### A.2 Proposition 2 — GAE-$h$ with $V_\text{tail}\equiv 0$ has no infinite-horizon residue
- **Setup.** $\hat A_t^{(h)} = \sum_{k=0}^{h-1}(\gamma\lambda)^k \delta_{t+k}^{(h)}$ with $\delta_t^{(h)} = r_\theta(s_t,a_t) + \gamma V^h(s_{t+1}) - V^h(s_t)$, under architectural commitment $V^h(s_{t+h})\equiv 0$ at the truncation boundary.
- **Statement.** At $\lambda=1$: $\hat A_t^{(h)} = G_t^{(h)} - V^h(s_t) = A_t^{(h)}$. For any $\lambda\in[0,1]$, the estimator depends on the trajectory only through $\{s_t,\dots,s_{t+h}\}$ — *no residual boundary term* $\gamma^h V^h(s_{t+h})$ enters the advantage.
- **Proof.** Telescoping at $\lambda=1$: $\sum_{k=0}^{h-1}\gamma^k\,\delta_{t+k}^{(h)} = \sum_{k=0}^{h-1}\gamma^k r_\theta(s_{t+k},a_{t+k}) + \gamma^h V^h(s_{t+h}) - V^h(s_t)$. Boundary term vanishes under $V^h(s_{t+h})\equiv 0$, leaving $G_t^{(h)} - V^h(s_t) = A_t^{(h)}$. For $\lambda\in[0,1]$, $\hat A_t^{(h)}$ is a convex combination of $k$-step advantages for $k\in\{1,\dots,h\}$, each depending only on $\{s_t,\dots,s_{t+h}\}$; dependence on any $s_{t+k}$ with $k>h$ enters only through $V^h(s_{t+h})\equiv 0$ → contributes zero. ∎
- **Implication.** SC-AIRL's only bootstrap channel is GAE-$h$'s per-step TD, not a boundary value at the cutoff. Licenses standard PPO as the inner-loop optimizer for each $\pi^h$ without inheriting infinite-horizon credit assignment.

### A.2.5 Remark — Consistency with AIRL identification
- Under (A3) and $\Phi\equiv 0$, $D_\text{mix}$ identifies $r_\theta$ up to the standard shaping+constant equivalence class (Ng 1999). Each per-depth planner satisfies the MaxEnt optimality $\pi^{\star,h}\propto\exp Q^{\star,h}$ with the $h$-step truncated $Q^{\star,h}$ (Ziebart 2008; Fu 2018). Depth heterogeneity is absorbed by $\{\pi^h\}$ rather than $r_\theta$ → SC-AIRL is a regular instance of mixed-policy AIRL whose horizon structure is *physical* ($h$-step truncation), not discount-based. **Empirical anchor**: cross-correlation $r{=}0.784\pm 0.043$ between SC-AIRL and Std AIRL reward functions (§6.3).

### A.3 Telescoping identity (used in §4.2)
- $\sum_{k=0}^{h-1}\gamma^k[f_\theta - r_\theta] = \gamma^h\Phi(s_{t+h}) - \Phi(s_t)$ by collapsing consecutive potential differences.
- Justifies the $\Phi\equiv 0$ commitment: any non-trivial shaping leaves a boundary term $\gamma^h\Phi(s_{t+h})$ at the truncation cutoff, acting as an implicit infinite-horizon bootstrap and undoing (A1).

### A.4 Router objective equivalence
- Mixture NLL $\mathcal{L}_\text{router}(\phi) = -\mathbb{E}_{\pi_E}[\log\sum_h p_\phi(h|s)\pi^h(a|s)]$ is equivalent up to constant to $\mathbb{E}[\text{KL}(q(h|s,a)\,\|\,p_\phi(h|s))]$ where $q(h|s,a)\propto p_\phi(h|s)\,\pi^h(a|s)$.

### A.5 Router consistency (optional)
- Under identifiable per-depth $\pi^h$, mixture-NLL has a unique maximizer equal to the true depth distribution. Mild regularity assumptions stated.

### A.6 Algorithm 1 — Training pseudocode (moved from main-body §4.6 in v1.2 for page-budget reasons)

**Inputs**: expert dataset $\mathcal{D}_E$, depth grid $\mathcal{H}=\{2,3,5,10\}$, total rounds $T$, warmup $T_\text{warm}=10{,}000$, router update interval $\Delta_\text{router}=10$.

**Outputs**: per-depth actors $\{\pi^h_{\omega_h}\}$ and critics $\{V^h_{\xi_h}\}$, shared reward $r_\theta$, router $p_\phi(h|s)$.

**Per-round structure (4 steps)**:
1. **Rollout**: collect on-policy trajectories $\tau^h_t$ from each $\pi^h_{\omega_h}$.
2. **Discriminator update**: update $\theta$ on the mixed-policy AIRL objective (Eq. 9), generator density $\pi_\text{mix}$ assembled from current $\{\pi^h\}$ and $p_\phi$.
3. **Reward recompute**: compute learned rewards $r_\theta(s,a)$ on each $\tau^h_t$.
4. **PPO update**: update each $(\omega_h, \xi_h)$ with standard PPO on $A_t^{(h)}$ (Eq. 6).

**Router update schedule (EM-style)**:
- **Warmup ($t < T_\text{warm}$)**: $p_\phi(h|s) = 1/|\mathcal{H}|$ frozen uniform; router not updated.
- **Main phase ($t \ge T_\text{warm}$)**: every $\Delta_\text{router}=10$ rounds, gradient steps on Eq. 12 (mixture NLL); $\{\pi^h\}$ frozen during router update; router never sees discriminator gradient directly.

**Auxiliary**: 
- State-normalization statistics frozen *within* a round (updated only at round boundary) — steps 2–4 operate on identical normalization.
- EMA log-prior update (`_em_log_prior`) with momentum 0.9 for stability.
- Checkpoint and evaluation hooks per `experiments/configs/router_full_51p.json`.

Detailed implementation, hyperparameter table, and code-level pseudocode → §9.B (Implementation Details) and §9.C (Full Pseudocode).

---

## 9.B Implementation Details

### B.1 Network architectures
- Policy $\pi^h$: 2-layer MLP, hidden [256, 256], LeakyReLU, softmax over |A|=5
- Value $V^h$: 2-layer MLP, hidden [256, 256], scalar output
- Reward $r_\theta$: 2-layer MLP on concat($s$, one-hot $a$)
- Potential $\Phi$: 2-layer MLP, hidden 128 (default: **disabled**, $\Phi \equiv 0$)
- Router $p_\phi(h|s)$: 2-layer MLP, hidden 64, dropout 0.1
- Per-participant variant: hidden [8, 8] (~1K total params) — achieves MAP 87.2%

### B.2 Full hyperparameter table
See THEORY §7.3; reproduced here as Table.

### B.3 Training schedule
- **Total rounds**: `n_rounds = 20000` (production config `experiments/configs/router_full_51p.json`)
- **Warmup phase**: `em_warmup = 10000` rounds (50% of training), uniform $p(h|s) = 1/|\mathcal{H}|$; router frozen
  - *Rationale*: empirical stability analysis of 47 completed `sc_categorical` runs (see `experiments/results/figures/sc_categorical_stability_{vs_round,summary}.png`) shows per-h policies and entropy signals continue drifting through ~10k rounds; the discriminator must not trust a router prior until the per-h policies have settled
- **Main (loop) phase**: rounds 10000–20000, alternating D_mix / PPO / router updates with `em_update_interval = 10` (~1000 router updates total)
  - *Rationale*: standard AIRL / DAC / EM-IRL convention — one discriminator (E-step posterior) update per ~10 generator-side PPO iterations so the router sees a near-stationary policy inside each EM window
- **Other EM settings**: `em_momentum = 0.9`, `em_temperature = 1.0`
- **PPO**: 4 epochs × 256 batch size per round
- Cross-ref: §4.4 (D_mix warmup/loop), Phase 2 finalization in `EXP_router_baselines_EXECUTION.md`

### B.4 Entropy regularization — implementation detail
- Uses per-depth $D_h$ (not $D_\text{mix}$) for gradient flow to $f_\theta$
- Detached $\pi^h$ in posterior $q$ to correct inverse-policy bias
- $\lambda_\text{ent} = 0.01$ (near-max entropy observed; does not harm MAP recovery)

### B.5 State representation (113-dim)
- Ego: position (2), velocity (2), heading (1) = 5
- Task context: goal direction (2), time remaining (1) = 3
- Surrounding vehicles (4 vehicles × 25 features): rel pos, vel, size, presence = 100
- Scene: lane structure (5)
- Normalized via RunningNorm initialized from expert data (momentum 0.999)

---

## 9.C Algorithm 1 — Full Pseudocode
Complete boxed pseudocode including:
- Warmup phase loop
- Main phase alternating updates (D_mix, PPO-per-h, router E-step)
- EMA log-prior update (`_em_log_prior`)
- State/reward/return normalization calls
- Checkpoint / evaluation hooks

Main body §4.7 shows abbreviated version (inputs, outputs, 10-line sketch).

---

## 9.D Extended Ablations

### D.1 H grid sensitivity
- $\mathcal{H} \in \{\{3,5\}, \{2,3,5,10\}, \{2,5,10,20\}\}$
- Metrics: MAP accuracy, success rate, action KL

### D.2 Router variants
- **Categorical softmax** (default) — no shape prior on $h$ distribution.
- **Gaussian kernel** (ablation) — unimodal prior over depth index, $\mu_\phi(s)\in[0,|\mathcal{H}|-1]$ scalar output.
- **No router** (uniform $1/|\mathcal{H}|$ baseline).
- *Deprecated*: truncated Poisson — replaced by Gaussian kernel for simpler scalar parameterization at the same unimodal commitment.

### D.3 Router training objective
- Mixture NLL (Eq. 16, default)
- KL distillation (Eq. 18)
- Joint (NLL + KL)

### D.4 Loop update schedule
- Non-loop (single shot router after convergence)
- Loop with EMA momentum $\alpha \in \{0.9, 0.99, 0.999\}$

### D.5 Warmup length
- `em_warmup` $\in \{0, 2500, 5000, 10000, 15000\}$ (fractions of `n_rounds=20000`)
- Production choice `10000` justified by document-based stability analysis (Appendix B.3); ablation confirms degradation at shorter warmups

### D.6 Entropy regularization weight
- $\lambda_\text{ent} \in \{0, 0.01, 0.1, 1.0\}$

### D.7 V_tail ablation — why Φ = 0 is optimal
- `v_tail_mode` $\in$ {none, phi_only, tail_only, full}
- Shows phi_only double-counting pathology (Φ already in $f_\theta$)
- Demonstrates Φ=0 + GAE-h implicit bootstrap is sufficient
- MAP accuracy: none=87.2%, phi_only=48.5%, others untested

### D.8 Normalize-then-shape pipeline order
- norm(r_θ) + shaping (current) vs norm(r_θ + shaping) (alternative)
- Analytically: alternative breaks telescoping (nonlinear norm traps shaping)
- Empirically: alternative degrades MAP by ~20%

### D.9 Per-participant vs pooled training
- N=56 separate models (default, stronger identifiability)
- Single pooled model with participant embedding
- Trade-off analysis

### D.10 Reward stability under random depth permutations
- Reward correlation under shuffled h labels
- Supports identifiability claim (§5.1)

---

## 9.E Dataset Details

### E.1 Pedestrian crossing task
- Participants: 56 (P902–P1054, excluding P1016)
- Trials per participant: ~282
- Average transitions per participant: ~9,300
- Decision steps per episode: 30–50
- Action space: {NOTHING, LEFT, RIGHT, ACCEL, BRAKE} (5 actions)

### E.2 State preprocessing
- RunningNorm with expert-initialized statistics
- Momentum α = 0.999, applied consistently in rollout + PPO update (Phase 5b fix)

### E.3 Train/val/test splits
- Per-participant: 80/10/10 trial-level
- Participant holdout: leave-one-out for generalization ablation

### E.4 Clinical measures (N = 51)
- BIS-11 (Barratt Impulsiveness Scale)
- CRA (Choice under Risk and Ambiguity)
- 6 participants excluded: P902, P903, P1010, P1016, P1022, P1051 (no clinical records)

### E.5 Data release statement
- Anonymized trajectories: release commitment on acceptance
- Raw video / identifying data: not released (IRB constraint)

---

## 9.F Compute Resources (NeurIPS Required)

| Item | Value |
|---|---|
| Hardware | Single NVIDIA RTX 3090 (24GB) |
| Per-participant training | ~3 GPU-hours (500 rounds, [8,8] net) |
| Full pooled training | ~36 GPU-hours (1000 rounds, [256,256,256] net) |
| Total experiments (N=56 + 4 baselines + ablations) | ~200 GPU-hours |
| Peak memory | <8GB per run |
| Total experimentation (incl. failed runs) | ~500 GPU-hours |

---

## 9.G Baseline Adaptation Details

### G.1 M1 Standard AIRL
- Single h=5 infinite-horizon policy, same reward/value architecture
- Delegates to `run_training_55participants.py` with h_list=[5]

### G.2 M2 Behavioral Cloning
- Cross-entropy supervised on expert (s, a)
- Same policy architecture, shared state normalization

### G.3 M3 Single-h Control
- SC-AIRL with fixed single h ∈ {2, 3, 5, 10}
- No router, no marginalization
- Control: isolates h choice from learning dynamics

### G.4 M6 GAIL
- Sigmoid discriminator D(s, a)
- Reward = −log(1 − D), no reward network, no shaping
- PPO generator updates

### G.5 Yao 2024 adaptation
- Tabular formulation extended to continuous via MLP
- Per-agent discount $\gamma_h$ as alternative to h-step truncation
- Shows equivalence-region boundary in deep setting

---

## 9.H PPO Diagnostics & Failure Modes

- PPO health criteria: clip_fraction < 0.15, approx_KL < 0.02, entropy(h=10) > 0.4
- State normalization bug (Phase 5b): inconsistent norm between rollout and update → ρ_t ≠ 1 → LEFT action 45.5%, success 0%
- Reward normalization clip(-10, 10): hard nonlinearity broke shaping invariance → MAP ~50%
- V_tail phi_only double-counting: MAP 48.5% vs 87.2% after removal

---

## 9.I Mechanism Validation — Extended

### I.1 BIS subscales
- Motor, Attention, Non-planning subscales separately
- Cognitive vs motor impulsivity differentiation

### I.2 CRA subscores
- Risk aversion α, ambiguity aversion β

### I.3 Per-participant depth profiles
- Histograms of $\mathbb{E}[h \mid \text{participant}]$
- Within-participant vs between-participant variance decomposition

### I.4 Correlation robustness
- Outlier removal sensitivity
- Bootstrap confidence intervals for r values
- Mean-depth vs state-conditional depth variance as independent predictors

### I.5 (moved to §9.L)
*OOD-related details previously drafted as §9.I.5 are now consolidated in §9.L "OOD Stake-Amplification: Curve, Replicated/Exploratory Leads, and Failure Modes" (referenced from §6.4 and §7.2 Limitations).*

---

## 9.J Reproducibility Statement (NeurIPS Required)

- **Code**: github.com/... (anonymized during review; public on acceptance)
- **Seeds**: Main results averaged over 3 seeds; per-participant runs = 1 seed (matched across methods)
- **Checkpoints**: Released upon acceptance
- **Configs**: All config files (`config/`, `experiments/configs/`) in repository
- **Environment**: Python 3.10, PyTorch 2.1, deterministic mode where feasible
- **Data**: Anonymized trajectories + clinical scores released; no identifying metadata

### J.5 Train-Test Split — Pre-Registered Evaluation Plan (referenced from §6.1, §7.2)

**Status (2026-04-28)**: Plan finalized and code-validated; 53-pid retraining pending user-approved server execution. Results in Table 1b are **placeholders** until execution complete. Reported as pre-registered to (i) demonstrate reproducibility commitment per NeurIPS guidelines, (ii) commit acceptance criteria *before* observing results.

**Holdout selection — stratified, not random**:
- 53 participants × 40 *common* map-seeds (seeds shared across all 53 PIDs).
- Pre-registered test seeds (8/40, stratified by expert success-rate quartile + ep-length match): `[1008, 1009, 1019, 1020, 1025, 1028, 1030, 1035]`. Selection script: `experiments/train_test/profile_common_seeds.py`. 
- Stratification verification: 4 expert-feature distributions (success_rate, ep_length, NOTHING_frac, L/R_frac) all show std-normalized train/test gap < 0.3 (vs random shuffle which gave WARN > 0.39 on NOTHING_frac and L/R_frac). Test seeds match the population distribution rather than randomly subsampling it.

**Pre-registered acceptance criteria (T1–T4)**:
| ID | Hypothesis | Threshold | Aggregation |
|---|---|---|---|
| **T1** | Imitation fidelity preserved | held-out action LL ≥ 90 % of train action LL (gap < 10 %) | Population mean (53 PIDs) |
| **T2** | Router generalizes | KL between $E[h\|s]$ distributions on held-out vs train states < 0.05 | Per-PID |
| **T3** | Crosswalk usage consistent | $\|\text{frac\_on\_cw}_\text{test} - \text{frac\_on\_cw}_\text{train}\| < 5\,\text{pp}$ | Population mean |
| **T4** | SC-AIRL > Single-h baseline on held-out | SC-AIRL held-out action LL > Single-h (B4, h=5) per-PID | Per-PID paired |

**Implementation status**:
- Loader patch (`lib/data/loader.py`: `holdout_seeds`, `holdout_mode='exclude'|'only'`): ✅ implemented + unit-tested (`test_loader_patch.py` all assertions pass).
- Training launcher (`run_training_55participants.py`: `--holdout_seeds_file` flag + `split_meta.json` sidecar + idempotent resume): ✅ implemented.
- Multi-server launcher (`launch_split_training.sh`: 3 servers × 18/18/17 PID slicing, dry-run validated): ✅ ready.
- P1000 single-PID dry-run: ✅ 232 expert trajectories (116 × 2 mirror), `final.pt` saved, `split_meta.json` correctly written.
- 53-PID retraining: ⏸ pending user-approved execution (~5h × 3-server parallel).

**Output layout (post-execution)**:
```
experiments/train_test/results/split_v1/
├── checkpoints/per_p{pid}_split_v1/checkpoints/final.pt
├── logs/per_p{pid}_split_v1/config.json + split_meta.json
├── eval/per_p{pid}_eval.json
└── summary.md
```

**Source**: `experiments/train_test/PLAN_TRAIN_TEST.md`, `experiments/train_test/seed_split.json`.

---

## 9.L OOD Stake-Amplification: Curve, Replicated/Exploratory Leads, and Failure Modes (referenced from §6.4, §7.2)

> Promoted from §9.I.5 (v1.2 evening 2026-04-28). Consolidates main-body §6.4 supplementary OOD evidence with multiplier-curve diagnostics and ×100 collapse failure-mode analysis. Source: `experiments/ood/ANALYSIS_OOD.md`, `experiments/ood/multsweep_2026-04-26_*/`, `experiments/ood/leads_cross_check.md`, `experiments/ood/diagnostics/c1_state_norm/`, `experiments/ood/diagnostics/c5_compound/`.

### L.1 Multiplier Curve and Graded Caution (×1 → ×100)

**Setup.** Reward-magnitude covariate shift via `obs[14]` scaling (penalty observation channel) at multipliers $\{1, 2, 5, 10, 100\}$, all-RED road condition; 52 PIDs × 5 multipliers × 30 episodes (260 paired smokes per sweep). Two sweep variants: no-acw (default crosswalk distribution) and acw (`CrossWalk.RATIO=1.0`).

**Effect curve (52-PID mean Δ, no-acw sweep)**:

| mult | Δ success | Δ collision | Δ ep_length | Δ NOTHING | Δ E[h] | Δ P(on_cw\|vis) |
|---|---|---|---|---|---|---|
| ×1.0 (control) | −0.01 | +0.01 | +0.9 | 0.00 | −0.07 | +0.02 |
| ×2.0 | −0.01 | +0.01 | +4.5 | +0.01 | +0.01 | +0.03 |
| ×5.0 | −0.28 | +0.07 | +24 | +0.07 | **+0.13** | +0.11 |
| ×10.0 | −0.52 | +0.04 | **+44** | +0.07 | **+0.23** | +0.11 |
| ×100.0 | −0.59 | −0.18 | +53 | **−0.19** | +0.31 | **−0.23** |

**Three-regime decomposition**:
- **Control (×1)**: identity — design check ✓
- **Graded caution (×2–×10)**: ep_length, crosswalk usage, NOTHING-fraction, router depth all monotonically increase with stakes — qualitatively human-like prudence under amplified risk
- **Policy collapse (×100)**: NOTHING-fraction, crosswalk usage, $E[h]$ all *reverse* sign; outside model's extrapolation envelope (~×10)

**Visualization**: `experiments/ood/multsweep_2026-04-26_22-00-43/curve.png` (6-panel: success / collision / ep_length / NOTHING / $E[h]$ / P(on_cw|vis) vs multiplier).

### L.2 Exploratory Trait × Stakes Leads — BH-FDR Honest Disclosure (NOT main-body)

> **2026-04-30 reframing**: previously labeled "Replicated and Exploratory Trait × Stakes Leads" with three "Bonferroni-passing replicated leads" promoted to main-body §6.4. Both labels retracted after reanalysis discovered (a) the two sweeps share the same per-PID *frozen posthoc-refit* router (fit once on baseline expert, reused across all OOD conditions) and the same seed-1 setup → cross-sweep agreement is *deterministic recomputation under different env conditions*, not statistical replication; (b) BH-FDR over the full 324-cell trait × stakes-sensitivity family yields **0 survivors** at q=.10. This appendix now reports the scan as exploratory only, with no main-body claim. Source: `experiments/ood/results/diagnostics/clinical_bh_fdr/`.

**Selection criterion (per cell)**: $|\rho| \ge 0.30 \wedge p < .10$; pooled family size = 162 (multsweep no-acw) + 162 (multsweep acw) = **324 cells**. Random expectation at α=.10 = 32; raw hits = 47 (slight excess); doc-lead criterion (|ρ|≥.30 ∧ p<.10) = 22 cells.

**BH-FDR result (pooled 324-cell family, q=.10)**: **0 survivors**. Adjusted p of all 22 doc-lead candidates lies between 0.27 and 0.94. The previously named "Bonferroni-passing replicated" leads (full table reproduced below) all fail BH q=.10 and are reclassified as direction-consistency exploratory observations only.

| Metric | Trait | $\rho$ no-acw (raw p) | $\rho$ acw (raw p) | BH-adj p (no-acw / acw) | BH q=.10 |
|---|---|---|---|---|---|
| @×5 d_ep_length | S_UPPS_P | +0.35 (.009) | +0.41 (.001) | 0.27 / 0.27 | ✗ |
| @×5 d_NOTHING_frac | S_UPPS_P | +0.32 (.018) | +0.36 (.006) | 0.35 / 0.35 | ✗ |
| @×5 d_expected_h | CES_D | +0.36 (.007) | +0.33 (.015) | 0.27 / 0.44 | ✗ |
| @×5 d_expected_h | BIS_nonplanning | −0.27 (.057) | −0.36 (.008) | 0.60 / 0.27 | ✗ |
| slope d_collision_rate | STAI | +0.31 (.026) | +0.04 (.799) | 0.42 / 0.94 | ✗ |

**Direction-consistency observations (no statistical claim)** — *not* a robustness criterion in the BH-corrected sense; reported transparently to support a single pre-registration follow-up:

| Category | Pattern (acw sweep, raw |ρ|≥.30) | Cells |
|---|---|---|
| Crosswalk usage ↓ | STAI/CES_D ↑ → crosswalk usage less increases under amplified stakes | 6 (all same direction) |
| Router depth slope ↑ | STAI/CES_D ↑ → router depth response slope steeper | 4 (all same direction) |
| BIS-nonplanning anchor | BIS / BIS_nonplanning ↑ → @×5 depth response damped | 2 (both negative) |
| Success rate | S_UPPS_P × @×5 success_rate negative | 1 |
| Replication-failed | STAI × collision-slope (no-acw only, ns in acw) | 3 |

**Recommendation**: any future paper claim about trait × OOD interaction must (i) pre-register a single specific lead from the cells above, (ii) collect an *independent* cohort or independent seeds (not the same checkpoint × different env condition), and (iii) report BH-FDR-adjusted p at q=.10. Until then, dynamic clinical OOD is reported here as a null finding under multiple-comparison correction.

Source artifacts: `experiments/ood/results/diagnostics/clinical_bh_fdr/bh_fdr_summary.md`, `bh_fdr_table.csv`; aggregator script `experiments/ood/scripts/bh_fdr_clinical.py`.

### L.3 Failure-Mode Diagnostics — Why ×100 Collapses

The ×100 collapse is mechanistic and traceable to two co-occurring causes (`experiments/ood/diagnostics/`):

**C1 — State-norm distortion (mechanistically confirmed)**:

| mult | normalized obs[14] mean | max | %\|n\|>3σ |
|---|---|---|---|
| ×1.0 | 0.03 | 1.26 | 0% |
| ×2.0 | 1.52 | 3.97 | 35% |
| ×5.0 | 5.98 | 12.11 | 68% |
| ×10.0 | 13.42 | 25.68 | 68% |
| ×100.0 | **147.33** | **269.97** | **100%** |

State-norm fits training-time obs[14] mean=0.535, σ=0.37. At ×100, normalized obs[14] is uniformly outside training ±3σ band → first hidden activation enters a region the policy has never seen.

**C5 — Compound rollout dynamics (partial mechanism with heterogeneous expression; N=52)**:
- Single-step policy distortion is small (TV(π_OOD, π_baseline) ≈ 0.20 at ×5, 0.40 at ×10)
- Across 50+ rollout steps, this small distortion compounds → episode-level state-visit distribution shifts in a *consistent direction* across the 52-PID population (toward less-dangerous tiles): on_road_frac 0.488 → 0.289 (−41%), on_crosswalk_frac 0.186 → 0.265 (+42%), nearby_car_total 1.21 → 0.81 (−33%) at ×10
- **2026-04-29 update**: an earlier sketch reported this mechanism on N=1 (P1000 only) with *primary cause* framing. After running the same diagnostic across all 52 PIDs, we retract the *primary cause* claim. The mechanism is real but **partial** — IQR (Q25–Q75) at ×10 expands 2–3× across all four state-visit features (on_road_frac at ×10 IQR [0.122, 0.460]), indicating heterogeneous expression and possibly bi-modal response under stress. P1000-specific effect sizes overstate the population mean by 1.6–5×; in particular `car_4ahead_closeness` is a P1000 outlier (+125% on P1000 vs +24% on N=52 mean) and is not retained as a population claim
- Source: `experiments/ood/results/diagnostics/c5_compound/c5_population_summary.md`, `c5_population.csv`, `c5_population.png` (sweep `experiments/ood/scripts/run_c5_pop_sweep.py`)
- Per-h fragility: $h{=}10$ planner is most fragile (TV 0.41 at ×10 vs 0.23 for $h{=}2$)

**C2 (per-h policy fragility)** and **C4 (router amplification)** explored and rejected as primary causes; full analysis in `experiments/ood/ANALYSIS_OOD.md` §5.7.

**Implication for §7.2 Limitations**: SC-AIRL's bounded-foresight imitation generalizes coherently to ~×10 stake amplification; ×100 lies beyond the model's input-distribution envelope due to combined state-norm distortion and compounding rollout dynamics — a property of IRL with offline-trained input normalization, not specific to the bounded-foresight architecture.

---

## 9.K NeurIPS 2026 Paper Checklist

*Full NeurIPS-provided checklist to be answered at end of appendix (~1–2 pages).*

Key responses planned:
- Claims match results: ✓
- Limitations discussed: ✓ (§7.2)
- Theoretical assumptions + proofs: ✓ (§5, Appendix A)
- Experimental reproducibility: ✓ (Appendix B, J)
- Code + data access: ✓ (anonymized during review)
- Compute disclosure: ✓ (Appendix F)
- Human subjects: IRB-approved, consented; clinical measures deidentified
- Broader impact: ✓ (§7.3, Appendix H)
- Safeguards against misuse: depth profiles not released at individual level

---

# 10. Decision Block — Should clinical content be in this paper?

> **Re-evaluated 2026-04-28 under Use-Inspired track.** Earlier risk model assumed standard methodology track. Under Use-Inspired track, "engaging with domain experts" and "real-world use case motivation" are *evaluation criteria*, not liabilities. Conclusion in §10.6 strengthened accordingly.

## 10.1 The dilemma (revised under Use-Inspired track)
- **Old risk (methodology track)**: clinical content reads as scope-creep → "this should go to a clinical journal" reject.
- **New calibration (Use-Inspired track)**: track explicitly invites real-world-use motivation; the failure mode flips. *Underselling* the cognitive/clinical use case is now the bigger risk — reviewers may judge the paper as "method without a use-case" → fails track-fit criterion.
- Project has an explicit BIS/CRA correlation signal that is **orthogonal** to the behavioral metrics and directly tests whether the learned depth is a meaningful cognitive construct — fits track's "match design to use case" criterion.

## 10.2 Binz (2022) NeurIPS precedent — re-analyzed
- Binz & Schulz (NeurIPS 2022, "Resource-Rational RL") devotes **§4.1 (~1 page)** to re-analyzing brain-lesion (vmPFC) data from Bechara et al. 1994 in the Iowa Gambling Task.
- **Crucial framing**: clinical content is NOT the contribution. It is positioned as **"Manipulating Computational Resources"** (§4) — a test of a *model mechanism prediction*: "if we reduce the model's description length, does it behave like a vmPFC-lesioned patient?"
- The result is a *one-direction* prediction: model → clinical pattern. Not: clinical → diagnostic claim.
- Clinical ≈ 10% of the paper length.

## 10.3 Decision for SC-AIRL — **Include, but as mechanism validation (Binz template)**
- **Placement**: §6.3 "Convergent Cognitive Validity of the Inferred Planning Depth", ~0.5 page, AFTER §6.1 imitation + §6.2 reward.
- **Framing**: "If SC-AIRL's depth estimates capture real bounded foresight, they should correlate with orthogonal psychometric measures of cognitive impulsivity."
- **What we claim**: model mechanism prediction confirmed by independent psychometric data.
- **What we do NOT claim**: diagnostic utility, individual-level screening, or clinical decision support.
- **Data scope**: N=51 (participants with BIS/CRA), report r and p with clear "population-level correlation" language.
- **Risk mitigation**: limitations paragraph explicitly states "not a clinical biomarker"; broader impact statement addresses misuse risk.

## 10.4 What would make clinical content a *liability* — avoid these
- Framing clinical correlation as the *primary* contribution (it isn't)
- Per-participant depth profiles presented as diagnostic (we report distributions)
- Claims about clinical populations we didn't actually study (no patient group, only trait measures)
- Using BIS/CRA to "tune" the model (we don't — they are orthogonal held-out measures)

## 10.5 Alternative: move to appendix only?
- Considered but rejected. The correlation is:
  - (a) orthogonal to behavioral metrics (cannot be derived from them)
  - (b) aligned with a specific theoretical prediction (bounded foresight ∝ impulsivity)
  - (c) precedented by Binz 2022's NeurIPS acceptance
- Moving it to appendix only would weaken the "depth is a meaningful cognitive construct" argument, which reviewers will otherwise question.

## 10.6 Final stance (revised 2026-04-28, Use-Inspired track)
> **Clinical content stays in main body as §6.3 Convergent Cognitive Validity (~0.5 page), framed as model-mechanism prediction following Binz 2022. Not as a clinical-utility claim.**
>
> **Additional Use-Inspired track adjustments** (added 2026-04-28):
> - **§1.1 hook**: Hybrid Hook (AI cooperation: AVs/HRI/decision support) → traditional psych model limitations → Lee 2024 IRL bridge → infinite-horizon limit.
> - **§1.2 cognitive evidence**: bounded rationality framing (Simon 1955; Russell 1997; Lieder & Griffiths 2020) + state-conditional depth (Huys 2012; Otto 2013; Opheusden 2023) — ML-audience-friendly jargon explanations included.
> - **§5.1 dataset framing**: emphasize that pedestrian-crossing data carries human cognitive limitations absent from standard driving benchmarks — justifies the non-standard dataset choice (Pauls-paper precedent).
> - **§6.4 mechanism validation**: keep at ~0.5 page (Binz precedent — ~10% paper share is the empirical sweet spot from accepted Use-Inspired papers); do *not* expand to make clinical the headline.
> - **Significance paragraph (§7)**: per track guidelines, briefly note non-ML domain baselines (e.g., classical heuristic-search models from cognitive science — Opheusden 2023) where space allows.

---

# 11. Revision notes (v1 → v1.1)

| v1 Issue (INDEX_v1.md) | v1.1 Resolution |
|---|---|
| Title "CogAIRL" + "better imitates" | Retitled with methodological framing |
| §3 Evaluation Metrics duplicated with §4 Results | §3 removed; metrics folded into §5.1 Setup |
| §2 Methods had no preliminaries / notation | New §2 Preliminaries + Problem Formulation |
| Theory buried as sub-sub-bullet | New §4 Theoretical Analysis (theorem + proposition) |
| Mixed policy as single line | §3.6 dedicated subsection |
| Dataset at end of §2 Methods | Moved to §5.1 Experiments |
| Training settings mixed into Methods | Moved to §5.1–5.2 (setup + baselines) |
| Related work had 3 thin subsections | 4 categorized subsections with "Why this paper goes here" rationale |
| Baselines: only "infinite horizon" | M1–M7 (Std AIRL, BC, Single-h, GAIL, Yao 2024 adapted) |
| "(clinical..?)" tentative | §5.7 Mechanism validation, Binz 2022 template |
| "bootstrapped value network" contradicts V_tail=0 decision | §3.2 makes V_tail=0 an architectural commitment |
| "Loop update / uniform warmup" jargon | §3.4 defines warmup + alternating loop update |
| "Depth router bayesian" one-liner | §3.5 full posterior matching objective |
| No figures | Figure 1 (architecture), Figure 2 (depth map), Figure 3 (identifiability) |
| No Algorithm box | Algorithm 1 in §3.7 |
| No Limitations | §7.2 explicit limitations |
| Korean self-notes left in outline | All resolved |
| "For future Neurocog" reason | Removed — this is a NeurIPS method paper |

---

# 12. Writing order recommendation

1. **First**: Figure 1 (architecture diagram) — forces architectural clarity before writing
2. **Then**: §3 Methods + §4 Theory (the contribution core)
3. **Then**: §2 Preliminaries (once notation is fixed by §3)
4. **Then**: §5 Experiments (after methods are stable)
5. **Then**: §1 Introduction (once results numbers are final)
6. **Last**: §6 Related Work, §7 Discussion, Abstract

---

# 13. Full paragraph drafts (English, ready for `draft.tex`)

> Self-contained English paragraphs for the v1.2 reframings. Index sections above (§1.1, §1.2, §5.2) are the *outline*; this section is the *prose*. When transferring to `draft.tex`, drop the `[Para X]` labels and connect with normal flow.

## 13.1 §1.1 — Computational modeling of human decisions meets bounded rationality

**[Para 1 — Significance + Challenge + First-trial limits]**
Modeling human decision-making is crucial in AI-applied contexts — autonomous driving, human-robot interaction, decision-support systems — where artificial agents must understand and anticipate naturalistic human behavior. Yet, faithfully imitating human behavior remains a fundamental challenge. Cognitive psychology has approached this through computational models — parametric reward functions fit to controlled laboratory tasks (delay-discounting, Go/No-go) — representing a foundational first attempt at formalizing human choice; these models capture stylized choice phenomena but fail to generalize to the high-dimensional, dynamically unfolding behavior people produce in naturalistic environments such as driving and pedestrian navigation (Daw 2011; Lieder \& Griffiths 2020).

**[Para 2 — IRL as the modern bridge; Lee 2024 precedent]**
Inverse reinforcement learning (Ng \& Russell 2000; Ziebart 2008; Fu et al. 2018) bridges this gap by inferring reward functions directly from observed behavior in environments too complex for hand-coded models. Lee et al. (2024) recently demonstrated this in cognitive psychology, applying deep AIRL to real-time driving behavior and recovering individual differences in trait impulsivity that traditional behavioral tasks failed to capture: IRL-inferred latent rewards predicted self-reported BIS impulsivity at $r{=}.72$, compared to $r{=}.48$ for behavioral summary statistics, and combining the two added no incremental variance.

**[Para 3 — The shared limitation: infinite horizon]**
Both Lee (2024) and standard AIRL inherit a foundational assumption from MaxEnt IRL (Ziebart 2008): the demonstrator is Boltzmann-rational with an infinite planning horizon. This is implausible for human behavior — working-memory limits cap planning depth at roughly $4{\pm}1$ items (Cowan 2001; Miller 1956), and Boltzmann-rational AIRL absorbs the resulting bounded-foresight suboptimality only as undifferentiated noise (Laidlaw et al. 2022, BPD). We propose SC-AIRL, which replaces this inherited assumption with a state-conditional bounded foresight inferred from behavior alone (§4).

## 13.2 §1.2 — Bounded rationality and state-conditional planning depth (cognitive MoE)

**[Para 4 — Bounded rationality framing + RHIP empirical anchor]**
Bounded rationality (Simon 1955, 1991; Russell 1997; Lieder \& Griffiths 2020) is the principled correction: humans operate under cognitive resource constraints that limit how deeply they can plan. Empirically at scale, finite-horizon inverse planning ($H{=}10$) outperforms infinite-horizon prediction of real driver trajectories at Google Maps scale (Barnes et al.\ 2023, RHIP) — bounded horizon is not merely a computational convenience but empirically optimal for human-behavior modeling at production scale. Behavioral evidence further shows that planning depth is *not fixed per individual* — it deepens with expertise (van Opheusden et al. 2023, *Nature*) and the same individual prunes lookahead more aggressively under specific states such as time pressure or branching complexity (Huys et al. 2012; Otto et al. 2013; Callaway et al. 2022).

**[Para 5 — Joint implication: cognitive mixture-of-experts]**
These two axes — bounded depth and state-conditional pruning — jointly motivate a cognitive mixture-of-experts view: human behavior arises from several decision systems operating at different planning depths, whose relative contribution is gated online by the current state. Existing IRL remedies address at most one axis. Softened rationality (Laidlaw 2022 BPD) absorbs heterogeneity into noise; discount rescaling (Yao 2024; Schultheis 2022) modulates the temporal weighting but retains infinite lookahead computation; trajectory-level expertise (IRLEED, Beliaev \& Pedarsani 2024; DTIL, Seo \& Unhelkar 2025) treats heterogeneity as fixed per-demonstrator. None model a state-varying physical horizon cutoff.

## 13.3 §5.2 — Baseline scoping (Option B+)

**[Scoping paragraph]**
Our objective is to infer latent reward structures and cognitive planning mechanisms directly from data, without relying on hand-crafted rules or domain-specific physical equations. We therefore focus baseline comparisons on state-of-the-art data-driven imitation learning algorithms — standard AIRL (Fu et al. 2018), behavioral cloning, GAIL, and single-$h$ ablations. Traditional non-ML generative models (e.g., social force models; Helbing \& Molnár 1995) remain popular in pedestrian simulation, but they require manually specified interaction rules and do not infer subjective reward functions, placing them outside the scope of inverse reward learning.

**[Latent-mechanism evaluation paragraph]**
When evaluating whether the inferred mechanisms capture meaningful individual differences (§6.4), we follow the approach established by Lee et al. (2024): they showed that simple behavioral summary statistics (e.g., mean speed, collision count) explain less variance in trait impulsivity than IRL-inferred latent rewards (predictive correlation $r{=}.48$ vs $r{=}.72$), and add no incremental variance when combined with IRL features. We accordingly discard surface-level summary statistics and compare models strictly on the quality of their inferred latent mechanisms — planning depth and reward consistency.

**[EM-depth positioning footnote (Yao 2024 differentiation)]**
The episode-level EM-depth baseline (B5) extends the core insight of Yao et al. (2024) — that planning-horizon heterogeneity should be jointly inferred with reward — to our physical-truncation setting. It does not reproduce Yao 2024's algorithm: Yao 2024 modulates a per-agent discount $\gamma_i$ while keeping infinite-lookahead value computation, whereas B5 keeps physical $h$-step truncation but lets $h$ be inferred per episode rather than per state. The B4-vs-B2 comparison therefore isolates the truncation-vs-discount axis, and the B5-vs-Ours comparison isolates the trajectory-level-vs-state-level granularity axis cleanly.

---

## 13.4 Length budget (target word counts for `draft.tex`)

| Section | Words | Pages (NeurIPS 10pt, ~550 wpp) | Status |
|---|---|---|---|
| §1.1 (Para 1–3) | ~200 | ~0.36 | drafted |
| §1.2 (Para 4–5) | ~150 | ~0.27 | drafted |
| §1.3 Contributions | ~250 | ~0.45 | inherited from v1.1 |
| §1.4 Results preview | ~50 | ~0.09 | inherited from v1.1 |
| **§1 total** | **~650** | **~1.18** | within 1.25–1.5p budget ✓ |
| §5.2 scoping (2 paras + footnote) | ~280 | ~0.51 | drafted |
| §5.2 baseline list (5-row table) | ~120 | ~0.22 | drafted |
| **§5.2 total** | **~400** | **~0.73** | reasonable for baselines section |
| §6.1 Behavior Gap (3 paras + table) | ~350 | ~0.64 | drafted |
| §6.2 Router Adaptivity | ~280 | ~0.51 | drafted |
| §6.3 Reward Superiority | ~330 | ~0.60 | drafted |
| §6.4 Mechanism Validation | ~280 | ~0.51 | drafted |
| §6.5 Ablations | ~120 | ~0.22 | drafted |
| **§6 total** | **~1360** | **~2.47** | within 2.5–3.0p budget ✓ |
