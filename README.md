# svsInvitationBot
Developed for 1508 Discord server and associated servers

Stores users' submitted in-game information in a database and allows them to sign up for events created by admins

Written with discord.py

## Requirements
Most modules can be installed with `python -m pip install -r requirements.txt`

However, the bot requires discord.py version >= 2.0.0, which is still in development as of 2022/5/8

Until its official release, must install from latest branch https://github.com/Rapptz/discord.py

## Inviting the bot to your server
My personal invite link: 

https://discord.com/api/oauth2/authorize?client_id=964610834041045043&permissions=124928&scope=bot

(see `add_bot_to_server_instructions.txt` for details)

Privileged Intents: Needs "Server Members", "Message Content" 

## Configuring the bot
I don't know how to make a config file, so user-config is currently done in globals.py

You must set various server-specific parameters, such as: 

* `MAIN_CHANNEL_ID_LIST` : list of the channels that events should be restricted to 
* `ADMIN_ROLE_NAME` : Role name that certain privileged commands are to be restricted behind
* `COMMAND_PREFIX`
* `LOGO_URL` : URL of the image to display with embeds (optional)
* `CSV_FILENAME` : Filename to use for created CSVs
* `NUMBER_OF_LOTTO_WINNERS` : Number of attendees to select for lottery winnings
* `CONFIRM_MAYBE_WARNING_HOURS` : Number of hours before the event that users who signed up as "MAYBE" should be reminded (set to 0 to never send reminder)
* `SEND_{HELP, ERROR}_TO_DM` : Flags to determine if `help` and `error` messages should be sent to the user's DM
* `BUG_REPORT_CHANNEL_ID` : Channel ID that bug reports logged with command `bug` are sent to (optional)

The channels in `MAIN_CHANNEL_ID_LIST` can be in different servers, but all servers must have an admin-role with the *same name*.

## Running the bot
If this is your first time running the bot, first populate `globals.py` with the necessary variables, then run `reset_db.py` to create the databases

You will also need to create a file `tokenFile.py` and populate it with `token=MY_BOT_TOKEN`

Otherwise, just run `main.py`
