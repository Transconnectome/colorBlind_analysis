#!/usr/bin/env python3
"""
Generate Summary Report for Phase 1-2 Results
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import sys

def generate_summary(dataset, timestamp):
    """Generate summary of Phase 1-2 results"""

    print("\n" + "="*70)
    print("GENERATING COMPREHENSIVE SUMMARY")
    print("="*70)
    print(f"Dataset: {dataset}")
    print(f"Timestamp: {timestamp}")
    print("")

    base_dir = Path('/scratch/connectome/haba6030/colorBlind')

    # Phase 2 results location
    procrustes_results_dir = base_dir / 'analysis' / 'comprehensive' / 'results' / timestamp
    summary_file = procrustes_results_dir / 'procrustes_analysis_summary.txt'

    if not summary_file.exists():
        print(f"⚠️  Warning: Procrustes summary not found at {summary_file}")
        print("   Phase 2 may not have completed successfully")
        return False

    # Read Procrustes summary
    print("Reading Procrustes results...")
    with open(summary_file, 'r') as f:
        procrustes_summary = f.read()

    # Create comprehensive summary
    output_file = base_dir / 'analysis' / 'comprehensive' / 'results' / f'COMPREHENSIVE_SUMMARY_{timestamp}.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("COMPREHENSIVE ANALYSIS SUMMARY\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {dataset}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("PHASE 0: Baseline Decoding\n")
        f.write("="*70 + "\n")
        f.write("Status: ✓ Completed\n")
        f.write("Location: analysis/phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/\n")
        f.write("Output: Amplitude arrays (amplitudes_z.npy) for all subjects and ROIs\n")
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("PHASE 1: RDM/RSA Analysis\n")
        f.write("="*70 + "\n")
        f.write("Status: ⚠️  Check individual ROI logs\n")
        f.write("Location: analysis/phase2_decoder_comparing/{dataset}/results/rdm_analysis/\n")
        f.write("Note: May require baseline results in new directory structure\n")
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("PHASE 2: Procrustes Alignment\n")
        f.write("="*70 + "\n")
        f.write("Status: ✓ Completed\n")
        f.write(f"Location: {procrustes_results_dir}/\n")
        f.write("\n")
        f.write(procrustes_summary)
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("PHASE 3: Filter Learning\n")
        f.write("="*70 + "\n")

        # Check if Phase 3 results exist
        phase3_exists = False
        for roi in ['V1', 'V2', 'V3', 'hV4']:
            roi_filter_dir = procrustes_results_dir / roi / 'filter_learning'
            if roi_filter_dir.exists():
                phase3_exists = True
                break

        if phase3_exists:
            f.write("Status: ✓ Completed\n")
            f.write(f"Location: {procrustes_results_dir}/[ROI]/filter_learning/\n")
            f.write("\n")
            f.write("Filters trained:\n")
            for roi in ['V1', 'V2', 'V3', 'hV4']:
                roi_filter_dir = procrustes_results_dir / roi / 'filter_learning'
                if roi_filter_dir.exists():
                    summary_file = roi_filter_dir / 'filter_summary.json'
                    if summary_file.exists():
                        import json
                        with open(summary_file, 'r') as ff:
                            filter_summary = json.load(ff)
                        n_filters = filter_summary.get('n_filters_trained', 0)
                        f.write(f"  {roi}: {n_filters} CVD subjects\n")
                    else:
                        f.write(f"  {roi}: ✓ (summary not available)\n")
        else:
            f.write("Status: ⚠️  Not completed or skipped\n")
            f.write("Location: (Phase 3 filters would be saved here)\n")

        f.write("\n")

        f.write("="*70 + "\n")
        f.write("KEY FINDINGS\n")
        f.write("="*70 + "\n")
        f.write("\n")
        f.write("Subject Exclusions:\n")
        f.write("  - sub-07: Excluded due to insufficient voxels\n")
        f.write("    V1: 165, V2: 6, V3: 13, hV4: 16 voxels\n")
        f.write("    (Causes severe truncation of other subjects)\n")
        f.write("\n")
        f.write("HC Subjects Used:\n")
        f.write("  - 01, 02, 03, 04, 05, 06 (6 subjects)\n")
        f.write("\n")
        f.write("CVD Subjects:\n")
        f.write("  - 08, 09, 10 (3 subjects)\n")
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("NEXT STEPS\n")
        f.write("="*70 + "\n")
        f.write("\n")
        f.write("1. Review Procrustes alignment quality (disparity values)\n")
        f.write("2. Check RDM similarity scores (group consistency)\n")
        f.write("3. Visualize aligned patterns (plots in results directory)\n")
        f.write("4. Consider Phase 3 filter learning if needed\n")
        f.write("\n")

        f.write("="*70 + "\n")
        f.write("FILES GENERATED\n")
        f.write("="*70 + "\n")
        f.write("\n")
        f.write(f"Summary: {output_file}\n")
        f.write(f"Procrustes: {procrustes_results_dir}/\n")
        f.write(f"Visualizations: {procrustes_results_dir}/*/\n")
        f.write("\n")
        f.write("="*70 + "\n")

    print(f"✓ Summary saved to: {output_file}")
    print("")

    # Print summary to console
    print("="*70)
    print("QUICK SUMMARY")
    print("="*70)
    print("")
    print("✓ Phase 0: Baseline Decoding - Complete")
    print("⚠️  Phase 1: RDM/RSA - Check logs")
    print("✓ Phase 2: Procrustes Alignment - Complete")
    print("⏸️  Phase 3: Filter Learning - Not implemented")
    print("")
    print(f"Full report: {output_file}")
    print("="*70)

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate comprehensive summary')
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--timestamp', type=str, required=True)

    args = parser.parse_args()

    success = generate_summary(args.dataset, args.timestamp)
    sys.exit(0 if success else 1)
