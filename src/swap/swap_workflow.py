import discord
import aiohttp
from consts import HEADERS, NETWORK_ID
from src.logger import notify_bot, notify_admin

async def get_swap_routes(interaction, bot, asset_in: int, asset_out: int, amount: float):
    """Fetch swap routes from Vestige Labs API"""
    try:
        url = f"https://api.vestigelabs.org/swap/routes"
        params = {
            "asset_in": asset_in,
            "asset_out": asset_out,
            "amount": amount,
            "network_id": NETWORK_ID
        }
        
        conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
        session = aiohttp.ClientSession(connector=conn)
        async with session.get(url=url, params=params, headers=HEADERS) as response:
            if response.status == 200:
                routes = await response.json()
                await session.close()
                return routes
            else:
                await notify_admin(interaction, bot, f"error fetching swap routes :: {response}")
                await session.close()
                return None
    except Exception as e:
        await notify_admin(interaction, bot, f"error in swap routes: {str(e)}")
        return None

async def swap_workflow(interaction: discord.Interaction, bot, asset_in: int, asset_out: int, amount: float):
    """Handle swap command workflow"""
    routes = await get_swap_routes(interaction, bot, asset_in, asset_out, amount)
    
    if not routes:
        await interaction.followup.send("❌ Could not fetch swap routes. Please try again.")
        return
    
    # Extract best route (usually first one)
    best_route = routes.get("routes", [])[0] if routes.get("routes") else None
    
    if not best_route:
        await interaction.followup.send("❌ No swap routes available for this pair.")
        return
    
    # Create embed with swap information
    embed = discord.Embed(
        title="Swap Route",
        color=discord.Color.blue(),
        description=f"Swap {amount} of asset {asset_in} for asset {asset_out}"
    )
    
    embed.add_field(
        name="Best Route",
        value=f"Output: {best_route.get('output_amount', 'N/A')}",
        inline=False
    )
    
    embed.add_field(
        name="Price Impact",
        value=f"{best_route.get('price_impact', 'N/A')}%",
        inline=True
    )
    
    embed.add_field(
        name="Hops",
        value=f"{len(best_route.get('hops', []))} hops",
        inline=True
    )
    
    await interaction.followup.send(embed=embed)
