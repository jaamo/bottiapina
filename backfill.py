import datetime
import os

import discord
from dotenv import load_dotenv

from threads import channels_to_scan

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
STATS_CHANNEL = os.getenv('DISCORD_STATS_CHANNEL') or os.getenv('DISCORD_CHANNEL')

# Rows per insert batch.
BATCH_SIZE = 500


# Read the message history of a single channel or thread into the database.
# Safe to run repeatedly: message_id is the primary key and inserts ignore
# duplicates.
async def scan_channel(apinaDB, channel, cutoff):
    is_thread = isinstance(channel, discord.Thread)
    parent_id = channel.parent_id if is_thread else None
    rows = []
    scanned = 0

    async for message in channel.history(after=cutoff, limit=None):
        rows.append((
            message.id,
            channel.id,
            parent_id,
            int(is_thread),
            message.author.id,
            message.author.display_name,
            channel.name,
            int(message.author.bot),
            message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ))
        scanned += 1
        if len(rows) >= BATCH_SIZE:
            apinaDB.log_messages(rows)
            rows = []

    if rows:
        apinaDB.log_messages(rows)

    return scanned


async def backfill(client, apinaDB, days):
    if not STATS_CHANNEL:
        print("DISCORD_STATS_CHANNEL (or DISCORD_CHANNEL) is not set.")
        return

    stats_channel = client.get_channel(int(STATS_CHANNEL))
    if not stats_channel:
        print("Channel %s not found. Is the bot on that server?" % (STATS_CHANNEL))
        return

    guild = stats_channel.guild
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    print("Backfilling %s from %s (%d days)." % (guild.name, cutoff.date(), days))

    channels = await channels_to_scan(guild, cutoff)
    print("Scanning %d channels and threads." % (len(channels)))

    total = 0
    for channel in channels:
        try:
            scanned = await scan_channel(apinaDB, channel, cutoff)
        except discord.Forbidden:
            print("  %-40s no access, skipped" % (channel.name))
            continue
        except discord.HTTPException as e:
            print("  %-40s failed: %s" % (channel.name, e))
            continue
        total += scanned
        print("  %-40s %d messages" % (channel.name, scanned))

    print("Scanned %d messages. Database now holds %d rows." % (total, apinaDB.total_messages()))


# Log in as a short lived client, backfill, then quit.
def run(apinaDB, days=35):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    done = False

    @client.event
    async def on_ready():
        # on_ready fires again after a reconnect; only backfill once.
        nonlocal done
        if done:
            return
        done = True
        try:
            await backfill(client, apinaDB, days)
        finally:
            await client.close()

    client.run(TOKEN)
