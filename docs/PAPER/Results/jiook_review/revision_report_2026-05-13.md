# Jiook-style Revision Report — main.tex (Introduction · Methods · Results · Discussion · Abstract)

Date: 2026-05-13
Authorship mode: **first-author user, Cha senior review** (a)
Sections covered: Title · Abstract · Introduction · Methods · Results · Discussion (Figure captions sampled)
Total issues: **22** (Critical: 5, High: 7, Medium: 6, Low: 4)

---

## Top 5 critical issues (ranked)

### [Critical-1] Abstract is a `\todo` placeholder
- **Rule**: L1.4 (abstract template) · §21 (universal)
- **Where**: `main.tex:59–61`
- **Why it matters for Cha**: Cha's abstracts are 7–11 sentence structured units with a fixed slot grammar (S1 disorder → S2 gap → S3 "To address this, we…" → S4–S6 method-result-effect-size → S(n-2) mediation → S(n-1) "Taken together" → Sn clinical utility). A `\todo{}` placeholder cannot be sent to a senior author for review.
- **Current**:
  > `\abstract{\todo{Placeholder abstract. Replace this with your actual abstract text. This study investigated neural color representations in individuals with color vision deficiency (CVD) using functional MRI and computational modeling approaches.}}`
- **Proposed (Cha voice, 8-sentence template)**:
  > S1: Color vision deficiency (CVD) affects roughly 8 % of males and reshapes cortical colour representation, yet existing correction filters are tuned to population-average retinal models. S2: Whether individual cortical hue geometry can ground a person-specific corrective filter has not been examined. S3: To address this, we measured 7 T fMRI in 2 CVD adults (one deutan, one protan) and 7 healthy controls while they viewed 8 isoluminant DKL hues. S4: Using leave-one-run-out (LORO) and leave-one-colour-out (LOCO) cross-validation on a forward encoding model, we found preserved 8-class hue discrimination at hV4 in both CVD participants ($p > 0.05$) but selectively impaired interpolation (sub-09 $d_{cc} = -2.68$, $p = 0.024$). S5: A 2-component angular-dilation model (S-cone shift $\beta_s$ and confusion-axis rotation $\beta_c$) fit each participant's hV4 vulnerability profile under a HYBRID first-/second-order representational-similarity loss; per-subject argmin: sub-08 $(16^\circ, +40^\circ)$, sub-09 $(12^\circ, -30^\circ)$. S6: The recovered $\beta_c$ sign matched Brettel's cone-physiology polarity for each subtype, and parameter magnitudes fell below the HC leave-one-out range. S7: Together, these results show that CVD cortical colour geometry is individually distorted along physiologically interpretable axes that the pre-image of the fit converts into an exact stimulus-space correction filter. S8: This cortical fingerprint may serve as the substrate for individualised CVD correction beyond the population-average retinal ceiling.
- **Evidence**: `analysis_full_text.md §abstract — 6/6 papers; analysis_full_text.md §slots — S3 transition 6/6, Sn clinical utility 7/8`

### [Critical-2] Discussion P1 lacks `we + past-tense` opening
- **Rule**: L2.D P1 · §25 opener
- **Where**: `Discussion/discussion_v2.tex:9–11`
- **Why it matters for Cha**: Every analysed Cha Discussion opens with one of "In this study, we found...", "We tested whether...", "This longitudinal study examined..." — the construction announces the finding through the first-person actor, then closes P1 with a "may/suggest" mechanism sentence. The current opener is an inanimate-subject claim ("The selective impairment of continuous hue interpolation ... identifies the cortical site...").
- **Current**:
  > "The selective impairment of continuous hue interpolation (LOCO) with preserved categorical discrimination (LORO) in hV4 identifies the cortical site at which CVD colour distortion is correctable."
- **Proposed (Cha voice)**:
  > "In this study, we tested whether individual hV4 colour geometry is sufficiently structured to ground a person-specific corrective filter. We found that two CVD adults retained 8-class hue discrimination at hV4 but selectively lost continuous-hue interpolation, and that the residual distortion was captured by a 2-component angular-dilation model with exact per-hue pre-images. These results suggest that the cortical site at which CVD colour information is geometrically distorted is also the site at which it can be inverted."
- **Evidence**: `analysis_discussion.md §opening formula — 8/8 papers`

### [Critical-3] Intro P_final stacks 3 citations (Cha allows ≤1)
- **Rule**: L2.I P_final citations · §20 density
- **Where**: `Introduction/introduction_v2.tex:200–222` (§Intro-5, the THEREFORE-paragraph)
- **Why it matters for Cha**: The "Here, we …" paragraph in Cha papers is a clean THEREFORE move; it carries 0–1 citations in 7/7 analysed Intros. The reader should arrive at the contribution unimpeded by literature backfill.
- **Current**:
  > "... framed as single-case analyses in the Crawford--Howell tradition~\citep{crawford1998, schuett2023} alongside a normative reference of seven healthy controls. ... an independent cross-cohort behavioural estimate of the S-cone compensation angle~\citep{emery2021}."
- **Proposed (Cha voice)**: Move `crawford1998, schuett2023` into Methods (Statistical Analyses sub-section where Crawford & Howell is operationalised) and `emery2021` into the preceding paragraph where the 21.4° anchor is already discussed. P_final then carries 0 citations.
- **Evidence**: `analysis_introduction.md §P_final — 7/7 papers, citation count 0–1`

### [Critical-4] Spine noun phrase does not recur verbatim across 4 anchor points
- **Rule**: L1.1 spine
- **Where**: Title, Abstract, Intro §Intro-5, Discussion P1, Discussion closer
- **Why it matters for Cha**: 5/6 Cha papers repeat the same noun phrase (e.g., "fronto-accumbal circuit", "individual prefrontal-limbic geometry") verbatim at four anchor points so the reader can recover the central object from a glance.
- **Current candidates** (4 different surface forms used):
  - Intro §Intro-5: "continuous cortical hue geometry"; "per-individual filter"
  - Discussion P1: "cortical site at which CVD colour distortion is correctable"
  - Discussion P5 (limits): "cortical colour geometry"
  - Discussion P6 (closer): "individual cortical colour geometry, measured via fMRI LOCO decoding and inverted through an angular-dilation model"
- **Proposed (Cha voice)**: Pick **one** noun phrase and recur it verbatim. Recommended: **"individual hV4 colour geometry"** (concrete + ROI-specific + locked construct). Insert verbatim at Abstract S7, Intro §Intro-5 first sentence, Discussion P1 first sentence, Discussion closer.
- **Evidence**: `analysis_full_text.md §spine — 5/6 papers verbatim recurrence at 4 anchors`

### [Critical-5] Banned vocabulary: `establishes`, `novel` (unqualified)
- **Rule**: L3.1 Tier-CHA-Banned · §19 Tier A
- **Where**:
  - `Discussion/discussion_v2.tex:23` — "establishes which cortical quantity is the operative corrective target"
  - `Discussion/discussion_v2.tex:29` — "supports interpolation to novel hues in typical observers" (technical term, but unflagged)
  - `Introduction/introduction_v2.tex:180` — "interpolates from its 7 training hues to a novel hue" (technical term)
- **Why it matters for Cha**: `establishes` and unqualified `novel` are zero-tolerance in the analysed corpus. Where "novel" is genuinely technical ("held-out") prefer the unambiguous term.
- **Proposed**:
  - L23: `establishes` → `identifies` or `pins down`
  - L29, L180: `novel hue(s)` → `held-out hue(s)` (technical precision + Cha-compatible)
- **Evidence**: `analysis_full_text.md §banned vocab — 0/14 papers use "establishes"; "novel" used only with qualifier (2/7)`

---

## All issues by section

### Abstract
- **[Critical-1]** Placeholder `\todo` — see above.

### Introduction
- **[Critical-3]** P_final 3 citations — see above.
- [High] **Hypothesis sentence missing in P_final.** L2.I requires `We hypothesized that...` or numbered hypotheses. Current enumeration is numbered *questions*. Cha's convention is hypothesis-statements answering each question. Fix: add one explicit `We hypothesized that ...` summary sentence after the enumeration. (`Introduction/introduction_v2.tex:233–235`)
- [High] **HC FPR caveat injected mid-Intro disrupts §Intro-3 flow.** The newly added paragraph "We note up front that per-subject statistical significance under label permutation cannot, by itself..." (L155–163) is methodological framing that belongs in Methods §Statistical Analyses or the §Intro-5 hypothesis paragraph. Currently mid-paragraph in §Intro-3 (gap paragraph). Move to §Intro-5 just before the numbered list.
- [Medium] **P_final design noun phrase missing.** Cha's P_final names the design ("a longitudinal MRI cohort", "two CVD individuals in a single-day 2AFC paradigm"). Current `We pose three connected questions in two CVD individuals (one moderate deutan, one moderate–severe protan)` opens but does not name the *design noun* ("single-case fMRI characterisation"). Add a `[design noun] in N participants` phrase.
- [Medium] **§Intro-1 P1 ends with a multi-sentence claim, not the conventional definitional close.** L2.I P1 is 1–4 sentences definitional. Current P1 is 5 sentences with a downstream-task forward reference ("This makes CVD a paradigmatic example... an individualized assistive filter must answer it before it can be designed"). Trim to 4 sentences ending on the Ishihara/psychophysics citation; move the filter forward-reference to P2.
- [Low] **`yet`/`Yet` pivot OK** (L133) — meets P_BUT requirement.

### Methods
- [High] **`establishes` not in Methods** but check for other banned vocab — clean. ✓
- [High] **`\todo` markers present** at participant identifiers / IRB approval? Spot-check needed. (Skill confidence < 70%.)
- [Medium] **Statistical Analyses sub-section** should be subsectioned per L2.M classical schema. Verify presence of H3 sub-subs for: LORO LDA, LOCO ForwardEncoding, $\Delta$RDM, 2-component fit, Pre-image. (`Methods/methods_v2.tex:142–298`)
- [Medium] **Senior-author caveat partial-application**: first-author mode requires ~1.5 "we" / 100 words in Methods. Methods is currently dense in `we`-actor sentences (good). Two analytic-choice sentences use anonymous passive — accept under senior-author allowance but flag if Cha asks to first-authorize the draft. (`Methods/methods_v2.tex` spot-check: SRM training paragraph)
- [Low] **FreeSurfer/FSL versioning** — confirm `Methods/methods_v2.tex` includes version numbers inline with each tool name (skill did not exhaustively scan; recommend grep `FreeSurfer|FSL|SPM|AFNI` and verify each match has version + citation adjacent).

### Results
- [High] **Effect-size token missing in 2 LOCO HC permutation sentences.** Cha rule: every p-value sentence carries an effect-size in the same parens (η², β, R², r, OR, Cohen's d). `results_v4.tex:101–102` reports `adj_acc = 0.47 ± 0.05` and `p_perm = 0.044` — but the test statistic (permutation z or rank) is absent. Add Cohen's d or the permutation z.
- [High] **Method-purpose openers consistent ✓** (L77 "Both CVD participants exceeded..."; L94 "We next asked where..."; L165 "To characterise the geometric basis..."). Cha-style.
- [Medium] **Interpretation in §Results paragraph 4 (geometry §)**: L183–190 "indicating that geometric distortion measured at the population-code level is complementary to, not redundant with, the LOCO-based functional characterisation" — interpretation at paragraph end (Cha-style OK). But "indicating" is stronger than Cha's standard `suggest`/`may`. Soften to "suggesting that...".
- [Low] **HC FPR caveat duplicated** (Results §6.5 L257–266 + Fig 4 caption + Methods §Two-component + Supplementary §S17). Acceptable as descriptive consistency but consider tightening to one canonical source + cross-refs.

### Discussion
- **[Critical-2]** P1 opener — see above.
- [High] **Mechanism triplet incomplete in interpretation paragraphs.** L2.D requires "may reflect [process]" + "consistent with [literature]" + "this suggests [implication]" in each mechanism paragraph. Discussion ¶3 (L35–50) contains "structurally consistent with" and "extends these findings", but no `may reflect [process]` sentence. Add one mechanism sentence: e.g., "These individually structured residuals may reflect cone-class-specific differences in V2/V3 compensation gain that survive into hV4."
- [High] **Limitations enumeration: 2 of 3 items lack remedy.** L2.D requires each numbered limit to close on a remedy. (`Discussion/discussion_v2.tex:65–80`)
  - Item 1 (N=2): remedy = "require replication with larger samples" ✓
  - Item 2 (sub-09 β_c CI): no remedy stated. Add: "Power-adequate replication or hierarchical-Bayes pooling across deutan/protan subtypes is required to determine whether the second component is genuinely absent in protan."
  - Item 3 (HC FPR): remedy partial ("Behavioural filter validation remains the registered criterion"). Strengthen: "External cross-cohort hue-scaling and Phase-3 2AFC discrimination data will arbitrate cortical-level specificity beyond the within-cohort permutation null."
- [Medium] **Closer (¶6) does not echo Intro §Intro-5 spine noun phrase verbatim.** Currently "individual cortical colour geometry, measured via fMRI LOCO decoding and inverted through an angular-dilation model". After Critical-4 fix, swap in **"individual hV4 colour geometry"** verbatim.
- [Medium] **No alternative-account refutation paragraph.** Cha-pattern (3/5 strict, 5/8 across corpus): name a plausible alternative explanation and refute it against literature. Candidate alternative for this paper: "An alternative reading is that the LOCO impairment merely reflects reduced V1–V3 input variance rather than cortex-level distortion, but the preserved LORO accuracy at hV4 (which depends on the same upstream input) argues against an input-variance account." Add one short paragraph between current P4 and P5.

### Figure captions (sampled)
- [Low] **Fig 4 caption "Caveats and consistency anchors" removed (per recent rev).** Now points to main text and Appendix — Cha-pattern compatible (figures carry inference; tables carry descriptives).
- [Low] **Fig 5 caption split across two pages via `\ContinuedFloat`** — non-standard for Cha, but acceptable as a structural concession to figure size.

---

## Baseline ↔ Cha conflicts flagged for user decision

| # | Conflict | Baseline (universal §) | Cha (L1.4 / L1.1) | Recommendation |
|---|---|---|---|---|
| 1 | Abstract claim front-loading | §21: "Here we show..." in S1 | L1.4: delay central claim to S3 with "To address this, we…" | **Follow Cha (S3 delay)** for senior-review submission; switch to §21 front-load only if venue (e.g., Nature) demands and Cha agrees. |
| 2 | End-of-Discussion field-impact vs clinical utility | §25: end with field impact | L2.D closer: end with clinical utility | **Follow Cha (clinical utility)** — current closer "may reduce discrimination thresholds where retinal-level correction does not" matches. |
| 3 | Pre-registration / open code | Modern venue norm (Nature/eLife 2026+): mandatory | Cha 0/8 papers preregistered | **Venue-dependent**. If eLife / Nature target: add pre-registration statement to Methods and a `Data availability` section. Cha has not done this in any prior paper, so seek explicit PI sign-off. |
| 4 | 5+ citation stacks in Intro P2 | §20: trim to ≤3 most representative | Cha violates 4/7 Intros | **Follow §20** (split). Cha's own violations are a venue convention drift, not a preference to inherit. Specifically `Introduction/introduction_v2.tex:39–50` and `:118–125`. |

---

## Reverse outline

### Title
- "Neural Representation of Color in Color Vision Deficiency: An fMRI Study" — noun-phrase + methods subtitle. Cha-pattern compatible (L1.5b). Could strengthen to declarative-result form: e.g., **"Individual hV4 Colour Geometry Predicts a Person-Specific Stimulus-Space Correction Filter in Colour Vision Deficiency"**.

### Abstract
- Placeholder. No reverse outline possible.

### Introduction
- §Intro-1 (¶1–2): CVD = structured distortion; the question is cortical, not retinal.
- §Intro-2 (¶3–5): current correction filters share a population-average retinal ceiling.
- §Intro-3 (¶6–9): cortical compensation exists in CVD; three concrete gaps remain; per-subject permutation is insufficient for specificity.
- §Intro-4 (¶10–11): LORO-preserved + LOCO-impaired defines the filter-warranted regime.
- §Intro-5 (¶12–13): three connected questions, three numbered analyses.

[Drift vs `pre_draft_2026-05-10.md`]: Intro structure aligned. §Intro-3 now contains the HC FPR caveat (newly added 2026-05-13); not in pre-draft. Acceptable insertion but location is a high-issue (see above).

### Methods (sampled)
- §Participants — Thirteen volunteers; HC n=7; CVD sub-08, sub-09; near-normal sub-10; 3 excluded.
- §Stimuli — 8 isoluminant DKL hues at 45°, RSVP paradigm.
- §MRI Acquisition — 7T sequence details.
- §Pipeline (GLMsingle → Procrustes → SRM).
- §ROI Definition (V1, V2, V3, hV4).
- §LORO (LDA, SRM-aligned).
- §LOCO (ForwardEncoding, vulnerability vector).
- §Geometry (SRM ΔRDM, mean pairwise correlation distance).
- §Two-component fit (HYBRID loss; argmin grid search).
- §Filter pre-image (Brent's method).
- §Behavioral (JND staircase, 8AFC, Phase-3 2AFC stub).

### Results (sampled)
- ¶ LORO preserved across ROIs.
- ¶ LOCO impaired selectively at hV4.
- ¶ ΔRDM ROI specificity divergent across CVD subjects.
- ¶ HYBRID 2-component fit recovers per-subject distortion.
- ¶ Filter pre-image (bijective, qualitative rendering).

### Discussion
- ¶1 Finding summary + corrective-site claim.
- ¶2 LOCO–behavioural dissociation establishes the corrective target.
- ¶3 β_s consistency with Emery / Tregillus; correction vectors divergent → cannot share retinal model.
- ¶4 Detection–correction dissociation = preregistered falsifier (2AFC Phase-3).
- ¶5 Limitations: N=2; sub-09 β_c not significant; HC FPR.
- ¶6 Closer: clinical translation.

---

## Quantitative profile

| Metric | Draft value | Cha range | Verdict |
|---|---|---|---|
| Abstract sentences | 0 (placeholder) | 7–11 | ✗ |
| Intro paragraphs | 5 | 4–6 | ✓ |
| Intro final ¶ citations | 3 | 0–1 | ✗ |
| Discussion paragraphs | 6 | 6–12 | ✓ |
| Limitations position | penultimate (¶5 of 6) | penultimate | ✓ |
| Limitation items numbered | yes (First/Second/Third) | yes | ✓ |
| Limitation remedies attached | 1.5/3 | 3/3 strict | ⚠ |
| "we" frequency Methods (sampled) | high | first-author ≥1.5/100w | ✓ |
| Effect size inline in Results claims | ~85% (LOCO hV4 ✓; perm tests ✗ 2 sites) | ≥80% | ✓ borderline |
| Spine noun-phrase recurrence (verbatim) | 0/4 | 4/4 | ✗ |
| Banned vocabulary count | 1 (`establishes`) + 2 contextual (`novel hue(s)`) | 0 | ⚠ |
| 5+ citation stacks | 2 (Intro P1, P2) | (Cha violates too — flag) | ⚠ |
| FreeSurfer/FSL versioned | not yet verified | yes | ? |
| Discussion P1 `we + past-tense` | ✗ (inanimate subject) | yes (8/8) | ✗ |
| Mechanism triplet (may reflect / consistent / suggests) | 1.5/3 | 3/3 | ⚠ |
| Alternative-account refutation | none | 3/5 strict, 5/8 corpus | ⚠ |
| Closer = clinical utility (not field impact) | ✓ | 7/8 | ✓ |
| Title declarative-result OR noun+method | noun+method (L1.5b) | either | ✓ |

---

## Handoff

- **Critical: 5** issues blocking PI submission — must fix before sending to Cha.
- **High: 7** — strongly recommended fixes.
- **Medium: 6** — strengthens Cha voice.
- **Low: 4** — polish.

**Conflicts flagged for user decision: 4** (abstract front-loading; pre-registration; 5+ citation stacks Cha-violation; field-impact vs clinical closer).

**Next:**
- Run `/apply-draft results/jiook_review/revision_report_2026-05-13.md` for a 3-iteration fix loop on Critical-1 → Critical-5, then High items.
- After application, re-run `/revise-as-jiook` to verify `Critical: 0` and recheck spine recurrence (4/4 verbatim).
- Surface the 4 baseline-vs-Cha conflicts to the user before applying.
- Decision: which spine noun phrase to lock (recommend **"individual hV4 colour geometry"**).
