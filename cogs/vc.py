from discord.ext import commands
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
import yt_dlp
from queue import Queue
import os
from dataclasses import dataclass
from typing import List, Optional
import ffmpeg
import time
import traceback
from pydub import AudioSegment
from pydub.playback import play
import copy

@dataclass
class Song:
    title: str
    path: str
    url: str
    order: int  # to maintain assigned song priorities inside the queue

class OrderedQueue:
    def __init__(self):
        self._queue: List[Song] = []
        self._counter = 0
        self._current_song: Song = None  
    def put(self, song: Song):
        song.order = self._counter  # Assign each song an priority upon being put inside the queue
        self._counter += 1          # Song 1 = Priority 0 / Song 2 = Priority 1 / etc...
        self._queue.append(song)
        self._queue.sort(key=lambda x: x.order)  # Keep songs sorted by their assigned order. Upon inserting into queue sorts the new queue by order

    def get(self) -> Song:
        if not self.empty():
            read_only_copy = copy.deepcopy(self._queue[0]) # Peek doesn't exist in Python for some reason. Deepcopy implementation so peek() function works
            self._current_song = read_only_copy
            curr_song = self._queue.pop()
            return curr_song
        raise IndexError("Queue is empty as a result of a call to get()")

    def empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)
    
    def peek(self) -> Song:
        if self._current_song is not None:
            return copy.deepcopy(self._current_song)
        raise IndexError("Queue is empty as a result of a call to peek()")
    
    def clear_current(self):
        self._current_song = None

    def prepare_ffmpeg_parse(self)->str:
        #placeholder for now --> implementing more PyDub functionality
        return 1
        

class vc(commands.Cog):
    def __init__(self, bot):
        self.audiopath = os.path.join(".", "project-03-discord-live-music-mixer-bot", "C:\\ffmpeg")        
        self.bot = bot
        self.queue = OrderedQueue()  # custom OrderedQueue class
        self.paused = False
        self.playing = False
        self.channel = {}
        self.joined = False
        self.played = True
        self.id = 0
        
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


    # Pydub Volume Manipulation
    @commands.command(name="volume")
    async def fx_volume(self, ctx: commands.Context, vol: float):
        """Wrapper method that uses the façade to apply volume filter"""
        try:
            current_song = self.queue.peek()
            extracted_audio = AudioSegment.from_file(current_song.path, format="mp3")
            await ctx.send(f"BEFORE VOLUME CHANGE the AUDIO DBFS = {extracted_audio.dBFS}")
            extracted_audio = extracted_audio + vol
            await ctx.send(f"Volume set to: {vol}")
            await ctx.send(f"AFTER VOLUME CHANGE the AUDIO DBFS = {extracted_audio.dBFS}")
        except Exception as e:
            await ctx.send(f"Error applying volume effect: {str(e)}")

    # Pydub 

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

                song = Song(title, songpath, url, 0)  # Order will be set by OrderedQueue
                self.queue.put(song)
                await ctx.send("Song Title: {}".format(title))

                # Wait if something is already playing
                while self.playing:
                    await asyncio.sleep(1)

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