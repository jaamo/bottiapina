# Bottiapina Discord bot

This bot monitors given YouTube channels and posts a notification to Discord channel when new videos are published.

## Required packages

- discord.py
- google-api-python-client
- google-auth-oauthlib
- google-auth-httplib2

## Installation

1. Clone this repo
1. Create Discord bot according to this tutorial https://realpython.com/how-to-make-a-discord-bot-python/
1. Create YouTube API key according to this tutorial (only API key required, OAuth2 is not) https://developers.google.com/youtube/v3/quickstart/python
1. Enable Discord developer mode: User settings -> Advanced -> Developer mode
1. Find a Discord channel you want to use and right click it to get the channel ID
1. Use this site to obtain YouTube channel id https://commentpicker.com/youtube-channel-id.php
1. Copy .env.example to .env and fill in Discord and YouTube parameters
1. Install dependencies: `pip install discord.py google-api-python-client google-auth-oauthlib google-auth-httplib2 python-dotenv`
1. Setup database: `python bottiapina-cli.py db-reset`
1. Add YouTube channels: `python bottiapina-cli.py db-add-channel [channel id]`
1. Start the bot: `python bottiapina.py`

## CLI usage

There is a simple command line interface for managing the bot.

CLI usage:

`python bottiapina-cli.py update-new-videos`

To see available commands:

`python bottiapina-cli.py`

## Related documentation:

- https://discord.com/developers/applications/
- https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python
- https://developers.google.com/youtube/v3/quickstart/python
- https://commentpicker.com/youtube-channel-id.php

python3 bot.py

Channel ids:
Kampiapina UC2Prp3t7Ol-a041FXTyCzNQ
Velogi UCKmHOEIHQyakrhBQrf6z9Yg
