from decimal import Decimal
from django.db import models
from django.db.models import UniqueConstraint
class ActiveStocksAlphaVantage(models.Model):
    ticker = models.CharField(max_length=50, unique=True)  # ticker musi być unikalny
    name = models.CharField(max_length=250)
    exchange = models.CharField(max_length=50)
    assetType = models.CharField(max_length=50)
    ipoDate = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50)
    is_yahoo_available = models.BooleanField(default=True)
    is_hist_available = models.BooleanField(default=True)
    yahoo_ticker = models.CharField(max_length=50, unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ticker'], name='unique_ticker')
        ]
        verbose_name = "Active Stock Alpha Vantage"
        verbose_name_plural = "Active Stocks Alpha Vantage"

    
    def __str__(self):
        return f'{self.ticker} - {self.name}'


class FundamentalData(models.Model):
    active_stocks_alpha_vantage  = models.OneToOneField('ActiveStocksAlphaVantage', on_delete=models.CASCADE, related_name='fundamental_data')

    # Basic Info
    long_name = models.CharField(max_length=255, blank=False, null=False)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    long_business_summary = models.TextField(blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)
    
    # Price and Dividend Info
    previous_close = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    dividend_rate = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    dividend_yield = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    payout_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    beta = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    trailing_pe = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    forward_pe = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    price_to_sales_trailing_12_months = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    
    # Volume and Market Info
    regular_market_volume = models.BigIntegerField(blank=True, null=True)
    average_volume = models.BigIntegerField(blank=True, null=True)
    average_volume_10_days = models.BigIntegerField(blank=True, null=True)
   
    price_52_week_low = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    price_52_week_high = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    percent_from_52_week_high_low = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    percent_52_week_change = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    
    price_50_day_moving_average = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    price_200_day_moving_average = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    price_to_book = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)

    # Dividend and Enterprise Info
    trailing_annual_dividend_rate = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    trailing_annual_dividend_yield = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    enterprise_value = models.BigIntegerField(blank=True, null=True)
    
    # Share Info
    profit_margins = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    float_shares = models.BigIntegerField(blank=True, null=True)
    shares_outstanding = models.BigIntegerField(blank=True, null=True)
    shares_short = models.BigIntegerField(blank=True, null=True)
    shares_short_prior_month = models.BigIntegerField(blank=True, null=True)
    shares_short_previous_month_date = models.DateField(blank=True, null=True)
    date_short_interest = models.DateField(blank=True, null=True)
    shares_percent_shares_out = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    held_percent_insiders = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    held_percent_institutions = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    short_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    short_percent_of_float = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    implied_shares_outstanding = models.BigIntegerField(blank=True, null=True)
    
    # Financial Metrics
    book_value = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    last_fiscal_year_end = models.DateField(blank=True, null=True)
    next_fiscal_year_end = models.DateField(blank=True, null=True)
    most_recent_quarter = models.DateField(blank=True, null=True)
    earnings_quarterly_growth = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    net_income_to_common = models.BigIntegerField(blank=True, null=True)
    trailing_eps = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    forward_eps = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    peg_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    
    # Split and Dividend Info
    last_split_factor = models.CharField(max_length=25, blank=True, null=True)
    last_split_date = models.DateField(blank=True, null=True)
    enterprise_to_revenue = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    enterprise_to_ebitda = models.DecimalField(max_digits=14, decimal_places=5, blank=True, null=True)
    last_dividend_value = models.DecimalField(max_digits=16, decimal_places=5, blank=True, null=True)
    last_dividend_date = models.DateField(blank=True, null=True)
    
    # Target Prices
    target_high_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    target_low_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    target_mean_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    target_median_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    upside = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    # Analyst Opinions
    number_of_analyst_opinions = models.SmallIntegerField(blank=True, null=True)
    
    # Financial Metrics Continued
    total_cash = models.BigIntegerField(blank=True, null=True)
    total_cash_per_share = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    ebitda = models.BigIntegerField(blank=True, null=True)
    total_debt = models.BigIntegerField(blank=True, null=True)
    quick_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    current_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    total_revenue = models.BigIntegerField(blank=True, null=True)
    debt_to_equity = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    revenue_per_share = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    return_on_assets = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    return_on_equity = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    free_cashflow = models.BigIntegerField(blank=True, null=True)
    operating_cashflow = models.BigIntegerField(blank=True, null=True)
    earnings_growth = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    revenue_growth = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    gross_margins = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    ebitda_margins = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    operating_margins = models.DecimalField(max_digits=16, decimal_places=5, blank=True, null=True)
    trailing_peg_ratio = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)

    # Risk Factors
    audit_risk = models.SmallIntegerField(blank=True, null=True)
    board_risk = models.SmallIntegerField(blank=True, null=True)
    compensation_risk = models.SmallIntegerField(blank=True, null=True)
    shareholder_rights_risk = models.SmallIntegerField(blank=True, null=True)
    overall_risk = models.SmallIntegerField(blank=True, null=True)
    
    last_updated = models.DateTimeField(auto_now=True)


class HistoricalData(models.Model):
    active_stocks_alpha_vantage = models.ForeignKey('ActiveStocksAlphaVantage', on_delete=models.CASCADE, related_name='stock_historical')
    date = models.DateField()
    open = models.DecimalField(max_digits=20, decimal_places=5)
    high = models.DecimalField(max_digits=20, decimal_places=5)
    low = models.DecimalField(max_digits=20, decimal_places=5)
    close = models.DecimalField(max_digits=20, decimal_places=5)
    adj_close = models.DecimalField(max_digits=20, decimal_places=5)
    volume = models.BigIntegerField()
    def __str__(self):
        return f"{self.active_stocks_alpha_vantage.yahoo_ticker} - {self.date} - {self.close}"
    class Meta:
        verbose_name = "Historical Data"
        verbose_name_plural = "Historical Data"
        constraints = [
            UniqueConstraint(fields=['active_stocks_alpha_vantage', 'date'], name='unique_ticker_date')
        ]