from discord.ext import commands
import discord
from discord_components import ComponentsBot
from discord import VoiceChannel, Member
from VoiceChat import VoiceChat

#default messaging permissions
intents = discord.Intents.default()

#initialize bot via componentsbot with intents
bot = ComponentsBot(command_prefix=",", intents=intents)
#adds VoiceChat.py as cog
bot.add_cog(VoiceChat(bot))
#reads token
with open("./dontpushtorepo.txt", 'r') as key:
    token = key.readlines()[0]

bot.run(token)