from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time
import requests
import yfinance as yf
from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, FundamentalData
import warnings
from django.db import close_old_connections

# Suppress specific warning
warnings.filterwarnings("ignore", category=RuntimeWarning, module="django.db.models.fields")

class Command(BaseCommand):
    help = 'Fetch and store key financial information for all tickers in the database'

    def fetch_data_for_ticker(self, ticker, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                session = requests.Session()
                session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
                info = yf.Ticker(ticker, session=session).info

                # Check if the response contains an error
                if 'quoteSummary' in info and info['quoteSummary'].get('error'):
                    error_description = info['quoteSummary']['error']['description']
                    self.stdout.write(self.style.WARNING(f'Error: {error_description} for ticker {ticker}'))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_yahoo_available=False)
                    return None

                if info.get('longName') is None:
                    self.stdout.write(self.style.WARNING(f'Error: ticker {ticker} has lack of basic info like Long Name, skipping.'))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_yahoo_available=False)
                    return None

                # Handle potential conversion issues
                info = {key: (None if value in ["Infinity", "NaN"] or value is None else value) for key, value in info.items()}

                # Convert timestamps to dates where necessary
                def convert_timestamp(ts):
                    return datetime.fromtimestamp(ts).date() if ts else None

                # Tworzenie obiektu FundamentalData bez zapisywania go od razu
                fundamental_data = FundamentalData(
                    active_stocks_alpha_vantage=ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker),
                    long_name=info.get('longName'),
                    exchange=info.get('exchange'),
                    quote_type=info.get('quoteType'),
                    industry=info.get('industry'),
                    sector=info.get('sector'),
                    long_business_summary=info.get('longBusinessSummary'),
                    previous_close=info.get('previousClose'),
                    dividend_rate=info.get('dividendRate'),
                    dividend_yield=info.get('dividendYield'),
                    ex_dividend_date=convert_timestamp(info.get('exDividendDate')),
                    payout_ratio=info.get('payoutRatio'),
                    beta=info.get('beta'),
                    trailing_pe=info.get('trailingPE'),
                    forward_pe=info.get('forwardPE'),
                    volume=info.get('volume'),
                    regular_market_volume=info.get('regularMarketVolume'),
                    average_volume=info.get('averageVolume'),
                    average_volume_10_days=info.get('averageVolume10days'),
                    market_cap=info.get('marketCap'),
                    fifty_two_week_low=info.get('fiftyTwoWeekLow'),
                    fifty_two_week_high=info.get('fiftyTwoWeekHigh'),
                    price_to_sales_trailing_12_months=info.get('priceToSalesTrailing12Months'),
                    fifty_day_moving_average=info.get('fiftyDayAverage'),
                    two_hundred_day_moving_average=info.get('twoHundredDayAverage'),
                    price_to_book=info.get('priceToBook'),
                    trailing_annual_dividend_rate=info.get('trailingAnnualDividendRate'),
                    trailing_annual_dividend_yield=info.get('trailingAnnualDividendYield'),
                    enterprise_value=info.get('enterpriseValue'),
                    profit_margins=info.get('profitMargins'),
                    float_shares=info.get('floatShares'),
                    shares_outstanding=info.get('sharesOutstanding'),
                    shares_short=info.get('sharesShort'),
                    shares_short_prior_month=info.get('sharesShortPriorMonth'),
                    shares_short_previous_month_date=convert_timestamp(info.get('sharesShortPreviousMonthDate')),
                    date_short_interest=convert_timestamp(info.get('dateShortInterest')),
                    shares_percent_shares_out=info.get('sharesPercentSharesOut'),
                    held_percent_insiders=info.get('heldPercentInsiders'),
                    held_percent_institutions=info.get('heldPercentInstitutions'),
                    short_ratio=info.get('shortRatio'),
                    short_percent_of_float=info.get('shortPercentOfFloat'),
                    implied_shares_outstanding=info.get('impliedSharesOutstanding'),
                    book_value=info.get('bookValue'),
                    last_fiscal_year_end=convert_timestamp(info.get('lastFiscalYearEnd')),
                    next_fiscal_year_end=convert_timestamp(info.get('nextFiscalYearEnd')),
                    most_recent_quarter=convert_timestamp(info.get('mostRecentQuarter')),
                    earnings_quarterly_growth=info.get('earningsQuarterlyGrowth'),
                    net_income_to_common=info.get('netIncomeToCommon'),
                    trailing_eps=info.get('trailingEps'),
                    forward_eps=info.get('forwardEps'),
                    peg_ratio=info.get('pegRatio'),
                    last_split_factor=info.get('lastSplitFactor'),
                    last_split_date=convert_timestamp(info.get('lastSplitDate')),
                    enterprise_to_revenue=info.get('enterpriseToRevenue'),
                    enterprise_to_ebitda=info.get('enterpriseToEbitda'),
                    fifty_two_week_change=info.get('52WeekChange'),
                    last_dividend_value=info.get('lastDividendValue'),
                    last_dividend_date=convert_timestamp(info.get('lastDividendDate')),
                    current_price=info.get('currentPrice'),
                    target_high_price=info.get('targetHighPrice'),
                    target_low_price=info.get('targetLowPrice'),
                    target_mean_price=info.get('targetMeanPrice'),
                    target_median_price=info.get('targetMedianPrice'),
                    number_of_analyst_opinions=info.get('numberOfAnalystOpinions'),
                    total_cash=info.get('totalCash'),
                    total_cash_per_share=info.get('totalCashPerShare'),
                    ebitda=info.get('ebitda'),
                    total_debt=info.get('totalDebt'),
                    quick_ratio=info.get('quickRatio'),
                    current_ratio=info.get('currentRatio'),
                    total_revenue=info.get('totalRevenue'),
                    debt_to_equity=info.get('debtToEquity'),
                    revenue_per_share=info.get('revenuePerShare'),
                    return_on_assets=info.get('returnOnAssets'),
                    return_on_equity=info.get('returnOnEquity'),
                    free_cashflow=info.get('freeCashflow'),
                    operating_cashflow=info.get('operatingCashflow'),
                    earnings_growth=info.get('earningsGrowth'),
                    revenue_growth=info.get('revenueGrowth'),
                    gross_margins=info.get('grossMargins'),
                    ebitda_margins=info.get('ebitdaMargins'),
                    operating_margins=info.get('operatingMargins'),
                    trailing_peg_ratio=info.get('trailingPegRatio')
                )
                
                return fundamental_data  # Zwracamy obiekt zamiast go zapisywać od razu
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
                return None  # W przypadku niepowodzenia zwracamy None
            finally:
                close_old_connections()  # Zamykamy stare połączenia

    def handle(self, *args, **kwargs):
        tickers = set(ActiveStocksAlphaVantage.objects.filter(is_yahoo_available=True).values_list('yahoo_ticker', flat=True))
        print("The number of tickers in ActiveStocksAlphaVantage: ", len(tickers))
        existing_ticker_ids = set(FundamentalData.objects.values_list('active_stocks_alpha_vantage_id', flat=True))
        print("The number of tickers in FundamentalData: ", len(existing_ticker_ids))
        tickers_to_fetch = ActiveStocksAlphaVantage.objects.filter(is_yahoo_available=True).values_list('yahoo_ticker', flat=True).exclude(id__in=existing_ticker_ids).values_list('yahoo_ticker', flat=True)
        tickers_to_fetch = set(tickers_to_fetch)
        print("The number of tickers to fetch: ", len(tickers_to_fetch))

        if not tickers_to_fetch:
            self.stdout.write(self.style.WARNING('No new tickers to fetch. Skipping...'))
            return  # No new tickers to fetch

        self.stdout.write(self.style.SUCCESS(f'Fetching data for {len(tickers_to_fetch)} new tickers'))


        batch_size = 100  # Możemy zmienić rozmiar partii wedle potrzeb
        fundamental_data_objects = []
        processed_tickers = []  # Lista przetworzonych tickerów

        with ThreadPoolExecutor(max_workers=100) as executor:
            for fundamental_data in executor.map(self.fetch_data_for_ticker, tickers_to_fetch):
                if fundamental_data:
                    fundamental_data_objects.append(fundamental_data)
                    processed_tickers.append(fundamental_data.active_stocks_alpha_vantage.yahoo_ticker)
                if len(fundamental_data_objects) >= batch_size:
                    FundamentalData.objects.bulk_create(fundamental_data_objects)
                    self.stdout.write(self.style.SUCCESS(f'Inserted batch of {len(fundamental_data_objects)} records: {processed_tickers}'))
                    fundamental_data_objects = []
                    processed_tickers = []

        # Wstawiamy pozostałe dane, jeśli jakieś zostały po ostatniej partii
        if fundamental_data_objects:
            FundamentalData.objects.bulk_create(fundamental_data_objects)
            self.stdout.write(self.style.SUCCESS(f'Inserted final batch of {len(fundamental_data_objects)} records: {processed_tickers}'))