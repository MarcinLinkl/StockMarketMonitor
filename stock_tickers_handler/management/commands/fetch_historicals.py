from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max


class Command(BaseCommand):
    help = 'Load historical chart data for active US stocks from Yahoo Finance into the database'

    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        BEGIN_DOWNLOADING_FROM = '2010-01-01'
        last_trading_day = self.get_last_trading_day(today)

        # Fetch tickers available for historical data
        active_tickers = set(
            ActiveStocksAlphaVantage.objects.filter(is_hist_available=True).values_list('yahoo_ticker', flat=True)
        )
        self.stdout.write(self.style.SUCCESS(f"Number of active tickers: {len(active_tickers)}"))

        # Determine outdated tickers
        last_date_dict, outdated_tickers, uptodate_tickers = self.get_outdated_tickers(last_trading_day)

        print(outdated_tickers[:10])
        print(uptodate_tickers[:10])

        self.stdout.write(self.style.SUCCESS(f"Outdated tickers to update: {len(outdated_tickers)}"))

        # Determine tickers without any data
        tickers_no_data = list(active_tickers - set(uptodate_tickers))
        self.stdout.write(self.style.SUCCESS(f"Tickers with no data: {len(tickers_no_data)}"))

        # Update outdated tickers
        total_updated, total_failed = self.update_tickers(last_date_dict)
        self.stdout.write(self.style.SUCCESS(f"Total tickers updated: {len(total_updated)}"))
        self.stdout.write(self.style.SUCCESS(f"Total tickers not updated: {len(total_failed)}"))

        # Fetch data for tickers without any data
        self.update_tickers_without_data(tickers_no_data, BEGIN_DOWNLOADING_FROM)

    def get_last_trading_day(self, today):
        """Calculate the last trading day, accounting for weekends."""
        last_trading_day = today - timedelta(days=1)
        if today.weekday() == 0:  # Monday
            last_trading_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            last_trading_day = today - timedelta(days=2)
        return last_trading_day

    def get_outdated_tickers(self, last_trading_day):
        """Identify tickers with outdated data."""
        max_dates = HistoricalData.objects.filter(
            active_stocks_alpha_vantage__is_hist_available=True
        ).values('active_stocks_alpha_vantage__yahoo_ticker').annotate(max_date=Max('date'))
        
        outdated_tickers = []
        uptodate_tickers = []
        last_date_dict = {}

        for entry in max_dates:
            ticker = entry['active_stocks_alpha_vantage__yahoo_ticker']
            max_date = entry['max_date']
            
            # Check if the max_date is older than the last trading day
            if max_date < last_trading_day:
                last_date_dict.setdefault(max_date, []).append(ticker)
                outdated_tickers.append(ticker)
            else:
                uptodate_tickers.append(ticker)
                
        return last_date_dict, outdated_tickers, uptodate_tickers

    def update_tickers(self, last_date_dict):
        """Fetch and update data for outdated tickers."""
        total_updated = []
        total_failed = []

        if last_date_dict:
            for last_data_date, tickers in last_date_dict.items():
                self.stdout.write(self.style.SUCCESS(f"Fetching data for {len(tickers)} tickers from {last_data_date}"))
                updated, failed = self.fetch_data(tickers, start_date=last_data_date + timedelta(days=1))
                total_updated.extend(updated)
                total_failed.extend(failed)

        return total_updated, total_failed

    def update_tickers_without_data(self, tickers, start_date):
        """Fetch and update data for tickers without any historical data."""
        if tickers:
            self.stdout.write(self.style.SUCCESS(f"Fetching data for {len(tickers)} tickers starting from {start_date}"))
            updated, failed = self.fetch_data(tickers, start_date=start_date)
            self.stdout.write(self.style.SUCCESS(f"Tickers updated: {len(updated)}"))
            self.stdout.write(self.style.SUCCESS(f"Tickers not updated: {len(failed)}"))

    def fetch_data(self, tickers, start_date, batch_size=20):
        """Fetch and save historical data in batches."""
        tickers_updated = []
        tickers_failed = []

        batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        self.stdout.write(f"Processing {len(batches)} batches")

        for batch_num, batch in enumerate(batches, start=1):
            try:
                self.stdout.write(f"Downloading batch {batch_num}/{len(batches)}: {batch}")
                data = yf.download(batch, interval='1d', start=start_date, group_by='ticker', progress=False, actions=False)
                if data.empty:
                    self.stdout.write(self.style.WARNING(f"No data returned for batch {batch_num}."))
                    tickers_failed.extend(batch)
                    continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error fetching batch {batch_num}: {e}"))
                tickers_failed.extend(batch)
                continue

            for ticker in batch:
                try:
                    if ticker not in data or data[ticker].dropna().empty:
                        self.stdout.write(self.style.WARNING(f"No data found for ticker {ticker}"))
                        continue

                    stock = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)

                    rows = data[ticker].dropna(axis=0, how='all')
    
                    historical_entries = [
                        HistoricalData(
                            active_stocks_alpha_vantage=stock,
                            date=_.date(),
                            open=row['Open'],
                            high=row['High'],
                            low=row['Low'],
                            close=row['Close'],
                            adj_close=row.get('Adj Close'),
                            volume=row['Volume']
                        )
                        for _, row in rows.iterrows() if not HistoricalData.objects.filter(active_stocks_alpha_vantage=stock, date= _.date()).exists()

                    ]
                    HistoricalData.objects.bulk_create(historical_entries, batch_size=batch_size)
                    tickers_updated.append(ticker)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing ticker {ticker}: {e}"))
                    tickers_failed.append(ticker)

        return tickers_updated, tickers_failed
