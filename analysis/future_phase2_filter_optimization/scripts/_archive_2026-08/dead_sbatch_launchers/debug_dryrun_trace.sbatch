#!/bin/bash
#SBATCH --job-name=dbg_trace
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/dbg_trace_%j.out
#SBATCH --error=logs/dbg_trace_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mpirun -np 1 python << 'PYEOF'
import sys, traceback
sys.path.insert(0, 'scripts')

# Replicate param_recovery_voxel single-cell call but with traceback
import s10b_v6_pca_rdm as v6
from neural_loss import load_amplitudes as _load_amps, ROI_K
from behav_loss import load_jnd_per_pair as _load_jnd
from forward_voxel_synth import (precompute_per_hc_W, estimate_noise_per_hc,
                                  synthesize_voxel_response)
sys.path.insert(0, '../future_phase1_forward_model/scripts')
from utils_forward_model import create_basis_full, HUE_ANGLES
import numpy as np

HC_ALL = ['sub-01','sub-02','sub-03','sub-04','sub-05','sub-06','sub-07']
v6.SUBSET_SIZE = 5
v6.N_RESAMPLES = 1
hc_k = 'sub-01'
subject_label = 'sub-08'
family = 'deutan'
combo_label = 'γALL|RDMV1|noLOCO'
gt_bs, gt_bc = 38.0, -10.0

# Pre-load
all_hc_amps = {}
for hc in HC_ALL:
    all_hc_amps[hc] = {}
    for roi in v6.ROIS:
        try:
            amp = _load_amps(hc, roi)
            if roi == 'V4' and amp.shape[2] < 20:
                continue
            all_hc_amps[hc][roi] = amp
        except Exception:
            pass
all_hc_jnd = {hc: _load_jnd(hc) for hc in HC_ALL}
original_hc_jnd_subjs = list(v6.HC_JND_SUBJS)

# Build fake amps via per-hc W synthesis
rng = np.random.default_rng(0)
donor_amps = all_hc_amps[hc_k]
fake_amps = {}
for roi in v6.ROIS:
    if roi not in donor_amps:
        continue
    K = ROI_K[roi]
    C_b = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    W_dict = precompute_per_hc_W({hc_k: donor_amps[roi]}, C_b)
    if hc_k not in W_dict:
        continue
    W_k = W_dict[hc_k]
    noise = estimate_noise_per_hc(donor_amps[roi], W_k, C_b)
    Y_synth = synthesize_voxel_response(
        W_k=W_k, beta_s=gt_bs, beta_c=gt_bc, family=family,
        theta_canonical=HUE_ANGLES.astype(float),
        noise_params=noise, rng=rng)
    fake_amps[roi] = Y_synth
print(f'fake_amps ROIs: {list(fake_amps.keys())}')

# pool excl donor
pool = {roi: {h: all_hc_amps[h][roi] for h in HC_ALL
              if h != hc_k and roi in all_hc_amps[h]}
        for roi in v6.ROIS}
print(f'pool sizes per ROI: {[(r, len(pool[r])) for r in pool]}')

# Monkey-patch
o_amps, o_hc, o_jnd = v6.load_amplitudes, v6.load_hc_pool, v6.load_jnd_per_pair
o_jnd_subjs = list(v6.HC_JND_SUBJS)
o_hc_subjs = list(v6.HC_SUBJS)
fake_jnd = dict(all_hc_jnd[hc_k])

def p_amps(sid, roi):
    if sid == subject_label:
        return fake_amps.get(roi)
    return None  # NOTE: this is the param_recovery version
def p_hc(roi):
    return dict(pool.get(roi, {}))
def p_jnd(sid):
    if sid == subject_label:
        return fake_jnd
    return all_hc_jnd.get(sid)

v6.load_amplitudes = p_amps
v6.load_hc_pool = p_hc
v6.load_jnd_per_pair = p_jnd
v6.HC_SUBJS = [h for h in HC_ALL if h != hc_k]
v6.HC_JND_SUBJS = [h for h in original_hc_jnd_subjs if h != hc_k]

try:
    storage = v6.fit_subject(subject_label)
    print('FIT OK')
    print('storage keys:', list(storage.keys())[:5])
    if combo_label in storage:
        b = storage[combo_label]
        print(f'block keys: {list(b.keys())}')
        if '2comp' in b and b['2comp']:
            print(f'2comp[0]: {b["2comp"][0]}')
except Exception as e:
    print(f'FIT FAILED: {type(e).__name__}: {e}')
    traceback.print_exc()
PYEOF
