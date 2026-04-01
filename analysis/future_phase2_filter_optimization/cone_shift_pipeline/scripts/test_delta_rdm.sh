#!/bin/bash
# Quick interactive test: cone_1way only, sub-09 only
# Run on server in interactive session to verify imports and data paths
#
# Usage:
#   ssh node3
#   cd /scratch/connectome/haba6030/colorBlind
#   bash analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts/test_delta_rdm.sh

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results/test_sim
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}

echo "=== Test: Step 1 (sub-09, cone_1way only) ==="
/usr/bin/time -v mpirun -np 1 python ${SCRIPT_DIR}/step1_fit_delta_rdm.py \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --metric cosine \
    --models cone_1way \
    --cvd_subjects 09 \
    2>&1

echo ""
echo "=== Test: Step 2 (sub-09, cone_1way V4 validation) ==="
/usr/bin/time -v mpirun -np 1 python ${SCRIPT_DIR}/step2_validate_v4_loco.py \
    --sim_dir ${OUTPUT_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --models cone_1way \
    --cvd_subjects 09 \
    2>&1

echo ""
echo "=== Check outputs ==="
find ${OUTPUT_DIR} -name "*.json" -exec echo {} \; -exec python -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
if 'phase_a' in d:
    pa = d['phase_a']
    print(f'  best_params={pa[\"best_params\"]}, best_loss={pa[\"best_loss\"]:.4f}')
    print(f'  label_perm_p={pa[\"label_perm_p\"]:.4f}')
    if pa.get('baseline_improvement_p'):
        print(f'  baseline_improvement_p={pa[\"baseline_improvement_p\"]:.4f}')
elif 'v4_loco' in d:
    v4 = d['v4_loco']
    print(f'  spearman_rho={v4[\"spearman_rho\"]:.3f}, label_perm_p={v4[\"label_perm_p\"]:.4f}')
" {} \;
