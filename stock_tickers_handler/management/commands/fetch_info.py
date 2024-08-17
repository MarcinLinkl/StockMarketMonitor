from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
import sys
import yfinance as yf
from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, FundamentalData
import logging
import traceback
import warnings

# Suppress specific warning
warnings.filterwarnings("ignore", category=RuntimeWarning, module="django.db.models.fields")

class Command(BaseCommand):
    help = 'Fetch and store key financial information for all tickers in the database'
    
    def fetch_data_for_ticker(self, ticker):
     
        try:
            fundamental_data_obj = FundamentalData.objects.filter(ticker__symbol=ticker).first()
            if fundamental_data_obj:
                self.stdout.write(self.style.WARNING(f'Fundamental data for {ticker} already exists, skipping.'))
                return

            info = yf.Ticker(ticker).info

            if info.get('longName') is None:
                self.stdout.write(self.style.WARNING(f'Error: ticker {ticker} has lack of basic info like Long Name, skipping.'))
                return 

            # Handle potential conversion issues
            info = {key: (None if value in ["Infinity", "NaN"] or value is None else value) for key, value in info.items()}
            
            # Convert timestamps to dates where necessary
            def convert_timestamp(ts):
                return datetime.fromtimestamp(ts).date() if ts else None

            fundamental_data, created = FundamentalData.objects.update_or_create(
                ticker=ActiveStocksAlphaVantage.objects.get(symbol=ticker),
                defaults={
                    'long_name': info.get('longName'),
                    'exchange': info.get('exchange'),
                    'quote_type': info.get('quoteType'),
                    'industry': info.get('industry'),
                    'sector': info.get('sector'),
                    'long_business_summary': info.get('longBusinessSummary'),
                    'previous_close': info.get('previousClose'),
                    'dividend_rate': info.get('dividendRate'),
                    'dividend_yield': info.get('dividendYield'),
                    'ex_dividend_date': convert_timestamp(info.get('exDividendDate')),
                    'payout_ratio': info.get('payoutRatio'),
                    'beta': info.get('beta'),
                    'trailing_pe': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'volume': info.get('volume'),
                    'regular_market_volume': info.get('regularMarketVolume'),
                    'average_volume': info.get('averageVolume'),
                    'average_volume_10_days': info.get('averageVolume10days'),
                    'market_cap': info.get('marketCap'),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                    'price_to_sales_trailing_12_months': info.get('priceToSalesTrailing12Months'),
                    'fifty_day_moving_average': info.get('fiftyDayMovingAverage'),
                    'two_hundred_day_moving_average': info.get('twoHundredDayMovingAverage'),
                    'price_to_book': info.get('priceToBook'),
                    'trailing_annual_dividend_rate': info.get('trailingAnnualDividendRate'),
                    'trailing_annual_dividend_yield': info.get('trailingAnnualDividendYield'),
                    'enterprise_value': info.get('enterpriseValue'),
                    'profit_margins': info.get('profitMargins'),
                    'float_shares': info.get('floatShares'),
                    'shares_outstanding': info.get('sharesOutstanding'),
                    'shares_short': info.get('sharesShort'),
                    'shares_short_prior_month': info.get('sharesShortPriorMonth'),
                    'shares_short_previous_month_date': convert_timestamp(info.get('sharesShortPreviousMonthDate')),
                    'date_short_interest': convert_timestamp(info.get('dateShortInterest')),
                    'shares_percent_shares_out': info.get('sharesPercentSharesOut'),
                    'held_percent_insiders': info.get('heldPercentInsiders'),
                    'held_percent_institutions': info.get('heldPercentInstitutions'),
                    'short_ratio': info.get('shortRatio'),
                    'short_percent_of_float': info.get('shortPercentOfFloat'),
                    'implied_shares_outstanding': info.get('impliedSharesOutstanding'),
                    'book_value': info.get('bookValue'),
                    'last_fiscal_year_end': convert_timestamp(info.get('lastFiscalYearEnd')),
                    'next_fiscal_year_end': convert_timestamp(info.get('nextFiscalYearEnd')),
                    'most_recent_quarter': convert_timestamp(info.get('mostRecentQuarter')),
                    'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),
                    'net_income_to_common': info.get('netIncomeToCommon'),
                    'trailing_eps': info.get('trailingEps'),
                    'forward_eps': info.get('forwardEps'),
                    'peg_ratio': info.get('pegRatio'),
                    'last_split_factor': info.get('lastSplitFactor'),
                    'last_split_date': convert_timestamp(info.get('lastSplitDate')),
                    'enterprise_to_revenue': info.get('enterpriseToRevenue'),
                    'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                    'fifty_two_week_change': info.get('52WeekChange'),
                    'last_dividend_value': info.get('lastDividendValue'),
                    'last_dividend_date': convert_timestamp(info.get('lastDividendDate')),
                    'current_price': info.get('currentPrice'),
                    'target_high_price': info.get('targetHighPrice'),
                    'target_low_price': info.get('targetLowPrice'),
                    'target_mean_price': info.get('targetMeanPrice'),
                    'target_median_price': info.get('targetMedianPrice'),
                    'number_of_analyst_opinions': info.get('numberOfAnalystOpinions'),
                    'total_cash': info.get('totalCash'),
                    'total_cash_per_share': info.get('totalCashPerShare'),
                    'ebitda': info.get('ebitda'),
                    'total_debt': info.get('totalDebt'),
                    'quick_ratio': info.get('quickRatio'),
                    'current_ratio': info.get('currentRatio'),
                    'total_revenue': info.get('totalRevenue'),
                    'debt_to_equity': info.get('debtToEquity'),
                    'revenue_per_share': info.get('revenuePerShare'),
                    'return_on_assets': info.get('returnOnAssets'),
                    'return_on_equity': info.get('returnOnEquity'),
                    'free_cashflow': info.get('freeCashflow'),
                    'operating_cashflow': info.get('operatingCashflow'),
                    'earnings_growth': info.get('earningsGrowth'),
                    'revenue_growth': info.get('revenueGrowth'),
                    'gross_margins': info.get('grossMargins'),
                    'ebitda_margins': info.get('ebitdaMargins'),
                    'operating_margins': info.get('operatingMargins'),
                    'trailing_peg_ratio': info.get('trailingPegRatio')
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new fundamental data for {ticker}'))

        except Exception as e:
            
            # for key, value in  info.items():
            #     self.stdout.write(f'{key}: {value}')
            self.stdout.write(self.style.ERROR(f'Error fetching data for {ticker}: {e}'))
          
            # Optionally log traceback for debugging
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            
            
    def handle(self, *args, **kwargs):
        tickers = ActiveStocksAlphaVantage.objects.values_list('symbol', flat=True)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.fetch_data_for_ticker, tickers)