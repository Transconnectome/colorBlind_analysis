#!/usr/bin/env python3
"""
Run a compact, scriptified version of `nilearn_test.ipynb` pipeline to compute LOAO diag-linear accuracy.

This script follows the notebook steps: compute per-run betas (via FirstLevelModel per run),
masking, select top-k voxels, and run leave-one-run-out classification with the diag-linear classifier.

It is intended for quick reproducible checks of accuracy using the notebook logic.

Usage:
  python3 tools/run_nilearn_test_from_nb.py

"""

import os
import json
import glob
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from nilearn.glm.first_level import FirstLevelModel, compute_regressor
from nilearn.maskers import NiftiMasker
from nilearn.image import load_img


# --------- Config (copied/trimmed from notebook) ---------
SUB = "sub-01"
TASK = "rsvp"
FMRIPREP_DIR = "output/pilot"
BIDS_DIR = "pilot"
OUTDIR = "./hrf_test_outputs_nbscript"
os.makedirs(OUTDIR, exist_ok=True)

HRF_MODEL = "glover"
DRIFT_MODEL = "cosine"
HIGH_PASS = 0.01
NOISE_MODEL = "ar1"
INTEREST_CONDS = [f"color_{i}" for i in range(1, 9)] + ["blank"]

# fmri runs (same as notebook)
fmri_imgs = [
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-2_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-3_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-4_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-5_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
    "output/pilot/sub-01/func/sub-01_task-rsvp_run-6_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz",
]

ROI_MASK = "output/pilot/sub-01/anat/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"


def get_run_tag_from_basename(bname: str):
    parts = bname.split("_")
    for p in parts:
        if p.startswith("run-"):
            return p
    return None


def events_path_for_bold(bold_path: str):
    bname = os.path.basename(bold_path)
    run_tag = get_run_tag_from_basename(bname)
    if run_tag is None:
        return f"{BIDS_DIR}/{SUB}/func/{SUB}_task-{TASK}_events.tsv"
    else:
        return f"{BIDS_DIR}/{SUB}/func/{SUB}_task-{TASK}_{run_tag}_events.tsv"


def frame_times_from_img(img_nii):
    n_scans = img_nii.shape[-1]
    TR = 1.5
    frame_times = np.arange(n_scans) * TR
    return frame_times, TR, n_scans


def fit_one_run_and_get_betas(bold_path, mask_img=ROI_MASK):
    ev_path = events_path_for_bold(bold_path)
    if not os.path.exists(ev_path):
        print(f"events not found for {bold_path}: {ev_path}")
        return None
    ev = pd.read_csv(ev_path, sep='\t')
    all_conds = sorted(ev['trial_type'].unique().tolist())
    conds = [c for c in INTEREST_CONDS if c in all_conds] or all_conds
    missing = [c for c in INTEREST_CONDS if c not in conds]
    if missing:
        print(f"[WARN] {bold_path} missing conditions {missing} -> skip run")
        return None

    ev = ev[ev['trial_type'].isin(conds)].copy()

    img = nib.load(bold_path)
    frame_times, TR, n_scans = frame_times_from_img(img)

    glm = FirstLevelModel(t_r=TR, hrf_model=HRF_MODEL, drift_model=DRIFT_MODEL,
                          high_pass=HIGH_PASS, noise_model=NOISE_MODEL, minimize_memory=False)
    glm = glm.fit(bold_path, events=ev)

    design = glm.design_matrices_[0]
    color_regressors = [c for c in design.columns if any(c.startswith(cc) for cc in conds)]
    base_regs = []
    for cc in conds:
        base = [r for r in color_regressors if r == cc or (r.startswith(cc) and ('deriv' not in r and 'post' not in r))]
        base_regs.append(base[0] if base else cc)

    masker = NiftiMasker(mask_img=mask_img, standardize=False).fit()
    X_list = []
    for cc in base_regs:
        try:
            beta_img = glm.compute_contrast(cc, output_type='effect_size')
        except Exception as e:
            print('contrast failed for', cc, e)
            return None
        X_list.append(masker.transform(beta_img))

    X = np.vstack(X_list).T  # (n_vox, n_colors)
    Xz = (X - X.mean(axis=1, keepdims=True)) / (X.std(axis=1, keepdims=True) + 1e-8)
    return Xz, np.array(base_regs)


def diag_linear_predict(train_X, train_y, test_X):
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])
    vars_ = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])
    ll = []
    for k in range(len(classes)):
        ll_k = -0.5*(np.log(2*np.pi*vars_[k]).sum() + ((test_X - means[k])**2/vars_[k]).sum(axis=1))
        ll.append(ll_k)
    ll = np.stack(ll, axis=1)
    preds = classes[ll.argmax(axis=1)]
    return preds


def main():
    run_mats = []
    run_labels = None
    valid_runs = []
    for bold_path in fmri_imgs:
        if not os.path.exists(bold_path):
            print('Missing BOLD file, skipping:', bold_path)
            continue
        out = fit_one_run_and_get_betas(bold_path, mask_img=ROI_MASK)
        if out is None:
            continue
        Xz, cols = out
        run_mats.append(Xz)
        valid_runs.append(bold_path)
        if run_labels is None:
            run_labels = cols

    if len(run_mats) < 2:
        raise RuntimeError('Not enough valid runs')

    # keep only color_* columns
    keep_cols = [j for j, name in enumerate(run_labels.tolist()) if str(name).startswith('color_')]
    if len(keep_cols) < len(run_labels):
        run_mats = [X[:, keep_cols] for X in run_mats]
        run_labels = run_labels[keep_cols]

    # top-k voxels
    k = 100
    absz = np.mean([np.abs(X) for X in run_mats], axis=0)
    score = absz.max(axis=1)
    topk_idx = np.argsort(score)[::-1][:k]
    run_mats_k = [X[topk_idx, :] for X in run_mats]

    samples_per_run = [X.T for X in run_mats_k]
    colors = run_labels

    all_preds, all_true = [], []
    for test_idx in range(len(samples_per_run)):
        X_train = np.vstack([samples_per_run[i] for i in range(len(samples_per_run)) if i!=test_idx])
        y_train = np.tile(colors, len(samples_per_run)-1)
        X_test = samples_per_run[test_idx]
        y_test = colors

        y_pred = diag_linear_predict(X_train, y_train, X_test)
        acc = (y_pred == y_test).mean()
        print(f"[Classification] Test {test_idx+1}: acc={acc:.3f}")
        all_preds.append(y_pred); all_true.append(y_test)

    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_preds)
    acc = (y_true == y_pred).mean()
    print('Overall accuracy:', acc)


if __name__ == '__main__':
    main()
