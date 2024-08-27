from django.shortcuts import render
from .models import HistoricalData, ActiveStocksAlphaVantage
from datetime import datetime, timedelta
import json

# TICKERS dictionary updated with sector names
TICKERS = {
    'XLRE': "Real Estate",
    'XLE': "Energy",
    'XLV': "Health Care",
    'XLF': "Financial",
    'XLI': "Industrial",
    'XLP': "Consumer Staples",
    'XLC': "Communication Services",
    'XLU': "Utilities",
    'XLK': "Technology",
    'XLB': "Materials",
    'XLY': "Consumer Discretionary (Consumer Cyclical)"
}

def get_sector_performance(ticker, days):
    start_date = datetime.now().date() - timedelta(days=days)
    
    historical_data = HistoricalData.objects.filter(
        active_stocks_alpha_vantage__yahoo_ticker=ticker,
        date__gte=start_date
    ).order_by('date')
    
    if historical_data.exists():
        start_price = historical_data.first().adj_close
        end_price = historical_data.last().adj_close
        performance_change = ((end_price - start_price) / start_price) * 100
        return float('{:.2f}'.format(performance_change))  # Format to 2 decimal places and return performance_change
    
    return None

def home(request):
    performance_data = {
        '5_years': {},
        '2_years': {},
        '1_year': {},
        '3_months': {},
        '1_month': {},
        '1_week': {},
    }

    for ticker, sector in TICKERS.items():
        for period in performance_data.keys():
            days = {
                '5_years': 1825,
                '2_years': 730,
                '1_year': 365,
                '3_months': 90,
                '1_month': 30,
                '1_week': 7,
            }[period]
            
            performance = get_sector_performance(ticker, days)
            if performance is not None:
                performance_data[period][sector] = performance

    # Sort data by performance
    sorted_performance_data = {
        period: dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        for period, data in performance_data.items()
    }

    return render(request, 'stock_tickers_handler/home.html', {
        'performance_data': json.dumps(sorted_performance_data),  # Convert to JSON
    })
