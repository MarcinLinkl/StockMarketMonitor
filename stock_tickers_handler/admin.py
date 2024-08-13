from django.contrib import admin
from .models import ActiveStocksAlphaVantage

@admin.register(ActiveStocksAlphaVantage)
class ActiveStocksAlphaVantageAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'exchange', 'assetType', 'ipoDate', 'status')
    search_fields = ('symbol', 'name')
