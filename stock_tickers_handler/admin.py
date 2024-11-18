from django.contrib import admin
from .models import ActiveStocksAlphaVantage, FundamentalData

@admin.register(ActiveStocksAlphaVantage)
class ActiveStocksAlphaVantageAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'exchange', 'assetType', 'ipoDate', 'status')
    search_fields = ('ticker', 'name')

@admin.register(FundamentalData)
class FundamentalDataAdmin(admin.ModelAdmin):
    list_display = ( 'active_stocks_alpha_vantage__yahoo_ticker','long_name','previous_close', 'trailing_pe',"forward_pe",'sector','industry','exchange','quote_type')
    search_fields = ('active_stocks_alpha_vantage__yahoo_ticker','long_name','sector','industry','exchange','quote_type')
    list_filter = ('sector','industry' ,'quote_type')