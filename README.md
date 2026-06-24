# DCF Equity Valuation Model

## Introduction

Valuing a company is a fundamental part of equity research and investment analysis. Among the various valuation techniques, the **Discounted Cash Flow (DCF)** model is one of the most widely used methods for estimating a company's intrinsic value by forecasting its future cash flows and discounting them to their present value.

The **DCF Equity Valuation Model** is a Python-based application that automates this valuation process using publicly available financial data obtained through the **Yahoo Finance API (`yfinance`)**. Instead of manually building a spreadsheet model, users can estimate the intrinsic value of any supported publicly traded company directly from the command line by providing its ticker symbol.

The model retrieves historical financial statements and market information, projects revenue over a five-year forecast period, estimates operating income, taxes, depreciation, capital expenditure, and working capital requirements, and computes projected **Free Cash Flows (FCF)**. These cash flows are discounted using the **Weighted Average Cost of Capital (WACC)**, while the terminal value is estimated using the **Gordon Growth Model** to determine the company's enterprise value, equity value, and intrinsic share price.

In addition to estimating intrinsic value, the model calculates the **Margin of Safety**, allowing users to compare the estimated fair value with the current market price. It also estimates the **implied revenue growth rate** using the **bisection method**, providing insight into the market's embedded growth expectations.

This project demonstrates the practical implementation of a complete DCF valuation pipeline in Python by combining financial statement analysis, valuation principles, and numerical optimization into a single automated workflow.

---

# Features

* Automated retrieval of financial statements and market data using `yfinance`
* Five-year revenue forecasting
* Weighted historical operating margin estimation
* Free Cash Flow (FCF) forecasting
* WACC estimation using the Capital Asset Pricing Model (CAPM)
* Mid-year discounting convention
* Terminal value estimation using the Gordon Growth Model
* Enterprise value and intrinsic share price calculation
* Margin of Safety analysis
* Implied revenue growth estimation using the bisection method
* Command-line interface for company valuation

---

# Project Structure

```text
.
├── DCFModel.py
├── EV_EBITDA by Industry.csv
├── requirements.txt
└── README.md
```

---

# Additional Data

The repository includes **EV_EBITDA by Industry.csv**, containing industry EV/EBITDA multiples. While the current implementation estimates terminal value using the Gordon Growth Model, this dataset can be used for future extensions involving exit multiple valuation.

---

# Requirements

* Python 3.x

Install the required dependencies:

```bash
pip install -r requirements.txt
```

or

```bash
pip install numpy pandas yfinance
```

---

# Usage

Run the model from the terminal.

```bash
python DCFModel.py --ticker SYMBOL
```

### Example

```bash
python DCFModel.py --ticker KO
```

### Custom Terminal Growth Rate

```bash
python DCFModel.py --ticker MSFT --TGR 0.025
```

### Custom Market Assumptions

```bash
python DCFModel.py --ticker NVDA --TGR 0.02 --riskfree ^FVX --market VT
```

---

# Command-Line Arguments

| Argument     | Description                      | Default      |
| ------------ | -------------------------------- | ------------ |
| `--ticker`   | Stock ticker symbol              | **Required** |
| `--TGR`      | Terminal (Perpetual) Growth Rate | `0.03`       |
| `--riskfree` | Risk-free rate benchmark         | `^TNX`       |
| `--market`   | Market benchmark                 | `VTI`        |

---

# Sample Output

```text
Implied Stock Price: 76.18
Margin of Safety: 8.31%

Current Price: 70.34
Implied Growth Rate: 2.87%
```

---

# Methodology

## Revenue Projection

Historical revenue is obtained from the company's income statement. The model initializes the forecast using the latest revenue estimate available on Yahoo Finance and compounds it using the expected one-year revenue growth rate.

Historical operating margins are estimated using weighted averages, assigning greater importance to recent financial performance.

Historical weighting scheme:

```text
[0.4, 0.3, 0.2, 0.1]
```

---

## Operating Income (EBIT)

Projected EBIT is estimated by applying the weighted historical EBIT margin to forecasted revenue.

```math
EBIT_t = Revenue_t \times EBIT\ Margin
```

---

## Net Operating Profit After Tax (NOPAT)

Projected taxes are estimated using the weighted historical effective tax rate.

```math
NOPAT = EBIT \times (1 - Tax\ Rate)
```

---

## Free Cash Flow (FCF)

Free Cash Flow represents the cash generated after accounting for operating expenses, capital expenditure, and changes in working capital.

```math
FCF =
NOPAT
+
Depreciation\ \&\ Amortization
-
Capital\ Expenditure
-
Change\ in\ Working\ Capital
```

---

## Weighted Average Cost of Capital (WACC)

The Weighted Average Cost of Capital represents the average cost of financing from debt and equity and serves as the discount rate for projected cash flows.

```math
WACC=
\frac{D}{D+E}R_d(1-\tau)+
\frac{E}{D+E}R_e
```

where

* **D** = Total Debt
* **E** = Market Capitalization
* **Rd** = Cost of Debt
* **Re** = Cost of Equity

### Cost of Debt

```math
R_d=
\frac{Interest\ Expense}{Total\ Debt}
```

### Cost of Equity (CAPM)

```math
R_e=
R_f+\beta(R_m-R_f)
```

The model uses:

* **^TNX** as the default risk-free rate.
* **VTI** as the default market benchmark.

---

## Enterprise Value

Projected Free Cash Flows are discounted using a **mid-year discounting convention**, assuming cash flows are generated throughout the year.

```math
EV=
\sum_{t=1}^{5}
\frac{FCF_t}
{(1+WACC)^{t-0.5}}
+
\frac{TV}
{(1+WACC)^5}
```

---

## Terminal Value

The model estimates terminal value using the **Gordon Growth Model**.

```math
TV=
\frac{FCF_5(1+g)}
{WACC-g}
```

where

* **g** = Perpetual growth rate.

---

## Equity Value

Enterprise Value is converted into Equity Value by accounting for outstanding debt and available cash.

```math
Equity\ Value
=
Enterprise\ Value
-
Total\ Debt
+
Cash
```

The intrinsic share price is then calculated as

```math
Intrinsic\ Share\ Price=
\frac{Equity\ Value}
{Shares\ Outstanding}
```

---

## Margin of Safety

```math
Margin\ of\ Safety=
\frac
{Intrinsic\ Price-Market\ Price}
{Market\ Price}
```

A positive Margin of Safety indicates that the estimated intrinsic value exceeds the current market price, while a negative value indicates potential overvaluation.

---

## Implied Revenue Growth

Rather than assuming a fixed growth rate, the model estimates the revenue growth implied by the current market price using the **bisection method**. The projected growth rate is iteratively adjusted until the calculated intrinsic share price converges to the observed market price within a specified tolerance.

---

# Model Assumptions

* Five-year explicit forecast period
* Revenue initialized using Yahoo Finance revenue estimates
* Weighted historical operating margins
* Mid-year discounting convention
* CAPM used to estimate the cost of equity
* Historical interest expense used to estimate the cost of debt
* Gordon Growth Model used for terminal value estimation

---

# Technologies Used

* Python
* NumPy
* Pandas
* yfinance
* argparse

---

# References

* Yahoo Finance (`yfinance`) – Financial statements and market data
* Investopedia – Discounted Cash Flow (DCF)
* Investopedia – Weighted Average Cost of Capital (WACC)
* Investopedia – Capital Asset Pricing Model (CAPM)
* NYU Stern – Enterprise Value Multiples by Industry

---

# Disclaimer

This project is intended for educational and research purposes only. It should not be considered financial or investment advice. Financial data obtained through Yahoo Finance may contain inaccuracies or delays. Users should independently verify all information using official company filings before making investment decisions.
