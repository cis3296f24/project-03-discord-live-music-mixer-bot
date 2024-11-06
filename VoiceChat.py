import os
import discord
import ffmpeg
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import pyaudio
from youtube_dl import *
from urllib import *
import asyncio
from asyncio import run_coroutine_threadsafe

class VoiceChat(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def define(self):
        for guild in self.bot.guilds:
            id = int(guild.id)


    @commands.command(name="test")
    async def initial(self, ctx):
        id = int(ctx.guild.id)
        await ctx.send("Test.")


    @commands.command(name="join")
    async def voice_join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("Please join a voice channel.")

    @commands.command(name="leave")
    async def voice_leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("Failed to leave channel.")