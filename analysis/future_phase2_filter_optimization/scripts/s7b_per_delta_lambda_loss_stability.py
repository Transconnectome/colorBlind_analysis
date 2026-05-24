#!/usr/bin/env python3
"""
S7 (B) — Per (Δλ source, subject, ROI) loss-choice stability.

For each cell (subject × ROI × Δλ source), extract the 8 R+C g* values across
the 8 loss targets and quantify spread:

  - sd(g*), range(g*)
  - boundary hit count (g ≈ 0.0 OR g ≈ 3.0)
  - stable_count = # losses with g* in (0.5, 2.8) (interior)
  - verdict: tight   if sd ≤ 0.2
             accept. if sd ≤ 0.4
             loose   otherwise

Input  : results/s5_all_paths/sub-{08,09}_{V1,V4}_sigma21.json
Output : results/s7b_per_delta_lambda/loss_stability.json
         results/s7b_per_delta_lambda/SUMMARY.md

2-Comp fits are excluded (no Δλ parameter).

Author: colorBlind Phase 2 — auto-generated 2026-05-24
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
IN_DIR = PROJ / "results" / "s5_all_paths"
OUT_DIR = PROJ / "results" / "s7b_per_delta_lambda"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUBJECTS = ["sub-08", "sub-09"]
ROIS = ["V1", "V4"]

LOSS_ORDER = [
    "L1_behav_alpha",
    "L2_behav_gamma",
    "L3_LOCO",
    "L4_RDM_corr",
    "L5_behav_composite",
    "L6_neural_composite",
    "L7_all_equal",
    "L8_modality_5050",
]

# Boundary thresholds (R+C grid is g in [0.0, 3.0])
BOUNDARY_LO = 0.05      # g ≈ 0 (no compensation)
BOUNDARY_HI = 2.95      # g ≈ 3 (saturated overshoot)
INTERIOR_LO = 0.5
INTERIOR_HI = 2.8

SD_TIGHT = 0.20
SD_ACCEPTABLE = 0.40


def verdict_for_sd(sd: float) -> str:
    if sd <= SD_TIGHT:
        return "tight"
    if sd <= SD_ACCEPTABLE:
        return "acceptable"
    return "loose"


def is_boundary(g: float) -> bool:
    return (g <= BOUNDARY_LO) or (g >= BOUNDARY_HI)


def is_interior(g: float) -> bool:
    return (g >= INTERIOR_LO) and (g <= INTERIOR_HI)


# ----------------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------------
def analyze_cell(fits_rc: list[dict]) -> dict[str, dict]:
    """Group R+C fits by (delta_lambda_source, delta_lambda_nm), compute stats."""
    # Group: key = (source, nm)
    groups: dict[tuple, dict[str, float]] = defaultdict(dict)
    for fit in fits_rc:
        src = fit.get("delta_lambda_source")
        nm = fit.get("delta_lambda_nm")
        loss = fit.get("loss_target")
        g = fit.get("g_best")
        if src is None or nm is None or loss is None or g is None:
            continue
        groups[(src, float(nm))][loss] = float(g)

    out: dict[str, dict] = {}
    for (src, nm), per_loss in groups.items():
        # Order g* by canonical loss order, drop missing
        g_per_loss_ordered = {L: per_loss[L] for L in LOSS_ORDER if L in per_loss}
        gs = list(g_per_loss_ordered.values())

        if len(gs) < 2:
            sd = 0.0
        else:
            sd = statistics.pstdev(gs)  # population SD over 8 samples
        rng = max(gs) - min(gs) if gs else 0.0
        boundary_count = sum(1 for g in gs if is_boundary(g))
        stable_count = sum(1 for g in gs if is_interior(g))
        v = verdict_for_sd(sd)

        # Cell key e.g. "DPS_lit_6.0"
        nm_str = f"{nm:g}"
        cell_key = f"{src}_{nm_str}"
        out[cell_key] = {
            "delta_lambda_source": src,
            "delta_lambda_nm": nm,
            "n_losses": len(gs),
            "g_per_loss": g_per_loss_ordered,
            "g_min": min(gs) if gs else None,
            "g_max": max(gs) if gs else None,
            "g_median": statistics.median(gs) if gs else None,
            "sd": sd,
            "range": rng,
            "boundary_count": boundary_count,
            "stable_count": stable_count,
            "verdict": v,
        }
    return out


def best_source_per_cell(cell_blocks: dict[str, dict]) -> dict:
    """Pick the most loss-stable Δλ source within a (subject, ROI) cell.

    Selection rule:
      1. Lowest SD wins.
      2. Tie-break (SD within 0.02): higher stable_count.
      3. Further tie: smaller boundary_count.
    """
    if not cell_blocks:
        return {"winner": None, "reason": "no data"}

    items = list(cell_blocks.items())
    items.sort(
        key=lambda kv: (
            kv[1]["sd"],
            -kv[1]["stable_count"],
            kv[1]["boundary_count"],
        )
    )
    winner_key, winner = items[0]
    return {
        "winner": winner_key,
        "winner_source": winner["delta_lambda_source"],
        "winner_delta_lambda_nm": winner["delta_lambda_nm"],
        "winner_sd": winner["sd"],
        "winner_range": winner["range"],
        "winner_stable_count": winner["stable_count"],
        "winner_boundary_count": winner["boundary_count"],
        "winner_verdict": winner["verdict"],
        "ranked": [
            {
                "source_key": k,
                "sd": v["sd"],
                "stable_count": v["stable_count"],
                "boundary_count": v["boundary_count"],
                "verdict": v["verdict"],
            }
            for k, v in items
        ],
    }


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    results: dict[str, dict] = {}

    for subj in SUBJECTS:
        for roi in ROIS:
            path = IN_DIR / f"{subj}_{roi}_sigma21.json"
            if not path.exists():
                print(f"[WARN] missing {path}")
                continue
            with open(path) as fh:
                data = json.load(fh)

            fits_rc = [f for f in data.get("fits", []) if f.get("model") == "R+C"]
            cell_blocks = analyze_cell(fits_rc)
            winner = best_source_per_cell(cell_blocks)

            cell_id = f"{subj}_{roi}"
            results[cell_id] = {
                "subject": subj,
                "roi": roi,
                "n_rc_fits": len(fits_rc),
                "blocks": cell_blocks,
                "most_loss_stable": winner,
            }

    # Write JSON
    out_json = OUT_DIR / "loss_stability.json"
    with open(out_json, "w") as fh:
        json.dump(
            {
                "config": {
                    "loss_order": LOSS_ORDER,
                    "boundary_lo": BOUNDARY_LO,
                    "boundary_hi": BOUNDARY_HI,
                    "interior_lo": INTERIOR_LO,
                    "interior_hi": INTERIOR_HI,
                    "sd_tight": SD_TIGHT,
                    "sd_acceptable": SD_ACCEPTABLE,
                },
                "results": results,
            },
            fh,
            indent=2,
        )
    print(f"[ok] wrote {out_json}")

    # Build SUMMARY.md
    lines: list[str] = []
    lines.append("# S7 (B) — Per (Δλ source, subject, ROI) loss-choice stability\n")
    lines.append(
        "For each cell × Δλ source, we extract the 8 R+C g\\* values across "
        "the 8 loss targets and quantify spread.\n"
    )
    lines.append("**Thresholds**: tight SD≤0.20, acceptable SD≤0.40, loose SD>0.40. "
                 f"Boundary: g≤{BOUNDARY_LO} or g≥{BOUNDARY_HI}. "
                 f"Interior: g∈[{INTERIOR_LO}, {INTERIOR_HI}].\n")

    # Main table
    lines.append("## Main table (12 rows = 4 cells × 3 Δλ sources)\n")
    lines.append(
        "| subject | ROI | Δλ source | Δλ (nm) | SD(g) | range(g) | "
        "boundary | stable | verdict |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---|")

    for cell_id, cell in results.items():
        subj = cell["subject"]
        roi = cell["roi"]
        blocks = cell["blocks"]
        # Stable source ordering (DPS, Boehm, JND) — fall back to alphabetical
        def _sort_key(k: str) -> tuple:
            v = blocks[k]
            src = v["delta_lambda_source"]
            rank = {"DPS_lit": 0, "Boehm_mid": 1, "Boehm_low": 1, "JND_Lamb": 2}.get(src, 99)
            return (rank, k)

        for key in sorted(blocks.keys(), key=_sort_key):
            b = blocks[key]
            lines.append(
                f"| {subj} | {roi} | {b['delta_lambda_source']} | "
                f"{b['delta_lambda_nm']:.1f} | {b['sd']:.3f} | {b['range']:.3f} | "
                f"{b['boundary_count']} | {b['stable_count']}/8 | {b['verdict']} |"
            )
    lines.append("")

    # Per-cell winners
    lines.append("## Most loss-stable Δλ per cell\n")
    lines.append(
        "Selection: lowest SD wins; tie-break by higher stable_count then lower boundary_count.\n"
    )
    lines.append("| subject | ROI | best Δλ source | Δλ (nm) | SD | stable | boundary | verdict |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|")
    for cell_id, cell in results.items():
        w = cell["most_loss_stable"]
        if not w.get("winner"):
            lines.append(f"| {cell['subject']} | {cell['roi']} | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {cell['subject']} | {cell['roi']} | {w['winner_source']} | "
            f"{w['winner_delta_lambda_nm']:.1f} | {w['winner_sd']:.3f} | "
            f"{w['winner_stable_count']}/8 | {w['winner_boundary_count']} | "
            f"{w['winner_verdict']} |"
        )
    lines.append("")

    # Per-cell g* matrix (loss x source) — for paper appendix
    lines.append("## Per-cell g\\* matrices (rows = loss, columns = Δλ source)\n")
    for cell_id, cell in results.items():
        blocks = cell["blocks"]
        if not blocks:
            continue
        ordered_keys = sorted(blocks.keys(), key=lambda k: (
            {"DPS_lit": 0, "Boehm_mid": 1, "Boehm_low": 1, "JND_Lamb": 2}.get(
                blocks[k]["delta_lambda_source"], 99
            ),
            k,
        ))
        lines.append(f"### {cell['subject']} {cell['roi']}\n")
        header = ["loss"] + [f"{blocks[k]['delta_lambda_source']} ({blocks[k]['delta_lambda_nm']:.1f}nm)"
                              for k in ordered_keys]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for L in LOSS_ORDER:
            row = [L]
            for k in ordered_keys:
                g = blocks[k]["g_per_loss"].get(L)
                row.append(f"{g:.2f}" if g is not None else "—")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    out_md = OUT_DIR / "SUMMARY.md"
    out_md.write_text("\n".join(lines))
    print(f"[ok] wrote {out_md}")

    # Console summary
    print("\n=== Per-cell winners ===")
    for cell_id, cell in results.items():
        w = cell["most_loss_stable"]
        if not w.get("winner"):
            print(f"  {cell_id}: NO DATA")
            continue
        print(
            f"  {cell_id:>11}: {w['winner_source']:<10} "
            f"Δλ={w['winner_delta_lambda_nm']:>4.1f}nm  "
            f"SD={w['winner_sd']:.3f}  stable={w['winner_stable_count']}/8  "
            f"boundary={w['winner_boundary_count']}  → {w['winner_verdict']}"
        )

    print("\n=== Full 12-row table ===")
    print(f"  {'cell':<12}{'src':<11}{'Δλ':>6}{'SD':>7}{'rng':>7}{'bnd':>5}{'stbl':>6}  verdict")
    for cell_id, cell in results.items():
        blocks = cell["blocks"]
        for key in sorted(blocks.keys(), key=lambda k: (
            {"DPS_lit": 0, "Boehm_mid": 1, "Boehm_low": 1, "JND_Lamb": 2}.get(
                blocks[k]["delta_lambda_source"], 99
            ),
            k,
        )):
            b = blocks[key]
            print(
                f"  {cell_id:<12}{b['delta_lambda_source']:<11}"
                f"{b['delta_lambda_nm']:>5.1f}"
                f"{b['sd']:>7.3f}{b['range']:>7.3f}"
                f"{b['boundary_count']:>5d}{b['stable_count']:>5d}/8  {b['verdict']}"
            )


if __name__ == "__main__":
    main()
