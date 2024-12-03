import discord
from discord.ext import commands
from discord import VoiceChannel, Member
import os
import asyncio
import signal
import shutil
import tempfile


song_dir = "./rsc"
# Check if the directory exists, and create it if not
if not os.path.exists(song_dir):
    os.makedirs(song_dir)
    print(f"Directory '{song_dir}' created.")

with open("./discordkey.txt", 'r') as key:
    token = key.readlines()[0]

intents = discord.Intents.default()
intents.message_content = True  # For reading message content (if needed)
intents.guilds = True  # Required for guild-related events
intents.voice_states = True  # Required for voice-related events
intents.members = True  # For detecting user join/leave in voice
bot = commands.Bot(command_prefix=",", intents=intents)

async def go():
    #adds VoiceChat.py as cog
    for fname in os.listdir("./cogs"):
        if fname.endswith(".py"):
            await bot.load_extension(f"cogs.{fname[:-3]}")

async def main():
    async with bot:
        await go()
        await bot.start(token)

#loop = asyncio.get_event_loop()
#loop.add_signal_handler(signal.SIGINT, handle_sigterm)
#loop.add_signal_handler(signal.SIGTERM, handle_sigterm)

try:
    asyncio.run(main())

except KeyboardInterrupt:
    # clear song directory
    for filename in os.listdir(song_dir):
        file_path = os.path.join(song_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory
        except Exception as e:
            print(f"Failed to Clear {song_dir}. Reason: {e}")

    print("\n" + "Bot Closed")
