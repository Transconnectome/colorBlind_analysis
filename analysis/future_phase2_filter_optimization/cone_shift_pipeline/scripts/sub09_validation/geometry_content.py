#!/usr/bin/env python3
"""
geometry_content.py — sub-09 ΔRDM_obs content inspection.

Verifies that sub-09 protan V1 ΔRDM_obs is not just a cosine-similar
random vector but actually contains the *specific* protan confusion
structure predicted by the Machado Δλ ≈ 16.5 nm simulator.

For both V1 (fitted Δλ = 16.5 nm) and V2 (fitted Δλ = 3.0 nm) we:

    1. Reconstruct ΔRDM_obs = RDM_CVD - RDM_HC_mean  in 8×8 form.
    2. Reconstruct ΔRDM_sim(Δλ_fit) from mean HC W via the Machado
       hue shift → design matrix → correlation RDM pipeline.
    3. Compute Pearson r, Spearman ρ, cosine, and signed agreement
       between obs and sim across the 28 off-diagonal pairs.
    4. List the top-5 negative shifts (confused pairs = decreased
       distance in CVD) and top-5 positive shifts (separated pairs =
       increased distance in CVD) for obs and for sim side by side.
    5. Flag how many of the 'known protan confusion' candidate pairs
       (c1-c4, c1-c5, c1-c8, c2-c3, c4-c5, c7-c8, c1-c2) land inside
       the top-5 obs negative list.
    6. Sweep Δλ ∈ [0, 20] at 0.5 nm step and plot cosine/Pearson/
       Spearman/sign-match profiles to confirm the peak near the fitted
       value.

Pass criterion (per ROI):
    Spearman ρ ≥ 0.50  AND  signed agreement ≥ 0.70

Outputs (to ``results/sub09_validation/geometry/``):
    geometry_table.csv
    geometry_summary.json
    fig_heatmap.png              — 8×8 heatmaps (obs / sim / diff) per ROI
    fig_scatter.png              — obs vs sim, 28 points per ROI
    fig_sweep.png                — metric profile vs Δλ per ROI
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import squareform

# ------------------------------------------------------------------ path setup
_HERE = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HERE.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
_FWD_DIR = str(_HERE.parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS,
    HUE_ANGLES,
    N_CHANNELS,
    N_COLORS,
    create_basis_matrix,
    load_amplitudes,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
from diagnostic_delta_rdm import (  # noqa: E402
    compare_delta_rdm,
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    precompute_hc_W,
)

# ------------------------------------------------------------------ config
SUBJECT = '09'
CVD_TYPE = 'protan'
MODEL = 'machado_1way'

ROI_DISK = {'V1': 'V1', 'V2': 'V2'}
ROI_FIT_DELTA = {'V1': 16.5, 'V2': 3.0}   # from step2_finetune_l3/sub-09_machado_1way.json

LOCAL_BASELINE = (_HERE.parent.parent.parent.parent
                  / 'phase1_procrustes_decoding' / 'results' / 'visualization'
                  / 'full_dataset_C010_with_residuals')

# Color names (c1..c8) follow CLAUDE.md convention
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
COLOR_TAGS = [f'c{i + 1}' for i in range(N_COLORS)]

# 'Known protan confusion' candidate pair list (idx_a, idx_b, label).
# These are the theoretical confusion pairs we expect to shrink the most
# under a protan cone shift in CIELab hue space.
PROTAN_CANDIDATE_PAIRS: List[Tuple[int, int, str]] = [
    (0, 3, 'c1-c4 red-green'),
    (0, 4, 'c1-c5 red-cyan'),
    (0, 7, 'c1-c8 red-magenta'),
    (1, 2, 'c2-c3 orange-yellow'),
    (3, 4, 'c4-c5 green-cyan'),
    (6, 7, 'c7-c8 purple-magenta'),
    (0, 1, 'c1-c2 red-orange'),
]

SPEARMAN_THRESHOLD = 0.50
SIGN_AGREEMENT_THRESHOLD = 0.70

DELTA_SWEEP_NM = np.arange(0.0, 20.0 + 1e-9, 0.5)


# ------------------------------------------------------------------ helpers
def _pair_index(i: int, j: int) -> int:
    """Return condensed-vector index for upper-triangular (i, j) with i < j.

    Uses the scipy-condensed convention: pairs are enumerated row-major
    over the upper triangle of an 8×8 matrix.
    """
    assert 0 <= i < j < N_COLORS
    return N_COLORS * i - (i * (i + 1)) // 2 + (j - i - 1)


def _format_pair(i: int, j: int) -> str:
    return f'{COLOR_TAGS[i]}-{COLOR_TAGS[j]} ({COLOR_NAMES[i]}-{COLOR_NAMES[j]})'


def _topk(vec28: np.ndarray, k: int, sign: str) -> List[Dict]:
    if sign == 'neg':
        idx = np.argsort(vec28)[:k]
    elif sign == 'pos':
        idx = np.argsort(vec28)[::-1][:k]
    else:
        raise ValueError(sign)
    rows = []
    for rank, flat_idx in enumerate(idx, 1):
        i, j = _condensed_to_ij(int(flat_idx))
        rows.append({
            'rank': rank,
            'pair_index': int(flat_idx),
            'i': i,
            'j': j,
            'pair_label': _format_pair(i, j),
            'value': float(vec28[flat_idx]),
        })
    return rows


def _condensed_to_ij(flat_idx: int) -> Tuple[int, int]:
    """Invert scipy condensed distance indexing for N_COLORS=8."""
    for i in range(N_COLORS):
        for j in range(i + 1, N_COLORS):
            if _pair_index(i, j) == flat_idx:
                return i, j
    raise ValueError(f'flat_idx {flat_idx} out of range')


def _load_hc_amps(baseline_dir: str, roi: str) -> Dict[str, np.ndarray]:
    disk_roi = ROI_DISK[roi]
    return {s: load_amplitudes(baseline_dir, s, disk_roi) for s in HC_SUBJECTS}


def _load_cvd_amps(baseline_dir: str, roi: str) -> np.ndarray:
    disk_roi = ROI_DISK[roi]
    return load_amplitudes(baseline_dir, SUBJECT, disk_roi)


def _delta_rdm_sim_for_delta(delta_nm: float,
                             hc_W: Dict[str, np.ndarray],
                             C_baseline: np.ndarray) -> np.ndarray:
    C_shifted = get_design_matrix(MODEL, [float(delta_nm)], cvd_type=CVD_TYPE)
    delta_sim, _ = compute_delta_rdm_sim(
        hc_W, C_shifted, C_baseline, distance='correlation')
    return delta_sim


# ------------------------------------------------------------------ per-ROI analysis
def _analyse_roi(roi: str,
                 baseline_dir: str,
                 C_baseline: np.ndarray) -> Dict:
    print(f'\n[{roi}] load amplitudes, precompute W_HC, ΔRDM_obs')
    hc_amps = _load_hc_amps(baseline_dir, roi)
    amp_cvd = _load_cvd_amps(baseline_dir, roi)
    hc_W, _ = precompute_hc_W(hc_amps, C_baseline)

    delta_obs_28, rdm_cvd, rdm_hc, _ = compute_delta_rdm_obs(
        amp_cvd, hc_amps, distance='correlation')
    delta_obs_mat = squareform(delta_obs_28)
    rdm_cvd_mat = squareform(rdm_cvd)
    rdm_hc_mat = squareform(rdm_hc)

    # ΔRDM_sim at the fitted Δλ
    delta_fit = ROI_FIT_DELTA[roi]
    delta_sim_28 = _delta_rdm_sim_for_delta(delta_fit, hc_W, C_baseline)
    delta_sim_mat = squareform(delta_sim_28)
    metrics_fit = compare_delta_rdm(delta_sim_28, delta_obs_28)

    print(f'[{roi}] metrics @ Δλ={delta_fit:.2f} nm: '
          f'pearson={metrics_fit["pearson_r"]:+.3f}, '
          f'spearman={metrics_fit["spearman_r"]:+.3f}, '
          f'cosine={metrics_fit["cosine"]:+.3f}, '
          f'signed={metrics_fit["signed_agreement"]:.2f} '
          f'(n_valid={metrics_fit["signed_agreement_n"]})')

    # Baseline (Δλ = 0) reference — should be approximately zero everywhere
    delta_sim_zero = _delta_rdm_sim_for_delta(0.0, hc_W, C_baseline)
    metrics_zero = compare_delta_rdm(delta_sim_zero, delta_obs_28)

    # Top-5 extremes in obs and sim
    top_neg_obs = _topk(delta_obs_28, 5, 'neg')
    top_pos_obs = _topk(delta_obs_28, 5, 'pos')
    top_neg_sim = _topk(delta_sim_28, 5, 'neg')
    top_pos_sim = _topk(delta_sim_28, 5, 'pos')

    # Protan candidate-pair audit
    obs_neg_flat_idx = {r['pair_index'] for r in top_neg_obs}
    sim_neg_flat_idx = {r['pair_index'] for r in top_neg_sim}
    candidates = []
    for i, j, label in PROTAN_CANDIDATE_PAIRS:
        pidx = _pair_index(i, j)
        candidates.append({
            'pair_label': label,
            'pair_index': pidx,
            'delta_obs': float(delta_obs_28[pidx]),
            'delta_sim': float(delta_sim_28[pidx]),
            'sign_match': bool(np.sign(delta_obs_28[pidx])
                               == np.sign(delta_sim_28[pidx])),
            'in_obs_top5_neg': pidx in obs_neg_flat_idx,
            'in_sim_top5_neg': pidx in sim_neg_flat_idx,
        })

    # Δλ sweep for the diagnostic profile plot
    sweep_rows = []
    for dl in DELTA_SWEEP_NM:
        delta_sim_dl = _delta_rdm_sim_for_delta(float(dl), hc_W, C_baseline)
        met = compare_delta_rdm(delta_sim_dl, delta_obs_28)
        sweep_rows.append({
            'delta_nm': float(dl),
            'pearson_r': met['pearson_r'],
            'spearman_r': met['spearman_r'],
            'cosine': met['cosine'],
            'signed_agreement': met['signed_agreement'],
            'signed_agreement_n': met['signed_agreement_n'],
        })

    # Verdict
    pass_spearman = metrics_fit['spearman_r'] >= SPEARMAN_THRESHOLD
    pass_sign = metrics_fit['signed_agreement'] >= SIGN_AGREEMENT_THRESHOLD
    verdict = 'PASS' if (pass_spearman and pass_sign) else 'FAIL'

    return {
        'roi': roi,
        'delta_lambda_fit_nm': delta_fit,
        'metrics_at_fit': metrics_fit,
        'metrics_at_zero': metrics_zero,
        'delta_obs_28': delta_obs_28.tolist(),
        'delta_sim_28': delta_sim_28.tolist(),
        'delta_obs_mat': delta_obs_mat.tolist(),
        'delta_sim_mat': delta_sim_mat.tolist(),
        'rdm_cvd_mat': rdm_cvd_mat.tolist(),
        'rdm_hc_mat': rdm_hc_mat.tolist(),
        'top_neg_obs': top_neg_obs,
        'top_pos_obs': top_pos_obs,
        'top_neg_sim': top_neg_sim,
        'top_pos_sim': top_pos_sim,
        'protan_candidates': candidates,
        'delta_sweep': sweep_rows,
        'verdict': {
            'spearman_r': metrics_fit['spearman_r'],
            'spearman_threshold': SPEARMAN_THRESHOLD,
            'spearman_pass': pass_spearman,
            'signed_agreement': metrics_fit['signed_agreement'],
            'sign_threshold': SIGN_AGREEMENT_THRESHOLD,
            'signed_pass': pass_sign,
            'overall': verdict,
        },
    }


# ------------------------------------------------------------------ outputs
def _write_csv(results: Dict[str, Dict], out_path: Path) -> None:
    columns = [
        'roi', 'pair_index', 'pair_label', 'delta_obs', 'delta_sim',
        'delta_diff', 'sign_match',
        'is_protan_candidate',
        'rank_in_obs_neg', 'rank_in_obs_pos',
        'rank_in_sim_neg', 'rank_in_sim_pos',
    ]
    cand_set = {p[2] for p in PROTAN_CANDIDATE_PAIRS}
    cand_map = {(_pair_index(i, j)): label
                for (i, j, label) in PROTAN_CANDIDATE_PAIRS}

    with open(out_path, 'w') as f:
        f.write(','.join(columns) + '\n')
        for roi, res in results.items():
            obs = np.array(res['delta_obs_28'])
            sim = np.array(res['delta_sim_28'])
            # Ranks
            sort_obs = np.argsort(obs)
            obs_neg_rank = {int(idx): r + 1 for r, idx in enumerate(sort_obs)}
            obs_pos_rank = {int(idx): r + 1 for r, idx in enumerate(sort_obs[::-1])}
            sort_sim = np.argsort(sim)
            sim_neg_rank = {int(idx): r + 1 for r, idx in enumerate(sort_sim)}
            sim_pos_rank = {int(idx): r + 1 for r, idx in enumerate(sort_sim[::-1])}
            for pidx in range(len(obs)):
                i, j = _condensed_to_ij(pidx)
                label = _format_pair(i, j)
                is_cand = 1 if pidx in cand_map else 0
                o = obs[pidx]
                s = sim[pidx]
                f.write(','.join([
                    roi,
                    str(pidx),
                    '"' + label + '"',
                    f'{o:.6f}',
                    f'{s:.6f}',
                    f'{o - s:+.6f}',
                    str(int(np.sign(o) == np.sign(s))),
                    str(is_cand),
                    str(obs_neg_rank[pidx]),
                    str(obs_pos_rank[pidx]),
                    str(sim_neg_rank[pidx]),
                    str(sim_pos_rank[pidx]),
                ]) + '\n')


def _plot_heatmap(results: Dict[str, Dict], out_path: Path) -> None:
    rois = list(results.keys())
    fig, axes = plt.subplots(
        len(rois), 3, figsize=(12, 4 * len(rois)), squeeze=False)
    for row, roi in enumerate(rois):
        res = results[roi]
        obs = np.array(res['delta_obs_mat'])
        sim = np.array(res['delta_sim_mat'])
        diff = obs - sim

        vmax = max(float(np.max(np.abs(obs))), float(np.max(np.abs(sim))))
        for col, (mat, title) in enumerate([
            (obs, f'{roi}: ΔRDM_obs'),
            (sim, f'{roi}: ΔRDM_sim (Δλ={res["delta_lambda_fit_nm"]:.1f} nm)'),
            (diff, f'{roi}: obs - sim'),
        ]):
            ax = axes[row, col]
            im = ax.imshow(mat, cmap='RdBu_r', vmin=-vmax, vmax=vmax)
            ax.set_xticks(range(N_COLORS))
            ax.set_xticklabels(COLOR_TAGS, fontsize=8)
            ax.set_yticks(range(N_COLORS))
            ax.set_yticklabels(COLOR_TAGS, fontsize=8)
            ax.set_title(title, fontsize=10)
            fig.colorbar(im, ax=ax, fraction=0.045)
    fig.suptitle(f'sub-{SUBJECT} {CVD_TYPE} × {MODEL}: ΔRDM geometry',
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _plot_scatter(results: Dict[str, Dict], out_path: Path) -> None:
    rois = list(results.keys())
    fig, axes = plt.subplots(1, len(rois), figsize=(5 * len(rois), 5),
                             squeeze=False)
    cand_set = {_pair_index(i, j) for (i, j, _) in PROTAN_CANDIDATE_PAIRS}
    for col, roi in enumerate(rois):
        ax = axes[0, col]
        res = results[roi]
        obs = np.array(res['delta_obs_28'])
        sim = np.array(res['delta_sim_28'])
        colors = ['#d62728' if idx in cand_set else '#1f77b4'
                  for idx in range(len(obs))]
        sizes = [60 if idx in cand_set else 30 for idx in range(len(obs))]
        ax.scatter(sim, obs, c=colors, s=sizes, edgecolor='k', linewidth=0.5)
        # Label protan candidate points
        for i, j, label in PROTAN_CANDIDATE_PAIRS:
            pidx = _pair_index(i, j)
            short = label.split(' ')[0]
            ax.annotate(short, (sim[pidx], obs[pidx]),
                        fontsize=7, xytext=(4, 4),
                        textcoords='offset points')
        # Reference lines
        lim = max(float(np.max(np.abs(obs))), float(np.max(np.abs(sim))))
        ax.plot([-lim, lim], [-lim, lim], 'k--', lw=0.8, alpha=0.5)
        ax.axhline(0, color='gray', lw=0.5)
        ax.axvline(0, color='gray', lw=0.5)
        ax.set_xlim(-lim * 1.1, lim * 1.1)
        ax.set_ylim(-lim * 1.1, lim * 1.1)
        ax.set_xlabel(f'ΔRDM_sim (Δλ={res["delta_lambda_fit_nm"]:.1f} nm)')
        ax.set_ylabel('ΔRDM_obs')
        m = res['metrics_at_fit']
        ax.set_title(
            f'{roi}: r_P={m["pearson_r"]:+.2f} | '
            f'ρ_S={m["spearman_r"]:+.2f} | '
            f'cos={m["cosine"]:+.2f} | '
            f'sign={m["signed_agreement"]:.2f}',
            fontsize=9)
        ax.set_aspect('equal', adjustable='box')
    fig.suptitle(
        f'sub-{SUBJECT} {CVD_TYPE}: ΔRDM_obs vs ΔRDM_sim '
        '(red = protan confusion candidate pairs)',
        fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _plot_sweep(results: Dict[str, Dict], out_path: Path) -> None:
    rois = list(results.keys())
    fig, axes = plt.subplots(1, len(rois), figsize=(6 * len(rois), 4),
                             squeeze=False)
    for col, roi in enumerate(rois):
        ax = axes[0, col]
        sweep = results[roi]['delta_sweep']
        dl = np.array([r['delta_nm'] for r in sweep])
        pe = np.array([r['pearson_r'] for r in sweep])
        sp = np.array([r['spearman_r'] for r in sweep])
        co = np.array([r['cosine'] for r in sweep])
        sg = np.array([r['signed_agreement'] for r in sweep])

        ax.plot(dl, pe, '-', color='#1f77b4', label='Pearson r')
        ax.plot(dl, sp, '-', color='#ff7f0e', label='Spearman ρ')
        ax.plot(dl, co, '-', color='#2ca02c', label='Cosine')
        ax.plot(dl, sg, '-', color='#9467bd', label='Signed agr.')
        ax.axvline(results[roi]['delta_lambda_fit_nm'], color='#d62728',
                   linestyle='--', lw=1.5,
                   label=f'Fitted Δλ = '
                         f'{results[roi]["delta_lambda_fit_nm"]:.1f} nm')
        ax.axhline(0, color='k', lw=0.5)
        ax.set_xlabel('Δλ (nm)')
        ax.set_ylabel('Metric value')
        ax.set_xlim(0, 20)
        ax.set_ylim(-1.05, 1.05)
        ax.set_title(f'{roi}: ΔRDM fit metric sweep', fontsize=10)
        ax.legend(loc='lower right', fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='sub-09 ΔRDM content verification')
    p.add_argument('--baseline_dir', type=str, default=str(LOCAL_BASELINE))
    p.add_argument('--output_dir', type=str,
                   default='results/sub09_validation/geometry')
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('sub-09 ΔRDM geometry content verification')
    print(f'  subject      : sub-{SUBJECT} ({CVD_TYPE})')
    print(f'  model        : {MODEL}')
    print(f'  rois         : {list(ROI_FIT_DELTA.keys())}')
    print(f'  fitted Δλ    : {ROI_FIT_DELTA}')
    print(f'  thresholds   : Spearman ρ ≥ {SPEARMAN_THRESHOLD}, '
          f'signed agr. ≥ {SIGN_AGREEMENT_THRESHOLD}')
    print(f'  baseline_dir : {args.baseline_dir}')
    print(f'  output_dir   : {output_dir}')
    print('=' * 64)

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    results: Dict[str, Dict] = {}
    for roi in ROI_FIT_DELTA:
        results[roi] = _analyse_roi(roi, args.baseline_dir, C_baseline)

    # Per-ROI stdout summary
    print('\n' + '=' * 64)
    print('PER-ROI TOP SHIFTS')
    for roi, res in results.items():
        print(f'\n[{roi}] fitted Δλ = {res["delta_lambda_fit_nm"]:.2f} nm')
        print('  --- top-5 NEGATIVE obs shifts (confused pairs in CVD) ---')
        for r in res['top_neg_obs']:
            print(f'    rank {r["rank"]}: {r["pair_label"]:<30s}  '
                  f'obs={r["value"]:+.4f}')
        print('  --- top-5 POSITIVE obs shifts (separated pairs in CVD) ---')
        for r in res['top_pos_obs']:
            print(f'    rank {r["rank"]}: {r["pair_label"]:<30s}  '
                  f'obs={r["value"]:+.4f}')
        print('  --- protan candidate audit ---')
        hit_count = 0
        for c in res['protan_candidates']:
            mark = 'O' if c['in_obs_top5_neg'] else '.'
            sign_mark = '+' if c['sign_match'] else '-'
            if c['in_obs_top5_neg']:
                hit_count += 1
            print(f'    [{mark}] sign{sign_mark} {c["pair_label"]:<30s}  '
                  f'obs={c["delta_obs"]:+.4f}  sim={c["delta_sim"]:+.4f}')
        total_cands = len(res['protan_candidates'])
        print(f'  → {hit_count}/{total_cands} protan candidates in obs top-5 negative')

    # Write aggregated outputs
    print('\n[write] geometry_table.csv')
    _write_csv(results, output_dir / 'geometry_table.csv')

    summary = {
        'subject': SUBJECT,
        'cvd_type': CVD_TYPE,
        'model': MODEL,
        'thresholds': {
            'spearman_r': SPEARMAN_THRESHOLD,
            'signed_agreement': SIGN_AGREEMENT_THRESHOLD,
        },
        'timestamp': datetime.now().isoformat(),
        'rois': {
            roi: {
                'delta_lambda_fit_nm': res['delta_lambda_fit_nm'],
                'metrics_at_fit': res['metrics_at_fit'],
                'metrics_at_zero': res['metrics_at_zero'],
                'top_neg_obs': res['top_neg_obs'],
                'top_pos_obs': res['top_pos_obs'],
                'top_neg_sim': res['top_neg_sim'],
                'top_pos_sim': res['top_pos_sim'],
                'protan_candidates': res['protan_candidates'],
                'verdict': res['verdict'],
            }
            for roi, res in results.items()
        },
        'overall_verdict': (
            'PASS' if all(r['verdict']['overall'] == 'PASS'
                          for r in results.values())
            else 'MIXED' if any(r['verdict']['overall'] == 'PASS'
                                for r in results.values())
            else 'FAIL'),
    }
    print('[write] geometry_summary.json')
    with open(output_dir / 'geometry_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print('[plot] fig_heatmap.png')
    _plot_heatmap(results, output_dir / 'fig_heatmap.png')
    print('[plot] fig_scatter.png')
    _plot_scatter(results, output_dir / 'fig_scatter.png')
    print('[plot] fig_sweep.png')
    _plot_sweep(results, output_dir / 'fig_sweep.png')

    # Final summary
    print('\n' + '=' * 64)
    print('SUMMARY')
    for roi, res in results.items():
        m = res['metrics_at_fit']
        v = res['verdict']
        print(f'  {roi}: Δλ={res["delta_lambda_fit_nm"]:>5.2f} nm | '
              f'ρ_S={m["spearman_r"]:+.3f} ({"PASS" if v["spearman_pass"] else "FAIL"}) | '
              f'sign={m["signed_agreement"]:.2f} ({"PASS" if v["signed_pass"] else "FAIL"}) | '
              f'overall={v["overall"]}')
    print(f'  overall_verdict: {summary["overall_verdict"]}')
    print('=' * 64)


if __name__ == '__main__':
    main()
