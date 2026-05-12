"""fixedW_onlyTest_p2a_ranking.py — P2a ranking across all candidate filters.

P2a = how well the model's predicted "CVD perceives" column matches the
SUBJECT's reported perception of original stimuli (raw_behav.md).

For each candidate (β_s, β_c) filter we predict θ_perceived for the 8 hues and
compare against subject-specific HC-equivalent name bins. Score uses
phase3_candidate_analysis_v2.hc_match_score (exact=1.0, adjacent partial credit).

Subjects:
  sub-08 deutan — SUB08_ORIGINAL_HC_EQUIV already canonical
  sub-09 protan — derived from raw_behav.md verbal reports

Output:
  results/fixedW_onlyTest/p2a_ranking.csv
  results/fixedW_onlyTest/p2a_ranking.md   (markdown table)
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)

_PHASE2 = _THIS_DIR.parent
OUT = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUT.mkdir(parents=True, exist_ok=True)

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
THETA_CONF_DEG = 150.0  # OLD formula convention (deutan); applied to protan too

# ---------------------------------------------------------------------------
# Sub-09 protan HC-equivalent perception (from raw_behav.md verbal reports)
# ---------------------------------------------------------------------------
SUB09_ORIGINAL_HC_EQUIV = {
    0:   "pink",         # "붉은색에 가까운 핑크" — pink-leaning red
    45:  "orange",       # "주황색" — PRESERVED
    90:  "yellow-green", # "올리브색" — olive (yellow-green family)
    135: "yellow-green", # "연두 + 민트색" — light yellow-green + mint
    180: "sky",          # "칙칙한 하늘색" — muted sky (cyan → sky)
    225: "sky",          # "조금 덜 칙칙한 하늘색" — slightly less muted sky (preserved)
    270: "blue",         # "파란색" — PRESERVED
    315: "violet",       # "연보라+연분홍" — light violet + light pink
}


# ---------------------------------------------------------------------------
# Candidate filters
# ---------------------------------------------------------------------------
SUB08_FILTERS = [
    # Phase 2 fits
    ('Phase A LOCO',                  38, -14),   # § canonical
    ('V4-only OLD',                   38,  +7),   # primary.png
    ('Fine grid c2 orange',           44, -14),
    # Loss inventory (V4)
    ('cycle12_cross_roi/opt2',        68, -38),
    ('cycle14_cross_roi_rdm/mw_jaccard/l_topk', 58, -36),  # Cycle 14 incl. l_topk_jaccard
    ('cycle15_opt3 v4mwj+v1mwj',      58, -28),
    ('cycle15_opt4 v4mwj+v4spear',    70, -52),
    ('l_mag',                         44, +58),
    ('sign_agree',                    10, +58),
    # Grid-edge (warn: argmin at boundary, may be noise)
    ('l_dir/pearson_r [edge]',        78, -60),
    ('l_rank/spearman_r [edge]',      74, -60),
    ('norm_resid [edge]',             76, -60),
    # Wretrained × loss variants
    ('A wretrained 4-term/L1/L3a-c',  10, -32),
    ('A wretrained V4-CCC',           16, +40),
    # Wfixed × loss variants
    ('B wfixed   4-term',              6, -48),
    ('B wfixed   V4-CCC',             46, -20),
    # Baseline
    ('β=0 baseline (no filter)',       0,   0),
]

SUB09_FILTERS = [
    # Phase 2 fits
    ('Phase A LOCO',                   6, -22),   # behaviorally consistent
    # Loss inventory (V4)
    ('cycle12_cross_roi',             30, +26),
    ('cycle14_cross_roi_rdm',         32, +22),
    ('cycle15_opt2 v4mwj+v1lrank/mw_jaccard', 44, +54),
    ('cycle15_opt3 v4mwj+v1mwj [DEGEN]', 0,  0),  # degenerate
    ('cycle15_opt4 v4mwj+v4spear',    24, +32),
    ('l_mag',                         72, +38),
    ('norm_resid',                    24, +44),
    # Grid-edge (warn)
    ('l_topk_jaccard [edge -]',        0, -60),
    ('sign_agree [edge -]',            0, -60),
    ('l_rank/spearman_r [edge +]',     0, +58),
    ('l_dir/pearson_r [edge +]',       0, +60),
    # Wretrained × loss variants
    ('A wretrained 4-term/V4-CCC',    30, +46),
    # Wfixed × loss variants
    ('B wfixed   4-term',             46, +48),
    ('B wfixed   V4-CCC',             46, +50),
    # Baseline
    ('β=0 baseline (no filter)',       0,   0),
]


def dt_old(theta_deg, bs, bc, theta_conf=THETA_CONF_DEG):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(theta_conf)))


def forward(theta, bs, bc):
    return (theta + dt_old(theta, bs, bc)) % 360.0


def p2a_compute(bs, bc, target_map):
    """Compute P2a per-color scores given subject's HC-equivalent map."""
    per_color = []
    total = 0.0
    exact = 0
    for theta in HUE_ANGLES:
        theta_cvd = forward(float(theta), bs, bc)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        per_color.append({
            'theta': theta,
            'theta_cvd': float(theta_cvd),
            'dt': float(theta_cvd - theta),
            'pred': pred,
            'target': target,
            'score': score,
        })
        total += score
        if pred == target:
            exact += 1
    p2a = total / 8.0
    return p2a, exact, per_color


def rank_filters(filters, target_map, subject_id):
    rows = []
    for name, bs, bc in filters:
        norm = float(np.hypot(bs, bc))
        p2a, exact, per_color = p2a_compute(bs, bc, target_map)
        rows.append({
            'subject': subject_id,
            'filter': name,
            'bs': bs, 'bc': bc, 'norm': norm,
            'p2a': p2a,
            'exact_n': exact,
            'per_color': per_color,
        })
    rows.sort(key=lambda r: -r['p2a'])  # descending
    return rows


def write_csv(all_rows, path):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['subject', 'filter', 'bs', 'bc', 'norm', 'p2a', 'exact_n',
                    *[f'c{i+1}_pred' for i in range(8)],
                    *[f'c{i+1}_target' for i in range(8)],
                    *[f'c{i+1}_score' for i in range(8)]])
        for r in all_rows:
            preds = [c['pred'] for c in r['per_color']]
            targets = [c['target'] for c in r['per_color']]
            scores = [f"{c['score']:.2f}" for c in r['per_color']]
            w.writerow([r['subject'], r['filter'], r['bs'], r['bc'],
                        f"{r['norm']:.1f}", f"{r['p2a']:.3f}", r['exact_n'],
                        *preds, *targets, *scores])
    print(f'  wrote {path}')


def write_md(sub08_rows, sub09_rows, path):
    md = []
    md.append('# P2a Ranking — sub-08 deutan + sub-09 protan')
    md.append('')
    md.append('P2a = mean match score between predicted CVD-percieved color (forward model output) and subject\'s actual reported HC-name perception (raw_behav.md).')
    md.append('Scoring: exact match = 1.0, adjacent name = partial credit (see `HC_ADJ` in phase3_candidate_analysis_v2.py).')
    md.append('')
    md.append('## sub-08 deutan (target = SUB08_ORIGINAL_HC_EQUIV)')
    md.append('')
    md.append('| Rank | Filter | β_s | β_c | norm | **P2a** | exact/8 |')
    md.append('|---|---|---|---|---|---|---|')
    for i, r in enumerate(sub08_rows):
        md.append(f"| {i+1} | {r['filter']} | {r['bs']:.0f} | {r['bc']:+.0f} | "
                  f"{r['norm']:.1f}° | **{r['p2a']:.3f}** | {r['exact_n']}/8 |")
    md.append('')
    md.append('### Per-color detail (sub-08 top 3)')
    md.append('')
    md.append('| Rank | Filter | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |')
    md.append('|---|---|---|---|---|---|---|---|---|---|')
    md.append(f"|  T | target | {' | '.join([SUB08_ORIGINAL_HC_EQUIV[t] for t in HUE_ANGLES])} |")
    for i, r in enumerate(sub08_rows[:3]):
        scores = [f"{c['pred']}({c['score']:.1f})" for c in r['per_color']]
        md.append(f"| {i+1} | {r['filter']} | {' | '.join(scores)} |")
    md.append('')
    md.append('## sub-09 protan (target = SUB09_ORIGINAL_HC_EQUIV)')
    md.append('')
    md.append('| Rank | Filter | β_s | β_c | norm | **P2a** | exact/8 |')
    md.append('|---|---|---|---|---|---|---|')
    for i, r in enumerate(sub09_rows):
        md.append(f"| {i+1} | {r['filter']} | {r['bs']:.0f} | {r['bc']:+.0f} | "
                  f"{r['norm']:.1f}° | **{r['p2a']:.3f}** | {r['exact_n']}/8 |")
    md.append('')
    md.append('### Per-color detail (sub-09 top 3)')
    md.append('')
    md.append('| Rank | Filter | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |')
    md.append('|---|---|---|---|---|---|---|---|---|---|')
    md.append(f"|  T | target | {' | '.join([SUB09_ORIGINAL_HC_EQUIV[t] for t in HUE_ANGLES])} |")
    for i, r in enumerate(sub09_rows[:3]):
        scores = [f"{c['pred']}({c['score']:.1f})" for c in r['per_color']]
        md.append(f"| {i+1} | {r['filter']} | {' | '.join(scores)} |")
    md.append('')
    md.append('## Notes')
    md.append('')
    md.append('- Forward model: `δθ = β_s·cos(θ-90°) + β_c·cos(θ-150°)`. THETA_CONF=150° applied to both deutan and protan (project convention; CIElab nominal).')
    md.append('- β=0 baseline = no filter applied = original color rendering. Its P2a measures how close original HC colors are to subject perception (lower P2a = more distortion subject reports).')
    md.append('- HC_NAME_BINS span 13 fine bins (red, red-orange, orange, ..., magenta, pink). HC_ADJ provides 1-step adjacency partial credit (0.3-0.8).')
    md.append('')
    Path(path).write_text('\n'.join(md))
    print(f'  wrote {path}')


def main():
    print('Computing P2a ranking for all candidate filters...')
    print(f'\n  HUE_ANGLES: {HUE_ANGLES}')
    print(f'  SUB08 target: {SUB08_ORIGINAL_HC_EQUIV}')
    print(f'  SUB09 target: {SUB09_ORIGINAL_HC_EQUIV}')

    sub08_rows = rank_filters(SUB08_FILTERS, SUB08_ORIGINAL_HC_EQUIV, '08')
    sub09_rows = rank_filters(SUB09_FILTERS, SUB09_ORIGINAL_HC_EQUIV, '09')

    write_csv(sub08_rows + sub09_rows, OUT / 'p2a_ranking.csv')
    write_md(sub08_rows, sub09_rows, OUT / 'p2a_ranking.md')

    print('\n=== sub-08 deutan TOP 5 ===')
    for i, r in enumerate(sub08_rows[:5]):
        print(f"  {i+1}. {r['filter']:25s} β=({r['bs']:+.0f}, {r['bc']:+.0f}) "
              f"norm={r['norm']:.1f}°  P2a={r['p2a']:.3f}  exact={r['exact_n']}/8")

    print('\n=== sub-09 protan TOP 5 ===')
    for i, r in enumerate(sub09_rows[:5]):
        print(f"  {i+1}. {r['filter']:25s} β=({r['bs']:+.0f}, {r['bc']:+.0f}) "
              f"norm={r['norm']:.1f}°  P2a={r['p2a']:.3f}  exact={r['exact_n']}/8")


if __name__ == '__main__':
    main()
