import discord, logging, os

from src.Bot import Bot

# Logic to pull from .env
from dotenv import load_dotenv
load_dotenv()
LOG_LEVEL = (os.environ.get("LOG_LEVEL") or "INFO").upper()
ADMIN = os.environ.get("ADMIN")

logging.getLogger('discord').propagate = False
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s     [%(user)s::%(id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def notify_bot(interaction: discord.Interaction, message: str):
    logger.info(f"{message}", extra={"user": interaction.user.name, "id": interaction.user.id})

async def notify_admin(interaction: discord.Interaction, bot: Bot,message: str):
    await bot.management_channel.send(f"<@{ADMIN}>, {message}")
    logger.critical(message, extra={"user": interaction.user.name, "id": interaction.user.id})