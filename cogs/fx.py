
import discord
from discord.ext import commands
from pydub import AudioSegment
import os

# Effects class inherits from commands.Cog
class fx(commands.Cog):
    def __init__(self, bot, vc_instance):
        self.bot = bot
        self.vc_instance = vc_instance  # Reference to vc.py instance for queue interaction
        self.temp_dir = "./temp_audio"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)  # Create temp directory if not exists

    async def process_audio(self, ctx, effect_name, effect_function, *args):
        """Apply effect to the currently playing audio in the queue."""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.send("I'm not in a voice channel or no audio is playing!")
                return

            # Get the currently playing song path from vc.py queue
            if self.vc_instance.queue.empty():
                await ctx.send("The queue is empty!")
                return

            current_song = self.vc_instance.queue.peek()
            original_path = current_song.path
            new_path = os.path.join(self.temp_dir, f"{effect_name}_{current_song.title}.mp3")

            # Apply the effect using Pydub
            audio = AudioSegment.from_file(original_path)
            processed_audio = effect_function(audio, *args)
            processed_audio.export(new_path, format="mp3")

            # Replace the current song in the queue with the processed audio
            self.vc_instance.queue.clear_current()  # Remove the current song
            current_song.path = new_path  # Update path to processed audio
            self.vc_instance.queue.put(current_song)  # Reinsert it into the queue
            await ctx.send(f"{effect_name} effect applied to {current_song.title}.")

        except Exception as e:
            await ctx.send(f"Error applying {effect_name}: {e}")

    @commands.command(name="eqlow")
    async def eqlow(self, ctx: commands.Context, value: float):
        # Apply a low-pass filter to boost lower frequencies
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "eqlow", lambda audio: audio.low_pass_filter(value))

    @commands.command(name="eqhigh")
    async def eqhigh(self, ctx: commands.Context, value: float):
        # Apply a high-pass filter to boost higher frequencies
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "eqhigh", lambda audio: audio.high_pass_filter(value))

    @commands.command(name="hifilter")
    async def hifilter(self, ctx: commands.Context, value: float):
        # Apply a high-pass filter to pass signals above a cutoff frequency
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "hifilter", lambda audio: audio.high_pass_filter(value))

    @commands.command(name="lofilter")
    async def lofilter(self, ctx: commands.Context, value: float):
        # Apply a low-pass filter to pass signals below a cutoff frequency
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "lofilter", lambda audio: audio.low_pass_filter(value))

    @commands.command(name="phase")
    async def phaser(self, ctx: commands.Context, value: float):
        # Apply a phaser effect by inverting the audio waveform
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return

        def invert_phase(audio):
            return audio._spawn(-audio.raw_data)  # Invert the waveform

        await self.process_audio(ctx, "phase", invert_phase)

    @commands.command(name="echo")
    async def echo(self, ctx: commands.Context, delay: int):
        # Apply an echo effect by overlaying the audio with a delayed version of itself
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "echo", lambda audio: audio.overlay(audio - 10, delay=delay))

    @commands.command(name="deepfry")
    async def deepfry(self, ctx: commands.Context, value: float):
        # Increase gain and distortion for a "deep fry" effect
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "deepfry", lambda audio: audio + value)

    @commands.command(name="gate")
    async def gate(self, ctx: commands.Context, threshold: float):
        # Apply a noise gate by reducing volume above a certain threshold
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return

        def apply_gate(audio, threshold):
            return audio - threshold if audio.dBFS > threshold else audio

        await self.process_audio(ctx, "gate", apply_gate, threshold)

    @commands.command(name="fshift")
    async def fshift(self, ctx: commands.Context, value: float):
        # Apply a frequency shift to alter pitch
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "fshift", lambda audio: audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate + value)}).set_frame_rate(audio.frame_rate))

    @commands.command(name="speed")
    async def speed(self, ctx: commands.Context, value: float):
        # Increase the speed (tempo) of the audio
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "speed", lambda audio: audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * value)}).set_frame_rate(audio.frame_rate))

    @commands.command(name="slow")
    async def slow(self, ctx: commands.Context, value: float):
        # Decrease the speed (tempo) of the audio
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("I'm not in a voice channel or no audio is playing!")
            return
        await self.process_audio(ctx, "slow", lambda audio: audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate / value)}).set_frame_rate(audio.frame_rate))


async def setup(bot):
    await bot.add_cog(fx(bot))


async def setup(bot):
    from vc import vc  # Import vc dynamically
    vc_instance = vc(bot)  # Create an instance of vc
    await bot.add_cog(fx(bot, vc_instance))
