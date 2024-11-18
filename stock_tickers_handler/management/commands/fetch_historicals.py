from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max

class Command(BaseCommand):
    help = 'Load tickers historical chart data for active US stocks from Yahoo Finance into the database'
    # FINAL START DATE FOR BEGINNING DOWNLOADING DATA

    BEGIN_DOWNLOADING_FROM = '2010-01-01'
    
    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        

        last_trading_day = self.get_last_trading_day(today)
        
        # Fetching available tickers from the ActiveStocksAlphaVantage model that are marked as available
        tickers_active_from_alpha_vantage = set(ActiveStocksAlphaVantage.objects.filter(is_hist_available=True).values_list('yahoo_ticker', flat=True))
        
        # print the number of tickers in ActiveStocksAlphaVantage
        self.stdout.write(self.style.SUCCESS(f"The number of tickers in ActiveStocksAlphaVantage: {len(tickers_active_from_alpha_vantage)}"))
        
        # Get outdated and no data tickers
        last_date_dict , outdated_ticker_list = self.get_outdated_tickers(last_trading_day)


        # print the number of outdated tickers
        self.stdout.write(self.style.SUCCESS(f"Tickers to update (outdated): {len(outdated_ticker_list)}"))

        
        # Get tickers without data
        tickers_no_data = list(tickers_active_from_alpha_vantage - set(
            outdated_ticker_list
        ))
        
        # print the number of tickers without data
        self.stdout.write(self.style.SUCCESS(f"Tickers without data: {len(tickers_no_data)}"))

        # Initialize counters for statistics
        total_updated_tickers = []
        total_not_updated_tickers = []
        

        # Fetch new data for tickers outdated
        if last_date_dict:
            # download in group based on date to update
            for last_data_date, tickers_to_update in last_date_dict.items():
                self.stdout.write(self.style.SUCCESS(f"Fetching new data for {len(tickers_to_update)} tickers... from {last_data_date}"))
                tickers_updated = self.fetch_data(tickers_to_update, start_date=last_data_date + timedelta(days=1))
                tickers_not_updated =  set(tickers_to_update) - set(tickers_updated)
                self.stdout.write(self.style.SUCCESS(f"Tickers updated: {len(tickers_updated)}, tickers not updated: {len(tickers_not_updated)} from {last_data_date} : {tickers_not_updated}" ))
                total_updated_tickers += tickers_updated
                total_not_updated_tickers += tickers_not_updated
        self.stdout.write(self.style.SUCCESS(f"Total tickers updated: {len(total_updated_tickers)}"))
        self.stdout.write(self.style.SUCCESS(f"Total tickers not updated: {len(total_not_updated_tickers)}"))
        

        total_updated_tickers_no_data = []
        total_not_updated_tickers_no_data = []

        # Fetch new data for tickers without data
        if tickers_no_data:
            self.stdout.write(self.style.SUCCESS(f"Fetching new data for {len(tickers_no_data)} tickers... from {BEGIN_DOWNLOADING_FROM}"))
            tickers_updated = self.fetch_data(tickers_no_data, start_date=BEGIN_DOWNLOADING_FROM)
            tickers_not_updated = set(tickers_to_update) - set(tickers_updated)
            self.stdout.write(self.style.SUCCESS(f"Tickers updated: {len(tickers_updated)}, tickers not updated: {len(tickers_not_updated)} from {BEGIN_DOWNLOADING_FROM} : {tickers_not_updated}" ))
            total_updated_tickers_no_data += tickers_updated
            total_not_updated_tickers_no_data += tickers_not_updated
        
      
    def get_last_trading_day(self, today):
        """Determine the last trading day considering weekends."""
        last_trading_day = today - timedelta(days=1)
        if today.weekday() == 0:  # Monday
            last_trading_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            last_trading_day = today - timedelta(days=2)
        return last_trading_day
        
  
    
    def get_outdated_tickers(self, last_trading_day):
        """Retrieve tickers with outdated data."""
        max_dates = HistoricalData.objects.filter(active_stocks_alpha_vantage__is_hist_available=True).values('active_stocks_alpha_vantage__yahoo_ticker').annotate(max_date=Max('date'))
       
        last_dates_tickers = max_dates.filter(max_date__lt=last_trading_day)
        
        last_dates_dict = {}
        outdated_ticker_list=[]
        for data in last_dates_tickers:
            ticker = data['active_stocks_alpha_vantage__yahoo_ticker']
            max_date = data['max_date']
            if max_date not in last_dates_dict:
                last_dates_dict[max_date] = []
            last_dates_dict[max_date].append(ticker)
            outdated_ticker_list.append(ticker)
       
        return last_dates_dict, outdated_ticker_list    
    
    def fetch_data(self, tickers_to_fetch, start_date, batch_size=20):
        """Fetch historical data from Yahoo Finance in batches."""
        historical_data_list = []
        tickers_updated = []

        # Break tickers into batches
        ticker_batches = [tickers_to_fetch[i:i + batch_size] for i in range(0, len(tickers_to_fetch), batch_size)]
        self.stdout.write(f"Total batches to process: {len(ticker_batches)}")

        for batch_num, tickers_batch in enumerate(ticker_batches, start=1):
            try:
                self.stdout.write(f"Downloading batch {batch_num}/{len(ticker_batches)}: {tickers_batch}")
                data = yf.download(tickers_batch, interval='1d', start=start_date, group_by='ticker', progress=True, actions=None)
                data = data.dropna(axis=0, how='all')
                
                if data.empty:
                    # All tickers in this batch failed
                    self.stdout.write(self.style.WARNING(f"No data returned for batch {batch_num}."))
                    continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to download data for batch {batch_num}: {e}"))
                continue

            for ticker in tickers_batch:
                if ticker not in data or data[ticker].dropna().empty:
                    self.stdout.write(self.style.WARNING(f"No data found for ticker {ticker} in batch {batch_num}."))
                    if start_date == "2010-01-01":
                        ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
                    continue

                # Populate data for valid tickers
                stock_instance = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
                ticker_data = data[ticker].dropna(axis=0, how='all')

                for date, row in ticker_data.iterrows():
                    date_obj = date.date()
                    if HistoricalData.objects.filter(active_stocks_alpha_vantage=stock_instance, date=date_obj).exists():
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

                    if len(historical_data_list) >= batch_size:
                        HistoricalData.objects.bulk_create(historical_data_list, batch_size=batch_size)
                        historical_data_list.clear()

                tickers_updated.append(ticker)

            # Bulk save any remaining data for the current batch
            if historical_data_list:
                HistoricalData.objects.bulk_create(historical_data_list)
                historical_data_list.clear()

        return tickers_updated
