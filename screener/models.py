from django.db import models

# Create your models here.

class Stock(models.Model):
    """Model to store stock information"""
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    market_cap = models.FloatField(null=True, blank=True)
    current_price = models.FloatField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    fifty_two_week_high = models.FloatField(null=True, blank=True)
    fifty_two_week_low = models.FloatField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

