"""
Behavioral Pilot Data Visualization — Phase 3
Generates 4-panel figure:
  (A) JND comparison: individual HC dots + group mean + CVD
  (B) RSVP per-color accuracy
  (C) SRM z vs JND ratio concordance
  (D) LOCO vulnerability vs JND direction alignment
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
from pathlib import Path

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
FIG_DIR = SCRIPT_DIR.parent / "figures"
RESULTS_DIR = SCRIPT_DIR.parent / "results"
FIG_DIR.mkdir(exist_ok=True)

# ── Load HC group metrics JSON ──
with open(RESULTS_DIR / "hc_group_metrics.json", 'r') as f:
    hc_metrics = json.load(f)

# ── Color palette ──
COLOR_MAP = {
    'red': '#E63946', 'orange': '#F4A261', 'yellow': '#E9C46A',
    'green': '#2A9D8F', 'cyan': '#00B4D8', 'blue': '#264653',
    'purple': '#7B2D8E', 'magenta': '#D63384'
}

# ── Data ──
pairs_short = ['R-O', 'O-Y', 'Y-G', 'G-B', 'Y-P', 'B-P', 'C-M', 'R-C']
pairs_raw = ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-magenta', 'red-cyan']

# Extract HC names and individual values
first_pair = hc_metrics[pairs_raw[0]]
hc_names = first_pair['hc_names']
n_hc = first_pair['n_hc']

hc_individual = {name: [hc_metrics[p][name] for p in pairs_raw] for name in hc_names}
hc_mean_jnd = [hc_metrics[p]['hc_mean'] for p in pairs_raw]
hc_sem_jnd = [hc_metrics[p]['hc_sem'] for p in pairs_raw]
cvd_jnd = [hc_metrics[p]['cvd'] for p in pairs_raw]
jnd_dir = [hc_metrics[p]['direction_hc_group'] for p in pairs_raw]

# SRM z (best ROI, sub-08)
srm_z = [1.66, 3.29, 4.14, -0.89, 13.87, 6.15, np.nan, np.nan]

# RSVP per-color
colors_order = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
cvd_acc = [1.0, 0.875, 0.625, 0.75, 1.0, 1.0, 0.5, 0.75]
hc2_acc = [1.0, 1.0, 1.0, 0.875, 1.0, 1.0, 0.875, 1.0]
loco_vuln = [False, True, True, False, True, False, True, False]

# ── Figure ──
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.suptitle(f'Phase 3: Behavioral Pilot — sub-08 (Deutan CVD) vs HC (N={n_hc})\n[PRELIMINARY]',
             fontsize=13, fontweight='bold', y=0.98)

# ── Panel A: JND Comparison (dots + mean + CVD) ──
ax = axes[0, 0]
x = np.arange(len(pairs_short))

# Individual HC dots (jittered)
hc_dot_colors = ['#A3C8E8', '#6AA8D2', '#4A90D9', '#3577BF', '#2060A0']
for j, name in enumerate(hc_names):
    jitter = (j - len(hc_names)/2 + 0.5) * 0.06
    vals = hc_individual[name]
    ax.scatter(x + jitter, vals, s=30, color=hc_dot_colors[j % len(hc_dot_colors)],
               edgecolors='gray', linewidths=0.3, zorder=3, label=name, alpha=0.8)

# HC group mean bar
w = 0.3
bars_hc = ax.bar(x - w/2, hc_mean_jnd, w, label=f'HC Mean (N={n_hc})', color='#4A90D9',
                 alpha=0.4, edgecolor='black', linewidth=0.8)
ax.errorbar(x - w/2, hc_mean_jnd, yerr=hc_sem_jnd, fmt='none', ecolor='black',
            elinewidth=1.5, capsize=3, capthick=1.5)

# CVD bar
bars_cvd = ax.bar(x + w/2, cvd_jnd, w, label='CVD (sub-08)', color='#E74C3C',
                  alpha=0.9, edgecolor='black', linewidth=1.0)

# Mark HYPO/HYPER/borderline
for i, d in enumerate(jnd_dir):
    all_vals = list(hc_individual[name][i] for name in hc_names) + [cvd_jnd[i]]
    y_max = max(all_vals)
    if d == 'HYPO':
        color, label = '#E74C3C', 'HYPO'
    elif d == 'HYPER':
        color, label = '#2ECC71', 'HYPER'
    else:
        color, label = '#F39C12', 'borderline'
    ax.text(x[i], y_max + 0.02, label, ha='center', va='bottom', fontsize=6.5,
            fontweight='bold', color=color)

ax.set_ylabel('JND (interpolation step)')
ax.set_xticks(x)
ax.set_xticklabels(pairs_short, fontsize=8)
ax.legend(fontsize=6, loc='upper left', ncol=3, columnspacing=0.8)
ax.set_title(f'(A) JND: Individual HC (N={n_hc}) + Mean (±SEM) vs CVD', fontweight='bold', fontsize=9.5)
ax.set_ylim(0, 1.0)
ax.axhline(y=0, color='black', linewidth=0.5)

# ── Panel B: RSVP Per-Color Accuracy ──
ax = axes[0, 1]
bar_colors = [COLOR_MAP[c] for c in colors_order]
x_rsvp = np.arange(len(colors_order))
w_rsvp = 0.35
bars_cvd_rsvp = ax.bar(x_rsvp - w_rsvp/2, cvd_acc, w_rsvp, label='CVD (sub-08)',
                        color=[c + 'CC' for c in bar_colors], edgecolor='black', linewidth=0.5)
bars_hc2_rsvp = ax.bar(x_rsvp + w_rsvp/2, hc2_acc, w_rsvp, label='HC2',
                        color=[c + '66' for c in bar_colors], edgecolor='black', linewidth=0.5)

for i, (v, acc) in enumerate(zip(loco_vuln, cvd_acc)):
    if v:
        ax.bar(x_rsvp[i] - w_rsvp/2, acc, w_rsvp, color='none', edgecolor='red',
               linewidth=2.5, linestyle='--')
        ax.text(x_rsvp[i] - w_rsvp/2, acc + 0.02, 'LOCO\nvuln', ha='center', va='bottom',
                fontsize=6, color='red', fontweight='bold')

ax.axhline(y=1.0, color='#4A90D9', linewidth=1.5, linestyle='--', label='HC1 (100%)', alpha=0.7)
ax.set_ylabel('Accuracy')
ax.set_title('(B) RSVP 8AFC: Per-Color Accuracy', fontweight='bold', fontsize=10)
ax.set_ylim(0, 1.25)
ax.legend(fontsize=7, loc='upper right')
ax.set_xticks(x_rsvp)
ax.set_xticklabels(colors_order, fontsize=8)

# ── Panel C: SRM z vs JND Ratio ──
ax = axes[1, 0]
jnd_ratio = [c / h if h > 0 else 0 for c, h in zip(cvd_jnd, hc_mean_jnd)]

srm_concordant = []
for i, z in enumerate(srm_z):
    if np.isnan(z) or jnd_dir[i] == 'borderline':
        srm_concordant.append(None)
    elif (z > 0 and jnd_dir[i] == 'HYPER') or (z < 0 and jnd_dir[i] == 'HYPO'):
        srm_concordant.append(True)
    else:
        srm_concordant.append(False)

n_concordant = sum(1 for c in srm_concordant if c is True)
n_discordant = sum(1 for c in srm_concordant if c is False)
n_evaluable = n_concordant + n_discordant

for i in range(len(pairs_short)):
    if np.isnan(srm_z[i]) or srm_concordant[i] is None:
        continue
    color = '#2ECC71' if srm_concordant[i] else '#E74C3C'
    marker = 'o' if srm_concordant[i] else 'x'
    ax.scatter(srm_z[i], jnd_ratio[i], c=color, s=80, marker=marker, zorder=5,
               edgecolors='black', linewidths=0.5)
    ax.annotate(pairs_short[i], (srm_z[i], jnd_ratio[i]),
                textcoords="offset points", xytext=(8, 5), fontsize=7)

ax.axhline(y=1.0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)
ax.axvline(x=0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)

ax.text(10, 0.3, 'CONCORDANT\n(over-sep + HYPER)', fontsize=7, color='#2ECC71',
        ha='center', style='italic', alpha=0.7)
ax.text(10, 3.5, 'DISCORDANT\n(over-sep + HYPO)', fontsize=7, color='#E74C3C',
        ha='center', style='italic', alpha=0.7)
ax.text(-0.5, 0.3, 'CONCORDANT\n(compressed + HYPO)', fontsize=7, color='#2ECC71',
        ha='center', style='italic', alpha=0.7)

concordant_patch = mpatches.Patch(color='#2ECC71', label=f'Concordant ({n_concordant}/{n_evaluable})')
discordant_patch = mpatches.Patch(color='#E74C3C', label=f'Discordant ({n_discordant}/{n_evaluable})')
ax.legend(handles=[concordant_patch, discordant_patch], fontsize=7, loc='upper left')

ax.set_xlabel('SRM z-score (sub-08, best ROI)')
ax.set_ylabel(f'JND Ratio (CVD / HC Group Mean, N={n_hc})')
ax.set_title(f'(C) SRM z vs JND Ratio (HC Group, N={n_hc})', fontweight='bold', fontsize=10)

# ── Panel D: LOCO Vulnerability → JND Alignment ──
ax = axes[1, 1]

loco_data = {
    'orange': {'p_V1': 0.0018, 'p_V2': 0.023, 'hypo_pairs': ['O-Y']},
    'yellow': {'p_V1': 0.0059, 'p_V2': 0.0077, 'hypo_pairs': ['O-Y', 'Y-G', 'Y-P']},
    'purple': {'p_V1': 0.020, 'p_V2': None, 'hypo_pairs': ['Y-P']},
    'cyan': {'p_V2': 0.0053, 'p_V1': None, 'hypo_pairs': []},
}

y_pos = np.arange(len(loco_data))
colors_loco = list(loco_data.keys())
p_vals = []
for c in colors_loco:
    ps = [v for v in [loco_data[c].get('p_V1'), loco_data[c].get('p_V2')] if v is not None]
    p_vals.append(min(ps))

neg_log_p = [-np.log10(p) for p in p_vals]
bar_colors_loco = [COLOR_MAP[c] for c in colors_loco]
bars = ax.barh(y_pos, neg_log_p, color=bar_colors_loco, edgecolor='black', linewidth=0.5, alpha=0.85)

# Update HYPO pair labels based on new group direction
for i, c in enumerate(colors_loco):
    hypo = loco_data[c]['hypo_pairs']
    # Check if pairs are still HYPO with updated N
    valid_hypo = []
    pair_map = {'O-Y': 'orange-yellow', 'Y-G': 'yellow-green', 'Y-P': 'yellow-purple',
                'B-P': 'blue-purple', 'C-M': 'cyan-magenta', 'R-C': 'red-cyan'}
    for hp in hypo:
        full_pair = pair_map.get(hp, '')
        if full_pair and hc_metrics.get(full_pair, {}).get('direction_hc_group') == 'HYPO':
            valid_hypo.append(hp)

    if valid_hypo:
        label = ', '.join(valid_hypo)
        ax.text(neg_log_p[i] + 0.05, i, f' JND HYPO: {label}', va='center', fontsize=8,
                fontweight='bold', color='#E74C3C')
    else:
        ax.text(neg_log_p[i] + 0.05, i, '  (no HYPO pair)', va='center', fontsize=8,
                style='italic', color='gray')

# Count LOCO-vulnerable colors that have at least one HYPO pair
n_loco_with_hypo = sum(1 for c in colors_loco
                       if any(hc_metrics.get({'O-Y': 'orange-yellow', 'Y-G': 'yellow-green',
                                              'Y-P': 'yellow-purple', 'B-P': 'blue-purple'}.get(hp, ''),
                                             {}).get('direction_hc_group') == 'HYPO'
                              for hp in loco_data[c]['hypo_pairs'])
                       if loco_data[c]['hypo_pairs'])
n_loco_with_pairs = sum(1 for c in colors_loco if loco_data[c]['hypo_pairs'])

ax.axvline(x=-np.log10(0.05), color='red', linewidth=1, linestyle='--', alpha=0.7, label='p=0.05')
ax.set_yticks(y_pos)
ax.set_yticklabels([c.capitalize() for c in colors_loco], fontsize=9)
ax.set_xlabel('-log10(p) Crawford-Howell')
ax.set_title(f'(D) LOCO Vulnerability -> JND HYPO ({n_loco_with_hypo}/{n_loco_with_pairs})',
             fontweight='bold', fontsize=10)
ax.legend(fontsize=8)
ax.set_xlim(0, 4.0)

plt.tight_layout(rect=[0, 0, 1, 0.95])
out_path = FIG_DIR / 'behavioral_pilot_summary.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"Saved: {out_path}")
plt.close()
