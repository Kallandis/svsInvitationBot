import discord
from discord.ext import commands
import logging
import tokenFile
import globals


logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True)

bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot


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


@bot.command()
async def repeat(ctx, *, arg):
    await ctx.send(arg)


@repeat.error
async def repeat_error(ctx, error):
    await ctx.send('Error with repeat')


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    globals.mainChannel = bot.get_channel(964654664677212220)   # svsBotTestServer/botchannel
    await globals.mainChannel.send(f'{bot.user.name} connected!')


# globals.client.run(tokenFile.token)
bot.run(tokenFile.token)
