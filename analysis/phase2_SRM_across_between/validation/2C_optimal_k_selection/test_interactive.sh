#!/bin/bash
# Interactive test: 1 fold, 1 ROI to verify before full array
set -e
source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2C_optimal_k_selection

echo "=== Test 2C Interactive: Fold=0, V1 only ==="
/usr/bin/time -v python ${SCRIPT_DIR}/run_k_selection_cv.py --fold 0 --roi V1 2>&1 | tee test_interactive_output.log

echo ""
echo "If successful, submit: sbatch run_k_selection_cv.sbatch"
