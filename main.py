import discord  # development branch 2.0.0a to be able to use Views, Interactions
from discord.ext import commands
import logging
import globals

logging.basicConfig(level=logging.INFO)

intents = discord.Intents(messages=True, members=True, guilds=True, message_content=True)
bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot

import commands
import requestEntry
import db
import tokenFile


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    print(f'discord.py version = {discord.__version__}')
    globals.guild = bot.get_guild(globals.guildID)
    globals.mainChannel = bot.get_channel(globals.mainChannelID)

    # populate the global event vars if bot is restarted while event is already active
    eventTitle, eventTime, eventMessageID = db.get_event()
    if eventMessageID:
        globals.eventInfo = eventTitle + ' @ ' + eventTime
        globals.eventMessageID = eventMessageID

    await globals.mainChannel.send(f'{bot.user.name} connected!')
    db.sql_write.start()    # start the sql_write loop that executes sql writes every # seconds
    # await bot.change_presence(activity = discord.SOMETHING)

if __name__ == "__main__":
    bot.run(tokenFile.token)
