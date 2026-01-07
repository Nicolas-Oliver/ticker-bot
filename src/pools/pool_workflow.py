import discord
import aiohttp
from consts import HEADERS, NETWORK_ID
from src.logger import notify_bot, notify_admin

async def get_pools(interaction, bot, asset_id: int = None):
    """Fetch liquidity pools from Vestige Labs API"""
    try:
        url = f"https://api.vestigelabs.org/pools"
        params = {
            "network_id": NETWORK_ID,
            "limit": 50
        }
        
        if asset_id:
            params["asset_id"] = asset_id
        
        conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
        session = aiohttp.ClientSession(connector=conn)
        async with session.get(url=url, params=params, headers=HEADERS) as response:
            if response.status == 200:
                pools = await response.json()
                await session.close()
                return pools
            else:
                await notify_admin(interaction, bot, f"error fetching pools :: {response}")
                await session.close()
                return None
    except Exception as e:
        await notify_admin(interaction, bot, f"error in pool fetch: {str(e)}")
        return None

async def pool_workflow(interaction: discord.Interaction, bot, asset_id: int = None):
    """Handle pool command workflow"""
    pools = await get_pools(interaction, bot, asset_id)
    
    if not pools:
        await interaction.followup.send("❌ Could not fetch pool data. Please try again.")
        return
    
    pool_list = pools.get("pools", [])
    
    if not pool_list:
        await interaction.followup.send("❌ No pools found.")
        return
    
    # Create embed with pool information
    embed = discord.Embed(
        title="Liquidity Pools",
        color=discord.Color.green(),
        description=f"Showing top {min(10, len(pool_list))} pools"
    )
    
    for i, pool in enumerate(pool_list[:10], 1):
        pool_info = f"**TVL:** ${float(pool.get('tvl', 0)):,.2f}\n"
        pool_info += f"**Volume 24h:** ${float(pool.get('volume_24h', 0)):,.2f}\n"
        pool_info += f"**Fee:** {pool.get('fee_tier', 'N/A')}%"
        
        embed.add_field(
            name=f"{i}. Pool {pool.get('pool_id', 'Unknown')[:8]}",
            value=pool_info,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)
