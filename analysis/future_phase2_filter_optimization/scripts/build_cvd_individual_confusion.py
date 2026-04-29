#!/usr/bin/env python3
"""Per-CVD-subject × ROI confusion matrices + signed-error profiles.

Input:  results/decoder_loco/decoder_loco_long.csv
Output (in results/decoder_loco/per_cvd/):
  - sub-{ID}_{ROI}_confusion.csv       (8x8 row-normalized, ForwardEncoding only)
  - sub-{ID}_{ROI}_signed_error.csv    (per color: circular mean / sd of signed error)
  - sub-{ID}_summary.csv               (per color: accuracy, top-1 confusion target, mean signed error)
  - cvd_individual_report.md           (human-readable report per subject)

CVD subjects: sub-08 (deutan), sub-09 (protan), sub-10 (deutan-mild)

Key metrics for filter design:
  - accuracy[c]          : P(pred=c | true=c)
  - confused_to[c]       : argmax over p≠c of P(pred=p | true=c)
  - signed_error_mean[c] : circular mean of (pred_hue - true_hue) in degrees
                           -> direction filter must push pre-image
  - confusion_axis       : whether errors cluster on protan (16°) or deutan (150°) axis
"""

import csv
import math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
CSV_IN = ROOT / 'analysis' / 'future_phase2_filter_optimization' / 'results' / 'decoder_loco' / 'decoder_loco_long.csv'
OUT = ROOT / 'analysis' / 'future_phase2_filter_optimization' / 'results' / 'decoder_loco' / 'per_cvd'
OUT.mkdir(parents=True, exist_ok=True)

CVD = {
    '08': {'subtype': 'deutan',      'confusion_axis_deg': 150.0},
    '09': {'subtype': 'protan',      'confusion_axis_deg':  16.0},
    '10': {'subtype': 'deutan_mild', 'confusion_axis_deg': 150.0},
}
ROIS = ['V1', 'V2', 'V3', 'V4']
MODEL = 'ForwardEncoding'  # Only FE (optimal model, MEMORY confirms)
N_COLORS = 8
COLOR_HUE = {i: i * 45.0 for i in range(N_COLORS)}
COLOR_NAME = {0: 'red', 1: 'orange', 2: 'yellow', 3: 'yel-grn',
              4: 'cyan', 5: 'blu-cy', 6: 'blue', 7: 'magenta'}


def circ_mean_deg(angles_deg):
    """Circular mean of signed error angles (in degrees)."""
    if not angles_deg:
        return float('nan')
    s = sum(math.sin(math.radians(a)) for a in angles_deg)
    c = sum(math.cos(math.radians(a)) for a in angles_deg)
    return math.degrees(math.atan2(s, c))


def circ_sd_deg(angles_deg):
    """Circular SD (Fisher 1993) of signed errors."""
    if not angles_deg:
        return float('nan')
    n = len(angles_deg)
    s = sum(math.sin(math.radians(a)) for a in angles_deg) / n
    c = sum(math.cos(math.radians(a)) for a in angles_deg) / n
    r = math.sqrt(s*s + c*c)
    if r < 1e-10:
        return 180.0
    return math.degrees(math.sqrt(-2.0 * math.log(r)))


def axis_alignment_score(signed_err, conf_axis_deg):
    """Cosine-similarity of the pred_hue direction to confusion axis.
    Positive = errors bias toward the confusion axis (expected for CVD).
    Returns mean over all trials of cos(2*(pred_direction - conf_axis))."""
    if not signed_err:
        return float('nan')
    # Each signed_error already encodes direction of confusion relative to true hue.
    # Project onto the confusion axis via doubled-angle (axial data).
    return sum(math.cos(2 * math.radians(a)) for a in signed_err) / len(signed_err)


def main():
    # Load trials
    trials = []
    with CSV_IN.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            if row['model'] != MODEL:
                continue
            if row['subject'] not in CVD:
                continue
            trials.append({
                'sub': row['subject'],
                'roi': row['roi'],
                'true': int(row['test_color_label']),
                'true_hue': float(row['test_hue']),
                'pred': int(row['pred_label']),
                'pred_hue': float(row['pred_hue']),
                'signed_err': float(row['signed_error']),
                'abs_err': float(row['abs_error']),
                'is_corr': int(row['is_correct']),
            })

    # Per subject × ROI confusion (row-normalized probability)
    conf_raw = defaultdict(lambda: [[0]*N_COLORS for _ in range(N_COLORS)])
    sig_err = defaultdict(lambda: defaultdict(list))

    for t in trials:
        key = (t['sub'], t['roi'])
        conf_raw[key][t['true']][t['pred']] += 1
        sig_err[key][t['true']].append(t['signed_err'])

    # Write per subject x ROI confusion + signed-error tables
    for (sub, roi), mat in conf_raw.items():
        # Row-normalize
        conf_prob = []
        for row in mat:
            rs = sum(row)
            conf_prob.append([v / rs if rs > 0 else 0.0 for v in row])
        fp = OUT / f'sub-{sub}_{roi}_confusion.csv'
        with fp.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['true_label', 'true_name'] + [f'pred_{i}_{COLOR_NAME[i]}' for i in range(N_COLORS)])
            for t in range(N_COLORS):
                w.writerow([t, COLOR_NAME[t]] + [f'{v:.4f}' for v in conf_prob[t]])

        # Signed error summary
        fp2 = OUT / f'sub-{sub}_{roi}_signed_error.csv'
        with fp2.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['true_label', 'true_name', 'n_trials', 'n_correct',
                        'accuracy', 'mean_abs_err', 'circ_mean_signed_err',
                        'circ_sd_signed_err', 'axis_alignment_2x'])
            conf_axis = CVD[sub]['confusion_axis_deg']
            for t in range(N_COLORS):
                errs = sig_err[(sub, roi)][t]
                abs_errs = [abs(e) for e in errs]
                n = len(errs)
                n_corr = sum(1 for e in errs if abs(e) < 1e-6)
                # For axis-alignment, compute error direction relative to confusion axis
                align = axis_alignment_score(errs, conf_axis)
                w.writerow([t, COLOR_NAME[t], n, n_corr,
                            f'{n_corr/n if n else 0:.4f}',
                            f'{sum(abs_errs)/n if n else 0:.2f}',
                            f'{circ_mean_deg(errs):.2f}',
                            f'{circ_sd_deg(errs):.2f}',
                            f'{align:.4f}'])

    # Per-subject summary across ROIs (for MD report)
    summary = {sub: {} for sub in CVD}
    for (sub, roi), mat in conf_raw.items():
        per_color = []
        for t in range(N_COLORS):
            row = mat[t]
            rs = sum(row) or 1
            acc = row[t] / rs
            # Top-1 off-diagonal
            off = [(p, c/rs) for p, c in enumerate(row) if p != t]
            off.sort(key=lambda x: -x[1])
            confused_to = off[0][0] if off else t
            confused_prob = off[0][1] if off else 0.0
            errs = sig_err[(sub, roi)][t]
            per_color.append({
                'true': t,
                'true_name': COLOR_NAME[t],
                'accuracy': acc,
                'confused_to': confused_to,
                'confused_to_name': COLOR_NAME[confused_to],
                'confused_to_prob': confused_prob,
                'circ_mean_err': circ_mean_deg(errs),
                'abs_mean_err': sum(abs(e) for e in errs) / len(errs) if errs else 0.0,
            })
        summary[sub][roi] = per_color

    # Write master summary CSV
    fp = OUT / 'cvd_individual_summary.csv'
    with fp.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['subject', 'cvd_subtype', 'roi', 'true_label', 'true_name',
                    'accuracy', 'confused_to_label', 'confused_to_name',
                    'confused_to_prob', 'circ_mean_signed_err', 'mean_abs_err'])
        for sub in sorted(summary):
            sub_type = CVD[sub]['subtype']
            for roi in ROIS:
                for rec in summary[sub].get(roi, []):
                    w.writerow([sub, sub_type, roi, rec['true'], rec['true_name'],
                                f"{rec['accuracy']:.4f}", rec['confused_to'], rec['confused_to_name'],
                                f"{rec['confused_to_prob']:.4f}",
                                f"{rec['circ_mean_err']:.2f}",
                                f"{rec['abs_mean_err']:.2f}"])

    # Write Markdown report
    md = ['# CVD Individual Confusion Report (decoder-LOCO, ForwardEncoding)',
          '',
          f'Source: `{CSV_IN.relative_to(ROOT)}` (11,520 trials total; 48 trials/cell per sub×ROI)',
          '',
          'Per-CVD subject × ROI decoder-LOCO confusion. Each subject is analyzed',
          'independently — no leave-one-subject-out needed (LOCO is already within-subject).',
          '',
          'Columns: accuracy = P(pred=true|true); confused_to = argmax off-diagonal;',
          'confused_to_prob = P(pred=confused_to|true); circ_mean_err = circular mean',
          'of (pred_hue − true_hue) ∈ (−180°, +180°]; positive = CCW / hue-advance.',
          '',
          'Chance exact accuracy = 0.125. Chance mean abs error ≈ 90°.',
          '']

    for sub in sorted(CVD):
        info = CVD[sub]
        md.append(f'## sub-{sub} ({info["subtype"]}, confusion axis ≈ {info["confusion_axis_deg"]:.0f}°)')
        md.append('')
        for roi in ROIS:
            recs = summary[sub].get(roi, [])
            if not recs:
                continue
            md.append(f'### sub-{sub} · {roi}')
            md.append('')
            md.append('| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |')
            md.append('|---|---:|---|---:|---:|---:|')
            for r in recs:
                arrow = f'{r["true_name"]} → {r["confused_to_name"]}' if r['confused_to'] != r['true'] else f'{r["true_name"]} (self)'
                md.append(f'| {r["true"]} {r["true_name"]} | {r["accuracy"]:.2f} | {arrow} | {r["confused_to_prob"]:.2f} | {r["circ_mean_err"]:+.1f} | {r["abs_mean_err"]:.1f} |')
            md.append('')

            # Identify colors where errors systematically align with the confusion axis
            # (|signed_err| large AND direction close to confusion axis or its reverse)
            conf_axis = info['confusion_axis_deg']
            sig_colors = []
            for r in recs:
                # Pred direction in CIELab ring: true_hue + signed_err -> expected confusion if close to conf_axis ± 180
                true_hue = COLOR_HUE[r['true']]
                pred_dir = true_hue + r['circ_mean_err']
                delta_to_axis = min(
                    abs((pred_dir - conf_axis + 180) % 360 - 180),
                    abs((pred_dir - (conf_axis + 180) + 180) % 360 - 180),
                )
                if r['abs_mean_err'] > 45 and delta_to_axis < 30:
                    sig_colors.append(f'{r["true_name"]} (|err|={r["abs_mean_err"]:.0f}°, pred_dir={pred_dir % 360:.0f}°)')
            if sig_colors:
                md.append(f'**Confusion-axis-aligned errors**: {", ".join(sig_colors)}')
                md.append('')

    # Compare sub-08 R+C qualitative report expectations
    md.append('---')
    md.append('')
    md.append('## Cross-reference with sub-08 R+C qualitative report (hV4)')
    md.append('')
    md.append('Sub-08 reported after R+C filter: c3≡c4 merge (yellow / yellow-green),')
    md.append('c5≡c6 merge (cyan / blue-cyan). These map to decoder labels 2≡3 and 4≡5.')
    md.append('')
    md.append('| Predicted merge | HC pooled P(true→conf) | sub-08 V4 P(true→conf) | Sub-08 pooled ROI P(true→conf) |')
    md.append('|---|---|---|---|')
    # Compute HC pooled and sub-08 per (true, pred)
    hc_mat = [[0]*N_COLORS for _ in range(N_COLORS)]
    sub08_mat_all = [[0]*N_COLORS for _ in range(N_COLORS)]
    sub08_mat_v4 = [[0]*N_COLORS for _ in range(N_COLORS)]
    for t in trials:
        sub = t['sub']
        if sub == '08':
            sub08_mat_all[t['true']][t['pred']] += 1
            if t['roi'] == 'V4':
                sub08_mat_v4[t['true']][t['pred']] += 1
    # Load HC via long CSV filter
    with CSV_IN.open() as f:
        for row in csv.DictReader(f):
            if row['model'] != MODEL:
                continue
            if int(row['subject']) <= 7:
                hc_mat[int(row['test_color_label'])][int(row['pred_label'])] += 1

    def prob_row(mat, t, p):
        rs = sum(mat[t])
        return mat[t][p] / rs if rs else 0.0

    for (t, p) in [(2, 3), (3, 2), (4, 5), (5, 4)]:
        md.append(f'| {COLOR_NAME[t]} → {COLOR_NAME[p]} (label {t}→{p}) | '
                  f'{prob_row(hc_mat, t, p):.3f} | '
                  f'{prob_row(sub08_mat_v4, t, p):.3f} | '
                  f'{prob_row(sub08_mat_all, t, p):.3f} |')
    md.append('')
    md.append('_If sub-08 values meaningfully exceed HC pooled P, the decoder-confusion signal supports'
              ' the R+C qualitative report. If not, perceptual merge (stimulus → perception) is decoupled'
              ' from BOLD-decoder confusion (voxel pattern → class)._')
    md.append('')

    md_fp = OUT / 'cvd_individual_report.md'
    md_fp.write_text('\n'.join(md))
    print(f'[ok] MD report: {md_fp}')
    print(f'[ok] summary CSV: {OUT / "cvd_individual_summary.csv"}')
    print(f'[ok] per-(sub, ROI) CSVs: {OUT}/sub-*_{{V1,V2,V3,V4}}_*.csv')


if __name__ == '__main__':
    main()
