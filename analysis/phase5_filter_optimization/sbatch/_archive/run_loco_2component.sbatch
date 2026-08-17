#!/bin/bash
#SBATCH --job-name=loco_2comp
#SBATCH --output=logs/loco_2comp_%j.out
#SBATCH --error=logs/loco_2comp_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# LOCO Filter Phase A: 2-Component model (beta_s + beta_c)
#
# Fits the 2-component angular dilation model to LOCO vulnerability.
# Grid: 26 x 51 = 1326 points (comparable to R+C's 1025).
#
# Jobs:
#   1. sub-08 hV4 shift_at_both  (~11 min)
#   2. sub-09 hV4 shift_at_both  (~11 min)
#   3. sub-08 V1  w_fixed        (~13 s)
#   4. sub-09 V1  w_fixed        (~13 s)
#   5. sub-10 V1  w_fixed        (~13 s, specificity null)
#
# Estimated total: ~23 min. Time limit 1h is safe margin.
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/phase_a_2component

echo "=============================================================="
echo "  LOCO Filter Phase A: 2-Component Model -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

python -c "import numpy, scipy, sklearn; print('OK: numpy', numpy.__version__)" \
    || { echo "ERROR: missing packages"; exit 1; }

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=results/loco_filter/phase_a_2component

# --- Sub-08 hV4 shift_at_both (primary: deutan, compare R+C p=0.005) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-08 hV4 shift_at_both -- 2component"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 08 --roi V4 --method shift_at_both \
    --models 2component \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-09 hV4 shift_at_both (secondary: protan, compare Machado p=0.018) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-09 hV4 shift_at_both -- 2component"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 09 --roi V4 --method shift_at_both \
    --models 2component \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-08 V1 w_fixed (cross-validate ΔRDM p=0.053) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-08 V1 w_fixed -- 2component"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 08 --roi V1 --method w_fixed \
    --models 2component \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-09 V1 w_fixed (cross-validate ΔRDM p=0.007***) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-09 V1 w_fixed -- 2component"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 09 --roi V1 --method w_fixed \
    --models 2component \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-10 V1 w_fixed (specificity null) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-10 V1 w_fixed -- 2component (specificity null)"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 10 --roi V1 --method w_fixed \
    --models 2component \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

echo ""
echo "=============================================================="
echo "  Phase A 2-Component finished -- $(date)"
echo "  Results: ${OUT_DIR}/"
echo "=============================================================="
