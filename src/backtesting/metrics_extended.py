"""Extended backtest metrics and KPIs."""


def profit_factor(gross_profit: float, gross_loss: float) -> float:
    """Calculate profit factor (gross profit / gross loss)."""
    if gross_loss == 0:
        return 0.0
    return abs(gross_profit) / abs(gross_loss)


def recovery_factor(net_profit: float, max_drawdown: float) -> float:
    """Recovery factor (net profit / max drawdown)."""
    if max_drawdown == 0:
        return 0.0
    return net_profit / abs(max_drawdown)


def ulcer_index(returns: list[float], lookback: int = 14) -> float:
    """Ulcer index (measure of downside volatility)."""
    import numpy as np
    running_max = np.maximum.accumulate(returns[-lookback:])
    drawdowns = (np.array(returns[-lookback:]) - running_max) / running_max
    return np.sqrt(np.mean(drawdowns ** 2))


def pain_index(returns: list[float]) -> float:
    """Pain index (average duration and magnitude of drawdowns)."""
    import numpy as np
    cumulative = np.cumprod(1 + np.array(returns))
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return np.mean(np.abs(drawdowns[drawdowns < 0]))


def calmar_ratio(annual_return: float, max_drawdown: float) -> float:
    """Calmar ratio (annual return / max drawdown)."""
    if max_drawdown == 0:
        return 0.0
    return annual_return / abs(max_drawdown)
