from discord_components import Select, SelectOption, Button
from discord.ext import commands
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from youtube_dl import YoutubeDL

class VoiceChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.index = 0
        self.paused = False
        self.playing = False
        self.channel = {}
        self.joined = False
        self.id = 0

    @commands.Cog.listener()
    async def define(self):
        print("T")

    @commands.command(name="test")
    async def initial(self, ctx: commands.Context):
        await ctx.send("Test.")


    @commands.command(name="join")
    async def voice_join(self, ctx: commands.Context):
        self.id = int(ctx.guild.id)
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if(self.joined == False):
             self.joined = True
             await ctx.send("Connecting..")
             self.channel[id] = await channel.connect()
             print(self.channel[id])
        else:
            await ctx.send("Please join a voice channel.")

    @commands.command(name="leave")
    async def voice_leave(self, ctx: commands.Context):
        if ctx.voice_client:
            if(self.paused == False and self.playing == False and self.joined):
                self.joined = False
                channel = ctx.author.voice.channel
                keyguild = ctx.guild
                for client in self.bot.voice_clients:
                    voicechan = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                    print(voicechan)
                    await ctx.send("Disconnecting..")
                    await voicechan.disconnect()
        else:
            await ctx.send("Failed to leave channel.")
        self.channel = None

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        self.playing = False
        self.paused = False

    @commands.command(name = "pause")
    async def pause(self, ctx: commands.Context):
        self.paused = True
        self.playing = False

    @commands.command(name = "play")
    async def play(self, url):
        print("Placeholder")


    @commands.command(name = "fx")
    async def fx(self, effect):
        print("Placeholder")

    