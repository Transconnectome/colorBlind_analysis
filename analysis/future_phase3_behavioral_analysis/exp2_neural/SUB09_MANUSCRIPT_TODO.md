# sub-09 exp2 — manuscript/pipeline conflict points (Option C documentation)

Created 2026-06-30 when sub-09 exp2 was processed (Stage 0–3). The live paper was written
**sub-08-only and explicitly states "the protan participant was not collected."** Adding
sub-09 converts the filter-validation section from single-case (deutan) to **N=2** and
collides with several existing statements. None blocks the *analysis* (methods are
identical and consistent); these are **writeup edits** to make once sub-09 numbers are final.

Source of truth = paper-consistency audit (2026-06-30) against the LIVE files
`docs/PAPER/main.tex` → `Methods/methods_v2.tex`, `Results/results_v4.tex`,
`Methods/supplementary_content.tex`, `Supplementary/S16_filter_eval_design.tex`.
(`Results/results_v3.tex` and both ICML `SD4H_cameraready_*` are NOT live for exp2 — ignore.)

## C1 — Scope: "protan not collected" is now FALSE  ⬛ must edit
- `methods_v2.tex:263` — "the protan participant was not collected."
- `results_v4.tex:189` — "(the protan participant was not collected)."
- `methods_v2.tex:48` — "The deutan participant additionally completed a second session…"
- `main.tex:71` (abstract) — "second session in the deutan participant".
- → Rewrite to N=2: both CVD subjects completed the second session; report deutan + protan.

## C2 — Abstract behavioral "parity" over-generalizes  ⬛ must edit
- `main.tex:71` — "both filters restored behavioral discrimination comparably" (no subject qualifier).
- Body `results_v4.tex:216` is correctly deutan-scoped ("the deutan participant's discrimination"), so it survives.
- **sub-09 (protan) BREAKS the parity generalization**: Optimal > Window — the deployed macOS
  filter actively HARMS protan (8AFC 1.00→0.86; introduces green→cyan + new cyan-magenta JND
  deficit), while Optimal preserves HC-like performance. Crawford-Howell standard.
- → Re-scope abstract: "in the deutan, both filters restored discrimination comparably; in the
  protan (already near-HC), the personalized filter preserved performance while the deployed
  filter degraded it." This STRENGTHENS the personalization argument (one-size-fits-all can harm).

## C3 — Primary endpoint framing (pipeline docs vs paper)  ✅ fixed in code/docs
- Paper PRIMARY = **hV4 LOCO adjacent accuracy** (`results_v4.tex:189`, `methods_v2.tex:265`);
  forward-tuning ρ = corroboration only (`results_v4.tex:191`). Reflects the 2026-06-28 correction.
- Stale "V1 primary" framing existed in `exp2_neural/RESULTS.md:19` and the script summary print
  → FIXED 2026-06-30: RESULTS.md correction banner added; `exp2_hc_likeness.py` summary now labels
  ρ-table "CORROBORATION" and the adjacent-accuracy table "*** PRIMARY ENDPOINT (hV4) ***".
- → When writing sub-09: headline **hV4 LOCO adjacent accuracy**, ρ as corroboration.

## C4 — Counterbalancing text is missing & must be added  ⬛ add sentence
- Paper only says generic "ABBA-counterbalanced, four runs per filter" (`S16:13`); no run→condition
  map, no per-subject mirror.
- Actual maps (verified from per-run info.json): sub-08 W O O W W O O W (Window {1,4,5,8});
  **sub-09 mirror O W W O O W W O (Optimal {1,4,5,8}, Window {2,3,6,7})**.
- → Add an explicit per-subject counterbalancing sentence (and confirm the recorded sub-08 map
  matches, since the paper never wrote it down).

## C5 — Label mapping (terminology only, no conflict)  ✅ confirmed
- Paper labels = "personalized filter" vs "deployed macOS accessibility filter".
- Internal labels = **Optimal = personalized (PsychoPy δθ render)**, **Window = deployed macOS
  OS-level filter** (sub-09 behav filenames "window_no_filter" confirm OS-level, PsychoPy renders none).
- Design matches sub-08 (personalized-vs-macOS). Just map the terms in the writeup.

## Methods that are ALREADY consistent (no edit) ✅
FE-6 uniform basis; OLS-pseudoinverse (α=0) decoding accuracy; ridge-GCV forward-tuning ρ;
per-condition Procrustes; SRM K={4,4,3,3}; HC subsampled to 4 runs; Cohen's d (no perm p).
All match the sub-08 scripts used for sub-09 verbatim.
