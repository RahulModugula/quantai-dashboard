"""Unit tests for the model and feature ablation study module."""

import pandas as pd
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_oos(n: int = 50) -> pd.DataFrame:
    import pandas as pd

    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "AAPL",
            "probability_up": 0.6,
        }
    )


def _make_mock_backtest_run(sharpe: float = 0.8) -> MagicMock:
    run = MagicMock()
    run.metrics = {"sharpe_ratio": sharpe}
    run.final_value = 105_000.0
    return run


def _make_mock_train_result(sharpe: float = 0.8) -> MagicMock:
    result = MagicMock()
    result.oos_predictions = _make_mock_oos()
    result.metrics = {"sharpe_ratio": sharpe}
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_model_ablation_returns_all_members():
    """run_model_ablation should include all four ensemble members in output."""
    from src.models.ablation import run_model_ablation

    mock_run = _make_mock_train_result(sharpe=0.8)
    mock_bt_run = _make_mock_backtest_run(sharpe=0.6)

    with (
        patch("src.models.ablation.walk_forward_train", return_value=mock_run),
        patch(
            "src.models.ablation.load_ohlcv",
            return_value=pd.DataFrame({"date": [], "close": [], "ticker": []}),
        ),
        patch("src.models.ablation.WalkForwardBacktester") as MockBT,
    ):
        MockBT.return_value.run.return_value = mock_bt_run
        result = run_model_ablation("AAPL")

    assert "members" in result
    for member in ("rf", "xgb", "lgbm", "lstm"):
        assert member in result["members"], f"Missing member: {member}"


def test_feature_ablation_returns_all_groups():
    """run_feature_ablation should include all default feature groups."""
    from src.models.ablation import DEFAULT_FEATURE_GROUPS, run_feature_ablation

    mock_run = _make_mock_train_result(sharpe=0.8)
    mock_bt_run = _make_mock_backtest_run(sharpe=0.65)

    with (
        patch("src.models.ablation.walk_forward_train", return_value=mock_run),
        patch(
            "src.models.ablation.load_ohlcv",
            return_value=pd.DataFrame({"date": [], "close": [], "ticker": []}),
        ),
        patch("src.models.ablation.load_features", return_value=pd.DataFrame()),
        patch("src.models.ablation.WalkForwardBacktester") as MockBT,
    ):
        MockBT.return_value.run.return_value = mock_bt_run
        result = run_feature_ablation("AAPL", fast_mode=False)

    assert "groups" in result
    for group in DEFAULT_FEATURE_GROUPS:
        assert group in result["groups"], f"Missing group: {group}"


def test_sharpe_delta_is_float():
    """marginal_contribution should be a float for each ablated member."""
    from src.models.ablation import run_model_ablation

    mock_run = _make_mock_train_result(sharpe=0.8)
    mock_bt_run = _make_mock_backtest_run(sharpe=0.7)

    with (
        patch("src.models.ablation.walk_forward_train", return_value=mock_run),
        patch(
            "src.models.ablation.load_ohlcv",
            return_value=pd.DataFrame({"date": [], "close": [], "ticker": []}),
        ),
        patch("src.models.ablation.WalkForwardBacktester") as MockBT,
    ):
        MockBT.return_value.run.return_value = mock_bt_run
        result = run_model_ablation("AAPL")

    for member, data in result["members"].items():
        assert isinstance(data["marginal_contribution"], float), (
            f"marginal_contribution for {member} is not float"
        )


def test_conclusion_is_string():
    """conclusion field should be a non-empty string."""
    from src.models.ablation import run_model_ablation

    mock_run = _make_mock_train_result(sharpe=0.8)
    mock_bt_run = _make_mock_backtest_run(sharpe=0.5)

    with (
        patch("src.models.ablation.walk_forward_train", return_value=mock_run),
        patch(
            "src.models.ablation.load_ohlcv",
            return_value=pd.DataFrame({"date": [], "close": [], "ticker": []}),
        ),
        patch("src.models.ablation.WalkForwardBacktester") as MockBT,
    ):
        MockBT.return_value.run.return_value = mock_bt_run
        result = run_model_ablation("AAPL")

    assert isinstance(result["conclusion"], str)
    assert len(result["conclusion"]) > 0


def test_ablation_module_imports():
    """Sanity check: ablation module imports without error."""
    from src.models.ablation import run_feature_ablation, run_model_ablation  # noqa: F401

    assert callable(run_model_ablation)
    assert callable(run_feature_ablation)
