import yfinance as yf
from datetime import datetime

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if not current_price:
            return None, None, None
        
        previous_close = info.get('previousClose', current_price)
        change_percent = ((current_price - previous_close) / previous_close) * 100
        
        market_state = info.get('marketState', 'REGULAR')
        
        return current_price, change_percent, market_state
    
    except Exception as e:
        print(f"Error fetching stock: {e}")
        return None, None, None