### External Imports
import discord, os
from discord import app_commands
import asyncio
from aiohttp import web
import sys
import traceback

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

try:
    load_the_commands(client, tree, bot)
except Exception as e:
    print(f"ERROR loading commands: {e}")
    traceback.print_exc()
    sys.exit(1)

# Health check endpoint for DigitalOcean
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_check_server():
    """Start HTTP health check server on port 8080"""
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("✓ Health check server started on port 8080")
        return True
    except Exception as e:
        print(f"✗ ERROR starting health check server: {e}")
        traceback.print_exc()
        return False

async def run_bot():
    """Run the Discord bot"""
    while True:
        try:
            await client.start(DISCORD_TOKEN)
        except Exception as e:
            print(f"✗ ERROR running Discord bot: {e}")
            traceback.print_exc()
            # brief backoff before retry to avoid tight crash loop
            await asyncio.sleep(10)
        else:
            # If start returns normally (e.g., shutdown), break loop
            print("Discord bot stopped; restarting in 10s")
            await asyncio.sleep(10)

async def main():
    """Run health check server and Discord bot concurrently"""
    try:
        print("Starting health check server...")
        health_started = await start_health_check_server()
        
        if health_started:
            print("Starting Discord bot...")
            # Run bot with retries while health server stays up
            await run_bot()
        else:
            print("ERROR: Could not start health check server")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR in main: {e}")
        traceback.print_exc()
        sys.exit(1)

# Run both bot and health check server
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
