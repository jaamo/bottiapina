# CLAUDE.md

Guidance for working in this repo. See `README.md` for full setup/deployment steps.

## What this is

**Bottiapina** is a Discord bot (Python + `discord.py`) that monitors a list of YouTube
channels and posts a notification to a Discord channel when a followed channel uploads a
new video. It also opens a thread on each notification message. The bot and its content
(commands, messages) are in Finnish. Cycling/mountain-biking YouTube channels are the
followed content.

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
- `apinadb.py` — `ApinaDB` class, thin SQLite wrapper over `bottiapina.db`. Single table
  `channels` storing channel metadata plus the last-seen video for change detection.
- `bottiapina-cli.py` — standalone CLI (no argparse; dispatches on `sys.argv[1]`) for DB
  setup and manual runs. Run with no args to print available commands.

Data flow: CLI/cog → `check_for_new_videos` → `YouTube` (API) + `ApinaDB` (state) → Discord.

## Running

```bash
source .venv/bin/activate           # Python 3.11.2 (prod pins this via pyenv)
pip install -r requirements.txt
python bottiapina-cli.py db-reset            # create/wipe the DB (DESTROYS ALL DATA)
python bottiapina-cli.py db-add-channel <id> # seed channels
python bottiapina.py                         # start the bot
```

There are no automated tests. To verify changes, use the CLI against the real APIs:
`python bottiapina-cli.py get-new-videos` (read-only, prints without saving) is the safe way
to exercise the YouTube path. Use `db-reset` + a single test channel when iterating.

## Configuration

Copy `.env.example` to `.env` and fill in:
`DISCORD_TOKEN`, `DISCORD_GUILD`, `DISCORD_CHANNEL` (numeric channel ID the bot posts to),
`YOUTUBE_API_KEY`.
`.env` and `*.db` are gitignored.

## Discord commands (prefix `+`)

- `+apinahelp` — help text
- `+apina-list` — list followed channels
- `+apina-add handle:<name>` or `+apina-add id:<channelId>` — add a channel (requires
  `manage_guild` permission)
- `+apina-remove <channelId>` — remove a channel (requires `manage_guild`)

Note: command *names* are `apina-*` (e.g. `apina-add`), but some help/usage strings still
show the older bare `+add`/`+remove`. The `@bot.event setup_hook` in `bottiapina.py` only
loads the cog; commands are defined in the cog, not the entry point.

## Conventions & gotchas

- **SQL:** most queries are parameterized, but `ApinaDB.add_channel` builds its `INSERT` via
  `%`-string formatting (the code even notes it's unsure if it's safe). Prefer parameterized
  queries for any new DB code; don't copy that pattern.
- The poll interval is hardcoded as `@tasks.loop(seconds=900)` in `ApinaCommands.py` — change
  it there.
- New-video detection is purely "latest upload id changed since last stored" — only the most
  recent upload per channel is tracked, so multiple uploads between polls may be missed.
- Errors in the YouTube path are swallowed (bare `except`) and only `print`ed; there is no
  structured logging.

## Deployment

Deployed to a Raspberry Pi over rsync (see README). Sync `*.py` and `extensions/*.py`; the
`bottiapina.db` on the Pi is the source of truth for the followed-channel list and can be
pulled back for backup.
