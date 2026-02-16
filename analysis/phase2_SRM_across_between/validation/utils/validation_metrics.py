"""
Core validation metrics for SRM validation tests
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional


def compute_icc(measurements: np.ndarray, icc_type: str = '3,1') -> Tuple[float, Tuple[float, float]]:
    """
    Compute Intraclass Correlation Coefficient with bootstrap CI.

    Parameters
    ----------
    measurements : np.ndarray
        Shape (n_measurements, n_observations)
        For run-split ICC: (2, n_features) where rows are run-set A and B
    icc_type : str
        ICC type (default: '3,1' for single-measurement consistency)

    Returns
    -------
    icc : float
        ICC coefficient
    ci : Tuple[float, float]
        Bootstrap 95% confidence interval

    Notes
    -----
    ICC(3,1) = (BMS - WMS) / (BMS + WMS)
    where BMS = between-measurement variance, WMS = within-measurement variance
    """
    n_measurements, n_obs = measurements.shape

    # Compute means
    grand_mean = np.mean(measurements)
    measurement_means = np.mean(measurements, axis=1)
    observation_means = np.mean(measurements, axis=0)

    # Sum of squares
    ss_total = np.sum((measurements - grand_mean) ** 2)
    ss_between_obs = n_measurements * np.sum((observation_means - grand_mean) ** 2)
    ss_between_meas = n_obs * np.sum((measurement_means - grand_mean) ** 2)
    ss_error = ss_total - ss_between_obs - ss_between_meas

    # Mean squares
    df_between_obs = n_obs - 1
    df_between_meas = n_measurements - 1
    df_error = (n_measurements - 1) * (n_obs - 1)

    ms_between_obs = ss_between_obs / df_between_obs
    ms_error = ss_error / df_error

    # ICC(3,1) - single measurement consistency
    icc = (ms_between_obs - ms_error) / (ms_between_obs + ms_error)

    # Bootstrap CI
    n_bootstrap = 1000
    icc_bootstrap = []

    for _ in range(n_bootstrap):
        # Resample observations with replacement
        idx = np.random.choice(n_obs, size=n_obs, replace=True)
        boot_data = measurements[:, idx]

        # Compute ICC for bootstrap sample
        boot_grand_mean = np.mean(boot_data)
        boot_obs_means = np.mean(boot_data, axis=0)

        boot_ss_total = np.sum((boot_data - boot_grand_mean) ** 2)
        boot_ss_between = n_measurements * np.sum((boot_obs_means - boot_grand_mean) ** 2)
        boot_ss_error = boot_ss_total - boot_ss_between

        boot_ms_between = boot_ss_between / df_between_obs
        boot_ms_error = boot_ss_error / df_error

        boot_icc = (boot_ms_between - boot_ms_error) / (boot_ms_between + boot_ms_error)
        icc_bootstrap.append(boot_icc)

    ci = (np.percentile(icc_bootstrap, 2.5), np.percentile(icc_bootstrap, 97.5))

    return icc, ci


def permutation_test(group1: np.ndarray, group2: np.ndarray,
                     n_permutations: int = 10000,
                     statistic: str = 't',
                     seed: Optional[int] = 42) -> Tuple[float, float, np.ndarray]:
    """
    Permutation test for group differences.

    Parameters
    ----------
    group1, group2 : np.ndarray
        Data for two groups (1D arrays)
    n_permutations : int
        Number of permutation iterations
    statistic : str
        Test statistic ('t' for t-test, 'mean_diff' for mean difference)
    seed : int or None
        Random seed for reproducibility

    Returns
    -------
    observed_stat : float
        Observed test statistic
    p_value : float
        Permutation p-value
    null_distribution : np.ndarray
        Distribution of test statistics under null hypothesis
    """
    if seed is not None:
        np.random.seed(seed)

    # Compute observed statistic
    if statistic == 't':
        observed_stat = stats.ttest_ind(group1, group2)[0]
    elif statistic == 'mean_diff':
        observed_stat = np.mean(group1) - np.mean(group2)
    else:
        raise ValueError(f"Unknown statistic: {statistic}")

    # Pool data
    pooled = np.concatenate([group1, group2])
    n1 = len(group1)
    n_total = len(pooled)

    # Permutation loop
    null_distribution = np.zeros(n_permutations)

    for i in range(n_permutations):
        # Shuffle and split
        np.random.shuffle(pooled)
        perm_group1 = pooled[:n1]
        perm_group2 = pooled[n1:]

        # Compute statistic
        if statistic == 't':
            null_distribution[i] = stats.ttest_ind(perm_group1, perm_group2)[0]
        elif statistic == 'mean_diff':
            null_distribution[i] = np.mean(perm_group1) - np.mean(perm_group2)

    # Compute p-value (two-tailed)
    p_value = np.mean(np.abs(null_distribution) >= np.abs(observed_stat))

    return observed_stat, p_value, null_distribution


def bootstrap_correlation(x: np.ndarray, y: np.ndarray,
                          n_bootstrap: int = 1000,
                          method: str = 'spearman',
                          seed: Optional[int] = 42) -> Tuple[float, Tuple[float, float]]:
    """
    Bootstrap confidence interval for correlation.

    Parameters
    ----------
    x, y : np.ndarray
        Data vectors to correlate (1D arrays)
    n_bootstrap : int
        Number of bootstrap iterations
    method : str
        Correlation method ('spearman' or 'pearson')
    seed : int or None
        Random seed

    Returns
    -------
    r : float
        Observed correlation
    ci : Tuple[float, float]
        Bootstrap 95% confidence interval
    """
    if seed is not None:
        np.random.seed(seed)

    # Compute observed correlation
    if method == 'spearman':
        r, _ = stats.spearmanr(x, y)
    elif method == 'pearson':
        r, _ = stats.pearsonr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Bootstrap
    n = len(x)
    r_bootstrap = []

    for _ in range(n_bootstrap):
        idx = np.random.choice(n, size=n, replace=True)
        if method == 'spearman':
            r_boot, _ = stats.spearmanr(x[idx], y[idx])
        else:
            r_boot, _ = stats.pearsonr(x[idx], y[idx])
        r_bootstrap.append(r_boot)

    ci = (np.percentile(r_bootstrap, 2.5), np.percentile(r_bootstrap, 97.5))

    return r, ci


def classify_icc(icc: float) -> str:
    """
    Classify ICC value according to standard thresholds.

    Parameters
    ----------
    icc : float
        ICC coefficient

    Returns
    -------
    classification : str
        'excellent', 'good', 'moderate', or 'poor'
    """
    if icc > 0.75:
        return 'excellent'
    elif icc > 0.60:
        return 'good'
    elif icc > 0.40:
        return 'moderate'
    else:
        return 'poor'
