import requests

def get_coin_data(coin_id: str) -> dict:
    """
    Pulls price, supply, volume from CoinGecko
    coin_id: 'zcash', 'bitcoin', 'ethereum', etc.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(f"Coin '{coin_id}' not found!")
    
    data = resp.json()
    return {
        "name": data["name"],
        "price": data["market_data"]["current_price"]["usd"],
        "circulating": data["market_data"]["circulating_supply"],
        "max_supply": data["market_data"].get("max_supply"),
        "total_supply": data["market_data"]["total_supply"],
        "volume_24h": data["market_data"]["total_volume"]["usd"]
    }