#!/usr/bin/env python3
"""
aphi_sanity_check.py — Reparameterize (β_s, β_c) → (A, φ) for inventory candidates.

The 2-component model δθ(θ) = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf) is mathematically
equivalent to a single 1st-harmonic shear A·cos(θ−φ).

  A   = √(β_s² + β_c² + 2·β_s·β_c·cos(90°−θ_conf))
  φ   = atan2(β_s·sin(90°) + β_c·sin(θ_conf),
              β_s·cos(90°) + β_c·cos(θ_conf))

Two candidates have the SAME shear iff both A and φ match. Different φ → different
distortion direction (different mechanism), even if A is similar.

This script:
  (1) Pulls (β_s, β_c) from the loss inventory CSV + Phase A canonical fits
  (2) Computes (A, φ) per subject × loss-variant (using θ_conf each was fit under)
  (3) Saves CSV + a 2-panel figure: (A, φ) polar scatter + per-CVD candidate table

Outputs:
  results/diagnostics/aphi_sanity/aphi_table.csv
  results/diagnostics/aphi_sanity/aphi_polar.png
"""

import csv
import json
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]  # phase5_filter_optimization
INVENTORY_CSV = ROOT / 'results' / 'inventory' / 'loss_inventory.csv'
CYCLE15_CSV = ROOT / 'results' / 'cycles' / 'cycle15_mwjaccard_cross.csv'
PHASE_A_DIR = ROOT / 'results' / 'fits' / 'phase_a_2component'
OUT_DIR = ROOT / 'results' / 'diagnostics' / 'aphi_sanity'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Per cycle9_signed_jaccard.py:245 — HC defaults to deutan; sub-10 defaults to deutan.
CVD_TYPE = {'08': 'deutan', '09': 'protan'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}

# β_s axis is FIXED at 90° (S-(L+M) cardinal direction).
THETA_S = 90.0


def aphi(beta_s: float, beta_c: float, theta_conf: float) -> tuple[float, float]:
    """Convert (β_s, β_c) into single-shear (A, φ).

    A·cos(θ−φ) ≡ β_s·cos(θ−THETA_S) + β_c·cos(θ−theta_conf)
    """
    s_rad = math.radians(THETA_S)
    c_rad = math.radians(theta_conf)
    x = beta_s * math.cos(s_rad) + beta_c * math.cos(c_rad)
    y = beta_s * math.sin(s_rad) + beta_c * math.sin(c_rad)
    A = math.hypot(x, y)
    phi = math.degrees(math.atan2(y, x)) % 360.0
    return A, phi


# ---------------------------------------------------------------------------
# 1) Load inventory rows
# ---------------------------------------------------------------------------

records: list[dict] = []


def _normalize_subj(subj: str) -> str:
    """Strip 'sub-' prefix so CVD_TYPE lookup works for both formats."""
    return subj.removeprefix('sub-')


def add_record(subj: str, role: str, source: str, bs: float, bc: float):
    """Append one (subj, source) candidate to records, computing (A, φ)."""
    key = _normalize_subj(subj)
    cvd = CVD_TYPE.get(key, 'deutan')  # HC + sub-10 → deutan default
    theta_conf = CONF_AXIS[cvd]
    A, phi = aphi(bs, bc, theta_conf)
    records.append({
        'subject': f'sub-{key}', 'role': role, 'source': source,
        'fit_family': cvd, 'theta_conf': theta_conf,
        'beta_s': bs, 'beta_c': bc,
        'A': A, 'phi': phi,
    })


# Cycle 15 winner (cycle15_opt2_v4mwj_v1lrank @ α=2, β=1) — both CVD distinct
with open(CYCLE15_CSV) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['variant'] != 'opt2_v4mwj_v1lrank':
            continue
        if row['alpha'] != '2.0' or row['beta'] != '1.0':
            continue
        add_record(row['subject'], row['role'], 'cycle15_opt2',
                   float(row['bs']), float(row['bc']))


# Loss inventory single-loss winners (mw_jaccard alone, l_rank, l_dir, etc.)
# Parse the CSV (which has different header than cycle15 csv)
INV_CSV = ROOT / 'results' / 'inventory' / 'loss_inventory.csv'
if INV_CSV.exists():
    with open(INV_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            loss_name = row.get('loss_variant') or row.get('variant') or ''
            roi = row.get('roi') or ''
            subj = row.get('subject') or ''
            role = row.get('role') or ''
            try:
                bs = float(row.get('beta_s', row.get('bs', 'nan')))
                bc = float(row.get('beta_c', row.get('bc', 'nan')))
            except ValueError:
                continue
            if not (np.isfinite(bs) and np.isfinite(bc)):
                continue
            if loss_name in ('mw_jaccard_loss', 'cycle12_cross_roi'):
                add_record(subj, role, f'{loss_name}_{roi}', bs, bc)


# Phase A canonical 2-component fits (CVD only)
for cvd_subj in ('08', '09'):
    p = PHASE_A_DIR / f'sub-{cvd_subj}_V4_2component.json'
    if not p.exists():
        continue
    d = json.loads(p.read_text())
    bs, bc = d['best_params']
    add_record(cvd_subj, 'CVD', 'phase_a_V4', float(bs), float(bc))


# ---------------------------------------------------------------------------
# 2) Save CSV
# ---------------------------------------------------------------------------

csv_path = OUT_DIR / 'aphi_table.csv'
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(
        f,
        fieldnames=['subject', 'role', 'source', 'fit_family', 'theta_conf',
                    'beta_s', 'beta_c', 'A', 'phi'],
    )
    w.writeheader()
    for r in records:
        w.writerow(r)
print(f'Wrote {len(records)} records → {csv_path}')


# ---------------------------------------------------------------------------
# 3) Two-panel figure: polar (A, φ) + (β_s, β_c) cartesian
# ---------------------------------------------------------------------------

# Style by role
def style(role: str, subject: str) -> dict:
    key = subject.removeprefix('sub-')
    if role == 'HC':
        return dict(color='#888888', marker='o', alpha=0.55, s=70)
    if key == '08':
        return dict(color='#d6391b', marker='*', alpha=0.95, s=240)
    if key == '09':
        return dict(color='#1f4e79', marker='*', alpha=0.95, s=240)
    if key == '10':
        return dict(color='#2e8b57', marker='D', alpha=0.85, s=110)
    return dict(color='black', marker='x', alpha=0.6, s=90)


fig = plt.figure(figsize=(13, 6))

# --- Panel 1: polar (A, φ) ---
ax1 = fig.add_subplot(121, projection='polar')
ax1.set_theta_zero_location('E')
ax1.set_theta_direction(1)
for r in records:
    s = style(r['role'], r['subject'])
    ax1.scatter(math.radians(r['phi']), r['A'], **s)
# Reference axes
ax1.axvline(math.radians(THETA_S), color='#d4a017', ls='--', lw=1, alpha=0.6,
            label='S-axis (90°)')
ax1.axvline(math.radians(CONF_AXIS['deutan']), color='#a6396b', ls=':', lw=1,
            alpha=0.7, label='deutan conf (150°)')
ax1.axvline(math.radians(CONF_AXIS['protan']), color='#3a7d44', ls=':', lw=1,
            alpha=0.7, label='protan conf (16°)')
ax1.set_rlabel_position(225)
ax1.set_rticks([20, 40, 60, 80])
ax1.set_title('(A, φ) — single-shear reparameterization\n'
              'A = magnitude (deg)   φ = shear axis direction',
              fontsize=10, pad=20)
ax1.legend(loc='upper left', bbox_to_anchor=(-0.18, 1.05), fontsize=8,
           framealpha=0.9)

# --- Panel 2: (β_s, β_c) cartesian ---
ax2 = fig.add_subplot(122)
for r in records:
    s = style(r['role'], r['subject'])
    ax2.scatter(r['beta_s'], r['beta_c'], **s)
    if r['role'] == 'CVD':
        ax2.annotate(f"{r['subject']}/{r['source'].split('_')[0]}",
                     (r['beta_s'], r['beta_c']), fontsize=7,
                     xytext=(4, 4), textcoords='offset points')
ax2.axhline(0, color='black', lw=0.5)
ax2.axvline(0, color='black', lw=0.5)
ax2.set_xlabel(r'$\beta_s$ (degrees, S-axis amplitude)')
ax2.set_ylabel(r'$\beta_c$ (degrees, confusion-axis amplitude)')
ax2.set_title('Native parameter space — (β_s, β_c)', fontsize=10)
ax2.grid(alpha=0.3)

# Custom legend for both panels
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#888888',
           label='HC (n=6)', markersize=8),
    Line2D([0], [0], marker='*', color='w', markerfacecolor='#d6391b',
           label='sub-08 deutan', markersize=14),
    Line2D([0], [0], marker='*', color='w', markerfacecolor='#1f4e79',
           label='sub-09 protan', markersize=14),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='#2e8b57',
           label='sub-10 (near-normal)', markersize=8),
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=8,
           framealpha=0.9)

fig.suptitle('2-Component sanity check — (β_s, β_c) reduces to single shear (A, φ)',
             fontsize=12, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.95])

fig_path = OUT_DIR / 'aphi_polar.png'
fig.savefig(fig_path, dpi=140, bbox_inches='tight')
print(f'Wrote figure → {fig_path}')

# ---------------------------------------------------------------------------
# 4) Summary table for CVD subjects (key for meeting)
# ---------------------------------------------------------------------------

print('\n=== CVD candidate (A, φ) summary ===')
print(f'{"subject":<8} {"source":<28} {"β_s":>6} {"β_c":>6} {"A":>6} {"φ":>6}')
for r in records:
    if r['role'] != 'CVD':
        continue
    print(f"{r['subject']:<8} {r['source']:<28} "
          f"{r['beta_s']:>6.1f} {r['beta_c']:>6.1f} "
          f"{r['A']:>6.1f} {r['phi']:>6.1f}")

print('\n=== HC distribution (φ in deg, A in deg) ===')
hc = [r for r in records if r['role'] == 'HC']
phi_arr = np.array([r['phi'] for r in hc])
A_arr = np.array([r['A'] for r in hc])
print(f'φ range: [{phi_arr.min():.1f}, {phi_arr.max():.1f}], '
      f'mean={phi_arr.mean():.1f}, std={phi_arr.std():.1f}')
print(f'A range: [{A_arr.min():.1f}, {A_arr.max():.1f}], '
      f'mean={A_arr.mean():.1f}, std={A_arr.std():.1f}')
