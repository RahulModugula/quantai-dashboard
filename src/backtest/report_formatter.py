"""Format backtest results for display."""
import pandas as pd


class ReportFormatter:
    """Format backtest results for human-readable output."""

    @staticmethod
    def format_metrics(metrics: dict) -> str:
        """Format performance metrics as text."""
        lines = [
            "=" * 50,
            "BACKTEST PERFORMANCE METRICS",
            "=" * 50,
        ]

        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"{key:.<30} {value:>10.2%}")
            else:
                lines.append(f"{key:.<30} {value:>10}")

        lines.append("=" * 50)
        return "\n".join(lines)

    @staticmethod
    def format_trades_table(trades: list[dict]) -> pd.DataFrame:
        """Convert trades to formatted DataFrame."""
        if not trades:
            return pd.DataFrame()

        df = pd.DataFrame(trades)

        # Format columns
        if "entry_price" in df.columns:
            df["entry_price"] = df["entry_price"].apply(lambda x: f"${x:.2f}")
        if "exit_price" in df.columns:
            df["exit_price"] = df["exit_price"].apply(lambda x: f"${x:.2f}")
        if "pnl" in df.columns:
            df["pnl"] = df["pnl"].apply(lambda x: f"${x:.2f}")

        return df

    @staticmethod
    def format_equity_curve(equity_curve: list[dict]) -> pd.DataFrame:
        """Format equity curve for display."""
        df = pd.DataFrame(equity_curve)

        if "value" in df.columns:
            df["value"] = df["value"].apply(lambda x: f"${x:,.0f}")

        return df

    @staticmethod
    def summary_statistics(metrics: dict) -> dict:
        """Extract key statistics for summary."""
        return {
            "Total Return": f"{metrics.get('total_return', 0):.2%}",
            "Sharpe Ratio": f"{metrics.get('sharpe_ratio', 0):.2f}",
            "Max Drawdown": f"{metrics.get('max_drawdown', 0):.2%}",
            "Win Rate": f"{metrics.get('win_rate', 0):.2%}",
            "Total Trades": metrics.get('total_trades', 0),
        }
