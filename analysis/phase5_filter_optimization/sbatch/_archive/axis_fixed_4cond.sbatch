#!/bin/bash
#SBATCH --job-name=ax4cond
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/ax4cond_%A_%a.out
#SBATCH --error=logs/ax4cond_%A_%a.err
#SBATCH --array=0-3

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

mkdir -p logs results/axis_3way

# 4 conditions: sub-08 deutan × {Stockman 150°, CIELab 175.7°}
#               sub-09 protan × {Stockman 16°, CIELab 11.8°}
SUBJECTS=(08    08      09       09)
FAMILIES=(deutan deutan protan   protan)
THETAS=(  150.0  175.7  16.0     11.8)
TAGS=(    Stockman150 CIELab175p7 Stockman16 CIELab11p8)

SID=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}
FAM=${FAMILIES[$SLURM_ARRAY_TASK_ID]}
TH=${THETAS[$SLURM_ARRAY_TASK_ID]}
TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}

echo "=== sub-${SID} ${FAM} θ_conf=${TH}° tag=${TAG} ==="
echo "Host: $(hostname)  Start: $(date)"

python scripts/subject_axis_refit.py \
    --subject ${SID} --family ${FAM} --theta_conf ${TH} \
    --bs_min 0 --bs_max 50 \
    --bc_min -60 --bc_max 60 --step 2 \
    --tag ${TAG}

# Move result to dedicated dir
mv results/sub09_protan_refit/sub-${SID}_V4_${TAG}_landscape.json \
   results/axis_3way/sub-${SID}_V4_${TAG}_landscape.json 2>/dev/null || true

echo "=== End: $(date) ==="
