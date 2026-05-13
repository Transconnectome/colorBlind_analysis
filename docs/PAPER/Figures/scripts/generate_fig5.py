"""
Figure 5 — Phase 2 BEST personalized filter output (V4-CCC + λ·l_topk).

Layout: side-by-side BEST_4col canonical visualizations for the two CVD
subjects (Phase 2 closure 2026-05-12). Each subject's 4-column panel shows
per-hue (1) original stimulus, (2) what the subject perceives without filter,
(3) the filter output (pre-image displayed to the screen), and (4) what the
subject perceives once the filter output is sent to their display.

Selection criterion (per future_phase2_filter_optimization/CLAUDE.md §0):
    LOCO-best descriptive fit + behavioral validation (P2a).
    Specificity is DESCRIPTIVE only — never a selection criterion.

Canonical params (results/BEST_summary.json):
    sub-08 deutan : β_s = 44°, β_c = +28°   norm = 52.2°   P2a = 0.575   exact = 4/8
    sub-09 protan : β_s = 30°, β_c = +46°   norm = 54.9°   P2a = 0.650   exact = 3/8

Source images (canonical, byte-identical to Phase 2 closure):
    results/BEST_4col_sub-08_V4_V4CCCltopk_bs44_bc+28.png
    results/BEST_4col_sub-09_V4_V4CCCltopk_bs30_bc+46.png
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import image as mpimg

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE       = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/"
                  "Projects/colorBlind_analysis")
PHASE2_RES = BASE / "analysis/future_phase2_filter_optimization/results"
OUT_DIR    = BASE / "docs/PAPER/Figures"

PNG_08 = PHASE2_RES / "BEST_4col_sub-08_V4_V4CCCltopk_bs44_bc+28.png"
PNG_09 = PHASE2_RES / "BEST_4col_sub-09_V4_V4CCCltopk_bs30_bc+46.png"
SUMMARY = json.load(open(PHASE2_RES / "BEST_summary.json"))

s08 = SUMMARY["subjects"]["sub-08"]
s09 = SUMMARY["subjects"]["sub-09"]

# ─── Style ───────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":        7,
    "pdf.fonttype":     42,
    "ps.fonttype":      42,
    "savefig.dpi":      300,
})

# Subject colors (same as Fig 2/4)
C08 = "#E07840"   # warm orange — sub-08 deutan
C09 = "#2AADA8"   # teal       — sub-09 protan

# ─── Figure ──────────────────────────────────────────────────────────────────
FIG_W = 180 / 25.4   # 7.087 in (Nature double-column width)
FIG_H = 150 / 25.4   # 5.91 in

fig = plt.figure(figsize=(FIG_W, FIG_H))

# Top banner — inverse-mapping schematic
fig.text(0.5, 0.965,
         "Inverse color mapping:   stim θ   ──(T⁻¹)──►   "
         "filter output θ+δθ   ──(CVD cortex)──►   perception = HC at θ",
         ha="center", va="top", fontsize=8.5, color="#222")
fig.text(0.5, 0.935,
         "Per-subject 2-component filter — argmin of  "
         "L = L_CCC(V4) + λ·l_top-K(V4, K=3) + 0.1·Tikh  "
         "(V4 LOCO only; λ ∈ [0.25, 2.0]).",
         ha="center", va="top", fontsize=6.5, color="#666", style="italic")

# Layout: two panels side by side, each holds one BEST_4col PNG
ax_a = fig.add_axes([0.04, 0.05, 0.45, 0.85])
ax_b = fig.add_axes([0.52, 0.05, 0.45, 0.85])

for ax, png, color, subj_id, cvd_type, params in [
    (ax_a, PNG_08, C08, "sub-08", "deutan", s08),
    (ax_b, PNG_09, C09, "sub-09", "protan", s09),
]:
    img = mpimg.imread(png)
    ax.imshow(img, aspect="equal")
    ax.axis("off")

# Panel letters A, B in figure coordinates
fig.text(0.03, 0.905, "A", fontsize=11, fontweight="bold", color=C08, va="top", ha="left")
fig.text(0.51, 0.905, "B", fontsize=11, fontweight="bold", color=C09, va="top", ha="left")

# Bottom caption — descriptive specificity reporting per §0
caption = (
    "L_CCC penalises rank discordance + mean/variance mismatch jointly "
    "(stricter than Spearman or Pearson alone); l_top-K enforces identity of "
    "the 3 most-vulnerable colors. "
    "Filter norms (52.2°, 54.9°) lie inside the HC LOO range [49.0°, 65.3°]; "
    "specificity is reported descriptively only (HC FPR = 100% under label-"
    "permutation precludes formal specificity claims)."
)
fig.text(0.5, 0.01, caption, ha="center", va="bottom",
         fontsize=6.0, color="#444", style="italic", wrap=True)

# ─── Save ────────────────────────────────────────────────────────────────────
out_png = OUT_DIR / "fig5_preimage.png"
out_pdf = OUT_DIR / "fig5_preimage.pdf"
fig.savefig(out_png, dpi=300, bbox_inches="tight")
fig.savefig(out_pdf, bbox_inches="tight")
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")

# ─── Sanity check printout ───────────────────────────────────────────────────
print()
print(f"sub-08  β=({s08['bs']:.0f}, {s08['bc']:+.0f})  "
      f"norm={s08['norm']:.1f}°  P2a={s08['p2a']:.3f}  exact={s08['exact']}/8")
print(f"sub-09  β=({s09['bs']:.0f}, {s09['bc']:+.0f})  "
      f"norm={s09['norm']:.1f}°  P2a={s09['p2a']:.3f}  exact={s09['exact']}/8")
