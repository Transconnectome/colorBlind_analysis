"""Update jnd_summary.csv from hc_group_metrics.json (supports variable N HC)."""
import json
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results"

# Load HC group metrics
with open(RESULTS_DIR / "hc_group_metrics.json", 'r') as f:
    metrics = json.load(f)

# Create updated summary
data = []
for pair in metrics:
    m = metrics[pair]
    hc_names = m['hc_names']

    row = {
        'pair': pair,
        'hc_group_mean': m['hc_mean'],
        'hc_group_std': m['hc_std'],
        'hc_group_sem': m['hc_sem'],
        'n_hc': m['n_hc'],
        'cvd_jnd_mean': m['cvd'],
        'ratio_cvd_hc_group': m['ratio'],
        'direction_hc_group': m['direction_hc_group'],
    }

    # Add individual HC columns
    for name in hc_names:
        row[f'{name}_jnd'] = m[name]

    data.append(row)

df = pd.DataFrame(data)

# Save
output_file = RESULTS_DIR / "jnd_summary.csv"
df.to_csv(output_file, index=False, float_format='%.4f')
print(f"Saved: {output_file}")
print(f"Columns: {', '.join(df.columns)}")
print(f"Rows: {len(df)}")
