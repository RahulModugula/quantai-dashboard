import pytest
from src.data.schemas import SIPRequest, ReverseSIPRequest


def test_sip_request_schema_valid():
    """Test valid SIP request."""
    req = SIPRequest(
        monthly_amount=5000.0,
        duration_years=10,
        expected_annual_return=0.12,
        annual_step_up=0.05,
    )
    assert req.monthly_amount == 5000.0
    assert req.duration_years == 10
    assert req.expected_annual_return == 0.12
    assert req.annual_step_up == 0.05


def test_sip_request_schema_invalid_amount():
    """Test invalid monthly amount."""
    with pytest.raises(ValueError):
        SIPRequest(
            monthly_amount=-1000.0,  # Negative
            duration_years=10,
            expected_annual_return=0.12,
        )

    with pytest.raises(ValueError):
        SIPRequest(
            monthly_amount=0.0,  # Zero
            duration_years=10,
            expected_annual_return=0.12,
        )


def test_sip_request_schema_invalid_duration():
    """Test invalid duration."""
    with pytest.raises(ValueError):
        SIPRequest(
            monthly_amount=5000.0,
            duration_years=0,  # Zero
            expected_annual_return=0.12,
        )

    with pytest.raises(ValueError):
        SIPRequest(
            monthly_amount=5000.0,
            duration_years=-5,  # Negative
            expected_annual_return=0.12,
        )


def test_reverse_sip_request_schema_valid():
    """Test valid reverse SIP request."""
    req = ReverseSIPRequest(
        target_corpus=1_000_000.0,
        duration_years=20,
        expected_annual_return=0.10,
        annual_step_up=0.05,
    )
    assert req.target_corpus == 1_000_000.0
    assert req.duration_years == 20
    assert req.expected_annual_return == 0.10
    assert req.annual_step_up == 0.05


def test_reverse_sip_request_schema_invalid_corpus():
    """Test invalid target corpus."""
    with pytest.raises(ValueError):
        ReverseSIPRequest(
            target_corpus=-500_000.0,  # Negative
            duration_years=20,
            expected_annual_return=0.10,
        )

    with pytest.raises(ValueError):
        ReverseSIPRequest(
            target_corpus=0.0,  # Zero
            duration_years=20,
            expected_annual_return=0.10,
        )


def test_reverse_sip_request_schema_invalid_duration():
    """Test invalid duration in reverse SIP."""
    with pytest.raises(ValueError):
        ReverseSIPRequest(
            target_corpus=1_000_000.0,
            duration_years=0,  # Zero
            expected_annual_return=0.10,
        )

    with pytest.raises(ValueError):
        ReverseSIPRequest(
            target_corpus=1_000_000.0,
            duration_years=-10,  # Negative
            expected_annual_return=0.10,
        )


@pytest.mark.skip(reason="Requires full API setup with dependencies")
def test_calculate_sip():
    """Test SIP calculation endpoint."""
    from src.api.routes.sip import calculate_sip

    req = SIPRequest(
        monthly_amount=5000.0,
        duration_years=10,
        expected_annual_return=0.12,
    )

    # This would require mocking the actual calculation
    result = calculate_sip(req)

    assert "pre_tax_corpus" in result
    assert "post_tax_corpus" in result


@pytest.mark.skip(reason="Requires full API setup with dependencies")
def test_reverse_sip_calculate():
    """Test reverse SIP calculation endpoint."""
    from src.api.routes.sip import reverse_sip

    req = ReverseSIPRequest(
        target_corpus=1_000_000.0,
        duration_years=20,
        expected_annual_return=0.10,
    )

    # This would require mocking the actual calculation
    result = reverse_sip(req)

    assert "monthly_amount" in result
