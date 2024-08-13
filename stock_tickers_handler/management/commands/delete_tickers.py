from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage

class Command(BaseCommand):
    help = 'Delete all data from the ActiveStocksAlphaVantage table'

    def handle(self, *args, **kwargs):
        # Delete all records from the ActiveStocksAlphaVantage model
        deleted_count, _ = ActiveStocksAlphaVantage.objects.all().delete()

        # Output the result
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} records from the database'))