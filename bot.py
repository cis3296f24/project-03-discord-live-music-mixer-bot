import discord
from discord.ext import commands
import os
import asyncio

# Read the token from the file
with open("./discordkey.txt", 'r') as key:
    token = key.readlines()[0].strip()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

# Create the bot instance
bot = commands.Bot(
    command_prefix=",", 
    intents=intents
)

# Function to load cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load cog {filename[:-3]}: {str(e)}")

# Bot ready event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')

# Main function to run the bot
async def main():
    async with bot:
        await load_cogs()
        await bot.start(token)

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())