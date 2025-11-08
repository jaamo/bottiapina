import os
import json
import threading

import discord
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv

from apinadb import ApinaDB
from youtube import YouTube

from functions import check_for_new_videos

DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')

apinaDB = ApinaDB()
youtube = YouTube()

class ApinaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_new_videos.start()
        print("Initialize bot")

    def cog_unload(self):
        self.check_for_new_videos.cancel()
        print("Unload bot")

    @commands.command(name="apina-help")
    async def help(self, ctx):
        help_text = """**Bottiapina - Käytettävissä olevat komennot:**

`/apina-list` - Näyttää listan kaikista seuratuista YouTube-kanavista

`/apina-add` - Lisää kanavan handlella tai ID:llä
*Vain moderaattorit voivat käyttää*

`/apina-remove` - Poistaa kanavan listalta
*Vain moderaattorit voivat käyttää*

Botti lähettää automaattisesti ilmoituksen, kun seuratut kanavat julkaisevat uusia videoita."""
        await interaction.response.send_message(help_text)

    @commands.command(name="apina-list")
    async def list(self, ctx):
        channel_list = []
        channels = apinaDB.get_channels()
        for channel in channels:
            channel_id = channel[0]
            channel_name = channel[1]
            channel_list.append("%s (%s)" % (channel_name, channel_id))
        
        if not channel_list:
            await interaction.response.send_message("Ei seurattuja kanavia.")
        else:
            await interaction.response.send_message('''Tällä hetkellä seuraan näitä kanavia:\n%s''' % ("\n".join(channel_list)))

    @commands.command(name="apina-add")
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, identifier: str = None):
        if not identifier:
            await interaction.response.send_message("Anna kanavan handle tai ID.", ephemeral=True)
            return

        # Get channel info from YouTube API
        try:
            if type == "handle":
                # Get channel by handle
                channel_list = youtube.get_channel_by_handle(identifier)
            else:
                # Get channel by ID
                channel_list = youtube.get_channel(identifier)

            if "items" not in channel_list or len(channel_list["items"]) == 0:
                await interaction.response.send_message("Kanavaa ei löytynyt YouTube API:sta.", ephemeral=True)
                return

            channel_id = channel_list["items"][0]["id"]
            channel_name = channel_list["items"][0]["snippet"]["title"]
            upload_playlist_id = channel_list["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Check if channel already exists
            if apinaDB.channel_exists(channel_id):
                await interaction.response.send_message("Kanava on jo listalla!", ephemeral=True)
                return

            # Add channel to database
            apinaDB.add_channel(channel_id, channel_name, upload_playlist_id)
            await interaction.response.send_message("Kanava lisätty: %s (%s)" % (channel_name, channel_id))
        except Exception as e:
            await interaction.response.send_message("Virhe kanavan lisäämisessä: %s" % (str(e)), ephemeral=True)

    @commands.command(name="apina-remove")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, channel_id: str = None):
        if not channel_id:
            await interaction.response.send_message("Anna kanavan ID.", ephemeral=True)
            return

        # Check if channel exists
        if not apinaDB.channel_exists(channel_id):
            await interaction.response.send_message("Kanavaa ei löytynyt listalta!", ephemeral=True)
            return

        # Get channel name before removing
        channels = apinaDB.get_channels()
        channel_name = None
        for channel in channels:
            if channel[0] == channel_id:
                channel_name = channel[1]
                break

        # Remove channel from database
        if apinaDB.remove_channel(channel_id):
            if channel_name:
                await interaction.response.send_message("Kanava poistettu: %s" % (channel_name))
            else:
                await interaction.response.send_message("Kanava poistettu: %s" % (channel_id))
        else:
            await interaction.response.send_message("Virhe kanavan poistamisessa.", ephemeral=True)

    @tasks.loop(seconds = 900) # 15 mins, 900 seconds
    async def check_for_new_videos(self):
        if not DISCORD_CHANNEL:
            return
        channel = self.bot.get_channel(int(DISCORD_CHANNEL))
        print("Checking for new content. Posting to channel %s" % (DISCORD_CHANNEL))
        if channel:
            new_videos = check_for_new_videos(youtube, apinaDB)
            print("New content:")
            print(new_videos)
            for video in new_videos:
                msg = await channel.send("Uusi video! %s: %s %s" % (video["channel_name"], video["video_title"], video["video_url"]))
                await msg.create_thread(name=video["video_title"])
                apinaDB.update_latest_video(
                    video["channel_id"],
                    video["video_id"],
                    video["video_title"],
                    video["video_url"],
                    video["video_description"],
                )
        else:
            print("Connection to Discord is down. Retrying soon...")

async def setup(bot: commands.Bot):
    cog = ApinaCommands(bot)
    await bot.add_cog(cog)
    # Register slash commands with the bot's command tree
    # Remove existing commands first to avoid duplicates on reload
    # Remove both old and new command names
    old_command_names = ["apinahelp", "list", "add", "remove"]
    new_command_names = ["apina-help", "apina-list", "apina-add", "apina-remove"]
    for cmd_name in old_command_names + new_command_names:
        try:
            bot.tree.remove_command(cmd_name)
        except:
            pass
    
    # Add commands from the cog
    bot.tree.add_command(cog.help)
    bot.tree.add_command(cog.list)
    bot.tree.add_command(cog.add)
    bot.tree.add_command(cog.remove)

