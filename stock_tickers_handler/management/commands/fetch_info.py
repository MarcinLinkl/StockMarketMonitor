from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import time
import requests
import yfinance as yf
from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, FundamentalData
import warnings
from django.db import close_old_connections

# Suppress specific warning (category must be a class, not a string)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="django.db.models.fields")

# Fields to be updated in the bulk update operation
UPDATE_FIELDS = [
    'previous_close', 'dividend_rate', 'dividend_yield', 'ex_dividend_date', 'payout_ratio', 
    'beta', 'trailing_pe', 'forward_pe', 'regular_market_volume', 'average_volume', 'average_volume_10_days',
    'market_cap', 'price_52_week_low', 'price_52_week_high', 'percent_from_52_week_high_low', 
    'price_to_sales_trailing_12_months', 'price_50_day_moving_average', 'price_200_day_moving_average',
    'price_to_book', 'trailing_annual_dividend_rate', 'trailing_annual_dividend_yield', 'enterprise_value', 
    'profit_margins', 'float_shares', 'shares_outstanding', 'shares_short', 'shares_short_prior_month', 
    'shares_short_previous_month_date', 'date_short_interest', 'shares_percent_shares_out', 
    'held_percent_insiders', 'held_percent_institutions', 'short_ratio', 'short_percent_of_float', 
    'implied_shares_outstanding', 'book_value', 'last_fiscal_year_end', 'next_fiscal_year_end', 
    'most_recent_quarter', 'earnings_quarterly_growth', 'net_income_to_common', 'trailing_eps', 
    'forward_eps', 'peg_ratio', 'last_split_factor', 'last_split_date', 'enterprise_to_revenue', 
    'enterprise_to_ebitda', 'percent_52_week_change', 'last_dividend_value', 'last_dividend_date', 
    'target_high_price', 'target_low_price', 'target_mean_price', 
    'target_median_price', 'upside', 'number_of_analyst_opinions', 'total_cash', 
    'total_cash_per_share', 'ebitda', 'total_debt', 'quick_ratio', 'current_ratio', 
    'total_revenue', 'debt_to_equity', 'revenue_per_share', 'return_on_assets', 'return_on_equity',
    'free_cashflow', 'operating_cashflow', 'earnings_growth', 'revenue_growth', 'gross_margins', 
    'ebitda_margins', 'operating_margins', 'trailing_peg_ratio',
    'audit_risk', 'board_risk', 'compensation_risk', 'shareholder_rights_risk', 'overall_risk'
]

# Function to round numerical values to 5 decimal places
def round_value(value):
    """Round float values to 5 decimal places, return None if value is None."""
    return round(value, 5) if value is not None else None

class Command(BaseCommand):
    help = 'Fetch and store key financial information for all tickers in the database'

    def fetch_data_for_ticker(self, ticker, retries=3):
        """Fetches financial data for a specific ticker with retry logic."""
        attempt = 0
        while attempt < retries:
            try:
                # Set up a session with headers for scraping
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate, sdch, br',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Upgrade-Insecure-Requests': '1'
                })
                info = yf.Ticker(ticker, session=session).info

                # Check for errors in the response
                if 'quoteSummary' in info and info['quoteSummary'].get('error'):
                    error_description = info['quoteSummary']['error']['description']
                    self.stdout.write(self.style.WARNING(f'Error: {error_description} for ticker {ticker}'))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_yahoo_available=False)
                    return None

                # Skip if longName is missing
                if info.get('longName') is None:
                    self.stdout.write(self.style.WARNING(f'Error: ticker {ticker} lacks basic info like Long Name, skipping.'))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_yahoo_available=False)
                    return None

                # Handle potential NaN or Infinity values by setting them to None
                info = {key: (None if value in ["Infinity", "NaN"] or value is None else value) for key, value in info.items()}

                # Convert timestamps to dates where necessary
                def convert_timestamp(ts):
                    """Convert a timestamp to a date."""
                    return datetime.fromtimestamp(ts).date() if ts else None

                # Create a FundamentalData object without saving it yet
                fundamental_data = FundamentalData(
                    active_stocks_alpha_vantage=ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker),
                    long_name=info.get('longName'),
                    exchange=info.get('exchange'),
                    quote_type=info.get('quoteType'),
                    industry=info.get('industry'),
                    sector=info.get('sector'),
                    long_business_summary=info.get('longBusinessSummary'),
                    previous_close=round_value(info.get('previousClose')),
                    dividend_rate=round_value(info.get('dividendRate')),
                    dividend_yield=round_value(info.get('dividendYield')),
                    ex_dividend_date=convert_timestamp(info.get('exDividendDate')),
                    payout_ratio=round_value(info.get('payoutRatio')),
                    beta=round_value(info.get('beta')),
                    trailing_pe=round_value(info.get('trailingPE')),
                    forward_pe=round_value(info.get('forwardPE')),
                    regular_market_volume=round_value(info.get('regularMarketVolume')),
                    average_volume=round_value(info.get('averageVolume')),
                    average_volume_10_days=round_value(info.get('averageVolume10days')),
                    market_cap=round_value(info.get('marketCap')),
                    price_52_week_low=round_value(info.get('fiftyTwoWeekLow')),
                    price_52_week_high=round_value(info.get('fiftyTwoWeekHigh')),
                    percent_from_52_week_high_low=(
                    round_value(((info.get('previousClose') - info.get('fiftyTwoWeekLow')) / (info.get('fiftyTwoWeekHigh') - info.get('fiftyTwoWeekLow'))) * 100) 
                    if info.get('fiftyTwoWeekHigh') is not None and info.get('fiftyTwoWeekLow') is not None and info.get('previousClose') is not None and info.get('fiftyTwoWeekHigh') != info.get('fiftyTwoWeekLow') else None
                    ),
                    price_to_sales_trailing_12_months=round_value(info.get('priceToSalesTrailing12Months')),
                    price_50_day_moving_average=round_value(info.get('fiftyDayAverage')),
                    price_200_day_moving_average=round_value(info.get('twoHundredDayAverage')),
                    price_to_book=round_value(info.get('priceToBook')),
                    trailing_annual_dividend_rate=round_value(info.get('trailingAnnualDividendRate')),
                    trailing_annual_dividend_yield=round_value(info.get('trailingAnnualDividendYield')),
                    enterprise_value=round_value(info.get('enterpriseValue')),
                    profit_margins=round_value(info.get('profitMargins')),
                    float_shares=round_value(info.get('floatShares')),
                    shares_outstanding=round_value(info.get('sharesOutstanding')),
                    shares_short=round_value(info.get('sharesShort')),
                    shares_short_prior_month=round_value(info.get('sharesShortPriorMonth')),
                    shares_short_previous_month_date=convert_timestamp(info.get('sharesShortPreviousMonthDate')),
                    date_short_interest=convert_timestamp(info.get('dateShortInterest')),
                    shares_percent_shares_out=round_value(info.get('sharesPercentSharesOut')),
                    held_percent_insiders=round_value(info.get('heldPercentInsiders')),
                    held_percent_institutions=round_value(info.get('heldPercentInstitutions')),
                    short_ratio=round_value(info.get('shortRatio')),
                    short_percent_of_float=round_value(info.get('shortPercentOfFloat')),
                    implied_shares_outstanding=round_value(info.get('impliedSharesOutstanding')),
                    book_value=round_value(info.get('bookValue')),
                    last_fiscal_year_end=convert_timestamp(info.get('lastFiscalYearEnd')),
                    next_fiscal_year_end=convert_timestamp(info.get('nextFiscalYearEnd')),
                    most_recent_quarter=convert_timestamp(info.get('mostRecentQuarter')),
                    earnings_quarterly_growth=round_value(info.get('earningsQuarterlyGrowth')),
                    net_income_to_common=round_value(info.get('netIncomeToCommon')),
                    trailing_eps=round_value(info.get('trailingEps')),
                    forward_eps=round_value(info.get('forwardEps')),
                    peg_ratio=round_value(info.get('pegRatio')),
                    last_split_factor=info.get('lastSplitFactor'),
                    last_split_date=convert_timestamp(info.get('lastSplitDate')),
                    enterprise_to_revenue=round_value(info.get('enterpriseToRevenue')),
                    enterprise_to_ebitda=round_value(info.get('enterpriseToEbitda')),
                    percent_52_week_change=round_value(info.get('52WeekChange'))*100 if info.get('52WeekChange') is not None else None,
                    last_dividend_value=round_value(info.get('lastDividendValue')),
                    last_dividend_date=convert_timestamp(info.get('lastDividendDate')),
                    target_high_price=round_value(info.get('targetHighPrice')),
                    target_low_price=round_value(info.get('targetLowPrice')),
                    target_mean_price=round_value(info.get('targetMeanPrice')),
                    target_median_price=round_value(info.get('targetMedianPrice')),
                    upside=round_value((info.get('targetMedianPrice') - info.get('previousClose')) / info.get('previousClose')) *100 if info.get('previousClose') is not None and info.get('targetMedianPrice') is not None else None,
                    number_of_analyst_opinions=round_value(info.get('numberOfAnalystOpinions')),
                    total_cash=round_value(info.get('totalCash')),
                    total_cash_per_share=round_value(info.get('totalCashPerShare')),
                    ebitda=round_value(info.get('ebitda')),
                    total_debt=round_value(info.get('totalDebt')),
                    quick_ratio=round_value(info.get('quickRatio')),
                    current_ratio=round_value(info.get('currentRatio')),
                    total_revenue=round_value(info.get('totalRevenue')),
                    debt_to_equity=round_value(info.get('debtToEquity')),
                    revenue_per_share=round_value(info.get('revenuePerShare')),
                    return_on_assets=round_value(info.get('returnOnAssets')),
                    return_on_equity=round_value(info.get('returnOnEquity')),
                    free_cashflow=round_value(info.get('freeCashflow')),
                    operating_cashflow=round_value(info.get('operatingCashflow')),
                    earnings_growth=round_value(info.get('earningsGrowth')),
                    revenue_growth=round_value(info.get('revenueGrowth')),
                    gross_margins=round_value(info.get('grossMargins')),
                    ebitda_margins=round_value(info.get('ebitdaMargins')),
                    operating_margins=round_value(info.get('operatingMargins')),
                    trailing_peg_ratio=round_value(info.get('trailingPegRatio')),
                    audit_risk=round_value(info.get('auditRisk')),
                    board_risk=round_value(info.get('boardRisk')),
                    compensation_risk=round_value(info.get('compensationRisk')),
                    shareholder_rights_risk=round_value(info.get('shareHolderRightsRisk')),
                    overall_risk=round_value(info.get('overallRisk'))
                )

                return fundamental_data
            except requests.exceptions.HTTPError as http_err:
                if http_err.response.status_code == 404:
                    self.stdout.write(self.style.WARNING(f'Error 404: ticker {ticker} not found. Marking as unavailable.'))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_yahoo_available=False)
                    return None
                else:
                    attempt += 1
                    self.stdout.write(self.style.ERROR(f'HTTP error for {ticker} on attempt {attempt}: {http_err}'))
                    if attempt < retries:
                        self.stdout.write(self.style.WARNING(f'Retrying in 20 seconds...'))
                        time.sleep(20)  # Wait before retrying
            except Exception as e:
                attempt += 1
                self.stdout.write(self.style.ERROR(f'Error fetching data for {ticker} on attempt {attempt}: {e}'))
                if attempt < retries:
                    self.stdout.write(self.style.WARNING(f'Retrying in 20 seconds...'))
                    time.sleep(20)  # Wait before retrying
                return None  # Return None if an error occurred
            finally:
                close_old_connections()  # Close any open connections

    def handle(self, *args, **kwargs):
        # Fetching available tickers from the ActiveStocksAlphaVantage model that are marked as available
        tickers = set(ActiveStocksAlphaVantage.objects.filter(is_yahoo_available=True).values_list('yahoo_ticker', flat=True))
        print("The number of tickers in ActiveStocksAlphaVantage: ", len(tickers))

        # Fetching tickers from the FundamentalData model that were updated in the last 30 days
        last_month_back = datetime.now() - timedelta(days=30)
        existing_ticker_ids = set(FundamentalData.objects.filter(last_updated__gte=last_month_back).values_list('active_stocks_alpha_vantage_id', flat=True))

        print("The number of tickers in FundamentalData updated in the last 30 days: ", len(existing_ticker_ids))

        # Fetching tickers to update (those that are available and haven't been updated in the last 30 days)
        tickers_to_fetch = set(
            ActiveStocksAlphaVantage.objects.filter(is_yahoo_available=True)
            .exclude(id__in=existing_ticker_ids)
            .values_list('yahoo_ticker', flat=True)
        )
        print("The number of tickers outdated (tickers to fetch): ", len(tickers_to_fetch))

        # If there are no new tickers to fetch, skip the operation
        if not tickers_to_fetch:
            self.stdout.write(self.style.WARNING('No new tickers to fetch. Skipping...'))
            return  # No new tickers to fetch

        # Inform the user about the number of tickers being fetched
        self.stdout.write(self.style.SUCCESS(f'Fetching data for {len(tickers_to_fetch)} new tickers'))

        batch_size = 10  # Set batch size for bulk inserts
        fundamental_data_objects = []
        processed_tickers = []  # List of processed tickers

        # Use ThreadPoolExecutor to handle multiple tickers concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            for fundamental_data in executor.map(self.fetch_data_for_ticker, tickers_to_fetch):
                if fundamental_data:
                    # Append the fetched data to the list
                    fundamental_data_objects.append(fundamental_data)
                    processed_tickers.append(fundamental_data.active_stocks_alpha_vantage.yahoo_ticker)

                # Once the batch reaches the set size, bulk create the records in the database
                if len(fundamental_data_objects) >= batch_size:
                    try:
                        FundamentalData.objects.bulk_create(
                            fundamental_data_objects,
                            update_conflicts=True,
                            unique_fields=["active_stocks_alpha_vantage"],
                            update_fields=UPDATE_FIELDS
                        )
                        self.stdout.write(self.style.SUCCESS(f'Inserted batch of {len(fundamental_data_objects)} records: {processed_tickers}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error during bulk_create for batch: {e}"))
                    finally:
                        fundamental_data_objects = []
                        processed_tickers = []

        # Insert any remaining records if the batch size was not reached
        if fundamental_data_objects:
            try:
                FundamentalData.objects.bulk_create(
                    fundamental_data_objects,
                    update_conflicts=True,
                    unique_fields=["active_stocks_alpha_vantage"],
                    update_fields=UPDATE_FIELDS
                )
                self.stdout.write(self.style.SUCCESS(f'Inserted final batch of {len(fundamental_data_objects)} records: {processed_tickers}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error during final bulk_create: {e}"))
                self.stdout.write(self.style.NOTICE(f"Final batch of {len(fundamental_data_objects)} records not inserted."))
                # print all the objects infos
                for fundamental_data in fundamental_data_objects:
                    print(fundamental_data)
