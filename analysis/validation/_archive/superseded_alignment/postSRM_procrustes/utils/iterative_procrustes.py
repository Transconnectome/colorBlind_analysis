"""
Iterative Procrustes for HC Template Generation

Implements Haxby et al. (2011) iterative Procrustes algorithm for
generating a common representational template from healthy control subjects.

Reference:
    Haxby et al. (2011). A common, high-dimensional model of the representational
    space in human ventral temporal cortex. Neuron, 72(2), 404-416.
"""

import numpy as np
from scipy.linalg import orthogonal_procrustes
from typing import List, Tuple, Dict


def procrustes_transform(source, target):
    """
    Compute Procrustes transformation from source to target.

    Args:
        source: (n_samples, n_features) source matrix
        target: (n_samples, n_features) target matrix

    Returns:
        transformed: (n_samples, n_features) aligned source
        rotation: (n_features, n_features) rotation matrix
        disparity: Procrustes disparity (squared Frobenius norm)
    """
    # Center and normalize
    source_centered = source - source.mean(axis=0)
    target_centered = target - target.mean(axis=0)

    source_norm = np.linalg.norm(source_centered)
    target_norm = np.linalg.norm(target_centered)

    if source_norm < 1e-10 or target_norm < 1e-10:
        raise ValueError("Cannot normalize near-zero matrix")

    source_scaled = source_centered / source_norm
    target_scaled = target_centered / target_norm

    # Compute optimal rotation
    rotation, _ = orthogonal_procrustes(source_scaled, target_scaled)

    # Apply transformation
    transformed = source_scaled @ rotation

    # Compute disparity
    disparity = np.sum((transformed - target_scaled) ** 2)

    # Scale back to target scale
    transformed = transformed * target_norm + target.mean(axis=0)

    return transformed, rotation, disparity


def iterative_procrustes_hc_template(
    hc_patterns: List[np.ndarray],
    max_iter: int = 10,
    tol: float = 0.001,
    verbose: bool = True
) -> Tuple[np.ndarray, List[np.ndarray], List[Dict]]:
    """
    Generate HC common template via iterative Procrustes (Haxby et al. 2011).

    Algorithm:
        1. Initialize template as mean of HC patterns
        2. For each iteration:
            a. Align each HC pattern to current template
            b. Update template = mean of aligned patterns
            c. Check convergence (relative template change)
        3. Return final template and aligned patterns

    Args:
        hc_patterns: List of (n_colors, n_features) patterns for HC subjects
        max_iter: Maximum iterations (default: 10)
        tol: Convergence tolerance for relative template change (default: 0.001)
        verbose: Print iteration info (default: True)

    Returns:
        template: (n_colors, n_features) final HC template
        aligned: List of (n_colors, n_features) aligned patterns
        history: List of dicts with convergence metrics per iteration
    """
    n_subjects = len(hc_patterns)
    n_colors, n_features = hc_patterns[0].shape

    if verbose:
        print(f"\n=== Iterative Procrustes (Haxby 2011) ===")
        print(f"  n_subjects: {n_subjects}")
        print(f"  n_colors: {n_colors}, n_features: {n_features}")

    # Initialize template as mean
    template = np.mean(hc_patterns, axis=0)  # (n_colors, n_features)

    history = []

    for iteration in range(max_iter):
        aligned = []
        disparities = []
        rotations = []

        # Align each subject to template
        for subj_idx, subj_pattern in enumerate(hc_patterns):
            try:
                transformed, rotation, disparity = procrustes_transform(
                    subj_pattern, template
                )
                aligned.append(transformed)
                disparities.append(disparity)
                rotations.append(rotation)
            except ValueError as e:
                print(f"  WARNING: Subject {subj_idx} failed: {e}")
                # Use unaligned pattern as fallback
                aligned.append(subj_pattern)
                disparities.append(np.nan)
                rotations.append(None)

        # Update template
        new_template = np.mean(aligned, axis=0)

        # Convergence check
        template_norm = np.linalg.norm(template)
        if template_norm < 1e-10:
            print(f"  ERROR: Template norm near zero at iteration {iteration}")
            break

        template_change = np.linalg.norm(new_template - template) / template_norm
        mean_disparity = np.nanmean(disparities)

        history.append({
            'iteration': iteration,
            'mean_disparity': float(mean_disparity),
            'template_change': float(template_change),
            'disparities': [float(d) if not np.isnan(d) else None for d in disparities],
            'n_failed': sum(np.isnan(disparities)),
        })

        if verbose:
            print(f"  Iter {iteration}: disparity={mean_disparity:.6f}, "
                  f"change={template_change:.8f}, failed={sum(np.isnan(disparities))}")

        template = new_template

        if template_change < tol:
            if verbose:
                print(f"  ✓ Converged at iteration {iteration}")
            break
    else:
        if verbose:
            print(f"  ⚠ Did not converge after {max_iter} iterations")

    return template, aligned, history


def apply_template_to_subjects(
    patterns: List[np.ndarray],
    template: np.ndarray,
    subject_ids: List[str],
    verbose: bool = True
) -> Tuple[List[np.ndarray], List[np.ndarray], List[float]]:
    """
    Apply HC template to align all subjects (HC + CVD).

    Args:
        patterns: List of (n_colors, n_features) patterns per subject
        template: (n_colors, n_features) HC template
        subject_ids: List of subject IDs for logging
        verbose: Print progress

    Returns:
        aligned: List of aligned patterns
        rotations: List of rotation matrices
        disparities: List of disparity values
    """
    if verbose:
        print(f"\n=== Applying Template to {len(patterns)} Subjects ===")

    aligned = []
    rotations = []
    disparities = []

    for subj_idx, (subj_pattern, subj_id) in enumerate(zip(patterns, subject_ids)):
        try:
            transformed, rotation, disparity = procrustes_transform(
                subj_pattern, template
            )
            aligned.append(transformed)
            rotations.append(rotation)
            disparities.append(disparity)

            if verbose:
                print(f"  {subj_id}: disparity={disparity:.6f}")

        except ValueError as e:
            print(f"  WARNING: {subj_id} failed: {e}")
            aligned.append(subj_pattern)
            rotations.append(None)
            disparities.append(np.nan)

    return aligned, rotations, disparities
