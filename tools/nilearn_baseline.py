#!/usr/bin/env python3
"""
Simple baseline runner for sub-01 voxelwise decoding using per-run deconvolution betas.
- Finds per-run deconv betas in derivatives/sub-01 (pattern: '*deconv_betas_run-*.nii*')
- Builds dataset: one sample per (run, color) where X is flattened voxels inside union mask
- Removes constant features, per-fold StandardScaler, optional PCA
- Leave-one-run-out logistic regression, saves accuracy, confusion matrix and artifacts

Usage:
    python tools/nilearn_baseline.py --sub sub-01 --outdir derivatives/sub-01/experiments/baseline_YYYYMMDDTHHMMSS

This is intentionally lightweight and defensive: it will not attempt heavy training or permutations.
"""

import argparse
import os
import sys
import glob
import json
import datetime
import numpy as np
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.image import resample_to_img
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt


def find_beta_files(subdir, subj):
    pattern = os.path.join(subdir, f"{subj}*deconv_betas_run-*.nii*")
    files = sorted(glob.glob(pattern))
    return files


def load_run_betas(fname):
    img = nib.load(fname)
    data = img.get_fdata(dtype=np.float32)
    affine = img.affine
    # expected shape: (n_colors, X, Y, Z) or (X,Y,Z,n_colors) - try to handle both
    if data.ndim == 4:
        # Heuristic: if first dim is small (<50) assume colors in first dim
        if data.shape[0] < 50:
            return data, affine, fname
        else:
            # else assume colors are last dim
            return np.moveaxis(data, -1, 0), affine, fname
    else:
        raise ValueError(f"Unexpected beta image shape {data.shape} in {fname}")


def build_run_matrix_with_mask(run_tuple, masker):
    """Convert one-run beta array to (n_vox, n_colors) using a fitted masker.
    run_tuple: (run_data, affine, fname)
    masker: fitted NiftiMasker
    """
    run_data, affine, fname = run_tuple
    imgs = []
    for i in range(run_data.shape[0]):
        # create a 3D image for this condition using the original affine
        img = nib.Nifti1Image(run_data[i].astype(np.float32), affine)
        imgs.append(img)
    arr = masker.transform(imgs)  # (n_colors, n_vox)
    return arr.T  # (n_vox, n_colors)


def remove_constant_features(X):
    var = X.var(axis=0)
    keep = var > 0
    if keep.sum() == 0:
        raise ValueError("No non-constant features remain after removing constant features.")
    return X[:, keep], keep


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def diag_linear_predict(train_X, train_y, test_X):
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])  # (C, D)
    vars_  = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])   # (C, D)
    ll = []
    for k in range(len(classes)):
        ll_k = -0.5*(np.log(2*np.pi*vars_[k]).sum() + ((test_X - means[k])**2/vars_[k]).sum(axis=1))
        ll.append(ll_k)
    ll = np.stack(ll, axis=1)
    preds = classes[ll.argmax(axis=1)]
    return preds


def run_baseline(sub, data_dir, outdir, pca_n=None, mask_path=None, topk=None, use_logreg=False, mask_strategy='first_run', mask_merge='none', masker_kwargs=None):
    ensure_dir(outdir)
    beta_files = find_beta_files(os.path.join(data_dir, sub), sub)
    if not beta_files:
        # try derivatives/<sub> directly
        beta_files = find_beta_files(os.path.join(data_dir, ''), sub)
    if not beta_files:
        raise FileNotFoundError(f"No deconv beta files found for {sub} in {data_dir}")
    print(f"Found {len(beta_files)} beta files, loading...")
    runs = [load_run_betas(f) for f in beta_files]
    # runs: list of tuples (data, affine, fname)
    n_colors_list = [r[0].shape[0] for r in runs]
    expected_n_colors = int(max(n_colors_list))
    print(f"Detected per-run color counts: {n_colors_list} -> expecting {expected_n_colors} colors per run")

    # Filter runs: skip runs that do not have expected number of colors or contain NaNs/empty data
    valid_runs = []
    skipped = []
    for data, aff, fname in runs:
        if data.shape[0] != expected_n_colors:
            print(f"[WARN] Skipping {os.path.basename(fname)}: has {data.shape[0]} colors (expected {expected_n_colors})")
            skipped.append(fname)
            continue
        if np.isnan(data).any():
            print(f"[WARN] Skipping {os.path.basename(fname)}: contains NaN values")
            skipped.append(fname)
            continue
        if np.allclose(data, 0):
            print(f"[WARN] Skipping {os.path.basename(fname)}: all-zero data")
            skipped.append(fname)
            continue
        valid_runs.append((data, aff, fname))

    if len(valid_runs) == 0:
        raise RuntimeError("No valid runs found after filtering; check beta files and shapes.")

    def _mask_stats(a_img, b_img, target_img=None):
        """Return stats comparing two mask images (resampled to target_img if given)."""
        if target_img is not None:
            a_r = resample_to_img(a_img, target_img, interpolation='nearest')
            b_r = resample_to_img(b_img, target_img, interpolation='nearest')
        else:
            a_r, b_r = a_img, b_img
        a_dat = (a_r.get_fdata() > 0)
        b_dat = (b_r.get_fdata() > 0)
        inter = int(np.logical_and(a_dat, b_dat).sum())
        union = int(np.logical_or(a_dat, b_dat).sum())
        a_tot = int(a_dat.sum())
        b_tot = int(b_dat.sum())
        return {'a_total': a_tot, 'b_total': b_tot, 'intersection': inter, 'union': union,
                'overlap_a': inter / float(a_tot) if a_tot>0 else 0.0,
                'overlap_b': inter / float(b_tot) if b_tot>0 else 0.0,
                'jaccard': inter / float(union) if union>0 else 0.0}

    # Prepare masker: prefer explicit mask_path, else allow strategies: 'first_run' (default) or 'union'
    if masker_kwargs is None:
        masker_kwargs = {'standardize': False}

    if mask_path is not None and os.path.exists(mask_path):
        print(f"Using provided brain mask: {mask_path}")
        provided_img = nib.load(mask_path)
        # compute script-default mask for comparison (fit on first-run mean)
        first_run_data_tmp, first_affine_tmp, _ = valid_runs[0]
        mean_tmp = np.mean(first_run_data_tmp, axis=0)
        mean_tmp_nifti = nib.Nifti1Image(mean_tmp.astype(np.float32), first_affine_tmp)
        masker_tmp = NiftiMasker(mask_img=None, **masker_kwargs).fit(mean_tmp_nifti)
        script_mask_img = masker_tmp.mask_img_
        # compare provided vs script-derived masks (resample provided to script grid)
        stats = _mask_stats(provided_img, script_mask_img, target_img=mean_tmp_nifti)
        print('Mask comparison (provided vs script-default):')
        print(f"  provided total: {stats['b_total']}, script-default total: {stats['a_total']}")
        print(f"  intersection: {stats['intersection']}, union: {stats['union']}")
        print(f"  overlap(provided fraction): {stats['overlap_b']:.3f}, overlap(script fraction): {stats['overlap_a']:.3f}, jaccard: {stats['jaccard']:.3f}")
        # use provided mask (may be merged below)
        masker = NiftiMasker(mask_img=provided_img, **masker_kwargs).fit()
    else:
        if mask_strategy == 'union':
            # compute union mask across all valid run mean images
            print("No explicit mask provided — computing UNION mask across all valid runs (mask_strategy=union)")
            mean_imgs = []
            for data, aff, _ in valid_runs:
                mean_img = np.mean(data, axis=0)
                mean_imgs.append(nib.Nifti1Image(mean_img.astype(np.float32), aff))
            # assume grids are identical; build boolean union of nonzero voxels
            base_affine = mean_imgs[0].affine
            stack = np.stack([mi.get_fdata() for mi in mean_imgs], axis=0)
            union_mask = (np.abs(stack) > 0).any(axis=0).astype(np.uint8)
            union_nifti = nib.Nifti1Image(union_mask, base_affine)
            masker = NiftiMasker(mask_img=union_nifti, **masker_kwargs).fit()
            print(f"Union mask voxels: {int(union_mask.sum())}")
        else:
            print("No explicit mask provided — computing automatic mask from first valid run mean image (mask_strategy=first_run)")
            first_run_data, first_affine, _ = valid_runs[0]
            mean_img = np.mean(first_run_data, axis=0)
            mean_nifti = nib.Nifti1Image(mean_img.astype(np.float32), first_affine)
            masker = NiftiMasker(mask_img=None, **masker_kwargs).fit(mean_nifti)
            try:
                mimg = masker.mask_img_
                print(f"First-run-derived mask voxels: {int((mimg.get_fdata()>0).sum())}")
            except Exception:
                pass

    # If user requested a merge mode and a provided mask exists, merge provided & script-default masks
    if mask_path is not None and mask_merge in ('union', 'intersection'):
        print(f"Merging provided mask with script-default mask using mode={mask_merge}")
        provided_img = nib.load(mask_path)
        # script default mask (fit on first run mean)
        first_run_data_tmp, first_affine_tmp, _ = valid_runs[0]
        mean_tmp = np.mean(first_run_data_tmp, axis=0)
        mean_tmp_nifti = nib.Nifti1Image(mean_tmp.astype(np.float32), first_affine_tmp)
        masker_tmp = NiftiMasker(mask_img=None, **masker_kwargs).fit(mean_tmp_nifti)
        script_mask_img = masker_tmp.mask_img_
        # resample provided to script grid
        provided_rs = resample_to_img(provided_img, mean_tmp_nifti, interpolation='nearest')
        a = (provided_rs.get_fdata() > 0)
        b = (script_mask_img.get_fdata() > 0)
        if mask_merge == 'union':
            merged = (np.logical_or(a, b)).astype(np.uint8)
        else:
            merged = (np.logical_and(a, b)).astype(np.uint8)
        merged_nifti = nib.Nifti1Image(merged, mean_tmp_nifti.affine)
        masker = NiftiMasker(mask_img=merged_nifti, **masker_kwargs).fit()
        stats2 = _mask_stats(merged_nifti, provided_img, target_img=mean_tmp_nifti)
        print(f"After merge - merged voxels: {int(merged.sum())}, overlap with provided: {stats2['overlap_b']:.3f}, jaccard(merged/provided): {stats2['jaccard']:.3f}")

    # Build run matrices consistent with the notebook: per-run (n_vox, n_colors) and per-run voxel-wise z-scoring
    run_mats = []
    for run_tuple in valid_runs:
        mat = build_run_matrix_with_mask(run_tuple, masker)  # (n_vox, n_colors)
        # per-run z-score across colors (axis=1 is voxel axis, we want z across last axis=colors)
        Xz = (mat - mat.mean(axis=1, keepdims=True)) / (mat.std(axis=1, keepdims=True) + 1e-8)
        run_mats.append(Xz)

    # Optionally select top-k voxels by mean absolute z across runs (not a union mask)
    if topk is not None and topk > 0:
        absz = np.mean([np.abs(X) for X in run_mats], axis=0)  # (n_vox, n_colors)
        score = absz.max(axis=1)
        topk_idx = np.argsort(score)[::-1][:topk]
        run_mats = [X[topk_idx, :] for X in run_mats]
        print(f"Selected top-{topk} voxels (by mean |z| score)")

    # Build samples_per_run as in notebook: each entry is (n_colors, n_vox)
    samples_per_run = [X.T for X in run_mats]

    # Prepare labels
    n_colors = expected_n_colors
    colors = np.arange(n_colors)

    # Classification: LOAO per-run using diag-linear by default (match notebook). Optionally use logistic regression.
    all_preds, all_true = [], []
    for test_idx in range(len(samples_per_run)):
        X_train = np.vstack([samples_per_run[i] for i in range(len(samples_per_run)) if i!=test_idx])
        y_train = np.tile(np.arange(n_colors), len(samples_per_run)-1)
        X_test  = samples_per_run[test_idx]
        y_test  = np.arange(n_colors)

        if use_logreg:
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)
            clf = LogisticRegression(max_iter=200, solver='liblinear', multi_class='ovr')
            clf.fit(X_train_s, y_train)
            y_pred = clf.predict(X_test_s)
        else:
            y_pred = diag_linear_predict(X_train, y_train, X_test)

        acc = (y_pred == y_test).mean()
        print(f"[Classification] Test {test_idx+1}: acc={acc:.3f}")
        all_preds.append(y_pred); all_true.append(y_test)

    # Aggregate predictions
    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_preds)
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, output_dict=True)

    timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    out_json = os.path.join(outdir, f"baseline_results_{timestamp}.json")
    with open(out_json, 'w') as fh:
        json.dump({
            'accuracy': float(acc),
            'n_runs': int(len(run_mats)),
            'n_colors': int(n_colors),
            'n_voxels_masked': int(run_mats[0].shape[0]),
            'n_features_used': int(run_mats[0].shape[0]),
            'classification_report': report
        }, fh, indent=2)
    print(f"Wrote results summary to {out_json}")

    # save confusion matrix figure - prefer the external plotting utility if available
    figfile = os.path.join(outdir, f"confusion_matrix_{timestamp}.png")
    try:
        # load tools/plot_confusion.py dynamically to avoid package import issues
        import importlib.util
        plot_path = os.path.join(os.path.dirname(__file__), 'plot_confusion.py')
        spec = importlib.util.spec_from_file_location('plot_confusion', plot_path)
        plot_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plot_mod)
        # use the helper to save the cm image
        plot_mod.save_confusion_matrix(cm, figfile, acc=acc)
        print(f"Wrote confusion matrix to {figfile} using tools/plot_confusion.py")
    except Exception as e:
        # fallback to inline plotting if helper not available or fails
        try:
            fig, ax = plt.subplots(figsize=(6,6))
            im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
            ax.set_title(f"Confusion matrix (acc={acc:.3f})")
            ax.set_xlabel('predicted')
            ax.set_ylabel('true')
            plt.colorbar(im, ax=ax)
            fig.savefig(figfile, dpi=150)
            plt.close(fig)
            print(f"Wrote confusion matrix to {figfile} (inline fallback)")
        except Exception:
            print(f"Failed to write confusion matrix to {figfile}: {e}")

    # save numpy artifacts
    np.save(os.path.join(outdir, f"y_true_{timestamp}.npy"), y_true)
    np.save(os.path.join(outdir, f"y_pred_{timestamp}.npy"), y_pred)
    print("Saved numpy artifacts")

    return {'accuracy': acc, 'cm': cm.tolist(), 'report_path': out_json, 'cm_png': figfile}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--sub', default='sub-01')
    p.add_argument('--data_dir', default='derivatives')
    p.add_argument('--outdir', default=None)
    p.add_argument('--pca', type=int, default=None)
    p.add_argument('--mask_path', default=None, help='Path to explicit brain mask to use')
    p.add_argument('--mask_strategy', choices=['first_run', 'union'], default='first_run', help='How to compute mask when no explicit mask is provided')
    p.add_argument('--mask_merge', choices=['none','union','intersection'], default='none', help='If provided mask differs from script default, optionally merge them before running')
    p.add_argument('--mask_standardize', action='store_true', help='Pass standardize=True to NiftiMasker (notebook used False by default)')
    p.add_argument('--mask_smoothing', type=float, default=None, help='smoothing_fwhm for NiftiMasker (mm)')
    p.add_argument('--topk', type=int, default=None, help='Select top-k voxels by mean |z| across runs')
    p.add_argument('--use_logreg', action='store_true', help='Use logistic regression instead of diag-linear')
    args = p.parse_args()

    if args.outdir is None:
        ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        args.outdir = os.path.join('derivatives', args.sub, 'experiments', f'baseline_{ts}')

    ensure_dir(args.outdir)
    # collect masker kwargs from CLI to mimic notebook settings
    masker_kwargs = {
        'standardize': bool(args.mask_standardize),
    }
    if args.mask_smoothing is not None:
        masker_kwargs['smoothing_fwhm'] = args.mask_smoothing

    res = run_baseline(args.sub, args.data_dir, args.outdir, pca_n=args.pca, mask_path=args.mask_path, topk=args.topk, use_logreg=args.use_logreg, mask_strategy=args.mask_strategy, mask_merge=args.mask_merge, masker_kwargs=masker_kwargs)
    print('Done. Summary:', res)
