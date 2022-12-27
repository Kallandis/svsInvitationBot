#!/home/pi/python_projects/svs_bot/.venv/bin/python3

import discord  # development branch 2.0.0a to be able to use Views, Interactions
import logging
import sys
import os
import datetime
import traceback
import asyncio

import my_bot
import tokenFile
import svsBot.globals as globals


def setup_logs():
    # logs directory
    logsdir = '/svsbotlogs'
    homedir = os.path.expanduser('~')
    if not os.path.exists(homedir + logsdir):
        os.mkdir(homedir + logsdir)
    
    # make a new logfile every time bot restarts
    timestr = str(datetime.datetime.now())
    timestr = timestr[2:]
    timestr = timestr.replace(' ', '_')
    timestr = timestr.replace('-', '')
    timestr = timestr.replace(':', '')
    logfile = timestr.split('.')[0]
    logfile = 'log_' + logfile
    logfile = homedir + logsdir + '/' + logfile
    
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        format='%(asctime)s - [%(levelname)s] [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S (UTC%z)')
    
    # handler for logging uncaught exceptions
    def handler(type, value, tb):
        for line in traceback.TracebackException(type, value, tb).format(chain=True):
            logging.exception(line)
        logging.exception(value)
    
        sys.__excepthook__(type, value, tb)     # calls default excepthook
    
    # send exceptions to handler
    sys.excepthook = handler


def setup_bot():
    # parameters for bot initialization
    bot_init_args = {
        'command_prefix': globals.COMMAND_PREFIX,
        'intents': discord.Intents(messages=True, members=True, guilds=True, message_content=True),
        'description': 'Manages event attendance and user history',
        'allowed_mentions': discord.AllowedMentions(everyone=False, roles=False),
        'activity': discord.Game(name=f'{globals.COMMAND_PREFIX}help')
    }

    # initialize bot
    bot = my_bot.Bot(bot_init_args)
    # globals.bot = bot
    return bot


async def main():
    async with bot:
        await bot.start(tokenFile.token)

if __name__ == "__main__":
    setup_logs()
    bot = setup_bot()
    asyncio.run(main())
