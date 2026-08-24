#!/bin/bash
#SBATCH --job-name=nested_adapt
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=logs/nested_adaptive_%j.out
#SBATCH --error=logs/nested_adaptive_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model/results/nested_adaptive
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}
mkdir -p logs

SUBJECTS="01 02 03 04 05 06 07 08 09 10"
ROIS="V1 V2 V3 V4"

for sub in ${SUBJECTS}; do
    for roi in ${ROIS}; do
        echo "=== sub-${sub} | ${roi} ==="
        mpirun -np 1 python ${SCRIPT_DIR}/validate_nested_adaptive_loco.py \
            --subject ${sub} \
            --roi ${roi} \
            --output_dir ${OUTPUT_DIR} \
            --baseline_dir ${BASELINE_DIR} \
            --n_restarts 5 \
            --lambda_spacing 0.1
        echo ""
    done
done

echo "=== ALL DONE ==="
