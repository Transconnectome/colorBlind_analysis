#!/usr/bin/env python3
"""cycle8_voxel_bootstrap.py — Plan 04 Cycle 8 #1.

HC subject resample bootstrap on the voxel-axis L of Cycle 7 selection rule.
For each (subj, roi):
  - n_boot=200 HC resamples (with replacement, n=6)
  - per boot: recompute HC mean/std for mean_amp, rdm cell, runc; then z of
    target subject and L_vox-axis = -[sign*z_mean + |z_rdm_row| + |z_runc|]
  - return distribution of L_vox-axis + components

self-contained (only numpy + scipy + standard lib).
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr

HC = ['01', '02', '03', '04', '05', '06']  # sub-07 excluded
N_COLORS = 8
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILY = {'08': ('deutan', 'yellow', -1.0),
          '09': ('protan', 'magenta', +1.0),
          '10': ('deutan', 'yellow', -1.0),
          '04': ('deutan', 'yellow', -1.0),  # HC LOO target (FP candidate, deutan)
          '02': ('protan', 'magenta', +1.0)}  # HC LOO target (FP candidate, protan)


def load_amp(data_root, subj, roi):
    p = Path(data_root) / f'sub-{subj}' / roi / 'amplitudes_procrustes.npy'
    if not p.exists():
        return None
    return np.load(p)


def per_color_signatures(amp):
    R, C, V = amp.shape
    pat = amp.mean(axis=0)  # (C, V)
    rms = np.sqrt((pat ** 2).mean(axis=1))
    mean_amp = pat.mean(axis=1)
    std_amp = pat.std(axis=1)
    k_top = max(1, int(round(V * 0.10)))
    top10 = np.zeros(C)
    for c in range(C):
        v = pat[c]
        idx = np.argsort(-v)[:k_top]
        top10[c] = v[idx].mean()
    rc = np.zeros(C)
    for c in range(C):
        m = amp[:, c, :]
        if V < 2:
            continue
        cs = []
        for i in range(R):
            for j in range(i + 1, R):
                if m[i].std() > 0 and m[j].std() > 0:
                    r, _ = pearsonr(m[i], m[j])
                    cs.append(r if np.isfinite(r) else 0.0)
        rc[c] = float(np.mean(cs)) if cs else 0.0
    return {'mean_amp': mean_amp, 'rms_amp': rms, 'std_amp': std_amp,
            'top10_mean': top10, 'run_consistency': rc}


def color_rdm(amp):
    pat = amp.mean(axis=0)
    C = pat.shape[0]
    rdm = np.zeros((C, C))
    for i in range(C):
        for j in range(C):
            if i == j or pat[i].std() == 0 or pat[j].std() == 0:
                continue
            r, _ = pearsonr(pat[i], pat[j])
            rdm[i, j] = 1.0 - (r if np.isfinite(r) else 0.0)
    return rdm


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--subject', required=True)
    p.add_argument('--roi', required=True)
    p.add_argument('--n_boot', type=int, default=200)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--data_dir', required=True)
    p.add_argument('--output_dir', required=True)
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    fam, color, sign = FAMILY[args.subject]
    c_idx = COLOR_IDX[color]

    # Pre-compute all subject signatures (HC + target)
    all_subs = HC + [args.subject]
    sigs = {}
    rdms = {}
    for s in all_subs:
        amp = load_amp(args.data_dir, s, args.roi)
        if amp is None:
            print(f'[skip] sub-{s} {args.roi}: missing')
            continue
        sigs[s] = per_color_signatures(amp)
        rdms[s] = color_rdm(amp)

    if args.subject not in sigs:
        print(f'Target sub-{args.subject} not loaded — abort')
        sys.exit(1)

    print(f'[Bootstrap] subj={args.subject} roi={args.roi} family={fam} '
          f'color={color}(idx={c_idx}) sign={sign:+.0f} n_boot={args.n_boot}')
    print(f'  HC pool size: {len([h for h in HC if h in sigs])}')

    # LOO: if target itself is a HC, exclude from pool
    hc_avail = [h for h in HC if h in sigs and h != args.subject]
    target = args.subject
    target_mean = sigs[target]['mean_amp'][c_idx]
    target_runc = sigs[target]['run_consistency'][c_idx]
    target_rdm_row = rdms[target][c_idx]  # full (8,) row

    # Point estimate (full HC pool)
    pool_mean = np.mean([sigs[h]['mean_amp'][c_idx] for h in hc_avail])
    pool_mean_sd = np.std([sigs[h]['mean_amp'][c_idx] for h in hc_avail], ddof=1)
    pool_runc = np.mean([sigs[h]['run_consistency'][c_idx] for h in hc_avail])
    pool_runc_sd = np.std([sigs[h]['run_consistency'][c_idx] for h in hc_avail], ddof=1)
    pool_rdm = np.array([rdms[h][c_idx] for h in hc_avail])
    pool_rdm_mu = pool_rdm.mean(axis=0)
    pool_rdm_sd = pool_rdm.std(axis=0, ddof=1)
    pool_rdm_sd = np.where(pool_rdm_sd < 1e-9, 1e-9, pool_rdm_sd)

    z_mean_pt = (target_mean - pool_mean) / pool_mean_sd
    z_runc_pt = (target_runc - pool_runc) / pool_runc_sd
    z_rdm_row_pt = (target_rdm_row - pool_rdm_mu) / pool_rdm_sd
    z_rdm_row_abs_pt = float(np.abs(z_rdm_row_pt).mean())
    L_pt = -(sign * z_mean_pt + z_rdm_row_abs_pt + abs(z_runc_pt))

    # Bootstrap
    boots = {'L_vox': [], 'z_mean': [], 'z_runc': [], 'z_rdm_row_abs': []}
    t0 = time.time()
    for b in range(args.n_boot):
        boot_subs = list(rng.choice(hc_avail, size=len(hc_avail), replace=True))
        bm = np.array([sigs[s]['mean_amp'][c_idx] for s in boot_subs])
        br = np.array([sigs[s]['run_consistency'][c_idx] for s in boot_subs])
        bdr = np.stack([rdms[s][c_idx] for s in boot_subs])  # (n, 8)
        mu_m, sd_m = bm.mean(), bm.std(ddof=1)
        mu_r, sd_r = br.mean(), br.std(ddof=1)
        mu_d = bdr.mean(axis=0)
        sd_d = bdr.std(axis=0, ddof=1)
        sd_m = max(sd_m, 1e-9)
        sd_r = max(sd_r, 1e-9)
        sd_d = np.where(sd_d < 1e-9, 1e-9, sd_d)
        z_m = (target_mean - mu_m) / sd_m
        z_r = (target_runc - mu_r) / sd_r
        z_dr = (target_rdm_row - mu_d) / sd_d
        z_dra = float(np.abs(z_dr).mean())
        L = -(sign * z_m + z_dra + abs(z_r))
        boots['L_vox'].append(float(L))
        boots['z_mean'].append(float(z_m))
        boots['z_runc'].append(float(z_r))
        boots['z_rdm_row_abs'].append(z_dra)
        if (b + 1) % max(1, args.n_boot // 10) == 0:
            print(f'  [{b+1}/{args.n_boot}] elapsed={time.time()-t0:.1f}s')

    summ = {}
    for k, v in boots.items():
        a = np.array(v)
        summ[k] = {
            'mean': float(a.mean()), 'median': float(np.median(a)),
            'std': float(a.std(ddof=1)), 'iqr': float(np.percentile(a, 75) - np.percentile(a, 25)),
            'ci95': [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))],
        }

    out = {
        'subject': args.subject, 'roi': args.roi, 'family': fam,
        'family_color': color, 'sign_family': sign,
        'n_boot': args.n_boot,
        'point_estimate': {
            'L_vox': float(L_pt),
            'z_mean': float(z_mean_pt),
            'z_runc': float(z_runc_pt),
            'z_rdm_row_abs': z_rdm_row_abs_pt,
        },
        'bootstrap_summary': summ,
        'config': {'hc_pool': hc_avail, 'sub07_excluded': True},
    }
    out_path = out_dir / f'sub-{args.subject}_{args.roi}.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote {out_path}')
    print(f'point: L_vox={L_pt:+.2f}  z_mean={z_mean_pt:+.2f} '
          f'z_runc={z_runc_pt:+.2f} |z_rdm|={z_rdm_row_abs_pt:.2f}')
    print(f'boot:  L_vox median={summ["L_vox"]["median"]:+.2f} '
          f'IQR={summ["L_vox"]["iqr"]:.2f}  CI95=[{summ["L_vox"]["ci95"][0]:+.2f}, {summ["L_vox"]["ci95"][1]:+.2f}]')


if __name__ == '__main__':
    main()
