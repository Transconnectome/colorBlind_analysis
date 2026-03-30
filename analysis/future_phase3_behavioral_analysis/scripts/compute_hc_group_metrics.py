"""
Compute HC Group Metrics from all available data sources.
HC1, HC2: Original pilot (summary values only, no raw data files)
JYPark, JHKim, MJChoi: Raw data from data/ directory
CVD: sub-08 deutan (summary values only)

Saves: results/hc_group_metrics.json
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RESULTS_DIR = SCRIPT_DIR.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

PAIRS_ORDERED = [
    'red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
    'yellow-purple', 'blue-purple', 'cyan-magenta', 'red-cyan'
]

# ── Original pilot data (no raw files, summary values only) ──
HC1_JND = {
    'red-orange': 0.235, 'orange-yellow': 0.443, 'yellow-green': 0.103,
    'green-blue': 0.103, 'yellow-purple': 0.025, 'blue-purple': 0.165,
    'cyan-magenta': 0.048, 'red-cyan': 0.048
}
HC2_JND = {
    'red-orange': 0.018, 'orange-yellow': 0.064, 'yellow-green': 0.018,
    'green-blue': 0.02, 'yellow-purple': 0.015, 'blue-purple': 0.04,
    'cyan-magenta': 0.015, 'red-cyan': 0.015
}
CVD_JND = {
    'red-orange': 0.062, 'orange-yellow': 0.84, 'yellow-green': 0.278,
    'green-blue': 0.077, 'yellow-purple': 0.062, 'blue-purple': 0.12,
    'cyan-magenta': 0.04, 'red-cyan': 0.015
}


def load_participant(folder_path):
    """Load JND data from summary CSV, averaging both staircases per pair."""
    summary_file = folder_path / "jnd_ses1_no_filter_summary.csv"
    df = pd.read_csv(summary_file)
    return df.groupby('pair_name')['jnd_mean'].mean().to_dict()


# ── Load all participants from data/ ──
data_participants = {}
for folder in sorted(DATA_DIR.iterdir()):
    if folder.is_dir() and not folder.name.startswith('.'):
        data_participants[folder.name] = load_participant(folder)
        print(f"  Loaded: {folder.name}")

# ── Build HC dictionary (order: HC1, HC2, then data/ participants) ──
hc_data = {'HC1': HC1_JND, 'HC2': HC2_JND}
for name, jnd_dict in data_participants.items():
    hc_data[name] = jnd_dict

hc_names = list(hc_data.keys())
n_hc = len(hc_names)
print(f"\nTotal HC participants: {n_hc} ({', '.join(hc_names)})")

# ── Compute group metrics ──
hc_metrics = {}

for pair in PAIRS_ORDERED:
    hc_values = [hc_data[name].get(pair, np.nan) for name in hc_names]
    hc_values_clean = [v for v in hc_values if not np.isnan(v)]

    hc_mean = float(np.mean(hc_values_clean))
    hc_std = float(np.std(hc_values_clean, ddof=1))
    hc_sem = hc_std / np.sqrt(len(hc_values_clean))

    cvd_val = CVD_JND[pair]
    ratio = cvd_val / hc_mean if hc_mean > 0 else np.nan

    if ratio > 1.15:
        direction = 'HYPO'
    elif ratio < 0.85:
        direction = 'HYPER'
    else:
        direction = 'borderline'

    entry = {
        'hc_names': hc_names,
        'hc_mean': hc_mean,
        'hc_std': hc_std,
        'hc_sem': float(hc_sem),
        'n_hc': len(hc_values_clean),
        'cvd': float(cvd_val),
        'ratio': float(ratio),
        'direction_hc_group': direction,
    }

    # Add individual HC values
    for name in hc_names:
        entry[name] = float(hc_data[name].get(pair, np.nan))

    hc_metrics[pair] = entry

# ── Save JSON ──
output_json = RESULTS_DIR / "hc_group_metrics.json"
with open(output_json, 'w') as f:
    json.dump(hc_metrics, f, indent=2)
print(f"\nSaved: {output_json}")

# ── Print summary table ──
print("\n" + "=" * 120)
print(f"HC GROUP METRICS (N={n_hc})")
print("=" * 120)

header = f"{'Pair':<18}"
for name in hc_names:
    header += f" {name:<8}"
header += f" {'Mean':<7} {'SD':<7} {'CVD':<7} {'Ratio':<6} {'Dir(Group)'}"
print(header)
print("-" * 120)

for pair in PAIRS_ORDERED:
    m = hc_metrics[pair]
    row = f"{pair:<18}"
    for name in hc_names:
        row += f" {m[name]:<8.4f}"
    row += (f" {m['hc_mean']:<7.4f}"
            f" {m['hc_std']:<7.4f}"
            f" {m['cvd']:<7.4f}"
            f" {m['ratio']:<6.2f}"
            f" {m['direction_hc_group']}")
    print(row)

print("=" * 120)
