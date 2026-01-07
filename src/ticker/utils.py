import aiohttp, time, copy

from src.Bot import Bot
from src.ticker.TokenInfo import TokenInfo
from consts import NETWORK_ID, HEADERS, SEARCH_URL

from src.logger import notify_bot, notify_admin

async def get_currencies(interaction, bot):
    algo_data = None
    url = "https://api.vestigelabs.org/assets/price"
    conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    async with session.get(url=url, headers=HEADERS) as response:
        if response.status == 200:
            algo_data = await response.json()
        else:
            await notify_admin(interaction, bot, f"error processing algo price :: {response}")
            await session.close()
            return None
    await session.close()

    return algo_data

async def get_ticker_candles(interaction, token: TokenInfo, start_num_days_ago):
    now = int(time.time())
    age = now - token.creation_timestamp

    if age <= 1800:     # 30 mins
        interval = 30
    elif age <= 3600:   # 1 hour
        interval = 60    
    elif age <= 86400:  # 1 day
        interval = 300 
    else:
        interval = 7200

    start = now - start_num_days_ago * 24 * 3600  # 7 days in seconds

    url = (f"https://api.vestigelabs.org/assets/{token.asset_id}/candles?"
           f"network_id={NETWORK_ID}&interval={interval}&start={start}"
           f"&denominating_asset_id=0&volume_in_denominating_asset=false")
    
    conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    async with session.get(url=url, headers=HEADERS) as response:
        if response.status == 200:
            candles = await response.json()
        else:
            notify_bot(interaction, f"error processing candles :: {response}")
            await session.close()
            return None
    await session.close()  

    if not candles: return None
    
    return candles

async def get_ticker_info(interaction, bot, ticker):
    conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=conn)
    async with session.get(url=SEARCH_URL.format(ticker), headers=HEADERS) as response:
        if response.status == 200:
            data = await response.json()
            token_data = data.get("results",[])
        else:
            notify_bot(interaction, f"error processing ticker :: {response}")
            await session.close()
            return None
    await session.close()  

    tokens = []
    # Exact Match or people who add a $ in their ticker...
    for token in token_data:
        token_info = TokenInfo(token)
        if ticker.lower() == token_info.ticker.lower().strip() or f"${ticker.lower()}" == token_info.ticker.lower().strip():
            tokens.append(token_info)
    # Highest rank "exact matching" ticker wings
    if tokens:
        highest_rank_token = min(tokens, key=lambda x: x.rank)
        return highest_rank_token
    else:
        return None

def find_highest_and_lowest(candles):
    highest_high = max(item["high"] for item in candles)
    lowest_low = min(item["low"] for item in candles)
    return highest_high, lowest_low

def calculate_percentage_change(current_price, price_24hr_ago, price_7days_ago):
    def percentage_change(new_price, old_price):
        if old_price == 0:
            return None
        return ((new_price - old_price) / old_price) * 100

    change_24hr = percentage_change(current_price, price_24hr_ago)
    change_7days = percentage_change(current_price, price_7days_ago)
    return change_24hr, change_7days

def conversion(currencies, currency, token):
    converted_token: TokenInfo = copy.deepcopy(token)

    postfix = ""
    if currency == "ALGO":
        postfix = " Ⱥ"
    elif currency == "USD":
        postfix = " $"
    elif currency == "EUR":
        postfix = " €"
    elif currency == "GBP":
        postfix = " £"
    else:
        postfix = " ?"

    token.change_24_hrs, token.change_7_days = calculate_percentage_change(
        token.price*currencies[currency], token.price1d*currencies[currency], token.price7d*currencies[currency])

    converted_token.price = f"{token.price*currencies[currency]:,.8f}{postfix}"
    converted_token.highest_24h = f"{token.highest_24h*currencies[currency]:,.8f}{postfix}"
    converted_token.highest_7d = f"{token.highest_7d*currencies[currency]:,.8f}{postfix}"
    converted_token.lowest_24h = f"{token.lowest_24h*currencies[currency]:,.8f}{postfix}"
    converted_token.lowest_7d = f"{token.lowest_7d*currencies[currency]:,.8f}{postfix}"
    converted_token.change_24_hrs = f"{token.change_24_hrs:,.2f}%"
    converted_token.change_7_days = f"{token.change_7_days:,.2f}%"
    converted_token.volume1d = f"{token.volume1d*currencies[currency]:,.3f}{postfix}"
    converted_token.market_cap = f"{token.market_cap*currencies[currency]:,.3f}{postfix}"
    return converted_token