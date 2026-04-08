#!/usr/bin/env python3
"""
neural_miss.py — sub-09 neural validation post-mortem.

Gen-4 Stage 3a declared sub-09 V1/V2/hV4 neural validation FAIL
(ρ_fit ≈ 0.12 / -0.52 / -0.19). This script inspects *which colors*
drive the failure and how far the simulated vulnerability profile is
from (i) the CVD observed profile and (ii) the per-HC reference cloud.

For each ROI in {V1, V2, hV4} we:

    1. Pull simulated_vuln, simulated_vuln_baseline, observed_vuln_cvd,
       and per_hc_vuln_fit (7 HC × 8 colors) from
       ``results/step3_neural/sub-09_machado_1way.json``.

    2. Compute per-color rank_diff = rank(obs) - rank(sim) and a sign-match
       flag (vs the color-wise median) so that each color gets a concrete
       miss score.

    3. Run leave-one-color-out Spearman on (obs, sim) across the 7 held-in
       colors: the rescued ρ (ρ_LOO) tells us which colors are single-point
       outliers.

    4. Compare observed_vuln_cvd to the per-HC distribution color-by-color
       (HC mean ± SD, z(obs) w.r.t. HC) — so we can tell whether a color's
       CVD vuln is inside the HC cloud (i.e., no CVD-specific effect to fit)
       or a real CVD outlier that the Machado Δλ simulator simply does not
       match.

    5. Rank colors by a composite "miss score" = |rank_diff| + (1 - sign_match)
       + bonus for being a LOO improver (ρ_LOO - ρ_all > 0.30) and report
       the top offenders.

This is a diagnostic script: there is NO pass/fail verdict. The output
is the input to our manuscript qualification of sub-09.

Outputs (to ``results/sub09_validation/neural_miss/``):
    neural_miss_table.csv          — per-color per-ROI rows
    neural_miss_summary.json       — per-ROI ρ / LOO / offenders / HC cloud
    fig_scatter.png                — obs vs sim scatter (3 panels)
    fig_loo_bar.png                — ρ_LOO per dropped color (3 panels)
    fig_hc_cloud.png               — per-color HC mean±SD with obs marker
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import rankdata, spearmanr

# ---------------------------------------------------------------- paths
_HERE = Path(__file__).resolve().parent
_PIPELINE = _HERE.parent.parent
DEFAULT_JSON = (_PIPELINE / 'results' / 'step3_neural'
                / 'sub-09_machado_1way.json')
DEFAULT_OUT = _PIPELINE / 'results' / 'sub09_validation' / 'neural_miss'

# ---------------------------------------------------------------- config
SUBJECT = '09'
CVD_TYPE = 'protan'
MODEL = 'machado_1way'
ROIS = ['V1', 'V2', 'hV4']

N_COLORS = 8
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
COLOR_TAGS = [f'c{i + 1}' for i in range(N_COLORS)]

# LOO-rescue threshold: a color is an "outlier driver" if dropping it
# raises ρ by more than LOO_RESCUE_THRESHOLD.
LOO_RESCUE_THRESHOLD = 0.30


# ---------------------------------------------------------------- small helpers
def _color_label(idx: int) -> str:
    return f'{COLOR_TAGS[idx]} ({COLOR_NAMES[idx]})'


def _rank(vec: np.ndarray) -> np.ndarray:
    return rankdata(vec, method='average')


def _loo_spearman(obs: np.ndarray, sim: np.ndarray) -> np.ndarray:
    """Return ρ_LOO per dropped color (shape (N_COLORS,))."""
    out = np.empty(N_COLORS, dtype=float)
    for i in range(N_COLORS):
        mask = np.ones(N_COLORS, dtype=bool)
        mask[i] = False
        rho, _ = spearmanr(obs[mask], sim[mask])
        out[i] = float(rho)
    return out


def _hc_cloud_stats(per_hc_vuln: Dict[str, list]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (mean, sd, matrix) over HC per color. matrix shape (n_hc, 8)."""
    mat = np.array([np.asarray(v, dtype=float)
                    for v in per_hc_vuln.values()])
    mean = mat.mean(axis=0)
    sd = mat.std(axis=0, ddof=1)
    return mean, sd, mat


def _safe_z(value: float, mean: float, sd: float) -> float:
    if sd <= 1e-12:
        return float('nan')
    return (value - mean) / sd


# ---------------------------------------------------------------- per-ROI analysis
def _analyse_roi(roi_name: str, roi_payload: dict) -> dict:
    obs = np.asarray(roi_payload['observed_vuln_cvd'], dtype=float)
    sim = np.asarray(roi_payload['simulated_vuln'], dtype=float)
    sim_baseline = np.asarray(roi_payload['simulated_vuln_baseline'], dtype=float)
    per_hc = roi_payload['per_hc_vuln_fit']
    delta_nm = float(roi_payload['delta_lambda_nm'])

    rho_fit = float(roi_payload['rho_fit'])
    rho_baseline = float(roi_payload['rho_baseline'])
    delta_rho_obs = float(roi_payload['delta_rho_obs'])
    label_p = float(roi_payload['label_perm_p'])
    improve_p = float(roi_payload['baseline_improvement_p'])

    # per-color rank difference (obs - sim)
    obs_rank = _rank(obs)
    sim_rank = _rank(sim)
    rank_diff = obs_rank - sim_rank

    # sign match vs column-wise median (simple direction agreement)
    obs_sign = np.sign(obs - np.median(obs))
    sim_sign = np.sign(sim - np.median(sim))
    sign_match = (obs_sign == sim_sign).astype(int)

    # LOO spearman
    rho_loo = _loo_spearman(obs, sim)
    loo_delta = rho_loo - rho_fit           # >0 means dropping color helps
    loo_rescues = loo_delta > LOO_RESCUE_THRESHOLD

    # HC cloud
    hc_mean, hc_sd, hc_mat = _hc_cloud_stats(per_hc)
    z_obs_vs_hc = np.array([_safe_z(o, m, s)
                            for o, m, s in zip(obs, hc_mean, hc_sd)])

    # composite miss score per color
    miss_score = np.abs(rank_diff) + (1 - sign_match)
    miss_score = miss_score.astype(float)
    miss_score[loo_rescues] += 2.0  # penalise LOO rescues heavily

    # rank colors by miss score (descending)
    worst_order = np.argsort(-miss_score)
    worst = [
        {
            'rank': rank + 1,
            'color_index': int(idx),
            'color_label': _color_label(int(idx)),
            'miss_score': float(miss_score[idx]),
            'rank_diff': float(rank_diff[idx]),
            'sign_match': int(sign_match[idx]),
            'loo_delta_rho': float(loo_delta[idx]),
            'loo_rescues_fit': bool(loo_rescues[idx]),
            'obs_vuln': float(obs[idx]),
            'sim_vuln': float(sim[idx]),
            'hc_mean': float(hc_mean[idx]),
            'hc_sd': float(hc_sd[idx]),
            'z_obs_vs_hc': float(z_obs_vs_hc[idx]),
        }
        for rank, idx in enumerate(worst_order[:5])
    ]

    return {
        'roi': roi_name,
        'delta_lambda_nm': delta_nm,
        'rho_fit': rho_fit,
        'rho_baseline': rho_baseline,
        'delta_rho_obs': delta_rho_obs,
        'label_perm_p': label_p,
        'baseline_improvement_p': improve_p,
        'obs': obs.tolist(),
        'sim': sim.tolist(),
        'sim_baseline': sim_baseline.tolist(),
        'obs_rank': obs_rank.tolist(),
        'sim_rank': sim_rank.tolist(),
        'rank_diff': rank_diff.tolist(),
        'sign_match': sign_match.tolist(),
        'sign_match_rate': float(sign_match.mean()),
        'rho_loo_per_dropped': rho_loo.tolist(),
        'loo_delta_rho': loo_delta.tolist(),
        'rho_loo_max': float(rho_loo.max()),
        'rho_loo_argmax': int(np.argmax(rho_loo)),
        'rho_loo_argmax_label': _color_label(int(np.argmax(rho_loo))),
        'hc_mean': hc_mean.tolist(),
        'hc_sd': hc_sd.tolist(),
        'z_obs_vs_hc': z_obs_vs_hc.tolist(),
        'n_colors_inside_hc_cloud_1sd': int(np.sum(np.abs(z_obs_vs_hc) <= 1.0)),
        'worst_offenders_top5': worst,
    }


# ---------------------------------------------------------------- outputs
def _write_table(rows: List[Dict], path: Path) -> None:
    keys = ['roi', 'color_tag', 'color_name', 'delta_lambda_nm',
            'obs_vuln', 'sim_vuln', 'sim_baseline',
            'obs_rank', 'sim_rank', 'rank_diff', 'sign_match',
            'hc_mean', 'hc_sd', 'z_obs_vs_hc',
            'loo_rho_when_dropped', 'loo_delta_rho', 'loo_rescues_fit']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _build_table_rows(roi_results: Dict[str, dict]) -> List[Dict]:
    rows: List[Dict] = []
    for roi, r in roi_results.items():
        delta_nm = r['delta_lambda_nm']
        loo_rescue_flags = (
            np.asarray(r['loo_delta_rho']) > LOO_RESCUE_THRESHOLD
        ).astype(int)
        for c in range(N_COLORS):
            rows.append({
                'roi': roi,
                'color_tag': COLOR_TAGS[c],
                'color_name': COLOR_NAMES[c],
                'delta_lambda_nm': delta_nm,
                'obs_vuln': r['obs'][c],
                'sim_vuln': r['sim'][c],
                'sim_baseline': r['sim_baseline'][c],
                'obs_rank': r['obs_rank'][c],
                'sim_rank': r['sim_rank'][c],
                'rank_diff': r['rank_diff'][c],
                'sign_match': r['sign_match'][c],
                'hc_mean': r['hc_mean'][c],
                'hc_sd': r['hc_sd'][c],
                'z_obs_vs_hc': r['z_obs_vs_hc'][c],
                'loo_rho_when_dropped': r['rho_loo_per_dropped'][c],
                'loo_delta_rho': r['loo_delta_rho'][c],
                'loo_rescues_fit': int(loo_rescue_flags[c]),
            })
    return rows


def _plot_scatter(roi_results: Dict[str, dict], path: Path) -> None:
    fig, axes = plt.subplots(1, len(roi_results),
                             figsize=(4.2 * len(roi_results), 4.2))
    if len(roi_results) == 1:
        axes = [axes]
    for ax, (roi, r) in zip(axes, roi_results.items()):
        obs = np.asarray(r['obs'])
        sim = np.asarray(r['sim'])
        ax.scatter(sim, obs, c='#d62728', s=60, edgecolor='k', zorder=3)
        for c in range(N_COLORS):
            ax.annotate(COLOR_TAGS[c], (sim[c], obs[c]),
                        xytext=(4, 2), textcoords='offset points',
                        fontsize=8)
        lim_lo = min(sim.min(), obs.min()) - 0.05
        lim_hi = max(sim.max(), obs.max()) + 0.05
        ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi],
                ls='--', c='k', alpha=0.4)
        ax.set_xlim(lim_lo, lim_hi)
        ax.set_ylim(lim_lo, lim_hi)
        ax.set_xlabel('simulated vuln (Δλ = {:.1f} nm)'.format(
            r['delta_lambda_nm']))
        ax.set_ylabel('observed vuln (CVD)')
        ax.set_title(
            f'{roi} | ρ={r["rho_fit"]:+.2f}  '
            f'(p={r["label_perm_p"]:.3f})'
        )
        ax.grid(True, alpha=0.2)
    fig.suptitle('sub-09 neural miss: obs vs sim per color', y=1.02)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def _plot_loo(roi_results: Dict[str, dict], path: Path) -> None:
    fig, axes = plt.subplots(1, len(roi_results),
                             figsize=(4.6 * len(roi_results), 3.8))
    if len(roi_results) == 1:
        axes = [axes]
    for ax, (roi, r) in zip(axes, roi_results.items()):
        rho_loo = np.asarray(r['rho_loo_per_dropped'])
        rho_fit = r['rho_fit']
        colors = ['#1f77b4' if rho_loo[c] - rho_fit <= LOO_RESCUE_THRESHOLD
                  else '#d62728'
                  for c in range(N_COLORS)]
        ax.bar(COLOR_TAGS, rho_loo, color=colors, edgecolor='k')
        ax.axhline(rho_fit, color='k', ls='--', lw=1.2,
                   label=f'ρ_all={rho_fit:+.2f}')
        ax.axhline(0, color='grey', lw=0.8)
        ax.set_ylim(-1.05, 1.05)
        ax.set_ylabel('ρ_LOO (dropped color)')
        ax.set_title(
            f'{roi}  max rescue: {r["rho_loo_argmax_label"]} '
            f'(ρ={r["rho_loo_max"]:+.2f})'
        )
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(True, alpha=0.2)
    fig.suptitle('sub-09 leave-one-color-out ρ', y=1.02)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def _plot_hc_cloud(roi_results: Dict[str, dict], path: Path) -> None:
    fig, axes = plt.subplots(1, len(roi_results),
                             figsize=(4.6 * len(roi_results), 3.8))
    if len(roi_results) == 1:
        axes = [axes]
    for ax, (roi, r) in zip(axes, roi_results.items()):
        hc_mean = np.asarray(r['hc_mean'])
        hc_sd = np.asarray(r['hc_sd'])
        obs = np.asarray(r['obs'])
        sim = np.asarray(r['sim'])
        xs = np.arange(N_COLORS)
        ax.errorbar(xs, hc_mean, yerr=hc_sd, fmt='o',
                    color='#1f77b4', ecolor='#1f77b4',
                    elinewidth=1.2, capsize=3, label='HC mean ± 1 SD')
        ax.scatter(xs, obs, marker='s', s=55, color='#d62728',
                   edgecolor='k', label='CVD obs', zorder=4)
        ax.scatter(xs, sim, marker='^', s=55, color='#2ca02c',
                   edgecolor='k', label='Machado sim', zorder=3)
        ax.set_xticks(xs)
        ax.set_xticklabels(COLOR_TAGS, rotation=0)
        ax.set_ylabel('vuln (HC W → subj amps)')
        ax.set_title(f'{roi} | {r["n_colors_inside_hc_cloud_1sd"]}/8 CVD inside ±1SD')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)
    fig.suptitle('sub-09 per-color HC cloud vs CVD obs vs Machado sim', y=1.02)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- driver
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage3_json', default=str(DEFAULT_JSON),
                    help='Path to sub-09 stage 3 neural JSON')
    ap.add_argument('--output_dir', default=str(DEFAULT_OUT),
                    help='Where to write table/JSON/figures')
    args = ap.parse_args()

    stage3_path = Path(args.stage3_json)
    if not stage3_path.exists():
        print(f'[ERR] stage3 JSON not found: {stage3_path}', file=sys.stderr)
        return 2

    with stage3_path.open() as f:
        payload = json.load(f)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'subject={payload.get("subject")} '
          f'model={payload.get("model")} '
          f'δ_v1={payload.get("delta_v1_nm")} '
          f'δ_v2={payload.get("delta_v2_nm")} '
          f'δ̄={payload.get("delta_bar_nm")}')

    roi_results: Dict[str, dict] = {}
    for roi in ROIS:
        if roi not in payload['rois']:
            print(f'[WARN] {roi} missing from stage3 JSON, skipping')
            continue
        r = _analyse_roi(roi, payload['rois'][roi])
        roi_results[roi] = r
        print(
            f'[{roi}] Δλ={r["delta_lambda_nm"]:.2f}  ρ={r["rho_fit"]:+.3f}  '
            f'sign_match={r["sign_match_rate"]:.2f}  '
            f'inside HC ±1SD: {r["n_colors_inside_hc_cloud_1sd"]}/8  '
            f'max ρ_LOO={r["rho_loo_max"]:+.3f} (drop {r["rho_loo_argmax_label"]})'
        )

    # write table
    rows = _build_table_rows(roi_results)
    _write_table(rows, out_dir / 'neural_miss_table.csv')

    # write summary
    summary = {
        'subject': SUBJECT,
        'cvd_type': CVD_TYPE,
        'model': MODEL,
        'timestamp': datetime.now().isoformat(),
        'stage3_json': str(stage3_path),
        'loo_rescue_threshold': LOO_RESCUE_THRESHOLD,
        'rois': roi_results,
    }
    with (out_dir / 'neural_miss_summary.json').open('w') as f:
        json.dump(summary, f, indent=2)

    # figures
    _plot_scatter(roi_results, out_dir / 'fig_scatter.png')
    _plot_loo(roi_results, out_dir / 'fig_loo_bar.png')
    _plot_hc_cloud(roi_results, out_dir / 'fig_hc_cloud.png')

    print(f'\nOutputs written to: {out_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
