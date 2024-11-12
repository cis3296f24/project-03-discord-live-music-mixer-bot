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
import yt_dlp
from queue import Queue
from Song import Song
import ffmpeg


#initializing class
class VoiceChat(commands.Cog):
    def __init__(self, bot):
        #bot instance
        self.bot = bot
        #music queue containing song name and file location on local system
        self.queue = Queue()
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
        #options for yt-dlp. indicates download as mp3, doesn't download playlist links, downloads highest-res audio possible
        self.ytoptions = {'outmpath': './resources', 'noplaylist': 'True', 'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], 'ffmpeg_location': './ffmpeg-2024-07-04-git-03175b587c-full_build/bin'}
        self.ffmpegoptions = {'before_options': 'reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    @commands.Cog.listener()
    async def on_ready(self):
        print("placeholder")


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
        else:
            await ctx.send("Please join a voice channel.")

        #leave voice chat function
        #NOTE: voice_leave is not functional. my code refuses to acknowledge the VoiceClient object it needs to disconnect
        #from the channel. Everything up to "await voicechan.disconnect()" works as expected, AFAIK.
    @commands.command(name="leave")
    async def voice_leave(self, ctx: commands.Context):
        #if bot is in a voice channel, and isn't playing any songs:
        if ctx.voice_client:
            if(self.paused == False and self.playing == False and self.joined):
                self.joined = False
                channel = ctx.author.voice.channel
                keyguild = ctx.guild
                #searches all channels the bot is in for the one that matches server ID, disconnects from it
                for client in self.bot.voice_clients:
                    voicechan = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                    print(voicechan)
                    await ctx.send("Disconnecting..")
                    await voicechan.disconnect()
        else:
            await ctx.send("Failed to leave channel.")
        self.channel = None

        #stop song playing function
    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
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
       while(self.queue.qsize() == 0):
          s = self.queue.get()
          #s.link.play()
        


    @commands.command(name = "fx")
    async def fx(self, ctx: commands.Context, effect):
        if(self.playing == False):
            ctx.send("Music needs to be playing for effects to be applied.")
        else:
            print("Placeholder")


    def queuekeep(self, size):
       print("T")


    @commands.command(name = "get")
    async def get(self, ctx: commands.Context, url):
     if(self.joined == False):
         await ctx.send("I must be in a voice channel to play music!")
     else:
      with yt_dlp.YoutubeDL(self.ytoptions) as youtube:
            try:
             songinfo = youtube.extract_info(url, download = True)
             songpath = youtube.prepare_filename(songinfo)
             print(songpath)
             songpath = "./" + songpath
             title = songinfo.get('title', None)
             #new song object made from downloaded video put into the queue
             self.queue.put(Song(title,songpath))
             print("SS")
             await ctx.send("Song Title: {}".format(title))
             self.play(self, ctx)
             
            except:
             await ctx.send("I can't manage to get the selected video.")
        
    