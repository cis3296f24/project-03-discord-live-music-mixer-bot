import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from discord.ext import commands
import ffmpeg
import subprocess #Equivalent to forking a process to create a child process. Mimics ffmpeg cmdline parsing of files


#Effects class inherits VoiceChat class, can check all its booleans, queues, etc
class fx(commands.Cog):
    def __init__(self, bot):
     self.bot = bot

   

#EQ class allows for high-low frequency adjustments. eqlow will specifically boost lower frequencies (bass boost, 808s, etc)
    @commands.command(name="eqlow")
    async def eqlow(self, ctx: commands.Context, value):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
        
        await ctx.send("EQLOW Activated w/ Value = {}".format(value))
       
        
        return

##EQ class allows for high-low frequency adjustments. eqlow will specifically boost higher frequencies (treble, snares, hi-hats, claps, most leads, etc)
    @commands.command(name="eqhigh")
    async def eqhigh(self, ctx: commands.Context, value):
       return
#High-pass filters only pass signals above its cutoff frequency and reduces signals below it to a specified tolerance 
    @commands.command(name="hifilter")
    async def hifilter(self, ctx: commands.Context, value):
       return
    
#Low-pass filters only pass signals below its cutoff frequency and reduces signals above it to a specified tolerance 
    @commands.command(name="lofilter")
    async def lofilter(self, ctx: commands.Context, value):
       return
    
#Phasers alter the frequency according to a specified range
    @commands.command(name="phase")
    async def phaser(self, ctx: commands.Context, value):
       return
    
#Echo adds delay and reverb to the track, adding an ethereal effect
    @commands.command(name="echo")
    async def echo(self, ctx: commands.Context, value):
       return
    
#Deepfry increases gain and distortion severely 
    @commands.command(name="deepfry")
    async def deepfry(self, ctx: commands.Context, value):
       return
    
#Reduces volume of audio signal based on certain thresholds
    @commands.command(name="gate")
    async def gate(self, ctx: commands.Context, value):
       return

#Frequency shifts will distort the pitch and texture of a track, creating a sour, artificial effect when pushed to its limits
    @commands.command(name="fshift") 
    async def fshift(self, ctx: commands.Context, value):
       return
    
#Increases a track's tempo 
    @commands.command(name="speed")
    async def speed(self, ctx: commands.Context, value):
       return
    
#Decreases a track's tempo
    @commands.command(name="slow")
    async def slow(self, ctx: commands.Context, value):
       return
    
async def setup(bot):
    await bot.add_cog(fx(bot))

 #THIS FUNCTION WILL PROBABLY BE INCREDIBLY ANNOYING TO IMPLEMENT SO I'M PUTTING IT DOWN HERE UNTIL THIS BOT CAN PLAY MUSIC

#"Undoes" effects by returning to the original, unaltered track
   # @commands.command(name="undo")
    #async def undo(self, ctx: commands.Context, value):
       #return
