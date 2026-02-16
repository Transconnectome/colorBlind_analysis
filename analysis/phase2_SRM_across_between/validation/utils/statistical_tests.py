"""
Statistical tests for validation analysis
"""

import numpy as np
from scipy import stats
from typing import Dict, Tuple


def spearman_brown_correction(r_half: float) -> float:
    """
    Spearman-Brown prophecy formula for split-half reliability correction.

    Parameters
    ----------
    r_half : float
        Split-half correlation (uncorrected)

    Returns
    -------
    r_full : float
        Predicted full-length reliability

    Notes
    -----
    Formula: r_full = (2 * r_half) / (1 + r_half)
    """
    return (2 * r_half) / (1 + r_half)


def repeated_measures_anova(data: np.ndarray, factor_names: list) -> Dict:
    """
    Repeated-measures ANOVA.

    Parameters
    ----------
    data : np.ndarray
        Shape (n_subjects, n_conditions)
        For alignment comparison: (n_subjects, n_methods) per ROI
    factor_names : list
        Names of conditions/factors

    Returns
    -------
    results : dict
        Contains F-statistic, p-value, effect size (eta-squared)
    """
    n_subjects, n_conditions = data.shape

    # Grand mean and condition means
    grand_mean = np.mean(data)
    subject_means = np.mean(data, axis=1)
    condition_means = np.mean(data, axis=0)

    # Sum of squares
    ss_total = np.sum((data - grand_mean) ** 2)
    ss_between_subjects = n_conditions * np.sum((subject_means - grand_mean) ** 2)
    ss_between_conditions = n_subjects * np.sum((condition_means - grand_mean) ** 2)
    ss_error = ss_total - ss_between_subjects - ss_between_conditions

    # Degrees of freedom
    df_between = n_conditions - 1
    df_subjects = n_subjects - 1
    df_error = df_between * df_subjects

    # Mean squares
    ms_between = ss_between_conditions / df_between
    ms_error = ss_error / df_error

    # F-statistic
    F = ms_between / ms_error
    p_value = 1 - stats.f.cdf(F, df_between, df_error)

    # Effect size (partial eta-squared)
    eta_squared = ss_between_conditions / (ss_between_conditions + ss_error)

    return {
        'F': F,
        'p_value': p_value,
        'df_between': df_between,
        'df_error': df_error,
        'eta_squared': eta_squared,
        'condition_means': dict(zip(factor_names, condition_means))
    }


def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, float]:
    """
    Bonferroni correction for multiple comparisons.

    Parameters
    ----------
    p_values : np.ndarray
        Array of p-values
    alpha : float
        Family-wise error rate

    Returns
    -------
    reject : np.ndarray
        Boolean array indicating which tests reject null
    corrected_alpha : float
        Bonferroni-corrected alpha threshold
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests
    reject = p_values < corrected_alpha

    return reject, corrected_alpha


def pairwise_comparisons(data: np.ndarray, condition_names: list,
                         alpha: float = 0.05) -> Dict:
    """
    Pairwise t-tests with Bonferroni correction.

    Parameters
    ----------
    data : np.ndarray
        Shape (n_subjects, n_conditions)
    condition_names : list
        Names of conditions
    alpha : float
        Family-wise error rate

    Returns
    -------
    results : dict
        Contains pairwise comparisons with corrected p-values
    """
    n_conditions = data.shape[1]
    n_comparisons = n_conditions * (n_conditions - 1) // 2
    corrected_alpha = alpha / n_comparisons

    comparisons = []

    for i in range(n_conditions):
        for j in range(i + 1, n_conditions):
            t_stat, p_value = stats.ttest_rel(data[:, i], data[:, j])

            comparisons.append({
                'comparison': f"{condition_names[i]} vs {condition_names[j]}",
                't_stat': t_stat,
                'p_value': p_value,
                'p_corrected': min(p_value * n_comparisons, 1.0),
                'significant': p_value < corrected_alpha,
                'mean_diff': np.mean(data[:, i] - data[:, j])
            })

    return {
        'comparisons': comparisons,
        'corrected_alpha': corrected_alpha,
        'n_comparisons': n_comparisons
    }


def effect_size_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cohen's d effect size.

    Parameters
    ----------
    group1, group2 : np.ndarray
        Data for two groups

    Returns
    -------
    d : float
        Cohen's d (standardized mean difference)
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    d = (mean1 - mean2) / pooled_std

    return d
