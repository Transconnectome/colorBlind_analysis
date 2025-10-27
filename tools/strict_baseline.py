#!/usr/bin/env python3
"""
Strict baseline runner that follows the notebook pipeline closely.

Differences from `nilearn_baseline.py`:
- When constructing per-condition 3D NIfTI images, preserve the original header.
- When using a provided mask, resample the mask to each beta image grid with copy_header=True
  to ensure header/voxel alignment matches notebook behavior.
- Use the provided mask (if available) for the NiftiMasker exactly as in the notebook.

This script writes the same artifacts as the baseline runner: results JSON, confusion PNG,
and y_true/y_pred numpy arrays.
"""
import argparse
import os
import glob
import datetime
import json
from pathlib import Path

import numpy as np
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.image import resample_to_img
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


def find_beta_files(subdir, subj):
    pattern = os.path.join(subdir, f"{subj}*deconv_betas_run-*.nii*")
    return sorted(glob.glob(pattern))


def load_nib_img(fname):
    img = nib.load(fname)
    data = img.get_fdata(dtype=np.float32)
    return img, data


def build_run_matrix_from_img(img, data, masker, preserve_header=True):
    # data expected shape: (n_colors, X, Y, Z) or (X,Y,Z,n_colors)
    if data.ndim == 4 and data.shape[0] < 50:
        n_colors = data.shape[0]
    elif data.ndim == 4 and data.shape[-1] < 50:
        data = np.moveaxis(data, -1, 0)
        n_colors = data.shape[0]
    else:
        raise ValueError(f"Unexpected beta data shape {data.shape}")

    imgs = []
    for i in range(n_colors):
        # preserve header when creating Nifti image
        hdr = img.header.copy() if preserve_header else None
        nif = nib.Nifti1Image(data[i].astype(np.float32), img.affine, header=hdr)
        imgs.append(nif)
    arr = masker.transform(imgs)  # (n_colors, n_vox)
    return arr.T  # (n_vox, n_colors)


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


def run_strict(sub, data_dir, outdir, mask_path=None, use_logreg=False, topk=None):
    ensure_dir(outdir)
    beta_files = find_beta_files(os.path.join(data_dir, sub), sub)
    if not beta_files:
        beta_files = find_beta_files(os.path.join(data_dir, ''), sub)
    if not beta_files:
        raise FileNotFoundError('No beta files found')

    # Load all run images
    runs = [load_nib_img(f) + (f,) for f in beta_files]
    # runs: list of tuples (img, data, fname)
    # determine expected n_colors
    n_colors_list = [r[1].shape[0] if r[1].ndim==4 and r[1].shape[0]<50 else (r[1].shape[-1] if r[1].ndim==4 else None) for r in runs]
    expected_n = int(max([n for n in n_colors_list if n is not None]))

    # Build masker: if mask provided, resample to the grid of the first beta image and use that mask
    masker_kwargs = {'standardize': False}
    if mask_path is not None and os.path.exists(mask_path):
        provided = nib.load(mask_path)
        # resample provided mask to first beta image grid
        target_img = runs[0][0]
        provided_rs = None
        resample_failed = False
        try:
            provided_rs = resample_to_img(provided, target_img, interpolation='nearest', copy_header=True)
        except Exception:
            try:
                provided_rs = resample_to_img(provided, target_img, interpolation='nearest', copy_header=False)
            except Exception:
                # if we cannot resample mask to beta grid, we'll instead resample beta images to mask grid later
                resample_failed = True

        if not resample_failed and provided_rs is not None:
            masker = NiftiMasker(mask_img=provided_rs, **masker_kwargs).fit()
            print(f'Using provided mask resampled to first run grid: voxels={(provided_rs.get_fdata()>0).sum()}')
        else:
            # We'll resample beta images to the provided mask grid when processing each run
            masker = NiftiMasker(mask_img=provided, **masker_kwargs).fit()
            print('Could not reliably resample provided mask to beta grid; will resample beta images to provided mask grid for processing')
    else:
        # fallback: compute mask from first run mean
        mean_img = nib.Nifti1Image(np.mean(runs[0][1], axis=0).astype(np.float32), runs[0][0].affine)
        masker = NiftiMasker(mask_img=None, **masker_kwargs).fit(mean_img)
        print(f'Computed mask from first run mean: voxels={(masker.mask_img_.get_fdata()>0).sum()}')

    # Build per-run matrices
    run_mats = []
    valid_runs = []
    for img, data, fname in runs:
        # normalize shape
        if data.ndim == 4 and data.shape[0] >= 50:
            data = np.moveaxis(data, -1, 0)
        if data.ndim != 4:
            print(f'Skipping {fname}: unexpected shape {data.shape}')
            continue
        if data.shape[0] != expected_n:
            print(f'Skipping {fname}: n_colors {data.shape[0]} != expected {expected_n}')
            continue
        if np.isnan(data).any() or np.allclose(data,0):
            print(f'Skipping {fname}: invalid data')
            continue
        mat = build_run_matrix_from_img(img, data, masker, preserve_header=True)
        # per-run z across colors (axis=1 last dim)
        Xz = (mat - mat.mean(axis=1, keepdims=True)) / (mat.std(axis=1, keepdims=True) + 1e-8)
        run_mats.append(Xz)
        valid_runs.append(fname)

    if len(run_mats) == 0:
        raise RuntimeError('No valid runs')

    # optional topk
    if topk is not None and topk>0:
        absz = np.mean([np.abs(X) for X in run_mats], axis=0)
        score = absz.max(axis=1)
        idx = np.argsort(score)[::-1][:topk]
        run_mats = [X[idx, :] for X in run_mats]
        print(f'Selected top-{topk} voxels')

    samples_per_run = [X.T for X in run_mats]
    n_colors = expected_n

    all_preds, all_true = [], []
    for test_idx in range(len(samples_per_run)):
        X_train = np.vstack([samples_per_run[i] for i in range(len(samples_per_run)) if i!=test_idx])
        y_train = np.tile(np.arange(n_colors), len(samples_per_run)-1)
        X_test = samples_per_run[test_idx]
        y_test = np.arange(n_colors)

        if use_logreg:
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)
            clf = LogisticRegression(max_iter=200, solver='liblinear', multi_class='ovr')
            clf.fit(X_train_s, y_train)
            y_pred = clf.predict(X_test_s)
        else:
            y_pred = diag_linear_predict(X_train, y_train, X_test)

        all_preds.append(y_pred); all_true.append(y_test)
        print(f'Test {test_idx+1}: acc={(y_pred==y_test).mean():.3f}')

    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_preds)
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, output_dict=True)

    timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    out_json = os.path.join(outdir, f'strict_baseline_results_{timestamp}.json')
    with open(out_json, 'w') as fh:
        json.dump({'accuracy': float(acc), 'n_runs': len(run_mats), 'n_colors': int(n_colors), 'n_voxels': int(run_mats[0].shape[0]), 'report': report}, fh, indent=2)
    print(f'Wrote {out_json}')

    # save numpy and confusion matrix using plotting util if available
    np.save(os.path.join(outdir, f'y_true_{timestamp}.npy'), y_true)
    np.save(os.path.join(outdir, f'y_pred_{timestamp}.npy'), y_pred)
    try:
        import importlib.util
        plot_path = os.path.join(os.path.dirname(__file__), 'plot_confusion.py')
        spec = importlib.util.spec_from_file_location('plot_confusion', plot_path)
        plot_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plot_mod)
        figfile = os.path.join(outdir, f'confusion_matrix_{timestamp}.png')
        plot_mod.save_confusion_matrix(cm, figfile, acc=acc)
        print(f'Wrote confusion matrix to {figfile}')
    except Exception:
        print('Failed to write confusion matrix via plot_confusion; skipping')

    return {'accuracy': acc, 'cm': cm.tolist(), 'report': out_json}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--sub', default='sub-01')
    p.add_argument('--data_dir', default='derivatives')
    p.add_argument('--outdir', default=None)
    p.add_argument('--mask_path', default=None)
    p.add_argument('--use_logreg', action='store_true')
    p.add_argument('--topk', type=int, default=None)
    args = p.parse_args()

    if args.outdir is None:
        ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        args.outdir = os.path.join('derivatives', args.sub, 'experiments', f'strict_baseline_{ts}')

    ensure_dir(args.outdir)
    res = run_strict(args.sub, args.data_dir, args.outdir, mask_path=args.mask_path, use_logreg=args.use_logreg, topk=args.topk)
    print('Done. Summary:', res)
