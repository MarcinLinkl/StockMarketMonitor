from django.urls import path,include
from stock_tickers_handler import views
from django.views.generic import TemplateView
from .views import indexes_view, search_view, charts_view, sectors_view, correlations_view,home
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [

    path('', home, name='home'),
    path('indexes/', indexes_view, name='indexes'),
    path('search/', search_view, name='search'),
    path('charts/', charts_view, name='charts'),
    path('sectors/', sectors_view, name='sectors'),
    path('correlations/', correlations_view, name='correlations'),

]+ debug_toolbar_urls()

