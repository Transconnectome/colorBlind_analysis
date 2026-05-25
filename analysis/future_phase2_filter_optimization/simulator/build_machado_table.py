"""Precompute Machado δθ lookup over (hue, Δλ, family) for the HTML simulator.

The HTML simulator interpolates this table to evaluate R+C:
  δθ_RC(θ; Δλ, g, family) = (2 - g) · δθ_Machado(θ; Δλ, family)

Output: machado_table.json next to this file. Structure:
  {
    "hue_grid_deg": [0, 1, ..., 359],
    "delta_lambda_grid_nm": [0, 0.5, 1.0, ..., 30.0],
    "protan": [[δθ at each hue for Δλ_0], [Δλ_1], ...],  # shape (61, 360)
    "deutan": same,
    "stim_lab": {color_1: [L,a,b], ...}
  }
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

_THIS = Path(__file__).resolve().parent
_SCRIPTS = _THIS.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS))

from machado_simulator import machado_shifted_hue_at  # noqa: E402
from stim_lab_render import STIM_LAB  # noqa: E402


HUE_GRID = np.arange(0, 360, 1, dtype=float)         # 360 hues
DL_GRID = np.arange(0.0, 30.0 + 1e-9, 0.5)           # 61 Δλ values
FAMILIES = ('protan', 'deutan')


def build_table() -> dict:
    out = {
        'hue_grid_deg': HUE_GRID.tolist(),
        'delta_lambda_grid_nm': DL_GRID.tolist(),
        'stim_lab': STIM_LAB,
    }
    for fam in FAMILIES:
        print(f'computing {fam} ...')
        grid = np.zeros((len(DL_GRID), len(HUE_GRID)), dtype=float)
        for i, dl in enumerate(DL_GRID):
            _, _, dtheta = machado_shifted_hue_at(float(dl), fam, HUE_GRID)
            grid[i] = dtheta
            if i % 10 == 0:
                print(f'  Δλ={dl:5.1f} nm   max|δθ|={np.max(np.abs(dtheta)):6.2f}°')
        out[fam] = [[round(float(v), 4) for v in row] for row in grid]
    return out


def main():
    table = build_table()
    out_path = _THIS / 'machado_table.json'
    with open(out_path, 'w') as f:
        json.dump(table, f)
    size_kb = out_path.stat().st_size / 1024
    print(f'\nwrote {out_path}  ({size_kb:.1f} KB)')


if __name__ == '__main__':
    main()
