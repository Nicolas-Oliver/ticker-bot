### External Imports
import discord, os
from discord import app_commands
import asyncio
from aiohttp import web

### Internal Imports
# Core
from src.Bot import Bot
from src.on_ready import on_ready 
from src.core_config import load_the_commands

# Logic to pull from .env
from dotenv import load_dotenv
load_dotenv()
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
MANAGEMENT_CHANNEL = os.environ.get("MANAGEMENT_CHANNEL")

# Fail fast if required env vars are missing so deployments surface a clear error
if not DISCORD_TOKEN:
    raise RuntimeError("Environment variable DISCORD_TOKEN is required")

# Brain/Bot State
bot = Bot()

class myclient(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.synced = False 

# Load Bot
async def on_ready_event():
    await on_ready(client, tree, bot, MANAGEMENT_CHANNEL)

intents=discord.Intents.default()
client = myclient(intents=intents)
tree = app_commands.CommandTree(client)

client.on_ready = on_ready_event

load_the_commands(client, tree, bot)

# Health check endpoint for DigitalOcean
async def health_check(request):
    return web.Response(text="OK", status=200)

async def run_bot_with_health_check():
    # Start health check server
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Health check server started on port 8080")
    
    # Run Discord bot
    await client.start(DISCORD_TOKEN)

# Run both bot and health check server
asyncio.run(run_bot_with_health_check())
