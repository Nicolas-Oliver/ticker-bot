import discord
from discord import app_commands

from src.Bot import Bot
from src.ticker.ticker_workflow import ticker_workflow
from src.swap.swap_workflow import swap_workflow
from src.pools.pool_workflow import pool_workflow

from src.logger import notify_bot

def define_commands(tree, bot: Bot):
    @tree.command(
        name = "info",
        description=f"retrieves information for particular coin"
    )
    @app_commands.describe(ticker=f"ticker for the coin you want info on, up to 8 chars")
    async def slash(interaction: discord.Interaction, ticker: str):
        await interaction.response.defer(thinking=True)
        
        if interaction.user.bot: return
        
        notify_bot(interaction, "ticker commmand used")
        await ticker_workflow(interaction, bot, ticker)
        notify_bot(interaction, "ticker complete")

    @tree.command(
        name = "swap",
        description="find the best swap routes between two assets"
    )
    @app_commands.describe(
        asset_in="asset ID to swap from",
        asset_out="asset ID to swap to",
        amount="amount to swap"
    )
    async def swap_command(interaction: discord.Interaction, asset_in: int, asset_out: int, amount: float):
        await interaction.response.defer(thinking=True)
        
        if interaction.user.bot: return
        
        notify_bot(interaction, "swap command used")
        await swap_workflow(interaction, bot, asset_in, asset_out, amount)
        notify_bot(interaction, "swap complete")

    @tree.command(
        name = "pools",
        description="view liquidity pools and their statistics"
    )
    @app_commands.describe(
        asset_id="optional: filter pools by asset ID"
    )
    async def pools_command(interaction: discord.Interaction, asset_id: int = None):
        await interaction.response.defer(thinking=True)
        
        if interaction.user.bot: return
        
        notify_bot(interaction, "pools command used")
        await pool_workflow(interaction, bot, asset_id)
        notify_bot(interaction, "pools complete")
