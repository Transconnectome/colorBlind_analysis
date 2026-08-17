"""3-way compare: PCA-RDM vs SRM-RDM-cosine vs SRM-Disparity v6 outputs.

For each (combo, model) cell, show param + test_loss_median for all three.
Then summarize best cell per model.

Usage:
  python compare_three_v6.py --subject sub-09 --top 12
  python compare_three_v6.py --subject sub-08 --top 15
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

RES = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/'
            'Projects/colorBlind_analysis/analysis/'
            'future_phase2_filter_optimization/results/s10_inclusion')


def load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())['summary']


def fmt(v, prec=3):
    if v is None:
        return ' nan '
    return f'{v:6.{prec}f}'


def param_str(pm, model):
    if pm is None:
        return ' -    '
    ps = pm.get('param_summary', {})
    if model.startswith('rc'):
        return f"g={fmt(ps.get('g_median'),2)}"
    return f"({fmt(ps.get('bs_median'),1)},{fmt(ps.get('bc_median'),1)})"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', required=True,
                        choices=['sub-08', 'sub-09'])
    parser.add_argument('--top', type=int, default=12)
    args = parser.parse_args()

    pca = load(RES / f's10b_v6_pca_rdm_results_{args.subject}.json')
    cos = load(RES / f's10b_v6_srm_rdm_results_{args.subject}.json')
    dis = load(RES / f's10b_v6_srm_disparity_results_{args.subject}.json')

    if pca is None:
        print(f'missing PCA file for {args.subject}'); return
    if cos is None and dis is None:
        print(f'no SRM files for {args.subject}'); return

    sample = next(iter(pca.keys()))
    models = list(pca[sample]['per_model'].keys())

    for model in models:
        print(f'\n========== {args.subject} | model={model} ==========')
        rows = []
        for label, c in pca.items():
            pm_pca = c['per_model'].get(model)
            pm_cos = cos[label]['per_model'].get(model) if (cos and label in cos) else None
            pm_dis = dis[label]['per_model'].get(model) if (dis and label in dis) else None
            if all(x is None for x in (pm_pca, pm_cos, pm_dis)):
                continue
            rows.append({'label': label, 'pca': pm_pca,
                          'cos': pm_cos, 'dis': pm_dis})

        rows.sort(key=lambda r: ((r['pca'] or {}).get('test_loss_median')
                                  if (r['pca'] and (r['pca'] or {}).get('test_loss_median') is not None)
                                  else 1e9))

        hdr = (f"{'combo':38s}  "
               f"{'PCA testL':>9s} {'COS testL':>9s} {'DIS testL':>9s}  "
               f"{'PCA param':>20s} {'COS param':>20s} {'DIS param':>20s}")
        print(hdr)
        print('-' * len(hdr))
        for r in rows[:args.top]:
            print(f"{r['label']:38s}  "
                  f"{fmt((r['pca'] or {}).get('test_loss_median')):>9s} "
                  f"{fmt((r['cos'] or {}).get('test_loss_median')):>9s} "
                  f"{fmt((r['dis'] or {}).get('test_loss_median')):>9s}  "
                  f"{param_str(r['pca'], model):>20s} "
                  f"{param_str(r['cos'], model):>20s} "
                  f"{param_str(r['dis'], model):>20s}")

    print('\n========== Best cell per model (argmin test_loss_median) ==========')
    for model in models:
        bests = {}
        for tag, sm in (('PCA', pca), ('COS', cos), ('DIS', dis)):
            if sm is None:
                continue
            best = None
            for label, c in sm.items():
                pm = c['per_model'].get(model)
                if not pm: continue
                tl = pm.get('test_loss_median')
                if tl is None: continue
                if best is None or tl < best[1]:
                    best = (label, tl, pm)
            bests[tag] = best
        print(f'\n{model}:')
        for tag, b in bests.items():
            if b:
                print(f"  {tag} best: {b[0]:42s} | test={b[1]:7.3f} | {param_str(b[2], model)}")
        labels = set(b[0] for b in bests.values() if b)
        print(f"  same combo across methods? {'YES' if len(labels) == 1 else 'NO  (combos: ' + ', '.join(labels) + ')'}")


if __name__ == '__main__':
    main()
