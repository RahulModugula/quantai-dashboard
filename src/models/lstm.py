import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class LSTMNet(nn.Module):
    def __init__(
        self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        return self.fc(last_hidden).squeeze(-1)


class LSTMWrapper:
    """Sklearn-compatible wrapper around a PyTorch LSTM for binary classification."""

    def __init__(
        self,
        input_dim: int = 20,
        hidden_dim: int = 64,
        sequence_length: int = 20,
        num_layers: int = 2,
        dropout: float = 0.2,
        lr: float = 1e-3,
        epochs: int = 50,
        batch_size: int = 64,
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.sequence_length = sequence_length
        self.num_layers = num_layers
        self.dropout = dropout
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None

    def _create_sequences(self, X: np.ndarray, y: np.ndarray | None = None):
        """Convert flat feature matrix into overlapping sequences."""
        sequences = []
        targets = []
        for i in range(len(X) - self.sequence_length):
            sequences.append(X[i : i + self.sequence_length])
            if y is not None:
                targets.append(y[i + self.sequence_length])

        X_seq = np.array(sequences, dtype=np.float32)
        if y is not None:
            y_seq = np.array(targets, dtype=np.float32)
            return X_seq, y_seq
        return X_seq

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_seq, y_seq = self._create_sequences(X, y)
        if len(X_seq) == 0:
            return self

        self.input_dim = X_seq.shape[2]
        self.model = LSTMNet(self.input_dim, self.hidden_dim, self.num_layers, self.dropout).to(
            self.device
        )

        dataset = TensorDataset(
            torch.FloatTensor(X_seq).to(self.device),
            torch.FloatTensor(y_seq).to(self.device),
        )
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.BCELoss()

        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                preds = self.model(X_batch)
                loss = criterion(preds, y_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item()

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            return np.full(max(0, len(X) - self.sequence_length), 0.5)

        X_seq = self._create_sequences(X)
        if len(X_seq) == 0:
            return np.array([])

        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_seq).to(self.device)
            probs = self.model(X_tensor).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs >= 0.5).astype(int)

    def get_params(self) -> dict:
        return {
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
            "sequence_length": self.sequence_length,
            "num_layers": self.num_layers,
            "epochs": self.epochs,
        }
