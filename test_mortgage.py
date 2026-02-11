import pytest
from mortgage import (
    annuity_payment,
    calculate_baseline_interest,
    calculate_shorten_term,
    calculate_reduce_payment,
)

# Standard test scenario: 500k PLN, 7% annual, 300 months (25 years), 500 PLN overpayment
PRINCIPAL = 500_000
ANNUAL_RATE = 7.0
MONTHLY_RATE = ANNUAL_RATE / 100 / 12
TOTAL_MONTHS = 300
OVERPAYMENT = 500

BASE_PAYMENT = annuity_payment(PRINCIPAL, MONTHLY_RATE, TOTAL_MONTHS)


class TestAnnuityPayment:
    def test_known_value(self):
        """500k at 7% for 300 months should give ~3534 PLN."""
        assert round(BASE_PAYMENT, 0) == 3534

    def test_zero_rate(self):
        assert annuity_payment(120_000, 0, 120) == pytest.approx(1000.0)

    def test_single_month(self):
        """One-month loan: repay full principal plus one month's interest."""
        assert annuity_payment(10_000, 0.01, 1) == pytest.approx(10_100.0, rel=1e-6)

    def test_higher_rate_means_higher_payment(self):
        low = annuity_payment(PRINCIPAL, 0.005, TOTAL_MONTHS)
        high = annuity_payment(PRINCIPAL, 0.01, TOTAL_MONTHS)
        assert high > low


class TestBaselineInterest:
    def test_total_paid_equals_principal_plus_interest(self):
        """Accounting identity: total payments = principal + total interest."""
        interest = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        total_paid = BASE_PAYMENT * TOTAL_MONTHS
        assert total_paid == pytest.approx(PRINCIPAL + interest, rel=1e-4)

    def test_zero_rate_no_interest(self):
        payment = annuity_payment(100_000, 0, 100)
        interest = calculate_baseline_interest(100_000, 0, payment, 100)
        assert interest == pytest.approx(0.0)


class TestShortenTerm:
    def test_shortens_term(self):
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.months < TOTAL_MONTHS

    def test_zero_overpayment_matches_baseline(self):
        """With no overpayment, result should match the standard amortization."""
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, 0, TOTAL_MONTHS)
        baseline = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        assert result.months == TOTAL_MONTHS
        assert result.total_interest == pytest.approx(baseline, rel=1e-4)

    def test_saves_interest(self):
        baseline = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.total_interest < baseline

    def test_balance_reaches_zero(self):
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.schedule[-1].balance == pytest.approx(0, abs=0.01)

    def test_schedule_length_matches_months(self):
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert len(result.schedule) == result.months

    def test_overpayment_equals_input(self):
        """First month's overpayment should match the configured amount."""
        result = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.schedule[0].overpayment == pytest.approx(OVERPAYMENT, rel=1e-6)
        assert all(e.overpayment >= 0 for e in result.schedule)

    def test_larger_overpayment_shortens_more(self):
        small = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, 200, TOTAL_MONTHS)
        large = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, 1000, TOTAL_MONTHS)
        assert large.months < small.months


class TestReducePayment:
    def test_saves_interest(self):
        baseline = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.total_interest < baseline

    def test_balance_reaches_zero(self):
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.schedule[-1].balance == pytest.approx(0, abs=0.01)

    def test_schedule_length_matches_months(self):
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert len(result.schedule) == result.months

    def test_installment_decreases(self):
        """Final required installment should be lower than the original."""
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert result.final_installment < BASE_PAYMENT

    def test_overpayments_nonnegative(self):
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert all(e.overpayment >= 0 for e in result.schedule)

    def test_zero_overpayment_matches_baseline(self):
        result = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, 0, TOTAL_MONTHS)
        baseline = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        assert result.months == TOTAL_MONTHS
        assert result.total_interest == pytest.approx(baseline, rel=1e-4)


class TestStrategyComparison:
    """Strategy A always saves more interest and finishes sooner than Strategy B
    (given equal overpayment amounts), because it maintains a higher effective
    payment throughout the loan lifetime."""

    def test_a_saves_more_interest(self):
        a = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        b = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert a.total_interest < b.total_interest

    def test_a_finishes_sooner(self):
        a = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        b = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert a.months < b.months

    def test_both_beat_baseline(self):
        baseline = calculate_baseline_interest(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, TOTAL_MONTHS)
        a = calculate_shorten_term(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        b = calculate_reduce_payment(PRINCIPAL, MONTHLY_RATE, BASE_PAYMENT, OVERPAYMENT, TOTAL_MONTHS)
        assert a.total_interest < baseline
        assert b.total_interest < baseline
