"""CLI entrypoint for walk-forward backtesting."""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtest.engine import WalkForwardBacktester
from src.backtest.report import generate_report
from src.config import settings
from src.data.storage import load_features, load_ohlcv
from src.models.training import walk_forward_train

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run walk-forward backtest")
    parser.add_argument("--tickers", nargs="+", default=settings.tickers[:1])
    parser.add_argument("--capital", type=float, default=settings.initial_capital)
    parser.add_argument("--output", default="backtest_report.json")
    args = parser.parse_args()

    backtester = WalkForwardBacktester(
        initial_capital=args.capital,
        commission_pct=settings.commission_pct,
        buy_threshold=settings.buy_threshold,
        sell_threshold=settings.sell_threshold,
    )

    reports = []
    for ticker in args.tickers:
        logger.info(f"Backtesting {ticker}...")
        try:
            train_result = walk_forward_train(ticker)
            prices = load_ohlcv(ticker)
            prices["date"] = prices["date"].astype(str)

            run = backtester.run(
                oos_predictions=train_result.oos_predictions,
                prices=prices,
            )
            report = generate_report(run)
            reports.append(report)

            m = report["metrics"]
            logger.info(
                f"[OK] {ticker}: return={m['total_return']:.2%}, "
                f"sharpe={m['sharpe_ratio']:.2f}, max_dd={m['max_drawdown']:.2%}, "
                f"win_rate={m['win_rate']:.2%}"
            )
        except Exception as e:
            logger.error(f"[FAIL] {ticker}: {e}")

    with open(args.output, "w") as f:
        json.dump(reports, f, indent=2, default=str)
    logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
