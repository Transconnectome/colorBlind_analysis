#!/bin/bash
# Upgrade PyTorch to NumPy 2.x compatible version

echo "=== Current Environment ==="
conda activate nilearn
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import torch; print(f'PyTorch (old): {torch.__version__}')" 2>/dev/null || echo "PyTorch not loaded"

echo ""
echo "=== Upgrading PyTorch to NumPy 2.x compatible version ==="
# PyTorch 2.0+ supports NumPy 2.x
conda install pytorch torchvision torchaudio cpuonly -c pytorch -y

echo ""
echo "=== Verification ==="
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import torch; print(f'PyTorch (new): {torch.__version__}')"
python -c "import torch; import numpy; x = torch.tensor([1.0, 2.0]); print(f'Test conversion: {x.numpy()}')"
python -c "import torch; torch.manual_seed(42); print('✓ manual_seed works')"

echo ""
echo "=== Done! ==="
