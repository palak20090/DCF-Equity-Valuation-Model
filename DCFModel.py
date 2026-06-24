import numpy as np
import pandas as pd
import yfinance as yf
import warnings
from argparse import ArgumentParser

# Setup command line argument configurations
argument_parser = ArgumentParser()
argument_parser.add_argument("--ticker", dest="stock_symbol", default=None)
argument_parser.add_argument("--TGR", dest="perp_growth_rate", default=0.03)
argument_parser.add_argument("--riskfree", dest="risk_free_asset", default="^TNX")
argument_parser.add_argument("--market", dest="market_index", default="VTI")
arguments = argument_parser.parse_args()


class DiscountedCashFlowValuation:
    def __init__(self, stock_symbol, args):
        self.stock_symbol = stock_symbol
        self.stock_data = yf.Ticker(f"{stock_symbol}")
        
        # Financial Statement Extracted Data
        self.income_statement = self.stock_data.income_stmt
        self.balance_sheet = self.stock_data.balance_sheet
        self.cash_flow_statement = self.stock_data.cash_flow
        
        # Historical Variables Setup
        self.operating_income = None
        self.historical_revenue = None
        self.effective_tax_rate = None
        self.perp_growth_rate = args.perp_growth_rate
        
        # Weighting Arrays for Historical Moving Averages
        self.revenue_weights = np.array([0.4, 0.3, 0.2, 0.1])
        self.historical_tax_weights = np.array([0.5, 0.3, 0.2])
        
        # Market and Company Specific Valuation Metrics
        self.market_cap = self.stock_data.info["marketCap"]
        self.total_debt = self.stock_data.info["totalDebt"]
        self.cash_reserves = self.stock_data.info["totalCash"]
        self.shares_outstanding = self.stock_data.info["sharesOutstanding"]
        self.equity_beta = self.stock_data.info["beta"]
        self.interest_expense = self.income_statement.loc["Interest Expense"][0]
        
        # Macroeconomic Assumptions
        self.risk_free_rate = yf.Ticker(f"{args.risk_free_asset}").info["previousClose"] / 100
        self.market_return_rate = yf.Ticker(f"{args.market_index}").info["threeYearAverageReturn"]
        self.current_price = self.stock_data.info["previousClose"]
        
        # DCF Pipeline Executions
        self.forecasted_revenue = self._project_revenue()
        self.forecasted_ebit = self._project_operating_income()
        self.forecasted_tax = self._project_taxes()
        self.nopat = self._compute_nopat()
        self.forecasted_da = self._project_depreciation_amortization()
        self.forecasted_capex = self._project_capital_expenditure()
        self.forecasted_nwc_change = self._project_working_capital_changes()
        self.forecasted_fcf = self._compute_free_cash_flows()
        
        # Valuation Outcomes
        self.wacc_rate = self._compute_wacc()
        self.estimated_terminal_value = self._compute_terminal_value()
        self.calculated_enterprise_value = self._discount_cash_flows()
        self.fair_value_per_share = self._compute_fair_value_per_share()
        self.safety_margin = (self.fair_value_per_share - self.current_price) / self.current_price

    def _project_revenue(self):
        self.historical_revenue = self.income_statement.loc["Total Revenue"][:-1]
        rev_ttm = self.stock_data.revenue_estimate.loc["0y", "avg"]
        rev_growth_rate = 1 + self.stock_data.revenue_estimate.loc["+1y", "growth"]
        return pd.Series(rev_ttm * (rev_growth_rate ** i) for i in range(5))
    
    def _project_operating_income(self):
        self.operating_income = self.income_statement.loc["EBIT"][:-1]
        ebit_margin = np.average(self.operating_income / self.historical_revenue, weights=self.revenue_weights)
        return self.forecasted_revenue * ebit_margin
    
    def _project_taxes(self):
        tax_provisions = self.income_statement.loc["Tax Provision"][:-1]
        self.effective_tax_rate = np.average((tax_provisions / self.operating_income)[:3], weights=self.historical_tax_weights)
        return self.forecasted_ebit * self.effective_tax_rate
    
    def _compute_nopat(self):
        return self.forecasted_ebit - self.forecasted_tax
    
    def _project_depreciation_amortization(self):
        da_history = abs(self.cash_flow_statement.loc["Depreciation And Amortization"][:-1])
        da_margin = np.average(da_history / self.historical_revenue, weights=self.revenue_weights)
        return self.forecasted_revenue * da_margin
    
    def _project_capital_expenditure(self):
        capex_history = abs(self.cash_flow_statement.loc["Capital Expenditure"][:-1])
        capex_margin = np.average(capex_history / self.historical_revenue, weights=self.revenue_weights)
        return self.forecasted_revenue * capex_margin
    
    def _project_working_capital_changes(self):
        nwc_history = self.cash_flow_statement.loc["Change In Working Capital"][:-1]
        nwc_margin = np.average(nwc_history / self.historical_revenue, weights=self.revenue_weights)
        return self.forecasted_revenue * nwc_margin
    
    def _compute_free_cash_flows(self):
        return (self.nopat + self.forecasted_da - self.forecasted_capex - self.forecasted_nwc_change)
    
    def _compute_wacc(self):
        debt_weight = self.total_debt / (self.total_debt + self.market_cap)
        equity_weight = self.market_cap / (self.total_debt + self.market_cap)
        cost_of_debt = self.interest_expense / self.total_debt
        cost_of_equity = self.risk_free_rate + (self.equity_beta * (self.market_return_rate - self.risk_free_rate))
        return debt_weight * cost_of_debt * (1 - self.effective_tax_rate) + equity_weight * cost_of_equity
    
    def _compute_terminal_value(self):
        return (self.forecasted_fcf[4] * (1 + self.perp_growth_rate)) / (self.wacc_rate - self.perp_growth_rate)
    
    def _discount_cash_flows(self):
        discounted_fcfs = sum(
            pd.Series((fcf / ((1 + self.wacc_rate) ** (0.5 + i))) for i, fcf in enumerate(self.forecasted_fcf))
        )
        discounted_tv = self.estimated_terminal_value / ((1 + self.wacc_rate) ** 5)
        return discounted_fcfs + discounted_tv
    
    def _compute_fair_value_per_share(self):
        equity_value = self.calculated_enterprise_value - self.total_debt + self.cash_reserves
        return equity_value / self.shares_outstanding

    def find_implied_growth_rate(self, tolerance=0.01, max_iterations=100):
        def eval_price_at_growth(growth_rate):
            self.forecasted_revenue = pd.Series(self.historical_revenue.iloc[0] * ((1 + growth_rate) ** i) for i in range(5))
            self.forecasted_ebit = self._project_operating_income()
            self.forecasted_tax = self._project_taxes()
            self.nopat = self._compute_nopat()
            self.forecasted_da = self._project_depreciation_amortization()
            self.forecasted_capex = self._project_capital_expenditure()
            self.forecasted_nwc_change = self._project_working_capital_changes()
            self.forecasted_fcf = self._compute_free_cash_flows()
            self.estimated_terminal_value = self._compute_terminal_value()
            self.calculated_enterprise_value = self._discount_cash_flows()
            return self._compute_fair_value_per_share()

        lower_bound = -0.5
        upper_bound = 0.5
        
        for _ in range(max_iterations):
            mid_point = (lower_bound + upper_bound) / 2
            calculated_price = eval_price_at_growth(mid_point)
            
            if abs(calculated_price - self.current_price) < tolerance:
                return mid_point
            
            if calculated_price > self.current_price:
                upper_bound = mid_point
            else:
                lower_bound = mid_point
        
        raise ValueError("Implied growth rate calculation did not converge")


def main():
    warnings.filterwarnings("ignore")
    stock_symbol = str(f"{arguments.stock_symbol}").upper()
    valuation_model = DiscountedCashFlowValuation(stock_symbol, arguments)
    
    print(f"Implied Stock Price: {valuation_model.fair_value_per_share:.2f}")
    print(f"Margin of Safety: {valuation_model.safety_margin:.2%}")

    implied_growth = valuation_model.find_implied_growth_rate()
    print(f"Current price: {valuation_model.current_price} ; Implied Growth Rate: {implied_growth:.2%}")


if __name__ == "__main__":
    main()