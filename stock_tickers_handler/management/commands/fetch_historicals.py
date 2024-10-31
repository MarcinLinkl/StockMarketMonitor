from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Load tickers historical chart data for active US stocks from Yahoo Finance into the database'
    
    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        last_trading_day = today - timedelta(days=1)
        
        # Adjust for weekends
        if today.weekday() == 0:  # Monday
            last_trading_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            last_trading_day = today - timedelta(days=2)

        # Fetching available tickers from the ActiveStocksAlphaVantage model that are marked as available
        tickers_active_from_alpha_vantage = set(ActiveStocksAlphaVantage.objects.filter(is_hist_available=True).values_list('yahoo_ticker', flat=True))

        # Get date dictionary for last data
        last_date_dict = {}
        max_dates = HistoricalData.objects.values('active_stocks_alpha_vantage__yahoo_ticker').annotate(max_date=Max('date'))

        # Get outdated tickers
        tickers_outdated = max_dates.filter(max_date__lt=last_trading_day)

        # Make dictionary for dates to be updated
        for data in tickers_outdated:
            ticker = data['active_stocks_alpha_vantage__yahoo_ticker']
            max_date = data['max_date']
            if max_date not in last_date_dict:
                last_date_dict[max_date] = []
            last_date_dict[max_date].append(ticker)

        # Get tickers without data
        no_data_tickers = tickers_active_from_alpha_vantage - set(max_dates.values_list('active_stocks_alpha_vantage__yahoo_ticker', flat=True))

        self.stdout.write(self.style.SUCCESS(f"The number of tickers in ActiveStocksAlphaVantage: {len(tickers_active_from_alpha_vantage)}"))
        self.stdout.write(self.style.SUCCESS(f"Tickers without data: {len(no_data_tickers)}"))
        self.stdout.write(self.style.SUCCESS(f"Tickers to update (outdated data): {len(tickers_outdated)}"))
        
        # Progress Bar for Fetching New Data
        if no_data_tickers:
            self.stdout.write(self.style.SUCCESS(f"Fetching new data for {len(no_data_tickers)} tickers... from {'2010-01-01'}"))
            with tqdm(total=len(no_data_tickers), desc="Fetching Data") as pbar:
                self.fetch_data(no_data_tickers, starts_date="2010-01-01", pbar=pbar, batch_size=20)

        # Progress Bar for Updating Data
        if last_date_dict:
            for date, tickers_to_update in last_date_dict.items():
                self.stdout.write(self.style.SUCCESS(f"Fetching data for {len(tickers_to_update)} tickers from {date}"))
                with tqdm(total=len(tickers_to_update), desc="Fetching Data") as pbar:
                    self.fetch_data(tickers_to_update, starts_date=date, pbar=pbar, batch_size=20)

    def fetch_data(self, tickers_to_fetch, starts_date="2010-01-01", end=None, pbar=None, batch_size=20):
        if end is None:
            end = datetime.now().date()
        historical_data_list = []
        try:
            print("Starting downloading data from", starts_date, "to", end)
            data = yf.download(tickers_to_fetch, interval='1d', start=starts_date, end=end, group_by='ticker', progress=True, actions=None)
            print("Downloaded data from", data.index[0], "to", data.index[-1])
            
            # Convert index to date and drop data for the starting date
            data.index = data.index.date
            data = data.loc[data.index != starts_date]
           
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to download data for tickers {tickers_to_fetch}: {e}"))
            return

        tickers_no_data = []
        tickers_successfully_fetched = []
        
        for ticker in tickers_to_fetch:
            if ticker not in data.columns:
                if starts_date == "2010-01-01":
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
                self.stdout.write(self.style.WARNING(f"Data for {ticker} not found in response"))
                pbar.update(1)
                continue

            ticker_data = data[ticker].dropna(axis=0, how='all')

            if ticker_data.empty:
                if starts_date == "2010-01-01":
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)

                tickers_no_data.append(ticker)
                pbar.update(1)
                continue
            
            tickers_successfully_fetched.append(ticker)
            stock_instance = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
            for date_obj, row in ticker_data.iterrows():
                
                
                # Check if the record already exists
                if HistoricalData.objects.filter(
                    active_stocks_alpha_vantage=stock_instance,
                    date=date_obj
                ).exists():
                    self.stdout.write(self.style.WARNING(f"Data for {ticker} on {date_obj} already exists. Skipping..."))
                    continue

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

                # Insert in batches
                if len(historical_data_list) >= batch_size:
                    HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)
                    historical_data_list.clear()

                pbar.update(1)

        # Log tickers with no data and those that were successfully fetched
        if tickers_no_data:
            self.stdout.write(self.style.WARNING(f"Tickers with no data from {starts_date}: {tickers_no_data}"))
        if tickers_successfully_fetched:
            self.stdout.write(self.style.SUCCESS(f"Tickers with data from {starts_date}: {tickers_successfully_fetched}"))

        # Insert remaining data if any
        if historical_data_list:
            HistoricalData.objects.bulk_create(historical_data_list)

        pbar.close()  # Ensure progress bar is closed
