"""SEC EDGAR tools — fetches recent filings via the free EDGAR full-text search API.

Notes on reliability
--------------------
EDGAR full-text search is best-effort. Queries match against the filing text
corpus, not a structured company master. Consequences:
  * small / private / recently renamed companies return zero hits
  * ambiguous names (e.g. "Apple") match unrelated filers
  * the SEC does not publish uptime guarantees for this endpoint

We try a quoted exact-phrase query first, then fall back to an unquoted broad
query if the exact phrase returned nothing. Callers should treat empty results
as "no signal", not "no filings exist".
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
_USER_AGENT = "QuantAI Research research@quantai.example.com"
_DEFAULT_LOOKBACK_DAYS = 90
_REQUEST_TIMEOUT_S = 15

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_sec_filings",
            "description": (
                "Fetch recent SEC EDGAR filings (8-K, 10-Q, 10-K, insider trading) for a company. "
                "Returns filing descriptions, types, and dates. Free API, no authentication needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name to search for, e.g. 'Apple Inc' or 'Microsoft'",
                    },
                    "form_types": {
                        "type": "string",
                        "description": "Comma-separated SEC form types to filter (default: '8-K,10-Q')",
                        "default": "8-K,10-Q",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of filings to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["company_name"],
            },
        },
    },
]


async def _edgar_query(
    session: aiohttp.ClientSession,
    q: str,
    form_types: str,
    since: str,
) -> list[dict[str, Any]]:
    """Run one EDGAR full-text search request and return the raw hits list.

    Raises aiohttp / asyncio exceptions; callers handle them.
    """
    async with session.get(
        _EDGAR_SEARCH_URL,
        params={
            "q": q,
            "dateRange": "custom",
            "startdt": since,
            "forms": form_types,
        },
        timeout=aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_S),
    ) as resp:
        if resp.status != 200:
            logger.info(f"EDGAR returned HTTP {resp.status} for q={q!r}")
            return []
        data = await resp.json(content_type=None)
        return data.get("hits", {}).get("hits", []) or []


def _format_hit(hit: dict, fallback_company: str) -> dict[str, Any]:
    src = hit.get("_source", {}) or {}
    display_names = src.get("display_names") or [fallback_company]
    entity_id = src.get("entity_id", "")
    file_name = src.get("file_name", "")
    return {
        "form_type": src.get("form_type", ""),
        "filed_at": src.get("file_date", ""),
        "period": src.get("period_of_report", ""),
        "company": display_names[0] if display_names else fallback_company,
        "description": (src.get("file_description") or "")[:300],
        "url": (
            f"https://www.sec.gov/Archives/edgar/data/{entity_id}/{file_name}"
            if entity_id and file_name
            else ""
        ),
    }


async def get_sec_filings_async(
    company_name: str,
    form_types: str = "8-K,10-Q",
    max_results: int = 5,
) -> dict[str, Any]:
    """Async fetch of SEC EDGAR filings.

    Strategy: exact-phrase match first; if empty, retry broad (unquoted) match.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=_DEFAULT_LOOKBACK_DAYS)).strftime(
        "%Y-%m-%d"
    )
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            hits = await _edgar_query(session, f'"{company_name}"', form_types, since)
            if not hits:
                # Broaden the query — drop quotes to allow loose matching.
                hits = await _edgar_query(session, company_name, form_types, since)
    except Exception as exc:
        logger.warning(f"SEC EDGAR search failed for {company_name}: {exc}")
        return {"error": str(exc), "company": company_name, "filings": []}

    filings = [_format_hit(hit, company_name) for hit in hits[:max_results]]
    return {
        "company": company_name,
        "filings": filings,
        "count": len(filings),
        "since": since,
    }


def get_sec_filings(
    company_name: str,
    form_types: str = "8-K,10-Q",
    max_results: int = 5,
) -> dict[str, Any]:
    """Synchronous wrapper (runs async inside event loop or new loop)."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context — run in a worker thread to avoid nesting loops.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    get_sec_filings_async(company_name, form_types, max_results),
                )
                return future.result(timeout=_REQUEST_TIMEOUT_S + 5)
        return loop.run_until_complete(get_sec_filings_async(company_name, form_types, max_results))
    except Exception as exc:
        logger.warning(f"SEC filings sync wrapper failed: {exc}")
        return {"company": company_name, "filings": [], "error": str(exc)}


async def dispatch_async(tool_name: str, args: dict) -> dict:
    """Async tool dispatcher."""
    if tool_name == "get_sec_filings":
        return await get_sec_filings_async(
            args.get("company_name", ""),
            form_types=args.get("form_types", "8-K,10-Q"),
            max_results=args.get("max_results", 5),
        )
    return {"error": f"Unknown tool: {tool_name}"}
