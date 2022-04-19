import discord
from discord.ext import commands
import logging
import globals

logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True, reactions=True)

bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot

import dm
import db
import tokenFile
import sqlite3 as sql3
import time
import datetime


def in_mainChannel():
    def predicate(ctx):
        return ctx.message.channel == globals.mainChannel
    return commands.check(predicate)


@bot.command(usage="MM/DD/YY")
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def create_event(ctx, *, datestring):
    """
    Creates event for the specified date at 11:00AM PST
    Requires ADMIN Role
    """
    # check if invoker is ADMIN and channel is mainChannel
    # if not ('ADMIN' in ctx.author.roles and ctx.channel == globals.mainChannel):
    #     return

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
    globals.event_info = title + ' @ ' + descr.split('\n')[0]

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_gold())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❔")
    await msg.add_reaction("❌")

    # start the sql_write loop that executes sql writes every 30 seconds
    db.sql_write.start()


@bot.command(usage="pass")
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def edit_event(ctx, *, arg):
    """
    """
    with sql3.connect('userHistory.db') as conn:
        db.reset_event(conn)
    pass


@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def delete_event(ctx):
    """
    """
    with sql3.connect('userHistory.db') as conn:
        db.reset_event(conn)
    pass


@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def mail_csv(ctx):
    """
    Close signups and send sorted .csv of attendees to command user
    Calls fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Requires ADMIN role
    """

    pass


@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def mail_db(ctx):
    """
    Sends dump of SQL database to user
    Requires ADMIN role
    """
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

    # check if message is in the dedicated event channel, and react author is not a bot
    if payload.channel_id != globals.mainChannel.id or payload.member.bot:
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

        db.update_status(member.id, status)
        await dm.ack_change(member)

    await status_logic()


@bot.event
async def on_raw_reaction_remove(payload):
    """
    If user removes reaction, must update their status to NO
    """
    pass

# commented out so that I can see error MSG for $help in private channel not working

# @bot.event
# async def on_command_error(ctx, error):
#     # generic error handling
#     errmsg = "ERROR: "
#     if isinstance(error, commands.MissingRequiredArgument):
#         errmsg += "Missing argument.\n"
#     elif isinstance(error, commands.PrivateMessageOnly):
#         errmsg += "Command must be used in DM.\n"
#     elif isinstance(error, commands.NoPrivateMessage):
#         errmsg += "Command only works in DM.\n"
#     elif isinstance(error, commands.BotMissingRole):
#         errmsg += "Bot lacks required role for this command.\n"
#     elif isinstance(error, commands.BotMissingPermissions):
#         errmsg += "Bot lacks required permissions for this command.\n"
#     elif isinstance(error, commands.MissingRole):
#         errmsg += "User lacks required role for this command.\n"
#     elif isinstance(error, commands.MissingPermissions):
#         errmsg += "User lacks required permissions for this command.\n"
#
#     errmsg += "$help [command] for specific info. $help for generic info"
#     await ctx.send(errmsg)


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    globals.mainChannel = bot.get_channel(964654664677212220)   # svsBotTestServer/botchannel
    await globals.mainChannel.send(f'{bot.user.name} connected!')
    # await bot.change_presence(activity = discord.SOMETHING)


if __name__ == "__main__":
    bot.run(tokenFile.token)
