import discord
from discord.ext import commands
from discord import VoiceChannel, Member
import os
import asyncio

with open("./discordkey.txt", 'r') as key:
    token = key.readlines()[0]

intents = discord.Intents.default()
intents.message_content = True  # For reading message content (if needed)
intents.guilds = True  # Required for guild-related events
intents.voice_states = True  # Required for voice-related events
intents.members = True  # For detecting user join/leave in voice

bot = commands.Bot(
    command_prefix=",", 
    intents=intents,
    ffmpeg_options={'executable': 'ffmpeg'}
)

async def go():
    #adds VoiceChat.py as cog
    for fname in os.listdir("./cogs"):
        if fname.endswith(".py"):
            await bot.load_extension(f"cogs.{fname[:-3]}")

async def main():
    async with bot:
        await go()
        await bot.start(token)

asyncio.run(main())
