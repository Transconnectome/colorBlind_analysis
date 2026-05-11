# SC-AIRL — Meeting Outline (logical flow only, synced with `INDEX_v1.2.md` / 2026-04-28)

> Subtitle + 1–2 lines per item so the logical flow is visible at a glance. Full detail in `INDEX_v1.2.md` (with English paragraph drafts in §13) and `draft.tex`.
>
> **v1.2 key changes** (vs v1.1):
> 1. **Track**: targeted at NeurIPS 2026 **Use-Inspired Contribution Track** (not standard methodology track).
> 2. **§1 reframed**: Hybrid Hook (AI cooperation: AVs/HRI/decision support) → Lee 2024 deep-AIRL precedent → infinite-horizon limit → bounded rationality + state-conditional depth.
> 3. **§5/§6 restructure**: previous §5 *Theoretical Analysis* (Prop 1/2) **moved to Appendix A**; previous §6 split into new §5 *Experimental Setup* + new §6 *Results* (4 empirical headlines).
> 4. **§5.2 baselines** scoped via Option B+ (data-driven IRL); Helbing 1995 + Lee 2024 explicitly justify exclusion of non-ML generative models and summary statistics.
> 5. **EM-depth (B5)** introduced as "episode-level baseline extending the core insight of Yao 2024 to physical truncation" (avoids implying B5 reproduces Yao's algorithm).
> 6. **N=52 canonical** (was N=51/N=56). Clinical numbers in §6.4 to be re-verified against current `router_clinical_correlations.csv`.
> 7. **C1/C2/C3/C4 4-contribution structure (calibrated; C3 reframed 2026-04-29)**: split v1.1's combined C2 (imitation+reward) into separate **C2 (imitation)** and **C3 (reward recovery + task-goal absorption)**; v1.1's C3 (clinical) → **C4**. C3 originally framed as "preliminary task-alignment" (sharper Δr, saliency, action-prediction asymmetry); reframed 2026-04-29 to "task-goal absorption + decoupling" after refined 3×2-cell analysis (`{off-road, on-road} × {none/medium/close imminent vehicle proximity}`) showed both methods recover near-identical context-action argmax structure (100% concordance in 5/6 cells), with contextual decision heterogeneity localized to policy/router rather than reward (cleanest expression: `offroad_close` expert is 52/52 NOOP while reward is UP-dominant; negation-style evidence).
> 8. **§6 restructure with 1:1 C-mapping**: §6.1 ↔ C2 (Imitation + C1 mechanism + train-test) | §6.2 ↔ C3 (Reward recovery + task-goal absorption) | §6.3 ↔ C4 (Clinical) | §6.4 supplementary (OOD) | §6.5 Ablations.
> 9. **Algorithm 1 moved to Appendix A.6** (page-budget; main-body §4.6 reduced to 1-line pointer + ablation conditions).
> 10. **OOD as supplementary §6.4 + §9.L Appendix (reframed 2026-04-30)**: §6.4 main-body now reports *behavioral* graded-caution monotonicity (×2/×5/×10) + per-attempt collision decomposition (commit/abort separation) only; *dynamic clinical OOD* moved out of main body to avoid double-counting against §6.3 static convergent validity. Previous "3 replicated Bonferroni-passing leads" claim retracted: two sweeps share the same per-PID frozen posthoc-refit router + seed-1 → cross-sweep agreement is deterministic recomputation, not statistical replication; BH-FDR over the full 324-cell trait × stakes-sensitivity family yields 0 survivors at q=.10. Trait × stakes scan now reported as exploratory only in Appendix L.2. Multiplier curve, per-attempt table, and C5 partial-mechanism N=52 evidence + ×100 collapse failure-mode diagnostics in Appendix L (L.1 / L.3).
> 11. **Train-test split with placeholders (§6.1 Table 1b)**: stratified 8/40 holdout pre-registered (T1–T4); placeholder values until ~5h × 3-server retraining executes; pre-registered plan in Appendix J.5.
> 12. **C4 (§6.3) refined to three-line structure (2026-04-30 v3)**: (i) router-invariant signal map across 3 main routers (`sc_categorical` posthoc / `stickbreaking` / `hspace_gaussian` posthoc; 19 metrics × 25 clinical × 3 routers = 1425 correlations → **15/475 cells robust same-sign, 0/475 mixed-sign**), (ii) within-domain in-task bridge (`shift_road_danger × NOTHING_ratio` +0.46 = top robust signal; `E_h_time_low × jaywalking` −0.41) — latent depth predicts in-task behavior the model was *not* trained on, complementing the cross-domain DDT bridge, (iii) Pillar 5 EM E[h] (state-independent global aggregate; UPPS-P facets +0.45–0.49). Time-pressure metric (Huys 2012 textbook lever) added as state contrast. STAI / CES_D / most DOSPERT cells reported as null honestly. Pending-verification box closed; full audit in `docs/paper_related/EXP_ROUTER_CLINICAL.md`.

---
## Potential Title

**SC-AIRL: State-Conditional Adversarial Inverse Reinforcement Learning for Imitating Human Behavior under Bounded Foresight**

---

## §1 Introduction

- **§1.1 Computational modeling of human decisions meets bounded rationality.**
    - **Para 1 (Significance + Challenge + First-trial limits)**: Modeling human decision-making is crucial in AI-applied contexts (autonomous driving, HRI, decision-support systems); yet faithfully imitating human behavior remains challenging. Cognitive psychology approached this via parametric reward models on lab tasks (DDT, GNG) — a *foundational first attempt* that captures stylized choice but fails to generalize to high-dim dynamic real-world behavior (Daw 2011; Lieder & Griffiths 2020).
    - **Para 2 (IRL bridge + Lee 2024)**: Inverse RL (Ng & Russell 2000; Ziebart 2008; Fu 2018) infers rewards from behavior. Lee et al. (2024) demonstrated this on real-time driving (BIS r=.72 vs summary-stats r=.48; combined adds nothing).
    - **Para 3 (Shared limitation)**: Lee 2024 + standard AIRL inherit MaxEnt IRL's *infinite-horizon Boltzmann-rationality* — implausible for humans (working memory 4±1, Cowan 2001); suboptimality absorbed only as noise (Laidlaw 2022 BPD).
- **§1.2 Bounded rationality and state-conditional planning depth (cognitive MoE).**
    - **Para 4**: Bounded rationality (Simon 1955; Russell 1997; Lieder & Griffiths 2020). **Empirically at scale, finite-horizon IRL (H=10) outperforms infinite-horizon for real driver trajectories at Google Maps scale (Barnes 2023, RHIP)** — bounded horizon is empirically optimal, not merely computational convenience. Depth not fixed: deepens with expertise (Opheusden 2023 *Nature*); shortens state-dependently (Huys 2012; Otto 2013; Callaway 2022).
    - **Para 5**: Cognitive MoE — bounded depth + state-conditional pruning gated online by state. Existing IRL remedies are partial: softened rationality (BPD), discount rescaling (Yao 2024; Schultheis 2022), trajectory-level expertise (IRLEED; DTIL) — none model state-varying physical horizon cutoff.
- **§1.3 Contributions (v1.2 final, calibrated 4-contribution).**
    - **C1 (propose)** **SC-AIRL: State-Conditional Bounded-Foresight AIRL** — first AIRL inferring state-conditional planning depth $h$; physical h-step cutoff via GAE-h (formal results in Appendix A).
    - **C2 (demonstrate)** **Improved Human Behavior Imitation under Bounded Foresight** (§6.1)
        - 2.13× tighter |ΔSR| vs Std AIRL
        - ~30% NOTHING-action gap reduction (−13.6%p → −9.5%p)
        - Top-1 0.585 → 0.762 (LogGauss); SC-Cat 0.725 with SR ~0.71
        - State-conditional adaptation does not collapse: SAFE/DANGER 1.089, p<.05 across all PIDs
    - **C3 (demonstrate)** **Depth-Invariant Reward Recovery and Task-Goal Absorption** (§6.2)
        - Reward identifiability r=0.784 ± 0.043 cross-correlation SC vs Std AIRL → verifies A3
        - Cross-method 3×2-cell argmax-action concordance: 100% in 5/6 contextual cells, 65.4% in 1/6 (`offroad_close`) — both methods recover near-identical context-action preference structure
        - Reward-vs-expert dissociation (negation-style decoupling): reward UP-dominant in 6/6 cells; expert UNANIMOUSLY NOOP in `offroad_close` (52/52 PIDs) yet reward UP-argmax → 73–90% dissociation in off-road × {medium, close} cells — contextual decision heterogeneity is absorbed by bounded-foresight policy/router, not by reward
    - **C4 (show)** **Convergent Cognitive Validity of the Inferred Planning Depth** (§6.3, Binz 2022 template, ~10% paper share)
        - *Three converging lines of evidence (2026-04-30 v3, 19 metrics × 25 clinical × 3 routers = 1425 correlations)*:
            - **(i) Router-invariant signal map**: 3 main routers (`sc_cat` posthoc / `stickbreaking` / `hspace_gaussian` posthoc); **15/475 robust same-sign, 0/475 mixed-sign**. Headline: $E[h]$ mean × DDT log(k) +0.40 robust 3/3; $E[h\mid\text{road}]$ × UPPS-P premeditation +0.40; state-adaptation × **BIS_motor robust 3/3 (mean +0.34)** (× BIS-total partial 2/3, mean +0.29, consistent direction); $\sigma_s(E[h\mid s])$ × DDT log(k) +0.31 robust 3/3.
            - **(ii) Within-domain in-task bridge** (NEW): latent depth predicts in-task behavior the model was *not* trained on — `shift_road_danger × NOTHING_ratio` r=**+0.46** (top of full 475-cell table); `E_h_time_low × jaywalking` −0.41; `E_h_safe / E_h_mean × jaywalking` −0.37 / −0.36 — all robust 3/3 routers. **Two independent bridges**: cross-domain (DDT lab task) + within-domain (gameplay).
            - **(iii) Pillar 5 EM E[h]** (state-independent global aggregate, $r_s{=}0.21$ ns vs router): UPPS-P facets +0.45–0.49 (p<.001). Different cognitive cut.
        - *Dynamic (OOD)*: not reported as C4 evidence in main body to avoid double-counting against (i)–(iii); trait × stakes-sensitivity scan moved to Appendix L.2 as exploratory only (BH-FDR q=.10 over 324 cells = 0 survivors; previous "Bonferroni-passing replicated leads" claim retracted 2026-04-30 — both sweeps share the same frozen posthoc-refit router and seed-1 setup, so cross-sweep agreement is deterministic recomputation, not statistical replication).
        - *Reported as null (honest)*: STAI-total / CES_D-total / most DOSPERT cells uniformly non-significant in *static* convergent validity — not hidden.
        - ✅ **Resolved 2026-04-30**: "BIS r=−0.38, CRA r=−0.44" v1.1 claim not reproducible; replaced by (i)+(ii)+(iii). UPPS-P numbers re-attributed to Pillar 5 EM (same numbers, correct provenance). Full audit: `docs/paper_related/EXP_ROUTER_CLINICAL.md`.
    - **Verb discipline**: *propose* (C1) — *demonstrate* (C2, C3) — *show* (C4)
    - **v1.2 split rationale**: v1.1's combined C2 (imitation+reward) split into separate C2 (imitation) and C3 (reward recovery + task-goal absorption) for §6.x ↔ C-numbering 1:1 mapping; clinical validation renumbered C3 → C4. C3 wording reframed 2026-04-29 from "preliminary task-alignment" to "task-goal absorption + decoupling" after pre-check showed near-identical context-action argmax across methods.
- **§1.4 Results preview** (mapped to C2/C3/C4).
    - **C2 (§6.1)**: 2.13× tighter $|\Delta SR|$, NOTHING gap −13.6%p → −9.5%p, Top-1 0.585 → 0.762; held-out generalization placeholder (Appendix J.5).
    - **C3 (§6.2)**: reward identifiability r=0.784 (verifies A3); 3×2 argmax concordance 100% in 5/6 cells; **continuous 5×2 heatmap** shows reward UP−NOOP narrow gradient (~0.4 range) vs policy UP−NOOP wide gradient (~1.1 range, off-road: +0.53→−0.61) — direct visualization that bounded-foresight modulation lives in policy channel; SC-AIRL-Cat policy modulates more than Std AIRL at extreme proximity while rewards differ ≤0.06 across all 10 cells.
    - **C4 (§6.3)**: 15/475 cells robust across 3 main routers; **0/475 mixed-sign**. Top: `shift_road_danger × NOTHING_ratio` +0.46 (within-domain bridge); `E_h_time_low × jaywalking` −0.41; DDT cluster mean +0.40; state-adaptation × BIS_motor +0.34 robust 3/3. Pillar 5 EM (distinct global cut) UPPS-P +0.45–0.49.
    - Supplementary (§6.4): behavioral graded-caution monotonicity (×5/×10) + per-attempt collision decomposition (commit/abort separation); ×100 collapse boundary diagnosed in Appendix L. Dynamic clinical OOD reported as exploratory only in Appendix L.2 (BH-FDR q=.10 = 0 survivors over 324 cells; previous "Bonferroni-passing replicated leads" claim retracted 2026-04-30; static convergent validity for the 4 main scores already covered by §6.3 (i)–(iii) and the null disclosure for STAI/CES_D-total/DOSPERT).

---

## §2 Related Work (3-stage)

### S1 Why bounded horizon — cognitive necessity + empirical validation

- **Binz & Schulz 2022 (NeurIPS)**
    - Constraint imposed *on the model* reproduces vmPFC-lesion-like patient behavior
    - Architectural precedent + mechanism-validation template for §6.4
- **Barnes 2023 (RHIP, Google Maps)**
    - IRL with finite horizon H=10 predicts real driver routes *better* than H=∞
- **Huys 2012 / Callaway 2022**
    - Same individual prunes lookahead state-dependently — motivates state-conditional depth
- **Tian 2021**
    - Cognitive bound as latent variable jointly inferred — methodological precedent
- **Lee et al. 2024 (*Psychol. Sci.*) — NEW in v1.2**
    - Closest real-time-IRL precedent on cog-psych-grade human data
    - IRL reward predicts BIS at r=.72 vs summary stats r=.48; combined adds 0 — *defends our exclusion of summary-statistic baselines* (§5.2 scoping)
    - Inherits infinite-horizon limit that SC-AIRL relaxes
- **Bounded rationality canon (NEW in v1.2)**: Simon 1955; Russell 1997; Lieder & Griffiths 2020 — principled framing for cognitive resource constraints

### S2 Multi-horizon IRL via discount-rate adaptation — two missing axes

- **Yao 2024 (NeurIPS, closest prior work)**
    - Per-agent discount $\gamma_i$ + shared reward in tabular 5×5
    - Starting point for SC-AIRL's two differentiation axes
- **Axis-1 Critique: physical h-step truncation, not discount rescaling**
    - **Schultheis 2022**: non-exponential discount, infinite lookahead intact
- **Axis-2 Critique: depth should be state-varying, not per-agent fixed**
    - **Li 2023 (DCPPO) / Mazumdar 2024**: bounded rationality theory, but never *learn* the bound
    - **Beliaev 2024 (IRLEED) / Seo 2025 (DTIL)**: heterogeneity as expertise/suboptimality at trajectory grain; no structural bounded-foresight

### S3a State-dependent depth is identifiable as latent variable

- **Opheusden 2023 (*Nature*)**: depth shifts with expertise/time-pressure within an individual — licenses $p_\phi(h|s)$ over $p_\phi(h|i)$
- **Seo 2024 (IDIL)**: end-to-end adversarial latent inference is unstable — direct precedent for our mixture-NLL on frozen $\pi^h$

### S3b Multi-policy mixture-of-experts architecture

- **Blessing 2023 (IMC)**: MoE gating avoids mode averaging
- **Chen 2025 (PEMMFIRL / Meta-IRL-MFG)**: probabilistic context distilled into context policy
- **Reuss 2024 (MoDE) / Wang 2024 (MoE-IL)**: state/context-conditional MoE is current SOTA direction
- **Chen 2023 (MH-AIRL, architectural sibling)**: same hierarchical-AIRL template indexed by *task*; we make latent variable *state-conditional*

---

## §3 Preliminaries & Problem

- **§3.0 Preliminaries.** MDP, MaxEnt IRL, AIRL log-ratio discriminator.
- **§3.1 Assumptions (A1)–(A3).**
    - A1: *physical* h-step truncation (no bootstrap past h)
    - A2: cognitive MoE (depth varies *within* a trajectory by state)
    - A3: single shared reward + Φ≡0
- **§3.2 Problem.**
    - Imitation gap = systematic deviation that rationality-assumed AIRL cannot absorb
    - Difficulties: reward–horizon coupling; stable inference of latent depth (resolved in §4 via factored E-M, IDIL-style)

---

## §4 SC-AIRL

- **§4.1 Overview — three structural replacements** (Truncation / Multi-policy / Shaping; A1 / A2 / A3)
- **§4.2 Depth-invariant reward.** Φ≡0 → $f_\theta = r_\theta$. (Identifiability discussion → Appendix A)
- **§4.3 Multi-policy + GAE-h.** $V^h$ is only bootstrap channel, strictly inside h-step window.
- **§4.4 Mixed-policy discriminator $D_\text{mix}$.** $\pi_\text{mix}=\sum_h p_\phi(h|s)\pi^h$ as denominator. EM schedule: warmup 10k uniform, then updates per Δ=10 rounds.
- **§4.5 Router $p_\phi(h|s)$.** Mixture-NLL with $\pi^h$ frozen (factored, IDIL-style). Categorical (default) vs Gaussian-kernel (ablation).
- **§4.6 Algorithm**

---

## §5 Experimental Setup (NEW STRUCTURE in v1.2)

> Previous §5 *Theoretical Analysis* (Prop 1/2) moved to **Appendix A** — prior works (Yao 2024; MH-AIRL; IDIL) similarly do not include such formal results in main body, and propositions' role here was vague.

- **§5.1 Non-standard Real-World Pedestrian Dataset.**
    - **N=52** (canonical, 2026-04-28; was N=56/N=51 in v1.1)
    - 113-dim state, 5 discrete actions
    - Use-Inspired emphasis: real-time real-world data carrying human cognitive limitations (deliberate waiting under risk, asymmetric lateral preferences) absent from standard driving benchmarks
    - Same lab/paradigm lineage as Lee 2024 (pedestrian-crossing variant of highway-IRL pipeline)
- **§5.2 Baselines — Ablation Ladder & Triangulation (Option B+ scoped).**
    - **B1 BC** (no reward learning) — surface-imitation upper bound
    - **B2 Std AIRL** ($h=\infty$) — primary baseline
    - **B3 GAIL** — adversarial IL without reward
    - **B4 Single-h AIRL** — fixed $h\in\{2,3,5,10\}$, no router
    - **B5 EM-depth AIRL** — *episode-level baseline extending the core insight of Yao 2024 (joint horizon-reward inference) to physical truncation*; per-trajectory h. **NOT a reproduction of Yao 2024's algorithm** (Yao modulates discount; we keep h-step truncation).
    - **OURS SC-AIRL** (Cat / Gauss / LogGauss) — per-state $p_\phi(h|s)$
    - **Triangulation**: B1 vs B2 = adversarial reward learning; B2 vs B4 = finite vs ∞; B4 vs B5 = fixed vs trajectory-mixed; **B5 vs Ours = trajectory-level vs state-level** (key novelty axis)
    - **Out-of-scope (justified)**: social force / heuristic planners (Helbing 1995) → not IRL; summary statistics → Lee 2024 dominance argument
- **§5.3 Evaluation Metrics — domain-aligned, beyond Success Rate.**
    - Behavioral imitation: Top-1, TV/KL/JS, NOTHING-gap, $|\Delta SR|$ (closer-to-expert is better)
    - Router quality: entropy CV%, depth ratio SAFE/DANGER, MAP synthetic sanity (→ Appendix)
    - Reward recovery + task-goal absorption (§6.2 ↔ C3): cross-method (s,a) Pearson r=0.784; 3×2-cell argmax-action concordance (closeness × is_road) + reward-vs-expert action-mode dissociation
    - Mechanism validation: depth × BIS / CRA / DDT (Binz 2022 template)

---

## §6 Results (NEW STRUCTURE in v1.2 — replaces theoretical content with empirical headlines)

> 4 empirical headlines, each answering one question that single-horizon AIRL fails. Theoretical theorems no longer in main body.

- **§6.1 Imitation Fidelity under Bounded Foresight (C2 + C1 mechanism + train-test).**
    - **Imitation result headline**: SC-AIRL recovers human-aligned action distributions — Top-1 0.762/0.725, $|\Delta SR|$ 0.069/0.093, NOTHING-gap reduced ~30% (−13.6%p → −9.5%p).
    - **Comparison anchor (Table 1)** — pinpoints failure modes of each baseline class:

      | Model | Top-1 | SR | NOTHING |
      |---|---|---|---|
      | BC | 0.887 | 0.474 ✗ | TBD |
      | Std AIRL | 0.585 ✗ | 0.823 (overshoots) | 0.270 (−13.6%p) |
      | EM-depth | TBD | TBD | TBD |
      | **SC-Cat** | 0.725 | 0.706 | 0.312 (−9.5%p) |
      | **SC-LogGauss** | **0.762** | 0.705 | 0.311 (−9.5%p) |
      | Expert | 1.000 | 0.640 | 0.407 |

    - **Mechanism (C1)**: state-conditional MoE routing — SAFE/DANGER ratio 1.089 ± 0.110 (mild but robust, p<.05); inter-individual entropy CV% 14.2% (vs Gauss-fixed-σ 2.4%) — recovers within-individual depth shift (van Opheusden 2023) from behavior alone.
    - **Generalization (Table 1b, placeholders)**: stratified 8/40 holdout, T1–T4 pre-registered in Appendix J.5. Status: code/launcher ✅, data inspection ✅, dry-run ✅, full execution ⏸ user-approval gated. Claim contingent on execution: depth routing is *not* trajectory memorization.
- **§6.2 Depth-Invariant Reward Recovery and Task-Goal Absorption (C3; verifies A3, supports C1).**
    - **(i) Identifiability anchor** — cross-correlation **r=0.784±0.043** SC vs Std AIRL on (s,a) reward landscape (51/52 PIDs r>0.6; p<<10⁻⁵⁰ vs null)
    - **(ii) Cross-method 3×2-cell argmax-action concordance** — both methods learn UP-dominant argmax across all 6 cells (`{off-road, on-road} × {none, medium, close imminent proximity}`, where **closeness** $C = \max(\text{obs}[77,81,89,93]) \in [0,1]$ — head-closeness of the nearest car in the same row and one row ahead, on left and right; max over the 4 imminent-vehicle proximity channels); per-PID concordance **100% in 5/6 cells**, 65.4% in `offroad_close` (SC: 37 UP / 14 NOOP / 1 RIGHT vs Std AIRL: 47 UP / 5 NOOP)
    - **(iii) Reward-vs-Expert dissociation (negation-style decoupling evidence)** — reward UP-dominant in 6/6 cells; expert behavior shifts dramatically: on-road × {none, medium} → expert UP 52/52 (0% dissociation); `offroad_close` (safe-zone but vehicle imminent) → **expert UNANIMOUSLY NOOP across all 52 PIDs** yet reward remains UP-dominant (73.1%/90.4% reward-vs-expert dissociation under SC/Std AIRL); `offroad_medium` → expert NOOP 43/52 (88.5% dissociation). Reward encodes *task goal* only; contextual decision heterogeneity (deliberate waiting, observation) is absorbed by bounded-foresight policy/router rather than by reward — directly verifying the architectural commitment.
    - **(iv) Cell-level preference confidence (supplementary)** — coherent 2-direction signal in `offroad_close`: SC less concordant + less sharp (d=−0.28, p=0.05) than Std AIRL, consistent with the partial NOOP-encoding in (ii). In other cells SC sharper at off-road no/medium proximity (d=+0.85, +0.48). Reported as secondary supporting evidence.
    - **(v) Continuous 5×2 reward-policy heatmap (refined 2026-04-29; paper §6.2 main figure)** — softmax(reward) UP−NOOP vs policy π(UP|·)−π(NOOP|·) across 5 **closeness** bins ($C \in \{0,\,(0,0.25],\,(0.25,0.5],\,(0.5,0.75],\,(0.75,1]\}$, $C$ defined in (ii)) × 2 road levels: **reward varies narrowly (~0.4 range across all 10 cells)** while **policy swings widely (~1.1 range, off-road: +0.53→−0.61)** — direct quantitative visualization of the decoupling thesis (bounded-foresight modulation lives in policy, not reward). Reward−policy gap grows monotonically with closeness (off-road: 0 → 0.65). SC-AIRL-Cat policy modulates more than Std AIRL at the highest-closeness cells (off-road × closeness>0.75: SC π=−0.61 vs Std π=−0.36; on-road × closeness>0.75: SC π=−0.21 vs Std π=0.00), with reward differences ≤0.06 in all 10 cells. Figures: `analysis/REWARD_COMPARISON/figures/reward_policy_heatmap_5bin.{pdf,png}` (PDF for LaTeX, PNG for slides/Notion).
- **§6.3 Convergent Cognitive Validity of the Inferred Planning Depth (C4, Binz 2022 template, ≤0.5p).**
    - **(i) Router-invariant signal map (3 main routers, 19 metrics × 25 clinical = 475 cells)**:
        - **15/475 robust** all-3-router same-sign; **0/475 mixed-sign**.
        - DDT cluster: $E[h]$ mean / $E[h\mid\text{SAFE}]$ / $E[h\mid\text{time_high}]$ / $\sigma_s(E[h\mid s])$ × DDT log(k) — mean r +0.31 to +0.40
        - State-adaptation $E[h\mid\text{SAFE}] - E[h\mid\text{DANGER}]$ × **BIS Motor robust 3/3** (mean +0.34); replicated under broader road zoning (`shift_safe_road × BIS_motor` +0.32)
        - BIS-total partial 2/3 (mean +0.29, consistent direction; motor facet drives trait-level)
        - UPPS-P premeditation cluster: $E[h\mid\text{road}]$ × premeditation +0.40 (top); 5 cells robust 3/3
    - **(ii) Within-domain in-task bridge (NEW 2026-04-30 v3)** — latent depth predicts in-task behavior the model was *not* optimized for:
        - `shift_road_danger × action_Nothing_ratio` r=**+0.46** (top of full 475-cell table); within-road tightening predicts how often participants chose NOTHING in-task
        - `E_h_time_low × jaywalking_ratio` −0.41; depth under time pressure ↔ less jaywalking
        - `E_h_safe / E_h_mean × jaywalking` −0.37 / −0.36 (robust 3/3)
        - **Two independent bridges** from depth construct → behavior: cross-domain (DDT) + within-domain (gameplay)
    - **(iii) Pillar 5 EM E[h] (state-independent global aggregate)**: UPPS-P — Sensation Seeking +0.48, Positive Urgency +0.49, Total +0.45 (all p<.001). Distinct from router (r=0.21 ns).
    - **Time-pressure metric (Huys 2012 textbook lever) — partial**: `E_h_time_low × jaywalking` and `E_h_time_high × DDT log k` robust 3/3; but `shift_time_press` itself non-significant — level under pressure is informative, the differential is too noisy at N=52.
    - **Reported as null (honest)**: STAI-total / CES_D-total / most DOSPERT cells uniformly non-significant; not hidden.
    - ✅ Resolved 2026-04-30 (was ⚠️ pending): see `docs/paper_related/EXP_ROUTER_CLINICAL.md`.
    - What we do NOT claim: diagnostic utility, individual screening
- **§6.4 Robustness under Covariate Shift (Supplementary Analysis).**
    - *Posthoc-router architectural disclosure*: OOD evaluation uses the post-training-refit categorical router (objective identical to in-training router loss, fitted on baseline expert under frozen per-h policies). Tests the *architectural gating object*, not the trained router weights; trained-router OOD generalization deferred to future work. Same posthoc checkpoint reused across all OOD conditions per PID — cross-condition agreement is deterministic recomputation, not statistical replication.
    - **Graded caution under stake amplification (population mean, N=52)**: at ×5/×10 (`obs[14]` outside trained [0,1] range), monotone increases in ep_length, NOTHING-fraction, crosswalk usage, router depth — qualitatively human-like prudence; boundary at ~×10
    - **Per-attempt collision decomposition (NEW)**: separates *abort* (NOTHING-stack → timeout) from *commit* (per-attempt collision). Abort scales gracefully (0.00 → 0.21 at ×5 → 0.48 at ×10 → 0.77 at ×100); commit-conditional collision spikes (0.38 → 0.57 at ×5 → 0.88 at ×10). Two-stage decision separation: risk recognition (NOTHING-abort) preserved under OOD, but commit-stage car-avoidance degrades — clarifies headline collision-rate increase as *commit-stage misalignment*, not abort-stage failure.
    - **Dynamic clinical OOD**: not reported in §6 main body (would double-count against §6.3 (i)–(iii) static cuts which already report the 4 main scores: BIS Motor (sig in static), DDT log(k) (sig), UPPS-P (sig), STAI/CES_D-total/DOSPERT (null and disclosed)). Trait × stakes-sensitivity scan reported as exploratory in Appendix L.2 (BH-FDR q=.10 over 324 cells = 0 survivors; previous "Bonferroni-passing replicated" claim retracted 2026-04-30).
    - Interpretation: behavioral graded caution is consistent with *some* extrapolation beyond the trained input range, but the per-attempt decomposition shows commit-stage misalignment grows non-linearly with stakes; we do not claim that the architectural gating object provides *clinical* convergent validity in OOD beyond §6.3 in-distribution.
    - Multiplier curve, per-attempt table, exploratory clinical leads with BH-FDR honest disclosure, C5 partial-mechanism N=52 evidence, and ×100 collapse failure-mode diagnostics → Appendix L (L.1/L.2/L.3).
- **§6.5 Ablations.**
    - Router 2×2: Cat / Gauss / LogGauss × no-loop / loop. Gauss-fixed-σ loses 6× expressivity.
    - Component: no truncation / no router / no multi-policy
    - $\mathcal{H}$ sensitivity: {3,5} vs {2,3,5,10} vs {2,5,10,20}

---

## §7 Discussion / Limitations / Broader Impact

- **Limits.**
    - Single domain (pedestrian crossing only)
    - Discrete $\mathcal{H}$ grid (continuous depth open)
    - Population-level mechanism validation (not diagnostic)
    - State-dependent only, not history-dependent
    - **In-distribution generalization (held-out map seeds)**: pre-registered T1–T4 plan ready (Appendix J.5); execution pending; supplementary OOD stake-amplification (§6.4, Appendix L) provides complementary covariate-shift axis with completed data.
    - **×100 OOD collapse boundary**: noted as known IRL+state-norm failure mode (Appendix L.3 diagnoses C1 state-norm distortion + C5 compound rollout dynamics) — not specific to bounded-foresight architecture.
- **Broader impact.**
    - Positive: interpretable AV/pedestrian models → safety; cognitive decision support
    - Risk: depth inference misuse for surveillance/actuarial → no per-individual depth release

---

## Appendix A (formal results, moved from main-body §5 in v1.2)

- A.0 Two formal questions raised by (A1) + (A3)
- A.1 **Proposition 1** — Bounded-support weighting ≠ discount-rescaling (statement + proof + implication)
- A.2 **Proposition 2** — GAE-h with $V_\text{tail}\equiv 0$ has no infinite-horizon residue (statement + proof + implication)
- A.2.5 Remark — Consistency with AIRL identification (Ng 1999 shaping equivalence; empirical anchor r=0.784 in §6.3)
- A.3 Telescoping identity (used in §4.2)
- A.4 Router objective equivalence (mixture-NLL ↔ KL distillation)
- A.5 Router consistency (optional)
