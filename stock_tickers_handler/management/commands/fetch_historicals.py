from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData
import yfinance as yf
from datetime import datetime, timedelta
from django.db.models import Max
from typing import List, Tuple, Dict

class Command(BaseCommand):
    help = 'Load historical chart data for active US stocks from Yahoo Finance into the database'
    DEFAULT_START_DATE = '2010-01-01'
    BATCH_SIZE = 20

    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        last_trading_day = self.get_last_trading_day(today)
        
        active_tickers = self.get_active_tickers()
        self.stdout.write(self.style.SUCCESS(f"Number of active tickers: {len(active_tickers)}"))

        last_date_dict, outdated_tickers, uptodate_tickers = self.get_outdated_tickers(last_trading_day)

        self.stdout.write(self.style.SUCCESS(f"Number of outdated tickers: {len(outdated_tickers)}"))
        self.stdout.write(self.style.SUCCESS(f"Number of uptodate tickers: {len(uptodate_tickers)}"))


        tickers_no_data = list(active_tickers - set(uptodate_tickers) - set(outdated_tickers))

        print(f"Number of no data tickers : {len(tickers_no_data)}")
      
        self.stdout.write(self.style.SUCCESS(f"Tickers with no data: {len(tickers_no_data)}"))

        total_updated, total_failed = self.update_tickers(last_date_dict)
        self.stdout.write(self.style.SUCCESS(f"Total tickers updated: {len(total_updated)}"))
        self.stdout.write(self.style.SUCCESS(f"Total tickers not updated: {len(total_failed)}"))

        self.update_tickers_without_data(tickers_no_data, self.DEFAULT_START_DATE)

    def get_last_trading_day(self, today: datetime.date) -> datetime.date:
        """Calculate the last trading day, accounting for weekends."""
        if today.weekday() == 0:  # Monday
            return today - timedelta(days=3)
        elif today.weekday() == 6:  # Sunday
            return today - timedelta(days=2)
        return today - timedelta(days=1)

    def get_active_tickers(self) -> set:
        """Fetch tickers available for historical data."""
        return set(
            ActiveStocksAlphaVantage.objects.filter(is_hist_available=True)
            .values_list('yahoo_ticker', flat=True)
        )

    def get_outdated_tickers(self, last_trading_day: datetime.date) -> Tuple[Dict[datetime.date, List[str]], List[str], List[str]]:
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
            if max_date < last_trading_day:
                last_date_dict.setdefault(max_date, []).append(ticker)
                outdated_tickers.append(ticker)
            else:
                uptodate_tickers.append(ticker)
        return last_date_dict, outdated_tickers, uptodate_tickers

    def update_tickers(self, last_date_dict: Dict[datetime.date, List[str]]) -> Tuple[List[str], List[str]]:
        """Fetch and update data for outdated tickers."""
        total_updated = []
        total_failed = []

        for last_data_date, tickers in last_date_dict.items():
            self.stdout.write(self.style.SUCCESS(f"Fetching data for {len(tickers)} tickers from {last_data_date}"))
            updated = self.fetch_data(tickers, start_date=last_data_date + timedelta(days=1))
            total_updated.extend(updated)

        return total_updated, total_failed

    def update_tickers_without_data(self, tickers: List[str], start_date: str):
        """Fetch and update data for tickers without any historical data."""
        if tickers:
            self.stdout.write(self.style.SUCCESS(f"Fetching data for {len(tickers)} tickers starting from {start_date}"))
            updated = self.fetch_data(tickers, start_date=start_date)
            self.stdout.write(self.style.SUCCESS(f"Tickers updated: {len(updated)}"))

    def fetch_data(self, tickers: List[str], start_date: str) -> List[str]:
        """Fetch and save historical data in batches."""
        tickers_updated = []
        batches = [tickers[i:i + self.BATCH_SIZE] for i in range(0, len(tickers), self.BATCH_SIZE)]
        self.stdout.write(f"Processing {len(batches)} batches")

        for batch_num, batch in enumerate(batches, start=1):
            self.stdout.write(f"Downloading batch {batch_num}/{len(batches)}: {batch}")
            data = yf.download(batch, interval='1d', start=start_date, group_by='ticker', progress=False, actions=False)

            if data.empty:
                self.stdout.write(self.style.WARNING(f"No data returned for batch {batch_num}."))
                continue

            for ticker in batch:
                try:
                    if ticker not in data or data[ticker].dropna().empty:
                        self.stdout.write(self.style.WARNING(f"No data found for ticker {ticker}"))
                        continue

                    self.save_historical_data(ticker, data[ticker])
                    tickers_updated.append(ticker)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing ticker {ticker}: {e}"))

        return tickers_updated

    def save_historical_data(self, ticker: str, data):
        """Save historical data for a given ticker."""
        stock = ActiveStocksAlphaVantage.objects.get(yahoo_ticker=ticker)
        rows = data.dropna(axis=0, how='all')
        historical_entries = [
            HistoricalData(
                active_stocks_alpha_vantage=stock,
                date=index.date(),
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                adj_close=row.get('Adj Close'),
                volume=row['Volume']
            )
            for index, row in rows.iterrows()
            if not HistoricalData.objects.filter(active_stocks_alpha_vantage=stock, date=index.date()).exists()
        ]
        HistoricalData.objects.bulk_create(historical_entries, batch_size=self.BATCH_SIZE)
