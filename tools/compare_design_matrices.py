#!/usr/bin/env python3
"""
Compare design matrices from the notebook (existing CSVs) with recomputed design matrices
built from events files and BOLD headers using Nilearn's design matrix builder.

Outputs:
 - Copies of found notebook design CSVs into <outdir>/notebook_designs/
 - Recomputed design CSVs into <outdir>/recomputed_designs/
 - A markdown summary at <outdir>/design_matrix_comparison.md listing column diffs per run

Usage:
  python tools/compare_design_matrices.py --sub sub-01 --outdir derivatives/sub-01/diagnostics/compare_design

This script attempts to mirror the GLM settings used by `tools/compute_run_betas.py` by default
but accepts overrides for hrf_model, drift_model and high_pass.
"""

import os
import glob
import shutil
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import nibabel as nib
from nilearn.glm.first_level import make_first_level_design_matrix


def find_notebook_designs(root='.'):
    patterns = [
        os.path.join(root, 'derivatives', '**', '*design*.csv'),
        os.path.join(root, 'hrf_test_outputs', '*.csv'),
        os.path.join(root, 'derivatives', '**', '*design_matrix*.csv'),
    ]
    files = []
    for p in patterns:
        files += glob.glob(p, recursive=True)
    files = sorted(set(files))
    return files


def find_bold_runs(sub, fmri_dir):
    pattern = os.path.join(fmri_dir, f"{sub}_task-rsvp_*_desc-preproc_bold.nii*")
    return sorted(glob.glob(pattern))


def run(args):
    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    nb_dir = os.path.join(args.outdir, 'notebook_designs')
    rc_dir = os.path.join(args.outdir, 'recomputed_designs')
    Path(nb_dir).mkdir(parents=True, exist_ok=True)
    Path(rc_dir).mkdir(parents=True, exist_ok=True)

    # gather notebook CSVs
    nb_files = find_notebook_designs('.')
    # filter to subject
    nb_files = [f for f in nb_files if args.sub in os.path.basename(f) or f.split(os.sep)[-1].startswith(args.sub)]

    # copy notebook files into outdir for easy inspection
    nb_map = {}
    for f in nb_files:
        bn = os.path.basename(f)
        dst = os.path.join(nb_dir, bn)
        try:
            shutil.copy2(f, dst)
            nb_map[bn] = dst
        except Exception:
            # ignore copy failures
            nb_map[bn] = f

    # find bold runs to recompute designs
    bolds = find_bold_runs(args.sub, args.fmri_dir)
    recomputed_map = {}

    for bold in bolds:
        bname = os.path.basename(bold)
        run_tag = None
        for part in bname.split('_'):
            if part.startswith('run-'):
                run_tag = part
                break
        if run_tag is None:
            run_tag = 'run-?'

        # load events
        # events path heuristic
        sub = bname.split('_')[0]
        ev_guess = os.path.join(args.bids_dir, sub, 'func', f"{sub}_task-rsvp_{run_tag}_events.tsv")
        if not os.path.exists(ev_guess):
            ev_guess = os.path.join(args.bids_dir, sub, 'func', f"{sub}_task-rsvp_events.tsv")
        if not os.path.exists(ev_guess):
            print(f"  events not found for {bold} (tried {ev_guess}) - skipping recompute")
            continue

        ev = pd.read_csv(ev_guess, sep='\t')
        # only keep onset/duration/trial_type columns if present
        if not set(['onset','duration','trial_type']).issubset(ev.columns):
            print(f"  events file {ev_guess} missing required columns - skipping")
            continue

        img = nib.load(bold)
        zooms = img.header.get_zooms()
        if len(zooms) >= 4:
            TR = float(zooms[3])
        else:
            TR = args.tr
        n_scans = img.shape[-1]
        frame_times = np.arange(n_scans) * TR

        design = make_first_level_design_matrix(frame_times, ev, hrf_model=args.hrf_model,
                                                drift_model=args.drift_model, high_pass=args.high_pass)

        out_csv = os.path.join(rc_dir, f"{sub}_{run_tag}_design_recomputed_HRF-{args.hrf_model}.csv")
        design.to_csv(out_csv, index=False)
        recomputed_map[f"{sub}_{run_tag}"] = out_csv
        print(f"  recomputed design for {run_tag} -> {out_csv} (n_cols={design.shape[1]})")

    # Now compare columns between any notebook CSV that mentions a run_tag and the recomputed one
    summary_lines = []
    summary_lines.append(f"# Design matrix comparison for {args.sub}\n")
    summary_lines.append(f"**GLM settings used for recomputation**: hrf_model={args.hrf_model}, drift_model={args.drift_model}, high_pass={args.high_pass}, TR fallback={args.tr}\n")

    summary_lines.append('## Found notebook design CSVs\n')
    for bn, path in nb_map.items():
        summary_lines.append(f"- {bn} => {path}\n")

    summary_lines.append('\n## Recomputed design CSVs\n')
    for k, v in recomputed_map.items():
        summary_lines.append(f"- {k} => {v}\n")

    summary_lines.append('\n## Per-run column diffs\n')
    for key, rc_path in recomputed_map.items():
        # try to find a notebook file for same run
        possible = [bn for bn in nb_map.keys() if key in bn]
        nb_path = nb_map[possible[0]] if possible else None
        rc_df = pd.read_csv(rc_path)
        rc_cols = list(rc_df.columns)
        nb_cols = []
        if nb_path is not None:
            try:
                nb_df = pd.read_csv(nb_path)
                nb_cols = list(nb_df.columns)
            except Exception:
                nb_cols = []

        only_nb = [c for c in nb_cols if c not in rc_cols]
        only_rc = [c for c in rc_cols if c not in nb_cols]

        summary_lines.append(f"### {key}\n")
        summary_lines.append(f"- notebook file: {nb_path if nb_path is not None else 'NOT FOUND'}\n")
        summary_lines.append(f"- recomputed file: {rc_path}\n")
        summary_lines.append(f"- notebook n_cols: {len(nb_cols)} | recomputed n_cols: {len(rc_cols)}\n")
        summary_lines.append(f"- columns only in notebook ({len(only_nb)}): {only_nb}\n")
        summary_lines.append(f"- columns only in recomputed ({len(only_rc)}): {only_rc}\n")
        summary_lines.append('\n')

    # Add notes about mask handling from scripts
    summary_lines.append('## Masking / resampling notes (extracted from scripts)\n')
    summary_lines.append('- `tools/compute_run_betas.py`: uses `NiftiMasker(mask_img=args.mask_path, standardize=False).fit()` to prepare masker (does not attempt forced copy_header resampling).\n')
    summary_lines.append('- `tools/strict_baseline.py`: attempts to resample provided mask to first beta image grid using `resample_to_img(..., copy_header=True)` and falls back to copying header False or resampling betas→mask if resample fails.\n')

    md_out = os.path.join(args.outdir, 'design_matrix_comparison.md')
    with open(md_out, 'w') as fh:
        fh.write('\n'.join(summary_lines))

    print('\nWrote summary to', md_out)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--sub', default='sub-01')
    p.add_argument('--fmri_dir', default='output/pilot/sub-01/func')
    p.add_argument('--bids_dir', default='pilot')
    p.add_argument('--outdir', default='derivatives/sub-01/diagnostics/compare_design')
    p.add_argument('--hrf_model', default='glover')
    p.add_argument('--drift_model', default='cosine')
    p.add_argument('--high_pass', type=float, default=0.01)
    p.add_argument('--tr', type=float, default=1.5, help='fallback TR if not present in header')
    args = p.parse_args()
    run(args)
