"""CLI entrypoint for walk-forward model training."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.models.training import walk_forward_train

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train the ML ensemble model")
    parser.add_argument("--tickers", nargs="+", default=settings.tickers)
    parser.add_argument("--window", type=int, default=settings.walk_forward_window)
    parser.add_argument("--interval", type=int, default=settings.retrain_interval)
    args = parser.parse_args()

    for ticker in args.tickers:
        logger.info(f"Training {ticker}...")
        try:
            result = walk_forward_train(ticker, window=args.window, retrain_interval=args.interval)
            logger.info(
                f"[OK] {ticker}: version={result.model_version}, "
                f"mean_acc={result.mean_test_accuracy:.3f}, "
                f"folds={len(result.fold_results)}"
            )
        except Exception as e:
            logger.error(f"[FAIL] {ticker}: {e}")


if __name__ == "__main__":
    main()
