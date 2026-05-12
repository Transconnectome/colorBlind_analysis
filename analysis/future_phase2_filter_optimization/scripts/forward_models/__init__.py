"""forward_models — Single source of truth for CVD forward models.

P1 (2026-05-10): Consolidates dt_2comp definition that was previously duplicated
across visualize_filter_candidates.py, loco_distortion_fit.py, and
comprehensive_2component_analysis.py. F3/F4 paradox (same params, different viz)
was caused by the SAME formula being implemented inconsistently across these files.

This package provides the single canonical implementation. All callers must
import from here.
"""

from .two_component import (
    CONF_AXIS_STOCKMAN,
    dt_2comp,
    forward_2comp,
    pre_image_2comp,
)

__all__ = [
    'CONF_AXIS_STOCKMAN',
    'dt_2comp',
    'forward_2comp',
    'pre_image_2comp',
]
