"""
Group-Level Analysis Package
============================

Phase 1: HC Consistency
-----------------------
- phase1_voxel_overlap: Jaccard index across HC subjects
- phase1_rsa: Representational Similarity Analysis (RDM)
- phase1_cross_subject_loso: Leave-one-subject-out cross-validation

Phase 2: HC-CVD Comparison
---------------------------
- phase2_decoder_transfer: Apply HC decoder to CVD subjects

Phase 3: 2nd-Level GLM
----------------------
- phase3_second_level_glm: Group-level GLM (nilearn)
"""

__all__ = [
    'phase1_voxel_overlap',
    'phase1_rsa',
    'phase1_cross_subject_loso',
    'phase2_decoder_transfer',
    'phase3_second_level_glm',
]
