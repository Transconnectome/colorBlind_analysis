#!/bin/bash
#SBATCH --job-name=drdm_fit
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=4:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=logs/drdm_fit_%j.log
#SBATCH --error=logs/drdm_fit_%j.err

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results/sim
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/logs

echo "=== Step 1: DRDM Fitting (V1+V2) ==="
echo "Start: $(date)"
free -h | head -2

mpirun -np 1 python ${SCRIPT_DIR}/fit_cone_shift_delta_rdm.py --output_dir ${OUTPUT_DIR} --baseline_dir ${BASELINE_DIR} --metric cosine --models cone_1way cone_3way fourier --cvd_subjects 08 09 10

echo ""
echo "Memory after step1:"
free -h | head -2

echo ""
echo "=== Step 2: V4 LOCO Validation ==="
echo "Start: $(date)"

mpirun -np 1 python ${SCRIPT_DIR}/validate_cone_shift_v4_loco.py --sim_dir ${OUTPUT_DIR} --output_dir ${OUTPUT_DIR} --baseline_dir ${BASELINE_DIR} --models cone_1way cone_3way fourier --cvd_subjects 08 09 10

echo ""
echo "=== All done ==="
echo "End: $(date)"
free -h | head -2
