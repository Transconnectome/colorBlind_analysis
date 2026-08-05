#!/bin/bash

# Deployment Verification Script
# Checks that all required files exist before uploading to server

echo "=================================================="
echo "Post-Procrustes Analysis Deployment Verification"
echo "=================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERRORS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc"
        echo "   $file"
        return 0
    else
        echo -e "${RED}✗${NC} $desc"
        echo "   Missing: $file"
        ((ERRORS++))
        return 1
    fi
}

check_dir() {
    local dir=$1
    local desc=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $desc"
        echo "   $dir"
        return 0
    else
        echo -e "${RED}✗${NC} $desc"
        echo "   Missing: $dir"
        ((ERRORS++))
        return 1
    fi
}

# Check directory structure
echo "=== Directory Structure ==="
check_dir "$SCRIPT_DIR" "Main scripts directory"
check_dir "$SCRIPT_DIR/utils" "Utils directory"
check_dir "$SCRIPT_DIR/sbatch" "SBATCH directory"
echo ""

# Check Phase 1: Noise Ceiling
echo "=== Phase 1: Noise Ceiling Files ==="
check_file "$SCRIPT_DIR/utils/noise_ceiling.py" "Noise ceiling utilities"
check_file "$SCRIPT_DIR/evaluate_with_noise_ceiling.py" "Phase 1 evaluation script"
check_file "$SCRIPT_DIR/sbatch/run_noise_ceiling_evaluation.sbatch" "Phase 1 SBATCH script"
echo ""

# Check Phase 2: Whitening + SNR
echo "=== Phase 2: Whitening + SNR Files ==="
check_file "$SCRIPT_DIR/utils/whitening.py" "Whitening utilities"
check_file "$SCRIPT_DIR/evaluate_whitening_ceiling_snr.py" "Phase 2 evaluation script"
check_file "$SCRIPT_DIR/sbatch/run_whitening_ceiling_evaluation.sbatch" "Phase 2 SBATCH script"
echo ""

# Check Phase 3: SRM (optional)
echo "=== Phase 3: SRM Files (Optional) ==="
check_file "$SCRIPT_DIR/utils/srm_alignment.py" "SRM utilities"
echo -e "${YELLOW}ℹ${NC} Note: SRM evaluation script not yet created (Phase 3)"
echo ""

# Check Phase 4: Visualization
echo "=== Phase 4: Visualization Files ==="
check_file "$SCRIPT_DIR/utils/rdm_visualization.py" "RDM visualization utilities"
echo ""

# Check prerequisite baseline script
echo "=== Prerequisite: Baseline with Residuals ==="
check_file "$SCRIPT_DIR/sbatch/run_baseline_with_residuals.sbatch" "Baseline+residuals SBATCH"
echo ""

# Check documentation
echo "=== Documentation ==="
check_file "$SCRIPT_DIR/sbatch/README.md" "SBATCH README"
PLAN_FILE="/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/PostProcrustes_plan_0130.md"
check_file "$PLAN_FILE" "Master plan document"
echo ""

# Count Python lines
echo "=== Code Statistics ==="
if [ -d "$SCRIPT_DIR/utils" ]; then
    UTILS_LINES=$(find "$SCRIPT_DIR/utils" -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')
    echo "Utils modules: $UTILS_LINES lines"
fi

if [ -f "$SCRIPT_DIR/evaluate_with_noise_ceiling.py" ] && [ -f "$SCRIPT_DIR/evaluate_whitening_ceiling_snr.py" ]; then
    EVAL_LINES=$(wc -l "$SCRIPT_DIR/evaluate_with_noise_ceiling.py" "$SCRIPT_DIR/evaluate_whitening_ceiling_snr.py" | tail -1 | awk '{print $1}')
    echo "Evaluation scripts: $EVAL_LINES lines"
fi

echo ""

# Summary
echo "=== Deployment Readiness ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All required files present!${NC}"
    echo ""
    echo "Ready to deploy. Suggested upload command:"
    echo ""
    echo "scp -r $SCRIPT_DIR/utils $SCRIPT_DIR/sbatch $SCRIPT_DIR/evaluate_*.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/"
    echo ""
    echo "After upload, run:"
    echo "  cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
    echo "  sbatch sbatch/run_noise_ceiling_evaluation.sbatch"
    echo "  sbatch sbatch/run_whitening_ceiling_evaluation.sbatch"
else
    echo -e "${RED}✗ Found $ERRORS missing files/directories${NC}"
    echo ""
    echo "Please resolve missing files before deployment."
fi

echo "=================================================="

exit $ERRORS
