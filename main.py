import discord
from discord.ext import commands
import logging
import tokenFile
import globals
import time
import datetime
import sqlite3 as sql3

logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True)

bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot


@bot.command()
async def create_event(ctx, *, arg):
    """
    USAGE: $create_event MM/DD/YY
    Creates event for the specified date at 11:00AM PST
    """
    # if 'ADMIN' not in ctx.author.roles:
    #     return

    print(ctx.author.roles)
    arg = [int(x) for x in arg.split('/')]
    month, day, year = arg
    if year < 2000:
        year += 2000
    date_time = datetime.datetime(year, month, day, 11, 0)
    print("date_time: ", date_time)
    print("unix time: ", time.mktime(date_time.timetuple()))
    unix_time = int(time.mktime(date_time.timetuple()))

    title = "SvS Event"
    descr = f"<t:{unix_time}>\nIt's an SvS Event"

    embed = discord.Embed(title=title, description=descr)
    await ctx.send(embed=embed)


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
    """Send a copy of the db dump to command user"""
    pass


@bot.command()
async def repeat(ctx, *, arg):
    await ctx.send(arg)


@repeat.error
async def repeat_error(ctx, error):
    await ctx.send('Error with repeat')


@bot.command()
async def foo(ctx, *, arg):
    embed = discord.Embed(title="BIGTITLE", description=arg)
    await ctx.send(embed=embed)



@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    globals.mainChannel = bot.get_channel(964654664677212220)   # svsBotTestServer/botchannel
    await globals.mainChannel.send(f'{bot.user.name} connected!')


if __name__ == "__main__":
    bot.run(tokenFile.token)
