# Mortgage Overpayment Calculator

Interactive tool to compare two mortgage overpayment strategies and understand their financial impact.

## Overview

This calculator helps you decide between two common overpayment approaches for annuity (equal installment) mortgages:

- **Strategy A: Shorten Term** — Pay a fixed overpayment each month to finish the loan earlier while keeping the required installment the same
- **Strategy B: Reduce Installment** — Pay a fixed overpayment each month while the bank recalculates and lowers your required installment after each payment

## Features

- 📊 Interactive parameter controls (loan amount, interest rate, term, overpayment)
- 📈 Step-interpolated charts showing balance and cumulative overpayments over time
- 💰 Side-by-side comparison of both strategies with key metrics:
  - Time/payment saved
  - Interest saved vs. baseline
  - Total overpayments made
  - Total amount paid
- 🇵🇱 Polish language interface
- ✅ Comprehensive test suite (22 tests)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/mortgage-calculator.git
   cd mortgage-calculator
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit pandas altair
   ```

## Usage

### Launch the app

```bash
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`

### Using the calculator

1. **Set your loan parameters** in the left sidebar:
   - Loan amount (PLN)
   - Annual interest rate (%)
   - Loan term (months)
   - Monthly overpayment (PLN)

2. **Review the comparison** between the two strategies:
   - Strategy A shows how much time you save and the final month count
   - Strategy B shows the final installment amount and reduction

3. **Analyze the charts:**
   - **Balance chart** — see how quickly each strategy pays down the principal
   - **Overpayment chart** — track cumulative overpayments over time

4. **Check the summary table** for detailed comparison of all key metrics

## Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest test_mortgage.py -v
```

All 22 tests should pass, covering:
- Annuity payment calculation
- Baseline interest calculation
- Both overpayment strategies
- Edge cases (zero rate, zero overpayment, etc.)
- Strategy comparison invariants

## Project Structure

```
mortgage-calculator/
├── app.py              # Streamlit UI
├── mortgage.py         # Core calculation logic
├── test_mortgage.py    # Test suite
├── README.md           # This file
└── .gitignore
```

## How It Works

### Strategy A: Shorten Term
- Fixed monthly payment = base installment + overpayment
- Bank's required installment stays constant
- Loan ends earlier as principal is paid down faster

### Strategy B: Reduce Installment
- Each month: pay current installment + fixed overpayment
- After each payment, bank recalculates required installment for remaining term
- Installment decreases progressively, giving growing financial flexibility

### Key Insight
Strategy A always saves more interest (for equal overpayment amounts) because it maintains higher effective payments throughout the loan lifetime. Strategy B offers progressively lower required payments, which may be valuable for managing cash flow.

## Technical Details

- **Annuity formula** used for installment calculation
- **Month-by-month amortization** simulation with precise interest tracking
- **Dataclasses** for structured return types
- **Type hints** throughout for code clarity
- **Comprehensive docstrings** explaining financial logic

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

---

Built with ❤️ using Streamlit
