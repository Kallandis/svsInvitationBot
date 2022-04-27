import discord
from discord.ext import commands
import globals
import db
import time
import datetime
from eventInteraction import EventButtonsView
from professionInteraction import ProfessionMenuView
from requestEntry import request_entry
from asyncio import TimeoutError
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# hard to pass the info from these custom decorators to on_error(), not worth using
# # custom decorator to check if command was used in a valid channel
# def in_mainChannels():
#     def predicate(ctx):
#         return ctx.message.channel in globals.mainChannels
#     return commands.check(predicate)
#
#
# # custom decorator to check if command was used in the active event channel, if it exists
# def in_validEventChannel():
#     def predicate(ctx):
#         if globals.activeEventChannel is not None:
#             return ctx.message.channel == globals.activeEventChannel
#         else:
#             return True
#     return commands.check(predicate)


@globals.bot.command(usage="MM/DD/YY")
@commands.has_role(globals.adminRole)
@commands.guild_only()
async def create_event(ctx, *, datestring):
    """
    Creates event for the specified date at 11:00AM PST
    Requires ADMIN Role
    """

    # check if there is an active event
    if globals.eventChannel is not None:
        if ctx.channel != globals.eventChannel:
            await ctx.send(f'ERROR: An event is already active in {globals.eventChannel.mention}.\n'
                           f'Only one event at a time may be active.')
        elif ctx.channel == globals.eventChannel:
            await ctx.send(f'```ERROR: An event is already active in this channel.\n'
                           f'$delete_event to delete the active event.```')
        return

    # parse MM/DD/YY from command input
    arg = [int(x) for x in datestring.split('/')]
    month, day, year = arg
    if year < 2000:
        year += 2000

    # TODO: use discord time function instead? not sure about timezones
    # convert MM/DD/YY to unix time
    date_time = datetime.datetime(year, month, day, 11, 0)
    unix_time = int(time.mktime(date_time.timetuple()))

    # build title and dynamic timestamp for embed
    title = "SvS Event"
    eventTime = f"<t:{unix_time}>"

    # and then format them up a bit
    eventInfo = title + ' @ ' + eventTime
    descr = '@ ' + eventTime + '\n\n'
    descr += "It's an SvS Event"
    descr += '\n\u200b'

    # create embed and add fields
    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_red())
    embed.add_field(name=f"{'YES':<20}", value="\u200b")
    embed.add_field(name=f"{'MAYBE':<20}", value="\u200b")
    embed.add_field(name=f"{'NO':<20}", value="\u200b")

    # create footer
    cmdList = ['edit_event', 'delete_event', 'mail_csv', 'mail_db']
    cmdList = [globals.commandPrefix + cmd for cmd in cmdList]
    embed.set_footer(text=', '.join(cmdList))

    # get the file to be sent with the event embed
    if globals.logoPath:
        filename = globals.logoPath.split('\\')[-1]
        attachments = [discord.File(globals.logoPath, filename=filename)]
        embed.set_thumbnail(url=f'attachment://{filename}')
    else:
        attachments = []

    # send event embed
    eventMessage = await ctx.send(embed=embed)

    # add the view to event embed. Updating of status, database, and embed fields will be handled in
    # eventInteraction.py through user interactions with the buttons.
    view = EventButtonsView(eventMessage)
    # await eventMessage.edit(embed=embed, view=view, attachments=attachments)
    await eventMessage.edit(embed=embed, view=view, attachments=attachments)

    # set globals to reduce DB accessing
    globals.eventInfo = eventInfo
    # globals.eventMessageID = eventMessage.id
    globals.eventMessage = eventMessage
    globals.eventChannel = ctx.channel

    # store event data in eventInfo.db
    db.update_event(title, eventTime, eventMessage.id, ctx.channel.id)


@globals.bot.command(usage="pass")
@commands.has_role(globals.adminRole)
@commands.guild_only()
async def edit_event(ctx, *, arg):
    """
    Edit the existing event
    Does not change the status of current attendees
    """
    if globals.eventChannel is None:
        await ctx.send(f'ERROR: No active event found')
        return
    elif ctx.channel != globals.eventChannel:
        await ctx.send(f'ERROR: Must use command in {globals.eventChannel.mention}')
        return

    pass


@globals.bot.command()
@commands.has_role(globals.adminRole)
@commands.guild_only()
async def delete_event(ctx, intent='delete'):
    """
    Sets eventInfo.db to default value
    Sets everyone's status to "NO"
    Empties the sql_write() "buffer"
    """

    # check if there is currently an event
    if globals.eventChannel is None:
        await ctx.send(f'ERROR: No active event found')
        return
    # if there is an event, check if it is in this channel
    elif ctx.channel != globals.eventChannel:
        await ctx.send(f'ERROR: Must use command in {globals.eventChannel.mention}')
        return

    user = ctx.author
    if user.dm_channel is None:
        await user.create_dm()
    dmChannel = user.dm_channel

    # prompt the user to send "confirm" in dmChannel to confirm their command
    timeout = 60
    prompt = ''
    if intent == 'delete':
        prompt += f'Type "confirm" within {timeout} seconds to confirm you want to delete the event.'
    elif intent == 'close':
        prompt += f'Type "confirm" within {timeout} seconds ' \
                  f'to confirm you want to close signups and send a CSV of attendees.'
    prompt = await user.dm_channel.send(prompt)

    try:
        reply = await globals.bot.wait_for('message', timeout=timeout, check=lambda m: m.channel == dmChannel)
    except TimeoutError:
        edit = f'No response received in {timeout} seconds, event **{intent}** aborted'
        await prompt.edit(edit)
        return

    # check if they responded with "confirm"
    if reply.content.lower() != 'confirm':
        edit = f'Event **{intent}** aborted'
        await prompt.edit(edit)
        return
    else:
        edit = f'Event **{intent}** successful'
        await prompt.edit(edit)

    # remove the eventMessage buttons, set the top-line of description to "this event is closed for signups"
    eventEmbed = globals.eventMessage.embeds[0]
    eventAttachments = globals.eventMessage.attachments

    content = '```This event is closed for signups.```'
    await globals.eventMessage.edit(content=content, view=None)

    # reset global vars
    globals.eventInfo = ''
    # globals.eventMessageID = 0
    globals.eventMessage = None
    globals.eventChannel = None

    # reset database
    db.update_event('placeholder', 'placeholder', 0, 0)
    db.reset_status()


@globals.bot.command()
@commands.has_role(globals.adminRole)
@commands.guild_only()
async def mail_csv(ctx):
    """
    Close signups and send sorted .csv of attendees to user
    Calls fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Requires ADMIN role
    """

    if globals.eventChannel is None:
        await ctx.send(f'ERROR: No active event found')
        return
    elif ctx.channel != globals.eventChannel:
        await ctx.send(f'ERROR: Must use command in {globals.eventChannel.mention}')
        return

    pass


@globals.bot.command()
@commands.has_role(globals.adminRole)
@commands.guild_only()
async def mail_db(ctx):
    """
    Sends dump of SQL database to user
    Requires ADMIN role
    """

    if ctx.author.dm_channel is None:
        await ctx.author.create_dm()
    dmChannel = ctx.author.dm_channel

    db.dump_db('svs_userHistory_dump.sql')
    await dmChannel.send(attachments=[discord.File('svs_userHistory_dump.sql')])
    pass


@globals.bot.command()
@commands.dm_only()
async def prof(ctx, *, intent=None):
    """
    $prof (no argument) to edit profession, $prof ? to show profession

    If the user is not in the database, prompts user to provide a database entry

    Else, sends the user either a ProfessionMenuView view object to change their profession, or an info embed made with
    db.info_embed() to show their database information
    """

    member = ctx.author
    ID = member.id

    intentDict = {None: "edit", "?": "show"}
    intent = intentDict.get(intent, None)
    if intent is None:
        msg = "```USAGE:\n$prof to edit profession\n$prof ? to show profession```"
        await ctx.send(msg)
        return

    entry = db.get_entry(ID)
    if not entry:   # check if user has been registered in DB. if not, register them
        await request_entry(member)

    elif intent == "edit":
        msg = await ctx.send(content="Enter profession. Menu will disappear in 5 minutes.")
        view = ProfessionMenuView(msg, 'class')
        await msg.edit(view=view)

    elif intent == "show":
        file, embed = db.info_embed(entry)
        kwargs = {'file': file, 'embed': embed} if file else {'embed': embed}
        await ctx.send(**kwargs)


@globals.bot.command()
@commands.dm_only()
async def lottery(ctx):
    """
    Toggles lottery opt in/out
    """
    member = ctx.author
    ID = member.id
    entry = db.get_entry(ID)

    if not entry:
        await request_entry(member)
    else:
        lotto = 1 - entry[7]
        lotto_in_out = 'in to' if lotto else 'out of'
        msg = f'You have opted ' + lotto_in_out + ' the lottery\n'
        db.update_lotto(ID, lotto)
        # await ctx.send('```' + msg + '```')
        # code blocks look nice, but they break time and message-link formatting. So don't use for consistency
        await ctx.send(msg)


# @globals.bot.event
# async def on_command_error(ctx, error):
#     logger.error(str(error))
#
#     # command has local error handler
#     if hasattr(ctx.command, 'on_error'):
#         return
#
#     # generic error handling
#     errmsg = f"{ctx.command} ERROR: "
#     if isinstance(error, commands.CheckFailure):
#         errmsg += str(error) + '\n'
#     elif isinstance(error, commands.MissingRequiredArgument):
#         errmsg += "Missing argument.\n"
#     elif isinstance(error, commands.NoPrivateMessage):
#         errmsg += "Command does not work in DM.\n"
#     elif isinstance(error, commands.BotMissingRole):
#         errmsg += "Bot lacks required role for this command.\n"
#     elif isinstance(error, commands.BotMissingPermissions):
#         errmsg += "Bot lacks required permissions for this command.\n"
#     elif isinstance(error, commands.MissingRole):
#         errmsg += "User lacks required role for this command.\n"
#     elif isinstance(error, commands.MissingPermissions):
#         errmsg += "User lacks required permissions for this command.\n"
#     else:
#         errmsg += 'Unknown error.\n'
#
#     errmsg += f"$help {ctx.command} for specific info. $help for list of commands."
#     await ctx.send(f'```{errmsg}```')
