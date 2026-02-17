#!/bin/bash
# Interactive test: 1 ROI to verify before full array
set -e
source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison

echo "=== Test 2D Interactive: V1 only ==="
/usr/bin/time -v python ${SCRIPT_DIR}/compare_alignment_stability.py --roi V1 2>&1 | tee test_interactive_output.log

echo ""
echo "If successful, submit: sbatch compare_alignment_stability.sbatch"
