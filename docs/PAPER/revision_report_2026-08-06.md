# Revision Report — introduction_v2.tex + discussion_v3.tex — 2026-08-06

Scope: newly edited regions (INTRO ¶3/¶3b/¶4 transition, Gap 2–3; DISC §17, §20, Limitations),
with full-file reverse outline for context.
Rules version: `~/.claude/writing/academic_writing_rules.md` (Parts II–V)
Pre-draft artifact: **none found** (`pre_draft_*.md` absent) — no baseline outline to test drift against.

---

## 1. Reverse outline

### Introduction
- L55–56 (¶1): CVD arises from an L/M photopigment shift whose magnitude varies continuously.
- L58 (¶2): Observers sharing a diagnostic label span near-normal to near-dichromatic severity.
- L63 (¶3): Current correction, hardware and software, is calibrated to a population-average retina.
- L65 (¶4): Retinal individualization exists but predicts discrimination imperfectly, leaving a cortical filter as the remaining step.
- L70 (¶5): Cortical activity patterns carry a color geometry shared across observers.
- **L72 (¶6): What has been measured of the cortical response in CVD is the strength of the signal.**
- **L74 (¶7): CVD also displaces colors relative to one another, known only from judgments, so the model must come from cortical measurements.**
- L76 (¶8): We take the individual's cortical representation as reference and invert it, targeting hV4.
- L81 (¶9): Three gaps — individual cortical geometry undescribed, cortical distances unmeasured, cortically inverted filter underinvestigated.
- L86–99 (¶10–13): Question, warranting regime, four sub-questions, hypotheses, scope disclaimer.

### Discussion
- **L18 (§17): The deficit was a structured geometric distortion localized to a different area in each participant, consistent with prior perceptual characterizations of CVD as multidimensional deformation with large individual differences.**
- L21 (§20a): Each fitted two-component model admitted an exact inverse defining the filter.
- **L23 (§20b): The filter is the first derived from cortical rather than retinal representation; prior inversions targeted response magnitude.**
- L25–27: The neural term made three contributions to the fit.
- L29: The two fitted distortions diverge and the sign is stable, but per-axis magnitudes are unidentifiable.
- L31: The retinal-plus-gain alternative is misspecified.
- L34, L36: Filter evaluation, behavioral then neural.
- **L39 (Limitations): N = 2 with one per subtype; separating per-person from subtype-average needs more individuals within a subtype and anomaloscope grading.**
- L41, L43: Analysis-choice dependence; stimulus-locus and objective limitations.

**Paragraph-summary test (§26 item 3).** All paragraphs summarize in one sentence. ¶7 (L74) and §17 (L18)
are the densest; both still pass, but see 4.Structure.

**Subsection topic rollup.** No `[SPLIT?]` flags. `\subsection{A neurally grounded, individualizable
correction filter}` covers L21–L31 (inverse → novelty → neural term → identifiability → alternative model),
which is one topic held at four altitudes. Acceptable.

**Drift.** Cannot be assessed — no pre-draft outline exists.

---

## 1.5 Long sentences (§2)

| Loc | Words | Flag | Action |
|---|---|---|---|
| **INTRO L74 s4** | 35 | **3 clauses** (`but` / `, and` / `who`) | **Split candidate.** "Protan and deutan observers keep both axes, but their map of the hue circle is dented at yellow and purple-blue. The size of that dent differs tenfold among observers who carry the same diagnosis." |
| INTRO L74 s3 | 30 | subordinate + `, and` | Borderline. Optional split at `, and`. |
| **DISC L39 s3** | 30 | compound predicate (`requires testing… and grading…`) | Was 18w before this edit. Optional split: "…within a single subtype. Their severity also has to be graded with an anomaloscope rather than the Ishihara plates used here." |
| INTRO L74 s2 | 24 | — | Pass |
| DISC L23 s3 | 24 | — | Pass |

None exceeds the 45-word hard threshold. No semicolons, no double em-dashes.

---

## 2. §19 Vocabulary

### Tier A — 1 hit (pre-existing, now better supported)
- **DISC L23** — "To our knowledge, this is **the first** color-correction filter derived from an individual's
  cortical color representation rather than from a retinal model."
  §19A requires the hedge **plus a citation of closest prior work**. The hedge was already present; the
  sentence added in this edit round now supplies the closest prior (`bashivan2019`, `shinkle2025`).
  **Status: remediated in substance.** Literal phrase "the first" remains — acceptable under §19A only
  because both conditions are now met. Do not remove the new sentence without also weakening this claim.
- INTRO L99 — "whether per-person correction **outperforms** a subtype average" → **false positive.**
  Appears inside a scope disclaimer of what the study does *not* test, not as a claim.

### Tier B — 0 genuine hits in edited text
- INTRO L99 "This **study** tests…" → FP (noun, not the untestable verb).
- DISC L25 "**improving** on it in 3 of 7 folds" → FP (quantified).
- DISC L48 "Larger and systematic **studies**… generalizable **improvement**" → pre-existing, outside scope.
  Flag for a later pass: "generalizable improvement in color perception" is unoperationalized (§19B/C).

### Tier C — 0 genuine hits in edited text
- DISC L41 "**significant** / non-significant" ×3 → FP (statistical usage with named tests).
- INTRO L65 "estimated **accurately**" → pre-existing, outside scope; §19C would want an error bound.

### Tier D — 0 hits
No self-praise anywhere in either file.

**Verdict: none of the newly written text introduces a §19 violation.**

---

## 3. §20 Citations

### 3.1 Provenance — **1 SERIOUS**

- **DISC L18** — "Individual differences among anomalous trichromats are **larger** than among normal
  trichromats and arise from different sources \cite{emery2021}."

  The source does not support **"larger."** Emery et al. (2021) write that AT individual differences were
  due to *"different and more robust sources"* than for NT observers, and explicitly disclaim knowledge of
  relative magnitude: *"we do not know whether … the sample of AT observers had individual differences of
  comparable magnitude to the NT sample."* Asserting greater magnitude attributes a claim the paper declines
  to make (§20 Provenance honesty).

  **Fix:** "Individual differences among anomalous trichromats arise from different and more robust sources
  than among normal trichromats \cite{emery2021}."

  This is load-bearing: the sentence is the defense for the two participants' distortions localizing to
  different areas. The corrected version still carries that defense.

### 3.2 Claim ↔ source specificity — all pass
| Loc | Claim type | Cited | Verdict |
|---|---|---|---|
| INTRO L74 | specific empirical (hue primaries land on different stimuli) | `emery2021` primary | ✓ |
| INTRO L74 | specific empirical (one axis where normals have two) | `saysani2018` primary | ✓ |
| INTRO L74 | specific empirical (dent at Y/PB, tenfold spread) | `ohkoba2021` primary | ✓ |
| DISC L18 | synthesis over prior work | `boehm2014, ohkoba2021, emery2021` (3 primaries) | ✓ acceptable — no review of CVD color-space deformation exists; 3 < 5-stack limit |
| DISC L23 | method-class characterization | `bashivan2019, shinkle2025` primaries | ✓ |

### 3.3 Accuracy of the new method-class sentence — **1 MINOR**
- **DISC L23** — "set the magnitude of response **in a chosen region**".
  Bashivan et al. target individual **neural sites** (single- and multi-unit), not regions; only
  Shinkle & Lescroart target regions. **Fix:** "in a chosen unit or region."

### 3.4 Density
No stack of 5+. Largest is 3 (`brouwer2009, brouwer2013, kuriki2015` at Gap 1; `boehm2014, ohkoba2021,
emery2021` at DISC L18).

---

## 4. §26 Checklist (scoped to edited regions)

### Reverse outline
- [✓] One sentence per paragraph, reads in order as a narrative
- [N/A] Match to §1 Step 5 outline — no pre-draft artifact exists
- [✓] No paragraph needs two sentences to summarize

### Claims
- [✓] Central contribution recoverable (not re-tested; abstract unchanged this round)
- [✓] Numeric Δ carries baseline + metric — "differs tenfold among observers who carry the same diagnosis"
      names the comparison set; DISC numbers unchanged
- [◑] "first / only / no X" cited — DISC L23 now cites closest prior (see 2.TierA)
- [✓] Untestable verbs replaced (edited text)
- [✓] Vague adjectives operationalized (edited text)
- [✓] No self-praise

### Citations
- [✓] General claim → appropriate source
- [✗] **Specific claim → primary, stated faithfully — DISC L18 `emery2021` overstates (3.1)**
- [✓] Method origin → original paper
- [✓] No 5+ stacks

### Structure
- [✓] Each paragraph one role — ¶3 = magnitude, ¶3b = geometry, ¶4 = design premise. The split fixed
      the pre-existing mismatch where ¶3's topic sentence promised geometry and its body delivered gain.
- [✓] First sentence = topic sentence — all four edited paragraphs open on their main claim
- [✗] **Pronouns / reference unambiguous — 2 issues (see 4.1, 4.2)**
- [◑] Terminology consistent — see 4.2
- [✓] Observation / interpretation / implication separated

### Section-by-section
- [✓] Introduction And–But–Therefore: *And* = cortex carries a shared color geometry (¶5);
      *But* = in CVD only strength has been measured (¶6) and the displacement is known only from
      judgments (¶7); *Therefore* = invert the individual's own cortical geometry (¶8). **The ¶3/¶3b
      split strengthened this — the "But" is now two explicit steps instead of one buried clause.**
- [✓] Discussion states limitations and ties to gap
- [✓] No new results introduced in Discussion

### 4.1 — **SERIOUS: old-to-new bridge broken at ¶2 → ¶3 (INTRO L70 → L72)**

The previous opener was "**Cortex reshapes this geometry in CVD**." The demonstrative *this geometry*
anaphorically bound ¶3 to ¶2's final sentence ("The relative positions of colors … constitute a geometry.
That geometry is shared across observers"). The replacement — "What has been measured in the cortical
response in CVD is the strength of the color signal" — carries no anaphor, so ¶2's terminal *new*
information is not picked up as ¶3's *familiar* opening (§2 old-to-new).

Two repairs, both preserving the magnitude framing the edit was made for:

- **(a) restore the anaphor, two short sentences**
  "In CVD, that geometry has not been measured. What has been measured is the strength of the color signal."
  Cost: pre-announces Gap 2 nine paragraphs early.
- **(b) restore the anaphor, one sentence** *(recommended)*
  "What has been measured of that response in CVD is the strength of the color signal."
  `that response` binds to ¶2's "response patterns"; no Gap 2 pre-emption.

### 4.2 — MINOR: "the same geometry" has an indirect antecedent (INTRO L74, final sentence)

¶3b describes the phenomenon as "where colors lie relative to one another" and "their map of the hue
circle", then closes on "cortical measurements of **the same geometry**." The word *geometry* last appeared
in ¶2 (L70), two paragraphs back. The reference resolves, but across a longer span than §3 prefers.

**Fix:** use the term once mid-paragraph, e.g. sentence 3 → "…and the map recovered from those judgments —
the geometry of their color space — has one axis where normal trichromats have two." Or simply change the
closing to "…of that geometry in cortex."

### 4.3 — MINOR: DISC §17 (L18) is now 10 sentences

The two added sentences bring the paragraph to 10. It still passes the one-sentence-summary test and all
sentences serve the single role of establishing and contextualizing the geometric distortion, so no split
is required. Flagged only so a later trimming pass knows where the length came from.

---

## 5. Priority summary

**Total issues: 7** (Fatal 0 · Serious 2 · Minor 5)

**Serious**
1. **DISC L18** — `emery2021` cited for "larger" individual differences; the source disclaims that comparison. (§20 provenance)
2. **INTRO L72** — anaphoric bridge from ¶2 lost when the topic sentence was rewritten. (§2 old-to-new)

**Minor**
3. INTRO L74 s4 — 35 words, 3 clauses → split. (§2)
4. DISC L39 s3 — 30-word compound predicate after the anomaloscope clause → optional split. (§2)
5. DISC L23 — "in a chosen region" → "in a chosen unit or region" (Bashivan targets sites). (§20)
6. INTRO L74 — "the same geometry" antecedent two paragraphs back. (§3/§4)
7. DISC L48 — pre-existing, outside scope: "generalizable improvement in color perception" unoperationalized. (§19B/C)

**Recommended sequence**
1. Fix 1 (citation provenance) — highest stakes; it is a claim the source does not make.
2. Fix 2 (option b, one-sentence anaphor restore).
3. Fix 3 and 5 — mechanical.
4. Defer 4, 6, 7 to a trimming pass.

**Net effect of this edit round on the checklist:** the ¶3/¶3b split repaired a pre-existing §7/§8
violation (topic sentence promised geometry, body delivered gain) and made the Introduction's
And–But–Therefore explicit. The Tier A "first" claim at DISC L23 moved from unsupported to
§19A-compliant. The two Serious items above are both introduced by this round and both are
one-sentence repairs.

---

## Naive-reader check (Phase 5.5)

**Not run.** The requested scope is the edited Introduction and Discussion regions; Phase 5.5 targets the
abstract and Introduction ¶1, which were not changed this round. Run it separately if you want an
abstract-level comprehension pass.
