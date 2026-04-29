"""
Per-Participant JND Profile Visualization
(A) Top row: Individual JND profiles for each participant (6 subplots)
(B) Bottom row: Staircase convergence for participants with trial data
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
from pathlib import Path

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
PHASE_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE_DIR.parent.parent
DATA_DIR = REPO_ROOT / "data" / "behavior"
RESULTS_DIR = PHASE_DIR / "results"
FIG_DIR = PHASE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Load metrics ──
with open(RESULTS_DIR / "hc_group_metrics.json", 'r') as f:
    hc_metrics = json.load(f)

pairs_raw = ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-magenta', 'red-cyan']
pairs_short = ['R-O', 'O-Y', 'Y-G', 'G-B', 'Y-P', 'B-P', 'C-M', 'R-C']

hc_names = hc_metrics[pairs_raw[0]]['hc_names']
n_hc = hc_metrics[pairs_raw[0]]['n_hc']

# ── Participant data ──
hc_mean = [hc_metrics[p]['hc_mean'] for p in pairs_raw]
hc_std = [hc_metrics[p]['hc_std'] for p in pairs_raw]
cvd_vals = [hc_metrics[p]['cvd'] for p in pairs_raw]
jnd_dir = [hc_metrics[p]['direction_hc_group'] for p in pairs_raw]

# All participants (HC + CVD)
all_participants = list(hc_names) + ['CVD (sub-08)']
all_jnd = {}
for name in hc_names:
    all_jnd[name] = [hc_metrics[p][name] for p in pairs_raw]
all_jnd['CVD (sub-08)'] = cvd_vals

# All HCs have trial data under unified layout
trial_participants = list(hc_names) + ['sub-08']

# Colors
PAIR_COLORS = {
    'red-orange': '#E63946', 'orange-yellow': '#F4A261',
    'yellow-green': '#E9C46A', 'green-blue': '#2A9D8F',
    'yellow-purple': '#7B2D8E', 'blue-purple': '#264653',
    'cyan-magenta': '#00B4D8', 'red-cyan': '#D63384'
}

# ═══════════════════════════════════════════════════════════════════════
# Figure 1: Individual JND profiles
# ═══════════════════════════════════════════════════════════════════════
n_participants = len(all_participants)
n_cols = 3
n_rows = (n_participants + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
fig.suptitle(f'Per-Participant JND Profiles (HC N={n_hc}, CVD N=1)\n'
             f'Gray band = HC group mean ± SD',
             fontsize=14, fontweight='bold', y=1.01)

axes_flat = axes.flatten() if n_participants > 1 else [axes]

for idx, name in enumerate(all_participants):
    ax = axes_flat[idx]
    vals = all_jnd[name]
    x = np.arange(len(pairs_short))

    # HC group mean ± SD band
    hm = np.array(hc_mean)
    hs = np.array(hc_std)
    ax.fill_between(x, hm - hs, hm + hs, alpha=0.15, color='steelblue', label='HC Mean ± SD')
    ax.plot(x, hm, color='steelblue', linewidth=1, linestyle='--', alpha=0.5)

    # Participant bars
    is_cvd = 'CVD' in name
    bar_color = '#E74C3C' if is_cvd else '#4A90D9'
    bar_alpha = 0.9 if is_cvd else 0.7

    bar_colors_individual = []
    for i, p in enumerate(pairs_raw):
        if is_cvd:
            d = jnd_dir[i]
            if d == 'HYPO':
                bar_colors_individual.append('#E74C3C')
            elif d == 'HYPER':
                bar_colors_individual.append('#2ECC71')
            else:
                bar_colors_individual.append('#F39C12')
        else:
            bar_colors_individual.append('#4A90D9')

    bars = ax.bar(x, vals, color=bar_colors_individual, alpha=bar_alpha,
                  edgecolor='black', linewidth=0.5)

    # Direction labels for CVD
    if is_cvd:
        for i, d in enumerate(jnd_dir):
            y_pos = vals[i] + 0.01
            if d == 'HYPO':
                ax.text(i, y_pos, 'HYPO', ha='center', va='bottom', fontsize=6,
                        fontweight='bold', color='#E74C3C')
            elif d == 'HYPER':
                ax.text(i, y_pos, 'HYPER', ha='center', va='bottom', fontsize=6,
                        fontweight='bold', color='#2ECC71')
            else:
                ax.text(i, y_pos, 'BL', ha='center', va='bottom', fontsize=6,
                        fontweight='bold', color='#F39C12')

    ax.set_xticks(x)
    ax.set_xticklabels(pairs_short, fontsize=8)
    ax.set_ylabel('JND', fontsize=9)
    title_suffix = ' [CVD]' if is_cvd else ' [HC]'
    ax.set_title(f'{name}{title_suffix}', fontweight='bold', fontsize=11,
                 color='#E74C3C' if is_cvd else 'black')
    ax.set_ylim(0, max(max(vals) * 1.15, 0.5))
    ax.axhline(y=0, color='black', linewidth=0.5)

# Hide unused axes
for idx in range(n_participants, len(axes_flat)):
    axes_flat[idx].set_visible(False)

plt.tight_layout()
out1 = FIG_DIR / 'per_participant_jnd_profiles.png'
plt.savefig(out1, dpi=200, bbox_inches='tight')
print(f"Saved: {out1}")
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# Figure 2: Staircase convergence for participants with trial data
# ═══════════════════════════════════════════════════════════════════════
n_trial = len(trial_participants)
fig, axes = plt.subplots(n_trial, 1, figsize=(16, 4 * n_trial))
fig.suptitle('Staircase Convergence (Per-Participant, All Pairs)',
             fontsize=14, fontweight='bold', y=1.01)

if n_trial == 1:
    axes = [axes]

for p_idx, pname in enumerate(trial_participants):
    ax = axes[p_idx]
    trial_file = DATA_DIR / f"{pname}_jnd_ses1_no_filter_trials.csv"
    df = pd.read_csv(trial_file)

    # Plot each pair's staircase
    pair_names_in_data = df['pair_name'].unique()

    for pair in pairs_raw:
        if pair not in pair_names_in_data:
            continue

        pair_df = df[df['pair_name'] == pair].sort_values('trial')
        color = PAIR_COLORS.get(pair, 'gray')

        # Plot both staircases
        for sc_id in pair_df['staircase_id'].unique():
            sc_df = pair_df[pair_df['staircase_id'] == sc_id]
            linestyle = '-' if sc_id.endswith('sc0') else '--'
            ax.plot(sc_df['trial'].values, sc_df['level'].values,
                    color=color, linewidth=1.2, linestyle=linestyle, alpha=0.7)

            # Mark reversals
            reversals = sc_df[sc_df['reversal_count'] > sc_df['reversal_count'].shift(1).fillna(0)]
            if len(reversals) > 0:
                ax.scatter(reversals['trial'].values, reversals['level'].values,
                           color=color, s=15, zorder=3, alpha=0.5)

    # Legend
    legend_patches = [mpatches.Patch(color=PAIR_COLORS.get(p, 'gray'),
                                     label=ps)
                      for p, ps in zip(pairs_raw, pairs_short)]
    ax.legend(handles=legend_patches, fontsize=7, loc='upper right', ncol=4)

    ax.set_xlabel('Trial', fontsize=10)
    ax.set_ylabel('Stimulus Level', fontsize=10)
    ax.set_title(f'{pname}', fontweight='bold', fontsize=12)
    ax.set_ylim(-0.05, 1.0)
    ax.axhline(y=0, color='black', linewidth=0.5)

plt.tight_layout()
out2 = FIG_DIR / 'per_participant_staircase.png'
plt.savefig(out2, dpi=200, bbox_inches='tight')
print(f"Saved: {out2}")
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# Figure 3: All participants overlay
# ═══════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 6))

x = np.arange(len(pairs_short))
width = 0.12
hc_colors = ['#DDEAF6', '#C8DDF0', '#A3C8E8', '#7EB3DD', '#5A9ED2', '#3589C7', '#1F6FAF']

# HC individual bars
for j, name in enumerate(hc_names):
    vals = all_jnd[name]
    offset = (j - len(hc_names)/2) * width
    ax.bar(x + offset, vals, width, label=name, color=hc_colors[j % len(hc_colors)],
           edgecolor='gray', linewidth=0.3, alpha=0.8)

# CVD bars (offset to the right)
cvd_offset = (len(hc_names)/2 + 0.5) * width
ax.bar(x + cvd_offset, cvd_vals, width, label='CVD (sub-08)', color='#E74C3C',
       edgecolor='black', linewidth=0.8, alpha=0.9)

# Direction markers
for i, d in enumerate(jnd_dir):
    all_vals_i = [all_jnd[name][i] for name in hc_names] + [cvd_vals[i]]
    y_max = max(all_vals_i)
    if d == 'HYPO':
        marker_color, marker_label = '#E74C3C', 'HYPO'
    elif d == 'HYPER':
        marker_color, marker_label = '#2ECC71', 'HYPER'
    else:
        marker_color, marker_label = '#F39C12', 'BL'
    ax.text(x[i], y_max + 0.015, marker_label, ha='center', va='bottom',
            fontsize=7, fontweight='bold', color=marker_color)

ax.set_xticks(x)
ax.set_xticklabels(pairs_short, fontsize=10)
ax.set_ylabel('JND (interpolation step)', fontsize=11)
ax.set_title(f'All Participants JND Comparison (HC N={n_hc}, CVD N=1)',
             fontweight='bold', fontsize=13)
ax.legend(fontsize=8, loc='upper left', ncol=3)
ax.set_ylim(0, max(max(cvd_vals), max(max(all_jnd[n]) for n in hc_names)) * 1.15)
ax.axhline(y=0, color='black', linewidth=0.5)

plt.tight_layout()
out3 = FIG_DIR / 'all_participants_comparison.png'
plt.savefig(out3, dpi=200, bbox_inches='tight')
print(f"Saved: {out3}")
plt.close()
