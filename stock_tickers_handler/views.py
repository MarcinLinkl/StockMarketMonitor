from django.shortcuts import render
from .models import HistoricalData, ActiveStocksAlphaVantage
from datetime import datetime, timedelta
import json

from django.http import JsonResponse

SECTORS = {
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
    'XLY': "Consumer Discretionary"
}

def get_sectors_data(tickers):
    start_date = datetime.now().date() - timedelta(days=1000)
    historical_data = HistoricalData.objects.filter(
        active_stocks_alpha_vantage__yahoo_ticker=ticker,
        date__gte=start_date
    ).order_by('date').values(
        'active_stocks_alpha_vantage__yahoo_ticker',
        'date',
        'close'
    )

    # Convert historical data into a dictionary for easier access
    data_dict = {}
    for entry in historical_data:
        ticker = entry['active_stocks_alpha_vantage__yahoo_ticker']
        date = entry['date']
        close = entry['close']
        if ticker not in data_dict:
            data_dict[ticker] = {}
        data_dict[ticker][date] = close

    # Calculate changes
    changes = {}
    for ticker, prices in data_dict.items():
        changes[ticker] = {
            '1d': calculate_change(prices, 1),
            '1w': calculate_change(prices, 7),
            '1m': calculate_change(prices, 30),
            '1y': calculate_change(prices, 365),
            '2y': calculate_change(prices, 730),
        }

    return changes

def calculate_change(prices, days):
    dates = sorted(prices.keys())
    if len(dates) < 2:
        return None  # Not enough data to calculate change

    current_date = dates[-1]
    past_date = current_date - timedelta(days=days)

    if past_date in prices:
        current_price = prices[current_date]
        past_price = prices[past_date]
        return ((current_price - past_price) / past_price) * 100  # Percentage change
    else:
        return None  # Past date not found



def sector_performance_view(request):
    tickers = list(SECTORS.keys())
    sector_data = get_sectors_data(tickers)  # Call your function to get sector data
    
    # Prepare the response data
    response_data = [
        {'ticker':SECTORS.get(ticker), 'performance': performance} 
        for ticker, performance in sector_data.items()
    ]
    
    return JsonResponse(response_data, safe=False)






# def get_sector_fundamental(tickers):
#     sector_fundamentals = FundamentalData.objects.filter(
#         active_stocks_alpha_vantage__yahoo_ticker__in=tickers
#     ).values(
#         'trailing_pe', 'volume', 'average_volume', 
#         'fifty_day_moving_average', 'two_hundred_day_moving_average', 
#         'fifty_two_week_low', 'fifty_two_week_high', 'trailing_annual_dividend_yield'
#     )

#     # Pobieramy tylko pierwszy zestaw danych, zakładając, że istnieje co najmniej jeden
#     return sector_fundamentals.first()
