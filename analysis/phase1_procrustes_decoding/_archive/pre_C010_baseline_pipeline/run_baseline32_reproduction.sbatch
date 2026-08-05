#!/bin/bash
#SBATCH --job-name=baseline32_repro
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/baseline32_repro_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/baseline32_repro_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --no-requeue

################################################################################
# Baseline32 Reproduction Test
#
# Purpose:
#   Reproduce the Baseline32 configuration that reportedly worked well
#   in the past. This configuration showed "high run reliability" according
#   to CURRENT_STATUS.md.
#
# Baseline32 Settings (from README.md):
#   - Smoothing:    0mm (no smoothing)
#   - High-pass:    0.01 Hz
#   - Motion:       cosine (6 DCT basis functions)
#   - CompCor:      None
#   - Drift:        none (handled by high-pass filter)
#   - Standardize:  False
#
# Hypothesis:
#   If this config shows high RDM correlation:
#   → Motion confounds (cosine) are critical
#   → Or drift=none vs per_run makes difference
#
# Expected:
#   - RDM correlation > 0.3 (vs A1: -0.025)
#   - Classification > 15% (vs A1: 12.5% chance)
################################################################################

set -e
source ~/.bashrc
conda activate nilearn

SUBJECT="01"
ROI="V1"

echo "================================================================================"
echo "Baseline32 Reproduction Test"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo ""
echo "Configuration (Baseline32):"
echo "  Subject:      sub-${SUBJECT}"
echo "  ROI:          ${ROI}"
echo "  Smooth:       0mm"
echo "  Highpass:     0.01 Hz"
echo "  Motion:       cosine (6 DCT basis)"
echo "  CompCor:      0"
echo "  Drift:        none (handled by highpass)"
echo "  Normalize:    none"
echo ""
echo "Comparison target:"
echo "  Past Baseline32: High run reliability ✅ (reported in CURRENT_STATUS.md)"
echo "  Current A1:      run_corr(RDM)=-0.025 ❌"
echo ""
echo "Start time: $(date)"
echo "================================================================================"
echo ""

cd /scratch/connectome/haba6030/colorBlind

# Run with Baseline32 settings
python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset method3_header_mi \
    --smooth 0 \
    --highpass 0.01 \
    --motion cosine \
    --compcor 0 \
    --drift none \
    --normalize-level none \
    --output-dir analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline32_reproduction/sub-${SUBJECT}/${ROI}

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Baseline32 reproduction completed"
    echo ""
    echo "Results location:"
    echo "  analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline32_reproduction/sub-${SUBJECT}/${ROI}/"
    echo ""
    echo "Next steps:"
    echo "  1. Download results to local"
    echo "  2. Run recompute_rdm_all_configs.py to include Baseline32"
    echo "  3. Compare RDM correlation with A1 and other configs"
else
    echo "❌ Baseline32 reproduction failed (exit code: ${EXIT_CODE})"
fi
echo "================================================================================"
echo "End time: $(date)"

exit ${EXIT_CODE}
