"""Compare PCA-RDM (s10b_v6) vs SRM-RDM (s10b_v6_srm_rdm) v6 results.

For each (subject, combo, model) cell:
  - PCA: load summary['per_model'][model_key]
  - SRM: load same key from SRM output
  - report: param_summary, train_loss / test_loss / test_focal medians (+IQRs)
  - rank combos by test_loss_median to see if best cells agree

Usage:
  python compare_pca_vs_srm_v6.py --subject sub-09
  python compare_pca_vs_srm_v6.py --subject sub-08
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

RES_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/'
                'Projects/colorBlind_analysis/analysis/'
                'future_phase2_filter_optimization/results/s10_inclusion')


def load_summary(path: Path) -> dict:
    d = json.loads(path.read_text())
    return d['summary']


def fmt(v, prec=3):
    if v is None:
        return '   nan'
    return f'{v:6.{prec}f}'


def fmt_param(pm, model):
    if pm is None:
        return '  -    '
    if model.startswith('rc'):
        g = pm.get('param_summary', {}).get('g_median')
        gi = pm.get('param_summary', {}).get('g_iqr')
        return f'g={fmt(g,2)} (iqr={fmt(gi,2)})'
    bs = pm.get('param_summary', {}).get('bs_median')
    bc = pm.get('param_summary', {}).get('bc_median')
    bsi = pm.get('param_summary', {}).get('bs_iqr')
    bci = pm.get('param_summary', {}).get('bc_iqr')
    return f'bs={fmt(bs,1)} bc={fmt(bc,1)} (iqrs={fmt(bsi,1)},{fmt(bci,1)})'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', required=True,
                        choices=['sub-08', 'sub-09'])
    parser.add_argument('--top', type=int, default=10,
                        help='Top-N combos by test_loss_median')
    args = parser.parse_args()

    pca_p = RES_DIR / f's10b_v6_pca_rdm_results_{args.subject}.json'
    srm_p = RES_DIR / f's10b_v6_srm_rdm_results_{args.subject}.json'
    if not pca_p.exists():
        raise SystemExit(f'missing {pca_p}')
    if not srm_p.exists():
        raise SystemExit(f'missing {srm_p}')

    pca = load_summary(pca_p)
    srm = load_summary(srm_p)

    # 1) Per-combo, per-model table: test_loss_median, train_loss_median,
    #    test_focal_median, param_summary
    print('=' * 130)
    print(f'PCA vs SRM v6 — {args.subject}')
    print('=' * 130)

    # Find all model keys
    sample_combo = next(iter(pca.keys()))
    model_keys = [k for k in pca[sample_combo]['per_model'].keys()]

    # Per-model ranking by test_loss_median (lower=better)
    for model_key in model_keys:
        rows = []
        for label, c_pca in pca.items():
            c_srm = srm.get(label)
            pm_pca = c_pca['per_model'].get(model_key)
            pm_srm = c_srm['per_model'].get(model_key) if c_srm else None
            if pm_pca is None and pm_srm is None:
                continue
            rows.append({
                'label': label,
                'pca': pm_pca, 'srm': pm_srm,
            })

        # Sort by PCA test_loss_median (None -> +inf)
        rows.sort(key=lambda r: (r['pca'] or {}).get('test_loss_median')
                  if r['pca'] and (r['pca'] or {}).get('test_loss_median') is not None
                  else 1e9)
        print(f'\n--- model={model_key} (sorted by PCA test_loss_median) ---')
        print(f"{'combo':40s}  {'PCA testL':>10s}  {'SRM testL':>10s}  "
              f"{'d':>7s}  {'PCA trL':>9s}  {'SRM trL':>9s}  "
              f"{'PCA focal':>10s}  {'SRM focal':>10s}  "
              f"{'PCA param':38s}  {'SRM param':38s}")
        topN = rows[:args.top]
        for r in topN:
            pa = r['pca'] or {}
            sr = r['srm'] or {}
            tlp = pa.get('test_loss_median')
            tls = sr.get('test_loss_median')
            d = (tls - tlp) if (tlp is not None and tls is not None) else None
            print(f"{r['label']:40s}  {fmt(tlp):>10s}  {fmt(tls):>10s}  "
                  f"{fmt(d):>7s}  {fmt(pa.get('train_loss_median')):>9s}  "
                  f"{fmt(sr.get('train_loss_median')):>9s}  "
                  f"{fmt(pa.get('test_focal_median')):>10s}  "
                  f"{fmt(sr.get('test_focal_median')):>10s}  "
                  f"{fmt_param(pa, model_key):38s}  {fmt_param(sr, model_key):38s}")

    # 2) Best cell summary: argmin test_loss_median per model
    print('\n' + '=' * 130)
    print('Best cell per model (argmin test_loss_median)')
    print('=' * 130)
    for model_key in model_keys:
        best_pca, best_srm = None, None
        for label, c in pca.items():
            pm = c['per_model'].get(model_key)
            if not pm:
                continue
            tl = pm.get('test_loss_median')
            if tl is None:
                continue
            if best_pca is None or tl < best_pca[1]:
                best_pca = (label, tl, pm)
        for label, c in srm.items():
            pm = c['per_model'].get(model_key)
            if not pm:
                continue
            tl = pm.get('test_loss_median')
            if tl is None:
                continue
            if best_srm is None or tl < best_srm[1]:
                best_srm = (label, tl, pm)
        print(f'\n{model_key}:')
        if best_pca:
            print(f"  PCA best: {best_pca[0]} | test={best_pca[1]:.3f} | "
                  f"{fmt_param(best_pca[2], model_key)}")
        if best_srm:
            print(f"  SRM best: {best_srm[0]} | test={best_srm[1]:.3f} | "
                  f"{fmt_param(best_srm[2], model_key)}")
        if best_pca and best_srm:
            same_combo = best_pca[0] == best_srm[0]
            print(f"  same combo? {'YES' if same_combo else 'NO'}")


if __name__ == '__main__':
    main()
