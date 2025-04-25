"""Download historical data and build feature matrices for all tickers."""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.data.features import build_feature_matrix
from src.data.ingestion import download_ohlcv
from src.data.storage import init_db, save_features, save_ohlcv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def seed():
    engine = init_db()
    logger.info(f"Seeding data for tickers: {settings.tickers}")

    for ticker in settings.tickers:
        try:
            # Download raw OHLCV
            df = download_ohlcv(ticker, period=f"{settings.lookback_years}y")
            save_ohlcv(df)

            # Build and store features
            features = build_feature_matrix(df)
            save_features(features)

            logger.info(f"[OK] {ticker}: {len(df)} OHLCV rows, {len(features)} feature rows")
        except Exception as e:
            logger.error(f"[FAIL] {ticker}: {e}")

    logger.info("Seeding complete")


if __name__ == "__main__":
    seed()
