from django.urls import path,include
from stock_tickers_handler import views

urlpatterns = [
    path('', views.home, name='home'),  
]
