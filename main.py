### External Imports
import os
import sys
import asyncio
import traceback

import threading
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
    """Import and run the Discord bot in a retry loop.

    Importing discord/bot modules happens *after* the health server is up,
    so readiness probes won't fail due to early import errors.
    """
    while True:
        try:
            # Import late to ensure health server is already running
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
                print("✗ ERROR: DISCORD_TOKEN is missing; retrying in 30s")
                await asyncio.sleep(30)
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

            # If start returns normally (e.g., clean shutdown), restart
            print("Discord bot stopped; restarting in 10s")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"✗ ERROR running Discord bot: {e}")
            traceback.print_exc()
            await asyncio.sleep(10)

async def main():
    """Start health server, then run the bot forever."""
    try:
        # 1. Start health check server FIRST to ensure container stays up
        print("Starting health check server...")
        health_started = await start_health_check_server()
        
        if not health_started:
            print("CRITICAL: Health check server failed to start, but continuing to try to run bot...")

        # 2. Start Discord bot (runs forever, with retries)
        print("Starting Discord bot...")
        bot_task = asyncio.create_task(run_bot_forever())
        await bot_task
            
    except Exception as e:
        print(f"FATAL ERROR in main: {e}")
        traceback.print_exc()
        # Sleep to keep container logs visible
        while True:
            await asyncio.sleep(60)

# Run both bot and health check server
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"FATAL ERROR at root: {e}")
        traceback.print_exc()
        # Last ditch effort to keep container alive for logs if asyncio fails
        import time
        while True:
            time.sleep(60)
