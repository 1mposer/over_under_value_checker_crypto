# === ENHANCED UNDERVALUED CRYPTO CHECKER  ===
import os, re, json, time, logging, random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, Optional, Tuple, Any
import requests
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Endpoints
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
MESSARI_BASE = "https://api.messari.io"
DEFILLAMA_API = "https://api.llama.fi"
ZEC_HUB_DASHBOARD = "https://zechub.wiki/dashboard"
ZKP_BABY_DASHBOARD = "https://zkp.baby"

# User-Agent for better scraping success
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Enhanced SLUG_MAP with comprehensive mapping
SLUG_MAP = {
    'bitcoin': {
        'symbol': 'BTC',
        'coingecko_id': 'bitcoin',
        'messari_slug': 'bitcoin',
        'defillama_slug': None,
        'cmc_id': 1,
        'has_special_metrics': False
    },
    'ethereum': {
        'symbol': 'ETH',
        'coingecko_id': 'ethereum',
        'messari_slug': 'ethereum',
        'defillama_slug': 'Ethereum',
        'cmc_id': 1027,
        'has_special_metrics': False
    },
    'zcash': {
        'symbol': 'ZEC',
        'coingecko_id': 'zcash',
        'messari_slug': 'zcash',
        'defillama_slug': None,
        'cmc_id': 1437,
        'has_special_metrics': True,
        'shielded_pool_source': 'zechub'
    },
    'ripple': {
        'symbol': 'XRP',
        'coingecko_id': 'ripple',
        'messari_slug': 'xrp',
        'defillama_slug': None,
        'cmc_id': 52,
        'has_special_metrics': False
    },
    'cardano': {
        'symbol': 'ADA',
        'coingecko_id': 'cardano',
        'messari_slug': 'cardano',
        'defillama_slug': 'Cardano',
        'cmc_id': 2010,
        'has_special_metrics': False
    },
    'solana': {
        'symbol': 'SOL',
        'coingecko_id': 'solana',
        'messari_slug': 'solana',
        'defillama_slug': 'Solana',
        'cmc_id': 5426,
        'has_special_metrics': False
    },
    'polkadot': {
        'symbol': 'DOT',
        'coingecko_id': 'polkadot',
        'messari_slug': 'polkadot',
        'defillama_slug': 'Polkadot',
        'cmc_id': 6636,
        'has_special_metrics': False
    }
}

# Reverse lookup dictionary for symbols
SYMBOL_TO_SLUG = {v['symbol']: k for k, v in SLUG_MAP.items()}

def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """Safely convert to Decimal with default fallback"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            # Remove commas from number strings
            value = value.replace(',', '')
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logger.warning(f"Could not convert {value} to Decimal, using default {default}")
        return default

def parse_number_from_text(text: str) -> Optional[float]:
    """Extract number from text with various formats"""
    if not text:
        return None
    
    # Remove all spaces and normalize separators
    text = text.replace(' ', '').replace('−', '-')
    
    # Try different patterns
    patterns = [
        r'([\d,]+(?:\.\d+)?)',  # Standard number with commas
        r'([\d\.]+)',            # Number with dots
        r'(\d+)',                # Just digits
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                # Remove commas and convert
                num_str = match.group(1).replace(',', '')
                return float(num_str)
            except ValueError:
                continue
    
    return None

class RateLimiter:
    """Rate limiter with jitter and exponential backoff"""
    def __init__(self, max_requests_per_minute=20):
        self.max_requests = max_requests_per_minute
        self.request_times = []
        self.backoff_until = None
        self.consecutive_429s = 0
    
    def wait_if_needed(self):
        """Wait if we've exceeded rate limit with jitter"""
        # Check if we're in backoff period
        if self.backoff_until and datetime.now() < self.backoff_until:
            wait_seconds = (self.backoff_until - datetime.now()).total_seconds()
            logger.info(f"In backoff period. Waiting {wait_seconds:.1f} seconds...")
            time.sleep(wait_seconds)
            return
        
        now = time.time()
        # Remove requests older than 60 seconds
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.max_requests:
            # Add jitter (0.5-1.5 seconds) to prevent synchronized bursts
            jitter = random.uniform(0.5, 1.5)
            sleep_time = 60 - (now - self.request_times[0]) + jitter
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds (with jitter)...")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def handle_429(self):
        """Handle 429 response with exponential backoff"""
        self.consecutive_429s += 1
        backoff_seconds = min(300, 30 * (2 ** (self.consecutive_429s - 1)))  # Max 5 minutes
        self.backoff_until = datetime.now() + timedelta(seconds=backoff_seconds)
        logger.warning(f"Got 429. Backing off for {backoff_seconds} seconds (attempt {self.consecutive_429s})")
    
    def reset_backoff(self):
        """Reset backoff on successful request"""
        if self.consecutive_429s > 0:
            self.consecutive_429s = 0
            self.backoff_until = None

class DataCache:
    """Enhanced cache with URL params awareness"""
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, key: str, params: Dict = None) -> str:
        """Generate cache key including params"""
        if params:
            # Sort params for consistent keys
            sorted_params = sorted(params.items())
            param_str = urlencode(sorted_params)
            return f"{key}_{param_str}"
        return key
    
    def get(self, key: str, params: Dict = None, max_age_hours: int = 24) -> Optional[Dict]:
        """Get cached data if it exists and isn't too old"""
        cache_key = self._get_cache_key(key, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check age
                cached_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cached_time < timedelta(hours=max_age_hours):
                    logger.debug(f"Cache hit for {cache_key}")
                    return data['data']
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Cache read error for {cache_key}: {e}")
        
        return None
    
    def set(self, key: str, data: Dict, params: Dict = None):
        """Cache data with timestamp"""
        cache_key = self._get_cache_key(key, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f)
        except (IOError, TypeError) as e:
            logger.warning(f"Cache write error for {cache_key}: {e}")

def make_request_with_retry(url: str, params: Dict = None, headers: Dict = None, 
                           max_retries: int = 3, timeout: int = 15) -> Optional[requests.Response]:
    """Make HTTP request with retries and proper error handling"""
    headers = headers or HEADERS
    
    for attempt in range(max_retries):
        # ALWAYS check rate limit first (fixes issue #2)
        rate_limiter.wait_if_needed()
        
        try:
            if attempt > 0:
                # Add delay between retries with exponential backoff
                time.sleep(2 ** attempt)
            
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 429:
                rate_limiter.handle_429()
                # Actually wait for the backoff period (fixes issue #1)
                rate_limiter.wait_if_needed()
                continue
            elif response.status_code >= 500:
                logger.warning(f"Server error {response.status_code} on attempt {attempt + 1}")
                continue
            
            rate_limiter.reset_backoff()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return None
    
    return None

# Initialize global instances
rate_limiter = RateLimiter(max_requests_per_minute=18)  # Conservative for free tier
cache = DataCache()

def normalize_coin_input(coin_input: str) -> str:
    """Normalize user input to standard slug"""
    coin_lower = coin_input.lower().strip()
    
    # Direct match in SLUG_MAP
    if coin_lower in SLUG_MAP:
        return coin_lower
    
    # Check if it's a symbol
    if coin_lower.upper() in SYMBOL_TO_SLUG:
        return SYMBOL_TO_SLUG[coin_lower.upper()]
    
    # Common aliases
    aliases = {
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'zec': 'zcash',
        'xrp': 'ripple',
        'ada': 'cardano',
        'sol': 'solana',
        'dot': 'polkadot'
    }
    
    if coin_lower in aliases:
        return aliases[coin_lower]
    
    # Default to input if not found
    logger.warning(f"Unknown coin: {coin_input}. Using as-is.")
    return coin_lower

def jget(obj, path, default=None):
    """Safe nested dictionary access"""
    cur = obj
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def get_coingecko(coin_slug: str) -> Dict:
    """Fetch market data from CoinGecko with enhanced error handling"""
    # Check if we have a mapping
    normalized = normalize_coin_input(coin_slug)
    if normalized in SLUG_MAP:
        coin_id = SLUG_MAP[normalized]['coingecko_id']
    else:
        coin_id = coin_slug
    
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    }
    
    # Check cache first
    cache_key = f"coingecko_{coin_id}"
    cached = cache.get(cache_key, params=params, max_age_hours=1)
    if cached:
        cached['source_url'] = f"{COINGECKO_BASE}/coins/{coin_id}"
        return cached
    
    rate_limiter.wait_if_needed()
    
    url = f"{COINGECKO_BASE}/coins/{coin_id}"
    response = make_request_with_retry(url, params=params)
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            
            result = {
                "name": data.get("name", "Unknown"),
                "symbol": data.get("symbol", "").upper(),
                "price_usd": safe_decimal(jget(data, "market_data.current_price.usd")),
                "circulating": safe_decimal(jget(data, "market_data.circulating_supply")),
                "max_supply": safe_decimal(jget(data, "market_data.max_supply")),
                "total_supply": safe_decimal(jget(data, "market_data.total_supply")),
                "coingecko_id": data.get("id", coin_id),
                "source_url": url
            }
            
            cache.set(cache_key, result, params=params)
            return result
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing CoinGecko response: {e}")
    
    raise Exception(f"Failed to fetch data from CoinGecko for {coin_id}")

def get_messari_issuance(coin_slug: str) -> Tuple[Optional[Decimal], str]:
    """Auto-fetch annual issuance from Messari with better 429 handling"""
    normalized = normalize_coin_input(coin_slug)
    if normalized in SLUG_MAP:
        messari_slug = SLUG_MAP[normalized].get('messari_slug', coin_slug)
    else:
        messari_slug = coin_slug
    
    # Check cache first
    cache_key = f"messari_issuance_{messari_slug}"
    cached = cache.get(cache_key, max_age_hours=24)
    if cached:
        return safe_decimal(cached['issuance']), cached['source']
    
    headers = {}
    if os.getenv("MESSARI_API_KEY"):
        headers["X-Messari-API-Key"] = os.environ["MESSARI_API_KEY"]
    
    # Don't call wait_if_needed here - make_request_with_retry handles it
    url = f"{MESSARI_BASE}/v1/assets/{messari_slug}/metrics"
    response = make_request_with_retry(url, headers=headers)
    
    # If we got 429, respect backoff and try ONE more time (fixes issue #3)
    if response is None or response.status_code == 429:
        logger.info("Messari unavailable, respecting backoff and trying once more...")
        time.sleep(5)  # Grace period
        response = make_request_with_retry(url, headers=headers, max_retries=1)
    
    if response and response.status_code == 200:
        try:
            data = response.json().get("data", {})
            
            annual_issuance = None
            source = None
            
            # Try different supply metrics
            y2y_realized = jget(data, "supply.y2y_realized_inflation_rate")
            if y2y_realized is not None:
                circ_supply = safe_decimal(jget(data, "supply.circulating"))
                if circ_supply > 0:
                    annual_issuance = safe_decimal(y2y_realized) * circ_supply
                    source = f"Messari API ({url}) - y2y realized inflation"
            
            if not annual_issuance:
                annual_rate = jget(data, "supply.annual_inflation_percent")
                if annual_rate is not None:
                    circ_supply = safe_decimal(jget(data, "supply.circulating"))
                    if circ_supply > 0:
                        annual_issuance = (safe_decimal(annual_rate) / 100) * circ_supply
                        source = f"Messari API ({url}) - annual inflation rate"
            
            if annual_issuance:
                cache.set(cache_key, {
                    'issuance': str(annual_issuance),
                    'source': source
                })
                return annual_issuance, source
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing Messari response: {e}")
    elif response and response.status_code == 429:
        logger.warning("Messari rate limit hit - will use manual entry or cache")
    
    return None, None

def zcash_shielded_value_locked_usd(price_usd: Decimal) -> Tuple[Optional[Decimal], Optional[str]]:
    """Get Zcash shielded pool value with robust scraping"""
    
    # Try ZKP.baby first
    logger.debug("Attempting ZKP.baby scraping...")
    response = make_request_with_retry(ZKP_BABY_DASHBOARD, headers=HEADERS, max_retries=2)
    
    if response and response.status_code == 200:
        html = response.text
        
        # Multiple regex patterns for resilience
        patterns = [
            # Total shielded with various formats
            (r'Total\s*Shielded\s*(?:Value)?\s*[·:\-]?\s*([\d,.\s]+)\s*ZEC', 'total'),
            (r'([\d,.\s]+)\s*ZEC\s*(?:Total\s*)?Shielded', 'total'),
            # Individual pools
            (r'Sapling\s*Pool\s*[·:\-]?\s*([\d,.\s]+)\s*ZEC', 'sapling'),
            (r'Orchard\s*Pool\s*[·:\-]?\s*([\d,.\s]+)\s*ZEC', 'orchard'),
        ]
        
        values = {}
        for pattern, pool_type in patterns:
            match = re.search(pattern, html, re.I | re.S)
            if match:
                value = parse_number_from_text(match.group(1))
                if value:
                    values[pool_type] = value
        
        # Use total if found, otherwise sum individual pools
        if 'total' in values:
            total_shielded = safe_decimal(values['total'])
            if total_shielded > 0:
                return total_shielded * price_usd, f"ZKP.baby ({ZKP_BABY_DASHBOARD}) - Total Shielded"
        
        if 'sapling' in values or 'orchard' in values:
            total = safe_decimal(values.get('sapling', 0)) + safe_decimal(values.get('orchard', 0))
            if total > 0:
                return total * price_usd, f"ZKP.baby ({ZKP_BABY_DASHBOARD}) - Sapling+Orchard"
    
    # Fallback to ZecHub
    logger.debug("Falling back to ZecHub scraping...")
    response = make_request_with_retry(ZEC_HUB_DASHBOARD, headers=HEADERS, max_retries=2)
    
    if response and response.status_code == 200:
        html = response.text
        
        # Flexible patterns for ZecHub
        patterns = [
            r'(Sapling|Orchard)\s*Pool\s*[—–\-:]+\s*([\d,.\s]+)\s*ZEC',
            r'(Sapling|Orchard)[^Z]*?([\d,.\s]+)\s*ZEC',
        ]
        
        pools = {}
        for pattern in patterns:
            matches = re.findall(pattern, html, re.I | re.S)
            for pool_name, amount in matches:
                value = parse_number_from_text(amount)
                if value:
                    pools[pool_name.lower()] = value
        
        if pools:
            total = safe_decimal(sum(pools.values()))
            if total > 0:
                return total * price_usd, f"ZecHub ({ZEC_HUB_DASHBOARD}) - {'+'.join(pools.keys())}"
    
    return None, None

def smart_value_locked(coin_slug: str, price_usd: Decimal) -> Tuple[Optional[Decimal], Optional[str]]:
    """Intelligently select value locked data source with full source transparency"""
    normalized = normalize_coin_input(coin_slug)
    
    # Special handling for Zcash
    if normalized == 'zcash' or coin_slug.lower() in ('zcash', 'zec'):
        return zcash_shielded_value_locked_usd(price_usd)
    
    # Try DeFiLlama chain TVL
    if normalized in SLUG_MAP and SLUG_MAP[normalized].get('defillama_slug'):
        defillama_slug = SLUG_MAP[normalized]['defillama_slug']
        rate_limiter.wait_if_needed()
        
        url = f"{DEFILLAMA_API}/v2/historicalChainTvl/{defillama_slug}"
        response = make_request_with_retry(url)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and data:
                    tvl = safe_decimal(data[-1].get("tvl"))
                    if tvl > 0:
                        return tvl, f"DeFiLlama API ({url}) - {defillama_slug} chain TVL"
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"DeFiLlama chain parse error: {e}")
    
    # Try protocol TVL
    rate_limiter.wait_if_needed()
    url = f"{DEFILLAMA_API}/protocol/{coin_slug}"
    response = make_request_with_retry(url)
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            tvl = data.get("tvl")
            if isinstance(tvl, list) and tvl:
                value = safe_decimal(tvl[-1].get("totalLiquidityUSD", 0))
                if value > 0:
                    return value, f"DeFiLlama API ({url}) - protocol TVL"
            elif isinstance(tvl, (int, float)):
                value = safe_decimal(tvl)
                if value > 0:
                    return value, f"DeFiLlama API ({url}) - protocol TVL"
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"DeFiLlama protocol parse error: {e}")
    
    return None, None

def main():
    print("\n=== ENHANCED UNDERVALUED CRYPTO CHECKER ===")
    print("Supported coins:", ", ".join(SLUG_MAP.keys()))
    print("\nYou can enter: coin name (bitcoin), symbol (BTC), or slug (btc)")
    
    coin_input = input("\nEnter coin: ").strip()
    normalized_coin = normalize_coin_input(coin_input)
    
    print(f"\nAnalyzing {normalized_coin}...")
    
    try:
        # Fetch market data
        print("→ Fetching market data...")
        cg = get_coingecko(normalized_coin)
        print(f"  ✓ Source: {cg.get('source_url', 'CoinGecko API')}")
        
        # Convert price to Decimal for calculations
        price_decimal = safe_decimal(cg["price_usd"])
        
        # Try auto-fetch issuance from Messari
        print("→ Checking Messari for issuance data...")
        auto_issuance, issuance_src = get_messari_issuance(normalized_coin)
        
        if auto_issuance:
            print(f"  ✓ Found: {auto_issuance:,.0f} new coins/year")
            print(f"  ✓ Source: {issuance_src}")
            new_coins_per_year = auto_issuance
        else:
            print("  ✗ Not found. Manual entry required.")
            print("\nEnter annual issuance if known (or press Enter to skip):")
            manual = input("New coins per year: ").strip()
            if manual:
                new_coins_per_year = safe_decimal(manual)
                issuance_src = "User provided"
            else:
                new_coins_per_year = Decimal('0')
                issuance_src = "Unknown (defaulted to 0)"
        
        # Fetch value locked
        print("→ Fetching value locked...")
        vl_decimal, vl_src = smart_value_locked(normalized_coin, price_decimal)
        
        if not vl_decimal:
            print("  ✗ Could not auto-detect value locked.")
            manual_vl = input("Enter value locked in USD (or press Enter for none): ").strip()
            if manual_vl:
                vl_decimal = safe_decimal(manual_vl)
                vl_src = "User provided"
            else:
                vl_decimal = Decimal('1')  # Avoid divide by zero
                vl_src = "None (defaulted to 1)"
        else:
            print(f"  ✓ Found: ${vl_decimal:,.2f}")
            print(f"  ✓ Source: {vl_src}")
        
        # Calculations with Decimal precision
        circulating = safe_decimal(cg.get("circulating", 0))
        max_supply = safe_decimal(cg.get("max_supply")) or safe_decimal(cg.get("total_supply")) or circulating
        
        # Guard against divide by zero
        if circulating > 0:
            inflation_pct = (new_coins_per_year / circulating * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        else:
            inflation_pct = Decimal('0')
            logger.warning("Circulating supply is 0, cannot calculate inflation")
        
        fdmc = (price_decimal * max_supply).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        
        if vl_decimal > 0:
            ratio = (fdmc / vl_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        else:
            ratio = Decimal('999999')  # Infinity proxy
            logger.warning("Value locked is 0, ratio set to maximum")
        
        # Output results with full source transparency
        print("\n" + "=" * 70)
        print(f"{cg['name'].upper()} ({cg['symbol']}) — UNDERVALUATION ANALYSIS")
        print("=" * 70)
        print(f"Price:              ${price_decimal:,.2f}")
        print(f"Circulating Supply: {circulating:,.0f}")
        print(f"Max Supply:         {max_supply:,.0f}")
        print(f"FDMC:               ${fdmc:,.2f}")
        print(f"New Coins/Year:     {new_coins_per_year:,.0f}")
        print(f"Inflation Rate:     {inflation_pct:.2f}%")
        print(f"Value Locked:       ${vl_decimal:,.2f}")
        print(f"FDMC/Value Ratio:   {ratio:.2f}x")
        print("\n--- Data Sources ---")
        print(f"Market Data:  {cg.get('source_url', 'CoinGecko API')}")
        print(f"Issuance:     {issuance_src}")
        print(f"Value Locked: {vl_src}")
        print("=" * 70)
        
        # Verdict based on Decimal comparisons
        if inflation_pct < 3 and ratio < 3:
            verdict = "🟢 UNDERVALUED - STRONG BUY"
            explanation = "Low inflation + low FDMC/Value ratio indicates undervaluation"
        elif inflation_pct < 5 and ratio < 5:
            verdict = "🟡 FAIRLY VALUED - HOLD"
            explanation = "Moderate metrics suggest fair valuation"
        elif ratio < 10:
            verdict = "🟡 SLIGHTLY OVERVALUED - CAUTIOUS HOLD"
            explanation = "Higher ratio suggests some overvaluation"
        else:
            verdict = "🔴 OVERVALUED - AVOID/SELL"
            explanation = "High FDMC/Value ratio indicates significant overvaluation"
        
        print(f"\nVERDICT: {verdict}")
        print(f"Reasoning: {explanation}")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Error during analysis: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main()