# Logs Directory

This directory stores application logs for debugging and monitoring.

## Log Files:
- `crypto_checker_YYYYMMDD.log` - Daily log files with analysis results
- `api_calls_YYYYMMDD.log` - API call logs for monitoring usage
- `errors_YYYYMMDD.log` - Error logs for debugging

## Log Levels:
- **DEBUG** - Detailed diagnostic information
- **INFO** - General information about program execution
- **WARNING** - Something unexpected happened but the program continues
- **ERROR** - A serious problem occurred

## Log Retention:
- Logs are kept for 30 days
- Large log files are rotated automatically
- Archive old logs to save disk space

## Log Analysis:
Use grep commands to analyze logs:
```bash
# Find all BUY recommendations
grep "Recommendation: BUY" crypto_checker_*.log

# Check for API errors
grep "ERROR" crypto_checker_*.log

# Monitor specific cryptocurrency
grep "Bitcoin" crypto_checker_*.log
```