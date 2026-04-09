#!/usr/bin/env python3
"""
step1_validate_cone_mapping.py — Cone->Hue expressiveness validation.

Validates the physics-based cone shift models before fitting:
  1. delta_theta vs delta_lambda curve (1-way and 3-way)
  2. Error distribution: full spectral vs matrix method
  3. Color-order preservation: critical delta_lambda threshold

Runs locally (conda env: srm).

Usage:
    python scripts/step1_validate_cone_mapping.py \
        --output_dir results/step1_cone_validation \
        --fig_dir figures
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from utils_cone_3way import (
    compute_1way_hue_shift,
    compute_shifted_hue_3way,
    compute_shifted_hue_full_spectral,
    compute_shifted_hue_matrix,
    HUE_ANGLES_DEG,
    COLOR_NAMES,
)

CVD_TYPES = ['deutan', 'protan']
MAX_SHIFT = 60
STEP = 1


def validation_1_delta_curves(output):
    """Validation 1: delta_theta vs delta_lambda curves."""
    print('[V1] Computing delta_theta vs delta_lambda curves...')
    results = {}

    for cvd_type in CVD_TYPES:
        curves = {'delta_lambda': [], 'delta_theta': [], 'hue_shifted': []}
        for dl in range(0, MAX_SHIFT + 1, STEP):
            _, hue_s, dt = compute_1way_hue_shift(float(dl), cvd_type)
            curves['delta_lambda'].append(dl)
            curves['delta_theta'].append(dt.tolist())
            curves['hue_shifted'].append(hue_s.tolist())

        # Also 3-way with only the affected cone
        curves_3way = {'delta_lambda': [], 'delta_theta': []}
        for dl in range(0, MAX_SHIFT + 1, STEP):
            if cvd_type == 'deutan':
                _, _, dt3 = compute_shifted_hue_3way(0, float(dl), 0)
            else:
                _, _, dt3 = compute_shifted_hue_3way(float(-dl), 0, 0)
            curves_3way['delta_lambda'].append(dl)
            curves_3way['delta_theta'].append(dt3.tolist())

        results[cvd_type] = {
            '1way': curves,
            '3way_single': curves_3way,
        }

    output['validation_1'] = results
    print('  Done.')


def validation_2_spectral_error(output):
    """Validation 2: Full spectral vs matrix method error."""
    print('[V2] Computing spectral vs matrix approximation error...')
    results = {}

    for cvd_type in CVD_TYPES:
        errors = {'delta_lambda': [], 'max_error_deg': [], 'mean_error_deg': [],
                  'per_color_error': []}
        for dl in range(0, MAX_SHIFT + 1, STEP):
            _, _, dt_full = compute_shifted_hue_full_spectral(float(dl), cvd_type)
            _, _, dt_matrix = compute_shifted_hue_matrix(float(dl), cvd_type)
            err = np.abs(dt_full - dt_matrix)
            errors['delta_lambda'].append(dl)
            errors['max_error_deg'].append(float(np.max(err)))
            errors['mean_error_deg'].append(float(np.mean(err)))
            errors['per_color_error'].append(err.tolist())

        results[cvd_type] = errors

    output['validation_2'] = results
    print('  Done.')


def validation_3_order_preservation(output):
    """Validation 3: Critical delta_lambda where color order breaks."""
    print('[V3] Checking color-order preservation...')
    results = {}

    for cvd_type in CVD_TYPES:
        critical_dl = None
        for dl in range(0, MAX_SHIFT + 1, STEP):
            _, hue_s, _ = compute_1way_hue_shift(float(dl), cvd_type)
            # Check if sorted order is preserved
            original_order = np.argsort(HUE_ANGLES_DEG)
            shifted_order = np.argsort(hue_s)
            if not np.array_equal(original_order, shifted_order):
                critical_dl = dl
                break

        results[cvd_type] = {
            'critical_delta_lambda': critical_dl,
            'order_preserved_up_to': (critical_dl - STEP) if critical_dl else MAX_SHIFT,
        }

    output['validation_3'] = results
    for cvd_type, r in results.items():
        crit = r['critical_delta_lambda']
        if crit:
            print(f'  {cvd_type}: order breaks at delta_lambda={crit} nm')
        else:
            print(f'  {cvd_type}: order preserved up to {MAX_SHIFT} nm')


def plot_validation(output, fig_dir):
    """Generate validation figures."""
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: delta_theta vs delta_lambda
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, cvd_type in enumerate(CVD_TYPES):
        ax = axes[idx]
        data = output['validation_1'][cvd_type]['1way']
        dls = data['delta_lambda']
        dts = np.array(data['delta_theta'])  # (N, 8)
        for c in range(8):
            ax.plot(dls, dts[:, c], label=COLOR_NAMES[c])
        ax.set_xlabel('delta_lambda (nm)')
        ax.set_ylabel('delta_theta (degrees)')
        ax.set_title(f'{cvd_type}: 1-way cone shift')
        ax.legend(fontsize=7, ncol=2)
        ax.axhline(0, color='gray', ls='--', lw=0.5)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_dir / 'cone_validation_v1_curves.png', dpi=150)
    plt.close()

    # Figure 2: Spectral vs matrix error
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, cvd_type in enumerate(CVD_TYPES):
        ax = axes[idx]
        data = output['validation_2'][cvd_type]
        ax.plot(data['delta_lambda'], data['max_error_deg'], 'r-', label='Max error')
        ax.plot(data['delta_lambda'], data['mean_error_deg'], 'b-', label='Mean error')
        ax.set_xlabel('delta_lambda (nm)')
        ax.set_ylabel('Error (degrees)')
        ax.set_title(f'{cvd_type}: full spectral vs matrix error')
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_dir / 'cone_validation_v2_error.png', dpi=150)
    plt.close()

    # Figure 3: 1-way vs 3-way comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, cvd_type in enumerate(CVD_TYPES):
        ax = axes[idx]
        d1 = output['validation_1'][cvd_type]['1way']
        d3 = output['validation_1'][cvd_type]['3way_single']
        dt1 = np.array(d1['delta_theta'])
        dt3 = np.array(d3['delta_theta'])
        # Plot max absolute shift across colors
        ax.plot(d1['delta_lambda'], np.max(np.abs(dt1), axis=1),
                'b-', label='1-way max|dt|')
        ax.plot(d3['delta_lambda'], np.max(np.abs(dt3), axis=1),
                'r--', label='3-way single max|dt|')
        ax.set_xlabel('delta_lambda (nm)')
        ax.set_ylabel('Max |delta_theta| (degrees)')
        ax.set_title(f'{cvd_type}: 1-way vs 3-way (single cone)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_dir / 'cone_validation_v3_1way_vs_3way.png', dpi=150)
    plt.close()

    print(f'  Figures saved to {fig_dir}/')


def main():
    parser = argparse.ArgumentParser(description='Step 1: Cone mapping validation')
    parser.add_argument('--output_dir', type=str,
                        default='results/step1_cone_validation')
    parser.add_argument('--fig_dir', type=str, default='figures')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Step 1: Cone -> Hue Expressiveness Validation')
    print('=' * 60)

    output = {'timestamp': datetime.now().isoformat()}

    validation_1_delta_curves(output)
    validation_2_spectral_error(output)
    validation_3_order_preservation(output)

    # Gate check
    for cvd_type in CVD_TYPES:
        crit = output['validation_3'][cvd_type]['critical_delta_lambda']
        if crit and crit < 20:
            print(f'\n  WARNING: {cvd_type} color order breaks at {crit} nm < 20 nm!')
            print('  Consider revising model bounds.')

    # Save results
    out_path = output_dir / 'step1_cone_validation.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nResults saved to {out_path}')

    # Plot
    plot_validation(output, args.fig_dir)

    print('\nStep 1 complete.')


if __name__ == '__main__':
    main()
