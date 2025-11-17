"""
Base class for forward models
"""

import numpy as np


class ForwardModel:
    """
    Base class for forward models (PCA components → Channels)

    Forward models map from neural activity patterns (PCA components or voxels)
    to idealized color channel responses.

    Implements: B = W × C
    where:
        B = neural activity (n_samples, n_features)
        C = channel responses (n_channels, n_samples)
        W = weight matrix to be learned
    """

    def __init__(self, n_channels=6):
        """
        Initialize forward model

        Parameters
        ----------
        n_channels : int, default=6
            Number of idealized color channels
        """
        self.n_channels = n_channels
        self.model = None

    def fit(self, X_train, C_train):
        """
        Train forward model

        Parameters
        ----------
        X_train : ndarray, shape (n_samples, n_features)
            Training neural activity (PCA components or voxels)
        C_train : ndarray, shape (n_channels, n_samples)
            Training channel responses
        """
        raise NotImplementedError("Subclasses must implement fit()")

    def predict(self, X_test):
        """
        Predict channel responses from neural activity

        Parameters
        ----------
        X_test : ndarray, shape (n_samples, n_features)
            Test neural activity (PCA components or voxels)

        Returns
        -------
        C_pred : ndarray, shape (n_channels, n_samples)
            Predicted channel responses
        """
        raise NotImplementedError("Subclasses must implement predict()")

    def get_name(self):
        """
        Return model name for logging

        Returns
        -------
        name : str
            Model name
        """
        raise NotImplementedError("Subclasses must implement get_name()")

    def get_params(self):
        """
        Get model hyperparameters as dictionary

        Returns
        -------
        params : dict
            Model hyperparameters
        """
        return {}
