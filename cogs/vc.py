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
#audiopath = "./project-03-discord-live-music-mixer-bot/ffmpeg-2024-07-04-git-03175b587c-full_build/bin"
audiopath = "C:\\ffmpeg"

#initializing class
class vc(commands.Cog):
    def __init__(self, bot):
        self.audiopath = os.path.join(".", "project-03-discord-live-music-mixer-bot", "C:\\ffmpeg")        
        self.bot = bot
        self.pathqueue = Queue()
        self.titlequeue = Queue()
        self.urlqueue = Queue()
        self.index = 0
        self.paused = False
        self.playing = False
        self.channel = {}               #keeps track of the channel ID the bot is in
        self.joined = False             #indicates if the bot has joined a channel
        self.played = True
        self.quit = True
        self.id = 0                     #server ID
        self.runtime = 0                #runtime of currently playing track. useful when applying or undo-ing effects so that the bot can remember where it left off
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
                self.playing = False
                self.paused = False
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from Voice Channel")

            except Exception as e:
                await ctx.send("Disconnection Error")
        else:
            await ctx.send("Not in Voice Channel")

    @commands.command(name = "pause")
    async def pause(self, ctx: commands.Context):
        if(self.playing):
         self.channel.pause()
         self.paused = True
         self.playing = False

    @commands.command(name = "unpause")
    async def unpause(self, ctx: commands.Context):
       if(self.paused):
        self.channel.resume()
        self.paused = False
        self.playing = True

        #apply effects function, will reference effects cog
    @commands.command(name = "fx")
    async def fx(self, ctx: commands.Context, effect):
        if(self.playing == False):
            ctx.send("Music needs to be playing for effects to be applied.")
        else:
            #effects applied here
            print("Placeholder")

    @commands.command(name = "skip")
    async def skip(self, ctx: commands.Context):
        if(self.playing):
           #stops audio and sets playing to false
           self.channel.stop()
           self.playing = False
           #leaves here if queue is empty
           if(self.pathqueue.qsize() == 0):
              await ctx.send("The queue is now empty.")
              return
           else:
              #grabs info from nearest queue get and puts it back into play
              title = self.titlequeue.get()
              path = self.pathqueue.get()
              await self.play(ctx, self.urlqueue.get())

    @commands.command(name = "alive")
    async def alive(self, ctx: commands.Context):
       await ctx.send("I am alive!")



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
             self.urlqueue.put(url)
             await ctx.send("Song Title: {}".format(title))
             #Stalls here until the previous track is finished
             while(self.playing):
              await asyncio.sleep(1)
       #iterates through the entire queue in order until none are left, sets playing to true
             while(self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize()):
              #Gets path and title from queues
              path = self.pathqueue.get()
              title = self.titlequeue.get()
              url = self.urlqueue.get()
              #Plays with FFmpeg and sets path to queue get() 
              aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
              #Plays song, goes to self.next() to check when the track stops playing
              self.playing = True
              self.played = True
              self.channel.play(aplay)
              await ctx.send("Now playing {}".format(title))
              #waits for the track to complete
              while(self.channel.is_playing()):
                 #print("T")
                 await asyncio.sleep(1)
              self.playing = False
              self.played = False
              os.remove(path)
            except:
              #tests if it's interrupted
              if(self.played):
                 await ctx.send("My audio stream was interrupted!")
              else:
                 await ctx.send("I can't manage to get the selected track.")

async def setup(bot):
    await bot.add_cog(vc(bot))

