import pytest
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from datetime import datetime

from src.data.schemas import PredictionResponse


@pytest.fixture
def mock_model_bundle():
    """Mock a trained model bundle."""
    mock_scaler = Mock()
    mock_scaler.transform.return_value = np.array([[1.0, 2.0, 3.0]])

    mock_model = Mock()
    mock_model.predict_proba.return_value = np.array([0.3, 0.7])
    mock_model.feature_importances.return_value = {
        "rsi_14": 0.25,
        "macd": 0.20,
        "bb_pct_b": 0.15,
    }

    return {
        "model": mock_model,
        "scaler": mock_scaler,
    }, {
        "feature_names": ["rsi_14", "macd", "bb_pct_b"],
    }


@pytest.fixture
def mock_paper_trader():
    """Mock a paper trader."""
    mock_portfolio = Mock()
    mock_portfolio.get_value.return_value = 100_000.0
    mock_portfolio.positions = {}

    mock_trader = Mock()
    mock_trader.portfolio = mock_portfolio

    return mock_trader


@pytest.fixture
def sample_features_df():
    """Create sample features DataFrame."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    return pd.DataFrame({
        "date": dates,
        "ticker": "AAPL",
        "rsi_14": np.random.uniform(30, 70, 100),
        "macd": np.random.randn(100),
        "bb_pct_b": np.random.uniform(0, 1, 100),
        "close": 150.0 + np.cumsum(np.random.randn(100) * 0.5),
    })


@patch("src.api.routes.predictions.get_paper_trader")
@patch("src.api.routes.predictions.get_model_bundle")
@patch("src.api.routes.predictions.load_features")
def test_get_prediction_success(
    mock_load_features,
    mock_get_bundle,
    mock_get_trader,
    mock_model_bundle,
    mock_paper_trader,
    sample_features_df,
):
    """Test successful prediction retrieval."""
    from src.api.routes.predictions import get_prediction

    mock_get_bundle.return_value = mock_model_bundle
    mock_get_trader.return_value = mock_paper_trader
    mock_load_features.return_value = sample_features_df

    result = get_prediction("AAPL")

    assert isinstance(result, PredictionResponse)
    assert result.ticker == "AAPL"
    assert 0.0 <= result.probability_up <= 1.0
    assert result.signal in ["buy", "sell", "hold"]
    assert 0.0 <= result.confidence <= 1.0
    assert result.disclaimer is not None


@patch("src.api.routes.predictions.get_model_bundle")
def test_get_prediction_no_model(mock_get_bundle):
    """Test prediction when no model is trained."""
    from fastapi import HTTPException
    from src.api.routes.predictions import get_prediction

    mock_get_bundle.return_value = (None, {})

    with pytest.raises(HTTPException) as exc_info:
        get_prediction("AAPL")

    assert exc_info.value.status_code == 503


@patch("src.api.routes.predictions.get_paper_trader")
@patch("src.api.routes.predictions.get_model_bundle")
@patch("src.api.routes.predictions.load_features")
def test_get_prediction_missing_data(
    mock_load_features,
    mock_get_bundle,
    mock_get_trader,
    mock_model_bundle,
    mock_paper_trader,
):
    """Test prediction when no feature data exists."""
    from fastapi import HTTPException
    from src.api.routes.predictions import get_prediction

    mock_get_bundle.return_value = mock_model_bundle
    mock_get_trader.return_value = mock_paper_trader
    mock_load_features.return_value = pd.DataFrame()  # Empty DataFrame

    with pytest.raises(HTTPException) as exc_info:
        get_prediction("MISSING")

    assert exc_info.value.status_code == 404


@patch("src.api.routes.predictions.get_paper_trader")
@patch("src.api.routes.predictions.get_model_bundle")
@patch("src.api.routes.predictions.load_features")
def test_get_prediction_handles_feature_importance_error(
    mock_load_features,
    mock_get_bundle,
    mock_get_trader,
    sample_features_df,
    mock_paper_trader,
):
    """Test that feature importance extraction errors are handled gracefully."""
    from src.api.routes.predictions import get_prediction

    mock_scaler = Mock()
    mock_scaler.transform.return_value = np.array([[1.0, 2.0, 3.0]])

    mock_model = Mock()
    mock_model.predict_proba.return_value = np.array([0.3, 0.7])
    mock_model.feature_importances.side_effect = Exception("Feature import error")

    mock_get_bundle.return_value = (
        {"model": mock_model, "scaler": mock_scaler},
        {"feature_names": ["rsi_14", "macd", "bb_pct_b"]},
    )
    mock_get_trader.return_value = mock_paper_trader
    mock_load_features.return_value = sample_features_df

    result = get_prediction("AAPL")

    assert result.feature_importances == {}


@patch("src.api.routes.predictions.get_paper_trader")
@patch("src.api.routes.predictions.get_model_bundle")
@patch("src.api.routes.predictions.load_features")
def test_get_prediction_with_existing_position(
    mock_load_features,
    mock_get_bundle,
    mock_get_trader,
    mock_model_bundle,
    sample_features_df,
):
    """Test prediction when portfolio already has position in ticker."""
    from src.api.routes.predictions import get_prediction

    mock_trader = Mock()
    mock_portfolio = Mock()
    mock_portfolio.get_value.return_value = 50_000.0
    mock_portfolio.positions = {"AAPL": 100}  # Existing position
    mock_trader.portfolio = mock_portfolio

    mock_get_bundle.return_value = mock_model_bundle
    mock_get_trader.return_value = mock_trader
    mock_load_features.return_value = sample_features_df

    result = get_prediction("AAPL")

    assert result.ticker == "AAPL"
    # Signal should be different when position exists


@patch("src.config.settings")
@patch("src.api.routes.predictions.get_prediction")
def test_list_predictions(mock_get_pred, mock_settings):
    """Test listing predictions for all tickers."""
    from src.api.routes.predictions import list_predictions
    from src.data.schemas import PredictionResponse

    mock_settings.tickers = ["AAPL", "MSFT", "GOOGL"]

    pred1 = PredictionResponse(
        ticker="AAPL",
        timestamp=datetime.now(),
        probability_up=0.7,
        signal="buy",
        confidence=0.8,
    )
    pred2 = PredictionResponse(
        ticker="MSFT",
        timestamp=datetime.now(),
        probability_up=0.5,
        signal="hold",
        confidence=0.5,
    )

    mock_get_pred.side_effect = [pred1, pred2, Exception("Failed")]

    results = list_predictions()

    assert len(results) == 3
    assert results[0]["ticker"] == "AAPL"
    assert results[1]["ticker"] == "MSFT"
    assert "error" in results[2]
