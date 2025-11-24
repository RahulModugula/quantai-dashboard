"""Track order execution and slippage."""

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    """Record of a trade execution."""

    ticker: str
    timestamp: str
    side: str  # BUY or SELL
    ordered_price: float
    executed_price: float
    shares: int
    commission: float

    @property
    def slippage(self) -> float:
        """Calculate slippage in basis points."""
        if self.side == "BUY":
            diff = self.executed_price - self.ordered_price
        else:
            diff = self.ordered_price - self.executed_price

        return (diff / self.ordered_price) * 10000  # Convert to basis points


class ExecutionTracker:
    """Track execution records and calculate metrics."""

    def __init__(self):
        self.records = []

    def record_execution(
        self,
        ticker: str,
        side: str,
        ordered_price: float,
        executed_price: float,
        shares: int,
        commission: float,
    ) -> ExecutionRecord:
        """Record a trade execution."""
        record = ExecutionRecord(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            side=side,
            ordered_price=ordered_price,
            executed_price=executed_price,
            shares=shares,
            commission=commission,
        )

        self.records.append(record)
        logger.info(
            f"Execution recorded: {side} {shares} {ticker} @ ${executed_price:.2f} "
            f"(ordered: ${ordered_price:.2f}, slippage: {record.slippage:.1f} bps)"
        )

        return record

    def average_slippage(self) -> float:
        """Calculate average slippage across all executions."""
        if not self.records:
            return 0.0

        total_slippage = sum(r.slippage for r in self.records)
        return total_slippage / len(self.records)

    def total_commission(self) -> float:
        """Calculate total commission paid."""
        return sum(r.commission for r in self.records)

    def get_records(self, ticker: str = None) -> list[ExecutionRecord]:
        """Get execution records, optionally filtered by ticker."""
        if ticker:
            return [r for r in self.records if r.ticker == ticker]
        return self.records
