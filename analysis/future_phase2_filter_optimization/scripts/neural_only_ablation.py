#!/usr/bin/env python3
"""Neural-only vs behavioral-only vs joint fit — atom ablation (no refitting).

Background
----------
Anticipated criticism: "the neural data may only be an auxiliary to the
behavioral (JND) term; the fit would come out the same from behavior alone."
If true, the paper's central claim (a filter derived from the individual's own
*cortical* representation) would be unsupported.

The v6 production run already enumerates combos with an EMPTY gamma set
(`enumerate_combos_sub08/09` -> `gamma_opts` includes `[]`), so neural-only
fits are already in the stored output. This script extracts and contrasts them
rather than refitting.

Combination rule in the production fit (s10b_v6_pca_rdm.py, ~line 570):

    comp = sum_over_atoms( zscore_grid(atom_grid) ) / sqrt(n_atoms)

i.e. every atom is z-scored on the (beta_s, beta_c) grid and then EQUALLY
weighted. There is no free weight that could privilege the behavioral term.

Atom classes
------------
  NEURAL : gamma_pairs == []            (RDM_<roi> and/or LOCO_V4 only)
  behav  : rdm_rois == [] and no LOCO   (gamma pairs only)
  BOTH   : at least one of each

Grid (two_comp.py)
------------------
  BS_GRID = 0 .. 50 step 2   (26 pts)   -> beta_s at 0 or 50 is a boundary hit
  BC_GRID = -50 .. 50 step 2 (51 pts)   -> beta_c at -50 or 50 is a boundary hit

`boundary` fraction is the key degeneracy diagnostic: an atom whose optimum
sits on the grid edge in most resamples is not identifying an interior
solution.

Input
-----
results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json

Output
------
results/s10_inclusion/neural_only_ablation.json

Usage
-----
    conda activate srm
    python scripts/neural_only_ablation.py
"""

import json
import os

import numpy as np

SUBJECTS = ['sub-08', 'sub-09']
FAMILY_KEY = '2comp'

# Adopted production combination per subject, per Results/results_v4.tex:
#   deutan  : gamma_OY  + L_RDM^(V2)  -> (beta_s, beta_c) = (6, -42)
#   protan  : gamma_all + L_RDM^(V1)  -> (beta_s, beta_c) = (2, +24)
ADOPTED = {
    'sub-08': {'joint': 'γOY|RDMV2|noLOCO',
               'neural': 'γ_|RDMV2|noLOCO',
               'behavioral': 'γOY|RDM_|noLOCO'},
    'sub-09': {'joint': 'γALL|RDMV1|noLOCO',
               'neural': 'γ_|RDMV1|noLOCO',
               'behavioral': 'γALL|RDM_|noLOCO'},
}
BS_EDGES = (0.0, 50.0)
BC_EDGES = (-50.0, 50.0)

_HERE = os.path.dirname(os.path.abspath(__file__))
PHASE = os.path.dirname(_HERE)
RESDIR = os.path.join(PHASE, 'results', 's10_inclusion')


def _stat(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if v.size == 0:
        return {'median': None, 'iqr': None, 'n': 0}
    return {'median': float(np.median(v)),
            'iqr': float(np.percentile(v, 75) - np.percentile(v, 25)),
            'n': int(v.size)}


def classify(cfg):
    has_g = bool(cfg.get('gamma_pairs'))
    has_n = bool(cfg.get('rdm_rois')) or bool(cfg.get('loco_v4'))
    if has_g and has_n:
        return 'both'
    return 'behavioral' if has_g else 'neural'


def extract(subject):
    with open(os.path.join(RESDIR,
              f's10b_v6_pca_rdm_results_{subject}.json')) as f:
        d = json.load(f)
    storage, summary = d['storage'], d['summary']
    rows = {}
    for label, blob in storage.items():
        fits = blob.get(FAMILY_KEY) or []
        if not fits:
            continue
        cfg = summary[label]['config']
        bs = [f.get('beta_s') for f in fits]
        bc = [f.get('beta_c') for f in fits]
        rows[label] = {
            'class': classify(cfg),
            'gamma_pairs': cfg.get('gamma_pairs'),
            'rdm_rois': cfg.get('rdm_rois'),
            'loco_v4': bool(cfg.get('loco_v4')),
            'n_resamples': len(fits),
            'beta_s': _stat(bs),
            'beta_c': _stat(bc),
            'boundary_frac': float(np.mean([bool(f.get('boundary'))
                                            for f in fits])),
        }
    return rows, d.get('meta', {})


def pair_contrasts(rows):
    """For each ROI, line up neural-only / behavioral-only / joint (noLOCO)."""
    out = []
    neural = {k: v for k, v in rows.items() if v['class'] == 'neural'}
    behav = {k: v for k, v in rows.items() if v['class'] == 'behavioral'}
    both = {k: v for k, v in rows.items() if v['class'] == 'both'}
    for nk, nv in neural.items():
        if nv['loco_v4']:
            continue          # LOCO combos are degenerate; see boundary_frac
        for bk, bv in behav.items():
            for jk, jv in both.items():
                if (jv['rdm_rois'] == nv['rdm_rois']
                        and jv['gamma_pairs'] == bv['gamma_pairs']
                        and not jv['loco_v4']):
                    d_n = {ax: abs(jv[ax]['median'] - nv[ax]['median'])
                           for ax in ('beta_s', 'beta_c')
                           if jv[ax]['median'] is not None
                           and nv[ax]['median'] is not None}
                    d_b = {ax: abs(jv[ax]['median'] - bv[ax]['median'])
                           for ax in ('beta_s', 'beta_c')
                           if jv[ax]['median'] is not None
                           and bv[ax]['median'] is not None}
                    tot_n = sum(d_n.values()) if len(d_n) == 2 else None
                    tot_b = sum(d_b.values()) if len(d_b) == 2 else None
                    out.append({
                        'rdm_rois': nv['rdm_rois'],
                        'gamma_pairs': bv['gamma_pairs'],
                        'neural_only': {'label': nk,
                                        'beta_s': nv['beta_s']['median'],
                                        'beta_c': nv['beta_c']['median'],
                                        'boundary_frac': nv['boundary_frac']},
                        'behavioral_only': {'label': bk,
                                            'beta_s': bv['beta_s']['median'],
                                            'beta_c': bv['beta_c']['median'],
                                            'boundary_frac': bv['boundary_frac']},
                        'joint': {'label': jk,
                                  'beta_s': jv['beta_s']['median'],
                                  'beta_c': jv['beta_c']['median'],
                                  'boundary_frac': jv['boundary_frac']},
                        'L1_joint_to_neural': tot_n,
                        'L1_joint_to_behavioral': tot_b,
                        'joint_closer_to': (
                            None if tot_n is None or tot_b is None
                            else ('neural' if tot_n < tot_b
                                  else ('behavioral' if tot_b < tot_n
                                        else 'tie'))),
                    })
    return out


def main():
    out = {
        'analysis': 'neural_only_ablation',
        'question': ('does the fit survive on neural atoms alone, or is the '
                     'neural term merely auxiliary to the behavioral JND term'),
        'family': FAMILY_KEY,
        'combination_rule': 'sum(zscore_grid(atom)) / sqrt(n_atoms) — equal weight',
        'grid': {'BS_GRID': [0.0, 50.0, 2.0], 'BC_GRID': [-50.0, 50.0, 2.0],
                 'boundary_definition': 'argmin at first/last index of either axis'},
        'source': 'results/s10_inclusion/s10b_v6_pca_rdm_results_{subject}.json',
        'subjects': {},
    }
    for sid in SUBJECTS:
        rows, meta = extract(sid)
        contrasts = pair_contrasts(rows)
        loco_rows = {k: v for k, v in rows.items() if v['loco_v4']}
        # Per-axis attribution for the ADOPTED combination (the one the paper
        # reports). Aggregating over all 71 combos answers a different, weaker
        # question; the adopted fit is what the claim rests on.
        adopted = None
        spec = ADOPTED.get(sid, {})
        if all(k in rows for k in spec.values()):
            j, n, b = (rows[spec['joint']], rows[spec['neural']],
                       rows[spec['behavioral']])
            adopted = {'labels': spec, 'per_axis': {}}
            for ax in ('beta_s', 'beta_c'):
                jv, nv, bv = (j[ax]['median'], n[ax]['median'], b[ax]['median'])
                dn, db = abs(jv - nv), abs(jv - bv)
                adopted['per_axis'][ax] = {
                    'joint': jv, 'neural_only': nv, 'behavioral_only': bv,
                    'dist_to_neural': dn, 'dist_to_behavioral': db,
                    'driven_by': ('neural' if dn < db
                                  else ('behavioral' if db < dn else 'tie')),
                }
            adopted['boundary_frac'] = {
                'joint': j['boundary_frac'], 'neural_only': n['boundary_frac'],
                'behavioral_only': b['boundary_frac']}

        tally = {'neural': 0, 'behavioral': 0, 'tie': 0}
        for c in contrasts:
            if c['joint_closer_to'] in tally:
                tally[c['joint_closer_to']] += 1
        neural_only = {k: (v['beta_s']['median'], v['beta_c']['median'])
                       for k, v in rows.items()
                       if v['class'] == 'neural' and not v['loco_v4']}
        out['subjects'][sid] = {
            'meta': meta,
            'n_combos': len(rows),
            'adopted_combination': adopted,
            'verdict': {
                'n_contrasts': len(contrasts),
                'joint_closer_to': tally,
                'dominant_term': (
                    'behavioral' if tally['behavioral'] > tally['neural']
                    else ('neural' if tally['neural'] > tally['behavioral']
                          else 'undetermined')),
                'neural_only_solutions_by_roi': neural_only,
            },
            'per_combo': rows,
            'contrasts_noLOCO': contrasts,
            'loco_boundary_frac': {
                'min': (min(v['boundary_frac'] for v in loco_rows.values())
                        if loco_rows else None),
                'median': (float(np.median([v['boundary_frac']
                                            for v in loco_rows.values()]))
                           if loco_rows else None),
                'n_combos': len(loco_rows),
            },
        }

    dest = os.path.join(RESDIR, 'neural_only_ablation.json')
    with open(dest, 'w') as f:
        json.dump(out, f, indent=2)

    for sid in SUBJECTS:
        s = out['subjects'][sid]
        print(f'\n=== {sid} ===')
        a = s.get('adopted_combination')
        if a:
            print(f'  ADOPTED {a["labels"]["joint"]}')
            for ax, r in a['per_axis'].items():
                print(f'    {ax}: joint {r["joint"]:>6.1f} | neural-only '
                      f'{r["neural_only"]:>6.1f} | behav-only '
                      f'{r["behavioral_only"]:>6.1f}  -> driven by '
                      f'{r["driven_by"]}')
        lb = s['loco_boundary_frac']
        print(f'  LOCO combos ({lb["n_combos"]}): boundary frac '
              f'median {lb["median"]:.2f}, min {lb["min"]:.2f}')
        print(f'  {"ROI":10s} {"gamma":14s} '
              f'{"neural":>14s} {"behav":>14s} {"joint":>14s}  closer')
        for c in s['contrasts_noLOCO']:
            roi = '+'.join(c['rdm_rois']) or '-'
            gam = ','.join(c['gamma_pairs']) or '-'
            f = lambda x: f'({x["beta_s"]:.0f},{x["beta_c"]:.0f})'
            print(f'  {roi:10s} {gam:14s} {f(c["neural_only"]):>14s} '
                  f'{f(c["behavioral_only"]):>14s} {f(c["joint"]):>14s}'
                  f'  {c["joint_closer_to"]}')
    print(f'\nwrote {dest}')


if __name__ == '__main__':
    main()
