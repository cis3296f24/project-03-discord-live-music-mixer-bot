import discord
from discord import VoiceChannel, Member, VoiceClient
import asyncio
from asyncio import run_coroutine_threadsafe
from discord_components import Select, SelectOption, Button
from discord.ext import commands
from VoiceChat import VoiceChat


class Effects(commands.Cog):
    def __init(self, bot):
     super().__init__(bot)


    @commands.Command(name="eq")
    async def eq(self, ctx: commands.Context, value):
       return

    @commands.Command(name="phase")
    async def phaser(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="echo")
    async def echo(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="deepfry")
    async def deepfry(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="gate")
    async def gate(self, ctx: commands.Context, value):
       return

    @commands.Command(name="fshift") 
    async def fshift(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="speed")
    async def speed(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="slow")
    async def slow(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="reverse")
    async def reverse(self, ctx: commands.Context, value):
       return
    
    @commands.Command(name="undo")
    async def undo(self, ctx: commands.Context, value):
       return