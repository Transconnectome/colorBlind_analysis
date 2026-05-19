#!/bin/bash
#SBATCH --job-name=repro_BEST
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/repro_BEST_%j.out
#SBATCH --error=logs/repro_BEST_%j.err

# Verify Phase 2 BEST reproducibility on server (nilearn env, node2)
# Per user 2026-05-19: confirm canonical fit (38, -14)/(6, -22) was server output.
# Records env info + h_base + per-subject (β_s, β_c).

set -e
source ~/.bashrc
conda activate nilearn

OUT_DIR=results/reproduce_canonical_BEST
mkdir -p ${OUT_DIR} logs

echo "===================================================================="
echo "Phase 2 BEST reproducibility check"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Conda env: ${CONDA_DEFAULT_ENV}"
echo "===================================================================="

# Record env versions
echo
echo "=== Environment versions ==="
python3 -c "
import numpy, scipy
print(f'numpy: {numpy.__version__}')
print(f'scipy: {scipy.__version__}')
try:
    import colour
    print(f'colour-science: {colour.__version__}')
except ImportError:
    print('colour-science: NOT INSTALLED')
" | tee ${OUT_DIR}/env_versions.txt

# Record h_base output (this is the critical reproducibility value)
echo
echo "=== Live h_base output (machado_shifted_hue) ==="
python3 -c "
import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, 'scripts/forward_models')
from forward_models.two_component import H_BASE_CANONICAL_8, USE_FROZEN_H_BASE
from machado_simulator import machado_shifted_hue
import numpy as np

print(f'USE_FROZEN_H_BASE = {USE_FROZEN_H_BASE}')
print(f'Frozen H_BASE_CANONICAL_8 = {H_BASE_CANONICAL_8.tolist()}')

for fam in ['deutan', 'protan']:
    h_live, _, _ = machado_shifted_hue(0.0, fam)
    print(f'Live machado_shifted_hue(0.0, {fam!r}) = {[round(h,4) for h in h_live]}')
    if USE_FROZEN_H_BASE:
        diff = np.array(h_live) - H_BASE_CANONICAL_8
        print(f'  Diff from canonical = {[round(d,3) for d in diff]}')
        print(f'  Max abs diff = {np.max(np.abs(diff)):.4f}°')
" | tee ${OUT_DIR}/h_base_check.txt

# Run canonical fit for sub-08 and sub-09 V4
for sid in 08 09; do
    echo
    echo "=== sub-${sid} V4 2component canonical fit ==="
    python3 scripts/loco_distortion_fit.py \
        --subject ${sid} \
        --roi V4 \
        --method shift_at_both \
        --models 2component \
        --output_dir ${OUT_DIR}/sub-${sid} 2>&1 | tee ${OUT_DIR}/sub-${sid}_fit.log
done

# Compare to canonical BEST_summary
echo
echo "=== Reproducibility verdict ==="
python3 -c "
import json
canonical = {
    '08': {'expected_bs': 38.0, 'expected_bc': -14.0},
    '09': {'expected_bs':  6.0, 'expected_bc': -22.0},
}
for sid, exp in canonical.items():
    p = f'${OUT_DIR}/sub-{sid}/sub-{sid}_V4_2component.json'
    d = json.load(open(p))
    bs, bc = d['best_params']
    match = (bs == exp['expected_bs']) and (bc == exp['expected_bc'])
    sym = '✓ REPRODUCED' if match else f'✗ MISMATCH (got {bs}, {bc})'
    print(f'sub-{sid}: expected ({exp[\"expected_bs\"]}, {exp[\"expected_bc\"]}); {sym}')
" | tee ${OUT_DIR}/verdict.txt

echo
echo "All outputs saved to: ${OUT_DIR}/"
