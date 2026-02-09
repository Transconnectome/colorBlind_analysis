#!/bin/bash
# Run C010 Between-Subject SRM Analysis Locally
#
# This runs all 4 ROIs sequentially on local machine.
# Each ROI runs dual pipeline (raw + procrustes SRM).
#
# Usage:
#   cd /path/to/SRM/
#   bash run_c010_between_subject_local.sh

set -e

echo "======================================"
echo "C010 Between-Subject SRM - Local Run"
echo "======================================"
echo ""
echo "Running 4 ROIs × 2 methods = 8 analyses"
echo "Subjects: HC (n=7), CVD (n=3)"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate srm environment
echo "Activating conda environment: srm"
source ~/.bashrc
conda activate srm
echo "Environment activated: $CONDA_DEFAULT_ENV"
echo ""

# Run each ROI
for roi in V1 V2 V3 V4; do
    echo "======================================"
    echo "Processing ROI: $roi"
    echo "======================================"
    echo ""

    python evaluate_srm_c010_between_subject.py --roi $roi

    echo ""
    echo "Completed: $roi"
    echo ""
done

echo "======================================"
echo "All ROIs completed!"
echo "======================================"
echo ""
echo "Results saved to: results/c010/"
echo ""
echo "Next steps:"
echo "1. Review results in results/c010/TIMESTAMP/"
echo "2. Run visualization: python visualize_srm_c010_between_subject.py"
