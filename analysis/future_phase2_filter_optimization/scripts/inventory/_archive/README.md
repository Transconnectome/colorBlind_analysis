# inventory/_archive/ — Pre-closure inventory builders

5 scripts moved 2026-05-28 (Phase B'). None of these is referenced by any
active doc; their outputs were consumed by Phase B v6 closure and superseded.

| File | Role |
|---|---|
| `build_cvd_individual_confusion.py` | Per-CVD confusion table; absorbed into v6 RDM atom |
| `build_decoder_loco_csv.py` | LOCO CSV builder; superseded by v6 outputs in `results/s10_inclusion/` |
| `build_loss_inventory.py` | Cycle 15 loss inventory (CLAUDE.md §2.5 historical) |
| `cycle14_ci_analysis.py` | Cycle 14 — superseded by cycle 15 inventory (CLAUDE.md §5) |
| `cycle14_v1rdm_only_analysis.py` | Cycle 14 V1-RDM only — same as above |

The `results/inventory/loss_inventory.{md,csv}` outputs they produced
remain at their original location (referenced by CLAUDE.md §2.5 only as
historical context).
