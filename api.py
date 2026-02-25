import requests
import json

def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if coin_id in data:
            price = data[coin_id]['usd']
            change_24h = data[coin_id].get('usd_24h_change', 0)
            return price, change_24h
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None, None

        
        
    