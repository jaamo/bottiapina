import os
import json
import threading

import discord
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

    @commands.command(name="apinahelp")
    async def help(self, ctx):
        help_text = """**Bottiapina - Käytettävissä olevat komennot:**

`+list` - Näyttää listan kaikista seuratuista YouTube-kanavista

`+add handle:channelname` - Lisää kanavan handlella (esim. `+add handle:kampiapina`)
`+add id:UC2Prp3t7Ol-a041FXTyCzNQ` - Lisää kanavan ID:llä
*Vain moderaattorit voivat käyttää*

`+remove <channel_id>` - Poistaa kanavan listalta
*Vain moderaattorit voivat käyttää*

Botti lähettää automaattisesti ilmoituksen, kun seuratut kanavat julkaisevat uusia videoita."""
        await ctx.send(help_text)

    @commands.command(name="list")
    async def list(self, ctx):
        channel_list = []
        channels = apinaDB.get_channels()
        for channel in channels:
            channel_id = channel[0]
            channel_name = channel[1]
            channel_list.append("%s (%s)" % (channel_name, channel_id))
        await ctx.send('''Tällä hetkellä seuraan näitä kanavia:\n%s''' % ("\n".join(channel_list)))

    @commands.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, identifier: str = None):
        if not identifier:
            await ctx.send("Käyttö: `+add handle:channelname` tai `+add id:UC2Prp3t7Ol-a041FXTyCzNQ`")
            return

        # Detect if identifier is a handle (starts with handle:) or an ID (starts with id:)
        is_handle = identifier.startswith('handle:')
        is_id = identifier.startswith('id:')
        
        # Extract the actual identifier
        if is_handle:
            handle = identifier[7:]  # Remove "handle:" prefix
        elif is_id:
            channel_id = identifier[3:]  # Remove "id:" prefix
        else:
            # For backward compatibility, assume it's an ID if no prefix
            channel_id = identifier
            is_id = True
        
        # Get channel info from YouTube API
        try:
            if is_handle:
                # Get channel by handle
                channel_list = youtube.get_channel_by_handle(handle)
            else:
                # Get channel by ID
                channel_list = youtube.get_channel(channel_id)

            if "items" not in channel_list or len(channel_list["items"]) == 0:
                await ctx.send("Kanavaa ei löytynyt YouTube API:sta.")
                return

            channel_id = channel_list["items"][0]["id"]
            channel_name = channel_list["items"][0]["snippet"]["title"]
            upload_playlist_id = channel_list["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Check if channel already exists
            if apinaDB.channel_exists(channel_id):
                await ctx.send("Kanava on jo listalla!")
                return

            # Add channel to database
            apinaDB.add_channel(channel_id, channel_name, upload_playlist_id)
            await ctx.send("Kanava lisätty: %s (%s)" % (channel_name, channel_id))
        except Exception as e:
            await ctx.send("Virhe kanavan lisäämisessä: %s" % (str(e)))

    @commands.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, channel_id: str = None):
        if not channel_id:
            await ctx.send("Käyttö: `+remove <YouTube-kanavan ID>`")
            return

        # Check if channel exists
        if not apinaDB.channel_exists(channel_id):
            await ctx.send("Kanavaa ei löytynyt listalta!")
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
                await ctx.send("Kanava poistettu: %s" % (channel_name))
            else:
                await ctx.send("Kanava poistettu: %s" % (channel_id))
        else:
            await ctx.send("Virhe kanavan poistamisessa.")

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
    await bot.add_cog(ApinaCommands(bot))

