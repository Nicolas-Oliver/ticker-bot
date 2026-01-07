### External Imports
import os
import sys
import asyncio
import traceback
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# DigitalOcean commonly sets PORT; default to 8080
PORT = int(os.environ.get("PORT", "8080"))

async def start_health_check_server():
    """Start HTTP health check server (binds 0.0.0.0:$PORT)."""
    try:
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/", "/health"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"OK")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # Silence default request logs
                return

        httpd = HTTPServer(("0.0.0.0", PORT), HealthHandler)

        def serve():
            httpd.serve_forever()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()

        print(f"✓ Health check server started on 0.0.0.0:{PORT}")
        return True
    except Exception as e:
        print(f"✗ ERROR starting health check server: {e}")
        traceback.print_exc()
        return False

async def run_bot_forever():
    """Run bot loops forever, even if imports fail."""
    while True:
        try:
            # Import dependencies inside the loop
            # If deps are missing, this loop will keep printing errors but container stays UP
            import discord
            from discord import app_commands
            from dotenv import load_dotenv

            from src.Bot import Bot
            from src.on_ready import on_ready
            from src.core_config import load_the_commands

            load_dotenv()
            discord_token = os.environ.get("DISCORD_TOKEN")
            management_channel = os.environ.get("MANAGEMENT_CHANNEL")

            if not discord_token:
                print("✗ ERROR: DISCORD_TOKEN is missing (retrying in 60s)")
                await asyncio.sleep(60)
                continue

            bot = Bot()

            class MyClient(discord.Client):
                def __init__(self, intents):
                    super().__init__(intents=intents)
                    self.synced = False

            async def on_ready_event():
                await on_ready(client, tree, bot, management_channel)

            intents = discord.Intents.default()
            client = MyClient(intents=intents)
            tree = app_commands.CommandTree(client)
            client.on_ready = on_ready_event

            try:
                load_the_commands(client, tree, bot)
                print("✓ Commands loaded successfully")
            except Exception as e:
                print(f"✗ ERROR loading commands: {e}")
                traceback.print_exc()

            print("Attempting to connect to Discord...")
            await client.start(discord_token)

            print("Discord bot stopped unexpectedly (restarting in 10s)")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"✗ ERROR running Discord bot: {e}")
            traceback.print_exc()
            await asyncio.sleep(10)


def keep_alive():
    """Fallback loop to keep container alive if asyncio loop dies."""
    while True:
        time.sleep(60)

async def main():
    """Start health server, then run the bot forever."""
    try:
        # 1. Start health check server FIRST
        print("Starting health check server...")
        health_started = await start_health_check_server()
        if not health_started:
            print("CRITICAL: Health check server failed to start")

        # 2. Run bot forever
        print("Starting Discord bot loop...")
        await run_bot_forever()

    except Exception as e:
        print(f"FATAL ERROR in main: {e}")
        traceback.print_exc()
        # Fallback to keep-alive loop so container logs are visible
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        # Run main asyncio loop
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"FATAL ERROR at root: {e}")
        traceback.print_exc()
        keep_alive()
