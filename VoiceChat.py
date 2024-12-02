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
from Song import Song
import ffmpeg
import time



#initializing class
class VoiceChat(commands.Cog):
    def __init__(self, bot):
        #bot instance
        self.bot = bot
        #music queue containing song name and file location on local system
        self.pathqueue = Queue()
        self.titlequeue = Queue()
        #paused boolean, important for play() and paused()
        self.paused = False
        #playing boolean
        self.playing = False
        #ffmpeg path in cwd, temporary solution
        self.audiopath = './ffmpeg-2024-07-04-git-03175b587c-full_build/bin'
        self.audioexe = './ffmpeg-2024-07-04-git-03175b587c-full_build/bin/ffmpeg.exe'
        #keeps track of the channel ID the bot is in
        self.channel = {}
        #indicates if the bot has joined a channel
        self.joined = False
        #server ID
        self.id = 0
        #runtime of currently playing track. useful when applying or undo-ing effects so that the bot can remember where it left off
        self.runtime = 0
        #options for yt-dlp. indicates download as mp3, doesn't download playlist links, downloads highest-res audio possible
        self.ytoptions = {'outmpath': './resources', 'noplaylist': 'True', 'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], 'ffmpeg_location': self.audiopath}
        self.ffmpegoptions = {'before_options': 'reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        #audio play
        self.aplay = 0
        self.voicestatus = {}




    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
           self.id = int(guild.id)


        #join voice chat function
    @commands.command(name="join")
    async def voice_join(self, ctx: commands.Context):
        #gets server ID
        self.id = int(ctx.guild.id)
        #if the command author is in a voice channel, 
        # and the bot isn't already in a channel, it will join that channel
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if(self.joined == False):
             #joined set to true, connects to server and sets channel ID
             self.joined = True
             await ctx.send("Connecting..")
             self.channel[id] = await channel.connect()
             path = "https://www.youtube.com/watch?v=-1QSokJSb5A"
             self.channel[id].play(discord.FFmpegPCMAudio(path, executable=self.audioexe))
             print("T")
        else:
            await ctx.send("Please join a voice channel.")

        #leave voice chat function
        #NOTE: voice_leave is not functional. my code refuses to acknowledge the VoiceClient object it needs to disconnect
        #from the channel. Everything up to "await voicechan.disconnect()" works as expected, AFAIK.

    def findChannel(self, bot, voice_channel: discord.VoiceChannel):
            for voice_client in self.bot.voice_clients:
               if voice_client.channel.id == voice_channel.id:
                  return voice_client
        
    @commands.command(name="leave")
    async def voice_leave(self, ctx: commands.Context):
        #if bot is in a voice channel, and isn't playing any songs:
        if ctx.voice_client:
            if(self.paused == False and self.playing == False and self.joined):
                self.joined = False
                channel = ctx.author.voice.channel
                client = self.findChannel(self.bot, channel)
                self.voicestatus = client
                keyguild = ctx.guild
                await ctx.send("Disconnecting..")
                await self.voicestatus.disconnect(force=True)

        else:
            await ctx.send("Failed to leave channel.")
        self.channel = None

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
        #ctx.voice_client.pause(self.aplay)

    @commands.command(name = "unpause")
    async def unpause(self, ctx: commands.Context):
       self.paused = False
       self.playing = True
       #ctx.voice_client.play(self.aplay)

        #play song function
    @commands.Cog.listener()
    async def play(self, ctx: commands.Context):
       id = int(ctx.guild.id)
       #sleeps until current track is done playing
       await ctx.send("INPLAY")
       while(self.joined == True):
         while(self.playing == True):
            time.sleep(1)
       #iterates through the entire queue in order until none are left, sets playing to true
        while(self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize()):
            path = self.pathqueue.get()
            title = self.titlequeue.get()
            self.channel.play(discord.FFmpegPCMAudio(path, executable=self.audioexe))
            await ctx.send("Now Playing: {}".format(title))
            self.playing = True
    

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
             #gets filename
             title = songinfo.get('title', None)
             self.pathqueue.put(url)
             self.titlequeue.put(title)
             await ctx.send("Song Title: {}".format(title))
             if not(self.playing):
              await self.play(ctx)
            except:
             await ctx.send("I can't manage to get the selected track.")
        

