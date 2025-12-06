"""
Walk-forward backtesting engine.

Critical invariant: predictions[t] were generated using ONLY data available
before time t. The engine enforces this by aligning predictions with prices
strictly on matching dates, with no lookahead.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from src.backtest.metrics import compute_all_metrics
from src.backtest.slippage import SlippageModel

logger = logging.getLogger(__name__)


@dataclass
class BacktestRun:
    ticker: str
    initial_capital: float
    final_value: float
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: dict
    oos_predictions: pd.DataFrame = field(default_factory=pd.DataFrame)
    total_slippage_cost: float = 0.0


class WalkForwardBacktester:
    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        buy_threshold: float = 0.6,
        sell_threshold: float = 0.4,
        max_position_pct: float = 0.10,
        slippage_model: Optional[SlippageModel] = None,
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.max_position_pct = max_position_pct
        self.slippage_model = slippage_model

    def run(
        self,
        oos_predictions: pd.DataFrame,
        prices: pd.DataFrame,
    ) -> BacktestRun:
        """
        Run backtest on out-of-sample predictions.

        Args:
            oos_predictions: DataFrame with columns [date, ticker, probability_up]
            prices: DataFrame with columns [date, ticker, close]
        """
        ticker = oos_predictions["ticker"].iloc[0]

        # Merge predictions with next-day prices — predictions[t] act on price[t+1]
        pred = oos_predictions[["date", "ticker", "probability_up"]].copy()
        pred["date"] = pd.to_datetime(pred["date"])

        px = prices[prices["ticker"] == ticker][["date", "close"]].copy()
        px["date"] = pd.to_datetime(px["date"])
        px = px.sort_values("date").reset_index(drop=True)

        # Shift prices by 1 so we execute at next-day open (approximated as close)
        px["next_close"] = px["close"].shift(-1)

        # Include volume if present, for slippage calculation
        price_cols = ["date", "close", "next_close"]
        if "volume" in prices.columns:
            vol_series = prices[prices["ticker"] == ticker][["date", "volume"]].copy()
            vol_series["date"] = pd.to_datetime(vol_series["date"])
            px = pd.merge(px, vol_series, on="date", how="left")
            price_cols.append("volume")

        merged = pd.merge(pred, px[price_cols], on="date", how="inner").dropna(
            subset=["next_close"]
        )
        merged = merged.sort_values("date").reset_index(drop=True)

        # Compute rolling 20-day average volume if available
        _fallback_volume = 1_000_000.0
        if "volume" in merged.columns:
            merged["avg_volume"] = (
                merged["volume"].rolling(20, min_periods=1).mean().fillna(_fallback_volume)
            )
        else:
            merged["avg_volume"] = _fallback_volume

        if merged.empty:
            raise ValueError(
                f"No overlapping dates between predictions and prices for {ticker}. "
                "Ensure seed_data.py has been run and predictions cover the same date range."
            )

        cash = self.initial_capital
        shares = 0.0
        equity_values = []
        trades_log = []
        total_slippage_cost = 0.0

        for _, row in merged.iterrows():
            price = float(row["next_close"])
            prob_up = float(row["probability_up"])
            date = row["date"]
            avg_vol = float(row["avg_volume"])
            portfolio_value = cash + shares * price

            if prob_up >= self.buy_threshold and shares == 0:
                # Buy — size to max_position_pct of portfolio
                target_value = portfolio_value * self.max_position_pct
                shares_to_buy = target_value / price
                order_value = shares_to_buy * price

                # Apply slippage to fill price
                if self.slippage_model is not None:
                    fill_price = self.slippage_model.apply(price, order_value, avg_vol, "buy")
                else:
                    fill_price = price
                slippage_cost = (fill_price - price) * shares_to_buy
                total_slippage_cost += slippage_cost

                cost = shares_to_buy * fill_price
                commission = cost * self.commission_pct

                if cash >= cost + commission:
                    cash -= cost + commission
                    shares += shares_to_buy
                    trades_log.append(
                        {
                            "date": date,
                            "ticker": ticker,
                            "side": "buy",
                            "shares": shares_to_buy,
                            "price": fill_price,
                            "commission": commission,
                            "pnl": None,
                        }
                    )

            elif prob_up <= self.sell_threshold and shares > 0:
                # Sell all
                order_value = shares * price

                # Apply slippage to fill price
                if self.slippage_model is not None:
                    fill_price = self.slippage_model.apply(price, order_value, avg_vol, "sell")
                else:
                    fill_price = price
                slippage_cost = (price - fill_price) * shares
                total_slippage_cost += slippage_cost

                proceeds = shares * fill_price
                commission = proceeds * self.commission_pct

                # Find last buy to compute realized PnL
                last_buy = next((t for t in reversed(trades_log) if t["side"] == "buy"), None)
                realized_pnl = (
                    (fill_price - last_buy["price"]) * shares - commission if last_buy else 0
                )

                cash += proceeds - commission
                trades_log.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "side": "sell",
                        "shares": shares,
                        "price": fill_price,
                        "commission": commission,
                        "pnl": realized_pnl,
                    }
                )
                shares = 0.0

            portfolio_value = cash + shares * price
            equity_values.append({"date": date, "value": portfolio_value})

        equity_df = pd.DataFrame(equity_values).set_index("date")
        equity_curve = equity_df["value"]

        trades_df = (
            pd.DataFrame(trades_log)
            if trades_log
            else pd.DataFrame(
                columns=["date", "ticker", "side", "shares", "price", "commission", "pnl"]
            )
        )

        # Compute trade-level analytics
        if not trades_df.empty:
            sell_trades = trades_df[trades_df["side"] == "sell"]
            if not sell_trades.empty:
                avg_win = sell_trades[sell_trades["pnl"] > 0]["pnl"].mean()
                avg_loss = (
                    abs(sell_trades[sell_trades["pnl"] <= 0]["pnl"].mean())
                    if (sell_trades["pnl"] <= 0).any()
                    else 0
                )
                trades_df.attrs["avg_win"] = float(avg_win) if not pd.isna(avg_win) else 0
                trades_df.attrs["avg_loss"] = float(avg_loss) if not pd.isna(avg_loss) else 0

        metrics = compute_all_metrics(equity_curve, trades_df)
        final_value = (
            float(equity_curve.iloc[-1]) if len(equity_curve) > 0 else self.initial_capital
        )

        logger.info(
            f"Backtest {ticker}: final={final_value:.2f}, "
            f"return={metrics['total_return']:.2%}, "
            f"sharpe={metrics['sharpe_ratio']:.2f}, "
            f"max_dd={metrics['max_drawdown']:.2%}"
        )

        return BacktestRun(
            ticker=ticker,
            initial_capital=self.initial_capital,
            final_value=final_value,
            equity_curve=equity_curve,
            trades=trades_df,
            metrics=metrics,
            oos_predictions=oos_predictions,
            total_slippage_cost=total_slippage_cost,
        )
