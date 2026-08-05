"""
Geometric Analysis Utilities

Functions for computing geometric metrics on RDMs:
- Inter-Subject Correlation (ISC)
- Deviation from group norm
- Circularity via MDS embedding
- MDS stress
"""

import numpy as np
from scipy.stats import spearmanr
from sklearn.manifold import MDS
from typing import Tuple, Dict


def compute_geometric_consistency_isc(rdm_subject, rdm_group_mean):
    """
    Compute Inter-Subject Correlation (ISC).

    Definition: Spearman correlation between subject RDM and group mean RDM.

    Args:
        rdm_subject: (n, n) subject's RDM
        rdm_group_mean: (n, n) group mean RDM

    Returns:
        isc: Spearman correlation coefficient
    """
    # Upper triangle (excluding diagonal)
    mask = np.triu_indices(rdm_subject.shape[0], k=1)

    isc, _ = spearmanr(rdm_subject[mask], rdm_group_mean[mask])

    return float(isc)


def compute_deviation_from_norm(rdm_subject, rdm_norm):
    """
    Compute Euclidean distance from normative RDM.

    Args:
        rdm_subject: (n, n) subject's RDM
        rdm_norm: (n, n) normative RDM (e.g., HC mean)

    Returns:
        deviation: Euclidean distance
    """
    deviation = np.linalg.norm(rdm_subject - rdm_norm)

    return float(deviation)


def compute_circularity_mds(rdm, n_components=2, random_state=42):
    """
    Compute circularity index via MDS 2D embedding.

    Definition: Perimeter / (2π × radius_gyration)
    - Perfect circle: circularity = 1.0
    - Ellipse/distorted: circularity ≠ 1.0

    Args:
        rdm: (n, n) dissimilarity matrix
        n_components: Number of MDS dimensions (default: 2)
        random_state: Random seed for MDS

    Returns:
        circularity: Circularity index
        stress: MDS stress (fit quality)
        embedding: (n, n_components) MDS coordinates
    """
    # MDS embedding
    mds = MDS(n_components=n_components, dissimilarity='precomputed', random_state=random_state)
    embedding = mds.fit_transform(rdm)

    if n_components != 2:
        # Circularity only defined for 2D
        return None, mds.stress_, embedding

    # Perimeter (consecutive points, closed loop)
    n_points = len(embedding)
    perimeter = sum(
        np.linalg.norm(embedding[(i + 1) % n_points] - embedding[i])
        for i in range(n_points)
    )

    # Radius of gyration
    centroid = embedding.mean(axis=0)
    radii = np.linalg.norm(embedding - centroid, axis=1)
    radius_gyration = radii.mean()

    if radius_gyration < 1e-10:
        circularity = np.nan
    else:
        circularity = perimeter / (2 * np.pi * radius_gyration)

    return float(circularity), float(mds.stress_), embedding


def compute_leave_one_out_isc(rdms, subject_ids):
    """
    Compute leave-one-out ISC for each subject.

    For each subject i:
        ISC[i] = corr(RDM[i], mean(RDM[j≠i]))

    Args:
        rdms: List of (n, n) RDMs
        subject_ids: List of subject IDs

    Returns:
        isc_dict: {subject_id: isc_value}
    """
    n_subjects = len(rdms)
    isc_dict = {}

    for i, (rdm_i, subj_id) in enumerate(zip(rdms, subject_ids)):
        # Compute leave-one-out mean
        rdms_others = [rdm for j, rdm in enumerate(rdms) if j != i]
        rdm_mean = np.mean(rdms_others, axis=0)

        # ISC
        isc = compute_geometric_consistency_isc(rdm_i, rdm_mean)
        isc_dict[subj_id] = isc

    return isc_dict


def compute_all_geometric_metrics(
    rdm_subject: np.ndarray,
    rdm_group_mean: np.ndarray,
    subject_id: str,
    group: str = None
) -> Dict:
    """
    Compute all geometric metrics for a single subject.

    Args:
        rdm_subject: (n, n) subject's RDM
        rdm_group_mean: (n, n) group mean RDM (for ISC and deviation)
        subject_id: Subject identifier
        group: Group label (e.g., 'HC' or 'CVD')

    Returns:
        metrics: Dictionary with all metrics
    """
    # ISC
    isc = compute_geometric_consistency_isc(rdm_subject, rdm_group_mean)

    # Deviation
    deviation = compute_deviation_from_norm(rdm_subject, rdm_group_mean)

    # Circularity
    circularity, mds_stress, embedding = compute_circularity_mds(rdm_subject)

    metrics = {
        'subject': subject_id,
        'group': group,
        'isc': isc,
        'deviation_from_hc': deviation,
        'circularity': circularity,
        'mds_stress': mds_stress,
        'mds_embedding': embedding.tolist() if embedding is not None else None,
    }

    return metrics


def compute_group_statistics(values_hc, values_cvd, metric_name):
    """
    Compute statistics comparing HC vs CVD groups.

    Args:
        values_hc: List of values for HC subjects
        values_cvd: List of values for CVD subjects
        metric_name: Name of the metric

    Returns:
        stats: Dictionary with means, stds, t-test, effect size
    """
    from scipy.stats import ttest_ind

    # Basic statistics
    hc_mean = np.mean(values_hc)
    hc_std = np.std(values_hc, ddof=1)
    cvd_mean = np.mean(values_cvd)
    cvd_std = np.std(values_cvd, ddof=1)

    # T-test
    t_stat, p_value = ttest_ind(values_hc, values_cvd)

    # Cohen's d
    pooled_std = np.sqrt(((len(values_hc) - 1) * hc_std**2 + (len(values_cvd) - 1) * cvd_std**2) /
                         (len(values_hc) + len(values_cvd) - 2))

    cohens_d = (hc_mean - cvd_mean) / pooled_std if pooled_std > 0 else np.nan

    stats = {
        'metric': metric_name,
        'hc_mean': float(hc_mean),
        'hc_std': float(hc_std),
        'hc_n': len(values_hc),
        'cvd_mean': float(cvd_mean),
        'cvd_std': float(cvd_std),
        'cvd_n': len(values_cvd),
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'cohens_d': float(cohens_d),
        'significant': bool(p_value < 0.05),
    }

    return stats
