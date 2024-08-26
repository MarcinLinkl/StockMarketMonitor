from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max

class Command(BaseCommand):
    help = 'Load tickers historical chart data for active US stocks from Yahoo Finance into the database'

    def handle(self, *args, **kwargs):
        tickers = list(ActiveStocksAlphaVantage.objects.filter(is_hist_available=True).values_list('yahoo_ticker', flat=True))
        self.stdout.write(self.style.SUCCESS(f"The number of tickers in ActiveStocksAlphaVantage: {len(tickers)}"))

        batch_size = 20
        historical_data_list = []
        tickers_to_update = []
        tickers_to_fetch = []

        today = datetime.now().date()
        last_trading_day = today - timedelta(days=1)
        if today.weekday() == 0:  # Monday
            last_trading_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            last_trading_day = today - timedelta(days=2)

        existing_dates_map = {}

        # Check if data for tickers is older than last_trading_day
        self.stdout.write(self.style.SUCCESS(f"Retrieving all tickers that are older than last_trading_day: {last_trading_day}"))
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

        # Counters for successful updates
        successful_fetch_count = 0
        successful_update_count = 0

        # Fetch and process new data
        if tickers_to_fetch:
            try:
                data = yf.download(tickers_to_fetch, interval='1d', start='2014-01-01', end=last_trading_day, group_by='ticker',progress=False, actions=None) 
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to download data for tickers_to_fetch {tickers_to_fetch}: {e}"))
                return
            
            for ticker in tickers_to_fetch:
                if ticker not in data.columns:
                    self.stdout.write(self.style.WARNING(f"Data for {ticker} not found in response"))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
                    continue

                ticker_data = data[ticker].dropna(axis=0, how='all')

                if ticker_data.empty:
                    self.stdout.write(self.style.WARNING(f"Skipping {ticker} because of empty data"))
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
                    continue
                
                self.stdout.write(self.style.SUCCESS(f"Fetched data for {ticker}"))        
                stock_instance = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
                for date, row in ticker_data.iterrows():
                    date_obj = date.date()

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

                successful_fetch_count += 1

            if historical_data_list:
                HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)
                self.stdout.write(self.style.SUCCESS(f"Bulk created {len(historical_data_list)} historical data records"))
                historical_data_list = []

        # Fetch and process updated data
        if tickers_to_update:
            last_dates = (
                HistoricalData.objects
                .filter(active_stocks_alpha_vantage__yahoo_ticker__in=tickers_to_update)
                .values('active_stocks_alpha_vantage__yahoo_ticker')
                .annotate(last_date=Max('date'))
            )

            ticker_date_map = {}
            for item in last_dates:
                ticker = item['active_stocks_alpha_vantage__yahoo_ticker']
                last_date = item['last_date']
                if last_date:
                    ticker_date_map.setdefault(last_date, set()).add(ticker)

            self.stdout.write(self.style.SUCCESS(f"Created last_dates_map for {len(ticker_date_map)} dates"))

            for last_date, tickers in ticker_date_map.items():
                self.stdout.write(self.style.SUCCESS(f"Tickers to update since {last_date}: {tickers}"))
                try:
                    data = yf.download(tickers, interval='1d', start=last_date + timedelta(days=1), end=last_trading_day, group_by='ticker' , threads=True,progress=False, actions=None) 
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to download data for tickers_to_update {tickers}: {e}"))
                    continue
                
                for ticker in tickers:
                    if ticker not in data.columns:
                        self.stdout.write(self.style.WARNING(f"Data for {ticker} not found in response"))
                        continue

                    ticker_data = data[ticker].dropna(axis=0, how='all')
                    if ticker_data.empty:
                        self.stdout.write(self.style.WARNING(f"Skipping {ticker} because of empty data"))
                        continue
                    else:
                        successful_update_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Fetched data for {ticker}"))
                    stock_instance = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
                    for date, row in ticker_data.iterrows():
                        date_obj = date.date()
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

                

            if historical_data_list:
                HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)
                self.stdout.write(self.style.SUCCESS(f"Bulk created {len(historical_data_list)} historical data records"))

        self.stdout.write(self.style.SUCCESS(f"Successful fetch updates: {successful_fetch_count}"))
        self.stdout.write(self.style.SUCCESS(f"Successful update operations: {successful_update_count}"))
        
