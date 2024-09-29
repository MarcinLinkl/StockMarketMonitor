from django.urls import path,include
from stock_tickers_handler import views
from .views import sector_performance_view
from django.views.generic import TemplateView
urlpatterns = [
    # path('', views.home, name='home'),  
    path('api/sector-performance/', sector_performance_view, name='sector_performance_api'),
    path('sector-performance/', TemplateView.as_view(template_name='sector_performance.html'), name='sector_performance'),
  
]
