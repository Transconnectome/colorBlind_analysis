# Discussion v3 — Structure, Evidence Pack & Writing Brief

> Created 2026-06-08. Supersedes the spine of `discussion_v2.tex` (which was hV4-centric and leaned on a now-retired "detection–correction divergence" argument). This file is the **authoritative brief** for drafting Discussion v3 and the reference for downstream work.
>
> **§2 revised 2026-08-06** — the 2026-06-08 skeleton (8 paragraphs) no longer described the file. Two changes drove the rewrite. (a) Phase 3 data arrived, so the planned forward-looking ¶6 became a reported evaluation. (b) A `/revise-draft` pass split three paragraphs that mixed roles (§7). Current file: **17 paragraphs**. §0, §1, §3, §4 are unchanged and remain authoritative.
>
> §2 below is the reverse outline **as written**, not an intended outline. Regenerate it whenever the paragraph count changes, or drift checks in the next cycle are meaningless.

---

## 0. Headline reframe (the thing v2 got wrong)

v2 framed the paper as **"hV4 color geometry → filter"** (an ROI-centric causal chain) and treated LOCO as the "operative corrective target." Both are wrong:

- The filter is **not** fit on hV4 LOCO. LOCO did **not** enter either winning loss combination (Methods §selection). Fits use **behavioral JND (γ) + ΔRDM (V1/V2)**.
- LOCO/RDM are **not** "the target." Their **의의 (significance)** is that they **measure a neural representational/geometric difference** — that CVD color deficits are a *structured geometric distortion* of cortical color representation (shape/structure/relational geometry), not a 1-D signal loss.

**Correct headline:**
> CVD color deficits manifest as an **individual-specific geometric distortion** of the cortical color representation. **RDM characterizes the structure** of that distortion; **LOCO is its functional consequence** (broken continuous-hue interpolation). **Neural and behavioral measurements jointly ground** a personalized stimulus-space correction. The filter is *downstream* of the finding — not the headline.

**Banned framing:** the word "target" for LOCO/RDM; the word "diverge"/"divergence" for retinal-vs-cortical corrections; any §S16 cosine-similarity (−0.54) argument (REMOVED entirely, see §4).

---

## 1. Three-contribution spine

| Block | Contribution | Status | ¶ |
|---|---|---|---|
| **C1** | CVD has a **structural/geometric difference** in cortical color representation (RQ1). RDM = structure, LOCO = functional consequence. | current result | ¶2 |
| **C2** | A **personalized filter built from individual cortical structural information** — neural adds information behavior cannot access; the method yields a per-person filter. | current result | ¶3–¶5 |
| **C3** | **Performance superiority** of the personalized filter vs OS-builtin (Windows/macOS) color filters and no-filter baseline. | **Phase 3, forward-looking TODO** | ¶6 |

---

## 2. Paragraph map (reverse outline as written, 2026-08-06)

`discussion_v3.tex` line numbers. One role per paragraph (§7); first sentence is the topic sentence (§8).

### Executive summary
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 1 | 15 | executive summary | Per-person filters were derived by inverting each participant's own cortical color model, the underlying representation was geometrically distorted rather than uniformly attenuated, and a two-person evaluation normalized behavioral thresholds while cortical interpolation effects split by participant. |

### `A geometric distortion of cortical color representation` — C1
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 2 | 18 | finding + literature placement | The deficit is a structured distortion of cortical color geometry localized to a different area in each participant, resolved by RDM (structure) and LOCO (functional consequence). |

### `A neurally grounded, individualizable correction filter` — C2
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 3 | 21 | filter definition | Inverting each fitted model assigns every hue a single replacement color, and that replacement is the filter. |
| 4 | 23 | novelty claim | This is the first filter derived from an individual's cortical color representation rather than a retinal model, and prior encoding-model inversions targeted response magnitude, not color arrangement. |
| 5 | 25–27 | neural term is load-bearing (C2a) | The neural term recovered a rotation the behavioral loss missed, reinforced the one it found, and narrowed the argmin spread. |
| 6 | 29 | individualization (C2b) | The two fitted distortions diverge in the sign of $\hat\beta_c$, and that sign held under HC resampling and leave-one-HC-out. |
| 7 | 31 | caveat bounding ¶6 | Per-axis magnitudes are unidentifiable, the recovered quantity is the dominant-axis sign, that sign is basis-dependent in the protan participant, and subtype is confounded with individual. |
| 8 | 33 | alternative-model rejection | The retinal-plus-gain class has one degree of freedom along the confusion axis, omits displacement away from it, and failed in fitting with $g > 2$. |

### `Filter evaluation`
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 9 | 36 | behavioral results | The individualized filter kept every discrimination pair within the HC range and preserved identification accuracy, whereas the deployed filter left two pairs deviant in the protan participant. |
| 10 | 38 | neural results | The neural effect varied by participant and by measure, geometry moved opposite to interpolation in each participant, and the protan geometric recovery occurred under both filters. |
| 11 | 40 | neural interpretation + scope | The two readouts sit at different hierarchical levels and can vary independently, so two cases cannot settle the neural effect. |

### `Limitations`
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 12 | 43 | sample | Both the CVD sample ($N=2$) and the HC cohort ($n=7$) are too small for population-level claims or a significance test, and severity grading needs an anomaloscope. |
| 13 | 45 | estimate robustness | Two reported estimates depend on analysis choices — the deutan V2 elevation on the alignment control, and $\hat\beta$ on the absence of confidence intervals. |
| 14 | 47 | stimulus scope | The single isoluminant, iso-chroma locus leaves the correction untested outside it. |
| 15 | 49 | fitting objective | The two neural loss terms are measured on different quantities at different ROIs, so a shared representation is needed before one objective can weight them jointly. |

### `Conclusion`
| ¶ | L | Role | One-sentence summary |
|---|---|---|---|
| 16 | 52 | what was derived | Each correction inverts that participant's own fitted cortical distortion and is therefore a per-person, not population-average, transform. |
| 17 | 54 | field impact | Larger systematic studies can quantify these distortions and establish whether the correction generalizes. |

### Changes from the 2026-06-08 skeleton

| 구 계획 | 현행 | 사유 |
|---|---|---|
| ¶4 individualization / ¶5 caveat — 별도 2문단 | ¶6 (L29) / ¶7 (L31) | 한때 병합돼 있던 것을 계획대로 복원 |
| ¶6 = C3 performance, **Phase 3 forward-looking TODO** | ¶9–¶11 = 실제 수행된 2인 평가 | Phase 3 데이터 확보 |
| ¶7 Limitations, `Four considerations` 단일 문단 | ¶12–¶15, 6항목 4문단 | 항목 추가(정렬 대조 비대칭, 손실항 이질성) + §7 분할 |
| ¶8 Synthesis + broader impact | ¶16–¶17 | 결론 2문단 분리 |

**REMOVED from v2 (변동 없음):** the upstream-input-rejection paragraph (LORO-preserved → not inherited deficit); the detection–correction "divergence" falsifier paragraph and its §S16 cosine statistic.

---

## 3. Evidence pack (CANONICAL — source of truth; do not deviate)

### LORO precondition (Results §loro) — established, NOT re-argued in Discussion
- Both CVD exceed 0.125 chance at every ROI. Cross-subject HC-HC vs HC-CVD MWU p=0.668. Within-ROI hV4 Crawford–Howell p=0.142.

### LOCO interpolation (Results §loco)
- HC hV4 adjacent accuracy 0.47±0.05 SEM, p=0.044 (8!=40,320 exact perms). V1–V3 not above chance.
- sub-08 adj acc 0.25 (t=−1.58, p=0.082 n.s., d_cc=−1.71); sub-09 adj acc 0.13 (t=−2.48, p=0.024, d_cc=−2.68).
- Both near-zero at blue/purple/magenta (S-cone intermediates). Per-hue: blue both d=2.20 p=0.042; purple d=1.02 p=0.19; magenta d=1.89 p=0.064. Vulnerability profile **v ∈ [0,1]^8**.

### Geometry / RDM (Results §geometry)
- ΔRDM = RDM_CVD − mean(RDM_HC). sub-08 elevated disparity **at V2 (p=0.040)** only; sub-09 **at V1 (p=0.007)** only.
- Idiosyncratic ROI specificity (V2 deutan, V1 protan) is inconsistent with a shared group-level gain mechanism.

### Retinal (R+C / Machado) insufficiency (Results §rc_insufficient) — basis for C3 rationale
- sub-08: 100% of resamples saturate grid boundary, g=3.0. sub-09: 41% saturation, g=2.95.
- g>2 ⇒ cortex reverses retinal shift past undistorted hue. Ishihara: sub-08 5/14, sub-09 7/14 (confirmed CVD). g>2 is internally inconsistent with confirmed CVD = **model failure, not a valid estimate**.
- DOF deficit: δθ=(2−g)·δθ_Machado displaces only along the fixed confusion axis.
- Machado non-invertibility (sub-09): collapses green 135°, cyan 180°, blue 225° onto ~127° → no exact pre-image.

### 2-component fits (Results §twocomp) — CANONICAL β
- **sub-08 (deutan, θ_conf=150°)**: loss γ_OY + L_RDM^(V2) → **(β_s, β_c) = (6°, −42°)**. L̄_test=−2.36 (IQR 2.15) vs alt −1.14. HC-resample IQR (8°,2°). Strict 7-fold LOO β_c ∈ [−46°,−38°] (all negative). Pre-image mean |δ| = **26.3°** (max 38°).
- **sub-09 (protan, θ_conf=16°)**: loss γ_all + L_RDM^(V1) → **(β_s, β_c) = (2°, +24°)**. L̄_test=−1.54 (IQR 1.42). HC-resample IQR (0°,0°); 87.7% same 45° bin; LOO IQR (0,0). Metric-dependent (Appendix crossatom). Pre-image mean |δ| = **16.2°** (max 25°).
- Dominant component = β_c for both. RDM held-out LOO: sub-08 0.594, sub-09 0.528; beat (0,0)=1.0 on all 7 folds; fits in top 5–8% of grid. Noise ceiling 0.240/0.274; recover 52%/67% of achievable range.
- RDM atom ROI matches disparity ROI (V2 sub-08, V1 sub-09); the two criteria are independent (loss by test-loss, disparity by Crawford–Howell).

### Neural role (Results §neural_role) — load-bearing for C2a
- sub-09 behavioral-only β_c≈+4°, did NOT beat baseline (ΔL=+0.01, 4/7 folds); RDM captures a signal the behavioral loss cannot detect.
- sub-08 behavioral-only AND combined share argmin (6°,−42°); adding RDM reduced boundary saturation 23%→9.3% (sharpened without shifting). Neural-only sub-08 non-degenerate β_c=−26° (corroborates deutan direction).
- Neural term reduces parameter IQR both: sub-08 (18,6)→(8,2) PCA; sub-09 (6,4)→(0,0) PCA.

### Identifiability (Results §identifiability) — basis for ¶5
- 0/6 checks significant after FDR (BH α=0.05). Voxel-level f_10° < 0.30 both. Non-dominant |β_s|≤6° below ~20–25° uncertainty (not recoverable). Dominant β_c=42° (sub-08) exceeds uncertainty → partial recovery (bias 4.7°).
- Sign of β_c stable across held-out: sub-08 <0 all LOO/resamples; sub-09 >0 **under PCA-basis only** (SRM-basis sign not verified).

### Selection (Methods §selection)
- 3 gates: directional precondition (signed d≥+0.5) → boundary saturation (<50%) → held-out test-loss (primary), test-loss IQR (secondary). **LOCO loss did NOT enter the winning combination for either participant.** Specificity is descriptive only, not a selection criterion.

---

## 4. Anti-overstatement constraints (CRITICAL — apply to every paragraph)

From project policy (`phase5_filter_optimization/CLAUDE.md` §0, §2.6; memory `project_v6_pca_closure`, `feedback_physiological_grounding`):
- **Descriptive only.** No specificity claim (HC FPR 100%; no p-value/FPR claim). State as "mechanism class (sign quadrant) descriptive."
- **No absolute (β_s, β_c) or g physiological interpretation.** R+C is an exploratory descriptive companion (near-degenerate loss; g unstable); **no etiological claim**.
- **"Individual" = between-subtype at N=2**, never within-subtype.
- **LOCO interpolation is robust only at hV4**; V1/V2 interpolation is below null. The geometric-distortion claim rests on RDM disparity (V1/V2) + hV4 interpolation failure — state it that way.
- **Mechanism class + sign robust; per-axis magnitude not.**
- **No "target" for LOCO/RDM. No "diverge" for retinal-vs-cortical.** Retinal argument = **insufficiency** (boundary saturation / over-compensation / non-invertibility), framed as model FAILURE.
- **§S16 divergence / cosine −0.54 REMOVED** from Discussion AND supplementary.
- **Phase 3 efficacy is forward-looking and two-directional** (state both "if confirmed" and "if not"); never assume success.

---

## 5. Genre templates (from NotebookLM analysis of comparable papers)

> Caveat: NotebookLM stores some PDFs as fragmentary excerpts; templates below are partly inferred heuristics, not verified full-paragraph maps.

**(A) Empirical fMRI color-neuroscience** (Bannert 2018, Brouwer & Heeger 2009, Tregillus 2021):
- First ¶ = executive summary (restate goal + neural finding + behavioral link, then "results suggest…").
- Middle = methodological-uniqueness defense ("simpler model, reconstructs *novel* stimuli") → "Nonetheless" limitation pivot → cross-species/literature grounding.
- Later = anatomical locus interpretation → mechanism (adaptation/gain).
- Last = broader significance → clinical implication → limitation (compensation incomplete) → future direction.

**(B) Model→correction bridge** (WHIS/Irino 2023 = structural twin, Akalin 2025, Boehm 2014) — 4-step justification:
1. **Baseline failure** — pure retinal/physical model fails to explain the phenomenon (Boehm: threshold 38% ≠ perception 86%).
2. **Parameterized bridge** — the specific transform (gain / inverse function).
3. **Validity defense** — objective metric OR rule out alternatives as implausible.
4. **"Restored symmetry" closure** — translate the math fix into a human benefit.

Our paper sits at (A)+(B); WHIS is the closest structural analog ("characterize structured deformation → parameterize → invert → correct").

NotebookLM CVD-framing support (use for ¶1–¶2):
- CVD = multidimensional geometric distortion/warping of cortical color space, not 1-D loss (MDS compression: Boehm; angular hue-scaling warp: Emery; representational geometry: Kriegeskorte 2008/2019 — RDM = what the brain "knows" about stimulus relationships).
- "Scattered but parallel": CVD relational structure preserved but scattered 1.4–1.6× more (our SRM/RDM result).
- Brouwer & Heeger: novel-color interpolation tests a continuous perceptual manifold; V4 supports it, V1–V3 do not; CVD interpolation failure = "broken color wheel."
- Population retinal model can't capture individual cortical compensation: Boehm (threshold≠suprathreshold), Emery (R-G amplitude uncorrelated with threshold loss), Bosten 2019 (large individual differences not associated with sensitivity loss).

---

## 6. Citation keys (valid in `docs/PAPER/bibliography.bib`)

brouwer2009, bannert2018, emery2021, tregillus2021, boehm2014, bosten2019, kriegeskorte2008, kriegeskorte2019, crawford1998, machado2009, isherwood2020, ishihara1917, akalin2025, feilong2018, conway2018, shapley2011, kuriki2015, parkes2009, brettel1997, hayashi2024, robinson2023, stockman2000, neitz2011, deeb2005, benjamini1995, nichols2002.

Use only these or keys already present in `discussion_v2.tex`/`results_v4.tex`. Do not invent keys; flag any concept lacking a key.

---

## 7. Output conventions for drafting

- LaTeX prose matching `discussion_v2.tex` (\section, \citeA{} for narrative cites, \cite{} for parenthetical, \ref{}, \emph{}, °/$^\circ$).
- One idea per paragraph; topic sentence first (C-C-C). Every paragraph closes on significance ("how it matters / the difference made"), per `~/.claude/writing/academic_writing_rules.md` and the Mensh & Kording scientific-writing guide.
- Active voice; no hedging clusters; no "very/clearly/importantly" filler.
