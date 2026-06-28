# Revision Report — Discussion (discussion_v3.tex)
Date: 2026-06-24 · Skill: /revise-draft · Target: `Discussion/discussion_v3.tex`
Rules: `~/.claude/writing/academic_writing_rules.md` §19/§20/§25/§26 + project guardrails (anti-overstatement; no specificity claim; etiology Δλ/g removed).

**Verdict**: structurally sound and guardrail-compliant; the etiology removal held and no specificity claim crept back. Main weakness is §2 expression density (long multi-clause sentences, semicolon/dash overuse) and a handful of Tier-C/A vocabulary items needing operationalization. No Fatal issues.

Counts: **Fatal 0 · Serious 4 · Minor 9**

---

## 1. Reverse outline (one sentence per paragraph)

- **¶1 (L15, opening)**: We asked whether CVD cortical color representation is structured enough to ground a personalized filter; both participants kept categorical discrimination but lost hue interpolation, modeled as a two-component geometric distortion that yields an invertible per-person correction, validated in the deutan case to the forward-tuning level but not behaviorally beyond a deployed filter.
- **¶2 (L17–18, "A geometric distortion")**: The deficit is a structured geometric distortion, not uniform attenuation — RDM shows *which* distances deviate (V2 deutan, V1 protan) and LOCO shows *where* interpolation breaks (hV4), consistent with multidimensional-deformation accounts.
- **¶3 (L21)**: Each filter is the stimulus-space pre-image of the fitted two-component model; mean rotation |δθ| = 26.3° (deutan) / 16.2° (protan).
- **¶4 (L23–25)**: Fitting behavioral and neural atoms independently gave three benefits — neural term resolved the confusion axis the behavioral fit could not, stabilized the deutan solution, and tightened parameter stability.
- **¶5 (L27)**: The filter is per-person and neurally grounded; the subtype contrast rests on the *sign/direction* of β_c (not identifiable per-axis magnitude), read from each participant's own geometry rather than diagnostic label.
- **¶6 (L29)**: A population-average (Machado) transform cannot substitute because it is confined to one axis and collapses three protan hues onto one pre-image, a structural limit independent of any fit.
- **¶7 (L31–32, "Filter evaluation")**: In the deutan second session the personalized filter beat the deployed filter on forward-tuning (moved toward HC in all 4 ROIs) but not on global representational geometry or behavior; advantage is confined to forward-tuning, single case.
- **¶8 (L34–35, "Limitations")**: Four bounds — N=2, single iso-luminant/iso-chroma locus, small HC reference cohort, no parameter bootstrap CIs.
- **¶9 (L37–40, "Conclusion")**: Proof-of-concept that individual cortical geometry can ground an invertible per-person correction, structurally distinct from population-average retinal approaches; a template for brain-based perceptual correction.

**Drift vs pre-draft (`pre_draft_2026-05-10.md` §5 Discussion)**: The pre-draft ¶4 "detection/correction divergence falsifier + 2AFC prediction" is **correctly absent** (header L8–9 says removed in v3); good. Etiology (Δλ/g) is **correctly absent**. No drift problems. The outline now reads as 3 contributions (C1 distortion / C2 filter / C3 evaluation) per the header spine — coherent.

**Two-role paragraph flag (§7)**: ¶7 (L31–32) mixes **result** (forward-tuning win), **counter-result** (geometry/behavior null), and **interpretation/scope-bounding** in one ~9-sentence block. It needs two sentences to summarize → §7 split candidate (Serious-2). ¶4 (L23–25) is a clean enumerated single role (the three benefits). All others are single-role.

---

## 2. §19 Vocabulary scan (Tier A/B/C/D)

### Tier A — overstatement (scrutinized hardest for Discussion)
- **No banned Tier-A tokens found.** No "first", "novel", "proves", "definitively", "comprehensive", "state-of-the-art", "always/never". `\cite{...} replicating brouwer2009` (L18) is hedged correctly. **PASS.**
- **[Minor-1] L32 "outperformed the deployed filter"** — Tier-A "outperforms" family. It *is* qualified in-clause ("moved... toward the HC reference in all four ROIs and outperformed"), but the comparison baseline + metric should be adjacent. Currently metric (forward-tuning / LOCO geometry) is named one clause earlier. Acceptable but tighten: name metric in the same clause ("outperformed the deployed filter on forward-tuning"). Direction: minor sharpen.

### Tier B — untestable verbs
- **[Minor-2] L18 "expose a structural distortion"** ("Two complementary measurements expose...") — "expose" reads as mild over-assert. Replace with "index" / "reveal" is fine, but consider "measure two facets of". Low priority.
- No "study/explore/investigate/understand/address" found. **PASS otherwise.**

### Tier C — vague adjectives needing inline operationalization
- **[Serious-1] L25 "corroborating the behavioral estimate"** and L25 **"differs in substance from a purely behavioral one"** — "in substance" is vague; the paragraph does quantify (IQR narrowing, same argmin, β_c = −26°), so anchor the phrase to the quantity: "differs in [the recovered confusion-axis direction / parameter-stability]". Direction: replace "in substance" with the operational quantity already in the paragraph.
- **[Serious-3] L29 "implausibly implying overcompensation"** — "implausibly" is an unoperationalized judgment adjective. Tie to the observable: g ≈ 3 implies >100% correction in observers who remain measurably impaired (the clause already says this) → drop "implausibly" or convert to "which would imply overcompensation (>1× gain) in observers who remain impaired". Direction: convert adjective to the stated criterion.
- **[Minor-3] L32 "This dissociation is coherent"** — "coherent" is Tier-C/D-adjacent self-assessment. The following dash-clause explains it; recast as "This dissociation follows from the filter restoring angular order while compressing radial scale" (state the mechanism, drop the evaluative adjective).
- **[Minor-4] L27 / L35 "robust directions" / "the sign of β_c is the recoverable quantity"** — "robust" appears (L27 "stable... the level the filter relies on"; L27 "robust directions"). Operationalized adjacently ("0 of 6 recovery checks survive FDR"), so **borderline PASS**; ensure "robust" always sits next to that FDR clause. Minor.
- **[Minor-5] L18 "significantly elevated"** (×, "disparity was significantly elevated at V2") — "significantly" carries the test+p inline (Crawford & Howell p=0.040) → **PASS** (operationalized).

### Tier D — self-praise
- **[Minor-6] L21 / L27 / L40 "the architectural advance" / "architecture is individualizable by construction" / "architecture that follows... is distinct by construction"** — "architectural advance" (L27) leans into Tier-D promotion. "distinct by construction" / "individualizable by construction" are defensible (they state a structural fact, not praise). Recommend keeping the "by construction" phrasings, downgrade "the architectural advance over a population-average correction" (L27) to "the design difference from a population-average correction". Direction: soften one promotional noun.

---

## 3. §20 Citation audit

All seven keys resolve in `bibliography.bib` (verified): kriegeskorte2008, kriegeskorte2019, brouwer2009, machado2009, crawford1998, boehm2014, emery2021. `\citeA` is the apacite author-prominent form and is used consistently project-wide (Methods uses it identically). No broken keys.

- **L17 `\cite{kriegeskorte2008, kriegeskorte2019}`** — general-domain statement about representational geometry → review/foundational pair. Correct specificity (§20). **PASS.**
- **L18 `replicating \citeA{brouwer2009}`** — specific empirical finding (hV4 supports interpolation) → primary paper. Correct (§20). **PASS.** Consistent with MEMORY framing note (Brouwer & Heeger did perform LOCO; replication claim is accurate, not "first").
- **L18 `\cite{boehm2014, emery2021}`** — general characterization ("multidimensional deformation rather than uniform attenuation"). Two primaries for a general claim. **[Minor-7, suspect-lite]**: §20 prefers a review for a general domain statement; two primaries is acceptable here since the claim is a synthesis, but flag that neither is a review. Low priority — not a mismatch, just a specificity nuance.
- **L29 `\cite{machado2009}` and `Section~\ref{sec:methods:candidates}` / `Appendix~A`** — method-origin citation for the population-average class. Correct (§20, original paper). **PASS.**

No 5+ citation stacks. **Citation section: PASS** (1 minor nuance).

---

## 4. §26 Checklist

### Reverse outline
- [x] One sentence per paragraph — done above; narrates the paper.
- [x] Matches §1 Step-5 outline — yes, modulo deliberate removals (etiology, divergence falsifier). No accidental drift.
- [~] **No paragraph needs two sentences** — **FAIL for ¶7 (L31–32)** → §7 split (Serious-2).

### Claims
- [x] One-sentence contribution recoverable (¶1 + ¶9 both carry it).
- [~] **Every numeric Δ has baseline + metric** — mostly yes. **[Serious-4] L24 "lowering the boundary-saturation rate from 23% to 9.3%"** has before/after but the *metric* "boundary-saturation rate" is not defined in Discussion (defined in Methods?); ensure forward reference or one-clause gloss. Similarly L21 "|δθ| = 26.3° / 16.2°" — units clear, baseline (no-correction = 0°) implicit; acceptable.
- [x] Every "first/only/no X" — none present (good).
- [~] Untestable verbs — "expose" (Minor-2), otherwise clean.
- [~] Vague adjectives operationalized — "in substance" (Serious-1), "implausibly" (Serious-3), "coherent" (Minor-3) outstanding.
- [~] No self-praise — "architectural advance" (Minor-6) borderline.

### Citations
- [x] General → review (kriegeskorte pair OK; boehm/emery minor nuance).
- [x] Specific empirical → primary (brouwer2009).
- [x] Method origin → original (machado2009).
- [x] No 5+ stacks.

### Structure
- [~] One role per paragraph — **FAIL ¶7** (Serious-2); rest PASS.
- [x] First sentence = topic sentence — every paragraph leads with its claim. PASS.
- [~] **Pronouns unambiguous (§3)** — **[Serious-2/Minor-8] L32 "this proximity", "it reshaped", "This dissociation"** chain in ¶7: "it" (the personalized filter) is recoverable but the paragraph's referent density is high. Mostly OK; tighten in the split.
- [x] Terminology consistent — "deutan/protan participant", "forward-tuning", "pre-image", "two-component" used consistently. PASS.
- [~] Observation/interpretation/implication separated (§9) — ¶7 fuses observation (proximity result) + interpretation ("this is the bar, not correction") in adjacent clauses; acceptable but dense.

### Section-by-section
- [x] **§25 Discussion states limitations AND ties to gap** — **PASS, strong.** Limitations ¶8 (L34–35) enumerates four, and each ties to the contribution: N=2 → "population-level claims require replication"; "Establishing per-person rather than subtype-average correction specifically requires testing several individuals within a single subtype — the decisive follow-up." This explicitly ties the limitation back to the C2 per-person contribution. Conclusion ¶9 ends with field impact ("template for personalized, brain-based perceptual correction"). Both §25 requirements met.
- [x] No new results in Discussion — ¶7 reports the Phase-3 deutan evaluation; this is the paper's own result presented in Results, recapitulated for interpretation. Acceptable (not a *new* analysis introduced only here). Confirm it also lives in Results.

### Final pass
- [~] Filler — **[Minor-9] L29 "for a reason that holds independent of any fit"** and L29 "even when scaled by a cortical gain" are slightly wordy but load-bearing (they establish the structural-vs-empirical distinction the guardrails require). Keep. Minor: "therefore does not represent distortion in orthogonal directions" — fine.
- [x] Negatives — "not diffuse signal loss but a structured..." uses positive equivalent. PASS.
- [~] Nominalizations — "a uniform attenuation of the chromatic signal" (L17–18) ×2; fine as familiar concept. Minor.
- [x] Passive → active — opening is active ("We asked", "We built", "We tested"). PASS.

---

## 5. Project-specific overclaim scan (guardrails)

**Result: CLEAN. No guardrail violations.** Detailed checks:

- **Specificity claim (forbidden)**: **None.** The draft never claims HC-specificity / CVD-specificity as a selection criterion or result. ¶5 (L27) explicitly states magnitude "is not the basis of the contrast" and rests the contrast on direction only. ¶8 (L35) recasts "per-person vs subtype-average" as a *future* test, not an established specificity result. Compliant with CLAUDE.md §3 "specificity claim 금지". **PASS.**
- **Etiology (Δλ/g) over-claim**: **None re-crept.** No Δλ, no opponent-gain g as etiological driver. The only g mention (L29 "gain saturated near g ≈ 3") is used to *reject* the Machado class empirically, not to assert an etiology — exactly the "β_c contrast kept, etiology removed" policy. **PASS** (this was the explicit risk flagged in the prompt; it is clean).
- **Physiological absolute-value interpretation (forbidden)**: **None.** L27 "Per-axis magnitude is not identifiable" and L35 "the sign of β_c is the recoverable quantity... point values whose interval precision awaits..." explicitly disclaim absolute-value reads. β_c values (−42°/+24°) are presented as *direction/sign* contrasts, not absolute physiological quantities. Matches MEMORY "production argmin = descriptive embedding, no physiological absolute-value interpretation". **PASS.**
- **Convergence between different physical quantities (forbidden)**: **None.** The draft does NOT equate β_s ≈ Emery's 21.4° S-cone shift (the pre-draft flagged this temptation at `pre_draft` L114). emery2021 is cited only at L18 for the *general* "multidimensional deformation" claim — structure grounding, not value convergence. L25 "corroborating the behavioral estimate" refers to neural-vs-behavioral fit of the *same* β_c quantity (same physical quantity, two measurements) — this is legitimate, not cross-quantity convergence. **PASS.**
- **Literature = structure not value** (feedback_physiological_grounding): boehm2014/emery2021 used for model *structure* (deformation class), brouwer2009 for paradigm match. Compliant. **PASS.**

---

## Number consistency vs project canonical (MEMORY)
Spot-checked against MEMORY/CLAUDE.md canonical values — **all match**:
- |δ| = 26.3° (deutan) / 16.2° (protan) ✓ (CLAUDE.md "canonical |δ|=26.3/16.2")
- β_c argmin (6°,−42°) deutan / (2°,+24°) protan ✓ (project_paper_figure_set "canonical (6,−42)/(2,+24)")
- SRM disparity V2 deutan p=0.040, V1 protan p=0.007 ✓ (MEMORY SRM individual)
- hV4 HC interpolation 0.47±0.05, p=0.044 ✓
- 2-component class, 0/6 recovery checks survive FDR ✓ (MEMORY v6 closure "12/12 FAIL"; the "0 of 6" per-participant magnitude-recovery figure is consistent with the descriptive-only stance)

Note: pre-draft (L41) lists older |δ| = 46.3°/20.1° — those are SUPERSEDED by the v6 PCA closure; the draft correctly uses the newer 26.3°/16.2°. No action needed (draft is current).

---

## Top issues (ranked)

1. **[Serious-2] ¶7 L31–32 two-role paragraph (§7/§26)** — result + counter-result + scope-bounding in one ~9-sentence block; needs two sentences to summarize. → Split into (a) forward-tuning result vs deployed filter, (b) geometry/behavior null + scope bound.
2. **[Serious-1] L25 "differs in substance"** — vague Tier-C; the quantities are right there (IQR, argmin, β_c=−26°). → Replace "in substance" with the operational quantity.
3. **[Serious-3] L29 "implausibly implying overcompensation"** — unoperationalized judgment adjective. → Convert to stated criterion (g≈3 ⇒ >1× gain in still-impaired observers).
4. **[Serious-4] L24 "boundary-saturation rate from 23% to 9.3%"** — metric undefined in Discussion. → Add one-clause gloss or forward-ref to Methods.
5. **[Minor-6] L27 "the architectural advance"** — Tier-D promotional noun. → "the design difference from a population-average correction".
