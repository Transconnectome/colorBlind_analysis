#!/bin/bash
#SBATCH --job-name=bsonly150
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/bsonly150_%A_%a.out
#SBATCH --error=logs/bsonly150_%A_%a.err
#SBATCH --array=0-2

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

mkdir -p logs results/axis_3way

# Task 0: sub-08 β_s only (β_c=0 forced, axis 90° trivially since β_c=0)
# Task 1: sub-09 β_s only
# Task 2: sub-09 axis=150° 2D fine (mechanism verification — was OLD wrong P2a-best by chance?)
SIDS=(   08 09 09 )
FAMS=(   deutan protan protan )
THETAS=( 150.0 150.0 150.0 )    # for tasks 0/1 axis doesn't matter (β_c=0); for 2 it's the wrong-axis verification
BSMINS=( 0 0 0 )
BSMAXS=( 100 100 50 )
BCMINS=( 0 0 -60 )
BCMAXS=( 0 0 60 )
STEPS=(  2 2 2 )
TAGS=( bs_only bs_only axis150_fine )

I=$SLURM_ARRAY_TASK_ID
SID=${SIDS[$I]}
FAM=${FAMS[$I]}
TH=${THETAS[$I]}
TAG=${TAGS[$I]}

echo "=== array=$I sub-${SID} ${FAM} θ_conf=${TH}° tag=${TAG} ==="
echo "Grid: β_s [${BSMINS[$I]}, ${BSMAXS[$I]}]  β_c [${BCMINS[$I]}, ${BCMAXS[$I]}]  step=${STEPS[$I]}"
echo "Host: $(hostname)  Start: $(date)"

python scripts/subject_axis_refit.py \
    --subject ${SID} --family ${FAM} --theta_conf ${TH} \
    --bs_min ${BSMINS[$I]} --bs_max ${BSMAXS[$I]} \
    --bc_min ${BCMINS[$I]} --bc_max ${BCMAXS[$I]} --step ${STEPS[$I]} \
    --tag ${TAG}

mv results/sub09_protan_refit/sub-${SID}_V4_${TAG}_landscape.json \
   results/axis_3way/sub-${SID}_V4_${TAG}_landscape.json 2>/dev/null || true

echo "=== End: $(date) ==="
