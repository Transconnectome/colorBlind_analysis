"""
GLMsingle Configuration Presets

Provides configuration dictionaries for different GLMsingle modes:
- Full: HRF + GLMdenoise + Fracridge (most accurate)
- Conservative: No HRF estimation (faster, fallback)
- Residuals: Force residual output for whitening
"""

import numpy as np


def get_config_full(n_pcs=10):
    """
    Full GLMsingle configuration with all features.

    Features:
    - Adaptive HRF fitting (20 basis functions)
    - GLMdenoise: Remove noise PCs
    - Fracridge: Cross-validated ridge regression
    - Residual saving for whitening

    Args:
        n_pcs: Number of noise PCs to evaluate (default: 10)

    Returns:
        config: Dictionary for GLM_single initialization
    """
    config = {
        # HRF estimation
        'wantlibrary': 1,  # Use 20-function HRF library
        'hrfthresh': 0.5,  # Require R² > 0.5 for HRF selection

        # GLMdenoise
        'wantglmdenoise': 1,  # Enable noise PC removal
        'n_pcs': n_pcs,  # Max PCs to evaluate

        # Fracridge
        'wantfracridge': 1,  # Enable ridge regularization
        'fracs': np.linspace(0.05, 1, 20),  # Ridge fractions to test

        # Output control
        'wantfileoutputs': [0, 0, 0, 0],  # No file outputs (but must have 4 elements)
        'wantmemoryoutputs': [1, 1, 1, 1],  # All outputs in memory

        # Performance
        'chunklen': 50000,  # Voxel chunk size

        # Residuals (CRITICAL for whitening)
        # Note: 'wantresiduals' not supported - will compute manually
    }

    return config


def get_config_conservative(n_pcs=10):
    """
    Conservative configuration without HRF estimation.

    Use when:
    - HRF estimation fails
    - Faster processing needed
    - Uniform HRF assumed across voxels

    Args:
        n_pcs: Number of noise PCs to evaluate

    Returns:
        config: Dictionary for GLM_single initialization
    """
    config = {
        # No HRF estimation
        'wantlibrary': 0,  # Use canonical HRF

        # GLMdenoise still enabled
        'wantglmdenoise': 1,
        'n_pcs': n_pcs,

        # Fracridge still enabled
        'wantfracridge': 1,
        'fracs': np.linspace(0.05, 1, 20),

        # Output control
        'wantfileoutputs': [0, 0, 0, 0],  # Must have 4 elements
        'wantmemoryoutputs': [1, 1, 1, 1],

        # Performance
        'chunklen': 50000,

        # Residuals
        # Note: 'wantresiduals' not supported - will compute manually
    }

    return config


def get_config_residuals():
    """
    Minimal configuration for residual extraction.

    Use when only residuals are needed (debugging/testing).

    Returns:
        config: Dictionary for GLM_single initialization
    """
    config = {
        # Disable advanced features
        'wantlibrary': 0,
        'wantglmdenoise': 0,
        'wantfracridge': 0,

        # Output control
        'wantfileoutputs': [0, 0, 0, 0],  # Must have 4 elements
        'wantmemoryoutputs': [1, 1, 1, 1],

        # Residuals
        'wantresiduals': True,
    }

    return config


def get_config_custom(
    use_hrf=True,
    use_glmdenoise=True,
    use_fracridge=True,
    n_pcs=10,
    hrfthresh=0.5
):
    """
    Custom configuration builder.

    Args:
        use_hrf: Enable adaptive HRF fitting
        use_glmdenoise: Enable noise PC removal
        use_fracridge: Enable ridge regularization
        n_pcs: Number of noise PCs
        hrfthresh: R² threshold for HRF selection

    Returns:
        config: Dictionary for GLM_single initialization
    """
    config = {
        # HRF
        'wantlibrary': int(use_hrf),
        'hrfthresh': hrfthresh if use_hrf else 0.5,

        # GLMdenoise
        'wantglmdenoise': int(use_glmdenoise),
        'n_pcs': n_pcs if use_glmdenoise else 0,

        # Fracridge
        'wantfracridge': int(use_fracridge),
        'fracs': np.linspace(0.05, 1, 20) if use_fracridge else [1],

        # Output control
        'wantfileoutputs': [0, 0, 0, 0],  # Must have 4 elements
        'wantmemoryoutputs': [1, 1, 1, 1],

        # Performance
        'chunklen': 50000,

        # Residuals
        # Note: 'wantresiduals' not supported - will compute manually
    }

    return config


def print_config_summary(config):
    """
    Print human-readable configuration summary.

    Args:
        config: GLMsingle configuration dictionary
    """
    print("GLMsingle Configuration:")
    print(f"  HRF Library: {'Enabled' if config.get('wantlibrary', 0) else 'Disabled'}")
    if config.get('wantlibrary', 0):
        print(f"    HRF threshold: {config.get('hrfthresh', 0.5)}")

    print(f"  GLMdenoise: {'Enabled' if config.get('wantglmdenoise', 0) else 'Disabled'}")
    if config.get('wantglmdenoise', 0):
        print(f"    Max PCs: {config.get('n_pcs', 10)}")

    print(f"  Fracridge: {'Enabled' if config.get('wantfracridge', 0) else 'Disabled'}")
    if config.get('wantfracridge', 0):
        fracs = config.get('fracs', [])
        print(f"    Ridge fractions: {len(fracs)} values from {fracs[0]:.2f} to {fracs[-1]:.2f}")

    print(f"  Residuals: {'Requested' if config.get('wantresiduals', False) else 'Not requested'}")
    print()


# Recommended configurations for our dataset
RECOMMENDED_CONFIG = get_config_full(n_pcs=10)
FALLBACK_CONFIG = get_config_conservative(n_pcs=10)

if __name__ == '__main__':
    # Test configurations
    print("=" * 60)
    print("RECOMMENDED CONFIGURATION (Full)")
    print("=" * 60)
    print_config_summary(RECOMMENDED_CONFIG)

    print("=" * 60)
    print("FALLBACK CONFIGURATION (Conservative)")
    print("=" * 60)
    print_config_summary(FALLBACK_CONFIG)

    print("=" * 60)
    print("CUSTOM EXAMPLE")
    print("=" * 60)
    custom = get_config_custom(
        use_hrf=True,
        use_glmdenoise=True,
        use_fracridge=False,
        n_pcs=15
    )
    print_config_summary(custom)
