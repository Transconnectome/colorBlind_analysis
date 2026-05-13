# Revision Report — Methods — 2026-05-13

Target: `docs/PAPER/Methods/methods_v2.tex` (312 lines)
Rules: §2–§18, §19, §20, §23, §26
Pre-draft outline: `docs/PAPER/pre_draft_2026-05-10.md` §5 Methods

## 1. Reverse outline

The file has 11 `\subsection`s (3 more than the intended 8-paragraph outline).

- §Participants (L17–28): Recruitment, Ishihara screening, classification of HC n=7 / CVD sub-08 deutan / sub-09 protan / sub-10 control. [intended ¶1 — match Y, but see §4 fatal N-count]
- §Stimuli and task (L35–54): 8 isoluminant CIELab hues, RSVP, six 7-min runs, PsychoPy version; second-session filter design described. [intended ¶1 partial — match Y; second session = forward reference to filter eval]
- §MRI acquisition and preprocessing (L61–71): 3T, 24 oblique slices, BIDS+ezBIDS, FreeSurfer coreg, FSL FLIRT+FNIRT. [NOT in intended outline — added scaffolding, acceptable]
- §ROI definition and response estimation (L78–97): Wang atlas ROI + voxel counts, two-stage GLM with FIR-derived HRF, within-subject Procrustes alignment. [intended ¶2 — match PARTIAL; outline says GLMsingle, file says two-stage GLM]
- §Shared Response Model (L104–120): SRM definition, HC-only training, CVD projection by Procrustes, K values per ROI. [intended ¶3 — match Y]
- §LORO (L127–140): LDA discriminant decoder, acc_exact, group HC–CVD via Mann-Whitney + Crawford & Howell. [NOT in intended outline — but matches Results order]
- §LOCO and vulnerability profile (L147–174): forward encoding model, adj_acc, hue vulnerability profile v, Crawford-Howell+Hedges'd. [intended ¶4 — match Y]
- §ΔRDM and disparity (L181–210): RDM construction, LOO disparity, ΔRDM permutation. [intended ¶5 — match Y]
- §Two-component model (L217–248): δθ equation, β_s/β_c grounding, 26×51 grid search, 40,320 permutations. [intended ¶6 — match Y]
- §Stimulus-space filter (L255–271): pre-image computation via Brent's method, bijectivity verification. [intended ¶7 — match Y, but L270 leaks result]
- §Behavioral concordance (L281–299): JND staircases, 8AFC. [intended ¶8 — match Y, but PENDING flag in outline absent from file]
- §Reproducibility (L306–312): software versions, seeds, code/data availability. [NOT in intended outline — acceptable closing]

### Drift vs intended outline
1. **GLMsingle drift**: Outline ¶2 says "GLMsingle single-trial amplitudes"; file L83–91 describes a two-stage FIR+ridge GLM. The file is internally consistent (no Prince 2022 cited), but is not GLMsingle as planned. Confirm which is canonical.
2. **DKL vs CIELab drift**: Outline says "8 equiluminant DKL hues"; file L35–37 says "CIE L*a*b* space". Project CLAUDE.md §10 also says DKL. These are different color spaces metrically.
3. **¶8 PENDING flag**: Outline marks behavioral ¶8 as [PENDING Phase 3]; file presents it as completed methodology (L278–294). Flag mismatch with project status (no Fig 6 results yet).

## 2. §19 Vocabulary scan

### Tier A (1)
- L235 — "Parameters were estimated by **exhaustive grid search**" — defensible (1,326 evaluated points IS exhaustive over the stated grid). KEEP, but consider "exhaustive over 26×51 grid" for precision.

### Tier B (0)
- L25 "Three additional participants were **excluded**" — concrete verb, OK.
- No instances of `study`, `explore`, `investigate`, `examine` in problematic senses.

### Tier C (3)
- L173 "small-$n$ comparisons" — `small` not operationalized. Replace with "n=7 HC reference distribution" or similar.
- L209 "A **significant** pairwise-disparity finding does not imply a **significant** ΔRDM result" — `significant` here is descriptive of test outcomes, but the sentence is conceptual; OK in context (test+threshold defined upstream at L192, L203).
- L247 "(i) **permutation-significant** fit" — compound coined locally; tolerable but acceptable to specify "p<0.05 under 40,320-permutation null".

### Tier D (0)
- No `elegant`, `principled`, `clean`, `unified`, `surprising`. Clean pass.

### Filler scan (0)
- No `in order to`, `due to the fact that`, `it is worth noting`. Clean pass.

## 3. §20 Citation audit

### Method-origin issues (3 missing)
- L130 — "shrinkage regularisation" used in LDA → **MISSING** Ledoit-Wolf citation (Ledoit & Wolf 2004, *J Multivar Anal*).
- L148 — "forward encoding model (ForwardEncoding)" → **MISSING** method-origin cite. The Brouwer & Heeger 2009 cite is already used at L42 (RSVP) and L84 (GLM); it belongs here (channel-encoding forward model).
- L173 — "Hedges' $d$ with the Crawford–Howell correction" → **MISSING** Hedges 1981 or Hedges & Olkin 1985 cite for d.

Also flagged: L83 "two-stage GLM" cites `dale1999, brouwer2009, brouwer2013` — none of these is the GLMsingle origin. If the intended pipeline is GLMsingle, add Prince et al. 2022, *J Neurophysiol*. If the file's two-stage method is canonical, this stack is acceptable.

### General-claim ↔ specific-cite mismatches
- L37 `\cite{cie1986}` for CIE L*a*b* — textbook-level fact, single foundational ref OK.
- L42 `\cite{brouwer2009}` for "Rapid Serial Visual Presentation (RSVP) design" — RSVP is not Brouwer & Heeger's contribution; it predates them. Cite an RSVP-origin paper (Potter & Levy 1969) or remove the cite and treat as standard.

### 5+ citation stacks
- None. Largest stack: 3 (L84 `dale1999, brouwer2009, brouwer2013`). Acceptable.

### Other
- L94 `\cite{gower1975}` for Procrustes — correct method-origin.
- L105 `\citeNP{chen2015, haxby2011, guntupalli2016}` for SRM — chen2015 is origin; haxby2011 + guntupalli2016 are hyperalignment relatives, not SRM specifically. Either trim to chen2015 only or specify the role of each.

## 4. §23 Methods-specific issues

### Fatal — Participants N inconsistency
- **L17–26: "Twelve volunteers were recruited"** but breakdown sums to **13**: HC n=7 (L21) + sub-08 (L23) + sub-09 (L23) + sub-10 (L24) + 3 excluded (L25) = 13. The opening sentence is off by one. Either change "Twelve" → "Thirteen", or reclassify one of the categories.

### Results-in-Methods leakage (Serious × 2)
- **L268–271**: "this occurred for the Machado model for sub-09 (3 of 8 hues; Figure~\ref{fig:filter}B) but not for the 2-component model" — empirical result; move to Results §Filter. §23 explicit: "State what was done, not what happened."
- **L299**: "Same-day performance confirmed Ishihara classifications (reported in Section~\ref{sec:results:participants})" — both (a) smuggles a result ("confirmed") and (b) forward-references Results §sec:results:participants. Replace with method-only statement, e.g., "Identifications were compared to Ishihara classifications post-hoc."

### Forward references to Results
- L299 (above) — only Results-section forward reference. L167, L299 reference Methods subsections (`sec:methods:filter`, etc.) — those are internal back/forward refs within Methods, acceptable.

### Order vs Results mismatch
- Results §1 = Participants; Methods §1 = Participants. ✓
- Results §2 = LORO (preserved discrimination); Methods §LORO at L127. ✓
- Results §3 = LOCO (interpolation impaired); Methods §LOCO at L147. ✓
- Results §4 = RDM geometry; Methods §RDM at L181. ✓
- Results §5 = 2-component; Methods §2-comp at L217. ✓
- Results §6 = Filter; Methods §Filter at L255. ✓
- §Behavioral concordance (L281) has no Results counterpart yet (Fig 6 PENDING per outline). PENDING flag should be retained in a comment.

### Undefined variables / abbreviations (Serious)
- **L118–119**: "leave-one-subject-out cross-validated **LOCO** performance" — LOCO acronym used 24 lines before its definition at L143–147. §23: "Define every variable before its later use." Add brief gloss at L118 ("…leave-one-color-out, see §\ref{sec:methods:loco}") or define LOCO at first occurrence.
- L107: "$W_i \in \mathbb{R}^{V \times k}$" introduces `V` (voxels) and `k` (latent dim) — `V` not defined verbally; `k` later equated to "Reduced dimensions" (L118). Add inline gloss ("V voxels, k latent dimensions").
- L165: "$\mathbf{v} \in [0,1]^8$" — defined inline ("hue vulnerability profile"). ✓
- L226: `h` (opponent-hue angle), `\theta_conf` defined immediately. ✓
- L258: $\theta_k$, $\tilde\theta_k$ defined inline. ✓
- ρ / Spearman ρ: L168, L201, L239 — defined inline as "Spearman ρ". ✓
- LORO defined at L127 first use. ✓
- ROI used at L82 first ("each participant's BOLD brain mask"); abbreviation never expanded. Spell "region of interest (ROI)" at first use.
- HRF defined at L84–85. ✓ FIR defined at L85. ✓ DOF, BIDS not expanded (BIDS L66, DOF L69).

### Software versions reported
- **Reported**: PsychoPy 2022.2.5 (L49); Python 3.10, numpy 1.24.3, scipy 1.11.3, scikit-learn 1.3.0, BrainIAK 0.11 (L306–307). ✓
- **Missing versions** (Minor): FreeSurfer (L68), FSL FLIRT/FNIRT (L69), ezBIDS (L66), Neurodesign (L44), nilearn (not mentioned but Memory says it's used). Add explicit version numbers.
- BrainIAK MPI note (`mpirun -np 1`) from project CLAUDE.md §9 absent — not strictly required in Methods, but flag for Reproducibility appendix.

### Terminology consistency
- **CIELab vs Stockman opponent-color space**: Stimuli are defined in CIELab (L35); the 2-component model lives in "Stockman opponent-color space" (L218). The transformation between them is not stated. The reader needs a sentence explaining that opponent-hue angles are derived from Stockman cone fundamentals applied to the CIELab stimulus set. Currently the spaces are introduced as if interchangeable.
- **CIELab vs DKL**: see Drift item §1.2. Project's own protocol description (CLAUDE.md §10) and pre-draft both say DKL. File says CIELab. Reconcile.
- "deutan" vs "deuteranomalous" (L23, L24, L227): "deuteranomalous" used at first introduction, "deutan" later. Consistent enough (full term once, abbreviation after) but reader-friendly to add "(deutan)" gloss at L23.
- hV4 / V4: hV4 used consistently in text (8 instances, no slips to bare "V4"). ✓

### Other observed issues
- L51–54: Second-session filter-evaluation paragraph is positioned in §Stimuli; it logically belongs in §Behavioral concordance or §Filter (it's a post-derivation evaluation, not stimulus design). Causes mild zig-zag (§17).
- L155–156: "averaged across the 6 runs of each test color (range $0$–$1$; chance level under a uniform random predictor $= 3/8 = 0.375$)" — the chance-level computation is operationally a result-relevant baseline. OK to keep here, but consider moving the parenthetical justification to a supplement.
- L185–187 (paragraph "Pairwise disparity"): mixes definition, procedure, and statistical test. §7 — borderline acceptable for Methods but consider splitting.

## 5. §26 Checklist (Methods-relevant items)
- [✗] §23 Order matches Results — order matches Results 1:1 (✓). BUT Participants N=12/13 inconsistency blocks pass.
- [✗] §23 No results in Methods — L268–271 and L299 leak results.
- [✓] §23 Cite original for established procedures — mostly OK; 3 missing cites flagged.
- [✗] §23 Variables defined before use — LOCO used at L118 before defined at L147; V/k notation lacks inline gloss.
- [✗] §4 Consistent terminology — CIELab vs Stockman opponent space transition unexplained; CIELab vs DKL drift vs pre-draft.
- [~] §6 Notation consistent — internally consistent; needs inline gloss for V, k at first appearance.
- [✓] §7 One role per paragraph — acceptable; L185 borderline.
- [✓] §8 Topic sentence first — all 11 subsections open with a purpose-defining sentence.
- [~] §17 No zig-zag — L51–54 second-session paragraph in Stimuli is mildly out of place.
- [~] Software versions reported — Python stack + PsychoPy yes; FreeSurfer/FSL/ezBIDS/nilearn/Neurodesign versions missing.

## 6. Priority summary

**Fatal (1)**
1. **L17 N=12 vs 13** off-by-one. Recount and fix the opening sentence.

**Serious (5)**
2. **L268–271** Result leak (Machado sub-09 3/8 hues + Figure reference) — move to Results.
3. **L299** Result leak + forward reference ("confirmed Ishihara classifications", `sec:results:participants`) — restate as method only.
4. **L118 LOCO used before defined** at L147 — gloss or forward-pointer.
5. **GLMsingle (outline) vs two-stage GLM (file)** drift — reconcile with PI; if two-stage is canonical, update pre_draft outline; if GLMsingle is canonical, rewrite L83–91 and add Prince 2022 cite.
6. **CIELab vs Stockman/DKL** color-space inconsistency between L35 (stimuli), L218 (model space), and pre-draft (DKL) — add a transformation-bridge sentence and reconcile naming with pre_draft + CLAUDE.md §10.

**Minor (7)**
7. L130 add Ledoit-Wolf cite for LDA shrinkage.
8. L148 add Brouwer & Heeger 2009 (or equivalent) cite for forward encoding model.
9. L173 add Hedges 1981 cite for Hedges' d.
10. L42 `\cite{brouwer2009}` is not the RSVP origin — remove or replace with an RSVP-origin paper.
11. L105 SRM cite stack (chen2015 + haxby2011 + guntupalli2016) — trim or differentiate roles.
12. Software versions missing for FreeSurfer, FSL, ezBIDS, Neurodesign, nilearn.
13. L51–54 second-session paragraph location (zig-zag §17) — move to §Behavioral concordance or §Filter.

**Recommended fix order**: 1 → 2 → 3 → 4 → 5 → 6 → minors batched.

**Pass status**: Methods is NOT submission-ready. Fatal + 2 Serious results leaks + 1 LOCO-before-definition violation block §26 pass.
