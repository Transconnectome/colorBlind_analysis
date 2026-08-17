# `presentation/` — Single Root for All Slide Assets

All advisor-meeting and academic-deck assets live under this directory.
**Do not** reference figures from `results/` paths in slide prompts —
the canonical location for *presentation-bound* PNGs is here.

## Layout

```
presentation/
├── README.md                          (this file)
├── claude_in_ppt_prompts.md           academic 10-slide bundle (paper-style)
├── claude_in_ppt_prompts_meeting.md   advisor 4 + N supplementary (THE main doc)
└── figures/
    ├── data/          ← Channel B (Python matplotlib, axis numbers required)
    │   ├── activation_overview.png
    │   ├── model_vs_baseline.png
    │   ├── loss_inventory_summary.png
    │   ├── slide5_rc_panels.png          (Stockman-derived R+C 4-panel)
    │   └── two_comp_stretch_anatomy.png  (2-comp ±β stretch anatomy)
    └── schematics/    ← Channel C (generative AI — conceptual diagrams only)
        ├── README.md                     generation workflow + verification
        ├── slide3_model_mechanisms.png   REQUIRED — Slide 3 row 1
        ├── slide1_pipeline_inset.png     OPTIONAL — Slide 1 Q1 inset
        └── slide3_eval_pipeline.png      OPTIONAL — Slide 3 row 3 alternative
```

## 3-channel composition rule

| Channel | Use for | Tool | Lives in |
|---|---|---|---|
| **A. Native PPT text** | bullets · tables · headlines · equations · narrative | Claude-in-PPT prompt (in `claude_in_ppt_prompts_meeting.md`) | rendered in slide |
| **B. Python data figure** | numbers · bars · heatmaps · CIs · curves with axis values | `scripts/visualization/figs_*.py` | `figures/data/` |
| **C. Generative schematic** | mechanisms · pipelines · conceptual diagrams (NO axis numbers) | GPT-5 Image / nanobanana / Imagen / DALL·E | `figures/schematics/` |

**Rule of thumb**: read a *number* → channel B.  understand a *process* → channel C.  otherwise → channel A.

## Regenerate Python data figures

```bash
cd analysis/future_phase2_filter_optimization
conda activate srm

python scripts/visualization/figs_activation_overview.py
python scripts/visualization/figs_model_vs_baseline.py
python scripts/visualization/figs_loss_inventory.py
python scripts/visualization/figs_slide5_rc_panels.py
```

Each script writes directly to `presentation/figures/data/` (no need to copy or move).

## Generate AI schematics

1. Open GPT-5 Image (preferred) / nanobanana / Imagen / DALL·E.
2. Open `claude_in_ppt_prompts_meeting.md`, find the slide section's "**C. Generative schematic**" block.
3. Paste the prompt, generate 4 candidates, pick best.
4. Save to `presentation/figures/schematics/<exact filename>` per the slide's spec.
5. Verify against `figures/schematics/README.md` checklist before inserting.

## Compose slides in PowerPoint

1. Open PowerPoint with the Claude add-in.
2. For each slide, paste the corresponding "**A. Native PPT text**" prompt from `claude_in_ppt_prompts_meeting.md`.
3. Where the prompt says `[INSERT: <filename>]`, insert the matching image from `figures/data/` or `figures/schematics/` (paths are absolute in each prompt).
4. Verify against the per-slide verification checklist in the same document.

## Note on deleted assets (2026-05-04)

Five composite single-image PNGs (`slide1_summary.png`, `slide2_activation_decoder.png`,
`slide3_model_loss.png`, `slide4_status_plans.png`, `phase2_meeting_overview.png`) were
removed after migrating to the 3-channel composition. Their text content is now rendered
natively as Channel A in the corresponding slide prompts; the Python figures they embedded
are now standalone in `figures/data/`.
