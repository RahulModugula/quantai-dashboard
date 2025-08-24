"""Test fixtures and utilities."""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TestDataFactory:
    """Generate test data."""

    @staticmethod
    def create_sample_trades(count: int = 10) -> List[Dict[str, Any]]:
        """Create sample trades."""
        trades = []
        base_date = datetime.now() - timedelta(days=30)

        for i in range(count):
            trades.append({
                "trade_id": f"trade_{i}",
                "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN"][i % 4],
                "entry_price": 150 + (i * 2),
                "exit_price": 152 + (i * 2),
                "entry_date": (base_date + timedelta(days=i)).isoformat(),
                "exit_date": (base_date + timedelta(days=i+1)).isoformat(),
                "pnl": 200 + (i * 10),
                "quantity": 10 + i,
            })

        return trades

    @staticmethod
    def create_sample_market_data(days: int = 30) -> List[Dict[str, Any]]:
        """Create sample market data."""
        data = []
        base_date = datetime.now() - timedelta(days=days)

        for i in range(days):
            date = (base_date + timedelta(days=i)).isoformat()
            data.append({
                "date": date,
                "open": 150.0 + (i * 0.5),
                "high": 152.0 + (i * 0.5),
                "low": 149.0 + (i * 0.5),
                "close": 151.0 + (i * 0.5),
                "volume": 1000000 + (i * 10000),
            })

        return data

    @staticmethod
    def create_sample_predictions(count: int = 5) -> List[Dict[str, Any]]:
        """Create sample predictions."""
        predictions = []

        for i in range(count):
            predictions.append({
                "prediction_id": f"pred_{i}",
                "symbol": ["AAPL", "MSFT", "GOOGL", "AMZN"][i % 4],
                "timestamp": datetime.now().isoformat(),
                "signal": ["BUY", "SELL", "HOLD"][i % 3],
                "confidence": 0.7 + (i * 0.05),
                "price_target": 150.0 + (i * 2),
            })

        return predictions

    @staticmethod
    def create_sample_portfolio(symbols: List[str] = None) -> Dict[str, Any]:
        """Create sample portfolio."""
        if symbols is None:
            symbols = ["AAPL", "MSFT", "GOOGL"]

        positions = {}
        for symbol in symbols:
            positions[symbol] = {
                "quantity": 100,
                "cost_basis": 150.0,
                "current_price": 155.0,
            }

        return {
            "portfolio_id": "portfolio_1",
            "cash": 10000.0,
            "positions": positions,
            "total_value": 50000.0,
        }

    @staticmethod
    def create_sample_backtest_result() -> Dict[str, Any]:
        """Create sample backtest result."""
        return {
            "backtest_id": "backtest_1",
            "total_trades": 50,
            "winning_trades": 30,
            "losing_trades": 20,
            "win_rate": 0.60,
            "total_return": 0.25,
            "annual_return": 0.12,
            "max_drawdown": 0.15,
            "sharpe_ratio": 1.5,
            "profit_factor": 2.0,
        }


class MockDataProvider:
    """Mock data provider for testing."""

    def __init__(self):
        """Initialize mock provider."""
        self.trades = TestDataFactory.create_sample_trades()
        self.market_data = TestDataFactory.create_sample_market_data()
        self.predictions = TestDataFactory.create_sample_predictions()

    def get_trades(self, symbol: str = None) -> List[Dict]:
        """Get mock trades."""
        if symbol:
            return [t for t in self.trades if t["symbol"] == symbol]
        return self.trades

    def get_market_data(self, symbol: str = None) -> List[Dict]:
        """Get mock market data."""
        return self.market_data

    def get_predictions(self, symbol: str = None) -> List[Dict]:
        """Get mock predictions."""
        if symbol:
            return [p for p in self.predictions if p["symbol"] == symbol]
        return self.predictions

    def add_trade(self, trade: Dict):
        """Add mock trade."""
        self.trades.append(trade)

    def clear(self):
        """Clear all mock data."""
        self.trades = []
        self.market_data = []
        self.predictions = []


class TestContext:
    """Test execution context."""

    def __init__(self):
        """Initialize test context."""
        self.data_factory = TestDataFactory()
        self.mock_provider = MockDataProvider()
        self.test_results = {}

    def record_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result."""
        self.test_results[test_name] = {
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        passed = sum(1 for r in self.test_results.values() if r["passed"])
        total = len(self.test_results)

        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
        }
