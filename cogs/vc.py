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
from pydub import AudioSegment, audio_segment
from pydub.effects import *
from pydub.playback import play
import copy
import numpy as np
from scipy.fft import fft, fftfreq
from pydub.utils import which
import shutil


@dataclass
class FilteredSong:
    forder: int
    fpath: str 

class FilteredAudioQueue:
    def __init__(self):
        self.filtered_queue: List[FilteredSong] = []
        self.fcounter = 0
        self.fcurrent_song: FilteredSong = None

    def put(self, audio: FilteredSong):
        audio.forder = self.fcounter  
        self.fcounter += 1          
        self.filtered_queue.append(audio)
        self.filtered_queue.sort(key=lambda x: x.forder) 


    def get(self) -> FilteredSong:
        if not self.empty():
            read_only_copy = copy.deepcopy(self.filtered_queue[0]) 
            self.fcurrent_song = read_only_copy
            curr_song = self.filtered_queue.pop()                   
            return curr_song
        raise IndexError("Queue is empty as a result of a call to get()")
    

    def peek(self) -> FilteredSong:
        if self.fcurrent_song is not None:
            return copy.deepcopy(self.fcurrent_song)
        raise IndexError("Queue is empty as a result of a call to peek()")


    def empty(self) -> bool:
        return len(self.filtered_queue) == 0
        

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
        self.audiopath = os.path.join("./ffmpeg-2024-07-04-git-03175b587c-full_build/bin/ffmpeg.exe")        
        self.bot = bot
        self.queue = OrderedQueue()  # custom OrderedQueue class
        self.fqueue = FilteredAudioQueue()
        self.paused = False
        self.playing = False
        self.channel = {}
        self.joined = False
        self.played = True
        self.id = 0
        self.undocall = ""
        self.start_time = 0
        self.currentpath = ""
        self.ffmpegoptions = {
        'before_options': f'-ss {self.start_time}',  # Seek to the start_time (in seconds)
        'options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }
        self.ytoptions = {
            'outmpath': './resources',
            'noplaylist': 'True',
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'
            }],
            '--ffmpeg-location': "./ffmpeg-2024-07-04-git-03175b587c-full_build/bin"
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
                        foptions = {'before_options': f'-ss {self.start_time}' }
                        new_source = discord.FFmpegPCMAudio(
                            temp_path, **foptions # Reduce FFmpeg output
                        )
                        
                        
                        ctx.voice_client.stop()     # Stop current playback before switching source
                        await asyncio.sleep(0.5)    # Small delay to ensure clean switch
                        
                        # (1) I have FFMPEG executable from PCM Audio & (2) The Path --> (3) Put into queue, play the song
                        #(4) Utilize the SAME play() global boolean state variables so we ENFORCE that 1 song plays at 1 time & 
                        #                   so that we recognize the filtered Song as a Song
                        self.fqueue.put(new_source)
                        while not self.fqueue.empty():
                            self.playing = True
                            self.played = True
                            self.channel.play(new_source)
                            await ctx.send(f"Applied {freq}Hz lowpass filter")
                            
                            # Wait for the track to complete
                        while ctx.voice_client.is_playing() or self.paused:
                            if not self.paused:
                                self.start_time+=1
                                print(self.start_time)
                            await asyncio.sleep(1)
                            
                        self.playing = False
                        self.played = False
                        self.paused = False   
                        os.remove(temp_path)
                        #ctx.voice_client.play(new_source)
                        #await ctx.send(f"Applied {freq}Hz lowpass filter")
                        
                    except Exception as e:
                        if self.played:
                            await ctx.send("IGNORE THIS ERROR!My FILTERED audio stream was interrupted!")
                    
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
    @commands.command(name="undo")
    async def undo(self, ctx: commands.Context):
        #sets options for new call to play audio
        #if original file was somehow removed
         if not os.path.exists(self.undocall):
            await ctx.send("Original stream no longer exists!")
         foptions = {'before_options': f'-ss {self.start_time}' }
         new_source = discord.FFmpegPCMAudio(self.undocall, **foptions) # Reduce FFmpeg output
         ctx.voice_client.stop()     # Stop current playback before switching source
         await asyncio.sleep(0.5)
         self.fqueue.put(new_source)
         #plays original track with archived path, assuming it still exists
         while not self.fqueue.empty():
            self.playing = True
            self.played = True
            self.channel.play(new_source)
            await ctx.send(f"Effect(s) successfully undone, returned to original track")

         while ctx.voice_client.is_playing():
            if not self.paused:
                self.start_time+=1
                print(self.start_time)
                await asyncio.sleep(1)
                            
         self.playing = False
         self.played = False
         self.paused = False   
         os.remove(self.undocall)
                        
         return 0

    @commands.command(name="highpass")
    async def fx_highpass_filter(self, ctx: commands.Context, freq: float):

        #grab audio file
        audio = AudioSegment.from_file(self.currentpath, format ="mp3")
        #create new HPF version
        try:
         new_audio = high_pass_filter(audio, cutoff = freq)
        except Exception as e:
            await ctx.send(f"Error exporting filtered audio: {str(e)}")
        #turn into numpy array
        samples = np.array(new_audio.get_array_of_samples())
        #convert BACK into an AudioSegment
        try:
         filtered_audio = AudioSegment(
          samples.tobytes(),
          frame_rate=audio.frame_rate,
          sample_width=audio.sample_width,
          channels=audio.channels
         )
        except Exception as e:
            await ctx.send(f"Error exporting filtered audio: {str(e)}")

        timestamp = int(time.time())
        #Set title of file to be unique based on int time
        path = f"filtered_{timestamp}.mp3"
        try:
        #FINALLY export that last object as a file .mp3
            filtered_audio.export(path, format="mp3")
        except Exception as e:
            await ctx.send(f"Error exporting filtered audio: {str(e)}")
            return
        
        foptions = {'before_options': f'-ss {self.start_time}' }
        new_source = discord.FFmpegPCMAudio(
        path, **foptions) # Reduce FFmpeg output
        
        ctx.voice_client.stop()     # Stop current playback before switching source
        await asyncio.sleep(0.5)
        self.fqueue.put(new_source)
        while not self.fqueue.empty():
            self.playing = True
            self.played = True
            self.channel.play(new_source)
            await ctx.send(f"Applied {freq}Hz highpass filter")

        while ctx.voice_client.is_playing():
            if not self.paused:
                self.start_time+=1
                print(self.start_time)
                await asyncio.sleep(1)
                            
        self.playing = False
        self.played = False
        self.paused = False   
        os.remove(path)
                        
        return 1

    @commands.command(name="pitchshift")
    async def pitch_shift(self, ctx: commands.Context, semitones: float):
        """
        Adjust the pitch of the current track by a number of semitones.
        Positive values increase pitch, negative values decrease pitch.
        """
        try:
            if not ctx.voice_client or not self.playing:
                await ctx.send("I'm not playing anything right now!")
                return
            # Get the currently playing song from the queue
            current_song = self.queue.peek()
            audio = AudioSegment.from_file(current_song.path, format="mp3")

            # Calculate the new sample rate
            new_sample_rate = int(audio.frame_rate * (2 ** (semitones / 12.0)))

            # Apply pitch shift by changing the frame rate
            shifted_audio = audio.spawn(
                audio.raw_data, overrides={'frame_rate': new_sample_rate}
            )

            # Resample back to the original frame rate to maintain playback speed
            resampled_audio = shifted_audio.set_frame_rate(audio.frame_rate)

            # Create a temporary file
            temp_path = f"shifted{int(time.time())}.mp3"
            resampled_audio.export(temp_path, format="mp3")

            # Stop the current playback and play the pitch-shifted track
            ctx.voice_client.stop()
            self.playing = True
            ctx.voice_client.play(discord.FFmpegPCMAudio(temp_path))

            # Notify the user
            await ctx.send(f"Applied pitch shift of {semitones} semitones.")

            # Wait for playback to finish and clean up
            while ctx.voice_client.is_playing():
                await asyncio.sleep(1)

            self.playing = False
            os.remove(temp_path)
        except Exception as e:
            await ctx.send(f"Error applying pitch shift: {str(e)}")


    @commands.command(name="highend")
    async def boosthigh(self, ctx: commands.Context, freq: float):
        try:
            current_song = self.queue.peek()
            #adds filtered audio back to original audiosegment
            audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
            lowend = high_pass_filter(audio, cutoff=freq)
            newaudio = audio + lowend

        except Exception as e:
                    await ctx.send(f"EQ Treble Boost Error: {str(e)}")
        return
        return



    @commands.command(name="normalize")
    async def normalize(self, ctx: commands.Context):
        current_song = self.queue.peek()
        audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
        #call normalize function
        new_audio = normalize(audio)
        #convert to numpy then back into audiosegment
        samples = np.array(new_audio.get_array_of_samples())
        try:
          normalized = AudioSegment(
          samples.tobytes(),
          frame_rate=audio.frame_rate,
          sample_width=audio.sample_width,
          channels=audio.channels
         )
        except Exception as e:
            await ctx.send(f"Error exporting normalized audio: {str(e)}")
        timestamp = int(time.time())
        #Set title of file to be unique based on int time
        path = f"norm_{timestamp}.mp3"
        try:
        #FINALLY export that last object as a file .mp3
            normalized.export(path, format="mp3")
        except Exception as e:
            await ctx.send(f"Error exporting normalized audio: {str(e)}")
            return
        foptions = {'before_options': f'-ss {self.start_time}' }
        new_source = discord.FFmpegPCMAudio(
        path, **foptions) # Reduce FFmpeg output

        ctx.voice_client.stop()     # Stop current playback before switching source
        await asyncio.sleep(0.5)
        self.fqueue.put(new_source)
        while not self.fqueue.empty():
            self.playing = True
            self.played = True
            self.channel.play(new_source)
            await ctx.send(f"Normalized Audio")

        while ctx.voice_client.is_playing():
            if not self.paused:
                self.start_time+=1
                print(self.start_time)
                await asyncio.sleep(1)
                            
        self.playing = False
        self.played = False
        self.paused = False   
        os.remove(path)


        return

    @commands.command(name="pan")
    async def pan(self, ctx: commands.Context, val: float):
        if(val > 1 or val < -1):
            await ctx.send(f"Value is too big. Pan value must be between -1 and 1.")
            return
        current_song = self.queue.peek()
        audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
        newaudio = pan(audio, val)
        print("APPLIED")
        samples = np.array(newaudio.get_array_of_samples())
        try:
         panned_audio = AudioSegment(
          samples.tobytes(),
          frame_rate=audio.frame_rate,
          sample_width=audio.sample_width,
          channels=audio.channels
         )
        except Exception as e:
            await ctx.send(f"Error exporting panned audio: {str(e)}")

        timestamp = int(time.time())
        #Set title of file to be unique based on int time
        path = f"pan_{timestamp}.mp3"
        try:
        #FINALLY export that last object as a file .mp3
            panned_audio.export(path, format="mp3")
        except Exception as e:
            await ctx.send(f"Error exporting panned audio: {str(e)}")
            return
        foptions = {'before_options': f'-ss {self.start_time}' }
        new_source = discord.FFmpegPCMAudio(
        path, **foptions) # Reduce FFmpeg output

        ctx.voice_client.stop()     # Stop current playback before switching source
        await asyncio.sleep(0.5)
        self.fqueue.put(new_source)
        while not self.fqueue.empty():
            self.playing = True
            self.played = True
            self.channel.play(new_source)
            await ctx.send(f"Applied {val} step audio panning")

        while ctx.voice_client.is_playing():
            if not self.paused:
                self.start_time+=1
                print(self.start_time)
                await asyncio.sleep(1)
                            
        self.playing = False
        self.played = False
        self.paused = False   
        os.remove(path)

        return
    



    @commands.command(name="gain")
    async def gain(self, ctx: commands.Context, freq: float):
        current_song = self.queue.peek()
        audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
        new_audio = audio + freq
        samples = np.array(new_audio.get_array_of_samples())
        try:
         gain_audio = AudioSegment(
          samples.tobytes(),
          frame_rate=audio.frame_rate,
          sample_width=audio.sample_width,
          channels=audio.channels
         )
        except Exception as e:
            await ctx.send(f"Error applying gain: {str(e)}")

        timestamp = int(time.time())
        #Set title of file to be unique based on int time
        path = f"gain_{timestamp}.mp3"
        try:
        #FINALLY export that last object as a file .mp3
            gain_audio.export(path, format="mp3")
        except Exception as e:
            await ctx.send(f"Error applying gain: {str(e)}")
            return
        foptions = {'before_options': f'-ss {self.start_time}' }
        new_source = discord.FFmpegPCMAudio(
        path, **foptions) # Reduce FFmpeg output

        ctx.voice_client.stop()     # Stop current playback before switching source
        await asyncio.sleep(0.5)
        self.fqueue.put(new_source)
        while not self.fqueue.empty():
            self.playing = True
            self.played = True
            self.channel.play(new_source)
            await ctx.send(f"Applied {freq}step gain")

        while ctx.voice_client.is_playing():
            if not self.paused:
                self.start_time+=1
                print(self.start_time)
                await asyncio.sleep(1)
                            
        self.playing = False
        self.played = False
        self.paused = False   
        os.remove(path)

        return

    @commands.command(name="lowend")
    async def boostlow(self, ctx: commands.Context, freq: float):
        try:
            current_song = self.queue.peek()
            #adds filtered audio back to original audiosegment
            audio = AudioSegment.from_file(current_song.path, format="mp3").set_channels(1)
            lowend = low_pass_filter(audio, cutoff=freq)
            newaudio = audio+lowend

        except Exception as e:
                    await ctx.send(f"EQ bass boost Error: {str(e)}")
        return
    
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
            self.channel.pause()
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
            self.channel.resume()
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
                songpath = youtube.prepare_filename(songinfo)
                #replace m4a with mp3 for songptah
                songpath = "./" + songpath.replace('m4a', 'mp3') 
                songpath = "./" + songpath.replace('webm', 'mp3')
                ffpath = which("ffmpeg")
                print(ffpath)
                self.currentpath = songpath
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
                    #keeps track of original file if users want to undo effects
                    self.undocall = current_song.path
                    ctx.voice_client.play(aplay)
                    await ctx.send("Now playing {}".format(current_song.title))

                    # Wait for the track to complete
                    while ctx.voice_client.is_playing() or self.paused:
                        if not self.paused:
                            self.start_time += 1
                            print(self.start_time)
                        await asyncio.sleep(1)
                        
                    self.playing = False
                    self.played = False
                    self.paused = False
                    self.runtime = 0
                    os.remove(current_song.path)
                    
            except Exception as e:
                if self.played:
                    await ctx.send("My audio stream was interrupted!")
                

       

            

async def setup(bot):
    await bot.add_cog(vc(bot))