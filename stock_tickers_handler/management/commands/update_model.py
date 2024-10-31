from django.core.management.base import BaseCommand
from stock_tickers_handler.models import ActiveStocksAlphaVantage, FundamentalData

class Command(BaseCommand):
    help = 'Update stock percentage calculations'

    def handle(self, *args, **kwargs):
        stocks = FundamentalData.objects.all()
        for stock in stocks:
            stock.save()  # To update the percentages as they are computed in the save method
        self.stdout.write(self.style.SUCCESS('Successfully updated stock percentages.'))