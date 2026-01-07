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

def start_health_check_server():
    """Start HTTP health check server (binds 0.0.0.0:$PORT)."""
    try:
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/", "/health"):
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"OK")
                    except BrokenPipeError:
                        pass
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                return

        server_address = ("0.0.0.0", PORT)
        try:
            httpd = HTTPServer(server_address, HealthHandler)
        except OSError as e:
            print(f"✗ ERROR binding health server to {server_address}: {e}", flush=True)
            return False

        def serve():
            print(f"✓ Health check server thread running on port {PORT}", flush=True)
            while True:
                try:
                    httpd.serve_forever()
                except Exception as e:
                    print(f"✗ ERROR in health check thread: {e}", flush=True)
                    traceback.print_exc()
                    time.sleep(1)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        
        print(f"✓ Health check server started on 0.0.0.0:{PORT}", flush=True)
        return True
    except Exception as e:
        print(f"✗ ERROR starting health check server: {e}", flush=True)
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
                print("✗ ERROR: DISCORD_TOKEN is missing (retrying in 60s)", flush=True)
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
                print("✓ Commands loaded successfully", flush=True)
            except Exception as e:
                print(f"✗ ERROR loading commands: {e}", flush=True)
                traceback.print_exc()

            print("Attempting to connect to Discord...", flush=True)
            await client.start(discord_token)

            print("Discord bot stopped unexpectedly (restarting in 10s)", flush=True)
            await asyncio.sleep(10)

        except BaseException as e:
            print(f"✗ CRITICAL ERROR running Discord bot: {e}", flush=True)
            traceback.print_exc()
            await asyncio.sleep(10)


def keep_alive():
    """Fallback loop to keep container alive if asyncio loop dies."""
    print("!! Entering infinite keep_alive loop to prevent container exit !!", flush=True)
    while True:
        time.sleep(3600)

async def main():
    """Run the bot forever."""
    # Run bot loop
    print("Starting Discord bot loop...", flush=True)
    await run_bot_forever()

if __name__ == "__main__":
    try:
        print("--- APP STARTUP ---", flush=True)
        
        # 1. Start health check server SYNCHRONOUSLY before anything else
        if not start_health_check_server():
            print("WARNING: Health check server failed to start, causing possible probe failures.", flush=True)
        
        # 2. Run main asyncio loop
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        print(f"FATAL ERROR at root: {e}", flush=True)
        traceback.print_exc()
    finally:
        keep_alive()
