# Bottiapina Discord bot

This bot monitors given YouTube channels and posts a notification to Discord channel when new videos are published.

It also posts a daily report at 09:00 Finnish time listing the threads that have been active
during the last 7 days (archived threads included) and server statistics: the most active
channels and members yesterday, over the past 7 days and over the past 30 days.

## Required packages

- discord.py
- google-api-python-client
- google-auth-oauthlib
- google-auth-httplib2

## Setting up python

Production server uses Python 3.11.2. To use the same version locally install it:

`pyenv install 3.11.2`

Create venv environment inside project folder:

`~/.pyenv/versions/3.11.2/bin/python3.11 -m venv .venv`


## Installation

1. Clone this repo
1. Create Discord bot according to this tutorial https://realpython.com/how-to-make-a-discord-bot-python/
1. Create YouTube API key according to this tutorial (only API key required, OAuth2 is not) https://developers.google.com/youtube/v3/quickstart/python
1. Enable Discord developer mode: User settings -> Advanced -> Developer mode
1. Find a Discord channel you want to use and right click it to get the channel ID
1. Use this site to obtain YouTube channel id https://commentpicker.com/youtube-channel-id.php
1. Copy .env.example to .env and fill in Discord and YouTube parameters
1. Run `source .venv/bin/activate` if you are using venv
1. Install dependencies: `pip install -r requirements.txt`
1. Setup database: `python bottiapina-cli.py db-reset`
1. Add YouTube channels: `python bottiapina-cli.py db-add-channel [channel id]`
1. Seed the statistics with past messages: `python bottiapina-cli.py stats-backfill`
1. Start the bot: `python bottiapina.py`

`DISCORD_CHANNEL` is the channel new videos are posted to. `DISCORD_STATS_CHANNEL` is the
channel the daily report goes to; leave it empty to use `DISCORD_CHANNEL` for both.

The bot needs *View Channel* and *Read Message History* on every channel that should show up
in the report. Private archived threads are skipped; including them would additionally
require *Manage Threads*.

## CLI usage

There is a simple command line interface for managing the bot.

CLI usage:

`python bottiapina-cli.py update-new-videos`

To see available commands:

`python bottiapina-cli.py`

## Discord bot commands

The bot responds to commands with the `+` prefix. Available commands:

- `+apinahelp` - Shows help text with all available commands
- `+apina-list` - Lists all followed YouTube channels with their names and IDs
- `+apina-add handle:channelname` - Adds a channel by handle (e.g. `+apina-add handle:kampiapina`)
- `+apina-add id:UC2Prp3t7Ol-a041FXTyCzNQ` - Adds a channel by YouTube channel ID
- `+apina-remove <channel_id>` - Removes a channel from the list
- `+apina-raportti` - Posts the daily thread and statistics report immediately

**Note:** The `+apina-add`, `+apina-remove` and `+apina-raportti` commands require moderator
permissions (manage_guild permission).

You can also add channels using the CLI tool during setup, but the Discord commands allow managing channels without stopping the bot.

## Debugging tips

1. Empty database `python bottiapina-cli.py db-reset`
1. Use test channel id
1. Add single channel with `python3 bottiapina-cli.py db-add-channel UC2Prp3t7Ol-a041FXTyCzNQ`
1. Run the bot `python bottiapina.py`

New content is checked every 15 minutes.  
Reduce the time in extensions/ApinaCommands.py

## Statistics

The bot records metadata about every message it sees - channel, author, timestamp - into the
`messages` table. **No message content is stored.** Rows older than 90 days are deleted
automatically after each daily report.

Statistics only cover the time the bot has been running, so run the backfill once to read the
existing history in:

`python bottiapina-cli.py stats-backfill 35`

It logs into Discord, walks every channel and recently active thread, and exits. Running it
again is harmless - messages are keyed by their id, so duplicates are ignored.

To check the numbers without Discord:

`python bottiapina-cli.py stats-top 7`

The report itself is posted at 09:00 Finnish time (`REPORT_TIME` in
`extensions/ApinaCommands.py`). "Yesterday" always means the previous full calendar day.
Use `+apina-raportti` in Discord to trigger the report immediately when testing.

## Production deployment :D

Deploy the Python source to the Raspberry Pi (does not touch the remote database or `.env`):

`./deploy.sh`

Then restart the bot on the server.

Back up the production database to this folder:

`./backup.sh`

Both scripts target `pi@192.168.1.75:/home/pi/bottiapina/`; edit the `REMOTE`/`REMOTE_DIR` variables at the top of the scripts to change the destination.

## Related documentation:

- https://discord.com/developers/applications/
- https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python
- https://developers.google.com/youtube/v3/quickstart/python
- https://commentpicker.com/youtube-channel-id.php

python3 bot.py

Channel ids:

python3 bottiapina-cli.py db-add-channel UC2Prp3t7Ol-a041FXTyCzNQ # Kampiapina  
python3 bottiapina-cli.py db-add-channel UCKmHOEIHQyakrhBQrf6z9Yg # Velogi  
python3 bottiapina-cli.py db-add-channel UCQDefGnTJGWnangzTnFNFhQ # ketjurevoluutio  
python3 bottiapina-cli.py db-add-channel UCumq7OOwpV23wGKlsm5bZqg # tapio-t  
python3 bottiapina-cli.py db-add-channel UCITuIFItrLMDpI44cjB1c_w # resupekka  
python3 bottiapina-cli.py db-add-channel UCG90HVVPlJ47ABh-7XXEajw # paulus  
python3 bottiapina-cli.py db-add-channel UC9STmnDzGHmiggXaldum7fg # samulione  
python3 bottiapina-cli.py db-add-channel UCOR6LpQCATsc55L-dyw9IoA # aleksi sanaksenaho  
python3 bottiapina-cli.py db-add-channel UCFSZyCE-UD0LtDP3Lvdk6gg # japen pyöräjutut  
python3 bottiapina-cli.py db-add-channel UCbZNGF8yVfa3dJKh7oE3iTA # viiksivelo  
python3 bottiapina-cli.py db-add-channel UCcBjJffYj4QB1ngg6St8giQ # utelias mieli  
python3 bottiapina-cli.py db-add-channel UCjQmJj4F8PcZRByRAXcBXWw # baltsu  
python3 bottiapina-cli.py db-add-channel UCp48RxIksJMaxAcrxsAJr9Q # superpate  
python3 bottiapina-cli.py db-add-channel UCYOIFqlogi0_EYgI2_QQvdw # fillaripäiväkirja  
python3 bottiapina-cli.py db-add-channel UChqBVvX3faw5Saf_6aBmDnQ # pelkkää alamäkeä  
python3 bottiapina-cli.py db-add-channel UCafr-brvPH5blLgxN6YhQkg # alanko ulkoilee  
python3 bottiapina-cli.py db-add-channel UC9s3_papfs8fSXdw-dUwbBA # polkuaddikti  
python3 bottiapina-cli.py db-add-channel UCKeDoCURs8VBtyrsJlsCjIA # sarpale  
python3 bottiapina-cli.py db-add-channel UCOE9Idh-XjDCxwc-LjfNo9g # masa  
python3 bottiapina-cli.py db-add-channel UCZkfDgS6O6z0EwjVPJBipGQ # mikko vulli  
python3 bottiapina-cli.py db-add-channel UCKeHwycZltSbByaRxuS34yQ # gravelsoturi  
python3 bottiapina-cli.py db-add-channel UCPCkw_Z-qdThcIqAcR_Lmbw # damuride  
python3 bottiapina-cli.py db-add-channel UCt-5eWIwd3PvIr_VQ4QOb1g # pakkopolkee  
python3 bottiapina-cli.py db-add-channel UC-OUJ1YPoman9bBeN8Kk0gA # rikun mtb juttuja  
python3 bottiapina-cli.py db-add-channel UC51syC8PWYK7XQ9yin_96fA # activelifeinfinland  
python3 bottiapina-cli.py db-add-channel UCd6k7GfrOpLlFabSplva7OA # saukki  
python3 bottiapina-cli.py db-add-channel UClGzNxV6GrPi4NyYvoEgZDw # Puhutaan pyöräilystä  
python3 bottiapina-cli.py db-add-channel UCav1yoInd0IJ5wcNxkrd6PQ # Pyöräily, retkeily, elämä
python3 bottiapina-cli.py db-add-channel UCh2dBsBDCgoK8Lfn7xuIENg # Iskus
python3 bottiapina-cli.py db-add-channel UClW8fnS0yeCMGEjCKd7OlHg # pekka tahkola 
python3 bottiapina-cli.py db-add-channel UCcm-lEm1Oh72LXh_HIuRsoQ # tero niemel�
python3 bottiapina-cli.py db-add-channel UCzEv8zvMz9LMKBajhzhBEyA # mika kimmo
