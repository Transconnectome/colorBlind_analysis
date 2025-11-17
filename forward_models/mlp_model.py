"""
Light MLP forward model (1 hidden layer)
"""

import numpy as np
from .base import ForwardModel


class MLPForwardModel(ForwardModel):
    """
    Light MLP forward model (1 hidden layer)

    Uses shallow neural network to learn nonlinear mapping from
    neural activity to channel responses.

    Architecture:
        Input (n_features) → Hidden (n_hidden, ReLU) → Dropout → Output (6 channels)

    Key advantages:
    - Gradient-based optimization (smooth, continuous)
    - Better interpolation for novel colors
    - Can learn complex nonlinear patterns
    - Biologically plausible (layered processing)

    Key challenges:
    - Requires careful hyperparameter tuning
    - May get stuck in local minima
    - Risk of overfitting with small data
    """

    def __init__(self, n_channels=6, n_hidden=16, learning_rate=0.001,
                 weight_decay=0.01, dropout=0.2, n_epochs=100,
                 early_stopping_patience=20, random_state=42, verbose=False):
        """
        Initialize Light MLP forward model

        Parameters
        ----------
        n_channels : int, default=6
            Number of color channels
        n_hidden : int, default=16
            Number of hidden units (keep small for small data!)
        learning_rate : float, default=0.001
            Learning rate for Adam optimizer
        weight_decay : float, default=0.01
            L2 regularization strength
        dropout : float, default=0.2
            Dropout rate (0.0 = no dropout)
        n_epochs : int, default=100
            Maximum training epochs
        early_stopping_patience : int, default=20
            Early stopping patience (epochs without improvement)
        random_state : int, default=42
            Random seed for reproducibility
        verbose : bool, default=False
            Print training progress
        """
        super().__init__(n_channels)
        self.n_hidden = n_hidden
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.dropout = dropout
        self.n_epochs = n_epochs
        self.early_stopping_patience = early_stopping_patience
        self.random_state = random_state
        self.verbose = verbose
        self.model = None
        self.best_model_state = None
        self.training_history = None

    def fit(self, X_train, C_train):
        """
        Train MLP with early stopping

        Parameters
        ----------
        X_train : ndarray, shape (n_samples, n_features)
            Training neural activity
        C_train : ndarray, shape (n_channels, n_samples)
            Training channel responses
        """
        import torch
        import torch.nn as nn
        import torch.optim as optim

        # Set random seed
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        # C_train: (n_channels, n_samples) → (n_samples, n_channels)
        y_train = C_train.T

        # Split train into train/val (80/20) for early stopping
        n_samples = len(X_train)
        n_train = max(int(0.8 * n_samples), n_samples - 2)  # Keep at least 2 for val
        indices = np.random.permutation(n_samples)
        train_idx, val_idx = indices[:n_train], indices[n_train:]

        X_tr, X_val = X_train[train_idx], X_train[val_idx]
        y_tr, y_val = y_train[train_idx], y_train[val_idx]

        # Convert to tensors
        X_tr_t = torch.FloatTensor(X_tr)
        y_tr_t = torch.FloatTensor(y_tr)
        X_val_t = torch.FloatTensor(X_val)
        y_val_t = torch.FloatTensor(y_val)

        # Define model
        class SimpleMLP(nn.Module):
            def __init__(self, n_input, n_hidden, n_output, dropout):
                super().__init__()
                self.fc1 = nn.Linear(n_input, n_hidden)
                self.relu = nn.ReLU()
                self.dropout = nn.Dropout(dropout)
                self.fc2 = nn.Linear(n_hidden, n_output)

            def forward(self, x):
                x = self.fc1(x)
                x = self.relu(x)
                x = self.dropout(x)
                x = self.fc2(x)
                return x

        n_input = X_train.shape[1]
        self.model = SimpleMLP(n_input, self.n_hidden, self.n_channels, self.dropout)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(),
                               lr=self.learning_rate,
                               weight_decay=self.weight_decay)

        # Training loop with early stopping
        best_val_loss = float('inf')
        patience_counter = 0
        history = {'train_loss': [], 'val_loss': []}

        for epoch in range(self.n_epochs):
            # Training
            self.model.train()
            optimizer.zero_grad()
            y_pred = self.model(X_tr_t)
            train_loss = criterion(y_pred, y_tr_t)
            train_loss.backward()
            optimizer.step()

            # Validation
            self.model.eval()
            with torch.no_grad():
                y_val_pred = self.model(X_val_t)
                val_loss = criterion(y_val_pred, y_val_t).item()

            # Record history
            history['train_loss'].append(train_loss.item())
            history['val_loss'].append(val_loss)

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= self.early_stopping_patience:
                    if self.verbose:
                        print(f"    Early stopping at epoch {epoch+1}")
                    break

            if self.verbose and (epoch + 1) % 20 == 0:
                print(f"    Epoch {epoch+1}/{self.n_epochs}: "
                      f"train_loss={train_loss.item():.4f}, "
                      f"val_loss={val_loss:.4f}")

        # Load best model
        self.model.load_state_dict(self.best_model_state)
        self.model.eval()
        self.training_history = history

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
        import torch

        if self.model is None:
            raise RuntimeError("Model must be fitted before prediction")

        self.model.eval()
        with torch.no_grad():
            X_test_t = torch.FloatTensor(X_test)
            y_pred = self.model(X_test_t).numpy()

        # (n_samples, n_channels) → (n_channels, n_samples)
        return y_pred.T

    def get_name(self):
        return f"MLP(hidden={self.n_hidden},lr={self.learning_rate})"

    def get_params(self):
        return {
            "method": "MLP",
            "n_hidden": self.n_hidden,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "dropout": self.dropout,
            "channels": self.n_channels
        }

    def get_weights(self):
        """
        Get first layer weights for visualization

        Returns
        -------
        weights : ndarray, shape (n_hidden, n_input)
            First layer weight matrix
        """
        if self.model is None:
            raise RuntimeError("Model must be fitted first")

        return self.model.fc1.weight.detach().numpy()
