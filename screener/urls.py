from django.urls import path
from . import views

app_name = 'screener'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_stock, name='search'),
    path('all/', views.all_stocks, name='all_stocks'),
    path('analysis/', views.analysis, name='analysis'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('api/summarize-news/<str:symbol>/', views.summarize_news, name='summarize_news'),
]
