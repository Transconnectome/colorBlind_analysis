#!/bin/bash
# Fix NumPy compatibility for PyTorch in nilearn environment

echo "=== Checking current environment ==="
conda activate nilearn
python -c "import numpy; print(f'Current NumPy: {numpy.__version__}')"
python -c "import torch; print(f'Current PyTorch: {torch.__version__}')" 2>/dev/null || echo "PyTorch not loaded"

echo ""
echo "=== Uninstalling NumPy 2.x ==="
conda remove numpy --force -y

echo ""
echo "=== Installing NumPy 1.26.4 ==="
conda install numpy=1.26.4 -y

echo ""
echo "=== Verification ==="
python -c "import numpy; print(f'New NumPy: {numpy.__version__}')"
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; import numpy; x = torch.tensor([1.0, 2.0]); print(f'Test conversion: {x.numpy()}')"

echo ""
echo "=== Done! ==="
