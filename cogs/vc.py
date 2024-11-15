#cogs/vc.py
from discord.ext import commands
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
import yt_dlp
from queue import Queue
import ffmpeg
import time

#ffmpeg path in cwd, temporary solution
audiopath = './ffmpeg-2024-07-04-git-03175b587c-full_build/bin'

#initializing class
class vc(commands.Cog):
    def __init__(self, bot):
        #bot instance
        self.bot = bot
        #music queue containing song name and file location on local system
        self.pathqueue = Queue()
        self.titlequeue = Queue()
        self.index = 0
        #paused boolean, important for play() and paused()
        self.paused = False
        #playing boolean
        self.playing = False
        #keeps track of the channel ID the bot is in
        self.channel = {}
        #indicates if the bot has joined a channel
        self.joined = False
        #server ID
        self.id = 0
        #runtime of currently playing track. useful when applying or undo-ing effects so that the bot can remember where it left off
        self.runtime = 0
        #options for yt-dlp. indicates download as mp3, doesn't download playlist links, downloads highest-res audio possible
        self.ytoptions = {'outmpath': './resources', 'noplaylist': 'True', 'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], 'ffmpeg_location': audiopath}
        self.ffmpegoptions = {'before_options': 'reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


    @commands.Cog.listener()
    async def on_ready(self):
        print("placeholder")


        #join voice chat function
    @commands.command(name="join")
    async def voice_join(self, ctx: commands.Context):

        if ctx.voice_client:
            await ctx.send("Already Connected to Voice Channel")
            return

        #gets server ID
        self.id = int(ctx.guild.id)
        if ctx.author.voice:
            #joined set to true, connects to server and sets channel ID
            self.joined = True
            await ctx.send("Connecting..")
            channel = await ctx.author.voice.channel.connect()
            self.channel[id] = channel
        else:
            await ctx.send("Please join a voice channel.")

        #leave voice chat function
        #NOTE: voice_leave is not functional. my code refuses to acknowledge the VoiceClient object it needs to disconnect
        #from the channel. Everything up to "await voicechan.disconnect()" works as expected, AFAIK.
    @commands.command(name="leave")
    async def voice_leave(self, ctx: commands.Context):
        #if bot is in a voice channel, and isn't playing any songs:

        if ctx.voice_client:
            try:
                self.joined = False
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from Voice Channel")

            except Exception as e:
                await ctx.send("Disconnection Error")
        else:
            await ctx.send("Not in Voice Channel")

        #stop song playing function
    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        self.playing = False
        self.paused = False

        #pause song function
    @commands.command(name = "pause")
    async def pause(self, ctx: commands.Context):
        self.paused = True
        self.playing = False

    @commands.command(name = "unpause")
    async def unpause(self, ctx: commands.Context):
       self.paused = False
       self.playing = True

        #play song function
    @commands.Cog.listener()
    async def play(self, ctx: commands.Context):
       #sleeps until current track is done playing
       await ctx.send("INPLAY")
       while(self.joined == True):
         while(self.playing == True):
            time.sleep(1)
       #iterates through the entire queue in order until none are left, sets playing to true
         while(self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize()):
            path = self.pathqueue.get()
            title = self.titlequeue.get()
            aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
            self.channel[id].play(aplay)
            await ctx.send("Now playing {}".format(title))
            self.playing = True
        

        #apply effects function, will reference effects cog
    @commands.command(name = "fx")
    async def fx(self, ctx: commands.Context, effect):
        if(self.playing == False):
            ctx.send("Music needs to be playing for effects to be applied.")
        else:
            #effects applied here
            print("Placeholder")

    

        #downloads youtube videos, creates Song object, places object in the queue and sets it to be played 
    @commands.command(name = "get")
    async def get(self, ctx: commands.Context, url):
     if(self.joined == False):
         await ctx.send("I must be in a voice channel to play music!")
     else:
      with yt_dlp.YoutubeDL(self.ytoptions) as youtube:
            try:
             #downloads video and metadata, converts to MP3
             songinfo = youtube.extract_info(url, download = False)

             #gets title from metadata
             title = songinfo.get('title', None)
             #new song object made from downloaded video put into the queue
             self.titlequeue.put(title)
             self.pathqueue.put(url)
             await ctx.send("Song Title: {}".format(title))
             if not(self.playing):
              await self.play(ctx)
            except:
             await ctx.send("I can't manage to get the selected track.")

async def setup(bot):
    await bot.add_cog(vc(bot))

