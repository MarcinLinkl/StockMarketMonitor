import requests
import csv
from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage
from datetime import datetime
from io import StringIO

class Command(BaseCommand):
    help = 'Load tickers data for active US stocks from API AlphaVantage into the database'
    
   


    def handle(self, *args, **kwargs):
        # Define the API key and URL for Alpha Vantage
        api_key = 'YX9741BHQFXIYA0B'
        url = f'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={api_key}'
        skipped_rows = 0
        # Fetch data from the API
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Convert the response text into a StringIO object to read as a CSV file
            data = response.text
            csv_file = StringIO(data)
            reader = csv.DictReader(csv_file)
            records = []
            existing_ticker = set(ActiveStocksAlphaVantage.objects.values_list('ticker', flat=True))

            # Process each row in the CSV file
            for row in reader:
                try:
                    # Extract data from each row
                    ticker = row['symbol']
                    name = row['name']
                    exchange = row['exchange']
                    assetType = row['assetType']
                    ipoDate_str = row['ipoDate']
                    status = row['status']
                    yahoo_ticker = row['symbol'].replace('-P-', '-P').replace('/', '-')
        
                    # Skip rows with missing essential fields
                    if not ticker or not name or not exchange or not assetType or not status:
                        self.stdout.write(self.style.WARNING(f'Skipped row with missing basic data: Ticker:{ticker}, Name:{name}, Exhange:{exchange}, Asset:{assetType}, IPO:{ipoDate_str}, Status:{status}'))
                     
                        
                        skipped_rows += 1
                        continue

                    # Convert IPO date from string to date object, handle 'null' values
                    ipoDate = datetime.strptime(ipoDate_str, '%Y-%m-%d').date() if ipoDate_str and ipoDate_str.lower() != 'null' else None

                    # Check if the record already exists
                    if ticker not in existing_ticker:
                        records.append(
                            ActiveStocksAlphaVantage(
                                ticker=ticker,
                                name=name,
                                exchange=exchange,
                                assetType=assetType,
                                ipoDate=ipoDate,
                                status=status,
                                yahoo_ticker=yahoo_ticker
                            )
                        )
                        existing_ticker.add(ticker)
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Symbol already exists in the database: {ticker}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row {row}: {e}'))

            # Insert all records into the database in bulk
            if records:
                ActiveStocksAlphaVantage.objects.bulk_create(records)
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(records)} records from AlphaVantage API from into the database. Skipped {skipped_rows} rows with missing basic data'))
            else:
                self.stdout.write(self.style.WARNING('No valid records found to load into the database'))
        else:
            # Log an error if the API request fails
            self.stdout.write(self.style.ERROR(f'Failed to fetch data from API: {response.status_code}'))
        