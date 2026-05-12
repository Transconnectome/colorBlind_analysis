"""comparison_8cond_taskCD.py — 8-condition comparison: argmin + per-cell viz + grid + README.

Conditions (8 per subject, 2 subjects = 16 cell-arrays):
  model      ∈ {2comp, machado}
  simulator  ∈ {wretrained, wfixed}
  loss       ∈ {canonical, ccc}

Argmin computed under canonical L_fit (existing 4-term) and CCC variant:
  L_fit_ccc = 1.0·(1 - CCC)/2 + 0.2·L_rdm + 0.1·L_smooth
  CCC = 2·r·σ_sim·σ_obs / (σ_sim² + σ_obs² + (μ_sim - μ_obs)²)

Per-condition outputs (16 sets) in results/fixedW_onlyTest/comparison_8cond/:
  landscape_sub-XX_{model}_{sim}_{loss}_<param>.png
  4col_sub-XX_{model}_{sim}_{loss}_<param>.png
  vuln_hue_sub-XX_{model}_{sim}_{loss}_<param>.png

Combined: comparison_grid_sub-{08,09}.png, summary_8cond.csv, README.md.

§0 compliance: descriptive comparison only. No specificity claims.
"""
from __future__ import annotations
import csv
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.stats import pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'visualization'))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))
_PHASE2 = _THIS_DIR.parent
for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from stim_lab_render import render_at_hue as _render_stim_lab
from machado_simulator import machado_shifted_hue, machado_shifted_hue_at
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)

# ============================================================================
# Paths and constants
# ============================================================================
OUTDIR = _PHASE2 / 'results' / 'fixedW_onlyTest' / 'comparison_8cond'
OUTDIR.mkdir(parents=True, exist_ok=True)

SRC_OLD = _PHASE2 / 'results' / 'old_formula'       # 2-comp landscapes
SRC_PHASE_A = _PHASE2 / 'results' / 'fits' / 'phase_a'  # Machado landscapes

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']
LABELS_SHORT = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']
THETA_CONF_DEG = 150.0   # 2-comp confusion-axis baseline used by dt_old

# Loss weights & normalisers (must match fixedW_onlyTest_v4ccc.py for consistency)
NORM_CCC = 2.0
W_CCC = {'alpha_ccc': 1.0, 'delta_rdm': 0.2, 'epsilon_smooth': 0.1}

CVD_INFO = {'08': ('deutan', '#E07B2C'), '09': ('protan', '#2D8E8B')}
SUBJECTS = ['08', '09']
MODELS = ['2comp', 'machado']
SIMULATORS = ['wretrained', 'wfixed']
LOSSES = ['canonical', 'ccc']


# ============================================================================
# CCC helpers (ddof=0, matching fixedW_onlyTest_v4ccc.py exactly)
# ============================================================================
def ccc_value(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def add_ccc_loss(cells, vuln_cvd):
    """Compute CCC + L_fit_ccc for each cell (in-place augmentation)."""
    vcvd = np.asarray(vuln_cvd)
    for c in cells:
        sim = np.asarray(c['vuln_sim'])
        ccc = ccc_value(sim, vcvd)
        l_ccc = (1.0 - ccc) / NORM_CCC
        l_rdm = c.get('l_rdm', 0.0)
        l_smooth = c.get('l_smooth', 0.0)
        c['ccc'] = float(ccc)
        c['l_ccc'] = float(l_ccc)
        c['l_fit_ccc'] = (W_CCC['alpha_ccc'] * l_ccc +
                          W_CCC['delta_rdm'] * l_rdm +
                          W_CCC['epsilon_smooth'] * l_smooth)
    return cells


# ============================================================================
# Landscape loaders
# ============================================================================
def load_2comp_wretrained(sid):
    """1326-cell augmented landscape with vuln_sim. Returns None if missing
    (Task A still computing). Downstream code skips this condition gracefully.
    """
    fn = SRC_OLD / f'sub-{sid}_V4_4term_landscape_with_vuln_sim.json'
    if not fn.exists():
        print(f'  [skip] {fn.name} missing — 2comp wretrained will be omitted '
              f'from comparison for sub-{sid}.')
        return None
    return json.load(open(fn))


def load_2comp_wfixed(sid):
    fn = SRC_OLD / f'sub-{sid}_V4_wfixed_landscape.json'
    return json.load(open(fn))


def _augment_machado(cells):
    """Ensure each Machado cell has 'delta_lambda_nm' (some files use 'params')."""
    for c in cells:
        if 'delta_lambda_nm' not in c:
            params = c.get('params', [0.0])
            c['delta_lambda_nm'] = float(params[0]) if params else 0.0
    return cells


def load_machado_wretrained(sid):
    fn = SRC_PHASE_A / f'sub-{sid}_V4_machado_1way_landscape.json'
    return _augment_machado(json.load(open(fn)))


def load_machado_wfixed(sid):
    fn = SRC_PHASE_A / f'sub-{sid}_V4_machado_1way_wfixed_landscape.json'
    return _augment_machado(json.load(open(fn)))


def load_vuln_cvd(sid):
    fn = SRC_OLD / f'sub-{sid}_V4_wfixed_summary.json'
    return np.array(json.load(open(fn))['vuln_cvd'])


# ============================================================================
# Pre-image inversion
# ============================================================================
def dt_2comp(theta_deg, bs, bc):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(THETA_CONF_DEG)))


def forward_2comp(theta_deg, bs, bc):
    dt = dt_2comp(theta_deg, bs, bc)
    return (theta_deg + dt) % 360.0, dt


def pre_image_2comp(target_deg, bs, bc, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    fwds = np.array([forward_2comp(t, bs, bc)[0] for t in grid])
    diff = (fwds - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def forward_machado(theta_deg, dlam, family):
    """Machado forward at arbitrary θ using machado_shifted_hue_at."""
    _, hue_shifted, _ = machado_shifted_hue_at(
        float(dlam), family, float(theta_deg) % 360.0)
    return float(np.atleast_1d(np.asarray(hue_shifted))[0])


def pre_image_machado(target_deg, dlam, family, n_grid=3600):
    """Find θ_pre such that forward_machado(θ_pre, ...) ≈ target_deg."""
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    _, hue_shifted, _ = machado_shifted_hue_at(float(dlam), family, grid)
    hue_shifted = np.asarray(hue_shifted, dtype=float)
    diff = (hue_shifted - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


# ============================================================================
# Argmin computation
# ============================================================================
def compute_argmins(cells, model_kind):
    """Return (best_canonical, best_ccc) cells, plus key parameters."""
    best_can = min(cells, key=lambda c: c['l_fit'])
    best_ccc = min(cells, key=lambda c: c['l_fit_ccc'])
    return best_can, best_ccc


def param_tag(model_kind, cell):
    if model_kind == '2comp':
        return f"bs{int(cell['bs'])}_bc{int(cell['bc']):+d}"
    else:
        dl = cell.get('delta_lambda_nm', cell.get('params', [0.0])[0])
        return f"dlam{dl:.1f}".replace('.', 'p')


def param_norm(model_kind, cell):
    """Return the 'magnitude' metric: norm for 2-comp, Δλ for Machado."""
    if model_kind == '2comp':
        return float(np.hypot(cell['bs'], cell['bc']))
    else:
        return float(cell.get('delta_lambda_nm', cell.get('params', [0.0])[0]))


# ============================================================================
# Per-condition visualisations
# ============================================================================
def render_landscape_2comp(cells, best, sid, family, color, loss_key, out_path):
    bs_vals = sorted(set(c['bs'] for c in cells))
    bc_vals = sorted(set(c['bc'] for c in cells))
    bs_idx = {v: i for i, v in enumerate(bs_vals)}
    bc_idx = {v: i for i, v in enumerate(bc_vals)}
    grid = np.full((len(bc_vals), len(bs_vals)), np.nan)
    key = 'ccc' if loss_key == 'ccc' else 'spearman_r'
    for c in cells:
        grid[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]

    fig, ax = plt.subplots(figsize=(5.2, 4.8), dpi=130)
    vmin = -0.5; vmax = 0.9
    im = ax.pcolormesh(bs_vals, bc_vals, grid, cmap='RdBu_r',
                       vmin=vmin, vmax=vmax, shading='nearest', rasterized=True)
    ax.plot(best['bs'], best['bc'], '*', color='white', ms=14,
            markeredgecolor='black', markeredgewidth=0.8, zorder=10)
    annot = (f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
             f"ρ={best['spearman_r']:.3f}, CCC={best.get('ccc', 0.0):.3f}")
    ax.text(best['bs'] + 2, best['bc'] - 2, annot,
            fontsize=8, color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.55, lw=0))
    ax.set_xlabel('β_s — S-cone shift (°)')
    ax.set_ylabel('β_c — confusion rotation (°)')
    ax.set_title(out_path.stem.replace('landscape_', ''), fontsize=9,
                 fontweight='bold', color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label('CCC' if loss_key == 'ccc' else 'Spearman ρ')
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches='tight')
    plt.close(fig)


def render_landscape_machado(cells, best, sid, family, color, loss_key, out_path):
    dlams = np.array([c['delta_lambda_nm'] for c in cells])
    rhos = np.array([c['spearman_r'] for c in cells])
    cccs = np.array([c.get('ccc', 0.0) for c in cells])
    lfit_can = np.array([c['l_fit'] for c in cells])
    lfit_ccc = np.array([c['l_fit_ccc'] for c in cells])

    fig, axes = plt.subplots(2, 1, figsize=(5.4, 4.6), dpi=130, sharex=True)
    axes[0].plot(dlams, rhos, 'o-', color=color, ms=4, lw=1.0, label='Spearman ρ')
    axes[0].plot(dlams, cccs, 's--', color='#777777', ms=3, lw=0.8, label='CCC')
    axes[0].axvline(best['delta_lambda_nm'], color='red', ls=':', lw=1.0)
    axes[0].set_ylabel('Score')
    axes[0].set_ylim(-0.7, 1.0)
    axes[0].axhline(0, color='#bbb', lw=0.4)
    axes[0].legend(fontsize=8)
    axes[0].spines[['top', 'right']].set_visible(False)

    axes[1].plot(dlams, lfit_can, 'o-', color='#444', ms=3, lw=0.8,
                 label='L_fit canonical')
    axes[1].plot(dlams, lfit_ccc, 's-', color=color, ms=3, lw=0.8,
                 label='L_fit_ccc')
    axes[1].axvline(best['delta_lambda_nm'], color='red', ls=':', lw=1.0)
    axes[1].set_xlabel('Δλ (nm)')
    axes[1].set_ylabel('Loss')
    axes[1].legend(fontsize=8)
    axes[1].spines[['top', 'right']].set_visible(False)

    fig.suptitle(out_path.stem.replace('landscape_', ''), fontsize=9,
                 fontweight='bold', color=color)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches='tight')
    plt.close(fig)


def render_4col(model_kind, cells_best, sid, family, color, loss_key, out_path):
    """4-column swatches: Original | CVD perceives | Filtered (pre-image) | CVD(Filtered)."""
    fig, axes = plt.subplots(8, 4, figsize=(5.5, 6.0),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    if model_kind == '2comp':
        bs, bc = cells_best['bs'], cells_best['bc']
        norm = float(np.hypot(bs, bc))
        ccc_val = cells_best.get('ccc', 0.0)
        rho = cells_best['spearman_r']
        title = (f"sub-{sid} ({family}) V4 2comp/{loss_key} "
                 f"β_s={bs:.0f}°, β_c={bc:+.0f}° (norm={norm:.1f}°) "
                 f"ρ={rho:.3f} CCC={ccc_val:.3f}")
    else:
        dl = cells_best['delta_lambda_nm']
        rho = cells_best['spearman_r']
        ccc_val = cells_best.get('ccc', 0.0)
        title = (f"sub-{sid} ({family}) V4 machado/{loss_key} "
                 f"Δλ={dl:.1f} nm  ρ={rho:.3f} CCC={ccc_val:.3f}")
    fig.suptitle(title, fontsize=9, y=1.00, color=color, fontweight='bold')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        axes[0, j].set_title(ct, fontsize=8)

    p2a_total, p2a_exact = 0.0, 0
    for i, theta in enumerate(HUE_ANGLES):
        if model_kind == '2comp':
            theta_cvd, dt = forward_2comp(float(theta), cells_best['bs'], cells_best['bc'])
            theta_pre, _ = pre_image_2comp(float(theta), cells_best['bs'], cells_best['bc'])
            theta_cvd_pre, _ = forward_2comp(theta_pre, cells_best['bs'], cells_best['bc'])
        else:
            dl = cells_best['delta_lambda_nm']
            theta_cvd = forward_machado(float(theta), dl, family)
            dt = (theta_cvd - theta + 180.0) % 360.0 - 180.0
            theta_pre, _ = pre_image_machado(float(theta), dl, family)
            theta_cvd_pre = forward_machado(theta_pre, dl, family)

        rgb_o = _render_stim_lab(float(theta), dL=0.0)
        rgb_cvd = _render_stim_lab(theta_cvd, dL=0.0)
        rgb_pre = _render_stim_lab(theta_pre, dL=0.0)
        rgb_cvd_pre = _render_stim_lab(theta_cvd_pre, dL=0.0)

        for k, rgb in enumerate([rgb_o, rgb_cvd, rgb_pre, rgb_cvd_pre]):
            ax = axes[i, k]
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            for sp in ax.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.5)

        axes[i, 0].text(-0.10, 0.5, f'{COLOR_LABELS[i]}\nθ={theta}°',
                        ha='right', va='center', fontsize=6.5,
                        transform=axes[i, 0].transAxes)

        if sid == '08':
            pred_name = hc_name(theta_cvd)
            tgt_name = SUB08_ORIGINAL_HC_EQUIV[int(theta)]
            score = hc_match_score(pred_name, tgt_name)
            mark = '✓' if pred_name == tgt_name else ('~' if score > 0 else '✗')
            txt_col = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
            axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}° {mark}',
                            ha='center', va='top', fontsize=6.5,
                            transform=axes[i, 1].transAxes, color=txt_col)
            p2a_total += score
            if pred_name == tgt_name:
                p2a_exact += 1
        else:
            axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}°',
                            ha='center', va='top', fontsize=6.5,
                            transform=axes[i, 1].transAxes)
        axes[i, 2].text(0.5, -0.02, f'θ_pre={theta_pre:.0f}°',
                        ha='center', va='top', fontsize=6.5,
                        transform=axes[i, 2].transAxes)

    if sid == '08':
        fig.text(0.5, -0.005, f'P2a={p2a_total/8:.3f} ({p2a_exact}/8 exact)',
                 ha='center', fontsize=7.5, color=color)
    plt.savefig(out_path, dpi=130, bbox_inches='tight')
    plt.close(fig)


def render_vuln_hue(vuln_cvd, best, model_kind, sid, family, color,
                    loss_key, out_path):
    fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=130)
    x = np.arange(8)
    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222', ms=5, lw=0.7,
            label='Observed (CVD)')
    vs = np.array(best['vuln_sim'])
    rho = best['spearman_r']
    ccc_val = best.get('ccc', 0.0)
    ax.plot(x, vs, 's-', color=color, ms=5, lw=1.4,
            label=f'sim (ρ={rho:.3f}, CCC={ccc_val:.3f})')
    ax.set_xticks(x); ax.set_xticklabels(LABELS_SHORT)
    ax.set_xlabel('Hue (DKL bin)')
    ax.set_ylabel('LOCO vulnerability')
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(out_path.stem.replace('vuln_hue_', ''), fontsize=8.5,
                 fontweight='bold', color=color)
    ax.legend(fontsize=8, loc='best')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches='tight')
    plt.close(fig)


# ============================================================================
# Combined comparison grid (4 rows × 4 columns per subject)
# ============================================================================
def render_comparison_grid(sid, family, color, condition_results, out_path):
    """4 rows (model × loss) × 4 columns (Original / CVD-perceives × {wretrained, wfixed}).

    Each cell shows 8 hue swatches stacked vertically.
    Row labels: 2comp-can, 2comp-ccc, machado-can, machado-ccc
    Col labels: wretrained-Original / wretrained-CVD / wfixed-Original / wfixed-CVD
    """
    # condition_results: dict[(model, sim, loss)] -> best cell
    row_specs = [
        ('2comp', 'canonical', '2-comp · canonical'),
        ('2comp', 'ccc',       '2-comp · CCC'),
        ('machado', 'canonical', 'Machado · canonical'),
        ('machado', 'ccc',       'Machado · CCC'),
    ]
    col_specs = [
        ('wretrained', 'orig', 'wretrained — Original'),
        ('wretrained', 'cvd',  'wretrained — CVD perceives'),
        ('wfixed', 'orig',     'wfixed — Original'),
        ('wfixed', 'cvd',      'wfixed — CVD perceives'),
    ]
    nrows, ncols = len(row_specs), len(col_specs)
    fig = plt.figure(figsize=(11.5, 11.5), dpi=130)
    fig.suptitle(f"sub-{sid} ({family}) V4 — 8-condition comparison grid "
                 f"(2comp × wretrained/wfixed × canonical/CCC + Machado same)",
                 fontsize=11, y=0.995, color=color, fontweight='bold')

    # Layout: each row has a row label gutter, each col has 8 stacked sub-axes
    outer = fig.add_gridspec(nrows, ncols, hspace=0.30, wspace=0.18,
                             left=0.10, right=0.97, top=0.94, bottom=0.04)
    for r, (model, loss, row_label) in enumerate(row_specs):
        for c, (sim, kind, col_label) in enumerate(col_specs):
            if (model, sim, loss) not in condition_results:
                # Render N/A placeholder cell
                inner = outer[r, c].subgridspec(8, 1, hspace=0.05)
                for k in range(8):
                    ax = fig.add_subplot(inner[k, 0])
                    ax.add_patch(Rectangle((0, 0), 1, 1, color='#dddddd'))
                    ax.set_xticks([]); ax.set_yticks([])
                    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                    for sp in ax.spines.values():
                        sp.set_edgecolor('black'); sp.set_linewidth(0.4)
                    if c == 0 and k == 0:
                        ax.text(-0.42, 0.5, row_label,
                                ha='right', va='center', fontsize=8,
                                transform=ax.transAxes, fontweight='bold')
                    if k == 3:
                        ax.text(0.5, 0.5, 'N/A\n(Task A\npending)',
                                ha='center', va='center', fontsize=7,
                                color='#666666',
                                transform=ax.transAxes)
                continue
            best = condition_results[(model, sim, loss)]
            inner = outer[r, c].subgridspec(8, 1, hspace=0.05)

            # Compute hue values for this cell
            theta_vals = HUE_ANGLES
            if model == '2comp':
                bs, bc = best['bs'], best['bc']
                if kind == 'orig':
                    hue_vals = list(theta_vals)
                else:
                    hue_vals = [forward_2comp(float(t), bs, bc)[0] for t in theta_vals]
            else:
                dl = best['delta_lambda_nm']
                if kind == 'orig':
                    hue_vals = list(theta_vals)
                else:
                    hue_vals = [forward_machado(float(t), dl, family) for t in theta_vals]

            for k, h in enumerate(hue_vals):
                ax = fig.add_subplot(inner[k, 0])
                rgb = _render_stim_lab(float(h), dL=0.0)
                ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
                ax.set_xticks([]); ax.set_yticks([])
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                for sp in ax.spines.values():
                    sp.set_edgecolor('black'); sp.set_linewidth(0.4)
                if c == 0 and k == 0:
                    # row label on first column at top
                    ax.text(-0.42, 0.5, row_label,
                            ha='right', va='center', fontsize=8,
                            transform=ax.transAxes, fontweight='bold')
                if r == 0 and k == 0:
                    # column label on first row
                    if model == '2comp':
                        tag = f'β=({best["bs"]:.0f},{best["bc"]:+.0f})'
                    else:
                        tag = f'Δλ={best["delta_lambda_nm"]:.1f}nm'
                    ax.set_title(f'{col_label}\n{tag}', fontsize=7.5, pad=4)
                if r > 0 and k == 0:
                    # per-row argmin tag (compact)
                    if model == '2comp':
                        tag = f'β=({best["bs"]:.0f},{best["bc"]:+.0f})'
                    else:
                        tag = f'Δλ={best["delta_lambda_nm"]:.1f}nm'
                    ax.set_title(tag, fontsize=7.0, pad=2)

    plt.savefig(out_path, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'wrote {out_path.name}')


# ============================================================================
# Main driver
# ============================================================================
def main():
    print(f'OUTDIR: {OUTDIR}')

    # Load all 4 landscapes per subject, augment with CCC, compute argmins
    all_results = {}
    for sid in SUBJECTS:
        family, color = CVD_INFO[sid]
        print(f'\n=== sub-{sid} ({family}) ===')
        vuln_cvd = load_vuln_cvd(sid)

        landscapes = {
            ('2comp', 'wretrained'): load_2comp_wretrained(sid),
            ('2comp', 'wfixed'):     load_2comp_wfixed(sid),
            ('machado', 'wretrained'): load_machado_wretrained(sid),
            ('machado', 'wfixed'):     load_machado_wfixed(sid),
        }
        # Drop missing conditions (Task A still computing)
        landscapes = {k: v for k, v in landscapes.items() if v is not None}
        # Augment CCC + L_fit_ccc on each
        for k, cells in landscapes.items():
            add_ccc_loss(cells, vuln_cvd)

        # Compute argmins
        condition_results = {}
        for (model, sim), cells in landscapes.items():
            best_can = min(cells, key=lambda c: c['l_fit'])
            best_ccc = min(cells, key=lambda c: c['l_fit_ccc'])
            condition_results[(model, sim, 'canonical')] = best_can
            condition_results[(model, sim, 'ccc')] = best_ccc
            print(f'  ({model:7s}, {sim:10s}): '
                  f'canonical→{param_tag(model, best_can):>14s} ρ={best_can["spearman_r"]:+.3f} '
                  f'CCC={best_can["ccc"]:+.3f} | '
                  f'ccc→{param_tag(model, best_ccc):>14s} ρ={best_ccc["spearman_r"]:+.3f} '
                  f'CCC={best_ccc["ccc"]:+.3f}')

        all_results[sid] = {
            'vuln_cvd': vuln_cvd,
            'landscapes': landscapes,
            'conditions': condition_results,
            'family': family, 'color': color,
        }

    # ------------------------------------------------------------------------
    # Per-condition figures: 16 sets
    # ------------------------------------------------------------------------
    print('\n=== Per-condition figures ===')
    for sid in SUBJECTS:
        family, color = CVD_INFO[sid]
        vuln_cvd = all_results[sid]['vuln_cvd']
        for model in MODELS:
            for sim in SIMULATORS:
                if (model, sim) not in all_results[sid]['landscapes']:
                    print(f'  [skip] sub-{sid} {model}/{sim}: landscape missing')
                    continue
                cells = all_results[sid]['landscapes'][(model, sim)]
                for loss in LOSSES:
                    best = all_results[sid]['conditions'][(model, sim, loss)]
                    tag = param_tag(model, best)
                    stem = f'sub-{sid}_{model}_{sim}_{loss}_{tag}'
                    # landscape
                    p_land = OUTDIR / f'landscape_{stem}.png'
                    if model == '2comp':
                        render_landscape_2comp(cells, best, sid, family, color,
                                               loss, p_land)
                    else:
                        render_landscape_machado(cells, best, sid, family, color,
                                                 loss, p_land)
                    # 4col swatches
                    p_4col = OUTDIR / f'4col_{stem}.png'
                    render_4col(model, best, sid, family, color, loss, p_4col)
                    # vuln_hue
                    p_v = OUTDIR / f'vuln_hue_{stem}.png'
                    render_vuln_hue(vuln_cvd, best, model, sid, family, color,
                                    loss, p_v)
                    print(f'  sub-{sid} {model}/{sim}/{loss}: {tag}')

    # ------------------------------------------------------------------------
    # Combined comparison grid (per subject)
    # ------------------------------------------------------------------------
    print('\n=== Combined comparison grid ===')
    for sid in SUBJECTS:
        family, color = CVD_INFO[sid]
        out_path = OUTDIR / f'comparison_grid_sub-{sid}.png'
        render_comparison_grid(sid, family, color,
                               all_results[sid]['conditions'], out_path)

    # ------------------------------------------------------------------------
    # Summary CSV
    # ------------------------------------------------------------------------
    print('\n=== Summary CSV ===')
    csv_path = OUTDIR / 'summary_8cond.csv'
    rows = []
    for sid in SUBJECTS:
        family = all_results[sid]['family']
        for model in MODELS:
            for sim in SIMULATORS:
                for loss in LOSSES:
                    if (model, sim, loss) not in all_results[sid]['conditions']:
                        continue
                    best = all_results[sid]['conditions'][(model, sim, loss)]
                    vs = np.array(best['vuln_sim'])
                    if model == '2comp':
                        argmin_param = f"bs={best['bs']:.0f},bc={best['bc']:+.0f}"
                    else:
                        argmin_param = f"dlam={best['delta_lambda_nm']:.1f}"
                    rows.append({
                        'subject': f'sub-{sid}',
                        'cvd_family': family,
                        'model': model,
                        'simulator': sim,
                        'loss': loss,
                        'argmin_params': argmin_param,
                        'norm_or_dlam': round(param_norm(model, best), 2),
                        'best_rho': round(best['spearman_r'], 4),
                        'best_ccc': round(best['ccc'], 4),
                        'l_fit_canonical': round(best['l_fit'], 4),
                        'l_fit_ccc': round(best['l_fit_ccc'], 4),
                        'max_sigma_sim': round(float(np.std(vs, ddof=1)), 4),
                    })
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f'wrote {csv_path.name}')

    # Save summary JSON for downstream use
    json_path = OUTDIR / 'summary_8cond.json'
    json_rows = []
    for sid in SUBJECTS:
        family = all_results[sid]['family']
        for model in MODELS:
            for sim in SIMULATORS:
                for loss in LOSSES:
                    if (model, sim, loss) not in all_results[sid]['conditions']:
                        continue
                    best = all_results[sid]['conditions'][(model, sim, loss)]
                    entry = {
                        'subject': sid, 'cvd_family': family,
                        'model': model, 'simulator': sim, 'loss': loss,
                        'best': {k: best[k] for k in best
                                 if k not in ('vuln_sim', 'delta_theta')},
                        'vuln_sim': best['vuln_sim'],
                        'delta_theta': best.get('delta_theta'),
                        'norm_or_dlam': param_norm(model, best),
                    }
                    json_rows.append(entry)
    with open(json_path, 'w') as f:
        json.dump({'conditions': json_rows}, f, indent=2)
    print(f'wrote {json_path.name}')

    # ------------------------------------------------------------------------
    # README
    # ------------------------------------------------------------------------
    print('\n=== README ===')
    write_readme(rows, all_results)


def write_readme(rows, all_results):
    md = []
    md += [
        '# 8-Condition Comparison Grid — sub-08 / sub-09 V4',
        '',
        f'Generated: {Path(__file__).name}',
        '',
        ('Compares argmins across **{Machado, 2-component} × '
         '{wretrained, wfixed} × {canonical L_fit, CCC loss}** for sub-08 '
         '(deutan) and sub-09 (protan) at V4. 16 (subject × condition) cells total.'),
        '',
        '## Methodology (descriptive only — §0 compliant)',
        '',
        '- **Simulators**:',
        '  - `wretrained` (shift_at_both): W retrained at every parameter via '
        'LOCO on shifted C; held-out test also uses shifted C.',
        '  - `wfixed` (shift_at_test_only, A1): W_k trained ONCE per (HC × '
        'held-out color) on UNSHIFTED C_baseline; only test design is shifted.',
        '- **Losses**:',
        '  - `canonical`: 4-term `1·L_vuln + 0.5·L_rank + 0.2·L_rdm + '
        '0.1·L_smooth` (NORM `{vuln:4, rank:2, rdm:2, smooth:32400}`).',
        '  - `ccc`: `1·(1−CCC)/2 + 0.2·L_rdm + 0.1·L_smooth`, where CCC is '
        "Lin's Concordance Correlation Coefficient with ddof=0 std (matches "
        '`fixedW_onlyTest_v4ccc.py`).',
        '- **Grids**:',
        '  - 2-component: β_s∈[0,50] step 2, β_c∈[−50,50] step 2 (1326 cells).',
        '  - Machado 1way: Δλ∈[0,20] step 0.5 nm (41 cells). Sign of cone-shift '
        'is encoded by family (deutan/protan), not by Δλ.',
        '- **HC pool**: sub-01..07 (n=7), V4 ROI; same as cached wretrained.',
        '- **CVD target vuln**: identical across all conditions per subject '
        '(loaded from `sub-XX_V4_wfixed_summary.json`).',
        '',
        '## §0 framing reminder',
        '',
        ('Per project CLAUDE.md §0, this is a **descriptive comparison** of '
         'methodological choices. We do **not** claim specificity from any '
         'condition; we do **not** use cross-condition agreement to select a '
         '"winner" filter. Behavioral validation is the sole filter-selection '
         'ground truth (CLAUDE.md §0, behav_validation.md §3).'),
        '',
        '## Results table (16 rows)',
        '',
        '| subject | model | simulator | loss | argmin | norm_or_Δλ | ρ | CCC | L_fit_can | L_fit_ccc | max σ_sim |',
        '|---|---|---|---|---|---|---|---|---|---|---|',
    ]
    for r in rows:
        md.append(
            f"| {r['subject']} | {r['model']} | {r['simulator']} | {r['loss']} "
            f"| {r['argmin_params']} | {r['norm_or_dlam']} "
            f"| {r['best_rho']:+.3f} | {r['best_ccc']:+.3f} "
            f"| {r['l_fit_canonical']:.4f} | {r['l_fit_ccc']:.4f} "
            f"| {r['max_sigma_sim']:.3f} |"
        )

    # Cross-condition agreement analysis
    md += [
        '',
        '## Key observations',
        '',
        '### A. Within (subject × model), do canonical vs CCC argmins agree?',
        '',
    ]
    for sid in SUBJECTS:
        family = all_results[sid]['family']
        for model in MODELS:
            for sim in SIMULATORS:
                if (model, sim, 'canonical') not in all_results[sid]['conditions']:
                    md.append(f"- sub-{sid} {model} {sim}: N/A (Task A pending)")
                    continue
                can = all_results[sid]['conditions'][(model, sim, 'canonical')]
                ccc = all_results[sid]['conditions'][(model, sim, 'ccc')]
                if model == '2comp':
                    agree = (can['bs'] == ccc['bs']) and (can['bc'] == ccc['bc'])
                    can_p = f"β=({can['bs']:.0f},{can['bc']:+.0f})"
                    ccc_p = f"β=({ccc['bs']:.0f},{ccc['bc']:+.0f})"
                else:
                    agree = (can['delta_lambda_nm'] == ccc['delta_lambda_nm'])
                    can_p = f"Δλ={can['delta_lambda_nm']:.1f}"
                    ccc_p = f"Δλ={ccc['delta_lambda_nm']:.1f}"
                md.append(f"- sub-{sid} {model} {sim}: canonical={can_p}, "
                          f"ccc={ccc_p} → {'AGREE' if agree else 'DIVERGE'}")
        md.append('')

    md += [
        '### B. Within (subject × loss), do wretrained vs wfixed argmins agree?',
        '',
    ]
    for sid in SUBJECTS:
        for model in MODELS:
            for loss in LOSSES:
                if (model, 'wretrained', loss) not in all_results[sid]['conditions']:
                    md.append(f"- sub-{sid} {model} {loss}: N/A wretrained (Task A pending)")
                    continue
                wr = all_results[sid]['conditions'][(model, 'wretrained', loss)]
                wf = all_results[sid]['conditions'][(model, 'wfixed', loss)]
                if model == '2comp':
                    agree = (wr['bs'] == wf['bs']) and (wr['bc'] == wf['bc'])
                    wr_p = f"β=({wr['bs']:.0f},{wr['bc']:+.0f})"
                    wf_p = f"β=({wf['bs']:.0f},{wf['bc']:+.0f})"
                else:
                    agree = (wr['delta_lambda_nm'] == wf['delta_lambda_nm'])
                    wr_p = f"Δλ={wr['delta_lambda_nm']:.1f}"
                    wf_p = f"Δλ={wf['delta_lambda_nm']:.1f}"
                md.append(f"- sub-{sid} {model} {loss}: wretrained={wr_p}, "
                          f"wfixed={wf_p} → {'AGREE' if agree else 'DIVERGE'}")
        md.append('')

    # Behavioral consistency analysis (within model class only)
    md += [
        '### C. Behavioral consistency check (per `raw_behav.md`)',
        '',
        ('User note: sub-09 shows LESS behavioral color distortion than '
         'sub-08. Therefore, the sub-09 cone-shift magnitude estimate '
         '**SHOULD** be smaller than sub-08\'s under any behaviorally-'
         'consistent simulator/loss combination. Comparisons are made '
         '**within model class only** — `norm` (degrees, 2-comp) and `Δλ` '
         '(nm, Machado) are not directly comparable.'),
        '',
        '#### 2-component (norm in degrees)',
        '',
        '| simulator | loss | sub-08 norm | sub-09 norm | sub-09 < sub-08? |',
        '|---|---|---|---|---|',
    ]
    for sim in SIMULATORS:
        for loss in LOSSES:
            if (('2comp', sim, loss) not in all_results['08']['conditions']
                or ('2comp', sim, loss) not in all_results['09']['conditions']):
                md.append(f"| {sim} | {loss} | N/A | N/A | — (Task A pending) |")
                continue
            b08 = all_results['08']['conditions'][('2comp', sim, loss)]
            b09 = all_results['09']['conditions'][('2comp', sim, loss)]
            n08 = float(np.hypot(b08['bs'], b08['bc']))
            n09 = float(np.hypot(b09['bs'], b09['bc']))
            md.append(f"| {sim} | {loss} | {n08:.1f}° | {n09:.1f}° | "
                      f"{'YES' if n09 < n08 else 'NO'} |")

    md += [
        '',
        '#### Machado 1way (Δλ in nm)',
        '',
        '| simulator | loss | sub-08 Δλ | sub-09 Δλ | sub-09 < sub-08? |',
        '|---|---|---|---|---|',
    ]
    for sim in SIMULATORS:
        for loss in LOSSES:
            if (('machado', sim, loss) not in all_results['08']['conditions']
                or ('machado', sim, loss) not in all_results['09']['conditions']):
                md.append(f"| {sim} | {loss} | N/A | N/A | — |")
                continue
            b08 = all_results['08']['conditions'][('machado', sim, loss)]
            b09 = all_results['09']['conditions'][('machado', sim, loss)]
            dl08 = b08['delta_lambda_nm']
            dl09 = b09['delta_lambda_nm']
            md.append(f"| {sim} | {loss} | {dl08:.1f} nm | {dl09:.1f} nm | "
                      f"{'YES' if dl09 < dl08 else 'NO'} |")

    md += [
        '',
        '#### Interpretation',
        '',
        ('Conditions where sub-09\'s estimate is smaller than sub-08\'s are '
         '**descriptively** consistent with the behavioral evidence. This is '
         'a **convergent-validity sanity check**, not a model-selection rule '
         '(§0). Filter selection remains governed by per-subject behavioral '
         'PASS/FAIL per behav_validation.md §3.'),
        '',
        '## Files',
        '',
        '- `summary_8cond.csv`, `summary_8cond.json` — 16-row table.',
        '- `landscape_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).',
        '- `4col_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).',
        '- `vuln_hue_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).',
        '- `comparison_grid_sub-{08,09}.png` (2 files): 4-row × 4-col matrix '
        'of stacked 8-hue swatches.',
        '',
        '## Reproduce',
        '',
        '```bash',
        '# Task A: augment 2-comp wretrained landscapes with vuln_sim (~10 min each)',
        'python scripts/comparison_8cond_taskA.py 08',
        'python scripts/comparison_8cond_taskA.py 09',
        '# Task B: Machado wfixed landscapes (~10 s each)',
        'python scripts/comparison_8cond_taskB.py 08',
        'python scripts/comparison_8cond_taskB.py 09',
        '# Task C+D: argmins, per-condition figs, grid, CSV, README',
        'python scripts/comparison_8cond_taskCD.py',
        '```',
        '',
    ]
    readme_path = OUTDIR / 'README.md'
    with open(readme_path, 'w') as f:
        f.write('\n'.join(md))
    print(f'wrote {readme_path.name}')


if __name__ == '__main__':
    main()
