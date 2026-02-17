# Project Overview

## Goal
- To establish that cortical color representations differ systematically between healthy controls (HC) and color vision deficient (CVD) individuals, that these differences are geometric in nature and recoverable in a shared representational space, and that such geometry enables continuous prediction of voxel responses — ultimately allowing the design of a personalized neural color-vision correction filter.

## Key hypothesis
1. Cortical-level difference hypothesis

Healthy controls and CVD individuals exhibit distinct representational geometries in visual cortex (V1–V4).

- HC–HC alignment should show high geometric consistency.
- CVD–CVD alignment should reveal internally consistent but shifted or distorted geometry.
- HC–CVD disparity should reflect systematic “collision deficiencies” in representational space.

These differences are not reducible to SNR or amplitude differences, but manifest as geometric distortions in representational manifold structure.

2. Within-group geometric validation hypothesis

If the representational differences are genuine:

- CVD–CVD alignment should still produce stable shared geometry.
- Their disparity structure should cluster according to deficiency type.
- Representational geometry should be captured by RDM similarity and Procrustes/SRM alignment metrics.

Thus, the deficit is not random noise but a structured geometric deformation. 

3. Alignment necessity hypothesis

Because voxel-level correspondences are not spatially identical across individuals,
geometric alignment (Procrustes / SRM / Hyperalignment) must precede decoding.

Prediction:

- Decoding accuracy and cross-subject generalization will significantly improve after alignment.
- Pre-SRM permutation tests should eliminate spurious structure, confirming that the recovered manifold is not alignment-imposed.
- Geometric statistics (e.g., RTM, representational topology measures) will validate shared manifold recovery.

4. Continuous representational hypothesis

After mapping subjects into a shared neural basis:

- Voxel responses to trained colors (8 stimuli) can be modeled in continuous color space.
- The learned manifold allows interpolation.
- Voxel responses for unseen intermediate colors can be predicted.
- Representational distance should vary smoothly along color angle.

Thus, cortex encodes color as a continuous geometric manifold, not discrete categories.

5. Predictive generative hypothesis

Given a color stimulus:

- The model can predict voxel response patterns.
- Conversely, voxel patterns can reconstruct color angle in perceptual space.

This establishes bidirectional mapping between stimulus space and cortical manifold.

6. Translational filter-design hypothesis (Future Phase)

If cortical geometry is:

- Measurable
- Alignable
- Predictively continuous

Then we can:

- Estimate the geometric distortion of a CVD individual's manifold.
- Compute a transformation in color space that compensates for cortical collision.
- Design a personalized display filter.
- Validate the filter by predicting improved separability in neural representational space.

Ultimately:

Neural geometry → Shared basis → Continuous prediction → Personalized color filter.

## Current bottleneck
- Fully demonstrating that group differences are geometric rather than amplitude-driven.

- Tight statistical demonstration of HC–HC vs CVD–CVD vs HC–CVD disparity.

- Proving alignment is necessary (not optional).

- Showing smooth interpolation in representational space (continuous prediction not yet demonstrated).

- Strengthening permutation controls to eliminate SRM-induced artifacts.

## Priority this week
- Finalize HC–HC / CVD–CVD / HC–CVD disparity comparisons (effect sizes + permutation-based p-values).

- Quantify geometric smoothness across color angle (manifold continuity test).

- Compare decoding performance:
1. Alignment: Pre-alignment, Procrustes, SRM
2. Decoder: SVM, Linear, Matrix-based, Non-linearlity added

- Draft “Geometric deformation model” figure.

- Outline Phase 2 interpolation experiment design.

## Links / pointers
- Repo root: /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
- Key results folder: In each subfolder/results in /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis
- Key scripts: 
- Notes (Notion/GDoc): 
