#!/bin/bash
# Interactive test: Run 1 fold, 1 ROI to verify before full array job
# Usage: bash test_interactive.sh

set -e

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1B_loso_stability

echo "=== Test 1B Interactive: Single fold test ==="
echo "Testing fold=0 (leave out sub-01), ROI=V1"

/usr/bin/time -v mpirun -np 1 python ${SCRIPT_DIR}/run_loso_srm.py --fold 0 --roi V1 2>&1 | tee test_interactive_output.log

echo ""
echo "=== Check output ==="
echo "Peak memory (see 'Maximum resident set size' above)"
echo "If successful, submit full job: sbatch run_loso_srm.sbatch"
