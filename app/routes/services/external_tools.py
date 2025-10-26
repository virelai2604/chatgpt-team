# app/routes/services/external_tools.py — BIFL v2.2
import httpx

async def get_exchange_rate(base: str = "USD", target: str = "EUR"):
    """Fetch live exchange rate between two currencies."""
    url = f"https://api.exchangerate.host/latest?base={base}&symbols={target}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
        rate = data.get("rates", {}).get(target)
        return {"base": base, "target": target, "rate": rate}

async def get_crypto_price(symbol: str = "BTC", currency: str = "USD"):
    """Fetch latest crypto price from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies={currency.lower()}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
        price = data.get(symbol.lower(), {}).get(currency.lower())
        return {"symbol": symbol, "currency": currency, "price": price}
