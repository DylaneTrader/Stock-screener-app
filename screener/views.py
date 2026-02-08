from django.shortcuts import render
from django.contrib import messages
from .models import Stock
import yfinance as yf
from datetime import datetime

# Create your views here.

def home(request):
    """Home view with stock screener form"""
    context = {
        'title': 'Stock Screener',
        'stocks': None,
    }
    
    if request.method == 'POST':
        # Get filter criteria from form
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        min_market_cap = request.POST.get('min_market_cap')
        max_pe = request.POST.get('max_pe')
        sector = request.POST.get('sector')
        
        # Build query
        stocks = Stock.objects.all()
        
        if min_price:
            try:
                stocks = stocks.filter(current_price__gte=float(min_price))
            except ValueError:
                messages.error(request, 'Invalid minimum price value')
        
        if max_price:
            try:
                stocks = stocks.filter(current_price__lte=float(max_price))
            except ValueError:
                messages.error(request, 'Invalid maximum price value')
        
        if min_market_cap:
            try:
                stocks = stocks.filter(market_cap__gte=float(min_market_cap))
            except ValueError:
                messages.error(request, 'Invalid minimum market cap value')
        
        if max_pe:
            try:
                stocks = stocks.filter(pe_ratio__lte=float(max_pe))
            except ValueError:
                messages.error(request, 'Invalid maximum P/E ratio value')
        
        if sector and sector != 'all':
            stocks = stocks.filter(sector__icontains=sector)
        
        context['stocks'] = stocks
        context['filter_applied'] = True
    
    return render(request, 'screener/home.html', context)

def stock_detail(request, symbol):
    """View for detailed stock information"""
    try:
        stock = Stock.objects.get(symbol=symbol.upper())
        
        info = None
        hist = None
        
        # Try to fetch live data from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get historical data for chart
            hist = ticker.history(period="1mo")
        except Exception as e:
            # If Yahoo Finance API fails, just show database data
            messages.warning(request, 'Unable to fetch live data. Showing stored data.')
        
        context = {
            'stock': stock,
            'info': info,
            'history': hist.to_dict() if hist is not None and not hist.empty else None,
        }
        
        return render(request, 'screener/stock_detail.html', context)
    except Stock.DoesNotExist:
        messages.error(request, f'Stock {symbol} not found in database')
        return render(request, 'screener/home.html', {'title': 'Stock Screener'})

def search_stock(request):
    """Search for a stock and add it to the database"""
    if request.method == 'POST':
        symbol = request.POST.get('symbol', '').upper().strip()
        
        if not symbol:
            messages.error(request, 'Please enter a stock symbol')
            return render(request, 'screener/search.html')
        
        try:
            # Fetch stock data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if valid stock
            if 'symbol' not in info or info.get('regularMarketPrice') is None:
                messages.error(request, f'Stock symbol {symbol} not found or invalid')
                return render(request, 'screener/search.html')
            
            # Create or update stock in database
            stock, created = Stock.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'name': info.get('longName', symbol),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'market_cap': info.get('marketCap'),
                    'current_price': info.get('regularMarketPrice') or info.get('currentPrice'),
                    'pe_ratio': info.get('trailingPE'),
                    'dividend_yield': info.get('dividendYield'),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                    'volume': info.get('volume'),
                }
            )
            
            if created:
                messages.success(request, f'Stock {symbol} added successfully!')
            else:
                messages.info(request, f'Stock {symbol} updated successfully!')
            
            return render(request, 'screener/search.html', {'stock': stock})
            
        except Exception as e:
            messages.error(request, f'Error fetching stock data: {str(e)}')
            return render(request, 'screener/search.html')
    
    return render(request, 'screener/search.html')

def all_stocks(request):
    """View to display all stocks in database"""
    stocks = Stock.objects.all()
    context = {
        'stocks': stocks,
        'title': 'All Stocks',
    }
    return render(request, 'screener/all_stocks.html', context)

