from django.db import models

class ActiveStocksAlphaVantage(models.Model):
    symbol = models.CharField(max_length=10, unique=True)  # Symbol musi być unikalny
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=50)
    assetType = models.CharField(max_length=50)
    ipoDate = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['symbol'], name='unique_symbol')
        ]
    
    def __str__(self):
        return f'{self.symbol} - {self.name}'