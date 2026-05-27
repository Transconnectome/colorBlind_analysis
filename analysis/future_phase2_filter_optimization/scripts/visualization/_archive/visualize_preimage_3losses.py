#!/usr/bin/env python3
"""visualize_preimage_3losses.py — pre-image figures for 3 fit-losses.

Generates 6 figures (3 losses × 2 subjects) using the existing 2-component
forward + pre-image pipeline from visualize_filter_candidates.

Output: results/visualizations/PREIMAGE/{setting}_{participant}.png
  settings: canonical, cycle14, cycle15
  participants: sub-08, sub-09

All 3 settings use the same 2-comp forward model with different (β_s, β_c)
parameters reflecting the argmin of each fit-loss formulation:
  canonical: hV4 LOCO ρ argmax (canonical L_fit, sub-08 §3 PASS source)
  cycle14:   2·L_mwJ(V4) + 1·L_rdm(V1) + 0.2·Tikh, α=2 β=1
  cycle15:   2·L_mwJ(V4) + 1·(1−ρ_LOCO_V1) + 0.2·Tikh, α=2 β=1
"""
from __future__ import annotations
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
# Add scripts/ (parent) FIRST so vfc's machado_simulator import works.
# vfc's own path-setup skips this if visualization/ is already in sys.path.
_SCRIPTS_DIR = _SCRIPT_DIR.parent
for _p in (str(_SCRIPTS_DIR), str(_SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import visualize_filter_candidates as vfc

ROOT = _SCRIPT_DIR.parent.parent
OUTDIR = ROOT / 'results' / 'visualizations' / 'PREIMAGE'
OUTDIR.mkdir(parents=True, exist_ok=True)

SETTINGS = {
    'canonical': {
        'title': 'Canonical L_fit  (hV4 LOCO ρ argmax — sub-08 §3 PASS source)',
        '08': {'beta_s': 38.0, 'beta_c': -14.0},
        '09': {'beta_s':  6.0, 'beta_c': -22.0},
    },
    'cycle14': {
        'title': 'Cycle 14  (2·L_mwJ(V4) + 1·L_rdm(V1) + 0.2·Tikh)',
        '08': {'beta_s': 58.0, 'beta_c': -36.0},
        '09': {'beta_s': 44.0, 'beta_c': 54.0},
    },
    'cycle15': {
        'title': 'Cycle 15 opt2  (2·L_mwJ(V4) + 1·(1−ρ_LOCO_V1) + 0.2·Tikh)',
        '08': {'beta_s': 68.0, 'beta_c': -38.0},
        '09': {'beta_s': 44.0, 'beta_c': 54.0},
    },
}

# Save originals so we can restore
_ORIG_TITLE = vfc.MODEL_TITLE['2comp']
_ORIG_PARAMS = {s: dict(vfc.SUBJECTS[s]['2comp']) for s in ('08', '09')}


def render_setting(setting_key: str) -> None:
    s = SETTINGS[setting_key]
    vfc.MODEL_TITLE['2comp'] = s['title']
    for subj in ('08', '09'):
        vfc.SUBJECTS[subj]['2comp'] = dict(s[subj])
        out = OUTDIR / f'{setting_key}_sub-{subj}.png'
        vfc.render_figure('2comp', subj, out)


def main() -> None:
    print(f'Writing pre-image figures to: {OUTDIR}')
    try:
        for key in ('canonical', 'cycle14', 'cycle15'):
            print(f'\n--- {key} ---')
            render_setting(key)
    finally:
        # Restore globals
        vfc.MODEL_TITLE['2comp'] = _ORIG_TITLE
        for s, p in _ORIG_PARAMS.items():
            vfc.SUBJECTS[s]['2comp'] = p

    # README
    with (OUTDIR / 'README.md').open('w') as f:
        f.write('# Pre-image visualizations — 3 fit-losses × 2 subjects\n\n')
        f.write('All figures use the **2-component forward model** with '
                '(β_s, β_c) from each fit-loss argmin.\n\n')
        f.write('| File | Setting | sub-08 (β_s, β_c) | sub-09 (β_s, β_c) |\n')
        f.write('|---|---|---|---|\n')
        for key, s in SETTINGS.items():
            p8 = s['08']; p9 = s['09']
            f.write(
                f"| `{key}_sub-XX.png` | {s['title']} | "
                f"({p8['beta_s']:.0f}°, {p8['beta_c']:+.0f}°) | "
                f"({p9['beta_s']:.0f}°, {p9['beta_c']:+.0f}°) |\n"
            )
        f.write('\n## Column legend\n')
        f.write('1. Original — stimulus θ on the L*=75, C*=40 ring\n')
        f.write('2. CVD perceives — forward pass at θ\n')
        f.write('3. Filtered — pre-image θ_pre such that CVD(θ_pre) ≈ θ\n')
        f.write('4. CVD(Filtered) — acid test (should match Col 1 if invertible)\n')
    print(f'\n→ {OUTDIR / "README.md"}')
    print('Done.')


if __name__ == '__main__':
    main()
