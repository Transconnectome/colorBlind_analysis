"""
GLMsingle + Whitening Utilities

Modules:
- glmsingle_interface: Load data, run GLMsingle with residuals
- glmsingle_config: Configuration presets
- whitening_from_residuals: Noise covariance estimation and whitening
"""

from .glmsingle_interface import (
    load_event_files,
    build_design_matrices,
    load_bold_data,
    run_glmsingle_with_residuals
)

from .glmsingle_config import (
    get_config_full,
    get_config_conservative,
    get_config_residuals
)

from .whitening_from_residuals import (
    estimate_noise_covariance,
    compute_whitening_matrix,
    apply_whitening
)

__all__ = [
    'load_event_files',
    'build_design_matrices',
    'load_bold_data',
    'run_glmsingle_with_residuals',
    'get_config_full',
    'get_config_conservative',
    'get_config_residuals',
    'estimate_noise_covariance',
    'compute_whitening_matrix',
    'apply_whitening'
]
