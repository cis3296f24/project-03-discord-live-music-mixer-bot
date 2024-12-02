import discord
from discord.ext import commands
import asyncio
import yt_dlp
from collections import deque
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = deque()
        self.ffmpeg_executable = "ffmpeg"  # Uses system-wide FFmpeg
        self.is_playing = False
        self.current_song = None
        self.voice_client = None

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user} MusicBot cog is ready!")

    async def check_permissions(self, ctx):
        permissions = ctx.channel.permissions_for(ctx.me)
        required_permissions = {
            "view_channel": permissions.view_channel,
            "send_messages": permissions.send_messages,
            "embed_links": permissions.embed_links,
            "connect": permissions.connect,
            "speak": permissions.speak,
        }
        
        missing_permissions = [perm for perm, has_perm in required_permissions.items() if not has_perm]
        
        if missing_permissions:
            await ctx.send(f"I'm missing the following permissions: {', '.join(missing_permissions)}")
            return False
        return True

    @commands.command(name="join")
    async def join(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if ctx.author.voice is None:
            return await ctx.send("You need to be in a voice channel to use this command.")
        
        channel = ctx.author.voice.channel
        if self.voice_client is None:
            self.voice_client = await channel.connect()
        else:
            await self.voice_client.move_to(channel)
        
        await ctx.send(f"Joined {channel.name}")

    @commands.command(name="leave")
    async def leave(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False
            self.song_queue.clear()
            await ctx.send("Left the voice channel and cleared the queue.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command(name="play")
    async def play(self, ctx, *, query):
        if not await self.check_permissions(ctx):
            return

        logger.info(f"Received play command with query: {query}")

        if self.voice_client is None:
            await self.join(ctx)
        
        async with ctx.typing():
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'noplaylist': True,
                    'quiet': True,
                }
                logger.info(f"Extracting info for: {query}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = await self.bot.loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                    if 'entries' in info:
                        # It's a playlist or a search query, take the first result
                        info = info['entries'][0]
                
                logger.info(f"Extracted info: {info['title']}")
                song_info = {
                    'title': info['title'],
                    'url': info['url'],
                    'duration': self.format_duration(info['duration']),
                }
                self.song_queue.append(song_info)
                
                queue_position = len(self.song_queue)
                embed = discord.Embed(title="Song Added to Queue", color=discord.Color.green())
                embed.add_field(name="Title", value=song_info['title'], inline=False)
                embed.add_field(name="Duration", value=song_info['duration'], inline=True)
                embed.add_field(name="Position in Queue", value=queue_position, inline=True)
                await ctx.send(embed=embed)
                
                if not self.is_playing:
                    await self.play_next()
            except Exception as e:
                logger.error(f"Error in play command: {str(e)}", exc_info=True)
                await ctx.send(f"An error occurred: {str(e)}")

    async def play_next(self):
        if not self.song_queue:
            self.is_playing = False
            return

        self.current_song = self.song_queue.popleft()
        self.is_playing = True

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }

        try:
            source = discord.FFmpegPCMAudio(self.current_song['url'], executable=self.ffmpeg_executable, **ffmpeg_options)
            self.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
            await self.voice_client.channel.send(f"Now playing: {self.current_song['title']}")
        except Exception as e:
            logger.error(f"Error playing {self.current_song['title']}: {str(e)}", exc_info=True)
            await self.voice_client.channel.send(f"Error playing {self.current_song['title']}: {str(e)}")
            await self.play_next()

    @commands.command(name="skip")
    async def skip(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("Skipped the current song.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(name="queue")
    async def queue(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if not self.song_queue:
            return await ctx.send("The queue is empty.")
        
        queue_list = "\n".join([f"{i+1}. {song['title']} ({song['duration']})" for i, song in enumerate(self.song_queue)])
        await ctx.send(f"Current queue:\n{queue_list}")

    @commands.command(name="pause")
    async def pause(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("Paused the music.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Resumed the music.")
        else:
            await ctx.send("The music is not paused.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if not await self.check_permissions(ctx):
            return

        if self.voice_client:
            self.song_queue.clear()
            self.voice_client.stop()
            self.is_playing = False
            await ctx.send("Stopped the music and cleared the queue.")
        else:
            await ctx.send("I'm not playing anything right now.")

    def format_duration(self, duration):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

async def setup(bot):
    await bot.add_cog(MusicBot(bot))