# Advisor-Meeting PPT Prompt Bundle (1 + 1 slides)

**Date**: 2026-05-04
**Scope**: Phase 2 status briefing for advisor — pipeline / models+loss / status+limits / next steps.
**Format**: 1 main one-page summary slide (Slide M1) + 1 supporting loss-inventory slide (Slide M2).

**Companion 10-slide bundle** (already exists for academic audience): `claude_in_ppt_prompts.md`. Do **not** confuse with this meeting bundle.

**Global style directive** (apply to every slide):
> Style: academic, 16:9, sans-serif, minimal chrome, single blue accent (#1f4e79). Body text >= 14pt; headings 16pt bold. Do NOT generate new images. Use only the referenced absolute file paths verbatim.

---

## Slide M1 — Phase 2 one-page overview (single image)

```
Create slide M1 titled
"Phase 2 — Personalized Inverse Filter for CVD: Pipeline · Models · Status · Next" (subtitle date 2026-05-04).

Layout: ONE full-bleed image, no body text, no caption.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/visualizations/meeting/phase2_meeting_overview.png

Position: centered, fill 100% of slide width, preserve aspect ratio.
The image already contains a 2x2 quadrant layout (Pipeline / Models+Loss / Status+Limits / Next Steps),
internal title bar, and footer references. Do NOT add a separate slide title or caption.

Style: 16:9, minimal chrome, no border, no shadow. Do NOT generate new visuals.
```

**Why a single image (not native PPT shapes)**: every quadrant carries dense, version-controlled content tied to project markdown — keeping it as one matplotlib-rendered PNG guarantees the figure stays in sync with `CLAUDE.md`, `README.md`, and `loss_inventory.md`. The script `scripts/figs_meeting_overview.py` regenerates it in <2s if numbers change.

---

## Slide M2 — Loss inventory + HC sanity (supporting evidence)

```
Create slide M2 titled
"Loss Inventory — How We Picked the Filter Candidates  (Cycle 15 mw_jaccard cross-validation)".

Layout: ONE full-bleed image, with a 2-line bullet block below it (8pt area).

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/visualizations/meeting/loss_inventory_summary.png

Position: centered, ~92% slide width.

Bullets below image (2 lines, condensed):
- 12 loss variants × 8 subjects (HC pool n=6 effective at hV4) ranked by HC sanity (emp_p <= 0.20 = CVD outlier above HC distribution)
- Two losses pass for BOTH CVD subjects: `cycle15_opt2` = 2*mw_jaccard(V4) + 1*l_rank(V1)  AND  `mw_jaccard_loss` (V4 only) → cross-validate (β_s=68°, β_c=−38°) for sub-08 and (β_s=44°, β_c=+54°) for sub-09

Footer (small italic):
results/loss_inventory.md (build_loss_inventory.py, 2026-05-03) · 10000-resample bootstrap on HC means.

Style: 16:9, single blue accent, minimal chrome, no clip-art. Do NOT generate new visuals.
```

**Why this slide is separate**: it is the *evidence* behind two specific cells in Slide M1's Q3 (sub-09 NEW candidate (44°, +54°)) and Q4 (sub-08 4-way comparison rationale). Show on demand if advisor asks "why this filter and not that one?".

---

## Speaking notes (reading order, not on slides)

### Slide M1 — read in this order with the advisor

1. **Header strip**: "Personalized Inverse Filter for CVD" — restate the SRQ in one sentence.
2. **Q1 (top-left, Pipeline)**: walk through Phase A → B → C; emphasize the **3-phase separation** (fit ≠ derive ≠ verify) — this is the design lesson from the ΔRDM inverse failure.
3. **Q2 (top-right, Models + Loss)**: 3 models are **fixed by assumption A2**; loss has **L_improve excluded from fit** (post-fit sanity only). Highlight 2-Component row (only one with both PASS at sub-08 and significant at sub-09).
4. **Q3 (bottom-left, Status × Limits)**: per-subject status with badges (sub-08 OK, sub-09 pending, sub-10 excluded). Then move to **3 critical limits** — be honest about specificity abandonment, n=6 pool, and 8-color resolution cap.
5. **Q4 (bottom-right, Next Steps)**: priority-ordered. The two HIGH items both gate Phase 2 closure — sub-09 behavioral and sub-08 4-way comparison. Phase 3 is contingent on sub-09 PASS.

### Slide M2 — only if asked

- "How did you decide between (38°, −14°) and (68°, −38°) for sub-08, or between (6°, −22°) and (44°, +54°) for sub-09?"
- Answer with the left panel: PASS+ losses (cycle15_opt2 and mw_jaccard alone) consistently land sub-08 at (68, −38) and sub-09 at (44, +54). The behavioral test is the final arbiter, not the loss alone.

---

## Verification checklist (before pasting)

- [ ] Slide M1 references `phase2_meeting_overview.png` (verified to exist 2026-05-04)
- [ ] Slide M2 references `loss_inventory_summary.png` (verified to exist 2026-05-04)
- [ ] Two prompts use ABSOLUTE Mac paths (already done above)
- [ ] No prompt asks Claude-in-PPT to generate new imagery
- [ ] sub-10 mentioned only as "excluded" (per CLAUDE.md rule §7)
- [ ] No specificity claim — only descriptive HC sanity emp_p reporting (per CLAUDE.md rule §6)
- [ ] Two figures are regenerable: `python scripts/figs_meeting_overview.py` and `python scripts/figs_loss_inventory.py`

---

## Regeneration

If numbers change after this meeting:

```bash
cd analysis/future_phase2_filter_optimization
conda activate srm
python scripts/figs_meeting_overview.py     # → results/figures/meeting/phase2_meeting_overview.png
python scripts/figs_loss_inventory.py        # → results/figures/meeting/loss_inventory_summary.png
```

Both scripts read directly from `results/loss_inventory.csv` and hardcoded summary stats from `CLAUDE.md` §3, §2.5. Update those source-of-truth files first; then regenerate.
