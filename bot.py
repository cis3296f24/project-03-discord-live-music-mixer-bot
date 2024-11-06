import discord
import ffmpeg
from discord.ext import commands
from discord_components import ComponentsBot
import pyaudio
import asyncio
from VoiceChat import VoiceChat

intents = discord.Intents.default()
intents.messages = True
bot = ComponentsBot(command_prefix=",", intents=intents)
bot.add_cog(VoiceChat(bot))
with open("dontpushtorepo.txt", 'r') as key:
    token = key.readlines()[0]

bot.run(token)