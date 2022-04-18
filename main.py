import discord
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle
import logging

import db
import tokenFile
import globals
import time
import datetime
import sqlite3 as sql3

logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True, reactions=True)

bot = commands.Bot(command_prefix='$', intents=intents)
globals.bot = bot


@bot.command()
async def create_event(ctx, *, datestring):
    """
    $create_event MM/DD/YY
    Creates event for the specified date at 11:00AM PST
    Requires ADMIN Role
    """
    # if 'ADMIN' not in ctx.author.roles:
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

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_gold())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❔")
    await msg.add_reaction("❌")


@bot.event
async def on_raw_reaction_add(payload):
    # check if message is in the dedicated event channel
    if payload.channel_id != globals.mainChannel.id:
        return

    message = await globals.mainChannel.fetch_message(payload.message_id)
    member = payload.member

    # exit if message has no embeds (and thus is not event message)
    if not message.embeds:
        return

    # remove other reactions from user (This is pretty slow and can break, might not be worth including)
    for rxn in message.reactions:
        if member in await rxn.users().flatten() and not member.bot and str(rxn) != str(payload.emoji):
            await message.remove_reaction(rxn.emoji, member)

    rxnDict = {
        "✅": "YES",
        "❔": "MAYBE",
        "❌": "NO"
    }
    status = rxnDict.get(str(payload.emoji), None)
    if status is None:
        logging.debug(f"IMPROPER REACTION: {str(payload.emoji)}")
        return

    conn = sql3.connect("userHistory.db")

    # check if user is in DB. If yes, proceed. If no, must create a new entry and prompt them to respond to DM asking
    # for their role. If they do not respond within 1hr, or if the CSV is built, their status will be changed to "NO"

    db.update_status(conn, member.id, status)
    conn.commit()
    conn.close()
    await member.create_dm()


# @bot.event
# async def on_button_click(ctx, button):
#     # ID = interaction.component.custom_id
#
#     print(button)
#     print(button.custom_id)
#     # member = interaction.author
#     member = ctx.author
#     await member.create_dm()
#     await member.dm_channel.send(f"You pressed {button.custom_id}")


@bot.command()
async def edit_event():
    """
    USAGE: pass
    """
    pass


@bot.command()
async def delete_event():
    """
    USAGE: pass
    """
    pass


@bot.command()
async def mail_event_attendees(ctx):
    """
    USAGE: pass
    Call fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Send sorted .csv of attendees to command user
    Will be copy-pasted into Excel for highlighting and visual decoration?
    """
    pass


@bot.command()
async def mail_db(ctx):
    """
    $mail_db
    Sends dump of SQL database to user
    Requires ADMIN role
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
