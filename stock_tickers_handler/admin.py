from django.contrib import admin
from .models import ActiveStocksAlphaVantage, FundamentalData

@admin.register(ActiveStocksAlphaVantage)
class ActiveStocksAlphaVantageAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'exchange', 'assetType', 'ipoDate', 'status')
    search_fields = ('ticker', 'name')

@admin.register(FundamentalData)
class FundamentalDataAdmin(admin.ModelAdmin):
    list_display = ('yahoo_ticker', 'long_name', 'sector', 'industry','quote_type', 'current_price','target_mean_price', \
                     'market_cap', 'price_to_sales_trailing_12_months', 'book_value','price_to_book','trailing_pe',"forward_pe")
    search_fields = ('yahoo_ticker__ticker','sector','industry','exchange','quote_type')
    list_filter = ('sector','industry' ,'quote_type')