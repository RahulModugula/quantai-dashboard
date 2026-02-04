"""Real-time price feed via Alpaca WebSocket API.

Falls back to polling yfinance if Alpaca credentials are not configured.
This allows the module to be useful in development without API keys.

Configure via environment variables:
    ALPACA_API_KEY=...
    ALPACA_SECRET_KEY=...
    ALPACA_FEED=iex  # or 'sip' for paying subscribers
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_ALPACA_WS_BASE = "wss://stream.data.alpaca.markets/v2"


class AlpacaFeed:
    """Real-time bar feed via Alpaca WebSocket streaming API.

    Uses ``websockets`` to connect to Alpaca's data stream, authenticate,
    subscribe to bar updates, and yield normalised price dicts.  Reconnects
    automatically with exponential backoff up to *max_retries* times.
    Incoming messages are buffered in a bounded ``asyncio.Queue``; when the
    queue is full the oldest message is dropped so the producer never blocks.
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        feed: str = "iex",
        reconnect_delay: float = 5.0,
        max_retries: int = 10,
        queue_size: int = 100,
    ) -> None:
        self._api_key = api_key or ""
        self._secret_key = secret_key or ""
        self._feed = feed
        self._reconnect_delay = reconnect_delay
        self._max_retries = max_retries
        self._queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=queue_size)
        self._tickers: list[str] = []
        self._closed = False
        self._ws: Any = None  # websockets.ClientConnection
        self._stats: dict[str, int] = {
            "reconnect_count": 0,
            "messages_received": 0,
            "messages_dropped": 0,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def subscribe(self, tickers: list[str]) -> None:
        """Subscribe to real-time bars for *tickers*."""
        if not tickers:
            raise ValueError("tickers must be a non-empty list")
        if not self._api_key or not self._secret_key:
            raise RuntimeError(
                "Alpaca credentials are required to open a WebSocket connection. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables, "
                "or use YFinanceFallbackFeed for development without credentials."
            )
        self._tickers = list(tickers)
        asyncio.get_event_loop().create_task(self._run())

    async def stream(self) -> AsyncIterator[dict]:
        """Yield price updates as they arrive from the Alpaca stream.

        Yields:
            {"ticker": str, "price": float, "volume": int,
             "timestamp": str, "source": "alpaca"}
        """
        while not self._closed:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                yield item
            except asyncio.TimeoutError:
                continue

    async def close(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._closed = True
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        logger.info(
            "AlpacaFeed closed. stats=%s",
            self._stats,
        )

    @property
    def stats(self) -> dict[str, int]:
        """Return a snapshot of feed statistics."""
        return dict(self._stats)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        """Background task: connect, authenticate, subscribe, and pump messages."""
        import websockets  # type: ignore[import-untyped]  # noqa: PLC0415

        url = f"{_ALPACA_WS_BASE}/{self._feed}"
        attempt = 0

        while not self._closed and attempt <= self._max_retries:
            try:
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    if attempt > 0:
                        self._stats["reconnect_count"] += 1
                    attempt = 0  # reset on successful connect

                    await self._authenticate(ws)
                    await self._send_subscription(ws)
                    await self._pump(ws)

            except Exception as exc:
                if self._closed:
                    break
                delay = min(self._reconnect_delay * (2**attempt), 60.0)
                logger.warning(
                    "AlpacaFeed connection lost (attempt %d/%d): %s. Retrying in %.1fs.",
                    attempt + 1,
                    self._max_retries,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                attempt += 1

        if attempt > self._max_retries:
            logger.error(
                "AlpacaFeed exhausted %d reconnect attempts. Giving up.",
                self._max_retries,
            )
            self._closed = True

    async def _authenticate(self, ws: Any) -> None:
        """Send auth message and wait for successful response."""
        auth_msg = json.dumps({"action": "auth", "key": self._api_key, "secret": self._secret_key})
        await ws.send(auth_msg)
        raw = await ws.recv()
        data = json.loads(raw)
        messages = data if isinstance(data, list) else [data]
        for msg in messages:
            if msg.get("T") == "error":
                raise RuntimeError(f"Alpaca auth error: {msg.get('msg', msg)}")
            if msg.get("T") == "success" and msg.get("msg") == "authenticated":
                logger.info("AlpacaFeed authenticated (feed=%s)", self._feed)
                return
        # Some versions send the welcome message first; treat non-error as ok
        logger.debug("AlpacaFeed auth response: %s", messages)

    async def _send_subscription(self, ws: Any) -> None:
        """Subscribe to bar updates for the configured tickers."""
        sub_msg = json.dumps({"action": "subscribe", "bars": self._tickers})
        await ws.send(sub_msg)
        logger.info("AlpacaFeed subscribed to bars: %s", self._tickers)

    async def _pump(self, ws: Any) -> None:
        """Read messages from the WebSocket and push parsed dicts to the queue."""
        async for raw in ws:
            if self._closed:
                break
            try:
                payload = json.loads(raw)
                messages = payload if isinstance(payload, list) else [payload]
                for msg in messages:
                    if msg.get("T") != "b":  # 'b' = bar update
                        continue
                    item = {
                        "ticker": msg.get("S", ""),
                        "price": float(msg.get("c", 0.0)),  # close price
                        "volume": int(msg.get("v", 0)),
                        "timestamp": msg.get(
                            "t",
                            datetime.now(tz=timezone.utc).isoformat(),
                        ),
                        "source": "alpaca",
                    }
                    self._stats["messages_received"] += 1
                    self._enqueue(item)
            except Exception as exc:
                logger.warning("AlpacaFeed failed to parse message: %s", exc)

    def _enqueue(self, item: dict) -> None:
        """Put *item* on the queue, dropping the oldest entry if full."""
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._stats["messages_dropped"] += 1
            except asyncio.QueueEmpty:
                pass
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            self._stats["messages_dropped"] += 1


class YFinanceFallbackFeed:
    """Poll yfinance every 60 seconds as a fallback when Alpaca creds aren't available."""

    _POLL_INTERVAL: float = 60.0

    async def stream(self, tickers: list[str]) -> AsyncIterator[dict]:
        """Yield normalised price dicts fetched via yfinance.

        Yields:
            {"ticker": str, "price": float, "volume": int,
             "timestamp": str, "source": "yfinance"}
        """
        import yfinance as yf  # type: ignore[import-untyped]  # noqa: PLC0415

        while True:
            ts = datetime.now(tz=timezone.utc).isoformat()
            try:
                data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: yf.download(
                        tickers,
                        period="1d",
                        interval="1m",
                        progress=False,
                        auto_adjust=True,
                    ),
                )
                for ticker in tickers:
                    try:
                        if len(tickers) == 1:
                            close = float(data["Close"].iloc[-1])
                            volume = int(data["Volume"].iloc[-1])
                        else:
                            close = float(data["Close"][ticker].iloc[-1])
                            volume = int(data["Volume"][ticker].iloc[-1])

                        yield {
                            "ticker": ticker,
                            "price": close,
                            "volume": volume,
                            "timestamp": ts,
                            "source": "yfinance",
                        }
                    except Exception as exc:
                        logger.warning("YFinanceFallbackFeed: could not parse %s: %s", ticker, exc)
            except Exception as exc:
                logger.error("YFinanceFallbackFeed: yfinance fetch failed: %s", exc)

            await asyncio.sleep(self._POLL_INTERVAL)


@asynccontextmanager
async def get_feed(tickers: list[str]):
    """Return the appropriate feed based on available credentials.

    If ``ALPACA_API_KEY`` and ``ALPACA_SECRET_KEY`` are set (via environment
    or ``.env``), returns an :class:`AlpacaFeed`; otherwise returns a
    :class:`YFinanceFallbackFeed`.

    Usage::

        async with get_feed(["AAPL", "MSFT"]) as feed:
            async for update in feed.stream():
                print(update)
    """
    from src.config.live_feed_config import live_feed_settings  # noqa: PLC0415

    if live_feed_settings.alpaca_api_key and live_feed_settings.alpaca_secret_key:
        logger.info("get_feed: using AlpacaFeed (feed=%s)", live_feed_settings.alpaca_feed)
        feed = AlpacaFeed(
            api_key=live_feed_settings.alpaca_api_key,
            secret_key=live_feed_settings.alpaca_secret_key,
            feed=live_feed_settings.alpaca_feed,
            reconnect_delay=live_feed_settings.live_feed_reconnect_delay,
            max_retries=live_feed_settings.live_feed_max_retries,
            queue_size=live_feed_settings.live_feed_queue_size,
        )
        await feed.subscribe(tickers)
        try:
            yield feed
        finally:
            await feed.close()
    else:
        logger.info("get_feed: Alpaca credentials not set, using YFinanceFallbackFeed")
        feed = YFinanceFallbackFeed()
        yield feed
