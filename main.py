import discord  # development branch 2.0.0a to be able to use Views, Interactions
from discord.ext import commands
import logging
import globals
import sys
import traceback

import tokenFile

logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
                    datefmt='%Y/%m/%d %H:%M:%S (UTC%z)')


# log uncaught exceptions
def handler(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        logging.exception(line)
    logging.exception(value)

    sys.__excepthook__(type, value, tb)     # calls default excepthook


sys.excepthook = handler


# create the bot
intents = discord.Intents(messages=True, members=True, guilds=True, message_content=True)
bot = commands.Bot(command_prefix=globals.commandPrefix,
                   intents=intents,
                   description='Manages event attendance and user history',
                   allowed_mentions=discord.AllowedMentions(everyone=False, roles=False)
                   )


globals.bot = bot

import help
import my_commands
import db
from eventInteraction import EventButtonsView


def setup():
    pass


def reload():
    # repopulate global variables to restore bot's state if bot restarts
    # most importantly, must restore EventButtonsView.last_statuses, to make the event embed not think everyone is new
    # that should be just a simple loop through the database
    pass


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    print(f'discord.py version = {discord.__version__}')

    # populate global guild-related variables

    # guild
    globals.guild = bot.get_guild(globals.guildID)
    if globals.guild is None:
        error = 'Failed to acquire server.'
        logging.error(error)
        sys.exit(error)

    # channels
    for _id in globals.mainChannelIDs:
        globals.mainChannels.append(bot.get_channel(_id))
    if not all(globals.mainChannels):
        error = 'Failed to acquire at least one channel.'
        logging.error(error)
        sys.exit(error)

    globals.bugReportChannel = bot.get_channel(globals.bugReportChannelID)
    if globals.bugReportChannel is None:
        error = 'Failed to acquire bug report channel'
        logging.error(error)

    # populate the global event vars if bot is restarted while event is already active
    eventTitle, eventTime, eventMessageID, eventChannelID = await db.get_event()
    if eventMessageID:
        globals.eventInfo = eventTitle + ' @ ' + eventTime
        # globals.eventMessageID = eventMessageID
        globals.eventChannel = bot.get_channel(eventChannelID)
        globals.eventMessage = await globals.eventChannel.fetch_message(eventMessageID)

        # re-initializes EventButtonsView instance so that buttons still work
        view = EventButtonsView(globals.eventMessage)
        await globals.eventMessage.edit(view=view)

    # add cogs
    await bot.add_cog(my_commands.DM(bot))
    await bot.add_cog(my_commands.Event(bot))
    await bot.add_cog(my_commands.Misc(bot))
    await bot.add_cog(help.Help(bot))


if __name__ == "__main__":
    bot.run(tokenFile.token)
    # await bot.start(tokenFile.token)
