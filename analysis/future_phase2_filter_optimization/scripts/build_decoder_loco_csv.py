#!/usr/bin/env python3
"""Build decoder-LOCO long-format CSV from phase3_decoder_comparing results.

Source:  analysis/phase3_decoder_comparing/results/loco/raw/sub-*_loco.json
Output:  analysis/future_phase2_filter_optimization/results/diagnostics/decoder_loco/decoder_loco_long.csv
         + decoder_loco_confusion_{model}.csv (8x8 confusion matrices, counts)
         + decoder_loco_summary.csv (per subject x roi x model: accuracy, adj-acc, mae)

Purpose: provide per-(subject, ROI, model, test_color, run) decoder predictions
in a form directly usable for confusion-based filter training or HC-specificity
diagnostics (decoder-LOCO does NOT require LOO across subjects — each decoder
is already leave-one-color-out within-subject).

Columns (long format):
  subject, group, roi, model, test_color_label, test_hue,
  run, pred_label, pred_hue, signed_error, abs_error,
  is_correct, is_adjacent

signed_error: wrapped hue_pred - hue_true ∈ (-180, +180]
abs_error:    |signed_error|
is_correct:   pred_label == test_color_label
is_adjacent:  abs_error <= 45 deg (B&H 2009 convention)
"""

import json
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / 'analysis' / 'phase3_decoder_comparing' / 'results' / 'loco' / 'raw'
OUT_DIR = ROOT / 'analysis' / 'future_phase2_filter_optimization' / 'results' / 'diagnostics/decoder_loco'
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUBJECTS = [f"{i:02d}" for i in range(1, 11)]
GROUP = {f"{i:02d}": ('HC' if i <= 7 else 'CVD') for i in range(1, 11)}
# sub-10 is near-normal deutan per MEMORY note
CVD_SUBTYPE = {'08': 'deutan', '09': 'protan', '10': 'deutan_mild'}


def signed_hue_diff(pred, true):
    """Wrapped circular difference pred - true ∈ (-180, +180]."""
    d = (pred - true + 180.0) % 360.0 - 180.0
    # Convention: -180 maps to +180 for right-open wrap
    if d <= -180.0:
        d += 360.0
    return d


def main():
    long_rows = []
    summary_rows = []
    # confusion[model][true][pred] = count over all subjects × rois × runs
    confusion_all = {}
    # confusion per group (HC vs CVD) for quick HC-specificity peek
    confusion_by_group = {}

    for sub in SUBJECTS:
        fp = SRC_DIR / f'sub-{sub}_loco.json'
        if not fp.exists():
            print(f"[skip] {fp} missing")
            continue
        data = json.loads(fp.read_text())
        group = GROUP[sub]
        subtype = CVD_SUBTYPE.get(sub, 'HC')
        results = data['results']

        for roi, roi_res in results.items():
            for model, m_res in roi_res.items():
                folds = m_res.get('fold_results', [])
                n_trials = 0
                n_correct = 0
                n_adjacent = 0
                abs_err_sum = 0.0

                for fold in folds:
                    true_label = fold['test_color']
                    true_hue = float(fold['test_hue'])
                    pred_hues = fold.get('pred_hues', [])
                    pred_labels = fold.get('pred_labels', [])
                    errs = fold.get('errors_per_run', [])

                    for run_idx, (ph, pl) in enumerate(zip(pred_hues, pred_labels)):
                        ph = float(ph)
                        sgn = signed_hue_diff(ph, true_hue)
                        abs_e = abs(sgn)
                        is_corr = int(pl) == int(true_label)
                        is_adj = abs_e <= 45.0

                        long_rows.append({
                            'subject': sub,
                            'group': group,
                            'cvd_subtype': subtype,
                            'roi': roi,
                            'model': model,
                            'test_color_label': int(true_label),
                            'test_hue': true_hue,
                            'run': run_idx,
                            'pred_label': int(pl),
                            'pred_hue': ph,
                            'signed_error': sgn,
                            'abs_error': abs_e,
                            'is_correct': int(is_corr),
                            'is_adjacent': int(is_adj),
                        })

                        n_trials += 1
                        n_correct += int(is_corr)
                        n_adjacent += int(is_adj)
                        abs_err_sum += abs_e

                        # Per-model confusion (class 0..7)
                        conf = confusion_all.setdefault(model, [[0]*8 for _ in range(8)])
                        conf[int(true_label)][int(pl)] += 1
                        gconf = confusion_by_group.setdefault((model, group), [[0]*8 for _ in range(8)])
                        gconf[int(true_label)][int(pl)] += 1

                if n_trials > 0:
                    summary_rows.append({
                        'subject': sub,
                        'group': group,
                        'cvd_subtype': subtype,
                        'roi': roi,
                        'model': model,
                        'n_trials': n_trials,
                        'accuracy_exact': n_correct / n_trials,
                        'accuracy_adjacent': n_adjacent / n_trials,
                        'mae_deg': abs_err_sum / n_trials,
                        # Chance levels:
                        'chance_exact': 1/8,
                        'chance_adjacent': 3/8,  # ±45° = 3 of 8 bins (self + 2 neighbours)
                    })

    # Write long CSV
    long_fp = OUT_DIR / 'decoder_loco_long.csv'
    with long_fp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=long_rows[0].keys())
        w.writeheader()
        w.writerows(long_rows)
    print(f"[ok] long-format trials: {len(long_rows)} rows -> {long_fp}")

    # Write summary CSV
    summ_fp = OUT_DIR / 'decoder_loco_summary.csv'
    with summ_fp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        w.writeheader()
        w.writerows(summary_rows)
    print(f"[ok] summary:           {len(summary_rows)} rows -> {summ_fp}")

    # Write confusion matrices (one file per model, pooled across subjects/ROIs/runs)
    for model, conf in confusion_all.items():
        fp = OUT_DIR / f'decoder_loco_confusion_{model}.csv'
        with fp.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['true_label'] + [f'pred_{i}' for i in range(8)])
            for t in range(8):
                w.writerow([t] + conf[t])
        print(f"[ok] confusion ({model}): {fp}")

    # Per-group confusion for HC vs CVD quick comparison (ForwardEncoding only is most informative)
    for (model, group), conf in confusion_by_group.items():
        fp = OUT_DIR / f'decoder_loco_confusion_{model}_{group}.csv'
        with fp.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['true_label'] + [f'pred_{i}' for i in range(8)])
            for t in range(8):
                w.writerow([t] + conf[t])


if __name__ == '__main__':
    main()
