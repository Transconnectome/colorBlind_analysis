#!/bin/bash
# Interactive test: 1 ROI to verify before full array
set -e
source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1C_split_half

echo "=== Test 1C Interactive: V1 only ==="
/usr/bin/time -v python ${SCRIPT_DIR}/run_split_half_srm.py --roi V1 2>&1 | tee test_interactive_output.log

echo ""
echo "If successful, submit: sbatch run_split_half_srm.sbatch"
