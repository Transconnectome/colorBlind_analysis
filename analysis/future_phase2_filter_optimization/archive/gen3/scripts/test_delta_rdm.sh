#!/bin/bash
# Quick interactive test: cone_1way only, sub-09 only
# Run on server in interactive session to verify imports and data paths
#
# Usage:
#   ssh node2
#   cd /scratch/connectome/haba6030/colorBlind
#   bash analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts/test_delta_rdm.sh

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results/test_sim
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}

echo "=== Step 1: DRDM Fitting (sub-09, cone_1way only) ==="
echo "Start: $(date)"
echo "Memory before:"
free -h | head -2

/usr/bin/time -v mpirun -np 1 python ${SCRIPT_DIR}/fit_cone_shift_delta_rdm.py --output_dir ${OUTPUT_DIR} --baseline_dir ${BASELINE_DIR} --metric cosine --models cone_1way --cvd_subjects 09 2>&1

echo ""
echo "Memory after step1:"
free -h | head -2

echo ""
echo "=== Step 2: V4 LOCO Validation (sub-09, cone_1way) ==="
echo "Start: $(date)"

/usr/bin/time -v mpirun -np 1 python ${SCRIPT_DIR}/validate_cone_shift_v4_loco.py --sim_dir ${OUTPUT_DIR} --output_dir ${OUTPUT_DIR} --baseline_dir ${BASELINE_DIR} --models cone_1way --cvd_subjects 09 2>&1

echo ""
echo "Memory after step2:"
free -h | head -2

echo ""
echo "=== Check outputs ==="
find ${OUTPUT_DIR} -name "*.json" -print
echo ""
echo "=== Done ==="
echo "End: $(date)"
