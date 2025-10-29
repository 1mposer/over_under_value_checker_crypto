# Analysis Results Directory

This directory stores the results of crypto analysis runs.

## File Format:
Results are stored as JSON files with the following structure:

```json
{
    "crypto_name": "Bitcoin",
    "timestamp": "2025-10-28T12:00:00Z",
    "market_data": {
        "price": 45000.0,
        "market_cap": 850000000000,
        "volume_24h": 25000000000
    },
    "analysis_scores": {
        "technical_score": 75,
        "fundamental_score": 80,
        "sentiment_score": 70,
        "overall_score": 76
    },
    "recommendation": "BUY",
    "reasoning": [
        "Strong technical indicators",
        "Solid fundamentals with growing adoption",
        "Positive market sentiment"
    ]
}
```

## File Naming:
Files are named: `{crypto_name}_{YYYYMMDD_HHMMSS}_analysis.json`