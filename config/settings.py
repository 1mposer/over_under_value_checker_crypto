# Configuration settings for the Crypto Value Checker

# API Configuration
API_KEYS = {
    "coinmarketcap": "YOUR_COINMARKETCAP_API_KEY_HERE",
    "coingecko": "YOUR_COINGECKO_API_KEY_HERE",
    "cryptocompare": "YOUR_CRYPTOCOMPARE_API_KEY_HERE"
}

# API Endpoints
API_ENDPOINTS = {
    "coinmarketcap_price": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
    "coingecko_price": "https://api.coingecko.com/api/v3/simple/price",
    "cryptocompare_price": "https://min-api.cryptocompare.com/data/price"
}

# Analysis Parameters
ANALYSIS_CONFIG = {
    "market_cap_threshold": 100000000,  # $100M minimum market cap
    "volume_threshold": 1000000,        # $1M minimum 24h volume
    "price_change_weight": 0.3,         # 30% weight for price momentum
    "fundamentals_weight": 0.5,         # 50% weight for fundamentals
    "sentiment_weight": 0.2             # 20% weight for sentiment
}

# Decision Thresholds
DECISION_THRESHOLDS = {
    "buy_score": 75,     # Score above 75 = BUY
    "hold_score": 40,    # Score 40-75 = HOLD
    "avoid_score": 40    # Score below 40 = AVOID
}

# File Paths
PATHS = {
    "whitepapers": "./whitepapers/",
    "data_cache": "./data/cache/",
    "logs": "./logs/",
    "results": "./data/results/"
}