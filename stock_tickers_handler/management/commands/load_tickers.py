import requests
import csv
from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage
from datetime import datetime
from io import StringIO

class Command(BaseCommand):
    help = 'Load tickers data for acvite US stocks from API AlphaVantage into the database'

    def handle(self, *args, **kwargs):
        # Define the API key and URL for Alpha Vantage
        api_key = 'YX9741BHQFXIYA0B'
        url = f'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={api_key}'

        # Fetch data from the API
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Convert the response text into a StringIO object to read as a CSV file
            data = response.text
            csv_file = StringIO(data)
            reader = csv.DictReader(csv_file)
            records = []

            # Process each row in the CSV file
            for row in reader:
                try:
                    # Extract data from each row
                    symbol = row['symbol']
                    name = row['name']
                    exchange = row['exchange']
                    assetType = row['assetType']
                    ipoDate_str = row['ipoDate']
                    status = row['status']

                    # Convert IPO date from string to date object, handle 'null' values
                    ipoDate = datetime.strptime(ipoDate_str, '%Y-%m-%d').date() if ipoDate_str and ipoDate_str.lower() != 'null' else None

                    # Append the new record to the list
                    records.append(
                        ActiveStocksAlphaVantage(
                            symbol=symbol,
                            name=name,
                            exchange=exchange,
                            assetType=assetType,
                            ipoDate=ipoDate,
                            status=status
                        )
                    )
                except Exception as e:
                    # Log any errors that occur during row processing
                    self.stdout.write(self.style.ERROR(f'Error processing row: {e}'))

            # Insert all records into the database in bulk
            ActiveStocksAlphaVantage.objects.bulk_create(records)

            # Output a success message
            self.stdout.write(self.style.SUCCESS('Successfully loaded data from API into the database'))
        else:
            # Log an error if the API request fails
            self.stdout.write(self.style.ERROR(f'Failed to fetch data from API: {response.status_code}'))
