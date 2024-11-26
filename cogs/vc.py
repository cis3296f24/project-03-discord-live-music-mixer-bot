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
import numpy as np
from scipy.fft import fft, fftfreq


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
            ''' "pop()" removes the item from the Queue,so set the global reference using deepcopy first, so no null reference exception is thrown '''
            read_only_copy = copy.deepcopy(self._queue[0]) 
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
            return copy.deepcopy(self._current_song) # Peek() method for Queues is read-only, so we make a copy adhere to that core concept
        raise IndexError("Queue is empty as a result of a call to peek()")
    
    def clear_current(self):
        self._current_song = None

    def prepare_ffmpeg_parse(self)->str:
        #placeholder for now --> implementing more PyDub functionality currently
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


    @commands.command(name="volume")
    async def fx_volume(self, ctx: commands.Context, vol: float):
        try:
            current_song = self.queue.peek()
            extracted_audio = AudioSegment.from_file(current_song.path, format="mp3")
            #await ctx.send(f"BEFORE VOLUME CHANGE the AUDIO DBFS = {extracted_audio.dBFS}")
            assert vol < 1000 
            extracted_audio = extracted_audio + vol
            await ctx.send(f"Volume set to: {vol}")
            #await ctx.send(f"AFTER VOLUME CHANGE the AUDIO DBFS = {extracted_audio.dBFS}")
        except Exception as e:
            await ctx.send(f"Error applying volume effect: {str(e)}")

    @commands.command(name="lowpass")
    async def fx_lowpass_filter(self, ctx: commands.Context, freq: float):
        """
        Analyze frequency content and apply lowpass filter to current audio.
        freq: cutoff frequency in Hz
        """
        try:
            # 1. Get current audio
            current_song = self.queue.peek()
            audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
            
            # 2. Convert to numpy array and normalize
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples / np.iinfo(np.int16).max  # Normalize to [-1, 1]
            
            # 3. Compute FFT
            fft_result = np.fft.rfft(samples)
            freqs = np.fft.rfftfreq(len(samples), 1/audio.frame_rate) 
            
            # 4. Get magnitude spectrum in dB
            # 20 and 1e-10 are arbitrary. Want to convert freq component to magnitude and use log scale since human hering is log based
            magnitudes = 20 * np.log10(np.abs(fft_result) + 1e-10)
            
            # 5. Find top 10 frequencies by magnitude
            peak_indices = np.argsort(magnitudes)[-10:]
            peaks = [(freqs[i], magnitudes[i]) for i in peak_indices]
            
            # 6. Format and send analysis
            analysis = "Dominant frequencies:\n" + "\n".join(
                f"Frequency {freq:.1f} Hz: {mag:.1f} dB" 
                for freq, mag in sorted(peaks, key=lambda x: x[1], reverse=True)
            )
            await ctx.send(f"```{analysis}```")

            # 7. Apply lowpass filter if frequency specified
            if freq > 0:
                try:
                    # Create and apply frequency mask
                    mask = freqs < freq
                    filtered_fft = fft_result * mask

                    # Convert back to time domain
                    filtered = np.real(np.fft.irfft(filtered_fft))
                    filtered = np.int16(filtered * np.iinfo(np.int16).max)

                    # Create filtered audio segment
                    filtered_audio = AudioSegment(
                        filtered.tobytes(),
                        frame_rate=audio.frame_rate,
                        sample_width=2,
                        channels=1
                    )

                    # Use timestamp in filename to ensure uniqueness
                    timestamp = int(time.time())
                    temp_path = f"filtered_{timestamp}.mp3"
                    
                    # Export with error handling
                    try:
                        filtered_audio.export(temp_path, format="mp3")
                    except Exception as e:
                        await ctx.send(f"Error exporting filtered audio: {str(e)}")
                        return

                    # Create new audio source
                    try:
                        new_source = discord.FFmpegPCMAudio(
                            executable="ffmpeg",
                            source=temp_path,
                            options="-loglevel error"  # Reduce FFmpeg output
                        )
                        
                        
                        ctx.voice_client.stop()     # Stop current playback before switching source
                        await asyncio.sleep(0.5)    # Small delay to ensure clean switch
                        
                        #PUT NEW SONG INTO THE QUEUE 
                        # SET THE NEW SONG TO CURRENT_SONG --> SO THAT PAUSE/UNPAUSE WORKS FOR IT




                        # Play new audio
                        
                        ctx.voice_client.play(new_source)
                        await ctx.send(f"Applied {freq}Hz lowpass filter")
                        
                    except Exception as e:
                        await ctx.send(f"Error playing filtered audio: {str(e)}")
                        return
                    
                    finally:
                        # Cleanup in finally block to ensure it runs
                        try:
                            await asyncio.sleep(1)  # Wait a bit before cleanup
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except Exception as e:
                            print(f"Cleanup error: {str(e)}")  # Log but don't send to chat

                except Exception as e:
                    await ctx.send(f"Error in filter application: {str(e)}")

        except Exception as e:
            await ctx.send(f"Error in audio processing: {str(e)}")

    @commands.command(name="highpass")
    async def fx_highpass_filter(self, ctx: commands.Context, freq: float):
        current_song = self.queue.peek()
        extracted_audio = AudioSegment.from_file(current_song.path, format="mp3")
        extracted_audio.high_pass_filter(freq)
        return 1


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
                
                if not os.path.exists(songpath):
                    await ctx.send("Failed to locate the downloaded track.")
                    return
                
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
                

       

            

async def setup(bot):
    await bot.add_cog(vc(bot))