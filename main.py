### External Imports
import discord, os
from discord import app_commands

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

client.run(DISCORD_TOKEN)