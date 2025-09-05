"""Shared FastAPI dependencies."""

from functools import lru_cache

from src.config import settings
from src.data.storage import get_engine
from src.trading.paper_trader import PaperTrader

_paper_trader: PaperTrader | None = None


def get_paper_trader() -> PaperTrader:
    global _paper_trader
    if _paper_trader is None:
        _paper_trader = PaperTrader(tickers=settings.tickers)
    return _paper_trader


def get_db_engine():
    return get_engine()


@lru_cache(maxsize=1)
def get_model_bundle():
    """Load model bundle once and cache it."""
    try:
        from src.models.registry import load_metadata, load_model
        bundle = load_model()
        meta = load_metadata()
        return bundle, meta
    except FileNotFoundError:
        return None, {}
