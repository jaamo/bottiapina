import os
import json
import threading

from discord.ext import tasks, commands
from dotenv import load_dotenv

from apinadb import ApinaDB
from youtube import YouTube

from functions import check_for_new_videos

apinaDB = ApinaDB()
youtube = YouTube()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')

# Bot command prefix.
bot = commands.Bot(command_prefix='+')

class ApinaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_for_new_videos.start()

    def cog_unload(self):
        self.check_for_new_videos.cancel()

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

    @tasks.loop(seconds = 900) # 15 mins
    async def check_for_new_videos(self):
        channel = bot.get_channel(int(DISCORD_CHANNEL))
        print("Checking for new content. Posting to channel %s" % (DISCORD_CHANNEL))
        if channel:
            new_videos = check_for_new_videos(youtube, apinaDB)
            print("New content:")
            print(new_videos)
            for video in new_videos:
                await channel.send("Uusi video! %s: %s %s" % (video["channel_name"], video["video_title"], video["video_url"]))
                apinaDB.update_latest_video(
                    video["channel_id"],
                    video["video_id"],
                    video["video_title"],
                    video["video_url"],
                    video["video_description"],
                )
        else:
            print("Connection to Discord is down. Retrying soon...")
bot.add_cog(ApinaCommands(bot))
bot.run(TOKEN)
