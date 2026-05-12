"""Regenerate F0-F6 PNGs with new STIM_LAB-based rendering.

Outputs to results/visualizations/sub08_PASS_comparison_STIM_LAB/.
Original Option C versions remain in sub08_PASS_comparison/ for comparison.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PHASE2 = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_PHASE2 / 'scripts'))

from visualize_phase3_preimage import render_figure as render_phase3
from visualize_filter_candidates import render_figure as render_vfc, SUBJECTS

OUT = _PHASE2 / 'results' / 'visualizations' / 'sub08_PASS_comparison_STIM_LAB'
OUT.mkdir(parents=True, exist_ok=True)

# F0 canonical: sub-08 2-comp (38, -14) — uses visualize_filter_candidates
SUBJECTS['08']['2comp'] = {'beta_s': 38.0, 'beta_c': -14.0}
print('F0 canonical (38, -14) via visualize_filter_candidates...')
render_vfc('2comp', '08', OUT / 'F0_canonical_38_-14_STIM_LAB.png')

# F4 cycle15opt2: sub-08 (68, -38) — visualize_filter_candidates
SUBJECTS['08']['2comp'] = {'beta_s': 68.0, 'beta_c': -38.0}
print('F4 cycle15opt2 (68, -38) via visualize_filter_candidates...')
render_vfc('2comp', '08', OUT / 'F4_cycle15opt2_68_-38_STIM_LAB.png')

# F6 cycle14: sub-08 (58, -36) — visualize_filter_candidates
SUBJECTS['08']['2comp'] = {'beta_s': 58.0, 'beta_c': -36.0}
print('F6 cycle14 (58, -36) via visualize_filter_candidates...')
render_vfc('2comp', '08', OUT / 'F6_cycle14_58_-36_STIM_LAB.png')

# F1, F2, F3 use visualize_phase3_preimage (CELLS dict format)
F_CELLS = [
    ('F1_V1V4avg_19_+3.5',
     {'subj': '08', 'cvd': 'deutan', 'roi_label': 'V1+V4 avg',
      'beta_s': 19.0, 'beta_c': 3.5, 'dlam_anchor': 1.5,
      'note': 'V1+V4 avg, cycle10d'}),
    ('F2_V4only_38_+7',
     {'subj': '08', 'cvd': 'deutan', 'roi_label': 'V4-only',
      'beta_s': 38.0, 'beta_c': 7.0, 'dlam_anchor': 1.5,
      'note': 'V4-only cycle10d argmin (β_c sign opposite of canonical)'}),
    ('F3_crossROI_68_-38',
     {'subj': '08', 'cvd': 'deutan', 'roi_label': 'Cross-ROI cycle12',
      'beta_s': 68.0, 'beta_c': -38.0, 'dlam_anchor': 1.5,
      'note': 'Cross-ROI loss (cycle12, α=β=1)'}),
]

for fname, cell in F_CELLS:
    print(f'{fname} via visualize_phase3_preimage...')
    render_phase3(cell, OUT / f'{fname}_STIM_LAB.png')

print(f'\nDone. Output: {OUT}')
