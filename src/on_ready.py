from src.loader import load_the_bot

async def on_ready(self, tree, bot, management_channel):
    await self.wait_until_ready()
    # Check if slash commands have been synced
    if not self.synced:
        await tree.sync()
        self.synced = True
        print("Commands Syncing...")

    # Lock bot until ready for users
    bot.locked = True
    
    # Set up management channel if provided
    if management_channel:
        bot.management_channel = await self.fetch_channel(management_channel)
        await bot.management_channel.send("Bot coming online.")
        print("########## Bot coming online ##########")
    else:
        print("########## Bot coming online (no management channel configured) ##########")

    ### Loading Data
    await load_the_bot(bot)  

    if bot.management_channel:
        await bot.management_channel.send("Bot ready, data loaded!")
    print("########## Bot ready, data loaded ##########")
    
    # Bot loaded with data, release lock
    bot.locked = False
