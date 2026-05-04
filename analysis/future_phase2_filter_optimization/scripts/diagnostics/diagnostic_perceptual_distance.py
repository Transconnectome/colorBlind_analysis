#!/usr/bin/env python3
"""
diagnostic_perceptual_distance.py — Compare candidate filters via
DeltaE_OKLab between HC reference perception and CVD-filter perception.

Diagnostic only — does NOT run any new fit. For each candidate (beta_s, beta_c),
computes 8-color pre-image and measures the OKLab distance between:
  HC_ref_perception_i  = render CIELab(target_i, L*=75, C*=40)
  CVD_filter_perception_i = cvd_response_lab(pre_image_i, cvd_type, dlam_cvd)

Lower mean DeltaE = filter perceptually closer to HC reference.
Per-color DeltaE identifies color-local failure (e.g., c2 orange, c8 magenta).

Purpose: pre-register expected behavioral ranking BEFORE sub-08 results return.
"""

import sys
from pathlib import Path
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

from visualize_filter_candidates import (
    cvd_response_lab, find_preimage, L_STAR, CHROMA, SUBJECTS,
)

# Ottosson 2020 OKLab matrices (XYZ-based path)
M_XYZ2LMS = np.array([
    [0.8189330101, 0.3618667424, -0.1288597137],
    [0.0329845436, 0.9293118715, 0.0361456387],
    [0.0482003018, 0.2643662691, 0.6338517070],
])
M_LMS2OKLAB = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
])
D65_XYZ = np.array([0.95047, 1.0, 1.08883])


def cielab_to_xyz(L, a, b):
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    delta = 6.0 / 29.0
    out = []
    for f in (fx, fy, fz):
        if f > delta:
            out.append(f ** 3)
        else:
            out.append((f - 16.0 / 116.0) * 3 * delta ** 2)
    return np.array(out) * D65_XYZ


def cielab_to_oklab(L, a, b):
    xyz = cielab_to_xyz(L, a, b)
    lms = M_XYZ2LMS @ xyz
    lms_prime = np.sign(lms) * np.cbrt(np.abs(lms))
    return M_LMS2OKLAB @ lms_prime


def delta_e_oklab(lab1, lab2):
    ok1 = cielab_to_oklab(*lab1)
    ok2 = cielab_to_oklab(*lab2)
    return float(np.linalg.norm(ok1 - ok2))


def delta_e_oklab_chroma(lab1, lab2):
    """Chromatic-only OKLab distance (a, b only, L excluded).

    Removes Machado luminance shift confound — measures hue+saturation
    distance only, which is what filter (β_s, β_c) actually manipulates.
    """
    ok1 = cielab_to_oklab(*lab1)
    ok2 = cielab_to_oklab(*lab2)
    return float(np.linalg.norm(ok1[1:] - ok2[1:]))


TARGETS = [0, 45, 90, 135, 180, 225, 270, 315]
COLORS = ['c1 red', 'c2 orange', 'c3 yellow', 'c4 yel-grn',
          'c5 cyan', 'c6 blue-cy', 'c7 blue', 'c8 magenta']


def evaluate(name, params, cvd, dlam):
    print(f'\n=== {name} ===')
    delta_es = []
    pre_images = []
    for i, target in enumerate(TARGETS):
        rad = np.deg2rad(target)
        hc_lab = (L_STAR, CHROMA * np.cos(rad), CHROMA * np.sin(rad))

        theta_pre, _ = find_preimage(target, '2comp', cvd, params)
        cvd_lab = cvd_response_lab(theta_pre, cvd, dlam)
        de_full = delta_e_oklab(hc_lab, tuple(cvd_lab))
        de_chroma = delta_e_oklab_chroma(hc_lab, tuple(cvd_lab))
        delta_es.append((de_full, de_chroma))
        pre_images.append(theta_pre)
        print(f'  {COLORS[i]:>11s}: target={target:>3}°  '
              f'pre={theta_pre:>6.1f}°  DE_full={de_full:.3f}  '
              f'DE_chroma={de_chroma:.3f}')

    full_arr = np.array([d[0] for d in delta_es])
    chroma_arr = np.array([d[1] for d in delta_es])
    mean_full = float(np.mean(full_arr))
    mean_chroma = float(np.mean(chroma_arr))
    max_full_i = int(np.argmax(full_arr))
    max_chroma_i = int(np.argmax(chroma_arr))
    print(f'  Mean DE_full   = {mean_full:.3f} | Mean DE_chroma = {mean_chroma:.3f}')
    print(f'  Worst full     = {COLORS[max_full_i]} ({full_arr[max_full_i]:.3f})')
    print(f'  Worst chroma   = {COLORS[max_chroma_i]} ({chroma_arr[max_chroma_i]:.3f})')
    return {'per_color_full': full_arr.tolist(),
            'per_color_chroma': chroma_arr.tolist(),
            'pre_images': pre_images,
            'mean_full': mean_full, 'mean_chroma': mean_chroma,
            'worst_full': COLORS[max_full_i],
            'worst_chroma': COLORS[max_chroma_i]}


print('=' * 70)
print('SUB-08 DEUTAN CANDIDATES')
print('=' * 70)

dlam_08 = float(SUBJECTS['08']['machado']['delta_lambda'])
print(f'dlam_cvd (Machado fit) = {dlam_08} nm')
print(f'L*={L_STAR}, C*={CHROMA}')

CANDS_08 = {
    'V4 §3 canonical (38, -14) [behav PASS]':
        {'beta_s': 38.0, 'beta_c': -14.0},
    'V4 cycle10d (38, +7) [under behav test]':
        {'beta_s': 38.0, 'beta_c': 7.0},
    'V1+V4 avg (19, +3.5) [under behav test]':
        {'beta_s': 19.0, 'beta_c': 3.5},
    'Cross-ROI loss cycle12 (68, -38) [under behav test]':
        {'beta_s': 68.0, 'beta_c': -38.0},
    'Identity (no filter, baseline)':
        {'beta_s': 0.0, 'beta_c': 0.0},
}

results_08 = {name: evaluate(name, p, 'deutan', dlam_08)
              for name, p in CANDS_08.items()}

print('\n=== SUB-08 RANKING by DE_full (luminance + chroma) ===')
for name, r in sorted(results_08.items(), key=lambda kv: kv[1]['mean_full']):
    print(f'  DE_full={r["mean_full"]:.3f}  worst={r["worst_full"]:>11s}  | {name}')
print('\n=== SUB-08 RANKING by DE_chroma (a, b only — hue+saturation) ===')
for name, r in sorted(results_08.items(), key=lambda kv: kv[1]['mean_chroma']):
    print(f'  DE_chroma={r["mean_chroma"]:.3f}  worst={r["worst_chroma"]:>11s}  | {name}')

print('\n' + '=' * 70)
print('SUB-09 PROTAN CANDIDATES')
print('=' * 70)

dlam_09 = float(SUBJECTS['09']['machado']['delta_lambda'])
print(f'dlam_cvd (Machado fit) = {dlam_09} nm')

CANDS_09 = {
    'V4 LOCO best (6, -22) [pending behav]':
        {'beta_s': 6.0, 'beta_c': -22.0},
    'V4 (0, 0) degenerate [LOCO l_fit]':
        {'beta_s': 0.0, 'beta_c': 0.0},
    'V1+V4 avg (30.5, +12)':
        {'beta_s': 30.5, 'beta_c': 12.0},
    'Cross-ROI loss cycle12 (30, +26)':
        {'beta_s': 30.0, 'beta_c': 26.0},
    'Identity (no filter, baseline)':
        {'beta_s': 0.0, 'beta_c': 0.0},
}

results_09 = {name: evaluate(name, p, 'protan', dlam_09)
              for name, p in CANDS_09.items()}

print('\n=== SUB-09 RANKING by DE_full (luminance + chroma) ===')
for name, r in sorted(results_09.items(), key=lambda kv: kv[1]['mean_full']):
    print(f'  DE_full={r["mean_full"]:.3f}  worst={r["worst_full"]:>11s}  | {name}')
print('\n=== SUB-09 RANKING by DE_chroma (a, b only — hue+saturation) ===')
for name, r in sorted(results_09.items(), key=lambda kv: kv[1]['mean_chroma']):
    print(f'  DE_chroma={r["mean_chroma"]:.3f}  worst={r["worst_chroma"]:>11s}  | {name}')

print('\n' + '=' * 70)
print('PRE-REGISTERED PREDICTION (before behavioral results return):')
print('  If mean DE is monotonic with behavioral PASS judgment,')
print('  the lowest-DE candidate should rank highest behaviorally.')
print('  Mismatch -> OKLab proxy is weak; per-color DE may still inform.')
print('=' * 70)
