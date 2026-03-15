#!/bin/bash
#SBATCH --job-name=dimensionality
#SBATCH --output=logs/dimensionality_%j.out
#SBATCH --error=logs/dimensionality_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# Dimensionality Analysis Pipeline (RT-5 Resolution)
# Runs eigenspectrum decay + MEME estimator sequentially
# Framework: Pospisil & Pillow (2024)

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"

mkdir -p logs
mkdir -p results/dimensionality/eigenspectrum
mkdir -p results/dimensionality/meme

echo "========================================================================"
echo "Dimensionality Analysis Pipeline"
echo "Question: Is CVD genuinely reduced-dimensional? (RT-5)"
echo "========================================================================"
echo

echo "=== Step 1/2: Eigenspectrum Decay Analysis ==="
echo "Framework: Pospisil & Pillow (2024) broken power law"
echo "Output: results/dimensionality/eigenspectrum/"
echo

python scripts/dimensionality/analyze_eigenspectrum_decay.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/dimensionality/eigenspectrum" \
    --n_early 10 \
    --n_late 50

if [ $? -ne 0 ]; then
    echo "ERROR: Eigenspectrum analysis failed"
    exit 1
fi

echo
echo "=== Step 2/2: MEME Dimensionality Estimator ==="
echo "Framework: Li et al. (2014), Pospisil (2024)"
echo "Output: results/dimensionality/meme/"
echo

python scripts/dimensionality/fit_meme_eigenspectrum.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/dimensionality/meme" \
    --n_moments 3 \
    --noise_percentile 95

if [ $? -ne 0 ]; then
    echo "ERROR: MEME analysis failed"
    exit 1
fi

echo
echo "========================================================================"
echo "Dimensionality Analysis Complete"
echo "========================================================================"
echo "Results:"
echo "  - Eigenspectrum: results/dimensionality/eigenspectrum/eigenspectrum_results.json"
echo "  - MEME: results/dimensionality/meme/meme_results.json"
echo
echo "Next steps:"
echo "  1. Check eigenspectrum: α_early vs α_late (broken power law?)"
echo "  2. Compare MEME k* to manual SRM k (V1=4, V2=4, V3=3, hV4=3)"
echo "  3. Test HC vs CVD: k*_CVD < k*_HC? (biological dimensionality reduction)"
echo "  4. Update RESULTS.md Section 11-12 with actual values"
echo
