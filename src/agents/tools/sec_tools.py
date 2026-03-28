"""SEC EDGAR tools — fetches recent filings via the free EDGAR full-text search API."""

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
_EDGAR_SEARCH_UI = "https://efts.sec.gov/LATEST/search-index"
_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index"

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


async def get_sec_filings_async(
    company_name: str,
    form_types: str = "8-K,10-Q",
    max_results: int = 5,
) -> dict[str, Any]:
    """Async fetch of SEC EDGAR filings."""
    since = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    params = {
        "q": f'"{company_name}"',
        "dateRange": "custom",
        "startdt": since,
        "forms": form_types,
        "_source": "hits",
        "hits.hits.total.value": 1,
        "hits.hits._source.period_of_report": 1,
        "hits.hits._source.file_date": 1,
        "hits.hits._source.form_type": 1,
        "hits.hits._source.display_names": 1,
        "hits.hits._source.file_description": 1,
    }
    # Use EDGAR full-text search API
    url = "https://efts.sec.gov/LATEST/search-index"
    headers = {"User-Agent": "QuantAI Research research@quantai.example.com"}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={
                    "q": f'"{company_name}"',
                    "dateRange": "custom",
                    "startdt": since,
                    "forms": form_types,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    # Fallback: try the EDGAR company search
                    return await _edgar_company_search(company_name, form_types, max_results)
                data = await resp.json(content_type=None)

        hits = data.get("hits", {}).get("hits", [])
        filings = []
        for hit in hits[:max_results]:
            src = hit.get("_source", {})
            filings.append({
                "form_type": src.get("form_type", ""),
                "filed_at": src.get("file_date", ""),
                "period": src.get("period_of_report", ""),
                "company": src.get("display_names", [company_name])[0]
                if src.get("display_names")
                else company_name,
                "description": src.get("file_description", "")[:300],
                "url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id', '')}/{src.get('file_name', '')}",
            })

        if not filings:
            return await _edgar_company_search(company_name, form_types, max_results)

        return {
            "company": company_name,
            "filings": filings,
            "count": len(filings),
            "since": since,
        }
    except Exception as exc:
        logger.warning(f"SEC EDGAR search failed for {company_name}: {exc}")
        return {"error": str(exc), "company": company_name, "filings": []}


async def _edgar_company_search(
    company_name: str, form_types: str, max_results: int
) -> dict[str, Any]:
    """Fallback: use EDGAR company search endpoint."""
    since = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    headers = {"User-Agent": "QuantAI Research research@quantai.example.com"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={
                    "q": company_name,
                    "dateRange": "custom",
                    "startdt": since,
                    "forms": form_types,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return {"company": company_name, "filings": [], "error": f"HTTP {resp.status}"}
                data = await resp.json(content_type=None)

        hits = data.get("hits", {}).get("hits", [])
        filings = []
        for hit in hits[:max_results]:
            src = hit.get("_source", {})
            filings.append({
                "form_type": src.get("form_type", ""),
                "filed_at": src.get("file_date", ""),
                "period": src.get("period_of_report", ""),
                "company": company_name,
                "description": src.get("file_description", "")[:300],
            })
        return {"company": company_name, "filings": filings, "count": len(filings), "since": since}
    except Exception as exc:
        return {"company": company_name, "filings": [], "error": str(exc)}


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
            # We're inside an async context — caller must await the async version
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    get_sec_filings_async(company_name, form_types, max_results),
                )
                return future.result(timeout=20)
        else:
            return loop.run_until_complete(
                get_sec_filings_async(company_name, form_types, max_results)
            )
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
