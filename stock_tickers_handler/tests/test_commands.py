from django.core.management import call_command
from django.test import TestCase
import io
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock
from stock_tickers_handler.models import ActiveStocksAlphaVantage, HistoricalData

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
        
        apple = ActiveStocksAlphaVantage.objects.get(ticker='AAPL')
        self.assertEqual(apple.name, 'Apple Inc.')
        self.assertEqual(apple.ipoDate, datetime.strptime('1980-12-12', '%Y-%m-%d').date())  # Correct date comparison

        google = ActiveStocksAlphaVantage.objects.get(ticker='GOOGL')
        self.assertEqual(google.name, 'Alphabet Inc.')
        self.assertEqual(google.ipoDate, datetime.strptime('2004-08-19', '%Y-%m-%d').date())  # Correct date comparison


class TestLoadTickersHistoricalData(TestCase):

    @patch('stock_tickers_handler.models.ActiveStocksAlphaVantage.objects.filter')
    def test_fetch_tickers_from_database(self, mock_filter):
        mock_filter.return_value.values_list.return_value = ['AAPL', 'MSFT']
        call_command('load_data')
        mock_filter.assert_called_once_with(is_yahoo_available=True)
        self.assertEqual(mock_filter.return_value.values_list.call_count, 1)

    @patch('yfinance.download')
    @patch('stock_tickers_handler.models.ActiveStocksAlphaVantage.objects.filter')
    def test_no_data_for_ticker(self, mock_filter, mock_yf_download):
        mock_filter.return_value.values_list.return_value = ['AAPL', 'MSFT']
        mock_yf_download.return_value.get.side_effect = lambda ticker: None if ticker == 'AAPL' else MagicMock()
        call_command('load_data')
        mock_yf_download.assert_called_once_with(['AAPL', 'MSFT'], '1d', 'max')

    @patch('yfinance.download')
    @patch('stock_tickers_handler.models.HistoricalData.objects.bulk_create')
    @patch('stock_tickers_handler.models.ActiveStocksAlphaVantage.objects.filter')
    def test_bulk_create_historical_data(self, mock_filter, mock_bulk_create, mock_yf_download):
        mock_filter.return_value.values_list.return_value = ['AAPL']
        mock_yf_download.return_value.get.return_value.iterrows.return_value = [
            (datetime(2023, 1, 1), {'Open': 100, 'High': 110, 'Low': 90, 'Close': 105, 'Adj Close': 105, 'Volume': 1000})
        ]
        call_command('load_data')
        self.assertEqual(mock_bulk_create.call_count, 1)
        self.assertEqual(len(mock_bulk_create.call_args[0][0]), 1)