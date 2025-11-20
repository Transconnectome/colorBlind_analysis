#!/usr/bin/env python
"""
Verify NumPy/PyTorch compatibility
"""

import sys

print("=" * 60)
print("Environment Verification")
print("=" * 60)

# Check NumPy
try:
    import numpy as np
    print(f"✓ NumPy version: {np.__version__}")
    if np.__version__.startswith('2.'):
        print("  ⚠ WARNING: NumPy 2.x detected - incompatible with old PyTorch!")
        sys.exit(1)
    else:
        print("  ✓ NumPy 1.x - compatible")
except Exception as e:
    print(f"✗ NumPy import failed: {e}")
    sys.exit(1)

# Check PyTorch
try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
except Exception as e:
    print(f"✗ PyTorch import failed: {e}")
    sys.exit(1)

# Test tensor-to-numpy conversion
try:
    x = torch.tensor([1.0, 2.0, 3.0])
    x_np = x.numpy()
    print(f"✓ Tensor-to-numpy conversion: {x_np}")
except Exception as e:
    print(f"✗ Conversion failed: {e}")
    sys.exit(1)

# Test torch.manual_seed
try:
    torch.manual_seed(42)
    print("✓ torch.manual_seed(42) successful")
except Exception as e:
    print(f"✗ manual_seed failed: {e}")
    sys.exit(1)

print("=" * 60)
print("✓ All checks passed!")
print("=" * 60)
