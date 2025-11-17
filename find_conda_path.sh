#!/bin/bash
################################################################################
# find_conda_path.sh
################################################################################
#
# Diagnostic script to find conda installation path
# Run this on the SERVER to identify correct conda setup
#
# Usage:
#   bash find_conda_path.sh
#
################################################################################

echo "========================================================================"
echo "Conda Diagnostic Report"
echo "========================================================================"
echo ""

# 1. Check if conda command is available
echo "[1/6] Checking if 'conda' command is available..."
if command -v conda &> /dev/null; then
    echo "✓ conda is available"
    which conda
    conda --version
else
    echo "✗ conda command not found in PATH"
fi
echo ""

# 2. Check common conda.sh locations
echo "[2/6] Checking common conda.sh locations..."
CONDA_SH_LOCATIONS=(
    "/opt/ohba/anaconda/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "/opt/anaconda3/etc/profile.d/conda.sh"
    "/usr/local/anaconda3/etc/profile.d/conda.sh"
    "/anaconda3/etc/profile.d/conda.sh"
)

FOUND_CONDA_SH=""
for path in "${CONDA_SH_LOCATIONS[@]}"; do
    if [ -f "$path" ]; then
        echo "✓ FOUND: $path"
        FOUND_CONDA_SH="$path"
    else
        echo "✗ Not found: $path"
    fi
done
echo ""

# 3. Search for conda.sh in common directories
echo "[3/6] Searching for conda.sh in file system..."
find /opt -name "conda.sh" 2>/dev/null | head -5
find $HOME -name "conda.sh" 2>/dev/null | head -5
echo ""

# 4. Check .bashrc for conda initialization
echo "[4/6] Checking .bashrc for conda init..."
if [ -f "$HOME/.bashrc" ]; then
    echo "✓ .bashrc exists"
    if grep -q "conda initialize" "$HOME/.bashrc"; then
        echo "✓ Found conda initialization in .bashrc:"
        grep -A 10 "conda initialize" "$HOME/.bashrc" | head -15
    else
        echo "✗ No conda initialization found in .bashrc"
    fi
else
    echo "✗ .bashrc not found"
fi
echo ""

# 5. Try to source conda and list environments
echo "[5/6] Attempting to activate conda..."
if [ -n "$FOUND_CONDA_SH" ]; then
    echo "Using: $FOUND_CONDA_SH"
    source "$FOUND_CONDA_SH"
    echo "✓ Successfully sourced conda.sh"
    echo ""
    echo "Available conda environments:"
    conda env list
elif [ -f "$HOME/.bashrc" ]; then
    echo "Trying .bashrc approach..."
    source "$HOME/.bashrc"
    if command -v conda &> /dev/null; then
        echo "✓ conda available after sourcing .bashrc"
        echo ""
        echo "Available conda environments:"
        conda env list
    else
        echo "✗ conda still not available"
    fi
else
    echo "✗ Cannot activate conda"
fi
echo ""

# 6. Check for nilearn environment
echo "[6/6] Checking for 'nilearn' environment..."
if command -v conda &> /dev/null; then
    if conda env list | grep -q "nilearn"; then
        echo "✓ 'nilearn' environment exists"

        # Try to activate it
        conda activate nilearn 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓ Successfully activated nilearn environment"
            echo ""
            echo "Python version:"
            python --version
            echo ""
            echo "Key packages:"
            python -c "import nilearn; print(f'nilearn: {nilearn.__version__}')" 2>/dev/null || echo "nilearn: not found"
            python -c "import numpy; print(f'numpy: {numpy.__version__}')" 2>/dev/null || echo "numpy: not found"
            python -c "import nibabel; print(f'nibabel: {nibabel.__version__}')" 2>/dev/null || echo "nibabel: not found"
        else
            echo "✗ Could not activate nilearn environment"
        fi
    else
        echo "✗ 'nilearn' environment not found"
        echo ""
        echo "Available environments:"
        conda env list
    fi
else
    echo "✗ conda not available - cannot check for nilearn environment"
fi
echo ""

# 7. Provide recommendations
echo "========================================================================"
echo "RECOMMENDATIONS"
echo "========================================================================"

if [ -n "$FOUND_CONDA_SH" ]; then
    echo "✓ Use this path in run_reconstruction.sh:"
    echo "  source $FOUND_CONDA_SH"
    echo "  conda activate nilearn"
elif [ -f "$HOME/.bashrc" ] && grep -q "conda initialize" "$HOME/.bashrc"; then
    echo "✓ Use .bashrc approach in run_reconstruction.sh:"
    echo "  source \$HOME/.bashrc"
    echo "  conda activate nilearn"
else
    echo "⚠ Conda installation not detected properly"
    echo ""
    echo "Please run these commands manually on the server:"
    echo "  1. which conda"
    echo "  2. conda --version"
    echo "  3. echo \$CONDA_PREFIX"
    echo "  4. conda env list"
    echo ""
    echo "Then update run_reconstruction.sh with the correct conda path"
fi
echo ""
echo "========================================================================"
