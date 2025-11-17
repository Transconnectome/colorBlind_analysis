"""
Forward Models for Color Reconstruction
========================================

This module provides different forward model implementations for mapping
PCA components (or voxel activations) to 6-channel color representations.

Available Models:
- LinearForwardModel: Standard linear model (B&H 2009)
- RFForwardModel: Random Forest regression
- MLPForwardModel: Light MLP (1 hidden layer)
"""

from .base import ForwardModel
from .linear_model import LinearForwardModel
from .rf_model import RFForwardModel
from .mlp_model import MLPForwardModel

__all__ = [
    'ForwardModel',
    'LinearForwardModel',
    'RFForwardModel',
    'MLPForwardModel',
]
