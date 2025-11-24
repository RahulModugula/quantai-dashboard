import numpy as np
import pandas as pd

from src.models.drift import detect_drift, rolling_accuracy


def _make_predictions(n: int, accuracy: float, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    actual = rng.integers(0, 2, size=n)
    prediction = actual.copy()
    flip_count = int(n * (1 - accuracy))
    flip_idx = rng.choice(n, size=flip_count, replace=False)
    prediction[flip_idx] = 1 - prediction[flip_idx]
    return pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=n, freq="B"),
            "prediction": prediction,
            "actual": actual,
        }
    )


def test_no_drift_stable_model():
    preds = _make_predictions(400, accuracy=0.55)
    result = detect_drift(preds, lookback_window=63, baseline_window=252)
    assert not result["drift_detected"]


def test_drift_detected_degraded_model():
    good = _make_predictions(300, accuracy=0.60, seed=1)
    bad = _make_predictions(100, accuracy=0.45, seed=2)
    bad["date"] = pd.date_range(good["date"].iloc[-1] + pd.Timedelta(days=1), periods=100, freq="B")
    preds = pd.concat([good, bad], ignore_index=True)
    result = detect_drift(preds, lookback_window=80, baseline_window=200)
    assert result["drift_detected"]
    assert result["accuracy_delta"] > 0.05


def test_drift_insufficient_data():
    preds = _make_predictions(50, accuracy=0.55)
    result = detect_drift(preds)
    assert not result["drift_detected"]
    assert result["reason"] == "insufficient data"


def test_rolling_accuracy_length():
    preds = _make_predictions(200, accuracy=0.55)
    ra = rolling_accuracy(preds, window=20)
    assert len(ra) == 200
