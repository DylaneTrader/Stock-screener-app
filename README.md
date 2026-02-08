# Stock Screener App

A Django-based stock screening application that uses the Yahoo Finance API to fetch and filter stock data based on various criteria.

## Features

- 🔍 **Stock Screening**: Filter stocks by price, market cap, P/E ratio, and sector
- 📊 **Real-time Data**: Fetches live stock data from Yahoo Finance API
- 📈 **Stock Details**: View detailed information for individual stocks
- ➕ **Add Stocks**: Search and add stocks to your database
- 🗂️ **Stock Database**: Store and manage your stock portfolio
- 🎨 **Modern UI**: Clean, responsive interface with gradient design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DylaneTrader/Stock-screener-app.git
cd Stock-screener-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

5. Open your browser and navigate to: `http://127.0.0.1:8000/`

## Usage

### Adding Stocks

1. Click on "Add Stock" in the navigation menu
2. Enter a valid stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
3. Click "Add Stock" to fetch data from Yahoo Finance and add to database

### Screening Stocks

1. Go to the Home page
2. Set your filter criteria:
   - Minimum/Maximum Price
   - Minimum Market Cap
   - Maximum P/E Ratio
   - Sector
3. Click "Screen Stocks" to see matching results

### Viewing Stock Details

- Click on "View Details" next to any stock in the results
- See comprehensive information including price, market cap, P/E ratio, dividend yield, 52-week highs/lows, and more

## Technologies Used

- **Backend**: Django 4.2
- **Data Source**: Yahoo Finance API (via yfinance library)
- **Database**: SQLite (default, can be changed in settings)
- **Frontend**: HTML, CSS (with inline styling)

## Project Structure

```
Stock-screener-app/
├── screener/               # Main app
│   ├── models.py          # Stock model definition
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   ├── admin.py           # Django admin configuration
│   └── templates/         # HTML templates
│       └── screener/
│           ├── base.html
│           ├── home.html
│           ├── search.html
│           ├── all_stocks.html
│           └── stock_detail.html
├── stockscreener/         # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
```

## API Limitations

This app uses the Yahoo Finance API through the `yfinance` library. Please note:
- Data is fetched in real-time and may have delays
- Some stocks might not have all data fields available
- Excessive requests might be rate-limited

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
