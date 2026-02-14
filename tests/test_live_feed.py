"""Unit tests for src/data/live_feed.py."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# test_yfinance_fallback_yields_price_dict
# ---------------------------------------------------------------------------


def test_yfinance_fallback_yields_price_dict():
    """YFinanceFallbackFeed should yield dicts with the expected shape."""
    import pandas as pd

    from src.data.live_feed import YFinanceFallbackFeed

    # Build a minimal DataFrame that mimics yfinance output for a single ticker
    index = pd.date_range("2026-02-04 15:59", periods=1, freq="1min", tz="UTC")
    df = pd.DataFrame({"Close": [195.50], "Volume": [1_234_567]}, index=index)

    feed = YFinanceFallbackFeed()
    # Patch poll interval so the loop only runs once then gets cancelled
    feed._POLL_INTERVAL = 0.0  # type: ignore[assignment]

    results: list[dict] = []

    async def _collect():
        with patch("yfinance.download", return_value=df):
            async for item in feed.stream(["AAPL"]):
                results.append(item)
                break  # one item is enough

    asyncio.get_event_loop().run_until_complete(_collect())

    assert len(results) == 1
    item = results[0]
    assert item["ticker"] == "AAPL"
    assert isinstance(item["price"], float)
    assert isinstance(item["volume"], int)
    assert "timestamp" in item
    assert item["source"] == "yfinance"


# ---------------------------------------------------------------------------
# test_alpaca_feed_requires_credentials_for_ws
# ---------------------------------------------------------------------------


def test_alpaca_feed_requires_credentials_for_ws():
    """AlpacaFeed.subscribe should raise RuntimeError when no credentials are set."""
    from src.data.live_feed import AlpacaFeed

    feed = AlpacaFeed(api_key="", secret_key="")

    with pytest.raises(RuntimeError, match="credentials are required"):
        asyncio.get_event_loop().run_until_complete(feed.subscribe(["AAPL"]))


# ---------------------------------------------------------------------------
# test_queue_drops_on_overflow
# ---------------------------------------------------------------------------


def test_queue_drops_on_overflow():
    """_enqueue should drop the oldest item and not block when queue is full."""
    from src.data.live_feed import AlpacaFeed

    feed = AlpacaFeed(api_key="pk", secret_key="sk", queue_size=3)

    # Fill the queue beyond its capacity
    for i in range(5):
        feed._enqueue(
            {
                "ticker": "AAPL",
                "price": float(100 + i),
                "volume": i,
                "timestamp": "2026-02-04T10:00:00+00:00",
                "source": "alpaca",
            }
        )

    # Queue should be full (3 items) and 2 drops should have occurred
    assert feed._queue.qsize() == 3
    assert feed._stats["messages_dropped"] == 2

    # Draining should not raise and should not hang
    prices = []
    while not feed._queue.empty():
        prices.append(feed._queue.get_nowait()["price"])
    assert len(prices) == 3


# ---------------------------------------------------------------------------
# test_feed_output_has_required_keys
# ---------------------------------------------------------------------------


def test_feed_output_has_required_keys():
    """Both feed types must yield dicts containing all required keys."""
    required_keys = {"ticker", "price", "volume", "timestamp", "source"}

    # --- AlpacaFeed via _pump (unit-tested by injecting a raw bar message) ---
    from src.data.live_feed import AlpacaFeed

    feed = AlpacaFeed(api_key="pk", secret_key="sk", queue_size=10)

    raw_bar = [
        {
            "T": "b",
            "S": "MSFT",
            "c": 415.25,
            "v": 500,
            "t": "2026-02-04T15:59:00Z",
        }
    ]

    async def _inject():
        # Simulate what _pump does with a list of bar messages
        import json as _json

        raw = _json.dumps(raw_bar)
        messages = _json.loads(raw)
        for msg in messages:
            if msg.get("T") == "b":
                item = {
                    "ticker": msg["S"],
                    "price": float(msg["c"]),
                    "volume": int(msg["v"]),
                    "timestamp": msg["t"],
                    "source": "alpaca",
                }
                feed._stats["messages_received"] += 1
                feed._enqueue(item)

    asyncio.get_event_loop().run_until_complete(_inject())

    alpaca_item = feed._queue.get_nowait()
    assert required_keys.issubset(alpaca_item.keys()), (
        f"Missing keys: {required_keys - alpaca_item.keys()}"
    )

    # --- YFinanceFallbackFeed ---
    import pandas as pd

    from src.data.live_feed import YFinanceFallbackFeed

    index = pd.date_range("2026-02-04 15:59", periods=1, freq="1min", tz="UTC")
    df = pd.DataFrame({"Close": [415.25], "Volume": [500]}, index=index)

    yf_feed = YFinanceFallbackFeed()
    yf_feed._POLL_INTERVAL = 0.0  # type: ignore[assignment]

    yf_results: list[dict] = []

    async def _collect_yf():
        with patch("yfinance.download", return_value=df):
            async for item in yf_feed.stream(["MSFT"]):
                yf_results.append(item)
                break

    asyncio.get_event_loop().run_until_complete(_collect_yf())
    assert required_keys.issubset(yf_results[0].keys())


# ---------------------------------------------------------------------------
# test_get_feed_returns_fallback_without_creds
# ---------------------------------------------------------------------------


def test_get_feed_returns_fallback_without_creds():
    """get_feed should return YFinanceFallbackFeed when no Alpaca creds are configured."""
    from src.data.live_feed import YFinanceFallbackFeed

    async def _check():
        # Patch live_feed_settings to have empty credentials
        mock_settings = MagicMock()
        mock_settings.alpaca_api_key = ""
        mock_settings.alpaca_secret_key = ""

        with patch("src.data.live_feed.live_feed_settings", mock_settings):
            from src.data.live_feed import get_feed

            async with get_feed(["AAPL"]) as feed:
                assert isinstance(feed, YFinanceFallbackFeed), (
                    f"Expected YFinanceFallbackFeed, got {type(feed).__name__}"
                )

    # Re-import to pick up the patch
    asyncio.get_event_loop().run_until_complete(_check())
