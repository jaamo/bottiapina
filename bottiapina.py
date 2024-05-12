import asyncio
import os
import json
import threading

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot command prefix.
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)

# Load extensions
@bot.event
async def setup_hook():
    await bot.load_extension("extensions.ApinaCommands")

# Start the bot
bot.run(TOKEN)
