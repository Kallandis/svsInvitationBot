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
import time
import datetime


# decorator to check if command was used in globals.mainChannel
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
    eventTime = descr.split('\n')[0]

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_gold())
    embed.add_field(name="YES", value="\u200b")
    embed.add_field(name="MAYBE", value="\u200b")
    embed.add_field(name="NO", value="\u200b")

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❔")
    await msg.add_reaction("❌")

    message_id = msg.id
    # store event data in eventInfo.db
    db.update_event(title, eventTime, message_id)


async def update_event_field(message: discord.Message, name: str, status: str, remove=False):
    embed = message.embeds[0]
    fields = embed.fields
    fieldDict = {
        "YES": 0,
        "MAYBE": 1,
        "NO": 2
    }

    fieldIndex = fieldDict[status]
    fieldName = fields[fieldIndex].name
    fieldValues = fields[fieldIndex].value.split('\n')

    if remove and name in fieldValues:
        print('rem', end=': ')
        fieldValues.remove(name)
    else:
        print('app', end=': ')
        fieldValues.append(name)

    print(f'fieldname: {fieldName}, fieldValues: {fieldValues}')
    fieldValue = '\n'.join(fieldValues)
    embed.set_field_at(fieldIndex, name=fieldName, value=fieldValue)

    await message.edit(embed=embed)


@bot.event
async def on_raw_reaction_add(payload):
    """
    Handles user Reactions to Event posts in dedicated Event channel
    DM commands are used to change registered profession, opt out of lottery
    Event Reactions are used to change status for upcoming event
    """

    # check if message is in the dedicated event channel. Wider scope than checking message_ID, but it's less
    # expensive than accessing the entryInfo.db database for every reaction in the server.
    if payload.channel_id != globals.mainChannel.id:
        return

    # get message and member object from payload
    message = await globals.mainChannel.fetch_message(payload.message_id)
    member = payload.member

    eventTitle, eventTime, eventMessageID = db.get_event()
    # checks if message is the active event. Make sure react author is not a bot
    if message.id != eventMessageID or member.bot:
        return

    rxnDict = {
        "✅": "YES",
        "❔": "MAYBE",
        "❌": "NO"
    }
    # status = None if rxn is not in approved list. Else
    status = rxnDict.get(str(payload.emoji), None)

    # prevent members from adding reacts to the event message. This could also be accomplished by locking "Add Reaction"
    # permission behind a higher-tier role in the server.
    if status is None:
        await message.remove_reaction(payload.emoji, member)
        logging.debug(f"IMPROPER REACTION: {str(payload.emoji)}")
        return

    # if rxn in approved list, remove any other existing reactions to the Event from this Member
    else:
        for rxn in message.reactions:
            if member in await rxn.users().flatten() and not member.bot and str(rxn) != str(payload.emoji):
                await message.remove_reaction(rxn.emoji, member)
                # TODO: test if this works
                # update_event_field(message, member.display_name, status, remove=True)

    async def status_logic():
        # status = rxnDict.get(str(payload.emoji), None)

        entry = db.get_entry(member.id)
        # have to fetch message again, to account for message.remove_reaction() concurrency issues with triggering
        # update_event_field() from on_raw_reaction_remove()
        message = await globals.mainChannel.fetch_message(payload.message_id)
        if not entry:
            success = await dm.request_entry(member, status=status)
            if not success:
                await message.remove_reaction(payload.emoji, member)
                if member.dm_channel is None:
                    await member.create_dm()
                msg = 'Failed to create database entry. You may react to the event to sign up again.'
                await member.dm_channel.send(msg)
                return

        else:
            db.update_status(member.id, status)
            await update_event_field(message, member.display_name, status)

            # only ack change if they registered as YES or MAYBE
            if status != 'NO':
                await dm.ack_change(member, 'status')

    await status_logic()


@bot.event
async def on_raw_reaction_remove(payload):
    """
    If user removes reaction, must update their status to NO
    """

    # message = await globals.mainChannel.fetch_message(payload.message_id)

    eventTitle, eventTime, eventMessageID = db.get_event()

    # only looks at the active event embed
    if payload.message_id != eventMessageID:
        return

    # TODO: figure out the error here. If was ?, then react w/ "chk", it triggers on_raw_rxn_remove(). But it doesn't remove the name from the field properly.
    # If member removed ✅ or ❔, set their status to "NO"
    # Don't need to check for bot b/c bot does not have a database entry
    elif str(payload.emoji) in ["✅", "❔"] and db.get_entry(payload.user_id):
        status = "YES" if str(payload.emoji) == "✅" else "MAYBE"
        member = globals.guild.get_member(payload.user_id)
        db.update_status(member.id, "NO")
        message = await globals.mainChannel.fetch_message(payload.message_id)
        await update_event_field(message, member.display_name, status, remove=True)
        await dm.ack_change(member, 'status')


@bot.command(usage="pass")
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def edit_event(ctx, *, arg):
    """
    Edit the existing event
    Does not change the status of current attendees
    """
    pass


@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def delete_event(ctx):
    """
    Sets eventInfo.db to default value
    Sets everyone's status to "NO"
    Empties the sql_write() "buffer"
    """
    db.update_event('placeholder', 'placeholder', 0)
    db.reset_status()


@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def mail_csv(ctx):
    """
    Close signups and send sorted .csv of attendees to user
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
    if ctx.author.dm_channel is None:
        await ctx.author.create_dm()

    db.dump_db()
    await ctx.author.dm_channel.send(file=discord.File('svs_userHistory_dump.sql'))
    pass


@bot.event
async def on_command_error(ctx, error):
    # generic error handling
    errmsg = "ERROR: "
    if isinstance(error, commands.MissingRequiredArgument):
        errmsg += "Missing argument.\n"
    elif isinstance(error, commands.PrivateMessageOnly):
        errmsg += "Command must be used in DM.\n"
    elif isinstance(error, commands.NoPrivateMessage):
        errmsg += "Command only works in DM.\n"
    elif isinstance(error, commands.BotMissingRole):
        errmsg += "Bot lacks required role for this command.\n"
    elif isinstance(error, commands.BotMissingPermissions):
        errmsg += "Bot lacks required permissions for this command.\n"
    elif isinstance(error, commands.MissingRole):
        errmsg += "User lacks required role for this command.\n"
    elif isinstance(error, commands.MissingPermissions):
        errmsg += "User lacks required permissions for this command.\n"
    else:
        logging.error(str(error))
        errmsg += 'Unknown error.\n'

    errmsg += "$help [command] for specific info. $help for generic info"
    await ctx.send(errmsg)


# temporary function for testing purposes
@bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannel()
async def print_db(ctx):
    pass


@bot.command()
async def foo(ctx, arg):
    eventTitle, eventTime, eventMessageID = db.get_event()
    message = await globals.mainChannel.fetch_message(eventMessageID)
    member = ctx.author
    status = arg.upper()
    await update_event_field(message, member.display_name, status, remove=True)


@bot.event
async def on_ready():
    print(f'{bot.user.name} connected!')
    globals.guild = bot.get_guild(964624340295499857)           # svsBotTestServer
    globals.mainChannel = bot.get_channel(964654664677212220)   # svsBotTestServer/botchannel
    await globals.mainChannel.send(f'{bot.user.name} connected!')
    db.sql_write.start()    # start the sql_write loop that executes sql writes every 30 seconds
    # await bot.change_presence(activity = discord.SOMETHING)


if __name__ == "__main__":
    bot.run(tokenFile.token)
