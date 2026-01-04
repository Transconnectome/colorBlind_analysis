Research Plan

Planning-Aware IRL/AIRL for Expertise, Clinical Traits, and (Exploratory) Neural Links

⸻

1. Motivation

Human behavior is not determined by reward alone. Observable actions are shaped by planning mechanisms—how far into the future people simulate outcomes, how consistently they search, and how noisy their choices are.
	•	Cognitive modeling suggests that expertise often reflects deeper planning rather than fundamentally different heuristics (van Opheusden et al., 2023).
	•	IRL theory shows that planning horizon can be a latent confounder that breaks reward identifiability if ignored (Yao et al., 2024).
	•	We aim to unify these ideas into a framework where planning is explicit, inferable, and manipulable, and examine how this improves IRL/AIRL interpretability—especially for individual differences and clinical traits.

⸻

2. Objectives

Objective 1

Define planning depth as an explicit, inferable factor in human decision-making models (planning depth h, inverse temperature \beta, lapse/dropout).

Objective 2

Test whether estimated planning depth discriminates novices vs experts in 4-in-a-row (using h \in \{1,\dots,5\}).

Objective 3

Improve explainability of IRL/AIRL by modeling planning as a latent confounder, rather than attributing all behavioral variation to reward.

Objective 4

Explain clinical variability (e.g., anxiety/disorder severity) or expertness(expert, novice) via planning mechanisms, not only via reward differences.

Objective 5 (Exploratory)

Connect planning parameters to neural mechanisms (parametrized fMRI; model-based regressors and/or individual-difference mapping).

⸻

3. Methods: Behavioral Planning Model (4-in-a-row)

3.1 Model components
	•	Planning depth h (discrete: 1 to 5): how many future steps are simulated.
	•	Inverse temperature \beta: how deterministic the choices are given action values.
	•	Lapse / dropout: random-choice probability (or feature omission as a later extension).
	•	State evaluation: heuristic scoring of board states (Opheusden-style).

⸻

4. Pseudocode: Behavioral Fitting & Discrimination
```
# From Opheusden

(Heuristic evaluation + depth-limited search → action values)

FUNCTION ExtractBoardFeatures(state s):
    # Example features (customizable):
    # center control, open two-in-a-row, open three-in-a-row, immediate win/loss threats...
    return feature_vector f(s)

FUNCTION HeuristicValue(state s, weights w):
    f = ExtractBoardFeatures(s)
    return dot(w, f)

FUNCTION DepthLimitedSearch_Q(state s, depth h, weights w):
    # Returns approximate Q-values for each legal action from s
    legal_actions = GetLegalActions(s)
    INITIALIZE Q[a] = -infinity for all a in legal_actions

    # Search tree nodes store: (state, depth, root_action)
    frontier = PriorityQueue()

    FOR a in legal_actions:
        s1 = Transition(s, a)                       # apply action
        score = HeuristicValue(s1, w)
        frontier.push(node=(s1, 1, a), priority=score)
        Q[a] = max(Q[a], score)                     # initialize

    WHILE frontier not empty:
        (st, d, root_a) = frontier.pop_best()
        IF d == h:
            CONTINUE

        next_actions = GetLegalActions(st)
        FOR a2 in next_actions:
            st2 = Transition(st, a2)
            score2 = HeuristicValue(st2, w)

            # optional: pruning rule (skip if clearly poor)
            IF Prune(score2): CONTINUE

            frontier.push(node=(st2, d+1, root_a), priority=score2)

            # backup/update to root action value (simple max-backup shown)
            Q[root_a] = max(Q[root_a], score2)

    return Q
```
```
# From Mhammedi

(Treat h as an explicit multi-step factor; infer/compare h via horizon-indexed fitting)

FUNCTION SoftmaxPolicy(Q, beta):
    # pi(a) proportional to exp(beta * Q[a])
    return softmax_over_actions(beta * Q)

FUNCTION AddLapse(pi_soft, lapse):
    # mixture with uniform random
    pi_uniform = UniformOverActions()
    return (1 - lapse) * pi_soft + lapse * pi_uniform

FUNCTION LogLikelihood_Trajectory(traj, h, beta, lapse, w):
    logp = 0
    FOR each timestep t in traj:
        s_t = traj[t].state
        a_t = traj[t].action

        Q_t = DepthLimitedSearch_Q(s_t, h, w)
        pi_soft = SoftmaxPolicy(Q_t, beta)
        pi = AddLapse(pi_soft, lapse)

        logp += log(pi[a_t])
    return logp

FUNCTION FitParticipant(data_i, H={1..5}):
    best_score = -infinity
    best_params = None

    FOR h in H:
        # Optimize (beta, lapse) and optionally w under fixed h
        # Recommend: start with fixed w to isolate depth effect
        (beta_hat, lapse_hat) = Optimize(beta, lapse):
            maximize LogLikelihood_Trajectory(all_trajs_i, h, beta, lapse, w_fixed)

        score = LogLikelihood_Trajectory(all_trajs_i, h, beta_hat, lapse_hat, w_fixed)
        score -= RegularizationPenalty(beta_hat, lapse_hat)

        IF score > best_score:
            best_score = score
            best_params = (h, beta_hat, lapse_hat)

    return best_params

Discrimination availability test (novice vs expert)

PROCEDURE DiscriminationTest(dataset D, labels y):
    # y: novice/expert label per participant (or proxy like Elo threshold)

    FOR each participant i:
        params_i = FitParticipant(D_i, H={1..5})
        h_hat[i] = params_i.h
        beta_hat[i] = params_i.beta
        lapse_hat[i] = params_i.lapse

    # Primary test: is h_hat predictive of novice/expert?
    metrics = EvaluateClassifier(feature=h_hat, label=y)
        # e.g., ROC-AUC, accuracy with threshold, logistic regression

    # Minimum sanity checks (recommended even before real data)
    # - Parameter recovery on simulated agents with known h
    # - Identifiability check: ensure h_hat is not replaced by lapse/beta

    return metrics, {h_hat, beta_hat, lapse_hat}
```

⸻

5. AIRL Extension (Planning-aware AIRL)

Idea

Compare:
	•	Standard AIRL: infer reward assuming fixed/implicit planning
	•	Planning-aware AIRL: treat planning parameters (e.g., h, \beta, lapse) as latent confounders, and test whether explicitly modeling them improves reward identifiability and generative realism.

Pseudocode (high-level)

# Standard AIRL baseline
PROCEDURE StandardAIRL(expert_trajectories):
    initialize reward_network r_phi
    initialize policy pi_theta

    REPEAT until convergence:
        # Update discriminator/reward
        phi <- UpdateRewardDiscriminator(r_phi, expert_trajectories, rollouts(pi_theta))

        # Update policy to match expert under inferred reward
        theta <- RL_UpdatePolicy(pi_theta, reward=r_phi)

    return r_phi, pi_theta

# Planning-aware AIRL (bi-level sketch)
PROCEDURE PlanningAwareAIRL(expert_trajectories, H={1..5}):
    best = -infinity
    best_model = None

    FOR h in H:
        # Constrain generator policy class to use planning depth h
        initialize reward_network r_phi
        initialize planner_policy pi_theta_h  # policy generated via depth-limited planner + beta/lapse

        REPEAT until convergence:
            phi <- UpdateRewardDiscriminator(r_phi, expert_trajectories, rollouts(pi_theta_h))
            theta_h <- UpdatePlannerParameters(pi_theta_h, reward=r_phi)  # update beta/lapse or planner weights

        score = EvaluateFitAndRealism(expert_trajectories, pi_theta_h, r_phi)
        IF score > best:
            best = score
            best_model = (h, r_phi, pi_theta_h)

    return best_model

Evaluation suggestions
	•	likelihood / imitation score
	•	OOD generalization
	•	“Turing-test-style” realism (define protocol clearly)

⸻

6. Clinical & Affective Modeling

If you have operational data from different clinical populations:
	•	fit planning parameters per person: \hat h, \hat\beta, \widehat{lapse}
	•	model relationships:
clinical traits (e.g., anxiety severity) → planning parameters → behavioral patterns
	•	key deliverable: explainable individual differences via planning mechanisms, not only via reward.

⸻

7. Parametrized fMRI (Exploratory)

Two feasible routes:
	1.	Model-based fMRI: derive trial-wise regressors (value, uncertainty, conflict, planning proxy) and test neural correlates.
	2.	Individual differences: correlate subject-level parameters (\hat h,\hat\beta,\widehat{lapse}) with ROI activity/connectivity.

Goal framing:

Anxiety may influence behavior by modulating planning-related computations, which should have measurable neural signatures.

⸻

8. Positioning & Key References
	•	van Opheusden et al. (2023): expertise ↔ planning depth
	•	Mhammedi et al. (2023): multi-step inverse perspective on latent structure (used here as “explicit multi-step factor” framing)
	•	Yao et al. (2024): planning horizon as latent confounder in IRL
	•	AIRL / MaxEnt IRL: reward ambiguity, identifiability issues

Key distinction of our plan: planning is not only inferred; it is treated as a manipulable, testable mechanism that explains expertise/clinical variability and improves IRL interpretability.

⸻