from django.db import models

class ActiveStocksAlphaVantage(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20)
    assetType = models.CharField(max_length=20)
    ipoDate = models.DateField(null=True, blank=True)
    delistingDate = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10)

    def __str__(self):
        return self.symbol