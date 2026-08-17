import datetime
from zoneinfo import ZoneInfo

import discord

from threads import find_recent_threads, last_activity

# All day boundaries are local Finnish days, not UTC days.
TIMEZONE = ZoneInfo("Europe/Helsinki")

# A thread counts as active when it has had a message within this many days.
ACTIVE_THREAD_DAYS = 7

# Discord embed descriptions max out at 4096 characters, so cap the list.
MAX_THREADS_LISTED = 25

# How many entries per statistic.
TOP_CHANNELS = 3
TOP_MEMBERS = 10

EMBED_COLOR = 0x00A86B


def now_local():
    return datetime.datetime.now(TIMEZONE)


# Format an aware datetime the way the message table stores it.
def utc_str(dt):
    return dt.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


# The reporting windows, as (label, start_utc, end_utc). Both end at local
# midnight today, so they only ever cover complete days. The statistics are
# posted at Monday midnight, which makes the 7 day window exactly the previous
# Monday to Sunday week.
def windows(now=None):
    now = now or now_local()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        ("Viimeiset 7 päivää", today - datetime.timedelta(days=7), today),
        ("Viimeiset 30 päivää", today - datetime.timedelta(days=30), today),
    ]


def plural_messages(count):
    return "%d viesti" % (count) if count == 1 else "%d viestiä" % (count)


# Finnish, human readable "how long ago".
def format_ago(then, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    days = (now.astimezone(TIMEZONE).date() - then.astimezone(TIMEZONE).date()).days
    if days <= 0:
        return "tänään"
    if days == 1:
        return "eilen"
    return "%d pv sitten" % (days)


# Prefer the live name from Discord, fall back to the snapshot stored when the
# message was logged (the channel or member may be gone).
def channel_label(guild, channel_id, stored_name):
    channel = guild.get_channel_or_thread(channel_id) if guild else None
    if channel:
        return "#%s" % (channel.name)
    return "#%s" % (stored_name or channel_id)


# The name to show for a member. People recognise the per-server nickname, and
# Member.display_name is exactly that - nick, then global name, then handle.
#
# Getting a Member is the tricky part. guild.get_member() only works when the
# member cache is populated, which needs the privileged members intent, and
# messages read back from history come with a plain User attached (Discord only
# sends the member object with gateway events), so what was stored at log time
# may well be the handle. One REST lookup per member fixes both; only a handful
# of names are shown per report and `cache` keeps it to one lookup each.
async def member_label(guild, author_id, stored_name, cache=None):
    if cache is not None and author_id in cache:
        return cache[author_id]

    member = guild.get_member(author_id) if guild else None
    if member is None and guild:
        try:
            member = await guild.fetch_member(author_id)
        except discord.HTTPException:
            # Left the server, or not fetchable. Fall back to the snapshot.
            member = None

    name = member.display_name if member else (stored_name or str(author_id))
    if cache is not None:
        cache[author_id] = name
    return name


# List of threads with a message in the last ACTIVE_THREAD_DAYS days. `ignore`
# is a threads.parse_ignore_list() pair of parent channels to leave out.
async def collect_active_threads(guild, now=None, ignore=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    since = now - datetime.timedelta(days=ACTIVE_THREAD_DAYS)
    return await find_recent_threads(guild, since, ignore), since


def build_threads_embed(threads, guild, now=None, counts=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    counts = counts or {}
    embed = discord.Embed(
        title="🧵 Aktiiviset ketjut (%d pv)" % (ACTIVE_THREAD_DAYS),
        color=EMBED_COLOR,
    )

    if not threads:
        embed.description = "Yhtään ketjua ei ole herätelty viime päivinä. Hiljaista kuin metsässä."
        return embed

    lines = []
    for thread in threads[:MAX_THREADS_LISTED]:
        parent = guild.get_channel(thread.parent_id) if guild else None
        parts = ["#%s" % (parent.name)] if parent else []
        # Counts come from our own message log, so they only cover the reporting
        # window. Left out when we have nothing logged for the thread.
        if counts.get(thread.id):
            parts.append(plural_messages(counts[thread.id]))
        parts.append(format_ago(last_activity(thread), now))
        if thread.archived:
            parts.append("arkistoitu")
        lines.append("• [%s](%s) — %s" % (thread.name, thread.jump_url, " · ".join(parts)))

    if len(threads) > MAX_THREADS_LISTED:
        lines.append("…ja %d muuta ketjua." % (len(threads) - MAX_THREADS_LISTED))

    embed.description = "\n".join(lines)
    return embed


async def build_stats_embed(apinaDB, guild, now=None):
    now = now or now_local()
    embed = discord.Embed(title="📊 Tilastot", color=EMBED_COLOR)
    names = {}

    for label, start, end in windows(now):
        start_utc, end_utc = utc_str(start), utc_str(end)
        total = apinaDB.message_count(start_utc, end_utc)

        if not total:
            embed.add_field(name=label, value="Ei viestejä.", inline=False)
            continue

        rows = ["**Kanavat**"]
        for channel_id, count, name in apinaDB.top_channels(start_utc, end_utc, TOP_CHANNELS):
            rows.append("%s — %s" % (channel_label(guild, channel_id, name), plural_messages(count)))

        rows.append("**Jäsenet**")
        for author_id, count, name in apinaDB.top_members(start_utc, end_utc, TOP_MEMBERS):
            label_name = await member_label(guild, author_id, name, names)
            rows.append("%s — %s" % (label_name, plural_messages(count)))

        rows.append("Yhteensä %s." % (plural_messages(total)))
        embed.add_field(name=label, value="\n".join(rows), inline=False)

    return embed


# The daily post: the list of active threads. Message counts come from our own
# log and cover the same window as the list.
async def build_threads_report(apinaDB, guild, now=None, ignore=None):
    now = now or now_local()
    now_utc = now.astimezone(datetime.timezone.utc)
    threads, since = await collect_active_threads(guild, now_utc, ignore)
    counts = apinaDB.message_counts_by_channel(utc_str(since), utc_str(now_utc))
    return build_threads_embed(threads, guild, now_utc, counts)
