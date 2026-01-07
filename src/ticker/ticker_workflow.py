import discord

from src.Bot import Bot
from src.ticker.TokenInfo import TokenInfo
from src.ticker.graph import get_graph
from src.ticker.utils import (
    calculate_percentage_change, get_ticker_info, 
    get_ticker_candles, find_highest_and_lowest,
    get_currencies
)
from src.ticker.ui_ticker_workflow import ticker_ui

from src.logger import notify_admin

async def ticker_workflow(interaction: discord.Interaction, bot: Bot, ticker: str):
    try:
        # Get Algo price in currencies
        currencies = await get_currencies(interaction, bot)
        if currencies == None:
            await interaction.edit_original_response(content="Problem pulling algos current price.")
            return None
        # del currencies["BTC"] # its like allllll zeros
        currencies["ALGO"] = 1

        
        # Get ticker/token data
        token: TokenInfo = await get_ticker_info(interaction, bot, ticker.lower())
        if token == None:
            await interaction.edit_original_response(content="Ticker not found")
            return None

        # Get candles for 7 days
        candles = await get_ticker_candles(interaction, token, 7)

        # Get candles for 24 days, only for the high/low
        candles_24 = await get_ticker_candles(interaction, token, 1)

        if candles:
            token.highest_7d, token.lowest_7d = find_highest_and_lowest(candles)
            token.highest_24h, token.lowest_24h = find_highest_and_lowest(candles_24)
            token.graph = get_graph(candles)
            
        await ticker_ui(interaction, currencies, "USD", token)

    except Exception as e:
        await interaction.edit_original_response(content="Something bad happened, and I need an adult...")
        await notify_admin(interaction, bot, f"Ticker: {ticker} :: Reason: {e}")
