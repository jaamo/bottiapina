import asyncio
import os
import json
import threading

import discord
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup - using slash commands (no prefix needed)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)

# Load extensions
@bot.event
async def setup_hook():
    await bot.load_extension("extensions.ApinaCommands")
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Start the bot
bot.run(TOKEN)
