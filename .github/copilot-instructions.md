# Copilot Instructions for Stock Screener App

## Project Overview

Django 4.2 stock screening application using **yfinance** for real-time Yahoo Finance data and **SQLite** for persistence. Single Django app (`screener`) with function-based views.

## Architecture

```
stockscreener/     # Django project settings
screener/          # Main app: models, views, templates
  management/commands/  # Custom django-admin commands
  templates/screener/   # HTML templates with inline CSS
```

**Data Flow**: User request → View fetches from yfinance API → Updates/queries `Stock` model → Renders template with context

## Key Patterns

### Stock Model (`screener/models.py`)
Single model storing stock metadata. All numeric fields are nullable (`null=True, blank=True`) to handle missing Yahoo Finance data gracefully.

### Views Pattern (`screener/views.py`)
- Use `yf.Ticker(symbol)` to fetch live data; always wrap in try/except
- Use `update_or_create()` when adding stocks to handle duplicates
- News summarization uses **Anthropic Claude API** via `settings.ANTHROPIC_API_KEY`

### Analysis View Calculations (`analysis()`)
The analysis view computes financial metrics using **numpy**:

**Performance & Risk Metrics:**
- **Returns**: `hist['Close'].pct_change()` for daily percentage changes
- **Volatility**: `returns.std() * np.sqrt(252) * 100` (annualized)
- **Sharpe Ratio**: `(annualized_return - 0.04) / volatility` (4% risk-free rate assumed)
- **Sortino Ratio**: Uses only negative returns for downside deviation
- **Calmar Ratio**: `annualized_return / max_drawdown`
- **VaR 95%**: `np.percentile(returns, 5) * 100`
- **Beta**: Covariance with S&P 500 / variance of S&P 500
- **Correlation Matrix**: Built by fetching history for all stocks in database, aligning dates, then computing pairwise correlations

**Technical Indicators:**
- **RSI (14-day)**: `100 - (100 / (1 + RS))` where RS = avg_gain / avg_loss
- **MACD**: EMA(12) - EMA(26) with signal line EMA(9)
- **Moving Averages**: SMA 20, 50, 200 with price position signals

**Fundamental Metrics (from yfinance):**
- ROE, ROA, Debt-to-Equity, Current Ratio, Free Cash Flow
- Revenue Growth, Profit Margin, Earnings Calendar

### Template Pattern
- All templates extend `base.html` using blocks: `{% block title %}`, `{% block content %}`
- Inline CSS in `base.html`; no external stylesheets
- Use Django messages framework for user feedback: `messages.success()`, `messages.error()`

## Commands

```bash
# Development server
python manage.py runserver

# Load sample stocks (10 popular tickers)
python manage.py load_sample_stocks

# Database migrations
python manage.py migrate
```

## Environment Variables

Configure in `.env` file (loaded via `python-dotenv`):
- `DJANGO_SECRET_KEY` - Required for production
- `DJANGO_DEBUG` - Set to `False` in production
- `ANTHROPIC_API_KEY` - Required for AI news summarization feature

## Adding New Features

### New View
1. Add function in `screener/views.py`
2. Add URL pattern in `screener/urls.py` with `app_name='screener'`
3. Create template in `screener/templates/screener/`

### New Stock Fields
1. Add field to `Stock` model (use `null=True, blank=True` for optional data)
2. Run `python manage.py makemigrations && python manage.py migrate`
3. Update `search_stock()` view to populate from `ticker.info`

### Management Commands
Place in `screener/management/commands/<command_name>.py` following `load_sample_stocks.py` pattern.

## External APIs

**yfinance**: No API key needed, but has rate limits. Always handle `ticker.info` returning incomplete data.

**Anthropic Claude**: Used in `summarize_news()` endpoint. Requires API key in environment.

## Code Conventions

- Stock symbols always uppercase: `symbol.upper()`
- **French is the preferred UI language** for user-facing text, error messages, and Claude prompts
- URL naming: `screener:view_name` (e.g., `screener:stock_detail`)
