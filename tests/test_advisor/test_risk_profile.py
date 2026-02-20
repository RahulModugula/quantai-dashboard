"""Tests for risk profiling and allocation."""

from src.advisor.risk_profile import score_risk_profile
from src.advisor.allocation import get_allocation, AllocationSuggestion


class TestRiskScoring:
    def test_young_aggressive_profile(self):
        result = score_risk_profile(
            age=25, income_stability=5, investment_horizon_years=20,
            loss_tolerance=5, existing_savings_months=12, debt_to_income_pct=0.05,
        )
        assert result.category == "Very Aggressive"
        assert result.score >= 75

    def test_old_conservative_profile(self):
        result = score_risk_profile(
            age=65, income_stability=2, investment_horizon_years=2,
            loss_tolerance=1, existing_savings_months=2, debt_to_income_pct=0.6,
        )
        assert result.category == "Conservative"
        assert result.score < 35

    def test_moderate_profile(self):
        result = score_risk_profile(
            age=40, income_stability=3, investment_horizon_years=7,
            loss_tolerance=3, existing_savings_months=6, debt_to_income_pct=0.2,
        )
        assert result.category in ("Moderate", "Aggressive")

    def test_score_clamped_to_100(self):
        result = score_risk_profile(
            age=20, income_stability=5, investment_horizon_years=30,
            loss_tolerance=5, existing_savings_months=24, debt_to_income_pct=0.0,
        )
        assert result.score <= 100

    def test_score_never_negative(self):
        result = score_risk_profile(
            age=100, income_stability=1, investment_horizon_years=0,
            loss_tolerance=1, existing_savings_months=0, debt_to_income_pct=1.0,
        )
        assert result.score >= 0

    def test_result_has_description(self):
        result = score_risk_profile(
            age=30, income_stability=3, investment_horizon_years=10,
            loss_tolerance=3, existing_savings_months=6, debt_to_income_pct=0.15,
        )
        assert len(result.description) > 0

    def test_dict_method(self):
        result = score_risk_profile(
            age=30, income_stability=3, investment_horizon_years=10,
            loss_tolerance=3, existing_savings_months=6, debt_to_income_pct=0.15,
        )
        d = result.dict()
        assert "score" in d
        assert "category" in d
        assert "description" in d


class TestAllocation:
    def test_conservative_allocation(self):
        alloc = get_allocation("Conservative")
        assert isinstance(alloc, AllocationSuggestion)
        assert alloc.allocations["Debt / Bonds"] >= 50

    def test_aggressive_allocation(self):
        alloc = get_allocation("Aggressive")
        total_equity = (
            alloc.allocations["Large Cap Equity"]
            + alloc.allocations["Mid Cap Equity"]
            + alloc.allocations["Small Cap Equity"]
        )
        assert total_equity >= 50

    def test_allocations_sum_to_100(self):
        for cat in ["Conservative", "Moderate", "Aggressive", "Very Aggressive"]:
            alloc = get_allocation(cat)
            total = sum(alloc.allocations.values())
            assert total == 100, f"{cat} allocations sum to {total}"

    def test_unknown_category_defaults_to_moderate(self):
        alloc = get_allocation("nonexistent")
        assert alloc.risk_category == "Moderate"

    def test_case_insensitive(self):
        alloc = get_allocation("aggressive")
        assert alloc.risk_category == "Aggressive"
