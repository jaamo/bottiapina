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
1. Run `source .venv/bin/activate` if you are using venv
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

## Production deployment :D

`rsync ./*.py pi@192.168.1.75:/home/pi/bottiapina/`

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
