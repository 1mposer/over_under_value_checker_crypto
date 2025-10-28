"""
undervalued_test.py
-------------------
Runs the 60-second undervalued test using:
  • Live data from fetcher
  • White-paper numbers you type in
"""

def run_test(coin_data: dict, whitepaper: dict):
    """
    coin_data: dict from fetcher (price, circulating, max_supply, etc.)
    whitepaper: dict with 'new_coins_per_year' and 'value_locked_usd'
    """
    price = coin_data["price"]
    circulating = coin_data["circulating"]
    max_supply = coin_data.get("max_supply") or coin_data.get("total_supply")

    # ---- 1. Inflation ----
    new_coins = whitepaper["new_coins_per_year"]
    inflation = (new_coins / circulating) * 100

    # ---- 2. FDMC ----
    fdmc = price * max_supply if max_supply else None

    # ---- 3. Value Locked Ratio ----
    value_locked = whitepaper["value_locked_usd"]
    ratio = fdmc / value_locked if fdmc and value_locked else None

    # ---- 4. Print Results ----
    print("\n" + "="*50)
    print(f"UNDERVALUED TEST: {coin_data['name'].upper()}")
    print("="*50)
    print(f"Price: ${price:,.2f}")
    print(f"Circulating: {circulating:,.0f}")
    print(f"Max Supply: {max_supply:,.0f}" if max_supply else "No max supply")
    print(f"Inflation: {inflation:.2f}%")
    if fdmc:
        print(f"FDMC: ${fdmc:,.0f}")
    print(f"Value Locked: ${value_locked:,.0f}")

    # ---- 5. Verdict ----
    if inflation > 10:
        print("Inflation > 10% → AVOID")
    elif inflation > 3:
        print("Inflation 3–10% → Medium")
    else:
        print("Inflation < 3% → SCARCE! GOOD")

    if ratio:
        print(f"FDMC / Value Locked = {ratio:.1f}x")
        if ratio < 3:
            print("→ UNDERVALUED! BUY")
        elif ratio < 10:
            print("→ Fair price, HOLD")
        else:
            print("→ Overvalued, SELL/AVOID")
    else:
        print("Missing data → Can't judge FDMC")

    print("="*50)