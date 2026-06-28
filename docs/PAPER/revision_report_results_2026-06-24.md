# Revision Report — Results (results_v4.tex)

- **Target**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/PAPER/Results/results_v4.tex`
- **Rules**: `~/.claude/writing/academic_writing_rules.md` (§7, §9, §11, §19, §20, §24, §26)
- **Date**: 2026-06-24
- **Mode**: report only — no edits applied.

Severity legend: **Fatal** (blocks submission / wrong-or-unanchored number / overclaim) · **Serious** (reviewer will flag) · **Minor** (polish).

---

## 1. Reverse outline (one sentence per paragraph, as written)

| § / line | Paragraph (as written) | Role | Flag |
|---|---|---|---|
| L29 | Filter validity requires retained discrimination; we verified via LORO. | motivation+method | OK (CCC opener) |
| L31 | Both CVD cases exceed chance at every ROI; cross-subject and within-ROI tests show no HC–CVD difference; stimuli are distinguishable. | result | **two-role**: observation + interpretation ("therefore individually distinguishable") + lit cite fused (§9) |
| L38 | hV4 alone supports above-chance HC interpolation; V1–V3 do not. | result | OK |
| L40 | Both CVD cases fall at/below chance at hV4; failure concentrates on S-cone hues; per-hue tests; defines vulnerability profile $\mathbf v$. | result | **two-role**: group LOCO result + per-hue exploratory result + construct definition ($\mathbf v$). Split candidate (§7) |
| L62 | We compared CVD–HC pairwise structure; computed disparity and ΔRDM. | method | OK |
| L64 | Elevated-disparity ROI differs by case (V2 deutan / V1 protan); reports both estimators. | result | OK |
| L66 | ΔRDM heatmaps show subject-specific distortion; disparity vs ΔRDM distinguished; distortion is "independent evidence". | result+interpretation | **two-role** (§9): observation + interpretive claim in one paragraph |
| L87–89 | R+C insufficient for both, by different evidence per case. | result | OK |
| L91 | $g>2$ contradicts confirmed CVD status → boundary is model failure. | interpretation | OK (argument paragraph) |
| L93 | Structural cause = DoF deficit; R+C excluded. | interpretation | OK |
| L100 | 2-component fits both with same form; differ in $(\hat\beta_s,\hat\beta_c)$. | result | OK (topic sentence good) |
| L102 | Deutan fit, held-out loss, IQR, LOO sign stability. | result | OK |
| L104–106 | Protan fit, near-tie among cells, metric-dependence caveat. | result | OK |
| L108 | LOCO did not enter either winning combination. | result | OK |
| L110 | RDM atom ROI matches disparity ROI; procedures distinct. | result+interpretation | borderline (§9) |
| L112–113 | Held-out folds beat baseline; fits reach 52%/67% of noise ceiling. | result | OK |
| L121 | Independent fitting reveals three benefits of the neural component. | result preview | OK |
| L123 | First benefit: neural term captures protan direction behavior cannot. | result | OK |
| L125–126 | Second benefit: neural term stabilizes deutan argmin. | result | OK |
| L128 | Third benefit: neural term reduces IQR in both. | result | OK |
| L134 | Mechanism class recoverable, per-axis magnitude not; 0/6 checks. | result | OK |
| L136 | Sign of $\hat\beta_c$ stable; direction recoverable, magnitude not. | result | OK |
| L138–140 | Loss landscape localizes the magnitude indeterminacy. | result | OK |
| L159 | Filter = pre-image of fitted transform. | method/result | OK |
| L161 | Deutan filter: mean $|\delta\theta|=26.3°$. | result | OK |
| L163 | Protan filter: mean $|\delta\theta|=16.2°$. | result | OK |
| L165 | The two fits differ in dominant-axis magnitude and direction. | result | OK |
| L187 | Neural eval: personalized > deployed forward-tuning in all ROIs; robustness; V1 caveat. | result | **two-role / overlong**: contrast result + robustness + per-ROI breakdown + V1-attenuation interpretation in one paragraph (§7) |
| L207 | LORO preserved by both filters; LOCO restored only by personalized; geometry not restored by either. | result | **two-role / overlong** (§7): three distinct readouts (LORO, LOCO, SRM/RDM) packed in one paragraph |
| L210 | Behavioral: both filters eliminate JND deficit; cannot be ranked; advantage confined to neural contrast. | result+interpretation | OK but dense |

**Drift vs pre-draft outline (§1 step 5)**: The pre-draft ¶D claim "LOCO impairment matched behavioral JND confusion 100%, SRM z 33%" is **absent** from results_v4 (correctly — MEMORY marks it SUPERSEDED). No drift problem; just noting the outline no longer matches and the reverse outline reflects the newer structure. Pre-draft Fig-count (6) ≠ draft Fig-count (8); pre-draft is stale, not a draft defect.

---

## 2. §19 Vocabulary scan (Tier A/B/C/D)

| Line | Tier | Quote | Issue | Suggested fix |
|---|---|---|---|---|
| L125 | **C** | "the neural-only fit independently corroborates this direction with a **meaningful estimate** ($\hat\beta_c = -26^\circ$)" | "meaningful" unoperationalized (§19 Tier C). | State criterion: "$\hat\beta_c=-26^\circ$, same sign as the combined fit" — replace "meaningful" with the actual concordance fact. |
| L31 | C | "showed **no HC--CVD difference** ... $p=0.668$" | Acceptable — null is anchored with test + p. Listed only to confirm filter pass. | none (false positive) |
| L187 | C | "The contrast was **robust**: the personalized condition remained more HC-like after dropping any single run..." | "robust" — but it IS operationalized inline (LORO drop + voxel re-extraction). | Borderline OK; tighten to "held under two perturbations (single-run drop; baseline voxel set)". |
| L106 | C | "this **stability** is specific to the PCA-basis loss" | "stability" operationalized earlier (IQR=0). | OK (false positive) |
| L136 | C | "the sign ... is **stable** across held-out reference sets" | operationalized (all LOO folds same sign). | OK |
| L31, L52, L40, L50 | C | "**significant** / reached **significance**" (per-hue, disparity) | All carry p-values/test name → statistics-context. | OK (false positives, §19 allows with p) |
| L210 | B/C | "Both filters **worked**" | colloquial, untestable verb. | "Both filters eliminated the baseline JND deficit ($|z|$: 2.24 → 0.85 / 0.78)". |
| L66, L93, L100 | — | "structurally insufficient", "structural cause", "model structure" | technical use, defined. | OK |

**Tier A (overclaim) scan**: No "first / novel / proves / always / never / outperforms / state-of-the-art / comprehensive" found. **Pass.** Note L88 "rejecting the model as misspecified" and L93 "R+C is therefore excluded" are bounded by stated gates → acceptable, not Tier A. Guardrail (no specificity claim) is respected — L150 and L177 explicitly mark fits as "descriptive ... not physiological point estimates."

---

## 3. §20 Citation audit

| Line | Cite | Claim | Verdict |
|---|---|---|---|
| L31 | `\cite{boehm2014, bosten2019}` | "in line with prior work on CVD above-threshold identification" | OK — general domain statement, two sources, not over-stacked. |
| L38 | `\citeA{brouwer2009}` | "hV4 as the primary interpolation gate, replicating" | **suspect (specificity/strength)**: "replicating" is strong for n=6 HC + single result. MEMORY literature-framing warns Brouwer & Heeger DID perform LOCO and novel-color reconstruction was in V4/VO1 — so the cite is correct in spirit, but "replicating" should be softened to "consistent with" per §19 (`proves`→`is consistent with` family). Primary paper for specific empirical claim = correct source type. |
| L88 | `\cite{wilson2019}` | "rejecting the model as misspecified" | **suspect**: confirm Wilson 2019 is a model-selection/misspecification methods reference, not a CVD paper. If it is a generic "model misspecification" cite, ensure it actually supports a boundary-saturation rejection rule (§20 self-check: supports vs illustrates). |
| L113 | `\cite{lagecastellanos2018}` | noise-ceiling from split-half HC reliability | **suspect**: verify this is the noise-ceiling/split-half-reliability method origin (method-origin → original paper, §20). If it is a downstream application, find the original. |

No 5+ citation stacks. Citation density is appropriately low for a Results section.

---

## 4. §26 Checklist (Results-applicable rows)

| Checklist item | Status | Evidence |
|---|---|---|
| Reverse outline narrates section | **Pass** | §1 above reads as a coherent functional→geometric→model→filter→validation arc. |
| No paragraph needs 2 sentences to summarize (§7) | **Fail** | L40, L66, L187, L207 are two-role (see §1). |
| Every numeric Δ has baseline + metric + dataset (§11) | **Fail** | Multiple (see §5 below). |
| Every "first/only/no X" cites review or removed (§19A) | **Pass** | none present. |
| Every untestable verb replaced (§19B) | **Fail (minor)** | L210 "worked". |
| Every vague adjective operationalized (§19C) | **Fail (minor)** | L125 "meaningful". |
| No self-praise (§19D) | **Pass** | — |
| Each result answers a prior question (§24) | **Partial** | L29/L38/L62/L100 each open with the question. L117–L121 "three benefits" reads as method-internal justification, not a reader-question raised in Intro; verify the Intro/§22 poses "what does the neural term add over behavior?" — else this subsection answers an un-asked question. **Flag for §24.** |
| First sentence = topic sentence (§8) | **Pass** | all subsections lead with the claim. |
| Pronouns unambiguous (§3) | **Pass (1 watch)** | L207 "only the personalized filter preserved how those hues interpolate" — "those hues" antecedent ("which hues were present") is OK. |
| Terminology consistent (§4) | **Fail (minor)** | "hV4" vs "V4" (L102, L104 RDM atom "V2"/"V1" fine, but L161/L163 use $|\delta\theta|$ while L187+ neural eval uses "$\rho$"/"forward-tuning correlation" for a related-but-different quantity; ensure reader knows LOCO-ρ (eval) ≠ adjacent-accuracy (discovery)). See §5. |
| Observation/interpretation/implication separated (§9) | **Fail** | L31, L66, L110 fuse observation + interpretation. |
| Figures self-contained, caption states takeaway (§13) | **Pass** | captions L46–53, L72–78, L146–150, L171–177, L192–203 all state takeaways. |

---

## 5. §11 + numeric-consistency scan (every statistic, with line)

> Per task: flagged for the user, **not** verified against source data. "X-ref" = cross-document inconsistency to resolve.

### 5a. §11 anchoring violations (baseline / metric / dataset missing)

| Line | Statistic | Missing element | Severity |
|---|---|---|---|
| L40 | "adjacent accuracy $0.47\pm0.05$ ... $n=6$ HC ... $p=0.044$ under $8!$ permutations" | **Anchored** (metric, n, test). OK. | — |
| L40 | deutan "adjacent accuracy $0.25$ ... $p=0.082$, $d_{cc}=-1.71$"; protan "$0.13$ ... $p=0.024$, $d_{cc}=-2.68$" | Baseline present (HC 0.47; chance 3/8). **OK** but the body text says "at or below the adjacent-accuracy chance level" — chance = 3/8 = 0.375; 0.25 and 0.13 are **below**, not "at or below". Minor wording. | Minor |
| L89 | protan R+C "$\overline{L}_{\rm test}=-0.86$ vs $-1.54$" | Metric (held-out composite loss) + comparison present. **OK.** | — |
| L102 | deutan "$\overline{L}_{\rm test}=-2.36$ (IQR $=2.15$)" vs competing "$-1.14$" | OK. | — |
| L104 | protan "$-1.54$ ... nearly tied ... $-1.52$" vs R+C "$-0.86$" | OK. | — |
| L112 | "ranking in the top $5$--$8\%$ of grid combinations" | **§11 Fail**: "top 5–8%" — of how many grid cells? per participant or pooled? metric for ranking (held-out loss?) not stated inline. | **Serious** |
| L113 | "reached $52\%$ (deutan) and $67\%$ (protan) of the way from baseline to ceiling" | baseline + ceiling both defined inline. **OK** (good example). | — |
| L126 | "reduced the boundary saturation rate from $23\%$ to $9.3\%$" | baseline + after present; dataset (resamples) implied. **OK.** | — |
| L128 | IQR reductions "$(18°,6°)$ to $(8°,2°)$ (PCA) and $(10°,4°)$ (SRM)"; protan "$(6°,4°)$ to $(0°,0°)$" | **OK** (before/after, basis labeled). | — |
| L134 | "$f_{10°}<0.30$"; "uncertainty $\sim20°$--$25°$"; "$|\hat\beta_c|=42°$ ... deviates ... by $4.7°$" | metric defined in Supp; **OK** with forward-ref. | — |
| L161/L163 | mean $|\delta\theta|=26.3°$ (deutan), $16.2°$ (protan) | metric defined (L159 pre-image). **OK.** | — |
| L187 | personalized $\rho$: V1 +0.21 ... deployed $\rho$: V1 −0.32 ...; "$\Delta\rho=0.37$--$0.57$" | metric = LOCO forward-tuning correlation; **but** baseline reference (HC ρ, no-filter ρ) not given inline for the four ρ values — only deployed vs personalized contrast. §11 wants the HC/no-filter anchor. | **Serious** |
| L187 | "V1's larger native effect ($d=+0.97$) attenuated under voxel matching ($d=-0.82$)" | $d$ relative to what distribution? (HC SD, presumably). State reference. | Minor |
| L207 | "$\approx0.69$--$0.72$ at V1; HC $0.71$ ... above $0.125$ chance"; "V1 adjacent $0.41$, HC $0.40$; exact $0.34$ vs HC $0.28$"; "deployed V1 adjacent $0.22$, chance $0.375$" | **Well-anchored** (HC + chance both present). Good. | — |
| L210 | JND "$|z|=2.24$" → deployed "$0.85$" / personalized "$0.78$"; 8AFC "$0.81$ → $0.97$"; Wilcoxon $p=0.84$ | baseline + after present; HC reference for $|z|$ implied (z is already HC-relative). **OK.** | — |

### 5b. Internal & cross-document consistency flags

| Line(s) | Issue | Action |
|---|---|---|
| L52 / L40 (blue per-hue) | Draft: blue "**both participants $d=2.20$, $p=0.042$**" (identical d for both). Pre-draft (`pre_draft_2026-05-10.md` L39): blue sub-08 $d=2.13, p=0.047$; sub-09 $d=2.15, p=0.046$ (**different** per participant). **X-ref inconsistency** — identical $d=2.20$ for two different participants is statistically implausible unless intentionally pooled; pre-draft (older 13-bin?) numbers differ. | **Fatal** — reconcile against current source `loco_reinforcement/per_color_breakdown.json` (9-bin `c3_relabel_p2a`, post-2026-05-16). Confirm whether 2.20 is a re-pooled value or a typo. MEMORY `feedback_label_scheme_cutoff` warns pre-2026-05-16 numbers use OLD scheme. |
| L40 vs L52 | purple "$d=1.02$, $p=0.19$" and magenta "$d=1.89$, $p=0.064$" appear **identically** in both body (L40) and caption (L52) — consistent within draft. Pre-draft had purple sub-08 $d=2.40, p=0.033$ (different). | Verify against current source; pre-draft superseded. |
| L161/L163 vs pre-draft L41 | Draft mean $|\delta|$: deutan **26.3°**, protan **16.2°**. Pre-draft: sub-08 **46.3°**, sub-09 **20.1°**. Draft matches project CLAUDE.md canonical (|δ|=26.3/16.2) and current argmins (6,−42)/(2,+24). Pre-draft uses the **superseded** (44°,+28°)/(30°,+46°) framework. | **No defect** — draft is the current canonical. Listed so the user doesn't "correct" the draft back to stale pre-draft numbers. |
| L102/L148/L161/L173 | Deutan $(\hat\beta_s,\hat\beta_c)=(6°,-42°)$ used consistently across body, Fig 6 caption, Fig 7 caption. **Consistent.** | OK |
| L104/L148/L163/L174 | Protan $(2°,+24°)$ consistent across body + both captions. **Consistent.** | OK |
| L125 vs L128 | Deutan neural-only $\hat\beta_c=-26°$ (L125). Saturation "$23\%$ to $9.3\%$" (L126). Two different deutan IQR-baselines appear: L128 says combined-fit reduces IQR "from $(18°,6°)$" while L102 reports the **adopted** HC-resample IQR as $(8°,2°)$. Consistent (before vs after). | OK — confirm $(18°,6°)$ is the behavioral-only baseline. |
| L66 / L76 / L110 | Disparity p-values consistent across body + caption + 2-comp section: protan V1 common-space $p=0.007$, LOSO $p=0.045$; deutan V2 $p=0.040$, LOSO $p=0.116$. **Internally consistent** (3 occurrences agree). | OK |
| L38 vs L40 | hV4 HC interpolation: body L38 "adjacent accuracy $0.47\pm0.05$ ... $p=0.044$". Pre-draft abstract numbers (L39) cite "ρ=0.42±0.14" — **different metric** (ρ vs adjacent accuracy). Draft header comment (L8) documents the metric switch ρ→adj_acc. | **No defect** in draft; flag only so abstract/intro (drafted later) use adj_acc, not the stale ρ=0.42. |
| L31 | "21 HC-to-HC vs 14 HC-to-CVD pairs" — with n=7 HC, HC-to-HC ordered pairs = 7×6=42 or unordered C(7,2)=21; HC-to-CVD = 7×2=14. **21 + 14 internally coherent** if HC-HC is unordered and HC-CVD counts both CVD ×7 HC. | OK (consistent) |
| L40 / Fig caption L49 | Chance levels: LORO chance = 1/8 = 0.125 (L31/L48). LOCO **adjacent** chance stated as **3/8** at L49/L52 body, but **$3/8 = 0.375$** — consistent. However L134-area and L207 use "chance $0.375$" and L207 also "chance $0.375$ (V1 adjacent)". **Consistent.** | OK |
| L207 | "exact $0.34$ vs HC $0.28$" — personalized exact accuracy (0.34) **exceeds** HC (0.28). For a "restores to HC level" claim, personalized > HC is fine, but note it is *above*, not *at*, HC; phrasing "returned to the HC level" slightly undersells/obscures. | Minor |

---

## 6. §24 — does each result answer a prior question?

- L29 (LORO) → answers "is color information retained?" (filter precondition). **Yes**, explicit.
- L38/L40 (LOCO) → answers "is interpolation impaired?" **Yes.**
- L62 (geometry) → "what is the geometric basis?" **Yes**, explicit ("To characterize the geometric basis...").
- L87 (R+C insufficient) → answers "can a retinal-only model explain it?" **Yes** (implicitly raised by mechanism question).
- L100 (2-component) → "what model fits?" **Yes.**
- L117 "Neural data identifies what behavior cannot" → **Weak link (§24)**: this answers a question that should be posed in Intro/Discussion ("why include neural loss at all?"). Confirm §22 raises it; otherwise this subsection answers an un-asked question and reads as internal methods justification inside Results.
- L130 (identifiability) → answers the reviewer-anticipated "are these parameters recoverable?" — good defensive §24/§14 move.
- L155/L182 (filter + eval) → "does the derived filter work?" **Yes.**

---

## Summary

- **Fatal: 1** — L40/L52 per-hue blue $d=2.20$ identical for both participants and inconsistent with pre-draft per-participant values; reconcile against current 9-bin source (label-scheme cutoff applies).
- **Serious: 4** — L112 "top 5–8%" unanchored (§11); L187 four ρ values lack HC/no-filter inline baseline (§11); two-role/overlong paragraphs L187 and L207 (§7); §24 weak link at L117 subsection (answers possibly un-asked question).
- **Minor: ~8** — L125 "meaningful" (§19C); L210 "worked" (§19B); L38 "replicating"→"consistent with"; L40 "at or below chance" wording; §9 fusions at L31/L66/L110; metric label LOCO-ρ vs adjacent-accuracy disambiguation; L207 "returned to HC level" while actually above HC.
- **Citations suspect: 3** — `wilson2019` (L88), `lagecastellanos2018` (L113), `brouwer2009` strength (L38).
- **Guardrails**: anti-overstatement and no-specificity-claim **respected** (L150/L177 descriptive disclaimers present). Draft canonical numbers (6,−42)/(2,+24), |δ|=26.3/16.2 match current project canon; pre-draft figures (44/28, 30/46, |δ| 46.3/20.1, ρ=0.42) are **superseded** — do not revert.
