# CLAUDE.md

Guidance for working in this repo. See `README.md` for full setup/deployment steps.

## What this is

**Bottiapina** is a Discord bot (Python + `discord.py`) that monitors a list of YouTube
channels and posts a notification to a Discord channel when a followed channel uploads a
new video. It also opens a thread on each notification message. The bot and its content
(commands, messages) are in Finnish. Cycling/mountain-biking YouTube channels are the
followed content.

Second feature: a daily report posted at 09:00 Europe/Helsinki listing threads active in
the last 7 days (archived included), and a weekly statistics post at Monday 00:00 with the
most active channels/members over 7 and 30 days. Both go to `DISCORD_STATS_CHANNEL`.

## Architecture

Flat module layout, no package. Core modules imported by both the bot and the CLI:

- `bottiapina.py` — entry point. Loads `.env`, creates the `commands.Bot` (prefix `+`),
  loads the `extensions.ApinaCommands` cog, and runs the bot. Nothing else lives here.
- `extensions/ApinaCommands.py` — the cog. Holds all Discord commands **and** the
  `@tasks.loop(seconds=900)` background task that polls YouTube every 15 minutes and posts
  new videos. This is where most bot logic lives.
- `functions.py` — `check_for_new_videos(youtube, apinaDB)`: iterates DB channels, asks the
  YouTube API for each channel's latest upload, returns a list of videos whose `video_id`
  differs from the stored one. It does **not** write to the DB — the caller updates the DB
  after acting on the result. Wrapped in a bare `try/except` so a YouTube timeout on one
  channel doesn't crash the whole loop.
- `youtube.py` — `YouTube` class wrapping the Google `youtube/v3` API (channels,
  playlistItems). API key only, no OAuth. Supports lookup by channel ID and by handle.
- `apinadb.py` — `ApinaDB` class, thin SQLite wrapper over `bottiapina.db`. Tables:
  `channels` (channel metadata + last-seen video for change detection), `messages`
  (message metadata for statistics — never content), `state` (key/value, e.g.
  `last_daily_report_date`). `_ensure_schema()` runs on every start with
  `CREATE TABLE IF NOT EXISTS`, so **deploying never requires `db-reset`**; only
  `channels` lives in `reset()`.
- `threads.py` — `find_recent_threads(guild, since)`: active threads via one
  `guild.active_threads()` call plus per-channel `archived_threads()`, which arrive
  newest-archived first so the loop breaks at the cutoff. `last_activity(thread)` derives
  the timestamp from the `last_message_id` snowflake.
- `stats.py` — reporting windows (local Finnish days), SQL aggregation via `ApinaDB`, and
  the Finnish embeds. `build_threads_report()` for the daily post, `build_stats_embed()`
  for the weekly one.
- `backfill.py` — one-shot `discord.Client` that reads message history into `messages`.
  Idempotent (`message_id` is the primary key).
- `bottiapina-cli.py` — standalone CLI (no argparse; dispatches on `sys.argv[1]`) for DB
  setup and manual runs. Run with no args to print available commands.

Data flow: CLI/cog → `check_for_new_videos` → `YouTube` (API) + `ApinaDB` (state) → Discord.
Stats flow: `on_message` listener (and `backfill.py` once) → `messages` table →
`stats.build_*` → the `daily_report` / `weekly_stats` loops → Discord.

## Running

```bash
source .venv/bin/activate           # Python 3.11.2 (prod pins this via pyenv)
pip install -r requirements.txt
python bottiapina-cli.py db-reset            # create/wipe the DB (DESTROYS ALL DATA)
python bottiapina-cli.py db-add-channel <id> # seed channels
python bottiapina-cli.py stats-backfill 35   # seed message stats from Discord history
python bottiapina.py                         # start the bot
```

There are no automated tests. To verify changes, use the CLI against the real APIs:
`python bottiapina-cli.py get-new-videos` (read-only, prints without saving) is the safe way
to exercise the YouTube path, and `python bottiapina-cli.py stats-top 7` prints the stats
straight from SQLite without touching Discord. Use `db-reset` + a single test channel when
iterating.

## Configuration

Copy `.env.example` to `.env` and fill in:
`DISCORD_TOKEN`, `DISCORD_GUILD`, `DISCORD_CHANNEL` (numeric channel ID the bot posts to),
`DISCORD_STATS_CHANNEL` (daily report target; falls back to `DISCORD_CHANNEL`),
`DISCORD_IGNORED_CHANNELS` (comma separated ids or names whose threads are hidden from the
report — statistics still count them), `YOUTUBE_API_KEY`.

`deploy.sh` does **not** sync `.env`. Any new variable must be added to the Pi's
`/home/pi/bottiapina/.env` by hand, or the fallback silently kicks in.
`.env` and `*.db` are gitignored.

## Discord commands (prefix `+`)

- `+apinahelp` — help text
- `+apina-list` — list followed channels
- `+apina-add handle:<name>` or `+apina-add id:<channelId>` — add a channel (requires
  `manage_guild` permission)
- `+apina-remove <channelId>` — remove a channel (requires `manage_guild`)
- `+apina-raportti` — post the thread list immediately (requires `manage_guild`)
- `+apina-tilastot` — post the statistics immediately (requires `manage_guild`); these two
  are the way to test without waiting for the scheduled times

Note: command *names* are `apina-*` (e.g. `apina-add`), but some help/usage strings still
show the older bare `+add`/`+remove`. The `@bot.event setup_hook` in `bottiapina.py` only
loads the cog; commands are defined in the cog, not the entry point.

## Conventions & gotchas

- **SQL:** all queries are parameterized. Keep it that way.
- `ApinaDB` shares one `self.cur` across the older methods. New code takes its own
  `self.con.cursor()` per query — the `on_message` listener writes constantly, and a shared
  cursor would clobber another query's results mid-iteration. `get_channels()` returns
  `fetchall()` rows for the same reason.
- The poll interval is hardcoded as `@tasks.loop(seconds=900)` in `ApinaCommands.py` — change
  it there, along with `THREADS_REPORT_TIME` and `STATS_REPORT_TIME`/`STATS_REPORT_WEEKDAY`.
- `tasks.loop(time=...)` has no day-of-week filter, so `weekly_stats` wakes every midnight
  and returns early unless it is Monday. Each loop has its own `state` guard key so a
  restart cannot double-post.
- Statistics only exist for the time the bot has been running. `stats-backfill` seeds
  history; downtime leaves gaps unless it is re-run.
- Bots are excluded from all rankings (`is_bot = 0`), but their messages are still stored.
- New-video detection is purely "latest upload id changed since last stored" — only the most
  recent upload per channel is tracked, so multiple uploads between polls may be missed.
- Errors in the YouTube path are swallowed (bare `except`) and only `print`ed; there is no
  structured logging.

## Deployment

Deployed to a Raspberry Pi over rsync (see README). Sync `*.py` and `extensions/*.py`; the
`bottiapina.db` on the Pi is the source of truth for the followed-channel list and the
message statistics, and can be pulled back for backup. The DB runs in WAL mode, so
`backup.sh` pulls `bottiapina.db*` — the `-wal` sidecar holds the newest commits.
