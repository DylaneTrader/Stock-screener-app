from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_GET
from .models import Stock
import yfinance as yf
from datetime import datetime, timezone
import numpy as np
import json

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


def analysis(request):
    """Data analysis view with performance, correlation, and risk metrics"""
    all_stocks = Stock.objects.all()
    symbol = request.GET.get('symbol', '')
    
    context = {
        'all_stocks': all_stocks,
        'stock': None,
    }
    
    if symbol:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            context['stock'] = stock
            
            # Fetch historical data
            period = request.GET.get('period', '1y')
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist is not None and not hist.empty:
                # Calculate price data for charts
                dates = [d.strftime('%Y-%m-%d') for d in hist.index]
                prices = hist['Close'].tolist()
                
                # Calculate returns
                returns = hist['Close'].pct_change().dropna()
                
                # Calculate drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.cummax()
                drawdown = ((cumulative - running_max) / running_max * 100).tolist()
                
                max_drawdown = min(drawdown) if drawdown else 0
                current_drawdown = drawdown[-1] if drawdown else 0
                
                # Performance metrics
                total_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                trading_days = len(returns)
                annualized_return = ((1 + total_return/100) ** (252/trading_days) - 1) * 100 if trading_days > 0 else 0
                
                # Risk metrics
                volatility = returns.std() * np.sqrt(252) * 100
                
                # Sharpe Ratio (assuming risk-free rate of 4%)
                risk_free_rate = 0.04
                excess_return = annualized_return/100 - risk_free_rate
                sharpe_ratio = excess_return / (volatility/100) if volatility > 0 else 0
                
                # Sortino Ratio
                negative_returns = returns[returns < 0]
                downside_std = negative_returns.std() * np.sqrt(252)
                sortino_ratio = excess_return / downside_std if downside_std > 0 else 0
                
                # Value at Risk (95%)
                var_95 = np.percentile(returns, 5) * 100
                
                # Benchmark data (S&P 500)
                benchmark_ticker = yf.Ticker("^GSPC")
                benchmark_hist = benchmark_ticker.history(period=period)
                
                benchmark_return = 0
                benchmark_normalized = []
                stock_normalized = []
                
                if benchmark_hist is not None and not benchmark_hist.empty:
                    benchmark_return = ((benchmark_hist['Close'].iloc[-1] / benchmark_hist['Close'].iloc[0]) - 1) * 100
                    
                    # Normalize for comparison chart
                    stock_normalized = ((hist['Close'] / hist['Close'].iloc[0] - 1) * 100).tolist()
                    benchmark_normalized = ((benchmark_hist['Close'] / benchmark_hist['Close'].iloc[0] - 1) * 100).tolist()
                    
                    # Calculate correlation and beta with S&P 500
                    benchmark_returns = benchmark_hist['Close'].pct_change().dropna()
                    
                    # Align the data
                    common_dates = returns.index.intersection(benchmark_returns.index)
                    if len(common_dates) > 10:
                        aligned_returns = returns.loc[common_dates]
                        aligned_benchmark = benchmark_returns.loc[common_dates]
                        
                        corr_sp500 = aligned_returns.corr(aligned_benchmark)
                        covariance = aligned_returns.cov(aligned_benchmark)
                        variance = aligned_benchmark.var()
                        beta = covariance / variance if variance > 0 else 0
                    else:
                        corr_sp500 = None
                        beta = None
                else:
                    corr_sp500 = None
                    beta = None
                
                # NASDAQ correlation
                nasdaq_ticker = yf.Ticker("^IXIC")
                nasdaq_hist = nasdaq_ticker.history(period=period)
                corr_nasdaq = None
                
                if nasdaq_hist is not None and not nasdaq_hist.empty:
                    nasdaq_returns = nasdaq_hist['Close'].pct_change().dropna()
                    common_dates = returns.index.intersection(nasdaq_returns.index)
                    if len(common_dates) > 10:
                        aligned_returns = returns.loc[common_dates]
                        aligned_nasdaq = nasdaq_returns.loc[common_dates]
                        corr_nasdaq = aligned_returns.corr(aligned_nasdaq)
                
                # Get additional info from Yahoo Finance
                info = ticker.info
                pe_ratio = info.get('trailingPE')
                pb_ratio = info.get('priceToBook')
                ev_ebitda = info.get('enterpriseToEbitda')
                peg_ratio = info.get('pegRatio')
                dividend_yield = info.get('dividendYield', 0)
                if dividend_yield:
                    dividend_yield = dividend_yield * 100
                
                # Additional Fundamental Metrics
                roe = info.get('returnOnEquity')
                if roe:
                    roe = roe * 100  # Convert to percentage
                roa = info.get('returnOnAssets')
                if roa:
                    roa = roa * 100  # Convert to percentage
                debt_to_equity = info.get('debtToEquity')
                current_ratio = info.get('currentRatio')
                free_cash_flow = info.get('freeCashflow')
                revenue_growth = info.get('revenueGrowth')
                if revenue_growth:
                    revenue_growth = revenue_growth * 100
                profit_margin = info.get('profitMargins')
                if profit_margin:
                    profit_margin = profit_margin * 100
                
                # Technical Indicators
                closes = hist['Close']
                
                # Moving Averages - full series for charts
                sma_20_series = closes.rolling(window=20).mean()
                sma_50_series = closes.rolling(window=50).mean()
                sma_200_series = closes.rolling(window=200).mean()
                
                sma_20 = sma_20_series.iloc[-1] if len(closes) >= 20 else None
                sma_50 = sma_50_series.iloc[-1] if len(closes) >= 50 else None
                sma_200 = sma_200_series.iloc[-1] if len(closes) >= 200 else None
                current_close = closes.iloc[-1]
                
                # Price vs Moving Averages signals
                above_sma_20 = current_close > sma_20 if sma_20 else None
                above_sma_50 = current_close > sma_50 if sma_50 else None
                above_sma_200 = current_close > sma_200 if sma_200 else None
                
                # RSI (14-day) - full series for chart
                delta = closes.diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_value = rsi.iloc[-1] if len(rsi) >= 14 else None
                
                # RSI interpretation
                rsi_signal = None
                if rsi_value:
                    if rsi_value > 70:
                        rsi_signal = 'Suracheté'
                    elif rsi_value < 30:
                        rsi_signal = 'Survendu'
                    else:
                        rsi_signal = 'Neutre'
                
                # MACD (12, 26, 9) - full series for chart
                ema_12 = closes.ewm(span=12, adjust=False).mean()
                ema_26 = closes.ewm(span=26, adjust=False).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_histogram = macd_line - signal_line
                
                macd_value = macd_line.iloc[-1] if len(macd_line) >= 26 else None
                macd_signal = signal_line.iloc[-1] if len(signal_line) >= 26 else None
                macd_hist_value = macd_histogram.iloc[-1] if len(macd_histogram) >= 26 else None
                macd_crossover = 'Haussier' if macd_value and macd_signal and macd_value > macd_signal else 'Baissier' if macd_value and macd_signal else None
                
                # Prepare technical indicator chart data
                # Replace NaN with None for JSON serialization
                def clean_series(s):
                    return [None if np.isnan(x) else round(x, 2) for x in s.tolist()]
                
                technical_chart_data = {
                    'dates': dates,
                    'prices': prices,
                    'sma_20': clean_series(sma_20_series),
                    'sma_50': clean_series(sma_50_series),
                    'sma_200': clean_series(sma_200_series),
                }
                
                rsi_chart_data = {
                    'dates': dates,
                    'rsi': clean_series(rsi),
                }
                
                macd_chart_data = {
                    'dates': dates,
                    'macd_line': clean_series(macd_line),
                    'signal_line': clean_series(signal_line),
                    'histogram': clean_series(macd_histogram),
                }
                
                # Calmar Ratio (annualized return / max drawdown)
                calmar_ratio = abs(annualized_return / max_drawdown) if max_drawdown != 0 else None
                
                # Earnings Calendar
                try:
                    calendar = ticker.calendar
                    if calendar is not None and not calendar.empty:
                        earnings_date = calendar.get('Earnings Date')
                        if earnings_date is not None:
                            if isinstance(earnings_date, list) and len(earnings_date) > 0:
                                next_earnings = earnings_date[0].strftime('%d/%m/%Y') if hasattr(earnings_date[0], 'strftime') else str(earnings_date[0])
                            else:
                                next_earnings = str(earnings_date)
                        else:
                            next_earnings = None
                    else:
                        next_earnings = None
                except:
                    next_earnings = None
                
                # Correlation matrix with ALL stocks in database
                correlation_matrix = {}
                correlation_symbols = []
                
                all_db_stocks = Stock.objects.all()
                if all_db_stocks.count() > 1:
                    stock_returns_dict = {symbol.upper(): returns}
                    correlation_symbols = [symbol.upper()]
                    
                    for other in all_db_stocks:
                        if other.symbol.upper() != symbol.upper():
                            try:
                                other_ticker = yf.Ticker(other.symbol)
                                other_hist = other_ticker.history(period=period)
                                if other_hist is not None and not other_hist.empty:
                                    other_returns = other_hist['Close'].pct_change().dropna()
                                    stock_returns_dict[other.symbol] = other_returns
                                    correlation_symbols.append(other.symbol)
                            except:
                                pass
                    
                    # Build correlation matrix
                    for sym1 in correlation_symbols:
                        correlation_matrix[sym1] = {}
                        for sym2 in correlation_symbols:
                            if sym1 in stock_returns_dict and sym2 in stock_returns_dict:
                                common_idx = stock_returns_dict[sym1].index.intersection(stock_returns_dict[sym2].index)
                                if len(common_idx) > 10:
                                    corr = stock_returns_dict[sym1].loc[common_idx].corr(stock_returns_dict[sym2].loc[common_idx])
                                    correlation_matrix[sym1][sym2] = round(corr, 2)
                                else:
                                    correlation_matrix[sym1][sym2] = None
                            else:
                                correlation_matrix[sym1][sym2] = None
                
                # Prepare chart data
                context.update({
                    'current_period': period,
                    'price_data': json.dumps({
                        'dates': dates,
                        'prices': prices
                    }),
                    'drawdown_data': json.dumps({
                        'dates': dates[1:],
                        'values': drawdown
                    }),
                    'benchmark_data': json.dumps({
                        'dates': dates,
                        'stock': stock_normalized,
                        'benchmark': benchmark_normalized[:len(dates)]
                    }),
                    'max_drawdown': max_drawdown,
                    'current_drawdown': current_drawdown,
                    'stock_return': total_return,
                    'benchmark_return': benchmark_return,
                    'alpha': total_return - benchmark_return,
                    'annualized_return': annualized_return,
                    'total_return': total_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'sortino_ratio': sortino_ratio,
                    'var_95': var_95,
                    'corr_sp500': corr_sp500,
                    'corr_nasdaq': corr_nasdaq,
                    'beta': beta,
                    'pe_ratio': pe_ratio,
                    'pb_ratio': pb_ratio,
                    'ev_ebitda': ev_ebitda,
                    'peg_ratio': peg_ratio,
                    'dividend_yield': dividend_yield,
                    'correlation_matrix': correlation_matrix,
                    'correlation_symbols': correlation_symbols,
                    # New Fundamental Metrics
                    'roe': roe,
                    'roa': roa,
                    'debt_to_equity': debt_to_equity,
                    'current_ratio': current_ratio,
                    'free_cash_flow': free_cash_flow,
                    'revenue_growth': revenue_growth,
                    'profit_margin': profit_margin,
                    # Technical Indicators
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'sma_200': sma_200,
                    'above_sma_20': above_sma_20,
                    'above_sma_50': above_sma_50,
                    'above_sma_200': above_sma_200,
                    'rsi_value': rsi_value,
                    'rsi_signal': rsi_signal,
                    'macd_value': macd_value,
                    'macd_signal': macd_signal,
                    'macd_hist_value': macd_hist_value,
                    'macd_crossover': macd_crossover,
                    # Technical Chart Data
                    'technical_chart_data': json.dumps(technical_chart_data),
                    'rsi_chart_data': json.dumps(rsi_chart_data),
                    'macd_chart_data': json.dumps(macd_chart_data),
                    # Additional Risk Metric
                    'calmar_ratio': calmar_ratio,
                    # Earnings
                    'next_earnings': next_earnings,
                })
                
                # Fetch news for the stock
                try:
                    news = ticker.news
                    news_list = []
                    if news:
                        for item in news[:10]:  # Limit to 10 news items
                            # Handle new yfinance structure where news is nested under 'content'
                            content = item.get('content', item)
                            
                            # Parse publish time
                            pub_date = content.get('pubDate', '')
                            if pub_date:
                                try:
                                    from dateutil import parser
                                    dt = parser.parse(pub_date)
                                    published_date = dt.strftime('%d/%m/%Y %H:%M')
                                except:
                                    published_date = pub_date[:16] if len(pub_date) > 16 else pub_date
                            else:
                                # Fallback to old structure
                                publish_time = item.get('providerPublishTime', 0)
                                if publish_time:
                                    published_date = datetime.fromtimestamp(publish_time, tz=timezone.utc).strftime('%d/%m/%Y %H:%M')
                                else:
                                    published_date = ''
                            
                            # Get thumbnail - handle new structure
                            thumbnail = None
                            thumb_data = content.get('thumbnail', item.get('thumbnail'))
                            if thumb_data:
                                resolutions = thumb_data.get('resolutions', [])
                                if resolutions:
                                    thumbnail = resolutions[0].get('url')
                            
                            # Get provider/publisher
                            provider = content.get('provider', {})
                            publisher = provider.get('displayName', item.get('publisher', ''))
                            
                            # Get link - try clickThroughUrl first, then canonicalUrl
                            link = ''
                            click_url = content.get('clickThroughUrl', {})
                            if click_url:
                                link = click_url.get('url', '')
                            if not link:
                                canonical_url = content.get('canonicalUrl', {})
                                if canonical_url:
                                    link = canonical_url.get('url', '')
                            if not link:
                                link = item.get('link', '')
                            
                            news_list.append({
                                'title': content.get('title', item.get('title', '')),
                                'publisher': publisher,
                                'link': link,
                                'published_date': published_date,
                                'type': content.get('contentType', item.get('type', '')),
                                'thumbnail': thumbnail,
                                'summary': content.get('summary', item.get('summary', '')),
                            })
                    context['news_list'] = news_list
                except Exception as e:
                    context['news_list'] = []
            else:
                messages.warning(request, 'Impossible de récupérer les données historiques.')
                
        except Stock.DoesNotExist:
            messages.error(request, f'Action {symbol} non trouvée.')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'analyse: {str(e)}')
    
    return render(request, 'screener/analysis.html', context)


@require_GET
def summarize_news(request, symbol):
    """API endpoint to summarize news using Claude AI"""
    
    # Check if API key is configured
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return JsonResponse({
            'success': False,
            'error': 'Clé API Anthropic non configurée. Ajoutez ANTHROPIC_API_KEY dans vos variables d\'environnement.'
        }, status=400)
    
    try:
        # Fetch news from yfinance
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return JsonResponse({
                'success': False,
                'error': 'Aucune actualité disponible pour cette action.'
            }, status=404)
        
        # Prepare news content for summarization
        news_texts = []
        for item in news[:10]:
            content = item.get('content', item)
            title = content.get('title', item.get('title', ''))
            summary = content.get('summary', item.get('summary', ''))
            provider = content.get('provider', {})
            publisher = provider.get('displayName', item.get('publisher', ''))
            
            news_texts.append(f"**{title}** ({publisher})\n{summary}")
        
        combined_news = "\n\n".join(news_texts)
        
        # Get stock info
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            stock_name = stock.name
        except Stock.DoesNotExist:
            stock_name = symbol
        
        # Call Claude API
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyse et résume les actualités suivantes concernant l'action {stock_name} ({symbol}).

Fournis un résumé structuré en français avec :
1. **Tendance générale** : Sentiment global des nouvelles (positif/négatif/neutre)
2. **Points clés** : Les 3-5 informations les plus importantes
3. **Impact potentiel** : Comment ces nouvelles pourraient affecter le cours de l'action

Actualités :
{combined_news}

Réponds de manière concise et professionnelle."""
                }
            ]
        )
        
        summary = message.content[0].text
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'symbol': symbol
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération du résumé : {str(e)}'
        }, status=500)
