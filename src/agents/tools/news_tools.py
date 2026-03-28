"""News tools — fetches recent news via yfinance (free, no auth required)."""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_news",
            "description": (
                "Fetch recent news headlines and summaries for a stock ticker. "
                "Returns the latest news articles from financial sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL",
                    },
                    "max_items": {
                        "type": "integer",
                        "description": "Maximum number of news items to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["ticker"],
            },
        },
    },
]


def get_recent_news(ticker: str, max_items: int = 10) -> dict[str, Any]:
    """Fetch recent news for ticker via yfinance."""
    ticker = ticker.upper()
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        raw_news = t.news or []

        articles = []
        for item in raw_news[:max_items]:
            content = item.get("content", {})
            # yfinance news structure varies by version
            title = content.get("title") or item.get("title", "")
            summary = (
                content.get("summary") or content.get("description") or item.get("summary", "")
            )
            provider = content.get("provider", {}).get("displayName") or item.get("publisher", "")
            pub_time = content.get("pubDate") or item.get("providerPublishTime")
            if isinstance(pub_time, (int, float)):
                pub_str = datetime.utcfromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M UTC")
            else:
                pub_str = str(pub_time) if pub_time else ""

            articles.append(
                {
                    "title": title,
                    "summary": summary[:500] if summary else "",
                    "publisher": provider,
                    "published": pub_str,
                }
            )

        if not articles:
            return {
                "ticker": ticker,
                "articles": [],
                "message": "No recent news found",
            }

        return {
            "ticker": ticker,
            "count": len(articles),
            "articles": articles,
            "fetched_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
    except Exception as exc:
        logger.warning(f"News fetch failed for {ticker}: {exc}")
        return {"error": str(exc), "ticker": ticker, "articles": []}


def dispatch(tool_name: str, args: dict) -> dict:
    """Route a tool call by name."""
    if tool_name == "get_recent_news":
        return get_recent_news(
            args.get("ticker", ""),
            max_items=args.get("max_items", 10),
        )
    return {"error": f"Unknown tool: {tool_name}"}
