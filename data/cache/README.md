# Data Cache Directory

This directory stores cached API responses to reduce API calls and improve performance.

## Structure:
- `market_data/` - Cached market data responses
- `historical/` - Cached historical price data
- `metadata/` - Cached cryptocurrency metadata

## Cache Files:
Cache files are named using the pattern: `{crypto_name}_{timestamp}.json`

## Cache Expiry:
- Market data: 5 minutes
- Historical data: 1 hour
- Metadata: 24 hours