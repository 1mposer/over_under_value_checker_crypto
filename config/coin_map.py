# config/coin_map.py
# ──────────────────────────────────────────────────────────────
# 100+ COINS – TIDY, GROUPED, ALPHABETICAL
# Format: "input": "coingecko_id"
# ──────────────────────────────────────────────────────────────

COIN_MAP = {
    # ── BITCOIN & FORKS ──
    "btc": "bitcoin", "bitcoin": "bitcoin", "bit": "bitcoin",
    "bch": "bitcoin-cash", "bitcoincash": "bitcoin-cash",
    "bsv": "bitcoin-sv", "bitcoinsv": "bitcoin-sv",

    # ── ETHEREUM & L2s ──
    "eth": "ethereum", "ethereum": "ethereum", "ether": "ethereum",
    "matic": "polygon", "polygon": "polygon", "pol": "polygon",
    "arb": "arbitrum", "arbitrum": "arbitrum",
    "op": "optimism", "optimism": "optimism",

    # ── LAYER 1s ──
    "ada": "cardano", "cardano": "cardano",
    "sol": "solana", "solana": "solana",
    "dot": "polkadot", "polkadot": "polkadot",
    "avax": "avalanche-2", "avalanche": "avalanche-2",
    "near": "near", "nearprotocol": "near",
    "atom": "cosmos", "cosmos": "cosmos",
    "hbar": "hedera", "hedera": "hedera",
    "xlm": "stellar", "stellar": "stellar",
    "vet": "vechain", "vechain": "vechain",
    "icp": "internet-computer", "dfinity": "internet-computer",
    "fil": "filecoin", "filecoin": "filecoin",
    "algo": "algorand", "algorand": "algorand",
    "xtz": "tezos", "tezos": "tezos",
    "eos": "eos", "eosio": "eos",
    "trx": "tron", "tron": "tron",

    # ── PRIVACY ──
    "zec": "zcash", "zcash": "zcash",
    "xmr": "monero", "monero": "monero",
    "dash": "dash", "xdash": "dash",

    # ── STABLECOINS ──
    "usdt": "tether", "tether": "tether",
    "usdc": "usd-coin", "usdcoin": "usd-coin",
    "dai": "dai", "daistablecoin": "dai",
    "busd": "binance-usd", "binanceusd": "binance-usd",

    # ── EXCHANGE TOKENS ──
    "bnb": "binancecoin", "binancecoin": "binancecoin",
    "cro": "crypto-com-chain", "cryptocom": "crypto-com-chain",
    "ftt": "ftx-token", "ftx": "ftx-token",
    "okb": "okb", "okex": "okb",
    "ht": "huobi-token", "huobi": "huobi-token",
    "kcs": "kucoin-shares", "kucoin": "kucoin-shares",

    # ── DEFI ──
    "uni": "uniswap", "uniswap": "uniswap",
    "aave": "aave", "aavev3": "aave",
    "comp": "compound-governance-token", "compound": "compound-governance-token",
    "mkr": "maker", "makerdao": "maker",
    "crv": "curve-dao-token", "curve": "curve-dao-token",
    "snx": "synthetix-network-token", "synthetix": "synthetix-network-token",
    "yfi": "yearn-finance", "yearn": "yearn-finance",

    # ── MEME ──
    "doge": "dogecoin", "dogecoin": "dogecoin", "dogecoin": "dogecoin",
    "shib": "shiba-inu", "shibainu": "shiba-inu", "shiba": "shiba-inu",
    "pepe": "pepe", "pepecoin": "pepe",
    "floki": "floki", "flokiinu": "floki",

    # ── PAYMENTS ──
    "xrp": "ripple", "ripple": "ripple",
    "ltc": "litecoin", "litecoin": "litecoin",

    # ── ORACLE & AI ──
    "link": "chainlink", "chainlink": "chainlink",
    "grt": "the-graph", "thegraph": "the-graph",
    "rndr": "render-token", "render": "render-token",
    "fet": "fetch-ai", "fetchai": "fetch-ai",
    "agix": "singularitynet", "singularity": "singularitynet",

    # ── GAMING & METAVERSE ──
    "mana": "decentraland", "decentraland": "decentraland",
    "sand": "the-sandbox", "sandbox": "the-sandbox",
    "axs": "axie-infinity", "axie": "axie-infinity",
    "gala": "gala", "galagames": "gala",

    # ── OTHERS ──
    "qnt": "quant-network", "quant": "quant-network",
    "hnt": "helium", "helium": "helium",
    "chz": "chiliz", "chiliz": "chiliz",
    "lrc": "loopring", "loopring": "loopring",
    "bat": "basic-attention-token", "brave": "basic-attention-token",
    "enj": "enjincoin", "enjin": "enjincoin",
    "hot": "holotoken", "holo": "holotoken",
    "celo": "celo", "celonetwork": "celo",
    "rose": "oasis-network", "oasis": "oasis-network",
    "kas": "kaspa", "kaspa": "kaspa",
}