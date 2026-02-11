"""Mortgage overpayment calculator — pure calculation functions.

Compares two overpayment strategies for an annuity (equal installment) mortgage:
  - Shorten term: fixed overpayment each month accelerates principal repayment,
    ending the loan earlier while the bank-required installment stays the same.
  - Reduce installment: fixed overpayment each month, bank recalculates the
    required installment downward after each payment, progressively lowering
    the mandatory monthly cost.
"""

from dataclasses import dataclass


@dataclass
class MonthlyEntry:
    """Single month in an amortization schedule."""
    month: int
    balance: float      # remaining balance after this month's payment
    interest: float     # interest portion of this month's payment
    principal: float    # principal portion of this month's payment
    overpayment: float  # amount paid above the required installment


@dataclass
class StrategyResult:
    """Outcome of a repayment strategy simulation."""
    months: int                      # actual number of months to fully repay
    total_interest: float            # cumulative interest paid
    schedule: list[MonthlyEntry]     # month-by-month breakdown
    final_installment: float         # last bank-required installment (excl. overpayment)


def annuity_payment(principal: float, monthly_rate: float, months: int) -> float:
    """Standard annuity formula: fixed monthly payment for given principal, rate, and term.

    For zero interest rate, falls back to simple division (principal / months).
    """
    if monthly_rate > 0:
        r_pow_n = (1 + monthly_rate) ** months
        return principal * (monthly_rate * r_pow_n) / (r_pow_n - 1)
    return principal / months


def calculate_baseline_interest(
    principal: float, monthly_rate: float, base_payment: float, total_months: int,
) -> float:
    """Total interest paid over the full loan term with no overpayments.

    Simulates standard month-by-month amortization. Numerically equivalent to
    ``base_payment * total_months - principal``, but computed iteratively for
    consistency with the strategy simulation functions.
    """
    balance = principal
    total_interest = 0.0
    for _ in range(total_months):
        interest = balance * monthly_rate
        balance -= base_payment - interest
        total_interest += interest
    return total_interest


def calculate_shorten_term(
    principal: float,
    monthly_rate: float,
    base_payment: float,
    overpayment: float,
    total_months: int,
) -> StrategyResult:
    """Strategy A: pay base_payment + overpayment each month, finish earlier.

    The bank's required installment stays at base_payment throughout.
    The fixed overpayment accelerates principal repayment, shortening the term.
    """
    balance = principal
    month = 0
    total_interest = 0.0
    schedule: list[MonthlyEntry] = []
    payment = base_payment + overpayment

    while balance > 0 and month < total_months:
        interest = balance * monthly_rate
        principal_paid = payment - interest

        # Final month: cap payment to remaining balance + interest
        if principal_paid > balance:
            principal_paid = balance
            payment = balance + interest

        balance -= principal_paid
        total_interest += interest
        month += 1

        schedule.append(MonthlyEntry(
            month=month,
            balance=balance,
            interest=interest,
            principal=principal_paid,
            overpayment=max(0.0, interest + principal_paid - base_payment),
        ))

    return StrategyResult(
        months=month,
        total_interest=total_interest,
        schedule=schedule,
        final_installment=base_payment,
    )


def calculate_reduce_payment(
    principal: float,
    monthly_rate: float,
    base_payment: float,
    overpayment: float,
    total_months: int,
) -> StrategyResult:
    """Strategy B: pay recalculated installment + overpayment each month.

    After each payment, the bank recalculates the required installment for the
    remaining original term and new (lower) balance. The installment decreases
    progressively while the borrower continues the same fixed overpayment on top.
    """
    balance = principal
    month = 0
    total_interest = 0.0
    schedule: list[MonthlyEntry] = []
    remaining = total_months
    installment = base_payment

    while balance > 0 and remaining > 0:
        interest = balance * monthly_rate
        current_installment = installment
        payment = installment + overpayment
        principal_paid = payment - interest

        # Final month: cap payment to remaining balance + interest
        if principal_paid > balance:
            principal_paid = balance
            payment = balance + interest

        balance -= principal_paid
        total_interest += interest
        month += 1
        remaining -= 1

        schedule.append(MonthlyEntry(
            month=month,
            balance=balance,
            interest=interest,
            principal=principal_paid,
            overpayment=max(0.0, interest + principal_paid - current_installment),
        ))

        # Recalculate required installment for reduced balance and remaining term
        if remaining > 0 and balance > 0:
            installment = annuity_payment(balance, monthly_rate, remaining)

    return StrategyResult(
        months=month,
        total_interest=total_interest,
        schedule=schedule,
        final_installment=installment,
    )
