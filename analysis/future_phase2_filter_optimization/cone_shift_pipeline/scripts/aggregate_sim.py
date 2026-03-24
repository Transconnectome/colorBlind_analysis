#!/usr/bin/env python3
"""
aggregate_sim.py — Collect and rank Geometry→Function simulation results.

Reads all result.json files from the sim output directory,
builds a ranked summary table, and saves to CSV + summary JSON.

Usage (local, after downloading results):
    python aggregate_sim.py --results_dir results/sim

    python aggregate_sim.py --results_dir results/sim --output summary_sim.csv
"""

import argparse
import json
import numpy as np
import csv
from pathlib import Path


def load_result(combo_dir):
    """Load config.json and result.json from one combination directory."""
    config_path = combo_dir / 'config.json'
    result_path = combo_dir / 'result.json'

    if not config_path.exists() or not result_path.exists():
        return None

    with open(config_path) as f:
        config = json.load(f)
    with open(result_path) as f:
        result = json.load(f)

    return config, result


def extract_row(config, result):
    """Extract a flat summary row from config + result."""
    pa = result['phase_a']
    pc = result['phase_c']
    pb = result['phase_b']

    # LOCO match (per-HC W, primary mode)
    loco = pc.get('loco_match', {})

    row = {
        'subject': config['subject'],
        'cvd_type': config['cvd_type'],
        'roi': config['roi'],
        'model': config['model'],
        'model_df': config['model_df'],
        'metric': config['metric'],

        # Phase A: ΔRDM fitting
        'rdm_pearson_r': pa['best_pearson_r'],
        'rdm_perm_p': pa['perm_p'],
        'rdm_sig': pa['significant'],
        'best_params': pa['best_params'],
        'delta_theta_deg': pa['delta_theta_deg'],

        # Phase B
        'mean_w_available': pb['mean_w_available'],

        # Phase C: LOCO reproduction (per-HC W)
        'loco_spearman': loco.get('spearman_rho', None),
        'loco_perm_p': loco.get('perm_p', None),
        'worst3_overlap': loco.get('worst3_overlap', None),
        'worst3_synthetic': loco.get('worst3_synthetic', None),
        'worst3_observed': loco.get('worst3_observed', None),

        # Phase C: mean-W variant
        'loco_spearman_mean_w': (
            pc['mean_w']['loco_match'].get('spearman_rho', None)
            if pc['mean_w'].get('loco_match') else None
        ),
        'loco_perm_p_mean_w': (
            pc['mean_w']['loco_match'].get('perm_p', None)
            if pc['mean_w'].get('loco_match') else None
        ),

        # Timing
        'elapsed_sec': config.get('elapsed_sec', None),
        'n_voxels': config.get('n_voxels', None),
    }

    return row


def rank_rows(rows, sort_key='loco_spearman', ascending=False):
    """Rank rows by a given key."""
    def key_fn(r):
        val = r.get(sort_key)
        if val is None:
            return -999 if not ascending else 999
        return val
    return sorted(rows, key=key_fn, reverse=not ascending)


def print_summary_table(rows, top_n=10):
    """Print a formatted summary table."""
    print(f'\n{"="*100}')
    print(f'Geometry→Function Simulation: {len(rows)} combinations completed')
    print(f'{"="*100}\n')

    # Phase A summary: ΔRDM fitting
    sig_count = sum(1 for r in rows if r['rdm_sig'])
    print(f'Phase A (ΔRDM fitting): {sig_count}/{len(rows)} significant (p<0.05)')

    # Top by RDM Pearson r
    by_rdm = rank_rows(rows, 'rdm_pearson_r')
    print(f'\nTop {min(top_n, len(by_rdm))} by ΔRDM Pearson r:')
    print(f'  {"Subject":<8} {"ROI":<4} {"Model":<12} {"Metric":<12} '
          f'{"r":>6} {"p":>7} {"sig":>4}')
    print(f'  {"-"*60}')
    for r in by_rdm[:top_n]:
        sig = '*' if r['rdm_sig'] else ''
        print(f'  {r["subject"]:<8} {r["roi"]:<4} {r["model"]:<12} {r["metric"]:<12} '
              f'{r["rdm_pearson_r"]:>6.3f} {r["rdm_perm_p"]:>7.4f} {sig:>4}')

    # Phase C summary: LOCO reproduction
    loco_sig = sum(1 for r in rows
                   if r.get('loco_perm_p') is not None and r['loco_perm_p'] < 0.05)
    print(f'\nPhase C (LOCO match): {loco_sig}/{len(rows)} significant (p<0.05)')

    # Top by LOCO Spearman rho
    by_loco = rank_rows(rows, 'loco_spearman')
    print(f'\nTop {min(top_n, len(by_loco))} by LOCO Spearman ρ:')
    print(f'  {"Subject":<8} {"ROI":<4} {"Model":<12} {"Metric":<12} '
          f'{"ρ":>6} {"p":>7} {"overlap":>8} {"worst3_syn":<30} {"worst3_obs":<30}')
    print(f'  {"-"*110}')
    for r in by_loco[:top_n]:
        rho = r['loco_spearman'] if r['loco_spearman'] is not None else float('nan')
        p = r['loco_perm_p'] if r['loco_perm_p'] is not None else float('nan')
        ov = r['worst3_overlap'] if r['worst3_overlap'] is not None else 0
        sig = '*' if p < 0.05 else ''
        syn = str(r.get('worst3_synthetic', ''))
        obs = str(r.get('worst3_observed', ''))
        print(f'  {r["subject"]:<8} {r["roi"]:<4} {r["model"]:<12} {r["metric"]:<12} '
              f'{rho:>6.3f} {p:>6.4f}{sig} {ov:>5}/3   {syn:<30} {obs:<30}')

    # Both Phase A and C significant
    both_sig = [r for r in rows
                if r['rdm_sig'] and r.get('loco_perm_p') is not None
                and r['loco_perm_p'] < 0.05]
    if both_sig:
        print(f'\nCombinations significant in BOTH Phase A and C ({len(both_sig)}):')
        for r in both_sig:
            print(f'  {r["subject"]} {r["roi"]} {r["model"]} {r["metric"]}: '
                  f'RDM r={r["rdm_pearson_r"]:.3f} p={r["rdm_perm_p"]:.4f}, '
                  f'LOCO ρ={r["loco_spearman"]:.3f} p={r["loco_perm_p"]:.4f}, '
                  f'overlap={r["worst3_overlap"]}/3')
    else:
        print('\nNo combinations significant in both Phase A and C.')

    # Per-subject summary
    print('\n--- Per-Subject Summary ---')
    for sub in sorted(set(r['subject'] for r in rows)):
        sub_rows = [r for r in rows if r['subject'] == sub]
        best = max(sub_rows, key=lambda r: r.get('loco_spearman') or -999)
        print(f'  {sub} ({sub_rows[0]["cvd_type"]}): '
              f'best LOCO ρ={best.get("loco_spearman", 0):.3f} '
              f'({best["roi"]} {best["model"]} {best["metric"]})')


def main():
    parser = argparse.ArgumentParser(description='Aggregate sim results')
    parser.add_argument('--results_dir', required=True, help='Sim results directory')
    parser.add_argument('--output', default=None, help='Output CSV path')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f'ERROR: {results_dir} does not exist')
        return

    # Collect all combo dirs
    rows = []
    for combo_dir in sorted(results_dir.iterdir()):
        if not combo_dir.is_dir():
            continue
        loaded = load_result(combo_dir)
        if loaded is None:
            print(f'  SKIP: {combo_dir.name} (missing files)')
            continue
        config, result = loaded
        row = extract_row(config, result)
        rows.append(row)

    if not rows:
        print('No results found!')
        return

    print(f'Loaded {len(rows)} results from {results_dir}')

    # Print summary
    print_summary_table(rows)

    # Save CSV
    output_csv = Path(args.output) if args.output else results_dir / 'summary.csv'
    csv_fields = [
        'subject', 'cvd_type', 'roi', 'model', 'model_df', 'metric',
        'rdm_pearson_r', 'rdm_perm_p', 'rdm_sig',
        'loco_spearman', 'loco_perm_p', 'worst3_overlap',
        'worst3_synthetic', 'worst3_observed',
        'loco_spearman_mean_w', 'loco_perm_p_mean_w',
        'elapsed_sec', 'n_voxels',
    ]
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
        writer.writeheader()
        for r in rank_rows(rows, 'loco_spearman'):
            writer.writerow(r)

    print(f'\nSaved summary to {output_csv}')

    # Save JSON summary
    output_json = output_csv.with_suffix('.json')
    summary = {
        'n_combos': len(rows),
        'phase_a_sig': sum(1 for r in rows if r['rdm_sig']),
        'phase_c_sig': sum(1 for r in rows
                           if r.get('loco_perm_p') is not None
                           and r['loco_perm_p'] < 0.05),
        'both_sig': sum(1 for r in rows
                        if r['rdm_sig']
                        and r.get('loco_perm_p') is not None
                        and r['loco_perm_p'] < 0.05),
        'rows': rows,
    }
    with open(output_json, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f'Saved JSON to {output_json}')


if __name__ == '__main__':
    main()
