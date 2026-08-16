import datetime
import os
import json
import threading

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

from apinadb import ApinaDB
from youtube import YouTube

from functions import check_for_new_videos
import stats
import threads as thread_tools

DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')
# Daily report goes to its own channel, falling back to the video channel.
DISCORD_STATS_CHANNEL = os.getenv('DISCORD_STATS_CHANNEL') or DISCORD_CHANNEL

# Channels whose threads are left out of the report. Comma separated ids
# (preferred) or names. Statistics still count these channels.
IGNORED_CHANNELS = thread_tools.parse_ignore_list(os.getenv('DISCORD_IGNORED_CHANNELS'))

# When the daily thread list is posted, Finnish time.
THREADS_REPORT_TIME = datetime.time(hour=9, minute=0, tzinfo=stats.TIMEZONE)

# The statistics are posted weekly, at the midnight between Sunday and Monday.
STATS_REPORT_TIME = datetime.time(hour=0, minute=0, tzinfo=stats.TIMEZONE)
STATS_REPORT_WEEKDAY = 0  # Monday, as datetime.weekday() counts them.

# How long message rows are kept.
RETENTION_DAYS = 90

apinaDB = ApinaDB()
youtube = YouTube()

class ApinaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_new_videos.start()
        self.daily_report.start()
        self.weekly_stats.start()
        print("Initialize bot")
        ignored_ids, ignored_names = IGNORED_CHANNELS
        if ignored_ids or ignored_names:
            print("Ignoring threads from: %s" % (
                ", ".join(sorted(str(i) for i in ignored_ids) + sorted("#%s" % (n) for n in ignored_names))))

    def cog_unload(self):
        self.check_for_new_videos.cancel()
        self.daily_report.cancel()
        self.weekly_stats.cancel()
        print("Unload bot")

    # Record message metadata for the statistics. No message content is stored.
    # This is a cog listener, not an on_message override, so it does not
    # interfere with command processing.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        is_thread = isinstance(message.channel, discord.Thread)
        try:
            apinaDB.log_message(
                message.id,
                message.channel.id,
                message.channel.parent_id if is_thread else None,
                is_thread,
                message.author.id,
                message.author.display_name,
                message.channel.name,
                message.author.bot,
                message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            )
        except Exception as e:
            print("Failed to log message %s: %s" % (message.id, e))

    @commands.command(name="apinahelp")
    async def help(self, ctx):
        help_text = """**Bottiapina - Käytettävissä olevat komennot:**

`+apina-list` - Näyttää listan kaikista seuratuista YouTube-kanavista

`+apina-add handle:channelname` - Lisää kanavan handlella (esim. `+apina-add handle:kampiapina`)
`+apina-add id:UC2Prp3t7Ol-a041FXTyCzNQ` - Lisää kanavan ID:llä
*Vain moderaattorit voivat käyttää*

`+apina-remove <channel_id>` - Poistaa kanavan listalta
*Vain moderaattorit voivat käyttää*

`+apina-raportti` - Lähettää listan aktiivisista ketjuista heti
*Vain moderaattorit voivat käyttää*

`+apina-tilastot` - Lähettää tilastot heti
*Vain moderaattorit voivat käyttää*

Botti lähettää automaattisesti ilmoituksen, kun seuratut kanavat julkaisevat uusia videoita.
Joka aamu klo 9 botti kokoaa listan aktiivisista ketjuista, ja maanantaiöisin tilastot."""
        await ctx.send(help_text)

    @commands.command(name="apina-list")
    async def list(self, ctx):
        channel_list = []
        channels = apinaDB.get_channels()
        for channel in channels:
            channel_id = channel[0]
            channel_name = channel[1]
            channel_list.append("%s (%s)" % (channel_name, channel_id))
        await ctx.send('''Tällä hetkellä seuraan näitä kanavia:\n%s''' % ("\n".join(channel_list)))

    @commands.command(name="apina-add")
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

    @commands.command(name="apina-remove")
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

    # The channel the reports are posted to, as a normal message. None when it
    # cannot be resolved.
    def report_channel(self):
        if not DISCORD_STATS_CHANNEL:
            print("No stats channel configured, skipping report.")
            return None
        channel = self.bot.get_channel(int(DISCORD_STATS_CHANNEL))
        if not channel:
            print("Stats channel %s not found. Retrying later..." % (DISCORD_STATS_CHANNEL))
            return None

        # bot.get_channel() resolves thread ids too, and posting into a thread
        # buries the report. The report belongs in the channel itself, so step
        # up to the parent when the configured id turns out to be a thread.
        if isinstance(channel, discord.Thread):
            parent = channel.parent
            if not parent:
                print("Stats channel %s is a thread with no reachable parent." % (DISCORD_STATS_CHANNEL))
                return None
            print("Stats channel %s is a thread, posting to #%s instead." % (DISCORD_STATS_CHANNEL, parent.name))
            channel = parent

        return channel

    # Post the daily thread list. Returns the channel it posted to, or None.
    async def post_threads_report(self):
        channel = self.report_channel()
        if not channel:
            return None
        print("Posting thread report to #%s (%s)." % (channel.name, channel.id))
        embed = await stats.build_threads_report(apinaDB, channel.guild, ignore=IGNORED_CHANNELS)
        await channel.send(embed=embed)
        return channel

    # Post the weekly statistics. Returns the channel it posted to, or None.
    async def post_stats_report(self):
        channel = self.report_channel()
        if not channel:
            return None
        print("Posting statistics to #%s (%s)." % (channel.name, channel.id))
        await channel.send(embed=await stats.build_stats_embed(apinaDB, channel.guild))
        return channel

    @tasks.loop(time=THREADS_REPORT_TIME)
    async def daily_report(self):
        # The loop only fires once a day, but a restart close to the report time
        # could fire it again. One report per day, no matter what.
        today = stats.now_local().strftime('%Y-%m-%d')
        if apinaDB.get_state('last_daily_report_date') == today:
            print("Daily report already posted for %s." % (today))
            return

        print("Posting daily report for %s." % (today))
        try:
            if not await self.post_threads_report():
                return
        except Exception as e:
            print("Failed to post daily report: %s" % (e))
            return

        apinaDB.set_state('last_daily_report_date', today)

        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=RETENTION_DAYS)
        removed = apinaDB.prune_messages(stats.utc_str(cutoff))
        if removed > 0:
            print("Pruned %d message rows older than %d days." % (removed, RETENTION_DAYS))

    @daily_report.before_loop
    async def before_daily_report(self):
        await self.bot.wait_until_ready()

    @tasks.loop(time=STATS_REPORT_TIME)
    async def weekly_stats(self):
        # tasks.loop(time=...) has no day-of-week filter, so it wakes up every
        # midnight and everything but Monday is skipped.
        now = stats.now_local()
        if now.weekday() != STATS_REPORT_WEEKDAY:
            return

        today = now.strftime('%Y-%m-%d')
        if apinaDB.get_state('last_weekly_stats_date') == today:
            print("Weekly statistics already posted for %s." % (today))
            return

        print("Posting weekly statistics for %s." % (today))
        try:
            if not await self.post_stats_report():
                return
        except Exception as e:
            print("Failed to post weekly statistics: %s" % (e))
            return

        apinaDB.set_state('last_weekly_stats_date', today)

    @weekly_stats.before_loop
    async def before_weekly_stats(self):
        await self.bot.wait_until_ready()

    @commands.command(name="apina-raportti")
    @commands.has_permissions(manage_guild=True)
    async def report(self, ctx):
        await self.run_report(ctx, self.post_threads_report, "Kootaan ketjuraporttia...")

    @commands.command(name="apina-tilastot")
    @commands.has_permissions(manage_guild=True)
    async def statistics(self, ctx):
        await self.run_report(ctx, self.post_stats_report, "Kootaan tilastoja...")

    # Run one of the report posters on demand and tell the caller how it went.
    async def run_report(self, ctx, poster, waiting_message):
        await ctx.send(waiting_message)
        try:
            channel = await poster()
        except Exception as e:
            await ctx.send("Virhe raportin koostamisessa: %s" % (str(e)))
            return

        # Say where it went: the report goes to DISCORD_STATS_CHANNEL, which is
        # rarely the channel the command was typed in.
        if not channel:
            await ctx.send("Tilastokanavaa ei löytynyt. Tarkista DISCORD_STATS_CHANNEL.")
        elif channel.id != ctx.channel.id:
            await ctx.send("Raportti lähetetty kanavalle #%s." % (channel.name))

async def setup(bot: commands.Bot):
    await bot.add_cog(ApinaCommands(bot))

