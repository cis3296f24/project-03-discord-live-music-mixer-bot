
import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from discord.ext import commands
import ffmpeg
import subprocess  # Equivalent to forking a process to create a child process. Mimics ffmpeg cmdline parsing of files
from pydub import AudioSegment
import os

# Effects class inherits VoiceChat class, can check all its booleans, queues, etc
class fx(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Temporary directory for processed audio
        self.temp_dir = "./temp_audio"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)  # Create the folder if it doesn't exist

    async def process_audio(self, ctx, effect_name, effect_function, *args):
        """Generic function to process audio with a given effect"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.send("I'm not in a voice channel or no audio is playing!")
                return

            # Get the currently playing song
            current_song = ctx.voice_client.source
            original_path = current_song.source  # Assumes the source is a file path
            new_path = os.path.join(self.temp_dir, f"{effect_name}.mp3")

            # Apply the effect using Pydub
            audio = AudioSegment.from_file(original_path)
            processed_audio = effect_function(audio, *args)
            processed_audio.export(new_path, format="mp3")

            # Play the processed audio
            ctx.voice_client.stop()
            ctx.voice_client.play(discord.FFmpegPCMAudio(new_path))
            await ctx.send(f"{effect_name} Effect Applied.")
        except Exception as e:
            await ctx.send(f"Error applying {effect_name}: {e}")

    # EQ class allows for high-low frequency adjustments. eqlow will specifically boost lower frequencies (bass boost, 808s, etc)
    @commands.command(name="eqlow")
    async def eqlow(self, ctx: commands.Context, value: int):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
        if value < 20 or value > 20000:
            await ctx.send("Frequency value must be between 20Hz and 20kHz.")
            return
        await self.process_audio(ctx, "eqlow", lambda audio: audio.low_pass_filter(value))
        return

    # EQ class allows for high-low frequency adjustments. eqhigh will specifically boost higher frequencies (treble, snares, etc)
    @commands.command(name="eqhigh")
    async def eqhigh(self, ctx: commands.Context, value: int):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
        if value < 20 or value > 20000:
            await ctx.send("Frequency value must be between 20Hz and 20kHz.")
            return
        await self.process_audio(ctx, "eqhigh", lambda audio: audio.high_pass_filter(value))
        return

    # High-pass filters only pass signals above its cutoff frequency and reduces signals below it to a specified tolerance
    @commands.command(name="hifilter")
    async def hifilter(self, ctx: commands.Context, cutoff: int):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        if cutoff < 20 or cutoff > 20000:
            await ctx.send("Cutoff frequency must be between 20Hz and 20kHz.")
            return
        await self.process_audio(ctx, "hifilter", lambda audio: audio.high_pass_filter(cutoff))
        return

    # Low-pass filters only pass signals below its cutoff frequency and reduces signals above it to a specified tolerance
    @commands.command(name="lofilter")
    async def lofilter(self, ctx: commands.Context, cutoff: int):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        if cutoff < 20 or cutoff > 20000:
            await ctx.send("Cutoff frequency must be between 20Hz and 20kHz.")
            return
        await self.process_audio(ctx, "lofilter", lambda audio: audio.low_pass_filter(cutoff))
        return

    # Echo adds delay and reverb to the track, adding an ethereal effect
    @commands.command(name="echo")
    async def echo(self, ctx: commands.Context, delay: int):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        if delay < 1 or delay > 5000:
            await ctx.send("Delay must be between 1ms and 5000ms.")
            return
        await self.process_audio(ctx, "echo", lambda audio: audio.overlay(audio - 10, delay=delay))
        return

async def setup(bot):
    await bot.add_cog(fx(bot))
