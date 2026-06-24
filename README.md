# Automated Discounted Cash Flow (DCF) & Valuation Engine

An automated, data-driven equity valuation engine that bypasses traditional spreadsheet constraints to model intrinsic corporate value. This system programmatically extracts data from the `yfinance` API, processes operational trends through a weighted-moving-average pipeline, applies dynamic discounting conventions, and reverse-engineers market sentiment using numerical root-finding algorithms.

---

## Core Financial Framework

### Decayed Weighting Matrix

Historical metrics (EBIT, D&A, CapEx, and Working Capital margins) are scaled using a decaying factor array:

```text
[0.4, 0.3, 0.2, 0.1]
```

This prioritizes recent macroeconomic environments and operational adjustments while minimizing historical noise.

### Mid-Year Discounting Convention

Cash flows assume mid-period distribution (`t = 0.5, 1.5, ...`) rather than restrictive year-end cliffs, neutralizing structural under-valuation and aligning with continuous corporate cash generation.

### Implied Growth Optimization

Features a custom root-finding algorithm that solves for the exact revenue growth rate implied by the asset's current market price.

---

# Technical Setup & Dependencies

Install the required libraries:

```bash
pip install numpy pandas yfinance
```

---

# Command Line Interface (CLI)

Execute valuations directly from the terminal.

```bash
python main.py --ticker SYMBOL [--TGR RATE] [--riskfree SYMBOL] [--market SYMBOL]
```

---

# Example Usage

## Standard Valuation

```bash
python main.py --ticker KO
```

## Advanced Configuration

```bash
python main.py --ticker NVDA --TGR 0.02 --riskfree ^FVX --market VT
```

---

# Command-Line Arguments

| Argument     | Variable                | Description                   | Default      |
| ------------ | ----------------------- | ----------------------------- | ------------ |
| `--ticker`   | `stock_symbol`          | Public equity ticker to value | **Required** |
| `--TGR`      | `perpetual_growth_rate` | Terminal growth rate          | `0.03`       |
| `--riskfree` | `risk_free_asset`       | Risk-free benchmark           | `^TNX`       |
| `--market`   | `market_index`          | Market benchmark for ERP      | `VTI`        |

---

# Example Output

```text
Implied Stock Price: 76.18
Margin of Safety: 8.31%

Current Price: 70.34
Implied Growth Rate: 2.87%
```

---

# Financial Methodology

## 1. Unlevered Free Cash Flow (FCF)

The engine estimates enterprise cash generation using:

[
\text{NOPAT} = \text{EBIT}\times(1-\tau)
]

[
\text{FCF}=\text{NOPAT}+D&A-\text{CapEx}-\Delta NWC
]

```python
def _compute_free_cash_flows(self):
    return (
        self.nopat
        + self.forecasted_da
        - self.forecasted_capex
        - self.forecasted_nwc_change
    )
```

---

## 2. Weighted Average Cost of Capital (WACC)

[
\text{WACC}
===========

\left(
\frac{D}{D+E}
\times
R_d
\times
(1-\tau)
\right)
+
\left(
\frac{E}{D+E}
\times
R_e
\right)
]

where

### Cost of Debt

[
R_d=\frac{\text{Interest Expense}}{\text{Total Debt}}
]

### Cost of Equity (CAPM)

[
R_e
===

R_f
+
\beta
\left(
R_m-R_f
\right)
]

```python
def _compute_wacc(self):
    debt_weight = self.total_debt / (self.total_debt + self.market_cap)
    equity_weight = self.market_cap / (self.total_debt + self.market_cap)

    cost_of_debt = self.interest_expense / self.total_debt
    cost_of_equity = (
        self.risk_free_rate
        + self.equity_beta
        * (self.market_return_rate - self.risk_free_rate)
    )

    return (
        debt_weight * cost_of_debt * (1 - self.effective_tax_rate)
        + equity_weight * cost_of_equity
    )
```

---

## 3. Present Value Engine

Enterprise value is calculated as:

[
\text{EV}
=========

\sum_{t=1}^{5}
\frac{\text{FCF}_t}
{(1+\text{WACC})^{t-0.5}}
+
\frac{\text{Terminal Value}}
{(1+\text{WACC})^5}
]

```python
def _discount_cash_flows(self):

    discounted_fcfs = sum(
        pd.Series(
            (
                fcf /
                ((1 + self.wacc_rate) ** (0.5 + i))
            )
            for i, fcf in enumerate(self.forecasted_fcf)
        )
    )

    discounted_tv = (
        self.estimated_terminal_value
        /
        ((1 + self.wacc_rate) ** 5)
    )

    return discounted_fcfs + discounted_tv
```

---

## 4. Terminal Value

The perpetual growth model estimates continuing value:

[
\text{Terminal Value}
=====================

\frac{\text{FCF}_5(1+g)}
{\text{WACC}-g}
]

### Alternative Terminal Value Approaches

Depending on the industry, different methodologies may be more appropriate.

* **EBITDA / EBIT Multiples**

  * Industrials
  * Utilities
  * Real Estate
  * Asset-heavy businesses

* **Revenue Multiples**

  * SaaS
  * Early-stage technology
  * High-growth businesses with temporarily low profitability

---

## 5. Implied Growth Rate Solver

Rather than assuming a fixed growth rate, the engine numerically solves for the revenue growth embedded in the current market price using a bisection algorithm.

```python
def find_implied_growth_rate(
    self,
    tolerance=0.01,
    max_iterations=100
):

    lower_bound = -0.5
    upper_bound = 0.5

    for _ in range(max_iterations):

        mid_point = (lower_bound + upper_bound) / 2

        calculated_price = eval_price_at_growth(mid_point)

        ...
```

---

# Features

* Automated financial statement extraction using `yfinance`
* Five-year DCF forecasting engine
* Weighted historical operating margin estimation
* Mid-year discounting convention
* Dynamic WACC estimation
* CAPM-based cost of equity
* Terminal value estimation
* Margin of safety calculation
* Market-implied revenue growth solver
* Command-line interface for flexible valuation workflows

---

# Disclaimer

This project is intended solely for educational, research, and financial modeling purposes. It does not constitute investment advice or a recommendation to buy or sell securities. Users should independently verify all financial data against official company filings before making investment decisions.
