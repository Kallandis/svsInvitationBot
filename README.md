# svsInvitationBot
Developed for 1508 Discord server and associated servers. 
Stores users' submitted in-game information in a database, and allows them to sign up for events created by admins
Written with discord.py

## Requirements
requirements.txt for most modules

Requires discord.py version >= 2.0.0, which is still in development as of 22/5/8
Until its official release, must install from latest branch https://github.com/Rapptz/discord.py

## Inviting the bot to your server
My personal invite link: 
https://discord.com/api/oauth2/authorize?client_id=964610834041045043&permissions=124928&scope=bot
see "add_bot_to_server_instructions.txt" for details

Privileged Intents: Needs "Server Members", "Message Content" 

## Configuring the bot
I don't know how to make a config file, so user-config is currently done in globals.py

## Running the bot
If this is your first time running the bot, first run `reset_db.py` to create the necessary database files.
Otherwise, just run `main.py`
