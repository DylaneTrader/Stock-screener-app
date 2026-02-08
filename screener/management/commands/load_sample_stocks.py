from django.core.management.base import BaseCommand
from screener.models import Stock


class Command(BaseCommand):
    help = 'Loads sample stock data for testing purposes'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample stock data...')
        
        sample_stocks = [
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'market_cap': 3450000000000,
                'current_price': 185.50,
                'pe_ratio': 31.25,
                'dividend_yield': 0.45,
                'fifty_two_week_high': 199.62,
                'fifty_two_week_low': 164.08,
                'volume': 52000000,
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software',
                'market_cap': 3100000000000,
                'current_price': 425.80,
                'pe_ratio': 37.12,
                'dividend_yield': 0.71,
                'fifty_two_week_high': 468.35,
                'fifty_two_week_low': 362.90,
                'volume': 25000000,
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'sector': 'Communication Services',
                'industry': 'Internet Content & Information',
                'market_cap': 2180000000000,
                'current_price': 175.30,
                'pe_ratio': 28.50,
                'dividend_yield': None,
                'fifty_two_week_high': 191.75,
                'fifty_two_week_low': 130.15,
                'volume': 28000000,
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla, Inc.',
                'sector': 'Consumer Cyclical',
                'industry': 'Auto Manufacturers',
                'market_cap': 890000000000,
                'current_price': 245.75,
                'pe_ratio': 75.20,
                'dividend_yield': None,
                'fifty_two_week_high': 299.29,
                'fifty_two_week_low': 138.80,
                'volume': 120000000,
            },
            {
                'symbol': 'AMZN',
                'name': 'Amazon.com, Inc.',
                'sector': 'Consumer Cyclical',
                'industry': 'Internet Retail',
                'market_cap': 1940000000000,
                'current_price': 188.40,
                'pe_ratio': 68.35,
                'dividend_yield': None,
                'fifty_two_week_high': 201.20,
                'fifty_two_week_low': 139.52,
                'volume': 48000000,
            },
            {
                'symbol': 'JPM',
                'name': 'JPMorgan Chase & Co.',
                'sector': 'Financial Services',
                'industry': 'Banks - Diversified',
                'market_cap': 620000000000,
                'current_price': 215.30,
                'pe_ratio': 12.45,
                'dividend_yield': 2.15,
                'fifty_two_week_high': 234.50,
                'fifty_two_week_low': 167.10,
                'volume': 11000000,
            },
            {
                'symbol': 'JNJ',
                'name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'industry': 'Drug Manufacturers',
                'market_cap': 410000000000,
                'current_price': 165.20,
                'pe_ratio': 22.80,
                'dividend_yield': 2.90,
                'fifty_two_week_high': 179.92,
                'fifty_two_week_low': 147.15,
                'volume': 7500000,
            },
            {
                'symbol': 'V',
                'name': 'Visa Inc.',
                'sector': 'Financial Services',
                'industry': 'Credit Services',
                'market_cap': 585000000000,
                'current_price': 295.60,
                'pe_ratio': 33.40,
                'dividend_yield': 0.68,
                'fifty_two_week_high': 314.25,
                'fifty_two_week_low': 267.40,
                'volume': 6800000,
            },
            {
                'symbol': 'WMT',
                'name': 'Walmart Inc.',
                'sector': 'Consumer Defensive',
                'industry': 'Discount Stores',
                'market_cap': 485000000000,
                'current_price': 175.85,
                'pe_ratio': 35.50,
                'dividend_yield': 1.20,
                'fifty_two_week_high': 183.50,
                'fifty_two_week_low': 155.30,
                'volume': 8200000,
            },
            {
                'symbol': 'XOM',
                'name': 'Exxon Mobil Corporation',
                'sector': 'Energy',
                'industry': 'Oil & Gas Integrated',
                'market_cap': 450000000000,
                'current_price': 108.50,
                'pe_ratio': 11.20,
                'dividend_yield': 3.25,
                'fifty_two_week_high': 126.35,
                'fifty_two_week_low': 95.80,
                'volume': 19000000,
            },
        ]
        
        stocks_created = 0
        stocks_updated = 0
        
        for stock_data in sample_stocks:
            stock, created = Stock.objects.update_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            
            if created:
                stocks_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created stock: {stock.symbol} - {stock.name}')
                )
            else:
                stocks_updated += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated stock: {stock.symbol} - {stock.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded {stocks_created} new stocks and updated {stocks_updated} existing stocks.'
            )
        )
