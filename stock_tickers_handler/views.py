from django.shortcuts import render
from .models import HistoricalData,FundamentalData ,ActiveStocksAlphaVantage
from datetime import datetime, timedelta
import json
import yfinance as yf
from django.utils import timezone
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
    'XLY': "Consumer Discretionary"
}

def get_sectors_data(tickers):
    start_date = datetime.now().date() - timedelta(days=1000)
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

def sectors_view(request):
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

    return render(request, 'sectors.html', {'performance_data': json.dumps(performance_data)})





def indexes_view(request):
    # Definiuj tickery dla różnych indeksów i surowców
    tickers = {
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC',
        'Dow Jones': '^DJI',
        'DAX': '^GDAXI',
        'FTSE 100': '^FTSE',
        'CAC 40': '^FCHI',
        'Hang Seng': '^HSI',
        'Nikkei 225': '^N225',
        'Gold': 'GC=F',
        'Silver': 'SI=F',
        'Palladium': 'PA=F',
        'Platinum': 'PL=F',
        'Crude Oil': 'CL=F',
        'Natural Gas': 'NG=F',
    }

    # Oblicz daty początkową i końcową
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365 * 2)  # 2 lata wstecz

    index_data = {}
    for index, ticker in tickers.items():
        # Pobierz dane z yfinance
        data = yf.download(ticker, start=start_date, end=end_date)

        if not data.empty:  # Sprawdź, czy dane zostały pobrane
            index_data[index] = {
                'current_price': data['Close'].iloc[-1],  # Ostatnia cena zamknięcia
                'day_change': ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100,  # Procentowa zmiana w ciągu ostatniego dnia
                'prices': data['Close'].tolist(),  # Lista cen zamknięcia
                'dates': data.index.strftime('%Y-%m-%d').tolist()  # Lista dat
            }

    context = {
        'index_data': index_data,
    }
    return render(request, 'indexes.html', context)
def search_view(request):
    query = request.GET.get('query', '')  # Get the search query from the request
    results = []

    if query:  # If a query is provided
        # Filtering the FundamentalData based on the search query
        results = FundamentalData.objects.filter(
            active_stocks_alpha_vantage__yahoo_ticker__icontains=query
        ) | FundamentalData.objects.filter(
            long_name__icontains=query
        )

    return render(request, 'search.html', {'results': results})

def charts_view(request):
    # Logika widoku dla Charts
    # Możesz dodać dane do wykresów tutaj
    performance_data = {
        '1_year': {'Technology': 20, 'Finance': 15, 'Health': 10, 'Energy': 8},
        '6_months': {'Technology': 15, 'Finance': 10, 'Health': 12, 'Energy': 5},
    }
    return render(request, 'charts.html', {'performance_data': json.dumps(performance_data)})
def correlations_view(request):
    # Logika widoku dla Correlations
    return render(request, 'correlations.html')
     
def home(request):
    return render(request, 'base.html')