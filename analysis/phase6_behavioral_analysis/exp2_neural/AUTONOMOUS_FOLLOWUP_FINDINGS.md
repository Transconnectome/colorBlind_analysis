# exp2 autonomous follow-up findings (2026-07-01)

Triggered by: sub-09 neural results far weaker than behavior; user asked to try every
follow-up analysis, judge significance, and derive next experiments. Scripts:
`scripts/exp2_followup_analyses.py` (server), local behavioral combination.

## TL;DR (honest bottom line)
**No domain shows a statistically significant Optimal-over-Window advantage at N=2.**
The neural-geometry-restoration claim is NOT supported by any RDM metric, and the HC
geometry *target itself* is unreliable at hV4. Robust results are the CHARACTERIZATION
(group, exp1) and the METHOD. Validation (exp2) is proof-of-concept, underpowered.

---

## 1. Reliability of the n=4-run LOCO estimate (is sub-09 hV4 just noise?)
exp1 no-filter, all C(6,4)=15 four-run subsets, hV4 LOCO adj:
- sub-09: mean 0.138, sd **0.028**, range [0.094, 0.188] → the estimate is fairly STABLE.
- Condition LOO-run(3) stability: sub-09 hV4 **Optimal = [0.083,0.042,0.042,0.042]** (mean 0.052, sd 0.018) — robustly low, NOT a noise artifact.
→ Cannot dismiss sub-09 hV4 as "n=4 noise." The low value is real. Defense must be
target-unreliability + run-position confound + floor + discriminability-intact, NOT noise.

## 2. Neural geometry (model-free voxel corr-dist RDM) → HC — NO Optimal restoration
voxel-RDM Spearman to HC-mean (HC self-consistency floor in brackets):
| ROI | HCself | sub-09 NF/Win/Opt | sub-08 NF/Win/Opt |
|---|---|---|---|
| V1 | 0.132 | −0.04 / **0.48** / −0.08 | 0.18 / 0.10 / 0.06 |
| V2 | 0.101 | 0.18 / **0.41** / 0.15 | **0.52** / −0.09 / −0.19 |
| V3 | 0.159 | **0.48** / 0.09 / 0.24 | 0.33 / −0.02 / −0.24 |
| hV4 | **−0.036** | 0.14 / **0.18** / −0.12 | 0.14 / −0.11 / −0.06 |
- **No condition pattern favors Optimal.** Where anything is high it's Window (sub-09 V1/V2) or no-filter (sub-08 V2/V3).
- **hV4 HC self-consistency = −0.036**: HC subjects do not agree with each other on the hV4 voxel RDM → there is no reliable hV4 geometry target to restore toward. (Same conclusion as SRM-RDM: hV4 HCself ρ=0.157.)

## 3. Neural–behavioral isomorphism (reduced, 8 JND pairs) — not measurable at hV4
Spearman(hV4 neural pair-dissim, behavioral JND):
- **HC-neural ~ HC-behavioral ρ = −0.33** (the CEILING) → even in HC, hV4 neural geometry does not match perceptual geometry on these pairs. The second-order isomorphism is undefined at hV4 with current data.
→ Reduced isomorphism fails; full version needs a proper 28-pair behavioral RDM (not collected).

## 4. Behavioral structure (JND pattern over 8 pairs) — suggestive, NOT significant
- Spearman of condition JND vector to HC ordering: sub-09 Opt **0.905** > NF 0.810 > Win 0.524; sub-08 NF 0.755 > Opt 0.711 > Win 0.667. (Window consistently worst at preserving structure.)
- But per-pair |JND−HC| test: Optimal closer than Window in **9/16** pooled, **Wilcoxon p=0.63 (ns)**; mean|dev| Win 0.054 vs Opt 0.046.
- Descriptive mechanism: Window introduces specific large distortions Optimal avoids — sub-09 green-blue (Win 0.242 vs HC 0.079; Opt 0.107), cyan-magenta (Win 0.145 vs HC 0.042; Opt 0.018).
→ Suggestive that Window distorts specific pairs while Optimal preserves structure, but not significant at N=2 / 8 pairs.

## 5. Behavioral means (recap) — parity
- sub-08 JND: NF 0.187 → Win 0.080 ≈ Opt 0.080; RSVP 0.81 → 0.97 = 0.97. (both filters help deutan; Opt=Win)
- sub-09 JND: NF 0.097 (best) → Win 0.115, Opt 0.109; RSVP 1.00 → Win 0.86, Opt 0.98. (protan at ceiling; Window hurts RSVP, Optimal doesn't)
- Wilcoxon Opt vs Win: p>0.5 both subjects.

---

## 2b. Cross-check across 4 RDM estimators (corr-dist, crossnobis, euclidean, SRM)
Crossnobis (cross-validated, noise-normalized; most reliable) + euclidean confirm the corr-dist conclusion:
- **hV4 (deficit ROI): NO Optimal restoration in ANY estimator, either subject** (Optimal negative/worst; crossnobis hV4 HCself +0.128 so the estimator is fine — the absence of restoration is real).
- Only isolated positive thread: **sub-09 V1** crossnobis NF −0.370 → Opt +0.019; euclidean NF −0.361 → Opt +0.185 (Optimal pulls strongly anti-HC V1 geometry to ~HC floor). But V1 is not the hue-interpolation ROI, HC V1 self-consistency ~0.10, single subject.
- Everywhere else the best condition is Window or no-filter, not Optimal.

## What is significant / supported
- **Characterization** (CVD = structural/geometric distortion, not signal weakening): strong, group-level, unchanged.
- **Method** (personalized inverse-filter): contribution, unchanged.
- **Optimal is non-inferior to Window** behaviorally; **Window introduces specific perceptual distortions** Optimal avoids (descriptive).
- **Negative/limiting**: no significant Optimal>Window in any domain at N=2; neural geometry restoration unsupported; hV4 geometry target unreliable (HC self ≈ 0 across voxel-RDM, SRM-RDM, neural-behavioral).

## How this affects the narrative
- Cannot claim "filter restores HC-like neural geometry" or "beats macOS filter." Must reframe to characterization + method + proof-of-concept (non-inferiority + structure preservation).
- The hV4 geometry-target unreliability is itself a methodological finding → motivates better measurement (more runs / better RDM estimator) before any single-subject geometry-restoration claim.

## 6. Pair-selectivity (the strongest result) — protan only
Behavioral |JND−HC| on MODEL-PREDICTED vulnerable (HYPO) pairs vs control pairs:
- **sub-09 (protan)**: HYPO {green-blue, cyan-magenta} Window |dev|=**0.133** vs control 0.031 → Window SELECTIVELY harms the protan-confusion pairs; Optimal recovers them (HYPO |dev|=0.026). Window HYPO-selective distortion +0.102, Optimal HYPO recovery +0.107.
- **sub-08 (deutan)**: NO selectivity (Optimal WORSE on its HYPO pairs, recovery −0.037). Deutan well-served by both filters.
→ **Pipeline-confound-resistant personalization evidence, but PROTAN-ONLY, N=1, descriptive.** A uniform rendering-path difference (macOS-OS Window vs PsychoPy Optimal) would NOT be pair-selective on the protan axis. Caveat: HYPO pairs partly chosen from sub-09's own Phase1-2 data (circular for "Optimal recovers"; NOT for "generic Window harms").

## 7. PIPELINE CONFOUND (confirmed, important)
Window = macOS OS-level color filter; Optimal = PsychoPy-rendered pre-image → DIFFERENT rendering paths. Any Optimal−Window difference could be rendering, not filter content. Controls: cross-subject filter swap (both PsychoPy) + photometry of the 8 colors under each path.

## 8. V1/V2 LOCO ρ favors Optimal — but in the null/uninterpretable regime
sub-09 V1 Opt ρ=+0.129(=HC) vs Win −0.096; V2 Opt +0.193 vs Win −0.068. sub-08 V1 Opt +0.212 vs Win −0.318. Consistent Opt>Win>NF BOTH subjects. BUT V1/V2 LOCO is permutation-null (discrimination-only) per frozen framework → suggestive/corroborative only, needs exp2-condition permutation null to interpret. Do NOT make primary.

## Follow-up experiments motivated (see synthesis)
1. Full 28-pair behavioral perceptual-geometry RDM (MLDS or pairwise similarity) → enables neural-behavioral isomorphism.
2. N up (≥3-4 per phenotype) to break N=2 / deutan-protan heterogeneity.
3. Deconfound ABBA run-position (true randomized interleaving or more runs).
4. Floored protan task (sub-09 ceiling) — harder discrimination so baseline isn't at 1.0.
5. Reconsider loss: mean-behavior parity but structure hints → weight structural/RDM term, validate on STRUCTURE not threshold.
