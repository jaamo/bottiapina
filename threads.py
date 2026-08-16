import discord


# Timestamp of the last message in a thread. Discord does not hand out an
# explicit "last activity" field, but the id of the last message is a snowflake
# and snowflakes carry their creation time.
def last_activity(thread):
    if thread.last_message_id:
        return discord.utils.snowflake_time(thread.last_message_id)
    if thread.archived and thread.archive_timestamp:
        return thread.archive_timestamp
    return thread.created_at or discord.utils.snowflake_time(thread.id)


# Parse a comma separated list of channels to leave out of the report into an
# (ids, names) pair. Ids are preferred - a channel can be renamed, and two
# channels in different categories can share a name - but names are accepted so
# the .env stays readable. A leading # is optional.
def parse_ignore_list(value):
    ids, names = set(), set()
    for part in (value or "").split(","):
        part = part.strip().lstrip("#")
        if not part:
            continue
        if part.isdigit():
            ids.add(int(part))
        else:
            names.add(part.casefold())
    return ids, names


NOTHING_IGNORED = (set(), set())


# Is this channel on the ignore list? The name is optional: an uncached parent
# channel can still be matched by id.
def is_ignored(ignore, channel_id, channel_name=None):
    ids, names = ignore
    if channel_id in ids:
        return True
    return channel_name is not None and channel_name.casefold() in names


# Find every thread in the guild - archived ones included - that has had a
# message since `since` (an aware UTC datetime). Newest activity first.
# `ignore` is a parse_ignore_list() pair of parent channels to skip.
async def find_recent_threads(guild, since, ignore=None):
    ignore = ignore or NOTHING_IGNORED
    found = {}

    # Active (non-archived) threads: a single API call for the whole guild.
    try:
        for thread in await guild.active_threads():
            parent = guild.get_channel(thread.parent_id)
            if is_ignored(ignore, thread.parent_id, parent.name if parent else None):
                continue
            found[thread.id] = thread
    except discord.HTTPException as e:
        print("Failed to list active threads: %s" % (e))

    # Archived threads have to be asked for per channel. They arrive ordered by
    # archive time, newest first, so we can stop as soon as one was archived
    # before the cutoff - it cannot have a newer message than that.
    for channel in list(guild.text_channels) + list(guild.forums):
        if is_ignored(ignore, channel.id, channel.name):
            continue
        try:
            async for thread in channel.archived_threads(limit=100):
                if thread.archive_timestamp and thread.archive_timestamp < since:
                    break
                found.setdefault(thread.id, thread)
        except discord.Forbidden:
            continue
        except discord.HTTPException as e:
            print("Failed to list archived threads for %s: %s" % (channel.name, e))
            continue

    recent = [t for t in found.values() if last_activity(t) >= since]
    recent.sort(key=last_activity, reverse=True)
    return recent


# All channels worth walking when backfilling message history: every text
# channel plus every thread that has been active recently. Deliberately does not
# take an ignore list - the ignore list only hides threads from the report, the
# statistics still count every channel.
async def channels_to_scan(guild, since):
    channels = list(guild.text_channels)
    channels += await find_recent_threads(guild, since)
    return channels
