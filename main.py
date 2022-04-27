import discord  # development branch 2.0.0a to be able to use Views, Interactions
from discord.ext import commands
import logging
import globals

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create the bot
intents = discord.Intents(messages=True, members=True, guilds=True, message_content=True)
bot = commands.Bot(command_prefix=globals.commandPrefix, intents=intents)
globals.bot = bot

import commands
import requestEntry
import db
import tokenFile


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    print(f'discord.py version = {discord.__version__}')

    # populate guild variables
    globals.guild = bot.get_guild(globals.guildID)
    for _id in globals.mainChannelIDs:
        globals.mainChannels.append(bot.get_channel(_id))

    # populate the global event vars if bot is restarted while event is already active
    eventTitle, eventTime, eventMessageID, eventChannelID = db.get_event()
    if eventMessageID:
        globals.eventInfo = eventTitle + ' @ ' + eventTime
        # globals.eventMessageID = eventMessageID
        globals.eventChannel = bot.get_channel(eventChannelID)
        globals.eventMessage = await globals.eventChannel.fetch_message(eventMessageID)

    # start the sql_write loop that executes sql writes every # seconds
    db.sql_write.start()

if __name__ == "__main__":
    bot.run(tokenFile.token)
