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


# Find every thread in the guild - archived ones included - that has had a
# message since `since` (an aware UTC datetime). Newest activity first.
async def find_recent_threads(guild, since):
    found = {}

    # Active (non-archived) threads: a single API call for the whole guild.
    try:
        for thread in await guild.active_threads():
            found[thread.id] = thread
    except discord.HTTPException as e:
        print("Failed to list active threads: %s" % (e))

    # Archived threads have to be asked for per channel. They arrive ordered by
    # archive time, newest first, so we can stop as soon as one was archived
    # before the cutoff - it cannot have a newer message than that.
    for channel in list(guild.text_channels) + list(guild.forums):
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
# channel plus every thread that has been active recently.
async def channels_to_scan(guild, since):
    channels = list(guild.text_channels)
    channels += await find_recent_threads(guild, since)
    return channels
