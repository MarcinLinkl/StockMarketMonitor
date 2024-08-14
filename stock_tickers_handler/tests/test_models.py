from django.test import TestCase
from stock_tickers_handler.models import ActiveStocksAlphaVantage
from datetime import datetime

class ActiveStocksAlphaVantageModelTest(TestCase):

    def setUp(self):
        # Set up initial data for tests
        self.stock = ActiveStocksAlphaVantage.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            assetType='Equity',
            ipoDate=datetime.strptime('1980-12-12', '%Y-%m-%d').date(),
            status='Active'
        )

    def test_model_creation(self):
        # Test that the model instance was created correctly
        stock = ActiveStocksAlphaVantage.objects.get(symbol='AAPL')
        self.assertEqual(stock.name, 'Apple Inc.')
        self.assertEqual(stock.exchange, 'NASDAQ')
        self.assertEqual(stock.assetType, 'Equity')
        self.assertEqual(stock.ipoDate, datetime.strptime('1980-12-12', '%Y-%m-%d').date())
        self.assertEqual(stock.status, 'Active')

    def test_unique_symbol(self):
        # Test that symbol is unique
        with self.assertRaises(Exception) as context:
            ActiveStocksAlphaVantage.objects.create(
                symbol='AAPL',
                name='Another Company',
                exchange='NYSE',
                assetType='Bond',
                ipoDate=datetime.strptime('1990-01-01', '%Y-%m-%d').date(),
                status='Inactive'
            )
        self.assertTrue('UNIQUE constraint failed' in str(context.exception))

    def test_str_representation(self):
        # Test the string representation of the model
        self.assertEqual(str(self.stock), 'AAPL - Apple Inc.')
