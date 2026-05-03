"""Extract signed confusion direction from LOCO fold results.

For each subject / ROI / held-out color:
  - mean_signed_bias : circular mean of (pred_hue - true_hue) across runs
                       >0 = clockwise (e.g. yellow→green), <0 = counter-clockwise (yellow→red)
  - abs_mae          : mean absolute error across runs (unsigned, from stored 'errors')
  - confusion_color  : which of the 8 canonical colors is closest to mean_pred_hue
  - confusion_delta  : color index difference (confusion_color - true_color), mod 8 with sign

Output:
  results/loco_confusion_direction/confusion_direction_all.csv   — full per-run detail
  results/loco_confusion_direction/confusion_bias_summary.csv    — one row per subj/ROI/color
  results/loco_confusion_direction/confusion_matrix_<subj>_<ROI>.csv  — 8×8 confusion count
"""

import json
import os
import numpy as np
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
LOCO_DIR = Path(
    '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
    'colorBlind_analysis/analysis/future_phase1_forward_model/results/validation'
)
OUT_DIR = Path(
    '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
    'colorBlind_analysis/analysis/future_phase2_filter_optimization/'
    'results/loco_confusion_direction'
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
COLOR_HUES  = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
ROIS        = ['V1', 'V2', 'V3', 'V4']
ENCODER     = 'ridge_gcv'

SUBJECTS = [
    ('01', 'HC'), ('02', 'HC'), ('03', 'HC'), ('04', 'HC'),
    ('05', 'HC'), ('06', 'HC'),
    ('08', 'CVD-deutan'), ('09', 'CVD-protan'), ('10', 'near-normal'),
]
# sub-07 excluded: V4 only 16 voxels, excluded from HC pool throughout


# ---------------------------------------------------------------------------
def circular_diff(pred: float, true: float) -> float:
    """Signed circular difference pred - true, in (-180, 180]."""
    return float(((pred - true + 180) % 360) - 180)


def nearest_color(hue: float) -> int:
    """Return index (0-7) of canonical color nearest to hue (circular)."""
    diffs = np.abs(np.array([circular_diff(hue, h) for h in COLOR_HUES]))
    return int(np.argmin(diffs))


# ---------------------------------------------------------------------------
all_rows   = []   # full detail
bias_rows  = []   # per subj/ROI/color summary

for subj_id, group in SUBJECTS:
    fname = LOCO_DIR / f'sub-{subj_id}_loco.json'
    if not fname.exists():
        print(f'MISSING: {fname.name}')
        continue

    data = json.load(open(fname))

    for roi in ROIS:
        if roi not in data:
            continue
        enc_data = data[roi].get(ENCODER, {})
        folds = enc_data.get('folds', [])
        if not folds:
            continue

        # 8×8 confusion count matrix (row=true, col=confused_with)
        conf_mat = np.zeros((8, 8), dtype=int)

        # collect per-color data
        color_signed_biases = {c: [] for c in range(8)}
        color_abs_errors    = {c: [] for c in range(8)}

        for fold in folds:
            c_true   = int(fold['test_color'])
            true_hue = float(fold['true_hue'])
            pred_hues = fold['pred_hues']
            abs_errs  = fold['errors']

            for pred_h, abs_e in zip(pred_hues, abs_errs):
                signed = circular_diff(pred_h, true_hue)
                color_signed_biases[c_true].append(signed)
                color_abs_errors[c_true].append(float(abs_e))

                # confusion target
                c_pred = nearest_color(float(pred_h))
                conf_mat[c_true, c_pred] += 1

                all_rows.append({
                    'subject':      f'sub-{subj_id}',
                    'group':        group,
                    'ROI':          roi,
                    'true_color':   c_true,
                    'true_name':    COLOR_NAMES[c_true],
                    'true_hue':     true_hue,
                    'pred_hue':     round(float(pred_h), 1),
                    'signed_error': round(signed, 1),
                    'abs_error':    round(float(abs_e), 1),
                    'confused_with_idx':  c_pred,
                    'confused_with_name': COLOR_NAMES[c_pred],
                })

        # save confusion matrix
        cm_path = OUT_DIR / f'confusion_matrix_sub-{subj_id}_{roi}.csv'
        with open(cm_path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['true\\pred'] + COLOR_NAMES)
            for i, row in enumerate(conf_mat):
                w.writerow([COLOR_NAMES[i]] + list(row))

        # per-color summary
        for c in range(8):
            biases = color_signed_biases[c]
            errs   = color_abs_errors[c]
            if not biases:
                continue

            mean_bias = float(np.mean(biases))
            # mean pred hue = true_hue + mean_bias (circular)
            mean_pred = (COLOR_HUES[c] + mean_bias) % 360
            c_confused = nearest_color(mean_pred)

            # signed delta in color-index space (-4..+4)
            delta = c_confused - c
            if delta > 4:
                delta -= 8
            elif delta < -4:
                delta += 8

            bias_rows.append({
                'subject':           f'sub-{subj_id}',
                'group':             group,
                'ROI':               roi,
                'true_color':        c,
                'true_name':         COLOR_NAMES[c],
                'true_hue':          COLOR_HUES[c],
                'mean_signed_bias':  round(mean_bias, 2),
                'std_signed_bias':   round(float(np.std(biases)), 2),
                'abs_mae':           round(float(np.mean(errs)), 2),
                'mean_pred_hue':     round(mean_pred, 1),
                'confused_with_idx': c_confused,
                'confused_with_name': COLOR_NAMES[c_confused],
                'color_delta':       delta,   # positive=clockwise, negative=ccw
                'n_runs':            len(biases),
            })

    print(f'sub-{subj_id} ({group}): done')


# ---------------------------------------------------------------------------
# Write CSVs
def write_csv(path, rows, fieldnames):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

detail_fields = [
    'subject', 'group', 'ROI', 'true_color', 'true_name', 'true_hue',
    'pred_hue', 'signed_error', 'abs_error',
    'confused_with_idx', 'confused_with_name',
]
write_csv(OUT_DIR / 'confusion_direction_all.csv', all_rows, detail_fields)

summary_fields = [
    'subject', 'group', 'ROI', 'true_color', 'true_name', 'true_hue',
    'mean_signed_bias', 'std_signed_bias', 'abs_mae',
    'mean_pred_hue', 'confused_with_idx', 'confused_with_name',
    'color_delta', 'n_runs',
]
write_csv(OUT_DIR / 'confusion_bias_summary.csv', bias_rows, summary_fields)

print(f'\nSaved to {OUT_DIR}')
print(f'  confusion_direction_all.csv     : {len(all_rows)} rows')
print(f'  confusion_bias_summary.csv      : {len(bias_rows)} rows')
print(f'  confusion_matrix_*.csv          : per subj×ROI')
