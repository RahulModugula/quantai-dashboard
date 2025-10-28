"""Portfolio and market analysis endpoints."""
import logging
from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_paper_trader
from src.analysis.sector import SectorAnalyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.get("/sector-composition")
def get_sector_composition() -> dict:
    """Analyze sector composition of current portfolio."""
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        analysis = SectorAnalyzer.analyze_portfolio(
            positions=portfolio.positions,
            portfolio_value=portfolio.get_value({}),
        )

        return {
            "composition": analysis,
            "portfolio_value": round(portfolio.get_value({}), 2),
            "position_count": len(portfolio.positions),
        }
    except Exception as e:
        logger.error(f"Sector analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sector-gaps")
def check_sector_coverage(target_sectors: str = "Technology,Healthcare,Financials,Energy") -> dict:
    """Identify missing sectors in portfolio.

    Args:
        target_sectors: Comma-separated list of desired sectors
    """
    try:
        trader = get_paper_trader()
        portfolio = trader.portfolio

        sectors = [s.strip() for s in target_sectors.split(",")]
        gaps = SectorAnalyzer.find_sector_gaps(
            positions=portfolio.positions,
            target_sectors=sectors,
        )

        return {
            "target_sectors": sectors,
            "gaps": gaps,
            "current_positions": len(portfolio.positions),
        }
    except Exception as e:
        logger.error(f"Gap analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sector-examples/{sector}")
def get_sector_examples(sector: str) -> dict:
    """Get example stocks in a sector.

    Args:
        sector: Sector name (e.g., "Technology", "Healthcare")
    """
    try:
        examples = SectorAnalyzer.get_examples_per_sector(sector)

        if not examples:
            from src.analysis.sector import TICKER_SECTORS
            return {
                "sector": sector,
                "examples": [],
                "message": f"No examples found for sector: {sector}",
                "available_sectors": list(set(TICKER_SECTORS.values())),
            }

        return {
            "sector": sector,
            "examples": examples,
            "count": len(examples),
        }
    except Exception as e:
        logger.error(f"Example lookup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")
