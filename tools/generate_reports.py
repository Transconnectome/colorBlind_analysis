#!/usr/bin/env python3
"""
generate_reports.py

Loads saved ROI responses and forward-model results, generates QC plots
and writes an updated bilingual pipeline report (Korean + English).
"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import cfg
from bh_viz import make_qc_report


def load_roi_data(analysis_dir):
    roi_names = ['V1', 'V2', 'V3', 'hV4', 'WholeBrain']
    roi_data = {}
    for roi in roi_names:
        for fname in [f'{roi}_responses_perrun.npy', f'{roi}_responses.npy']:
            p = os.path.join(analysis_dir, fname)
            if os.path.exists(p):
                try:
                    roi_data[roi] = np.load(p)
                except Exception:
                    # try allow_pickle
                    roi_data[roi] = np.load(p, allow_pickle=True)
                break
    return roi_data


def load_model_results(analysis_dir):
    rois = ['V1','V2','V3','hV4','WholeBrain']
    results = {}
    for roi in rois:
        p = os.path.join(analysis_dir, f'{roi}_forward_model.npz')
        if os.path.exists(p):
            try:
                d = np.load(p, allow_pickle=True)
                # convert numpy arrays to python types where appropriate
                res = {}
                for k in d.files:
                    val = d[k]
                    try:
                        res[k] = val.tolist()
                    except Exception:
                        res[k] = val
                results[roi] = res
            except Exception as e:
                print('Failed loading', p, e)
    return results


def write_bilingual_report(analysis_dir, summary):
    outp = os.path.join(analysis_dir, 'pipeline_report_bilingual.md')
    lines = []
    lines.append('# Pipeline Report / 파이프라인 보고서')
    lines.append('')
    lines.append('## Summary (English)')
    lines.append('')
    lines.append('- This report summarizes the current QC and forward-model results.')
    lines.append('')
    lines.append('### Mean test accuracies by ROI')
    lines.append('')
    for roi, acc in summary.items():
        lines.append(f'- {roi}: {acc:.3f}')
    lines.append('')
    lines.append('## 요약 (한국어)')
    lines.append('')
    lines.append('- 이 보고서는 QC 및 forward-model(leave-one-run-out) 결과의 요약입니다.')
    lines.append('')
    lines.append('### ROI별 평균 테스트 정확도')
    lines.append('')
    for roi, acc in summary.items():
        lines.append(f'- {roi}: {acc:.3f}')

    with open(outp, 'w') as f:
        f.write('\n'.join(lines))

    print('Wrote bilingual report to', outp)


def main():
    analysis_dir = cfg.analysis_dir
    roi_data = load_roi_data(analysis_dir)
    model_results = load_model_results(analysis_dir)

    # prepare roi_data for plotting: convert per-run stacked arrays into (n_colors, n_voxels)
    roi_plot_data = {}
    for roi, data in roi_data.items():
        try:
            arr = np.array(data)
            if arr.ndim == 2:
                if arr.shape[0] == cfg.N_RUNS * cfg.N_COLORS:
                    # reshape to (n_runs, n_colors, n_voxels) then average across runs
                    n_runs = cfg.N_RUNS
                    n_colors = cfg.N_COLORS
                    n_vox = arr.shape[1]
                    arr3 = arr.reshape(n_runs, n_colors, n_vox)
                    arr_mean = np.mean(arr3, axis=0)  # (n_colors, n_voxels)
                    roi_plot_data[roi] = arr_mean
                elif arr.shape[0] == cfg.N_COLORS:
                    roi_plot_data[roi] = arr
                else:
                    # fallback: try to aggregate into N_COLORS groups
                    try:
                        arr2 = arr.reshape(-1, cfg.N_COLORS, arr.shape[1])
                        roi_plot_data[roi] = np.mean(arr2, axis=0)
                    except Exception:
                        roi_plot_data[roi] = arr
            else:
                roi_plot_data[roi] = arr
        except Exception:
            roi_plot_data[roi] = data

    # generate QC plots
    out_plot_dir = os.path.join(analysis_dir, 'qc_plots')
    make_qc_report(roi_plot_data, model_results, out_plot_dir)

    # compute summary (mean test_accuracy when available, else train_accuracy)
    summary = {}
    for roi, res in model_results.items():
        ta = res.get('test_accuracy')
        if ta and len(ta):
            try:
                summary[roi] = float(np.mean(ta))
            except Exception:
                summary[roi] = float(np.nan)
        else:
            tr = res.get('train_accuracy')
            if tr and len(tr):
                summary[roi] = float(np.mean(tr))
            else:
                summary[roi] = float('nan')

    write_bilingual_report(analysis_dir, summary)


if __name__ == '__main__':
    main()
