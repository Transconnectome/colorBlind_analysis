#!/bin/bash
#SBATCH --job-name=dryrun
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/dryrun_smoke_%j.out
#SBATCH --error=logs/dryrun_smoke_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mkdir -p results/redteam/dryrun logs

echo "=== Step 1: verify alpha patch in-script (donor excluded, train=5) ==="
mpirun -np 1 python -c "
import sys
sys.path.insert(0, 'scripts')
import s10b_v6_pca_rdm as v6
HC_ALL = ['sub-01','sub-02','sub-03','sub-04','sub-05','sub-06','sub-07']
print(f'orig v6.HC_SUBJS (len={len(v6.HC_SUBJS)}): {v6.HC_SUBJS}')
print(f'orig SUBSET_SIZE={v6.SUBSET_SIZE}, N_RESAMPLES={v6.N_RESAMPLES}')
donor = 'sub-01'
v6.HC_SUBJS = [h for h in HC_ALL if h != donor]
v6.SUBSET_SIZE = 5
v6.N_RESAMPLES = 1
import numpy as np
rng = np.random.default_rng(0)
sel = rng.choice(len(v6.HC_SUBJS), size=v6.SUBSET_SIZE, replace=False)
subset = [v6.HC_SUBJS[i] for i in sorted(sel)]
complement = [h for h in v6.HC_SUBJS if h not in subset]
print(f'after LOO donor={donor}: HC_SUBJS={v6.HC_SUBJS}')
print(f'  train(subset, n={len(subset)})={subset}')
print(f'  test(complement, n={len(complement)})={complement}')
assert donor not in subset and donor not in complement, 'DONOR LEAK'
assert len(subset)==5, f'train size {len(subset)}!=5'
print('PASS: donor excluded, train=5')
"

echo ""
echo "=== Step 2: param_recovery_voxel (1 candidate, 1 HC, M=1) ==="
mpirun -np 1 python scripts/param_recovery_voxel.py \
    --m-realizations 1 \
    --candidates S08-stable \
    --hc-subset sub-01

echo ""
echo "=== Step 3: null_within_hc_loo (1 candidate, M=1) ==="
mpirun -np 1 python scripts/null_within_hc_loo.py \
    --m-noise 1 \
    --candidates S08-stable

echo ""
echo "=== Step 4: null_label_permutation (1 candidate, N=2) ==="
mpirun -np 1 python scripts/null_label_permutation.py \
    --n-perm 2 \
    --candidates S08-stable

echo "=== DRY-RUN COMPLETE ==="
