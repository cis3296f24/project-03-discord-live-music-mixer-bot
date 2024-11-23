from discord.ext import commands
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
import yt_dlp
from queue import Queue
import os
from dataclasses import dataclass
from typing import List

@dataclass
class Song:
    title: str
    path: str
    url: str
    order: int  # to track insertion order to maintain priority inside the queue

class OrderedQueue:
    def __init__(self):
        self._queue: List[Song] = []
        self._counter = 0

    def put(self, song: Song):
        song.order = self._counter
        self._counter += 1
        self._queue.append(song)
        self._queue.sort(key=lambda x: x.order)  # Keep songs sorted by order. Upon inserting into queue sorts all songs by priority/order

    def get(self) -> Song:
        if not self.empty():
            return self._queue.pop(0)
        raise IndexError("Queue is empty")

    def empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)

class vc(commands.Cog):
    def __init__(self, bot):
        self.audiopath = os.path.join(".", "project-03-discord-live-music-mixer-bot", "C:\\ffmpeg")        
        self.bot = bot
        self.queue = OrderedQueue()  # Using our custom OrderedQueue
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
        
        if self.queue.empty():
            await ctx.send("The queue is now empty.")
            return
        else:
            next_song = self.queue.get()
            await self.play(ctx, next_song.url)

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
                
                # Create new Song object and add to ordered queue
                song = Song(title, songpath, url, 0)  # Order will be set by OrderedQueue
                self.queue.put(song)
                await ctx.send("Song Title: {}".format(title))

                # Wait if something is already playing
                while self.playing:
                    await asyncio.sleep(1)

                # Process queue
                while not self.queue.empty():
                    current_song = self.queue.get()
                    aplay = discord.FFmpegPCMAudio(executable="ffmpeg", source=current_song.path)
                    self.playing = True
                    self.played = True
                    ctx.voice_client.play(aplay)
                    await ctx.send("Now playing {}".format(current_song.title))

                    # Wait for the track to complete
                    while ctx.voice_client.is_playing() or self.paused:
                        await asyncio.sleep(1)
                        
                    self.playing = False
                    self.played = False
                    self.paused = False
                    os.remove(current_song.path)
                    
            except Exception as e:
                if self.played:
                    await ctx.send("My audio stream was interrupted!")
                else:
                    await ctx.send("I can't manage to get the selected track.")

async def setup(bot):
    await bot.add_cog(vc(bot))