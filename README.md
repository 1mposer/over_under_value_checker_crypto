# Crypto Value Checker

A Python-based cryptocurrency analysis tool that performs quick undervaluation assessments and provides investment recommendations.

## Purpose

This tool analyzes cryptocurrencies using a "60-Second Undervalued Test" algorithm that:
- Fetches real-time market data from multiple APIs
- Analyzes cryptocurrency whitepapers for fundamental insights
- Applies technical analysis indicators
- Generates BUY/HOLD/AVOID recommendations

## Quick Start

### Prerequisites
- Python 3.8 or higher
- API keys for cryptocurrency data sources (see Setup section)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.template .env
# Edit .env file with your API keys
```

### Usage
```bash
# Analyze a cryptocurrency
python main.py Bitcoin
python main.py Zcash
python main.py Ethereum
```

## How It Works

### 1. Data Collection
- **Market Data**: Price, volume, market cap, supply metrics
- **Historical Data**: Price trends and momentum analysis
- **Whitepaper Analysis**: Technology assessment and fundamentals

### 2. Analysis Components
- **Market Metrics (40%)**: Market cap analysis, volume trends, liquidity
- **Fundamentals (35%)**: Technology innovation, use case strength, team quality
- **Technical Analysis (15%)**: Price momentum, support/resistance, RSI
- **Sentiment (10%)**: Market sentiment indicators and social signals

### 3. Scoring System
- **75+ Score**: **BUY** - Strong undervaluation signals
- **40-74 Score**: **HOLD** - Fair value, monitor for changes
- **<40 Score**: **AVOID** - Overvalued or high risk

## Project Structure

```
crypto-value-checker/
├── main.py                 # Main entry point
├── config/
│   └── settings.py         # Configuration and API settings
├── data/
│   ├── fetcher.py          # Market data fetching
│   ├── cache/              # Cached API responses
│   └── results/            # Analysis results storage
├── whitepapers/
│   ├── analyzer.py         # Whitepaper analysis module
│   └── README.md           # Whitepaper storage guide
├── analysis/
│   ├── undervalued_test.py # Core 60-second test algorithm
│   └── technical.py        # Technical analysis indicators
├── utils/
│   ├── helpers.py          # Utility functions
│   └── logger.py           # Logging configuration
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
└── .env.template          # Environment variables template
```

## Setup

### 1. API Keys Required
Get free API keys from:
- **CoinMarketCap**: https://coinmarketcap.com/api/
- **CoinGecko**: https://coingecko.com/en/api
- **CryptoCompare**: https://cryptocompare.com/api/

### 2. Environment Configuration
Copy `.env.template` to `.env` and add your API keys:
```bash
COINMARKETCAP_API_KEY=your_api_key_here
COINGECKO_API_KEY=your_api_key_here
CRYPTOCOMPARE_API_KEY=your_api_key_here
```

### 3. Whitepaper Setup
Add cryptocurrency whitepapers to the `whitepapers/` directory:
- Download whitepapers in PDF or text format
- Name files as: `{crypto_name}_whitepaper.{ext}`
- Example: `bitcoin_whitepaper.pdf`, `zcash_whitepaper.txt`

## Analysis Output

Example output for Bitcoin analysis:
```
Analyzing Bitcoin...
├── Market Data: ✓ Fetched current price and volume
├── Whitepaper: ✓ Analyzed technology and use case
├── Technical: ✓ Calculated momentum indicators
└── Sentiment: ✓ Assessed market sentiment

Overall Score: 76/100
Recommendation: BUY

Reasoning:
• Strong technical indicators with bullish momentum
• Solid fundamentals with growing institutional adoption
• Market sentiment remains positive despite volatility
• Trading above key support levels with high volume
```

## Disclaimer

This tool is for educational and research purposes only. Cryptocurrency investments are highly volatile and risky. Always do your own research and consult with financial advisors before making investment decisions.
