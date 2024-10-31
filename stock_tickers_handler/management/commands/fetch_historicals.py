from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max

class Command(BaseCommand):
    help = 'Load tickers historical chart data for active US stocks from Yahoo Finance into the database'
    
    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        # FINAL START DATE FOR BEGINNING DOWNLOADING DATA
        BEGIN_DOWNLOADING_FROM = '2010-01-01'

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
        tickers_no_data = tickers_active_from_alpha_vantage - set(
            outdated_ticker_list
        )
        
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
                tickers_not_updated =  set(tickers_updated) - set(tickers_updated)
                self.stdout.write(self.style.SUCCESS(f"Successfully tickers updated: {len(tickers_updated)} and not updated: {len(tickers_not_updated)} from {last_data_date} : {tickers_not_updated}" ))
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
            tickers_not_updated = set(tickers_updated) - set(tickers_updated)
            self.stdout.write(self.style.SUCCESS(f"Successfully tickers updated: {len(tickers_updated)} and not updated: {len(tickers_not_updated)} from {BEGIN_DOWNLOADING_FROM} : {tickers_not_updated}" ))
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
        """Fetch historical data from Yahoo Finance, handling missing data errors."""
        historical_data_list = []
        ticker_updated = []
        failed_tickers = []

        try:
            self.stdout.write(f"Starting downloading data from {start_date}")
            data = yf.download(tickers_to_fetch, interval='1d', start=start_date, group_by='ticker', progress=False, actions=None)
            data = data.dropna(axis=0, how='all')
            if data.empty:
                failed_tickers.extend(tickers_to_fetch)  # All tickers in this batch failed
                return ticker_updated, failed_tickers
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to download data for tickers {tickers_to_fetch}: {e}"))
            return ticker_updated, tickers_to_fetch  # Return all tickers as failed

        for ticker in tickers_to_fetch:
            if ticker not in data.columns or data[ticker].dropna().empty:
                failed_tickers.append(ticker)
                if start_date == "2010-01-01":
                    ActiveStocksAlphaVantage.objects.filter(yahoo_ticker=ticker).update(is_hist_available=False)
                self.stdout.write(self.style.WARNING(f"No data found for ticker: {ticker}, flagging it as unavailable"))
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

            ticker_updated.append(ticker)

        if historical_data_list:
            HistoricalData.objects.bulk_create(historical_data_list)

        return ticker_updated, failed_tickers
