#!/bin/bash
#SBATCH --job-name=s09grid
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/s09grid_%A_%a.out
#SBATCH --error=logs/s09grid_%A_%a.err
#SBATCH --array=0-1

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

mkdir -p logs results/axis_3way

# sub-09 protan grid extension to resolve β_c boundary hit
# Conditions: Stockman 16°, CIELab 11.8° with β_c ∈ [-80, +80]
THETAS=( 16.0       11.8       )
TAGS=(   Stockman16ext CIELab11p8ext )

TH=${THETAS[$SLURM_ARRAY_TASK_ID]}
TAG=${TAGS[$SLURM_ARRAY_TASK_ID]}

echo "=== sub-09 protan θ_conf=${TH}° tag=${TAG} ==="
echo "Host: $(hostname)  Start: $(date)"

python scripts/subject_axis_refit.py \
    --subject 09 --family protan --theta_conf ${TH} \
    --bs_min 0 --bs_max 80 \
    --bc_min -80 --bc_max 80 --step 2 \
    --tag ${TAG}

mv results/sub09_protan_refit/sub-09_V4_${TAG}_landscape.json \
   results/axis_3way/sub-09_V4_${TAG}_landscape.json 2>/dev/null || true

echo "=== End: $(date) ==="
