# utils/tvl.py
import requests

def get_auto_tvl(coin: str, price: float) -> int:
    coin = coin.lower()

    # Zcash
    if coin in ["zcash", "zec"]:
        try:
            data = requests.get("https://api.zkp.baby/v1/shielded").json()
            return int(data["shielded_balance"] * price)
        except:
            return 1600000000

    # Monero
    elif coin in ["monero", "xmr"]:
        try:
            circ = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}").json()["market_data"]["circulating_supply"]
            return int(circ * price)
        except:
            return 2800000000

    # PoS (DefiLlama)
    elif coin in ["ethereum", "cardano", "solana", "polkadot", "eth", "ada", "sol", "dot"]:
        try:
            map_id = {"eth": "ethereum", "ada": "cardano", "sol": "solana", "dot": "polkadot"}
            url = f"https://api.llama.fi/tvl/{map_id.get(coin, coin)}"
            tvl = requests.get(url).json()
            if isinstance(tvl, (int, float)):
                return int(tvl)
        except:
            pass

    # Bitcoin HODL
    elif coin in ["bitcoin", "btc"]:
        return int(19700000 * 0.5 * price)

    # XRP Liquidity
    elif coin in ["xrp", "ripple"]:
        return 10000000000

    # Fallback
    print(f"No auto-TVL for '{coin}'. Enter manually:")
    return int(float(input("Value locked in USD: ")))