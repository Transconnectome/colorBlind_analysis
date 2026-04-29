"""
Literature convergence visualization:
1. β_s bootstrap distributions vs Emery 2021 (21.4°)
2. Cortical compensation hierarchy (Tregillus 2021)
3. Cross-method convergence summary
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results" / "2component_comprehensive_v2"
FIG_DIR = Path(__file__).parent.parent / "results" / "figures" / "literature_convergence"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load data
with open(RESULTS_DIR / "sub-08_2component_results.json") as f:
    d08 = json.load(f)
with open(RESULTS_DIR / "sub-09_2component_results.json") as f:
    d09 = json.load(f)

EMERY_BETA_S = 21.4  # degrees


# --- Figure 1: β_s bootstrap distributions vs Emery 2021 ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

for ax, data, subj, color, cvd_type in [
    (axes[0], d08, "sub-08", "#2196F3", "deutan"),
    (axes[1], d09, "sub-09", "#FF5722", "protan"),
]:
    bs_dist = np.array(data["bootstrap_V1"]["beta_s_dist"])
    bs_mean = data["bootstrap_V1"]["beta_s_mean"]
    bs_ci = data["bootstrap_V1"]["beta_s_ci95"]

    ax.hist(bs_dist, bins=30, color=color, alpha=0.6, edgecolor="white", linewidth=0.5,
            density=True, label=f"Bootstrap (n=500)")

    ax.axvline(bs_mean, color=color, linewidth=2, linestyle="-",
               label=f"Mean = {bs_mean:.1f}°")
    ax.axvline(EMERY_BETA_S, color="#4CAF50", linewidth=2.5, linestyle="--",
               label=f"Emery 2021 = {EMERY_BETA_S}°")

    ax.axvspan(bs_ci[0], bs_ci[1], alpha=0.15, color=color,
               label=f"95% CI [{bs_ci[0]:.0f}°, {bs_ci[1]:.0f}°]")

    ax.set_title(f"{subj} ({cvd_type})\nβ_s = {bs_mean:.1f}° (Emery B-Y phase = {EMERY_BETA_S}°)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("β_s (S-cone axis dilation, degrees)", fontsize=11)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_xlim(-5, 55)

axes[0].set_ylabel("Density", fontsize=11)

fig.suptitle(
    "Cross-Method Agreement: fMRI β_s (dilation) vs Behavioral B-Y Phase (Emery et al. 2021)",
    fontsize=14, fontweight="bold", y=1.02
)
fig.tight_layout()
fig.savefig(FIG_DIR / "beta_s_emery_convergence.png", dpi=200, bbox_inches="tight")
print(f"Saved: {FIG_DIR / 'beta_s_emery_convergence.png'}")
plt.close()


# --- Figure 2: Cortical compensation hierarchy (Tregillus 2021) ---
fig, ax = plt.subplots(figsize=(10, 6))

# Tregillus data
rois = ["V1", "V2v", "V3v"]
amp_factors = [2.94, 6.39, 7.82]
amp_sds = [2.81, 5.21, 5.76]
p_values = [0.04, 0.62, 1.00]
at_vs_cn = ["AT < CN", "AT ≈ CN", "AT ≈ CN"]

x = np.arange(len(rois))
bars = ax.bar(x, amp_factors, yerr=amp_sds, width=0.5,
              color=["#EF5350", "#66BB6A", "#66BB6A"],
              edgecolor="black", linewidth=0.8, capsize=8, alpha=0.85)

ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=1.5, label="Reduction model (no compensation)")

for i, (roi, amp, p, label) in enumerate(zip(rois, amp_factors, p_values, at_vs_cn)):
    p_text = f"p={p:.2f}" if p < 0.05 else f"p={p:.2f} (NS)"
    ax.text(i, amp + amp_sds[i] + 0.5, f"{label}\n{p_text}", ha="center", fontsize=10,
            fontweight="bold" if p < 0.05 else "normal")

ax.annotate("", xy=(2.3, 7.82), xytext=(0.7, 2.94),
            arrowprops=dict(arrowstyle="->", color="#1565C0", linewidth=2.5, linestyle="-"))
ax.text(1.7, 3.5, "Progressive\namplification", fontsize=11, color="#1565C0",
        fontweight="bold", rotation=25)

# Our g parameter
ax.annotate("Our sub-09: g = −1.10\n(10% overcompensation)",
            xy=(2.0, 8.5), fontsize=10, color="#E65100",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF3E0", edgecolor="#E65100"),
            ha="center")

ax.set_xticks(x)
ax.set_xticklabels(rois, fontsize=13, fontweight="bold")
ax.set_ylabel("Amplification Factor\n(AT CRF / Reduction Model)", fontsize=12)
ax.set_title("Cortical Compensation Hierarchy in Anomalous Trichromats\n(Tregillus et al. 2021, Current Biology)",
             fontsize=14, fontweight="bold")
ax.legend(fontsize=10, loc="upper left")
ax.set_ylim(0, 16)

fig.tight_layout()
fig.savefig(FIG_DIR / "tregillus_compensation_hierarchy.png", dpi=200, bbox_inches="tight")
print(f"Saved: {FIG_DIR / 'tregillus_compensation_hierarchy.png'}")
plt.close()


# --- Figure 3: Combined convergence summary ---
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

# Panel A: β_s convergence
ax = axes[0]
methods = ["Emery 2021\n(Behavioral\nhue scaling)", "This study\n(fMRI ΔRDM)\nsub-08", "This study\n(fMRI ΔRDM)\nsub-09"]
values = [EMERY_BETA_S, d08["bootstrap_V1"]["beta_s_mean"], d09["bootstrap_V1"]["beta_s_mean"]]
errors_lo = [0, values[1] - d08["bootstrap_V1"]["beta_s_ci95"][0],
             values[2] - d09["bootstrap_V1"]["beta_s_ci95"][0]]
errors_hi = [0, d08["bootstrap_V1"]["beta_s_ci95"][1] - values[1],
             d09["bootstrap_V1"]["beta_s_ci95"][1] - values[2]]
colors_a = ["#4CAF50", "#2196F3", "#FF5722"]

bars = ax.bar(range(3), values, yerr=[errors_lo, errors_hi],
              color=colors_a, alpha=0.8, edgecolor="black", linewidth=0.8, capsize=6, width=0.6)
ax.axhline(y=EMERY_BETA_S, color="#4CAF50", linestyle="--", linewidth=1.5, alpha=0.6)

for i, v in enumerate(values):
    ax.text(i, v + errors_hi[i] + 1.5, f"{v:.1f}°", ha="center", fontsize=11, fontweight="bold")

ax.set_xticks(range(3))
ax.set_xticklabels(methods, fontsize=9)
ax.set_ylabel("β_s (degrees)", fontsize=12)
ax.set_title("A. S-Cone Axis Change\n~20° Scale Agreement", fontsize=12, fontweight="bold")
ax.set_ylim(0, 45)

# Panel B: Tregillus g parameter
ax = axes[1]
g_labels = ["Tregillus\nrange\n(V2v/V3v)", "This study\nsub-09\n(R+C V1)"]
g_vals = [-1.3, -1.10]
g_range = [[-1.4, -1.2], [-1.10, -1.10]]

ax.barh(0, abs(g_vals[0]), height=0.4, color="#66BB6A", alpha=0.8, edgecolor="black", left=0)
ax.barh(0, 0.2, height=0.6, color="#66BB6A", alpha=0.3, edgecolor="#66BB6A", linestyle="--", left=1.0)
ax.barh(1, abs(g_vals[1]), height=0.4, color="#FF5722", alpha=0.8, edgecolor="black", left=0)

ax.text(abs(g_vals[0]) + 0.05, 0, f"g ≈ −1.2 to −1.4\n(20-40% overcomp)", va="center", fontsize=10)
ax.text(abs(g_vals[1]) + 0.05, 1, f"g = −1.10\n(10% overcomp)", va="center", fontsize=10)

ax.axvline(x=1.0, color="gray", linestyle="--", linewidth=1.5, label="Exact compensation (g=−1)")
ax.set_yticks([0, 1])
ax.set_yticklabels(g_labels, fontsize=10)
ax.set_xlabel("|g| (compensation magnitude)", fontsize=11)
ax.set_title("B. Cortical Opponent Gain\ng Parameter", fontsize=12, fontweight="bold")
ax.legend(fontsize=9, loc="lower right")
ax.set_xlim(0, 2.0)

# Panel C: Cross-phase convergence
ax = axes[2]
phases = ["Phase 2\n(SRM)", "Future Ph.1\n(Forward)", "Future Ph.2\n(Filter)", "Future Ph.3\n(Behav.)"]
metrics = ["Crawford-\nHowell", "LOCO\nvulnerability", "2-Component\nβ_s", "LOCO→JND\nconcordance"]
results = ["sub-08 V2 p=0.040*\nsub-09 V1 p=0.007*",
           "orange/yellow/purple\nCrawford-Howell p<0.02",
           "20-23° ↔ Emery 21.4°\n(~20° scale, directional)",
           "3/3 = 100%\n(HC N invariant)"]
status_colors = ["#4CAF50", "#4CAF50", "#4CAF50", "#4CAF50"]

for i, (phase, metric, result, col) in enumerate(zip(phases, metrics, results, status_colors)):
    ax.add_patch(plt.Rectangle((0.05, 3-i-0.35), 0.35, 0.7,
                                facecolor="#E3F2FD", edgecolor="#1565C0", linewidth=1.5))
    ax.text(0.225, 3-i, phase, ha="center", va="center", fontsize=8, fontweight="bold")

    ax.add_patch(plt.Rectangle((0.45, 3-i-0.35), 0.5, 0.7,
                                facecolor="#E8F5E9", edgecolor="#2E7D32", linewidth=1.5))
    ax.text(0.7, 3-i+0.1, metric, ha="center", va="center", fontsize=7.5, fontweight="bold")
    ax.text(0.7, 3-i-0.15, result, ha="center", va="center", fontsize=6.5, color="#333")

    if i < 3:
        ax.annotate("", xy=(0.225, 3-i-0.4), xytext=(0.225, 3-i-0.6),
                     arrowprops=dict(arrowstyle="->", color="#1565C0", linewidth=1.5))

ax.set_xlim(0, 1)
ax.set_ylim(-0.8, 3.8)
ax.axis("off")
ax.set_title("C. Cross-Phase\nConvergence Chain", fontsize=12, fontweight="bold")

fig.suptitle("Literature Verification Summary — Phase 2 Filter Optimization",
             fontsize=15, fontweight="bold", y=1.03)
fig.tight_layout()
fig.savefig(FIG_DIR / "literature_convergence_summary.png", dpi=200, bbox_inches="tight")
print(f"Saved: {FIG_DIR / 'literature_convergence_summary.png'}")
plt.close()

print("\nAll 3 figures saved to:", FIG_DIR)
