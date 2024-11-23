from discord.ext import commands
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
import yt_dlp
from queue import Queue
import os

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
        self.channel = {}
        self.joined = False
        self.played = True
        self.quit = True
        self.id = 0
        self.runtime = 0
        self.ytoptions = {
            'outmpath': './resources',
            'noplaylist': 'True',
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }],
            '--ffmpeg-location': "C:\\ffmpeg"
        }
        self.ffmpegoptions = {
            'before_options': 'reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

    @commands.command(name="join")
    async def voice_join(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.send("Already Connected to Voice Channel")
            return

        self.id = int(ctx.guild.id)
        if ctx.author.voice:
            self.joined = True
            await ctx.send("Connecting..")
            self.channel = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Please join a voice channel.")

    @commands.command(name="leave")
    async def voice_leave(self, ctx: commands.Context):
        if ctx.voice_client:
            try:
                # Clear all flags when leaving
                self.joined = False
                self.playing = False
                self.paused = False
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from Voice Channel")
            except Exception as e:
                await ctx.send("Disconnection Error")
        else:
            await ctx.send("Not in Voice Channel")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        if self.playing and not self.paused:
            ctx.voice_client.pause()
            self.paused = True
            await ctx.send("Paused the current track")
        elif self.paused:
            await ctx.send("The track is already paused!")
        else:
            await ctx.send("Nothing is playing right now!")

    @commands.command(name="unpause")
    async def unpause(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
        if self.paused:
            ctx.voice_client.resume()
            self.paused = False
            await ctx.send("Resumed the track")
        else:
            await ctx.send("The track is not paused!")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        if not self.playing:
            await ctx.send("Nothing is playing right now!")
            return
            
        ctx.voice_client.stop()
        self.playing = False
        self.paused = False
        
        if self.pathqueue.qsize() == 0:
            await ctx.send("The queue is now empty.")
            return
        else:
            title = self.titlequeue.get()
            path = self.pathqueue.get()
            await self.play(ctx, self.urlqueue.get())

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, url):
        if not self.joined:
            await ctx.send("I must be in a voice channel to play music!")
            return
            
        with yt_dlp.YoutubeDL(self.ytoptions) as youtube:
            try:
                songinfo = youtube.extract_info(url, download=True)
                songpath = youtube.prepare_filename(songinfo).replace('webm', 'mp3')
                songpath = "./" + songpath
                title = songinfo.get('title', None)
                
                self.titlequeue.put(title)
                self.pathqueue.put(songpath)
                self.urlqueue.put(url)
                await ctx.send("Song Title: {}".format(title))

                # Wait if something is already playing
                while self.playing:
                    await asyncio.sleep(1)

                # Process queue
                while self.pathqueue.qsize() > 0 and self.pathqueue.qsize() == self.titlequeue.qsize():
                    path = self.pathqueue.get()
                    title = self.titlequeue.get()
                    url = self.urlqueue.get()

                    aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
                    self.playing = True
                    self.played = True
                    ctx.voice_client.play(aplay)
                    await ctx.send("Now playing {}".format(title))

                    # Wait for the track to complete
                    while ctx.voice_client.is_playing() or self.paused:
                        await asyncio.sleep(1)
                        
                    self.playing = False
                    self.played = False
                    self.paused = False
                    os.remove(path)
                    
            except Exception as e:
                if self.played:
                    await ctx.send("My audio stream was interrupted!")
                else:
                    await ctx.send("I can't manage to get the selected track.")

async def setup(bot):
    await bot.add_cog(vc(bot))