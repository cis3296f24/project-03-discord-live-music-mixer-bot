import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from discord_components import Select, SelectOption, Button
from discord.ext import commands
from VoiceChat import VoiceChat


#Effects class inherits VoiceChat class, can check all its booleans, queues, etc
class Effects(VoiceChat):
    def __init__(self, bot):
     super().__init__(bot)

#EQ class allows for high-low frequency adjustments. eqlow will specifically boost lower frequencies (bass boost, 808s, etc)
    @commands.Command(name="eqlow")
    async def eqlow(self, ctx: commands.Context, value):
       return

##EQ class allows for high-low frequency adjustments. eqlow will specifically boost higher frequencies (treble, snares, hi-hats, claps, most leads, etc)
    @commands.Command(name="eqhigh")
    async def eqhigh(self, ctx: commands.Context, value):
       return
#High-pass filters only pass signals above its cutoff frequency and reduces signals below it to a specified tolerance 
    @commands.Command(name="hifilter")
    async def hifilter(self, ctx: commands.Context, value):
       return
    
#Low-pass filters only pass signals below its cutoff frequency and reduces signals above it to a specified tolerance 
    @commands.Command(name="lofilter")
    async def lofilter(self, ctx: commands.Context, value):
       return
    
#Phasers alter the frequency according to a specified range
    @commands.Command(name="phase")
    async def phaser(self, ctx: commands.Context, value):
       return
    
#Echo adds delay and reverb to the track, adding an ethereal effect
    @commands.Command(name="echo")
    async def echo(self, ctx: commands.Context, value):
       return
    
#Deepfry increases gain and distortion severely 
    @commands.Command(name="deepfry")
    async def deepfry(self, ctx: commands.Context, value):
       return
    
#Reduces volume of audio signal based on certain thresholds
    @commands.Command(name="gate")
    async def gate(self, ctx: commands.Context, value):
       return

#Frequency shifts will distort the pitch and texture of a track, creating a sour, artificial effect when pushed to its limits
    @commands.Command(name="fshift") 
    async def fshift(self, ctx: commands.Context, value):
       return
    
#Increases a track's tempo 
    @commands.Command(name="speed")
    async def speed(self, ctx: commands.Context, value):
       return
    
#Decreases a track's tempo
    @commands.Command(name="slow")
    async def slow(self, ctx: commands.Context, value):
       return
    



 #THIS FUNCTION WILL PROBABLY BE INCREDIBLY ANNOYING TO IMPLEMENT SO I'M PUTTING IT DOWN HERE UNTIL THIS BOT CAN PLAY MUSIC

#"Undoes" effects by returning to the original, unaltered track
   # @commands.Command(name="undo")
    #async def undo(self, ctx: commands.Context, value):
       #return