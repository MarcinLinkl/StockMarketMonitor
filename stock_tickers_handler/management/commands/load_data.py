from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

class Command(BaseCommand):
    help = 'Load tickers historical chart data for active US stocks from Yahoo Finance into the database'

    def fetch_and_process_data(self, ticker, data, existing_dates_map):
        historical_data_list = []

        ticker_data = data[ticker].dropna(axis=0, how='all')
        if ticker_data.empty:
            self.stdout.write(self.style.WARNING(f"Skipping {ticker} because of empty data"))
            ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
            return []

        self.stdout.write(self.style.SUCCESS(f"Fetched data for {ticker}"))
        stock_instance = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
        existing_dates = existing_dates_map.get(ticker, set())

        for date, row in ticker_data.iterrows():
            date_obj = date.date()

            if date_obj not in existing_dates:
                historical_data_list.append(HistoricalData(
                    active_stocks_alpha_vantage=stock_instance,
                    date=date_obj,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    adj_close=row.get('Adj Close'),
                    volume=row['Volume']
                ))
        
        return historical_data_list

    def handle(self, *args, **kwargs):
        tickers = list(ActiveStocksAlphaVantage.objects.filter(is_hist_available=True).values_list('yahoo_ticker', flat=True))
        self.stdout.write(self.style.SUCCESS(f"The number of tickers in ActiveStocksAlphaVantage: {len(tickers)}"))

        batch_size = 20
        fetch_batch_size = 300
        historical_data_list = []
        tickers_to_update = []
        tickers_to_fetch = []

        last_trade_day = datetime.now().date() - timedelta(days=1)
        today = datetime.now().date()

        last_trading_day = today - timedelta(days=1)
        if today.weekday() == 0:  # Monday
            last_trading_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            last_trading_day = today - timedelta(days=2)
 

        existing_dates_map = {}
        for ticker in tickers:
            existing_dates = set(HistoricalData.objects.filter(active_stocks_alpha_vantage__yahoo_ticker=ticker).values_list('date', flat=True))
            existing_dates_map[ticker] = existing_dates

            last_date = max(existing_dates) if existing_dates else None
            if not last_date:
                tickers_to_fetch.append(ticker)
            elif last_date < last_trading_day:
                tickers_to_update.append(ticker)

        self.stdout.write(self.style.SUCCESS(f"Tickers to fetch (no data): {len(tickers_to_fetch)}"))
        self.stdout.write(self.style.SUCCESS(f"Tickers to update (outdated data): {len(tickers_to_update)}"))

        tickers_to_process = tickers_to_fetch + tickers_to_update

        for i in range(0, len(tickers_to_process), fetch_batch_size):
            tickers_batch = tickers_to_process[i:i + fetch_batch_size]
            self.stdout.write(self.style.WARNING(f"Fetching data for tickers: {tickers_batch}"))

            try:
                data = yf.download(tickers_batch, interval='1d', start='2014-01-01', end=datetime.now(), group_by='ticker')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to download data for batch {tickers_batch}: {e}"))
                continue

            with ThreadPoolExecutor(max_workers=50) as executor:
                future_to_ticker = {executor.submit(self.fetch_and_process_data, ticker, data, existing_dates_map): ticker for ticker in tickers_batch}

                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        historical_data_list.extend(future.result())
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f"{ticker} generated an exception: {exc}"))

                    if len(historical_data_list) >= batch_size:
                        HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)
                        historical_data_list.clear()

        if historical_data_list:
            HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded historical data for {len(tickers_to_process)} tickers into the database.'))
