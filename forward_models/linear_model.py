"""
Linear forward model (Brouwer & Heeger 2009)
"""

import numpy as np
from .base import ForwardModel


class LinearForwardModel(ForwardModel):
    """
    Linear forward model (B&H 2009 original method)

    Implements: B = W × C
    Solves for W using: W = B × C^T × (C × C^T)^-1

    This is the baseline model - a simple linear mapping from
    neural activity to channel responses.
    """

    def __init__(self, n_channels=6):
        super().__init__(n_channels)
        self.W = None

    def fit(self, X_train, C_train):
        """
        Train linear forward model

        Parameters
        ----------
        X_train : ndarray, shape (n_samples, n_features)
            Training neural activity
        C_train : ndarray, shape (n_channels, n_samples)
            Training channel responses

        Notes
        -----
        Computes weight matrix W using least squares:
        W = X^T @ C^T @ (C @ C^T)^-1
        """
        # W = X^T @ C^T @ (C @ C^T)^-1
        self.W = X_train.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

    def predict(self, X_test):
        """
        Predict channel responses

        Parameters
        ----------
        X_test : ndarray, shape (n_samples, n_features)
            Test neural activity

        Returns
        -------
        C_pred : ndarray, shape (n_channels, n_samples)
            Predicted channel responses

        Notes
        -----
        Uses pseudoinverse to avoid numerical issues:
        C = (W^T @ W)^-1 @ W^T @ X
        """
        if self.W is None:
            raise RuntimeError("Model must be fitted before prediction")

        # C = (W^T @ W)^-1 @ W^T @ X
        # Use pseudoinverse to avoid singular matrix errors
        C_pred = np.linalg.pinv(self.W.T @ self.W) @ self.W.T @ X_test.T

        return C_pred  # (n_channels, n_samples)

    def get_name(self):
        return "Linear"

    def get_params(self):
        return {"method": "OLS", "channels": self.n_channels}
