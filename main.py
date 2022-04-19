import discord
from discord.ext import commands
import logging
import time
import datetime
import sqlite3 as sql3

import db
import dm
import tokenFile
import globals

logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True, reactions=True)

bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot

sqlEntries = []


@bot.command()
async def create_event(ctx, *, datestring):
    """
    $create_event MM/DD/YY
    Creates event for the specified date at 11:00AM PST
    Requires ADMIN Role
    """
    # check if invoker is ADMIN and channel is mainChannel
    if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
        return

    # parse MM/DD/YY from command input
    arg = [int(x) for x in datestring.split('/')]
    month, day, year = arg
    if year < 2000:
        year += 2000

    # convert MM/DD/YY to unix time
    date_time = datetime.datetime(year, month, day, 11, 0)
    unix_time = int(time.mktime(date_time.timetuple()))

    # build title and dynamic timestamp for embed
    title = "SvS Event"
    descr = f"<t:{unix_time}>\nIt's an SvS Event"

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_gold())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❔")
    await msg.add_reaction("❌")


@bot.command()
async def edit_event(ctx, *, arg):
    """
    USAGE: pass
    """
    if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
        return
    pass


@bot.command()
async def delete_event(ctx):
    """
    USAGE: pass
    """
    if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
        return
    pass


@bot.command()
async def mail_event_attendees(ctx):
    """
    USAGE: pass
    Call fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Send sorted .csv of attendees to command user
    Will be copy-pasted into Excel for highlighting and visual decoration?
    """
    if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
        return
    pass


@bot.command()
async def mail_db(ctx):
    """
    $mail_db
    Sends dump of SQL database to user
    Requires ADMIN role
    """
    if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
        return
    pass


@bot.event
async def on_raw_reaction_add(payload):
    """
    Handles user reaction input to DM or Event posts in dedicated Event channel
    DM reactions used to change registered profession, opt out of lottery
    Event reactions used to change status for upcoming event
    """

    # DEPRECATED: handling DM I/O through commands now
    # check if message is in a dmChannel; if so, pass to dm.on_react()
    # if payload.guild_id is None:
    #     print('dmchannel yep')
    #     dm.on_react(payload)
    #     return

    print(f'guild id: {payload.guild_id}')

    # check if message is in the dedicated event channel
    if payload.channel_id != globals.mainChannel.id:
        return

    # get message and member object from payload
    message = await globals.mainChannel.fetch_message(payload.message_id)
    member = payload.member

    # exit if message has no embeds (and thus is not the event message)
    if not message.embeds:
        return

    # remove other reactions from user (This is pretty slow and can break, might not be worth including)
    for rxn in message.reactions:
        if member in await rxn.users().flatten() and not member.bot and str(rxn) != str(payload.emoji):
            await message.remove_reaction(rxn.emoji, member)

    async def status_logic():
        # build eventString to be passed to DM ACK / Request
        embed = message.embeds[0]
        embedTitle = embed.title
        embedTime = embed.description.split('\n')[0]
        eventString = embedTitle + ' @ ' + embedTime

        rxnDict = {
            "✅": "YES",
            "❔": "MAYBE",
            "❌": "NO"
        }
        status = rxnDict.get(str(payload.emoji), None)

        if status is None:
            logging.debug(f"IMPROPER REACTION: {str(payload.emoji)}")
            return

        with sql3.connect('userHistory.db') as conn:
            entry = db.get_entry(conn, member.id)

        if not entry:
            resp = await dm.request_entry(member)
            if resp is None:
                status = "NO"

        with sql3.connect('userHistory.db') as conn:
            db.update_status(conn, member.id, status)
            await dm.ack_status(conn, member, eventString)

    await status_logic()


@bot.event
async def on_raw_reaction_remove(payload):
    """
    If user removes reaction, DM them that they have been marked as "NO"?
    """
    pass


@bot.event
async def on_command_error(ctx, error):
    # generic error handling
    errmsg = "ERROR: "
    if isinstance(error, commands.MissingRequiredArgument):
        errmsg += "Missing argument. "
    elif isinstance(error, commands.PrivateMessageOnly):
        errmsg += "Command must be used in DM."
    elif isinstance(error, commands.NoPrivateMessage):
        errmsg += "Command only works in DM."
    elif isinstance(error, commands.BotMissingRole):
        errmsg += "Bot lacks required role for this command."
    elif isinstance(error, commands.BotMissingPermissions):
        errmsg += "Bot lacks required permissions for this command."
    elif isinstance(error, commands.MissingRole):
        errmsg += "User lacks required role for this command."
    elif isinstance(error, commands.MissingPermissions):
        errmsg += "User lacks required permissions for this command."

    errmsg += "$help [command] for specific info. $help for generic info"
    await ctx.send(errmsg)


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    globals.mainChannel = bot.get_channel(964654664677212220)   # svsBotTestServer/botchannel
    await globals.mainChannel.send(f'{bot.user.name} connected!')
    # await bot.change_presence(activity = discord.SOMETHING)


if __name__ == "__main__":
    bot.run(tokenFile.token)
