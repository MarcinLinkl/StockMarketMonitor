from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch
from stock_tickers_handler.models import ActiveStocksAlphaVantage
import io
from datetime import datetime

class CommandTestCase(TestCase):
    @patch('requests.get')
    def test_load_tickers(self, mock_get):
        # Prepare mock response
        mock_response = io.StringIO(
            'symbol,name,exchange,assetType,ipoDate,status\n'
            'AAPL,Apple Inc.,NASDAQ,Equity,1980-12-12,Active\n'
            'GOOGL,Alphabet Inc.,NASDAQ,Equity,2004-08-19,Active\n'
        )
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_response.getvalue()

        # Run the command
        call_command('load_tickers')

        # Check database for the data
        self.assertEqual(ActiveStocksAlphaVantage.objects.count(), 2)
        
        apple = ActiveStocksAlphaVantage.objects.get(symbol='AAPL')
        self.assertEqual(apple.name, 'Apple Inc.')
        self.assertEqual(apple.ipoDate, datetime.strptime('1980-12-12', '%Y-%m-%d').date())  # Correct date comparison

        google = ActiveStocksAlphaVantage.objects.get(symbol='GOOGL')
        self.assertEqual(google.name, 'Alphabet Inc.')
        self.assertEqual(google.ipoDate, datetime.strptime('2004-08-19', '%Y-%m-%d').date())  # Correct date comparison
