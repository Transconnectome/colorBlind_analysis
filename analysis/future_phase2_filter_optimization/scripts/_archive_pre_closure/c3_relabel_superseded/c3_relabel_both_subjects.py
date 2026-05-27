"""c3_relabel_both_subjects.py — Apply corrected labels to BOTH sub-08 and sub-09.

User directive (2026-05-15):
  1. No cherrypicking (constrained argmin not justified). Use loss global argmin only.
  2. Each loss term/weight must have neural/biological justification.
  3. Apply corrected labels to sub-09 too.
  4. Re-evaluate P2a under corrected labels for both. Revise loss accordingly.

This script:
  Step A. Translate sub-09 Korean reports to corrected vocab.
  Step B. Diagnose Option C global argmin P2a under corrected labels (both subjects).
  Step C. Per-term diagnosis: which loss terms contribute to mismatch?
  Step D. Propose revised loss with explicit justification per term.
  Step E. Find revised loss global argmin (no cherrypick).
"""
from __future__ import annotations
import sys
from pathlib import Path
import json
import math
import numpy as np

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))
ROOT = THIS.parent
OUT = ROOT / 'results' / 'c3_relabel'
OUT.mkdir(parents=True, exist_ok=True)

from c3_relabel_p2a import (
    HC_NAME_BINS_NEW, hc_name_new, HC_TARGET_NEW, HC_ADJ_NEW, hc_match,
    dt_2comp, forward, pre_image,
)

# ===========================================================================
# Step A: Sub-09 corrected SUB09_ORIG_HC_EQUIV (from Korean reports + new vocab)
# ===========================================================================
# Sub-09 protan ORIGINAL reports (raw_behav.md):
#   C1: 붉은색에 가까운 핑크 (red-leaning pink)
#   C2: 주황색 (orange)
#   C3: 올리브색 (olive)  ← matches actual render!
#   C4: 연두 + 민트색 (yellow-green + mint)
#   C5: 칙칙한 하늘색 (dull sky)
#   C6: 조금 덜 칙칙한 하늘색 (less dull sky)
#   C7: 파란색 (blue)
#   C8: 연보라+연분홍 (light violet+pink)

SUB08_ORIG_NEW = {
    0: 'pink', 45: 'green', 90: 'green', 135: 'yellow-green',
    180: 'olive', 225: 'sky-cyan', 270: 'sky-blue', 315: 'blue-violet',
}

SUB09_ORIG_NEW = {
    0: 'pink',                # 붉은색에 가까운 핑크 (closer to pink than red-orange)
    45: 'red-orange',         # 주황색 (matches actual)
    90: 'olive',              # 올리브색 (MATCHES actual)
    135: 'yellow-green',      # 연두+민트
    180: 'cyan',              # 칙칙한 하늘 (close to cyan)
    225: 'sky-cyan',          # 조금 덜 칙칙한 하늘
    270: 'sky-blue',          # 파란색 (matches)
    315: 'violet',            # 연보라+연분홍 (close to violet)
}

# Sub-09 protan axis (Stockman)
PROTAN_AXIS = 16.0


# ===========================================================================
# Step B: Option C P2a under corrected labels for BOTH subjects
# ===========================================================================
def p2a_corrected(bs, bc, axis, target_map):
    total = 0.0; ex = 0; details = []
    for theta in [0, 45, 90, 135, 180, 225, 270, 315]:
        tcvd = forward(float(theta), bs, bc, axis)
        pred = hc_name_new(tcvd)
        tgt = target_map[theta]
        s = hc_match(pred, tgt)
        total += s
        if pred == tgt: ex += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'pred': pred, 'tgt': tgt, 'score': s})
    return total/8.0, ex, details


print('=' * 95)
print('Step B: Option C P2a under CORRECTED labels (both subjects)')
print('=' * 95)
print(f'{"Filter":<28} {"P2a_08":<10} {"P2a_09":<10} {"avg":<8} {"min":<8} {"sum":<8}')
print('-' * 95)

candidates = [
    ('CURRENT sub-08 (40,+26)', 40, 26, 150.0, SUB08_ORIG_NEW, '08'),
    ('CURRENT sub-09 (12,-28)', 12, -28, 16.0, SUB09_ORIG_NEW, '09'),
]
for label, bs, bc, axis, tmap, sid in candidates:
    p, ex, det = p2a_corrected(bs, bc, axis, tmap)
    print(f'{label:<28} P2a={p:.3f} ({ex}/8)')
    for d in det:
        flag = '✓' if d['score'] == 1.0 else ('~' if d['score'] >= 0.5 else '✗')
        print(f'   c{[0,45,90,135,180,225,270,315].index(d["theta"])+1} '
              f'tcvd={d["tcvd"]:>5.1f}°  pred={d["pred"]:<14} tgt={d["tgt"]:<14} {flag} {d["score"]:.2f}')

# ===========================================================================
# Step C: Per-term diagnosis — Single-term + pairwise argmins
# ===========================================================================
print('\n' + '=' * 95)
print('Step C: Per-term diagnosis (single + pairwise loss term argmins)')
print('=' * 95)

# Load grids for both subjects
def load_grids(sid):
    if sid == '08':
        axis3 = 'results/axis_3way/sub-08_V4_Stockman150_landscape.json'
        tier2 = 'results/CANDIDATE/tier2_v4ccc_srm_rdm/sub-08_V4_V4CCC_SRMRDM_landscape.json'
        axis = 150.0; tmap = SUB08_ORIG_NEW
    else:
        axis3 = 'results/axis_3way/sub-09_V4_Stockman16_landscape.json'
        tier2 = 'results/CANDIDATE/tier2_v4ccc_srm_rdm/sub-09_V4_V4CCC_SRMRDM_landscape.json'
        axis = 16.0; tmap = SUB09_ORIG_NEW

    with open(ROOT / axis3) as f:
        d3 = json.load(f)
    with open(ROOT / tier2) as f:
        d2 = json.load(f)

    bs_step = d3['grid']['bs'][2]; bc_step = d3['grid']['bc'][2]
    bs_grid = np.arange(d3['grid']['bs'][0], d3['grid']['bs'][1]+0.001, bs_step)
    bc_grid = np.arange(d3['grid']['bc'][0], d3['grid']['bc'][1]+0.001, bc_step)
    N_bs, N_bc = len(bs_grid), len(bc_grid)

    L_topk = np.full((N_bs, N_bc), np.nan)
    L_tikh = np.full((N_bs, N_bc), np.nan)
    vuln_sim = np.full((N_bs, N_bc, 8), np.nan)
    for c in d3['cells']:
        i = int(round((c['bs'] - bs_grid[0]) / bs_step))
        j = int(round((c['bc'] - bc_grid[0]) / bc_step))
        L_topk[i, j] = c['l_topk']
        L_tikh[i, j] = c['tikh']
        vuln_sim[i, j] = c['vuln_sim']

    L_rdmV1 = np.full((N_bs, N_bc), np.nan)
    for c in d2:
        i = int(round((c['bs'] - bs_grid[0]) / bs_step))
        j = int(round((c['bc'] - bc_grid[0]) / bc_step))
        if 0 <= i < N_bs and 0 <= j < N_bc:
            L_rdmV1[i, j] = c['l_rdm_V1']

    V_obs = np.array(d3['vuln_cvd'])
    L_mse = np.mean((vuln_sim - V_obs[None, None, :])**2, axis=-1) / (np.var(V_obs)+1e-9)
    return {'bs_grid': bs_grid, 'bc_grid': bc_grid, 'V_obs': V_obs,
            'L_topk': L_topk, 'L_mse': L_mse, 'L_rdmV1': L_rdmV1, 'L_tikh': L_tikh,
            'axis': axis, 'tmap': tmap}


def argmin_with_weights(g, w_topk, w_mse, w_rdmV1, w_tikh):
    safe = lambda x: np.where(np.isnan(x), 1e6, x)
    L = (w_topk*safe(g['L_topk']) + w_mse*safe(g['L_mse']) +
         w_rdmV1*safe(g['L_rdmV1']) + w_tikh*safe(g['L_tikh']))
    idx = np.unravel_index(np.nanargmin(L), L.shape)
    bs = float(g['bs_grid'][idx[0]]); bc = float(g['bc_grid'][idx[1]])
    p, ex, _ = p2a_corrected(bs, bc, g['axis'], g['tmap'])
    return bs, bc, p, ex, float(L[idx])


g8 = load_grids('08')
g9 = load_grids('09')

# Single-term argmins
print('\n--- Single-term argmins (with tiny Tikh=0.1 for non-degenerate solution) ---\n')
print(f'{"Loss":<24} {"sub-08 argmin":<20} {"P2a_08":<10} {"sub-09 argmin":<20} {"P2a_09":<10}')
single_combos = [
    ('L_topk only',  1.0, 0.0, 0.0, 0.1),
    ('L_mse only',   0.0, 1.0, 0.0, 0.1),
    ('L_rdmV1 only', 0.0, 0.0, 1.0, 0.1),
    ('L_Tikh only',  0.0, 0.0, 0.0, 1.0),
]
for label, wt, wm, wr, wT in single_combos:
    b8s, b8c, p8, e8, _ = argmin_with_weights(g8, wt, wm, wr, wT)
    b9s, b9c, p9, e9, _ = argmin_with_weights(g9, wt, wm, wr, wT)
    print(f'{label:<24} ({b8s:>3.0f},{b8c:>+4.0f})           {p8:.3f} ({e8}/8)  '
          f'({b9s:>3.0f},{b9c:>+4.0f})           {p9:.3f} ({e9}/8)')

# Drop-one analysis
print('\n--- Drop-one analysis (Option C with one term zeroed) ---\n')
print(f'{"Loss":<24} {"sub-08 argmin":<20} {"P2a_08":<10} {"sub-09 argmin":<20} {"P2a_09":<10}')
drop_combos = [
    ('Option C ALL',    0.3, 0.3, 0.3, 3.0),
    ('drop L_topk',     0.0, 0.3, 0.3, 3.0),
    ('drop L_mse',      0.3, 0.0, 0.3, 3.0),
    ('drop L_rdmV1',    0.3, 0.3, 0.0, 3.0),
    ('drop L_Tikh',     0.3, 0.3, 0.3, 0.0),
]
for label, wt, wm, wr, wT in drop_combos:
    b8s, b8c, p8, e8, _ = argmin_with_weights(g8, wt, wm, wr, wT)
    b9s, b9c, p9, e9, _ = argmin_with_weights(g9, wt, wm, wr, wT)
    print(f'{label:<24} ({b8s:>3.0f},{b8c:>+4.0f})           {p8:.3f} ({e8}/8)  '
          f'({b9s:>3.0f},{b9c:>+4.0f})           {p9:.3f} ({e9}/8)')

# Tikh sweep
print('\n--- Tikh λ sweep with neural weights (0.3, 0.3, 0.3) ---\n')
print(f'{"λ":<6} {"sub-08 argmin":<20} {"P2a_08":<10} {"sub-09 argmin":<20} {"P2a_09":<10}')
for lam in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0]:
    b8s, b8c, p8, e8, _ = argmin_with_weights(g8, 0.3, 0.3, 0.3, lam)
    b9s, b9c, p9, e9, _ = argmin_with_weights(g9, 0.3, 0.3, 0.3, lam)
    print(f'{lam:<6.1f} ({b8s:>3.0f},{b8c:>+4.0f})           {p8:.3f} ({e8}/8)  '
          f'({b9s:>3.0f},{b9c:>+4.0f})           {p9:.3f} ({e9}/8)')

# Save state for next analysis
out = {
    'SUB08_ORIG_corrected_vocab': SUB08_ORIG_NEW,
    'SUB09_ORIG_corrected_vocab': SUB09_ORIG_NEW,
    'HC_TARGETS_corrected': HC_TARGET_NEW,
}
with open(OUT / 'both_subjects_corrected.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(f'\nWrote {OUT}/both_subjects_corrected.json')
