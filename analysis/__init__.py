"""
Analysis Package for Color Blindness fMRI Study
===============================================

This package contains group-level analyses for color decoding from fMRI data.

Subpackages:
-----------
- group_level: Group-level analyses (HC consistency, HC-CVD comparison)

Utilities:
----------
Uses existing utilities from parent directory:
- utils_color_decoding.py: Color space, forward encoding model, visualization
- group_level_common_voxels.py: Data loading functions
"""

__version__ = "1.0.0"

# Import existing utilities for convenience
import sys
from pathlib import Path

# Add parent directory to path to import existing utils
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
