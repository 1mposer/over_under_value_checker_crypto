# main.py
# --------------------------------------------------------------
# Crypto Valuation Tool – LOCAL RUN
# --------------------------------------------------------------

import subprocess
import sys
import os

# ---------- 1. AUTO-INSTALL DEPENDENCIES ----------
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Create a minimal requirements.txt if it doesn't exist
REQ_FILE = os.path.join(os.path.dirname(__file__), "requirements.txt")
if not os.path.exists(REQ_FILE):
    with open(REQ_FILE, "w") as f:
        f.write("requests>=2.28.0\n")
    print("Created requirements.txt")

# Install requests if missing
try:
    import requests
except ImportError:
    print("requests not found – installing...")
    install("requests")
    import requests

# ---------- 2. IMPORT LOCAL MODULES ----------
# Make sure Python can find config/ and utils/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.coin_map import COIN_MAP
from utils.tvl import get_auto_tvl

# ---------- 3. FETCH COIN DATA ----------
def get_coin_data(coin: str):
    coin_id = COIN_MAP.get(coin.lower(), coin.lower())
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"Error {resp.status_code} for '{coin}'. Try 'ripple' for XRP.")
    data = resp.json()
    return {
        "name": data["name"],
        "price": data["market_data"]["current_price"]["usd"],
        "circulating": data["market_data"]["circulating_supply"],
        "max_supply": data["market_data"].get("max_supply")
    }

# ---------- 4. MAIN LOGIC ----------
def main():
    print("\n=== Universal Crypto Valuation Tool ===\n")
    coin = input("Enter coin (zcash, xrp, btc, etc): ").strip().lower()
    new_coins = float(input("New coins per year (from white paper): "))

    # ---- Fetch live data ----
    try:
        data = get_coin_data(coin)
        price = data["price"]
    except Exception as e:
        print(f"\n{e}")
        print("Could not retrieve data. Check spelling or internet connection.\n")
        return

    # ---- Auto TVL ----
    value_locked = get_auto_tvl(coin, price)
    print(f"Auto Value Locked: ${value_locked:,}")

    # ---- Calculations ----
    inflation = (new_coins / data["circulating"]) * 100
    fdmc = price * (data["max_supply"] or data["circulating"] * 2)
    ratio = fdmc / value_locked

    # ---- Verdict ----
    print("\n" + "="*60)
    print(f"{data['name'].upper()} UNDERVALUED TEST")
    print(f"Price:      ${price:,.2f}")
    print(f"Inflation:  {inflation:.2f}%")
    print(f"FDMC:       ${fdmc:,.0f}")
    print(f"TVL:        ${value_locked:,}")
    print(f"FDMC/TVL:   {ratio:.1f}x")

    if inflation < 3 and ratio < 3:
        print("→ UNDERVALUED! BUY")
    elif ratio < 10:
        print("→ Fair, HOLD")
    else:
        print("→ Overvalued, AVOID")
    print("="*60)

if __name__ == "__main__":
    main()