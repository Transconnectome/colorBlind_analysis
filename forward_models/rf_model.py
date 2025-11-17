"""
Random Forest forward model
"""

import numpy as np
from .base import ForwardModel


class RFForwardModel(ForwardModel):
    """
    Random Forest forward model

    Uses Random Forest regression to learn nonlinear mapping from
    neural activity to channel responses.

    Key advantages:
    - Automatically learns feature interactions (e.g., PC1 × PC2)
    - Provides feature importance per channel
    - Robust to outliers
    - No gradient optimization required

    Key challenges:
    - May overfit with small data
    - Poor extrapolation beyond training range
    - Requires hyperparameter tuning
    """

    def __init__(self, n_channels=6, n_estimators=100, max_depth=5,
                 min_samples_leaf=3, random_state=42):
        """
        Initialize Random Forest forward model

        Parameters
        ----------
        n_channels : int, default=6
            Number of color channels
        n_estimators : int, default=100
            Number of trees in forest
        max_depth : int, default=5
            Maximum depth of trees (prevent overfitting)
        min_samples_leaf : int, default=3
            Minimum samples per leaf (smoothness)
        random_state : int, default=42
            Random seed for reproducibility
        """
        super().__init__(n_channels)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        self.model = None

    def fit(self, X_train, C_train):
        """
        Train Random Forest

        Parameters
        ----------
        X_train : ndarray, shape (n_samples, n_features)
            Training neural activity
        C_train : ndarray, shape (n_channels, n_samples)
            Training channel responses
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.multioutput import MultiOutputRegressor

        # C_train: (n_channels, n_samples) → (n_samples, n_channels)
        y_train = C_train.T

        # Train separate RF for each channel using MultiOutputRegressor
        self.model = MultiOutputRegressor(
            RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                random_state=self.random_state,
                n_jobs=-1  # Use all cores
            )
        )
        self.model.fit(X_train, y_train)

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
        """
        if self.model is None:
            raise RuntimeError("Model must be fitted before prediction")

        # Returns: (n_samples, n_channels) → (n_channels, n_samples)
        y_pred = self.model.predict(X_test)
        return y_pred.T

    def get_name(self):
        return f"RF(depth={self.max_depth},trees={self.n_estimators})"

    def get_params(self):
        return {
            "method": "RandomForest",
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_leaf": self.min_samples_leaf,
            "channels": self.n_channels
        }

    def get_feature_importance(self):
        """
        Get feature importance for each channel

        Returns
        -------
        importances : ndarray, shape (n_channels, n_features)
            Feature importance per channel
        """
        if self.model is None:
            raise RuntimeError("Model must be fitted first")

        importances = []
        for estimator in self.model.estimators_:
            importances.append(estimator.feature_importances_)

        return np.array(importances)  # (n_channels, n_features)
