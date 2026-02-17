"""
Test 1D-ext: Per-Group Disparity Color-Dependency Permutation Test

Purpose:
    Test whether SRM captures color-dependent structure for EACH group separately.
    Supplements existing permutation test (which tests disparity_diff and RDM correlations)
    by adding per-group disparity tests.

Motivation:
    The existing disparity_difference test (CVD_mean - HC_mean, p=0.953) is uninformative
    because shuffling color labels destroys ALL color structure, making the between-group
    difference under null meaningless. Instead, we test:

    1. HC within-group consistency: Are HC subjects more consistent with each other
       (lower HC-to-HC-ref disparity) under true vs. shuffled labels?
    2. CVD within-group consistency: Are CVD subjects more consistent with each other
       (lower CVD-CVD pairwise disparity) under true vs. shuffled labels?

    If both pass → SRM captures meaningful color structure for both groups →
    any HC-CVD difference in observed data is interpretable as a real difference
    in color representation, not an SRM artifact.

Method:
    Same as run_color_permutation_with_srm_retraining.py:
    1. Load ORIGINAL amplitude data (6 runs × 8 colors × n_voxels)
    2. Average across runs → (8 colors × n_voxels)
    3. For each permutation:
       - Shuffle color labels in ORIGINAL data
       - Train SRM on shuffled data
       - Compute PER-GROUP metrics in newly learned SRM space
    4. Compare observed per-group metrics to null distributions

    Key difference: metrics are per-group (not group-difference).

Expected:
    Under TRUE labels + SRM: subjects with similar color vision agree more → LOWER disparity
    Under SHUFFLED labels + SRM: no consistent structure → HIGHER disparity
    Therefore: observed within-group disparity < null distribution → color-dependency confirmed
    p-value direction: P(null ≤ observed) should be small
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.linalg import orthogonal_procrustes
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr

# Import shared functions from existing permutation script
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from run_color_permutation_with_srm_retraining import (
    load_baseline_amplitudes,
    permute_color_labels,
    compute_procrustes_disparity,
    compute_rdm,
    HC_SUBJECTS,
    CVD_SUBJECTS,
    ROIS,
    SRM_K_VALUES,
)


def compute_pergroup_metrics(hc_patterns: list, cvd_patterns: list) -> dict:
    """
    Compute per-group disparity and RDM metrics (not group differences).

    Uses leave-one-out (LOO) references to avoid self-referencing bias:
    - HC: for subject i, reference = mean of OTHER 6 HC subjects
    - CVD: for subject i, reference = mean of OTHER 2 CVD subjects

    Parameters
    ----------
    hc_patterns : list
        List of HC patterns, each (8, k)
    cvd_patterns : list
        List of CVD patterns, each (8, k)

    Returns
    -------
    metrics : dict
    """
    hc_arr = np.array(hc_patterns)  # (n_hc, 8, k)
    n_hc = len(hc_patterns)

    # HC LOO disparities: subject i vs mean of other (n-1) HC subjects
    hc_loo_disps = []
    for i in range(n_hc):
        others = np.delete(hc_arr, i, axis=0)  # (n_hc-1, 8, k)
        loo_ref = others.mean(axis=0)           # (8, k)
        hc_loo_disps.append(compute_procrustes_disparity(hc_patterns[i], loo_ref))

    # CVD LOO disparities: subject i vs mean of other CVD subjects
    cvd_loo_disps = []
    if len(cvd_patterns) > 1:
        cvd_arr = np.array(cvd_patterns)  # (n_cvd, 8, k)
        for i in range(len(cvd_patterns)):
            others = np.delete(cvd_arr, i, axis=0)
            loo_ref = others.mean(axis=0)
            cvd_loo_disps.append(compute_procrustes_disparity(cvd_patterns[i], loo_ref))

    # CVD within-group pairwise disparities (kept for comparison)
    cvd_pairwise_disps = []
    for i in range(len(cvd_patterns)):
        for j in range(i + 1, len(cvd_patterns)):
            cvd_pairwise_disps.append(
                compute_procrustes_disparity(cvd_patterns[i], cvd_patterns[j])
            )

    # RDM correlations (within-group)
    hc_rdms = [compute_rdm(p) for p in hc_patterns]
    cvd_rdms = [compute_rdm(p) for p in cvd_patterns]
    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)

    hc_rdm_corrs = []
    for i in range(len(hc_rdms)):
        for j in range(i + 1, len(hc_rdms)):
            r, _ = spearmanr(hc_rdms[i][mask], hc_rdms[j][mask])
            if np.isfinite(r):
                hc_rdm_corrs.append(r)

    cvd_rdm_corrs = []
    for i in range(len(cvd_rdms)):
        for j in range(i + 1, len(cvd_rdms)):
            r, _ = spearmanr(cvd_rdms[i][mask], cvd_rdms[j][mask])
            if np.isfinite(r):
                cvd_rdm_corrs.append(r)

    return {
        'hc_loo_disp_mean': float(np.mean(hc_loo_disps)),
        'cvd_loo_disp_mean': float(np.mean(cvd_loo_disps)) if cvd_loo_disps else float('nan'),
        'cvd_pairwise_disp_mean': float(np.mean(cvd_pairwise_disps)) if cvd_pairwise_disps else float('nan'),
        'hc_rdm_corr': float(np.mean(hc_rdm_corrs)) if hc_rdm_corrs else 0.0,
        'cvd_rdm_corr': float(np.mean(cvd_rdm_corrs)) if cvd_rdm_corrs else 0.0,
        'per_subject_hc_loo_disp': [float(d) for d in hc_loo_disps],
        'per_subject_cvd_loo_disp': [float(d) for d in cvd_loo_disps],
    }


def run_single_pergroup_permutation(hc_amplitudes_list: list, cvd_amplitudes_list: list,
                                     roi: str, k: int, seed: int) -> dict:
    """
    Run a single permutation: shuffle labels → train SRM → compute per-group metrics.

    Same SRM retraining as existing script, but returns per-group metrics.
    """
    # Shuffle color labels for all subjects (same seeding as existing script)
    hc_shuffled = [permute_color_labels(amp, seed=seed + i)
                   for i, amp in enumerate(hc_amplitudes_list)]
    cvd_shuffled = [permute_color_labels(amp, seed=seed + 100 + i)
                    for i, amp in enumerate(cvd_amplitudes_list)]

    try:
        from brainiak.funcalign.srm import SRM

        # Prepare SRM input (transpose to n_voxels × n_colors)
        all_srm_input = [amp.T for amp in (hc_shuffled + cvd_shuffled)]

        # Train SRM on all shuffled subjects
        srm = SRM(n_iter=10, features=k)
        srm.fit(all_srm_input)

        # Transform all subjects
        all_aligned = srm.transform(all_srm_input)

        # Split back into HC and CVD, transpose to (8, k)
        n_hc = len(hc_shuffled)
        hc_aligned = [arr.T for arr in all_aligned[:n_hc]]
        cvd_aligned = [arr.T for arr in all_aligned[n_hc:]]

        # Compute per-group metrics
        return compute_pergroup_metrics(hc_aligned, cvd_aligned)

    except Exception as e:
        print(f"  WARNING: Permutation {seed} failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_pergroup_permutation_test(baseline_dir: Path, output_dir: Path,
                                   roi: str, n_permutations: int = 100):
    """
    Run per-group disparity permutation test for a single ROI.

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline amplitudes (full_dataset_C010)
    output_dir : Path
        Output directory for results
    roi : str
        ROI name (V1, V2, V3, hV4)
    n_permutations : int
        Number of permutations
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / f"{roi}_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    k = SRM_K_VALUES[roi]

    print(f"\n{'=' * 80}")
    print(f"Per-Group Disparity Permutation Test - {roi} (k={k})")
    print(f"{'=' * 80}")
    print(f"Permutations: {n_permutations}")
    print(f"Method: Shuffle labels → Retrain SRM → Per-group metrics")
    print(f"Tests: HC LOO disparity, CVD LOO disparity, CVD pairwise disparity")
    print()

    # Load baseline amplitudes
    print("Loading baseline amplitudes...")
    hc_amplitudes_list = []
    cvd_amplitudes_list = []

    for subject in HC_SUBJECTS:
        try:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            amp_mean = amp.mean(axis=0)  # (8, n_voxels)
            hc_amplitudes_list.append(amp_mean)
            print(f"  Loaded {subject}: {amp_mean.shape}")
        except Exception as e:
            print(f"  WARNING: Could not load {subject}: {e}")

    for subject in CVD_SUBJECTS:
        try:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            amp_mean = amp.mean(axis=0)  # (8, n_voxels)
            cvd_amplitudes_list.append(amp_mean)
            print(f"  Loaded {subject}: {amp_mean.shape}")
        except Exception as e:
            print(f"  WARNING: Could not load {subject}: {e}")

    if len(hc_amplitudes_list) < 6 or len(cvd_amplitudes_list) < 2:
        raise ValueError(f"Insufficient data: HC={len(hc_amplitudes_list)}, CVD={len(cvd_amplitudes_list)}")

    # ---- Compute observed metrics (true labels) ----
    print("\nComputing observed metrics (true labels)...")
    from brainiak.funcalign.srm import SRM

    all_srm_input_obs = [amp.T for amp in (hc_amplitudes_list + cvd_amplitudes_list)]
    srm_obs = SRM(n_iter=10, features=k)
    srm_obs.fit(all_srm_input_obs)
    all_aligned_obs = srm_obs.transform(all_srm_input_obs)

    n_hc = len(hc_amplitudes_list)
    hc_aligned_obs = [arr.T for arr in all_aligned_obs[:n_hc]]
    cvd_aligned_obs = [arr.T for arr in all_aligned_obs[n_hc:]]

    observed = compute_pergroup_metrics(hc_aligned_obs, cvd_aligned_obs)

    print(f"  HC LOO disp mean:               {observed['hc_loo_disp_mean']:.4f}")
    print(f"  CVD LOO disp mean:              {observed['cvd_loo_disp_mean']:.4f}")
    print(f"  CVD pairwise disp mean:         {observed['cvd_pairwise_disp_mean']:.4f}")
    print(f"  HC RDM corr:                    {observed['hc_rdm_corr']:.3f}")
    print(f"  CVD RDM corr:                   {observed['cvd_rdm_corr']:.3f}")
    print(f"  Per-subject HC LOO disp:        {observed['per_subject_hc_loo_disp']}")
    print(f"  Per-subject CVD LOO disp:       {observed['per_subject_cvd_loo_disp']}")

    # ---- Permutation loop ----
    print(f"\nRunning {n_permutations} permutations...")
    print("  (Each permutation retrains SRM)")

    null_hc_loo_disp = []
    null_cvd_loo_disp = []
    null_cvd_pairwise_disp = []
    null_hc_rdm = []
    null_cvd_rdm = []
    null_per_subject_hc = {i: [] for i in range(n_hc)}
    null_per_subject_cvd = {i: [] for i in range(len(cvd_amplitudes_list))}

    for perm_i in range(n_permutations):
        if (perm_i + 1) % 10 == 0:
            print(f"  Permutation {perm_i + 1}/{n_permutations}")

        seed = 42 + perm_i * 1000
        metrics = run_single_pergroup_permutation(
            hc_amplitudes_list, cvd_amplitudes_list, roi, k, seed
        )

        if metrics is not None:
            null_hc_loo_disp.append(metrics['hc_loo_disp_mean'])
            null_cvd_loo_disp.append(metrics['cvd_loo_disp_mean'])
            null_cvd_pairwise_disp.append(metrics['cvd_pairwise_disp_mean'])
            null_hc_rdm.append(metrics['hc_rdm_corr'])
            null_cvd_rdm.append(metrics['cvd_rdm_corr'])

            for i, d in enumerate(metrics['per_subject_hc_loo_disp']):
                null_per_subject_hc[i].append(d)
            for i, d in enumerate(metrics['per_subject_cvd_loo_disp']):
                null_per_subject_cvd[i].append(d)

    null_hc_loo_disp = np.array(null_hc_loo_disp)
    null_cvd_loo_disp = np.array(null_cvd_loo_disp)
    null_cvd_pairwise_disp = np.array(null_cvd_pairwise_disp)
    null_hc_rdm = np.array(null_hc_rdm)
    null_cvd_rdm = np.array(null_cvd_rdm)

    n_successful = len(null_hc_loo_disp)

    # ---- Compute p-values ----
    # Disparity: lower = more consistent → P(null <= observed) should be small
    p_hc_loo_disp = np.mean(null_hc_loo_disp <= observed['hc_loo_disp_mean'])
    p_cvd_loo_disp = np.mean(null_cvd_loo_disp <= observed['cvd_loo_disp_mean'])
    p_cvd_pairwise_disp = np.mean(null_cvd_pairwise_disp <= observed['cvd_pairwise_disp_mean'])

    # RDM correlation: higher = more consistent → P(null >= observed) should be small
    p_hc_rdm = np.mean(null_hc_rdm >= observed['hc_rdm_corr'])
    p_cvd_rdm = np.mean(null_cvd_rdm >= observed['cvd_rdm_corr'])

    # Per-subject p-values (LOO disparity, one-tailed: P(null <= observed))
    per_subject_hc_pvals = []
    for i, obs_d in enumerate(observed['per_subject_hc_loo_disp']):
        null_arr = np.array(null_per_subject_hc[i])
        p = np.mean(null_arr <= obs_d) if len(null_arr) > 0 else float('nan')
        per_subject_hc_pvals.append(float(p))

    per_subject_cvd_pvals = []
    for i, obs_d in enumerate(observed['per_subject_cvd_loo_disp']):
        null_arr = np.array(null_per_subject_cvd[i])
        p = np.mean(null_arr <= obs_d) if len(null_arr) > 0 else float('nan')
        per_subject_cvd_pvals.append(float(p))

    # ---- Build interpretation ----
    hc_pass = p_hc_loo_disp < 0.05
    cvd_ref_pass = p_cvd_loo_disp < 0.05
    cvd_pair_pass = p_cvd_pairwise_disp < 0.05
    cvd_pass = cvd_ref_pass or cvd_pair_pass
    if hc_pass and cvd_pass:
        interpretation = ("Both HC and CVD show color-dependent within-group consistency "
                          "-> SRM captures meaningful color structure for both groups")
    elif hc_pass:
        interpretation = ("HC shows color-dependent consistency but CVD does not "
                          "-> CVD group may lack shared color structure")
    elif cvd_pass:
        interpretation = ("CVD shows color-dependent consistency but HC does not "
                          "-> unexpected, may indicate insufficient HC sample")
    else:
        interpretation = ("Neither group shows color-dependent within-group consistency "
                          "-> SRM may not capture color structure reliably")

    # ---- Store results ----
    results = {
        'roi': roi,
        'k': k,
        'n_permutations': n_permutations,
        'n_successful': n_successful,
        'observed': {
            'hc_loo_disp_mean': observed['hc_loo_disp_mean'],
            'cvd_loo_disp_mean': observed['cvd_loo_disp_mean'],
            'cvd_pairwise_disp_mean': observed['cvd_pairwise_disp_mean'],
            'hc_rdm_corr': observed['hc_rdm_corr'],
            'cvd_rdm_corr': observed['cvd_rdm_corr'],
            'per_subject_hc_loo_disp': observed['per_subject_hc_loo_disp'],
            'per_subject_cvd_loo_disp': observed['per_subject_cvd_loo_disp'],
        },
        'p_values': {
            'hc_loo_disp_mean': float(p_hc_loo_disp),
            'cvd_loo_disp_mean': float(p_cvd_loo_disp),
            'cvd_pairwise_disp_mean': float(p_cvd_pairwise_disp),
            'hc_rdm_corr': float(p_hc_rdm),
            'cvd_rdm_corr': float(p_cvd_rdm),
            'per_subject_hc_loo_disp': per_subject_hc_pvals,
            'per_subject_cvd_loo_disp': per_subject_cvd_pvals,
        },
        'null_distributions': {
            'hc_loo_disp_mean': null_hc_loo_disp.tolist(),
            'cvd_loo_disp_mean': null_cvd_loo_disp.tolist(),
            'cvd_pairwise_disp_mean': null_cvd_pairwise_disp.tolist(),
            'hc_rdm_corr': null_hc_rdm.tolist(),
            'cvd_rdm_corr': null_cvd_rdm.tolist(),
        },
        'null_means': {
            'hc_loo_disp_mean': float(np.mean(null_hc_loo_disp)) if n_successful > 0 else None,
            'cvd_loo_disp_mean': float(np.mean(null_cvd_loo_disp)) if n_successful > 0 else None,
            'cvd_pairwise_disp_mean': float(np.mean(null_cvd_pairwise_disp)) if n_successful > 0 else None,
            'hc_rdm_corr': float(np.mean(null_hc_rdm)) if n_successful > 0 else None,
            'cvd_rdm_corr': float(np.mean(null_cvd_rdm)) if n_successful > 0 else None,
        },
        'interpretation': interpretation,
        'test_description': {
            'hc_loo_disp_mean': 'LOO: each HC subject vs mean of other 6 HC (lower=better)',
            'cvd_loo_disp_mean': 'LOO: each CVD subject vs mean of other 2 CVD (lower=better)',
            'cvd_pairwise_disp_mean': 'Mean CVD-CVD pairwise disparity (3 pairs, lower=better)',
            'hc_rdm_corr': 'Mean within-HC pairwise RDM Spearman correlation (higher=better)',
            'cvd_rdm_corr': 'Mean within-CVD pairwise RDM Spearman correlation (higher=better)',
            'p_direction_disparity': 'P(null <= observed): small p means observed disparity is lower than null',
            'p_direction_rdm': 'P(null >= observed): small p means observed correlation is higher than null',
        },
        'subjects': {
            'hc': HC_SUBJECTS[:n_hc],
            'cvd': CVD_SUBJECTS[:len(cvd_amplitudes_list)],
        },
        'timestamp': datetime.now().isoformat(),
    }

    # Save results
    out_file = results_dir / 'pergroup_disparity_permutation_results.json'
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)

    # ---- Print summary ----
    print(f"\n{'=' * 80}")
    print(f"RESULTS SUMMARY - {roi}")
    print(f"{'=' * 80}")
    print(f"Successful permutations: {n_successful}/{n_permutations}")

    print(f"\nPer-Group LOO Disparity Tests (lower observed = color-dependent consistency):")
    print(f"  HC LOO disp mean:     {observed['hc_loo_disp_mean']:.4f} vs null {np.mean(null_hc_loo_disp):.4f}  p={p_hc_loo_disp:.4f}  {'PASS' if hc_pass else 'FAIL'}")
    print(f"  CVD LOO disp mean:    {observed['cvd_loo_disp_mean']:.4f} vs null {np.mean(null_cvd_loo_disp):.4f}  p={p_cvd_loo_disp:.4f}  {'PASS' if cvd_ref_pass else 'FAIL'}")
    print(f"  CVD pairwise mean:    {observed['cvd_pairwise_disp_mean']:.4f} vs null {np.mean(null_cvd_pairwise_disp):.4f}  p={p_cvd_pairwise_disp:.4f}  {'PASS' if cvd_pair_pass else 'FAIL'}")

    print(f"\nRDM Correlation Tests (higher observed = color-dependent structure):")
    print(f"  HC RDM corr:  {observed['hc_rdm_corr']:.3f} vs null {np.mean(null_hc_rdm):.3f}  p={p_hc_rdm:.4f}")
    print(f"  CVD RDM corr: {observed['cvd_rdm_corr']:.3f} vs null {np.mean(null_cvd_rdm):.3f}  p={p_cvd_rdm:.4f}")

    print(f"\nPer-Subject HC LOO Disparities:")
    for i, (subj, d, p) in enumerate(zip(HC_SUBJECTS[:n_hc], observed['per_subject_hc_loo_disp'], per_subject_hc_pvals)):
        print(f"  {subj}: {d:.4f}  p={p:.4f}")

    print(f"\nPer-Subject CVD LOO Disparities:")
    for i, (subj, d, p) in enumerate(zip(CVD_SUBJECTS[:len(cvd_amplitudes_list)],
                                          observed['per_subject_cvd_loo_disp'],
                                          per_subject_cvd_pvals)):
        print(f"  {subj}: {d:.4f}  p={p:.4f}")

    print(f"\nInterpretation: {interpretation}")
    print(f"\nResults saved to: {out_file}")

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Per-group disparity color-dependency permutation test')
    parser.add_argument('--roi', type=str, required=True, choices=ROIS,
                        help='ROI to analyze')
    parser.add_argument('--n_permutations', type=int, default=100,
                        help='Number of permutations (default: 100 for testing)')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory')
    args = parser.parse_args()

    # Paths - detect local vs server
    local_base = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    server_base = Path('/scratch/connectome/haba6030/colorBlind')

    if local_base.exists():
        base_dir = local_base
        baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
    elif server_base.exists():
        base_dir = server_base
        baseline_dir = base_dir / 'derivatives' / 'full_dataset_C010'
    else:
        base_dir = Path(__file__).parent.parent.parent.parent
        baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if args.output_dir is None:
        output_dir = (base_dir / 'analysis' / 'phase2_SRM_across_between' /
                      'validation' / '1D_permutation' / 'results_pergroup')
    else:
        output_dir = Path(args.output_dir)

    results = run_pergroup_permutation_test(baseline_dir, output_dir,
                                             args.roi, args.n_permutations)

    print("\nPer-group disparity permutation test completed!")
