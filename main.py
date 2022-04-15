import discord
from discord.ext import commands
import logging
import tokenFile
import globals

logging.basicConfig(level=logging.INFO)
globals.client = discord.Client()

bot = commands.Bot(command_prefix='$')


@bot.command()
async def create_event(ctx, *, arg):
    pass


@create_event.error
async def create_event_error(ctx, error):
    if isinstance(error, create_event.BadArgument):
        await ctx.send('I could not find that member')
    else:
        await ctx.send('Unknown error')


@bot.command()
async def edit_event():
    pass


@bot.command()
async def delete_event():
    pass


@bot.command()
async def mail_event_attendees(ctx):
    """
    Call fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Send sorted .csv of attendees to command user
    Will be copy-pasted into Excel for highlighting and visual decoration?
    """
    pass


@bot.command()
async def mail_db(ctx):
    """Send a copy of the long-term db to command user"""
    pass


globals.client.run(tokenFile.token)
