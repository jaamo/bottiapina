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

    @commands.command(name="wtf")
    async def wtf(self, ctx):
        channel_names = []
        channels = apinaDB.get_channels()
        for channel in channels:
            channel_names.append(channel[1])
        await ctx.send('''No mitäs mitäs! Olen bottiapina ja lähettelen tänne aina viestiä, kun YouTubeen postaillaan uusia videoita.\n
Minut on koodattu Pythonilla ja löydyn GitHubista: https://github.com/jaamo/bottiapina\n
Tällä hetkellä seuraan näitä kanavia: %s.\n
Kanavalistalle lisäillään Suomalaisia YouTube-kanavia, jotka tuottavat aktiivesti pyöräilyaiheista sisältöä. Jos joku kanava listalta puuttuu, niin vinkkaa ylläpidolle!''' % (", ".join(channel_names)))

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

