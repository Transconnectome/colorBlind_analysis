#!/bin/bash
# Quick interactive test: sub-08 hV4, fourier DE to verify DE works
# Run on server: bash scripts/test_loco_filter.sh
set -eo pipefail

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=results/loco_filter/phase_a_test

mkdir -p ${OUT_DIR}

echo "=== Quick test: sub-08 hV4 fourier_warp DE ==="
/usr/bin/time -v mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 08 --roi V4 --method shift_at_both \
    --models fourier_warp \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR} \
    2>&1 | tee ${OUT_DIR}/test_output.log

echo ""
echo "=== Test done. Check: ${OUT_DIR}/ ==="
