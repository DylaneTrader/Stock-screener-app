from django.contrib import admin
from .models import Stock

# Register your models here.

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'sector', 'current_price', 'market_cap', 'pe_ratio', 'last_updated']
    list_filter = ['sector', 'last_updated']
    search_fields = ['symbol', 'name', 'sector', 'industry']
    readonly_fields = ['last_updated']

