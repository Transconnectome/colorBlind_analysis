"""s5_tregillus_compare.py — Side-by-side R+C (current uniform scaling) vs
R+C-Tregillus (opponent R-G gain) comparison.

For every (subject, ROI, Δλ source, loss) cell:
  - current  : g, loss, ‖δθ‖, boundary flag
  - tregillus: g, loss, ‖δθ‖, boundary flag, in zone?
  - δθ cosine between two
  - Δloss (Tregillus better if negative)

Writes:
  results/s5_tregillus/comparison_table.json  — full 96-row table
  results/s5_tregillus/COMPARISON_REPORT.md   — narrative
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S5_DIR = ROOT / 'results' / 's5_all_paths'
TREG_DIR = ROOT / 'results' / 's5_tregillus'


def _norm(x):
    arr = np.asarray(x, dtype=float)
    return float(np.linalg.norm(arr))


def _cosine(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-6 or nb < 1e-6:
        return float('nan')
    return float(np.dot(a, b) / (na * nb))


def _rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=float) ** 2)))


def main():
    rows = []
    cells = []
    for subj in ('sub-08', 'sub-09'):
        for roi in ('V1', 'V4'):
            cells.append((subj, roi))

    for subj, roi in cells:
        s5_path = S5_DIR / f"{subj}_{roi}_sigma21.json"
        tr_path = TREG_DIR / f"{subj}_{roi}_sigma21.json"
        with open(s5_path) as f:
            s5 = json.load(f)
        with open(tr_path) as f:
            tr = json.load(f)

        # index R+C fits by (delta_lambda_source, loss_target)
        s5_rc = {(fit['delta_lambda_source'], fit['loss_target']): fit
                 for fit in s5['fits'] if fit['model'] == 'R+C'}
        tr_rc = {(fit['delta_lambda_source'], fit['loss_target']): fit
                 for fit in tr['fits'] if fit['model'] == 'R+C_opp'}

        for key in sorted(s5_rc):
            cur = s5_rc[key]
            opp = tr_rc[key]
            dt_cur = np.asarray(cur['delta_theta_at_best'], dtype=float)
            dt_opp = np.asarray(opp['delta_theta_at_best'], dtype=float)
            cos = _cosine(dt_cur, dt_opp)
            dloss = opp['loss_best'] - cur['loss_best']  # negative = treg better
            rows.append({
                'subject': subj, 'roi': roi, 'family': s5['cvd_family'],
                'delta_lambda_source': key[0],
                'delta_lambda_nm': cur['delta_lambda_nm'],
                'loss_target': key[1],
                # current
                'cur_g': cur['g_best'],
                'cur_loss': cur['loss_best'],
                'cur_dtheta_norm': _norm(dt_cur),
                'cur_dtheta_rms': _rms(dt_cur),
                'cur_dtheta_max_abs': float(np.max(np.abs(dt_cur))),
                'cur_misspecified': cur.get('misspecified', False),
                # tregillus
                'tre_g': opp['g_best'],
                'tre_loss': opp['loss_best'],
                'tre_dtheta_norm': _norm(dt_opp),
                'tre_dtheta_rms': _rms(dt_opp),
                'tre_dtheta_max_abs': float(np.max(np.abs(dt_opp))),
                'tre_boundary_low': opp['boundary_low'],
                'tre_boundary_high': opp['boundary_high'],
                'tre_in_zone': opp['in_tregillus_zone'],
                # cross
                'delta_theta_cosine': cos,
                'delta_loss_tre_minus_cur': dloss,
                'tre_better_fit': bool(dloss < 0),
            })

    # Save raw table
    with open(TREG_DIR / 'comparison_table.json', 'w') as f:
        json.dump(rows, f, indent=2, default=str)

    # Counts
    n_total = len(rows)
    n_tre_better = sum(1 for r in rows if r['tre_better_fit'])
    n_in_zone = sum(1 for r in rows if r['tre_in_zone'])
    n_boundary = sum(1 for r in rows if r['tre_boundary_low'] or r['tre_boundary_high'])

    # Build report
    report = []
    report.append('# Tregillus R+C vs Current Uniform-Scaling R+C — Comparison Report')
    report.append('')
    report.append('**Forward map difference**:')
    report.append('- **Current** (`rc_1dof.forward_rc`): δθ_RC = (2 − g)·δθ_Machado')
    report.append('  · uniform linear scaling across hue; g∈[0,3]; g=2 → δθ=0 by construction')
    report.append('- **Tregillus** (`rc_opponent_1dof.forward_rc_opp`): rg′ = rg_ret + g·(rg_ret − rg_base), by′ = by_ret')
    report.append('  · L-M-channel selective gain; B-Y preserved; g∈[-2,+2]; g=-1 ≈ partial restoration (R-G only)')
    report.append('')
    report.append(f'**Total cells**: {n_total} (= 2 subj × 2 ROI × 3 Δλ × 8 loss)')
    report.append(f'**Tregillus lower loss**: {n_tre_better}/{n_total} '
                  f'({100*n_tre_better/n_total:.1f}%)')
    report.append(f'**Tregillus g in [-1, 0] (physiological zone)**: {n_in_zone}/{n_total} '
                  f'({100*n_in_zone/n_total:.1f}%)')
    report.append(f'**Tregillus g at grid boundary**: {n_boundary}/{n_total} '
                  f'({100*n_boundary/n_total:.1f}%)')
    report.append('')

    # ===== Headline cells =====
    report.append('## Headline cells (paper-relevant)')
    report.append('')

    def pick(rows, **kw):
        out = [r for r in rows
               if all(r.get(k) == v for k, v in kw.items())]
        return out

    def cell_block(title, rs):
        report.append(f'### {title}')
        if not rs:
            report.append('(no matching rows)')
            return
        report.append('')
        report.append('| Δλ src | Δλ (nm) | Loss | Cur g | Cur loss | Cur ‖δθ‖ | '
                      'Tre g | Tre loss | Tre ‖δθ‖ | δθ cos | Δloss | Tre zone? | Boundary? |')
        report.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        for r in rs:
            b = ('LOW' if r['tre_boundary_low']
                 else ('HIGH' if r['tre_boundary_high'] else '-'))
            zone = '✓' if r['tre_in_zone'] else '✗'
            better = '✓' if r['tre_better_fit'] else '✗'
            cos_s = f"{r['delta_theta_cosine']:.3f}" if np.isfinite(r['delta_theta_cosine']) else 'nan'
            report.append(
                f"| {r['delta_lambda_source']} | {r['delta_lambda_nm']:.1f} | "
                f"{r['loss_target']} | {r['cur_g']:+.2f} | {r['cur_loss']:.4f} | "
                f"{r['cur_dtheta_norm']:.1f}° | {r['tre_g']:+.2f} | "
                f"{r['tre_loss']:.4f} | {r['tre_dtheta_norm']:.1f}° | "
                f"{cos_s} | {r['delta_loss_tre_minus_cur']:+.4f} ({better}) | "
                f"{zone} | {b} |"
            )
        report.append('')

    # Headline 1: sub-09 V1 L4 RDM (key question 1)
    rs = pick(rows, subject='sub-09', roi='V1', loss_target='L4_RDM_corr')
    cell_block('sub-09 V1 — L4 RDM (key question: does Tregillus give cos > 0.13?)', rs)

    # Headline 2: sub-09 V1 L2 behav (key question 2: over-shoot recovery)
    rs = pick(rows, subject='sub-09', roi='V1', loss_target='L2_behav_gamma')
    cell_block('sub-09 V1 — L2 behav γ (key question: Tregillus zone recovery?)', rs)

    # Headline 3: sub-08 V1/V4 L8 PRIMARY
    rs = pick(rows, subject='sub-08', loss_target='L8_modality_5050')
    cell_block('sub-08 V1/V4 — L8 modality PRIMARY (δθ shape agreement?)', rs)

    rs = pick(rows, subject='sub-09', loss_target='L8_modality_5050')
    cell_block('sub-09 V1/V4 — L8 modality PRIMARY', rs)

    # ===== Per-cell full tables =====
    report.append('## Full 96-row comparison')
    report.append('')
    for subj in ('sub-08', 'sub-09'):
        for roi in ('V1', 'V4'):
            rs = pick(rows, subject=subj, roi=roi)
            cell_block(f'{subj} {roi}', rs)

    # ===== Aggregate patterns =====
    report.append('## Aggregate patterns')
    report.append('')

    # Per-subject Tregillus zone rate
    report.append('### Tregillus g zone occupancy per (subject, ROI, loss)')
    report.append('')
    report.append('| Subject | ROI | Loss | n cells (Δλ src) | n in zone [-1,0] | n boundary |')
    report.append('|---|---|---|---|---|---|')
    for subj in ('sub-08', 'sub-09'):
        for roi in ('V1', 'V4'):
            for loss in ['L1_behav_alpha', 'L2_behav_gamma', 'L3_LOCO',
                         'L4_RDM_corr', 'L5_behav_composite',
                         'L6_neural_composite', 'L7_all_equal',
                         'L8_modality_5050']:
                rs = pick(rows, subject=subj, roi=roi, loss_target=loss)
                n_zone = sum(1 for r in rs if r['tre_in_zone'])
                n_bd = sum(1 for r in rs
                           if r['tre_boundary_low'] or r['tre_boundary_high'])
                report.append(
                    f'| {subj} | {roi} | {loss} | {len(rs)} | {n_zone} | {n_bd} |'
                )
    report.append('')

    # δθ cosine distribution
    cos_vals = [r['delta_theta_cosine'] for r in rows
                if np.isfinite(r['delta_theta_cosine'])]
    if cos_vals:
        report.append('### δθ cosine (current vs Tregillus) summary')
        report.append('')
        cv = np.asarray(cos_vals)
        report.append(f'- n with finite cos: {len(cv)}')
        report.append(f'- mean: {cv.mean():+.3f}, median: {np.median(cv):+.3f}, '
                      f'std: {cv.std():.3f}')
        report.append(f'- n cos > 0.9 (near-identical δθ): {int(np.sum(cv > 0.9))}')
        report.append(f'- n cos > 0.5 (broadly agree): {int(np.sum(cv > 0.5))}')
        report.append(f'- n cos ∈ [-0.5, 0.5] (disagree): '
                      f'{int(np.sum(np.abs(cv) <= 0.5))}')
        report.append(f'- n cos < -0.5 (opposite): {int(np.sum(cv < -0.5))}')
        report.append('')

    # Δloss distribution
    dloss_vals = np.asarray([r['delta_loss_tre_minus_cur'] for r in rows])
    report.append('### Δloss (Tregillus − Current) per loss family')
    report.append('')
    report.append('| Loss | n cells | n Treg better | median Δloss | mean Δloss |')
    report.append('|---|---|---|---|---|')
    for loss in ['L1_behav_alpha', 'L2_behav_gamma', 'L3_LOCO',
                 'L4_RDM_corr', 'L5_behav_composite',
                 'L6_neural_composite', 'L7_all_equal',
                 'L8_modality_5050']:
        rs = pick(rows, loss_target=loss)
        if not rs:
            continue
        dvals = np.asarray([r['delta_loss_tre_minus_cur'] for r in rs])
        n_better = int(np.sum(dvals < 0))
        report.append(
            f'| {loss} | {len(rs)} | {n_better} | {np.median(dvals):+.4f} | '
            f'{dvals.mean():+.4f} |'
        )
    report.append('')

    # Save
    md_path = TREG_DIR / 'COMPARISON_REPORT.md'
    with open(md_path, 'w') as f:
        f.write('\n'.join(report))
    print(f'Wrote {md_path}')

    return rows


if __name__ == '__main__':
    main()
