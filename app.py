# app.py
import streamlit as st
import pandas as pd
import altair as alt
from itertools import accumulate

from mortgage import (
    annuity_payment,
    calculate_baseline_interest,
    calculate_shorten_term,
    calculate_reduce_payment,
)

st.set_page_config(page_title="Kalkulator nadpłat kredytu hipotecznego", layout="wide")

st.title("Kalkulator nadpłat kredytu hipotecznego")

# --- Sidebar: loan parameters ---

st.sidebar.header("Parametry kredytu")
principal = st.sidebar.number_input("Kwota kredytu (PLN)", value=500000, step=10000)
rate = st.sidebar.number_input("Roczna stopa procentowa (%)", value=7.0, step=0.1)
total_months = st.sidebar.number_input("Okres kredytowania (miesiące)", value=300, step=1)
overpayment = st.sidebar.number_input("Miesięczna nadpłata (PLN)", value=500, step=100)

monthly_rate = rate / 100 / 12
base_payment = annuity_payment(principal, monthly_rate, total_months)

st.sidebar.markdown(f"**Podstawowa rata miesięczna:** {base_payment:,.2f} PLN")

# --- Calculations ---

baseline_interest = calculate_baseline_interest(principal, monthly_rate, base_payment, total_months)
result_a = calculate_shorten_term(principal, monthly_rate, base_payment, overpayment, total_months)
result_b = calculate_reduce_payment(principal, monthly_rate, base_payment, overpayment, total_months)

# --- Strategy comparison cards ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("Strategia A: Skrócenie okresu")
    st.markdown("*Płać więcej co miesiąc, spłać kredyt wcześniej*")

    years_saved = (total_months - result_a.months) // 12
    months_saved = (total_months - result_a.months) % 12

    st.metric("Zaoszczędzony czas", f"{years_saved} lat {months_saved} mies.")
    st.metric("Zaoszczędzone odsetki", f"{baseline_interest - result_a.total_interest:,.0f} PLN")
    st.metric("Nowa rata miesięczna", f"{base_payment + overpayment:,.2f} PLN")
    st.metric("Liczba miesięcy", result_a.months)

with col2:
    st.subheader("Strategia B: Zmniejszenie raty")
    st.markdown("*Nadpłacaj co miesiąc, rata maleje z każdą nadpłatą*")

    st.metric("Ostatnia rata miesięczna", f"{result_b.final_installment:,.2f} PLN")
    st.metric("Obniżka raty", f"{base_payment - result_b.final_installment:,.2f} PLN")
    st.metric("Zaoszczędzone odsetki", f"{baseline_interest - result_b.total_interest:,.0f} PLN")
    st.metric("Liczba miesięcy", result_b.months)

# --- Charts ---


def _build_step_chart(df: pd.DataFrame, x: str, y: str) -> alt.Chart:
    """Melt a wide DataFrame and render as a step-interpolated Altair line chart."""
    melted = df.melt(x, var_name='Strategia', value_name=y)
    return alt.Chart(melted).mark_line(interpolate='step-after').encode(
        x=f'{x}:Q', y=f'{y}:Q', color='Strategia:N',
    )


# Balance over time
st.subheader("Porównanie harmonogramów spłat")

num_rows = max(len(result_a.schedule), len(result_b.schedule))

df_balance = pd.DataFrame({'Miesiąc': range(1, num_rows + 1)})
df_balance['Strategia A (Skrócenie)'] = [
    result_a.schedule[i].balance if i < len(result_a.schedule) else 0
    for i in range(num_rows)
]
df_balance['Strategia B (Obniżenie)'] = [
    result_b.schedule[i].balance if i < len(result_b.schedule) else 0
    for i in range(num_rows)
]

st.altair_chart(_build_step_chart(df_balance, 'Miesiąc', 'Saldo'), width='stretch')

# Cumulative overpayments over time
st.subheader("Nadpłaty w czasie")

cumsum_a = list(accumulate(e.overpayment for e in result_a.schedule))
cumsum_b = list(accumulate(e.overpayment for e in result_b.schedule))

df_overpayments = pd.DataFrame({'Miesiąc': range(1, num_rows + 1)})
df_overpayments['Strategia A (Skrócenie)'] = [
    cumsum_a[i] if i < len(cumsum_a) else cumsum_a[-1]
    for i in range(num_rows)
]
df_overpayments['Strategia B (Obniżenie)'] = [
    cumsum_b[i] if i < len(cumsum_b) else cumsum_b[-1]
    for i in range(num_rows)
]

st.altair_chart(_build_step_chart(df_overpayments, 'Miesiąc', 'Suma nadpłat'), width='stretch')

col_ov1, col_ov2 = st.columns(2)
with col_ov1:
    st.metric("Suma nadpłat — Strategia A", f"{cumsum_a[-1]:,.0f} PLN")
with col_ov2:
    st.metric("Suma nadpłat — Strategia B", f"{cumsum_b[-1]:,.0f} PLN")

# --- Summary comparison table ---

st.subheader("Podsumowanie porównania")

total_paid_baseline = base_payment * total_months
total_paid_a = sum(e.interest + e.principal for e in result_a.schedule)
total_paid_b = sum(e.interest + e.principal for e in result_b.schedule)

comparison_df = pd.DataFrame({
    'Wskaźnik': [
        'Rata miesięczna', 'Okres kredytu (miesiące)', 'Łączne odsetki',
        'Oszczędność odsetek', 'Suma nadpłat', 'Łączna kwota wpłat',
    ],
    'Bazowy': [
        f"{base_payment:,.2f} PLN", str(total_months),
        f"{baseline_interest:,.2f} PLN", "0 PLN",
        "0 PLN", f"{total_paid_baseline:,.2f} PLN",
    ],
    'Strategia A': [
        f"{base_payment + overpayment:,.2f} PLN", str(result_a.months),
        f"{result_a.total_interest:,.2f} PLN",
        f"{baseline_interest - result_a.total_interest:,.2f} PLN",
        f"{cumsum_a[-1]:,.2f} PLN", f"{total_paid_a:,.2f} PLN",
    ],
    'Strategia B': [
        f"{result_b.final_installment:,.2f} PLN", str(result_b.months),
        f"{result_b.total_interest:,.2f} PLN",
        f"{baseline_interest - result_b.total_interest:,.2f} PLN",
        f"{cumsum_b[-1]:,.2f} PLN", f"{total_paid_b:,.2f} PLN",
    ],
})

st.table(comparison_df)
