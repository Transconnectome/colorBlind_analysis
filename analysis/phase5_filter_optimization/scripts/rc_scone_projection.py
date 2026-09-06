#!/usr/bin/env python
"""
Degrees of freedom of the retinal-family (R+C) model versus the 2-component model.

The R+C model is delta_theta_RC(theta; g) = (2 - g) * delta_theta_Mach(theta),
so a single gain rescales one fixed per-hue profile. The 2-component model is
delta_theta(theta) = beta_s cos(theta - 90) + beta_c cos(theta - theta_conf),
with two independently fitted amplitudes.

This script projects the Machado profile onto the 2-component basis by ordinary
least squares and reports, per subtype and per cone-shift anchor:

  beta_s, beta_c   least-squares amplitudes of the Machado profile in that basis
  ratio            |beta_s / beta_c|, the S-cone-axis content the gain cannot
                   vary independently of the confusion-axis content
  frac_ss          fraction of the profile's sum of squares the basis captures
                   (uncentred, since the basis carries no intercept)

Supports Supplementary S11 (app:retinal_family) and Results (the statement that
the retinal family fixes the relative weight of the two terms).

Usage:  python rc_scone_projection.py
Writes: results/rc_scone_projection.json
"""
import sys
import json
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rc_1dof import delta_machado

HUES = np.arange(0.0, 360.0, 45.0)          # nominal Lab hue angles of the 8 stimuli
THETA_CONF = {'deutan': 150.0, 'protan': 16.0}
ANCHORS = {'deutan': [6.0, 6.5, 8.0], 'protan': [1.5, 3.0, 10.0]}
OUT = Path(__file__).resolve().parents[1] / 'results' / 'rc_scone_projection.json'


def design(theta_conf):
    """8 x 2 basis [cos(theta - 90), cos(theta - theta_conf)]."""
    rad = np.deg2rad(HUES)
    return np.column_stack([np.cos(rad - np.pi / 2),
                            np.cos(rad - np.deg2rad(theta_conf))])


def project(delta, theta_conf):
    X = design(theta_conf)
    beta, *_ = np.linalg.lstsq(X, delta, rcond=None)
    resid = delta - X @ beta
    ss_tot = float(np.sum(delta ** 2))
    frac_ss = float(1.0 - np.sum(resid ** 2) / ss_tot) if ss_tot > 0 else float('nan')
    return {
        'beta_s': float(beta[0]),
        'beta_c': float(beta[1]),
        'ratio_abs': float(abs(beta[0] / beta[1])) if beta[1] != 0 else float('inf'),
        'rms_delta': float(np.sqrt(np.mean(delta ** 2))),
        'rms_residual': float(np.sqrt(np.mean(resid ** 2))),
        'frac_ss': frac_ss,
        'delta_machado': [float(v) for v in delta],
    }


def main():
    out = {
        'description': 'Least-squares projection of the Machado per-hue shift '
                       'profile onto the 2-component basis.',
        'hues_deg': [float(h) for h in HUES],
        'theta_conf_deg': THETA_CONF,
        'subtypes': {},
    }
    for family, anchors in ANCHORS.items():
        out['subtypes'][family] = {}
        for dl in anchors:
            delta = delta_machado(dl, family)
            out['subtypes'][family][f'{dl:g}nm'] = project(delta, THETA_CONF[family])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))

    print(f"{'subtype':<8}{'dl(nm)':>7}{'beta_s':>9}{'beta_c':>9}{'|bs/bc|':>9}{'fracSS':>8}")
    for family in ANCHORS:
        for key, r in out['subtypes'][family].items():
            print(f"{family:<8}{key:>7}{r['beta_s']:>9.1f}{r['beta_c']:>9.1f}"
                  f"{r['ratio_abs']:>9.2f}{r['frac_ss']:>8.2f}")
    print(f"\nwritten: {OUT}")


if __name__ == '__main__':
    main()
