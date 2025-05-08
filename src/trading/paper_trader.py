"""
Paper trading loop - simulates live trading with virtual portfolio.

Runs in a background asyncio task. Each tick:
  1. Fetch latest price (Redis cache or yfinance fallback)
  2. Get model prediction
  3. Convert to signal
  4. Execute on virtual portfolio
  5. Store snapshot to SQLite
"""

import asyncio
import logging
from datetime import datetime

import redis

from src.config import settings
from src.data.storage import save_portfolio_snapshot, save_trades
from src.models.registry import load_metadata, load_model
from src.trading.portfolio import Portfolio
from src.trading.signals import SignalType, generate_signal

logger = logging.getLogger(__name__)


class PaperTrader:
    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or settings.tickers
        self.portfolio = Portfolio(
            initial_capital=settings.initial_capital,
            commission_pct=settings.commission_pct,
        )
        self._models: dict = {}
        self._scalers: dict = {}
        self._running = False
        self._redis: redis.Redis | None = None

    def _init_redis(self):
        try:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Redis connected")
        except Exception:
            logger.warning("Redis unavailable, will use yfinance fallback")
            self._redis = None

    def _load_models(self):
        """Load the latest trained model for each ticker."""
        try:
            bundle = load_model()
            self._model = bundle["model"]
            self._scaler = bundle["scaler"]
            meta = load_metadata()
            self._feature_names = meta.get("feature_names", [])
            logger.info(f"Loaded model version {meta.get('version_id')}")
        except FileNotFoundError:
            logger.warning("No trained model found. Run train_model.py first.")
            self._model = None
            self._scaler = None
            self._feature_names = []

    def _get_latest_price(self, ticker: str) -> float | None:
        """Fetch latest price from Redis cache, falling back to yfinance."""
        if self._redis:
            try:
                price = self._redis.get(f"price:{ticker}")
                if price:
                    return float(price)
            except Exception:
                pass

        try:
            import yfinance as yf
            data = yf.Ticker(ticker).fast_info
            return float(data.last_price)
        except Exception as e:
            logger.error(f"Could not fetch price for {ticker}: {e}")
            return None

    def _get_prediction(self, ticker: str, price: float) -> float:
        """Get model probability for next-day up move."""
        if self._model is None:
            return 0.5  # No model — return neutral

        if self._redis:
            try:
                prob = self._redis.get(f"prediction:{ticker}")
                if prob:
                    return float(prob)
            except Exception:
                pass

        return 0.5

    def _cache_prices(self, prices: dict[str, float]):
        """Write latest prices to Redis."""
        if not self._redis:
            return
        try:
            pipe = self._redis.pipeline()
            for ticker, price in prices.items():
                pipe.set(f"price:{ticker}", price, ex=60)
            pipe.execute()
        except Exception:
            pass

    async def tick(self):
        """One trading tick — fetch prices, generate signals, execute."""
        now = datetime.now()
        current_prices = {}

        for ticker in self.tickers:
            price = self._get_latest_price(ticker)
            if price:
                current_prices[ticker] = price

        if not current_prices:
            return

        self._cache_prices(current_prices)

        # Generate signals and execute
        new_trades = []
        for ticker, price in current_prices.items():
            prob_up = self._get_prediction(ticker, price)
            has_position = ticker in self.portfolio.positions
            portfolio_value = self.portfolio.get_value(current_prices)

            signal = generate_signal(
                ticker=ticker,
                probability_up=prob_up,
                portfolio_value=portfolio_value,
                current_price=price,
                has_position=has_position,
                buy_threshold=settings.buy_threshold,
                sell_threshold=settings.sell_threshold,
                max_position_pct=settings.max_position_pct,
            )

            if signal.signal_type == SignalType.BUY:
                trade = self.portfolio.buy(ticker, signal.suggested_shares, price, now)
                if trade:
                    new_trades.append(trade)
            elif signal.signal_type == SignalType.SELL:
                pos = self.portfolio.positions.get(ticker)
                if pos:
                    trade = self.portfolio.sell(ticker, pos.shares, price, now)
                    if trade:
                        new_trades.append(trade)

        # Store snapshot
        snap = self.portfolio.snapshot(current_prices, now)
        try:
            save_portfolio_snapshot(snap)
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    async def run(self):
        """Main trading loop."""
        self._init_redis()
        self._load_models()
        self._running = True
        logger.info("Paper trader started")

        while self._running:
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Tick error: {e}")
            await asyncio.sleep(settings.ws_update_interval)

    def stop(self):
        self._running = False
        logger.info("Paper trader stopped")
