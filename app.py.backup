# app.py — Public Web Dashboard
import streamlit as st
import requests
from config.coin_map import COIN_MAP
from utils.tvl import get_auto_tvl

st.set_page_config(page_title="OUVC Crypto Checker", layout="wide")
st.title("Crypto Valuation Checker")
st.caption("Enter a coin → Get instant BUY/HOLD/AVOID verdict")

# === INPUTS ===
col1, col2 = st.columns(2)
with col1:
    coin = st.text_input("Coin (e.g., zcash, xrp, btc)", "zcash").strip().lower()
with col2:
    new_coins = st.number_input("New Coins per Year", value=738000, step=10000)

# === FETCH DATA ===
@st.cache_data(ttl=60)
def get_coin_data(coin):
    coin_id = COIN_MAP.get(coin, coin)
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        st.error(f"Cannot find '{coin}'. Try 'ripple' for XRP.")
        return None
    data = resp.json()
    return {
        "name": data["name"],
        "price": data["market_data"]["current_price"]["usd"],
        "circulating": data["market_data"]["circulating_supply"],
        "max_supply": data["market_data"].get("max_supply")
    }

if st.button("Analyze", type="primary"):
    with st.spinner("Fetching data..."):
        data = get_coin_data(coin)
        if not data:
            st.stop()
            return

        price = data["price"]
        value_locked = get_auto_tvl(coin, price)

        inflation = (new_coins / data["circulating"]) * 100
        max_supply = data["max_supply"] if data["max_supply"] is not None else data["circulating"] * 2
        fdmc = price * max_supply
        ratio = fdmc / value_locked

        st.success(f"**{data['name'].upper()}** Analyzed!")
        colA, colB, colC = st.columns(3)
        colA.metric("Price", f"${price:,.2f}")
        colB.metric("Inflation", f"{inflation:.2f}%")
        colC.metric("FDMC / TVL", f"{ratio:.1f}x")

        if inflation < 3 and ratio < 3:
            st.balloons()
            st.markdown("### UNDERVALUED! BUY")
        elif ratio < 10:
            st.markdown("### Fair, HOLD")
        else:
            st.markdown("### Overvalued, AVOID")

        st.caption("Made with love by 1mposer")