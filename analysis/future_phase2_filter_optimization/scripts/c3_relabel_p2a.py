"""c3_relabel_p2a.py — Re-evaluate P2a under CORRECTED labels.

Corrected HC_NAME_BINS based on actual STIM_LAB rendering:
  pink (-22.5, 22.5), red-orange (22.5, 67.5), olive (67.5, 112.5),
  green (112.5, 157.5), cyan (157.5, 202.5), sky-cyan (202.5, 247.5),
  sky-blue (247.5, 292.5), violet (292.5, 337.5)

Corrected SUB08_ORIGINAL_HC_EQUIV (from raw_behav.md → new vocab):
  0:pink, 45:green (deutan miss), 90:green (deutan miss), 135:yellow-green,
  180:olive (아이보리 → desaturated yellow-brown),
  225:sky-cyan (탁한 하늘), 270:sky-blue (파랑), 315:blue-violet (진한 파랑)

Strategy: re-evaluate CURRENT (40, +26) and search grid for new argmin
preserving the same Option C composite loss (NO loss formulation change).
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

# ===========================================================================
# Corrected labels
# ===========================================================================
HC_NAME_BINS_NEW = [
    (-22.5,  22.5, 'pink'),
    ( 22.5,  67.5, 'red-orange'),
    ( 67.5, 112.5, 'olive'),
    (112.5, 157.5, 'green'),
    (157.5, 202.5, 'cyan'),
    (202.5, 247.5, 'sky-cyan'),
    (247.5, 292.5, 'sky-blue'),
    (292.5, 337.5, 'violet'),
    (337.5, 360.0, 'pink'),  # wrap
]

def hc_name_new(theta):
    t = float(theta) % 360.0
    if t < 0: t += 360
    if t >= 337.5 or t < 22.5: return 'pink'
    for lo, hi, name in HC_NAME_BINS_NEW:
        if lo <= t < hi:
            return name
    return 'pink'

# Sub-08 perceives originals as (Korean reports translated to corrected vocab)
SUB08_ORIG_NEW = {
    0:   'pink',           # 핑크
    45:  'green',          # 초록 (deutan miss — orange/red-orange → green)
    90:  'green',          # 초록 (deutan miss — olive → green)
    135: 'yellow-green',   # 연두 (close to green)
    180: 'olive',          # 아이보리 (cyan → olive/warm desaturated) MISS
    225: 'sky-cyan',       # 탁한 하늘 (correct)
    270: 'sky-blue',       # 파랑 (correct!)
    315: 'blue-violet',    # 진한 파랑 (violet → blue-violet, mild deutan miss)
}

# HC ideal: actual rendered color at each θ
HC_TARGET_NEW = {
    0: 'pink', 45: 'red-orange', 90: 'olive', 135: 'green',
    180: 'cyan', 225: 'sky-cyan', 270: 'sky-blue', 315: 'violet',
}

# Adjacency for partial credit (under new vocab)
HC_ADJ_NEW = {
    'pink':        {'red-orange': 0.6, 'violet': 0.5},
    'red-orange':  {'pink': 0.6, 'olive': 0.6, 'orange': 0.7},
    'olive':       {'red-orange': 0.6, 'green': 0.7, 'yellow-green': 0.8},
    'yellow-green':{'olive': 0.8, 'green': 0.8},
    'green':       {'olive': 0.7, 'yellow-green': 0.8, 'cyan': 0.4},
    'cyan':        {'green': 0.4, 'sky-cyan': 0.8, 'olive': 0.3},
    'sky-cyan':    {'cyan': 0.8, 'sky-blue': 0.7},
    'sky-blue':    {'sky-cyan': 0.7, 'violet': 0.5, 'blue-violet': 0.8},
    'blue-violet': {'sky-blue': 0.8, 'violet': 0.7},
    'violet':      {'sky-blue': 0.5, 'blue-violet': 0.7, 'pink': 0.5},
}

def hc_match(pred, tgt):
    if pred == tgt: return 1.0
    return HC_ADJ_NEW.get(pred, {}).get(tgt, 0.0)

# ===========================================================================
# Forward model (raw-θ, matches p2amax_option_C generator)
# ===========================================================================
def dt_2comp(theta, bs, bc, axis=150.0):
    th = math.radians(theta)
    return bs * math.cos(th - math.pi/2) + bc * math.cos(th - math.radians(axis))

def forward(theta, bs, bc, axis=150.0):
    return (theta + dt_2comp(theta, bs, bc, axis)) % 360.0

def pre_image(target, bs, bc, axis=150.0, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd = (grid + np.array([dt_2comp(t, bs, bc, axis) for t in grid])) % 360.0
    diff = (fwd - target + 180) % 360 - 180
    return float(grid[np.argmin(np.abs(diff))])


# ===========================================================================
# P2a under corrected labels
# ===========================================================================
def p2a_corrected(bs, bc, target_map):
    total = 0.0; ex = 0; details = []
    for theta in [0, 45, 90, 135, 180, 225, 270, 315]:
        tcvd = forward(float(theta), bs, bc)
        pred = hc_name_new(tcvd)
        tgt = target_map[theta]
        s = hc_match(pred, tgt)
        total += s
        if pred == tgt: ex += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'pred': pred, 'tgt': tgt, 'score': s})
    return total/8.0, ex, details


# ===========================================================================
# Run analysis
# ===========================================================================
print('=' * 95)
print('P2a evaluation under CORRECTED labels (HC bins + SUB08_ORIG vocab)')
print('=' * 95)

cands = [
    ('CURRENT (40,+26)', 40,  26),
    ('Hybrid (16,+40)',  16,  40),
    ('Probe (0, -12)',    0, -12),
    ('Probe (10,-22)',   10, -22),
    ('Probe (12,-28)',   12, -28),
    ('Probe (20,-30)',   20, -30),
    ('Probe (30,-30)',   30, -30),
    ('Probe (40,-26)',   40, -26),  # mirror of CURRENT
    ('ZONE_C (44,-40)',  44, -40),
]

print(f'{"Candidate":<22} {"P2a":<7} {"exact":<7} per-color matches')
print('-' * 95)
for label, bs, bc in cands:
    p, ex, det = p2a_corrected(bs, bc, SUB08_ORIG_NEW)
    matches = ' '.join([f'c{i+1}:{d["pred"][:5]}/{d["tgt"][:5]}' for i, d in enumerate(det)])
    print(f'{label:<22} {p:.3f}   {ex}/8     {matches}')

# Now grid search for global argmin under new labels
print('\n\n=== Grid search: global argmin of P2a under corrected SUB08_ORIG vocab ===\n')
best_p2a = -1
best_cell = None
results = []
for bs in np.arange(0, 51, 2):
    for bc in np.arange(-60, 61, 2):
        p, ex, _ = p2a_corrected(bs, bc, SUB08_ORIG_NEW)
        results.append({'bs': float(bs), 'bc': float(bc), 'p2a': p, 'exact': ex})
        if p > best_p2a:
            best_p2a = p
            best_cell = (bs, bc, ex)

print(f'Best P2a in grid: ({best_cell[0]:.0f}, {best_cell[1]:+.0f})  P2a={best_p2a:.3f} ({best_cell[2]}/8)')

# Top 20 cells
results.sort(key=lambda r: (-r['p2a'], -r['exact']))
print(f'\nTop 20 P2a cells:')
for r in results[:20]:
    print(f'  ({r["bs"]:>3.0f}, {r["bc"]:>+4.0f})  P2a={r["p2a"]:.3f}  exact={r["exact"]}/8')

# Now load Option C composite landscape and find best cell that BOTH:
#  - has good P2a under corrected labels
#  - has low ΔL from Option C composite argmin
print('\n\n=== Cross-reference with Option C composite landscape ===\n')
import json as _json
with open(ROOT / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json') as f:
    d3 = _json.load(f)
# Get composite L per cell — need tier2 too for L_rdmV1
with open(ROOT / 'results/CANDIDATE/tier2_v4ccc_srm_rdm/sub-08_V4_V4CCC_SRMRDM_landscape.json') as f:
    d2 = _json.load(f)

bs_step = d3['grid']['bs'][2]; bc_step = d3['grid']['bc'][2]
bs_grid = np.arange(d3['grid']['bs'][0], d3['grid']['bs'][1]+0.001, bs_step)
bc_grid = np.arange(d3['grid']['bc'][0], d3['grid']['bc'][1]+0.001, bc_step)
N_bs, N_bc = len(bs_grid), len(bc_grid)

l_topk = np.full((N_bs, N_bc), np.nan)
l_tikh = np.full((N_bs, N_bc), np.nan)
vuln_sim = np.full((N_bs, N_bc, 8), np.nan)
for c in d3['cells']:
    i = int(round((c['bs'] - bs_grid[0]) / bs_step))
    j = int(round((c['bc'] - bc_grid[0]) / bc_step))
    l_topk[i, j] = c['l_topk']
    l_tikh[i, j] = c['tikh']
    vuln_sim[i, j] = c['vuln_sim']

l_rdmV1 = np.full((N_bs, N_bc), np.nan)
for c in d2:
    i = int(round((c['bs'] - bs_grid[0]) / bs_step))
    j = int(round((c['bc'] - bc_grid[0]) / bc_step))
    if 0 <= i < N_bs and 0 <= j < N_bc:
        l_rdmV1[i, j] = c['l_rdm_V1']

V_obs = np.array(d3['vuln_cvd'])
L_mse = np.mean((vuln_sim - V_obs[None, None, :])**2, axis=-1) / (np.var(V_obs)+1e-9)

# Option C composite
safe = lambda x: np.where(np.isnan(x), 1e6, x)
L_C = 0.3*safe(l_topk) + 0.3*safe(L_mse) + 0.3*safe(l_rdmV1) + 3.0*safe(l_tikh)
L_REF = float(np.nanmin(L_C))
idx_ref = np.unravel_index(np.nanargmin(L_C), L_C.shape)
print(f'Option C global argmin: ({bs_grid[idx_ref[0]]:.0f}, {bc_grid[idx_ref[1]]:+.0f}), L={L_REF:.3f}')

# For top-P2a cells, look up L
print(f'\nTop-P2a cells with their Option C composite L:')
print(f'{"(bs, bc)":<14} {"P2a":<7} {"exact":<7} {"L_optC":<8} {"ΔL":<8}')
seen = set()
for r in results[:30]:
    key = (r['bs'], r['bc'])
    if key in seen: continue
    seen.add(key)
    i = int(round((r['bs'] - bs_grid[0]) / bs_step))
    j = int(round((r['bc'] - bc_grid[0]) / bc_step))
    if 0 <= i < N_bs and 0 <= j < N_bc:
        L = float(L_C[i, j])
        dL = L - L_REF
        print(f'({r["bs"]:>3.0f}, {r["bc"]:>+4.0f})  {r["p2a"]:.3f}  {r["exact"]}/8     {L:.3f}   {dL:+.3f}')

# Output
data = {
    'corrected_HC_NAME_BINS': HC_NAME_BINS_NEW,
    'corrected_SUB08_ORIG': SUB08_ORIG_NEW,
    'corrected_HC_TARGETS': HC_TARGET_NEW,
    'top_p2a_cells': results[:30],
    'option_C_argmin_global': {
        'bs': float(bs_grid[idx_ref[0]]),
        'bc': float(bc_grid[idx_ref[1]]),
        'L': L_REF,
        'p2a_under_corrected_labels': p2a_corrected(float(bs_grid[idx_ref[0]]),
                                                     float(bc_grid[idx_ref[1]]),
                                                     SUB08_ORIG_NEW)[0],
    },
}
with open(OUT / 'p2a_corrected_labels.json', 'w') as f:
    json.dump(data, f, indent=2, default=str, ensure_ascii=False)
print(f'\nWrote {OUT}/p2a_corrected_labels.json')
