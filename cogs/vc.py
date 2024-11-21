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
import traceback

#ffmpeg path in cwd, temporary solution
audiopath = "./project-03-discord-live-music-mixer-bot/ffmpeg-2024-07-04-git-03175b587c-full_build/bin"

#initializing class
class vc(commands.Cog):
    def __init__(self, bot):
        self.audiopath = os.path.join(".", "project-03-discord-live-music-mixer-bot", "ffmpeg-2024-07-04-git-03175b587c-full_build", "bin")
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
        
        self.quit = True
        #server ID
        self.id = 0
        #runtime of currently playing track. useful when applying or undo-ing effects so that the bot can remember where it left off
        self.runtime = 0
        #options for yt-dlp. indicates download as mp3, doesn't download playlist links, downloads highest-res audio possible
        self.ytoptions = {'outmpath': './resources', 'noplaylist': 'True', 'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], '--ffmpeg-location': audiopath}
        self.ffmpegoptions = {'before_options': 'reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


    @commands.Cog.listener()
    async def on_ready(self):
        while not self.quit:
         
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
            self.channel = await ctx.author.voice.channel.connect()
            #self.channel[id] = channel
        else:
            await ctx.send("Please join a voice channel.")

        #leave voice chat function
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
        if(self.playing):
         await self.channel.pause()
         self.paused = True
         self.playing = False

    @commands.command(name = "unpause")
    async def unpause(self, ctx: commands.Context):
       if(self.paused):
        await self.channel.play()
        self.paused = False
        self.playing = True

        #play song function
   # @commands.Cog.listener()
    #async def play(self, ctx: commands.Context):
       #sleeps until current track is done playing
       #await ctx.send("INPLAY")
       #while(self.joined == True):
         #while(self.playing == True):
           # time.sleep(1)
       #iterates through the entire queue in order until none are left, sets playing to true
        # while(self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize()):
        #    path = self.pathqueue.get()
         #   title = self.titlequeue.get()
         #   aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
          #  self.channel.play(aplay, after=await self.play(ctx))
          #  await ctx.send("Now playing {}".format(title))
          #  self.playing = True
      # await ctx.send("The queue is currently empty.")
        

        #apply effects function, will reference effects cog
    @commands.command(name = "fx")
    async def fx(self, ctx: commands.Context, effect):
        if(self.playing == False):
            ctx.send("Music needs to be playing for effects to be applied.")
        else:
            #effects applied here
            print("Placeholder")

    @commands.command(name = "skip")
    async def skip(self, ctx: commands.Context, effect):
        if(self.playing):
           self.channel.stop()
           self.playing = False

    @commands.command(name = "alive")
    async def alive(self, ctx: commands.Context):
       await ctx.send("I am alive!")


    @commands.Cog.listener()
    async def next(self, ctx: commands.Context, path):
       while(self.channel.is_playing()):
        time.sleep(1)
       #deletes the file in local storage after song is done playing
       try:
        os.remove(path)
       except:
        await ctx.send(traceback.print_exc())
       self.playing = False

        #downloads youtube videos, creates Song object, places object in the queue and sets it to be played 
    @commands.command(name = "play")
    async def play(self, ctx: commands.Context, url):
     if(self.joined == False):
         await ctx.send("I must be in a voice channel to play music!")
     else:
      with yt_dlp.YoutubeDL(self.ytoptions) as youtube:
            try:
             #downloads video metadata
             songinfo = youtube.extract_info(url, download = True)
             songpath = youtube.prepare_filename(songinfo).replace('webm', 'mp3')
             songpath = "./" + songpath
             #gets title from metadata
             title = songinfo.get('title', None)
             #song info put into the queues
             self.titlequeue.put(title)
             self.pathqueue.put(songpath)
             await ctx.send("Song Title: {}".format(title))
             #Stalls here until the previous track is finished
             while(self.playing):
              time.sleep(1)
       #iterates through the entire queue in order until none are left, sets playing to true
             while(self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize()):
              #Gets path and title from queues
              path = self.pathqueue.get()
              title = self.titlequeue.get()
              #Plays with FFmpeg and sets path to queue get() 
              aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
              #Plays song, goes to self.next() to check when the track stops playing
              self.channel.play(aplay, after=await self.next(ctx, path))
              await ctx.send("Now playing {}".format(title))
              self.playing = True
            except:
              await ctx.send("I can't manage to get the selected track.")

async def setup(bot):
    await bot.add_cog(vc(bot))

