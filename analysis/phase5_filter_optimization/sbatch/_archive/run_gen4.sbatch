#!/bin/bash
#SBATCH --job-name=gen4_cone_shift
#SBATCH --output=logs/gen4_cone_shift_%j.out
#SBATCH --error=logs/gen4_cone_shift_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# Resource sizing rationale (K ≤ 6, V ≈ 300–1000, 8 colors):
#   • Matrices are tiny → BLAS with >4 threads is SLOWER (sync overhead).
#     Sweet spot = 4 OpenBLAS threads.
#   • Peak memory ≲ 2 GB (HC amps + W caches + 2-D L₃ grids).
#     16 GB leaves a ~8× safety margin.
#   • The bottleneck is Stage 3a scipy Spearman perm loops (~1.45M iters,
#     single-threaded Python). Realistic wall time 1–2 h; 4 h is safe.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Gen-4 Machado-Anchored Cone-Shift Pipeline (L3 fine-tune) — SLURM entry
#
# Runs stages 0..4 sequentially on a single node2 CPU node. BrainIAK calls
# MPI_Init_thread on import so every python invocation is wrapped in
# `mpirun -np 1` (see MEMORY.md BrainIAK MPI Fix).
#
# Stage order:
#   step0_precompute        — HC W + ΔRDM_obs + Stockman cache
#   step1_machado_anchor    — coarse Δλ grid per (subj, ROI, model)
#   step2_finetune_l3       — narrow joint V1+V2 L3 fine-tune + 8! null
#   step3_validate_neural   — hV4 LOCO transfer (held out)
#   step3_validate_cognition— Machado canonical agreement
#   step4_summary           — summary_table.csv + matplotlib figures
#
# Submission (from project root on node3/login):
#   sbatch analysis/phase5_filter_optimization/cone_shift_pipeline/sbatch/run_gen4.sbatch
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results

echo "=============================================================="
echo "  Gen-4 Cone-Shift Pipeline — $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "  CPUs/task : ${SLURM_CPUS_PER_TASK}"
echo "  Mem       : ${SLURM_MEM_PER_NODE} MB"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

# Verify key environment
python -c "import numpy, scipy, sklearn, brainiak; print('numpy', numpy.__version__, '/ brainiak', brainiak.__version__)" \
    || { echo "ERROR: nilearn env missing expected packages"; exit 1; }

# --- stage 0 --------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 0 — precompute"
mpirun -np 1 python scripts/step0_precompute.py \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/step0_precompute

# --- stage 1 --------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 1 — Machado coarse anchor"
mpirun -np 1 python scripts/step1_machado_anchor.py \
    --step0_dir results/step0_precompute \
    --output_dir results/step1_machado_anchor \
    --models machado_1way machado_alpha_free cone_3way

# --- stage 2 --------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 2 — joint V1+V2 L3 fine-tune"
mpirun -np 1 python scripts/step2_finetune_l3.py \
    --step0_dir results/step0_precompute \
    --step1_dir results/step1_machado_anchor \
    --output_dir results/step2_finetune_l3 \
    --models machado_1way machado_alpha_free

# --- stage 3a -------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 3a — NEURAL validation (hV4 held out)"
mpirun -np 1 python scripts/step3_validate_neural.py \
    --step0_dir results/step0_precompute \
    --step2_dir results/step2_finetune_l3 \
    --output_dir results/step3_neural \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --models machado_1way machado_alpha_free

# --- stage 3b -------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 3b — COGNITION validation (Machado agreement)"
mpirun -np 1 python scripts/step3_validate_cognition.py \
    --step0_dir results/step0_precompute \
    --step2_dir results/step2_finetune_l3 \
    --output_dir results/step3_cognition \
    --models machado_1way machado_alpha_free

# --- stage 4 --------------------------------------------------------------
echo ""
echo "[$(date +%H:%M:%S)]  Stage 4 — summary + figures"
mpirun -np 1 python scripts/step4_summary.py \
    --step1_dir results/step1_machado_anchor \
    --step2_dir results/step2_finetune_l3 \
    --step3_neural_dir results/step3_neural \
    --step3_cognition_dir results/step3_cognition \
    --output_dir results/step4_summary

echo ""
echo "=============================================================="
echo "  Gen-4 pipeline finished — $(date)"
echo "  Summary CSV : results/step4_summary/summary_table.csv"
echo "  Figures     : results/step4_summary/figures/"
echo "=============================================================="
