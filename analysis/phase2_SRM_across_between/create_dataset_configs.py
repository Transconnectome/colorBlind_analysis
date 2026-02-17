"""
Create standardized config.json files for SRM-aligned datasets.

Reads existing *_srm_results.json and .npy file shapes to generate
config.json with full dataset provenance for downstream traceability.

Usage:
    python create_dataset_configs.py [--results_dir PATH]
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime


def create_config_for_alignment(results_dir: Path, roi_disk: str, alignment: str) -> dict:
    """
    Create config.json for one ROI × alignment combination.

    Parameters
    ----------
    results_dir : Path
        Directory containing SRM results (e.g., results/c010/combined_with_aligned/)
    roi_disk : str
        ROI name on disk (V1, V2, V3, V4)
    alignment : str
        Alignment method: 'procrustes' or 'raw'

    Returns
    -------
    config : dict or None
        Config dict, or None if source files missing
    """
    srm_results_file = results_dir / f"{roi_disk}_{alignment}_srm_results.json"
    npy_file = results_dir / f"{roi_disk}_{alignment}_aligned_amplitudes.npy"

    if not srm_results_file.exists():
        print(f"  SKIP: {srm_results_file.name} not found")
        return None

    # Load SRM results metadata
    with open(srm_results_file) as f:
        srm_results = json.load(f)

    # Load .npy to get shape
    # Format: numpy object array wrapping a dict {subject_id: (8, k) array}
    if npy_file.exists():
        data = np.load(npy_file, allow_pickle=True)
        if data.dtype == object and data.ndim == 0:
            # Dict stored as numpy scalar object
            data_dict = data.item()
            n_subjects = len(data_dict)
            subject_order = list(data_dict.keys())
            first_shape = next(iter(data_dict.values())).shape
            output_shape_per_subject = list(first_shape)
        else:
            # Regular array (n_subjects, 8, k)
            n_subjects = data.shape[0]
            subject_order = None
            output_shape_per_subject = list(data.shape[1:])
    else:
        print(f"  WARNING: {npy_file.name} not found, using metadata only")
        n_subjects = len(srm_results['subjects']['hc']) + len(srm_results['subjects']['cvd'])
        output_shape_per_subject = [8, srm_results['n_features']]
        subject_order = None

    # Map disk name back to canonical ROI name
    roi_canonical = 'hV4' if roi_disk == 'V4' else roi_disk

    config = {
        "alignment_method": srm_results.get("method", f"{alignment}_averaged_srm"),
        "srm_k": srm_results["n_features"],
        "srm_n_iter": 10,
        "srm_training_subjects": srm_results["subjects"]["hc"],
        "srm_projection_subjects": srm_results["subjects"]["cvd"],
        "input_data": "amplitudes_procrustes.npy" if alignment == "procrustes" else "amplitudes_raw.npy",
        "input_source": "phase1_preprocess_decoding/results/full_dataset_C010",
        "output_file": f"{roi_disk}_{alignment}_aligned_amplitudes.npy",
        "output_format": "dict",
        "output_shape_per_subject": output_shape_per_subject,
        "n_subjects": n_subjects,
        "subject_order": subject_order if subject_order else (srm_results["subjects"]["hc"] + srm_results["subjects"]["cvd"]),
        "timestamp": srm_results.get("timestamp", "unknown"),
        "roi": roi_canonical,
        "roi_disk": roi_disk,
        "source_results_json": srm_results_file.name,
        "config_created": datetime.now().isoformat()
    }

    return config


def main(results_dir: Path = None):
    if results_dir is None:
        base = Path(__file__).parent
        results_dir = base / "results" / "c010" / "combined_with_aligned"

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    rois_disk = ['V1', 'V2', 'V3', 'V4']
    alignments = ['procrustes', 'raw']

    created = 0
    for roi_disk in rois_disk:
        for alignment in alignments:
            print(f"Processing {roi_disk} / {alignment}...")
            config = create_config_for_alignment(results_dir, roi_disk, alignment)

            if config is not None:
                out_file = results_dir / f"{roi_disk}_{alignment}_config.json"
                with open(out_file, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"  Created: {out_file.name}")
                created += 1

    print(f"\nDone. Created {created} config.json files in {results_dir}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create config.json for SRM-aligned datasets')
    parser.add_argument('--results_dir', type=str, default=None,
                        help='Path to combined_with_aligned directory')
    args = parser.parse_args()

    results_dir = Path(args.results_dir) if args.results_dir else None
    main(results_dir)
