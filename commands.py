import discord
from discord.ext import commands
import globals
import db
import time
import datetime
from eventInteraction import EventButtonsView
from professionInteraction import ProfessionMenuView
from requestEntry import request_entry


# custom decorator to check if command was used in globals.mainChannel
def in_mainChannels():
    def predicate(ctx):
        return ctx.message.channel in globals.mainChannels
    return commands.check(predicate)


@globals.bot.command(usage="MM/DD/YY")
@commands.has_role(globals.adminRole)
@in_mainChannels()
async def create_event(ctx, *, datestring):
    """
    Creates event for the specified date at 11:00AM PST
    Requires ADMIN Role
    """

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

    eventInfo = title + ' @ ' + eventTime
    descr = "It's an SvS Event"
    descr = '@ ' + eventTime + '\n' + descr

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_red())
    embed.add_field(name=f"{'YES':<20}", value="\u200b")
    embed.add_field(name=f"{'MAYBE':<20}", value="\u200b")
    embed.add_field(name=f"{'NO':<20}", value="\u200b")

    cmdList = ['$edit_event', '$delete_event', '$mail_csv', '$mail_db']
    embed.set_footer(text=', '.join(cmdList))

    # event embed
    eventMessage = await ctx.send(embed=embed)
    # add the view to event embed. Updating of status, database, and embed fields will be handled in
    # eventInteraction.py through user interactions with the buttons.
    view = EventButtonsView(eventMessage)
    await eventMessage.edit(embed=embed, view=view)

    # set globals to reduce DB accessing
    globals.eventInfo = eventInfo
    globals.eventMessageID = eventMessage.id

    # store event data in eventInfo.db
    db.update_event(title, eventTime, eventMessage.id)


@globals.bot.command(usage="pass")
@commands.has_role(globals.adminRole)
@in_mainChannels()
async def edit_event(ctx, *, arg):
    """
    Edit the existing event
    Does not change the status of current attendees
    """
    pass


@globals.bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannels()
async def delete_event(ctx):
    """
    Sets eventInfo.db to default value
    Sets everyone's status to "NO"
    Empties the sql_write() "buffer"
    """
    db.update_event('placeholder', 'placeholder', 0)
    db.reset_status()


@globals.bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannels()
async def mail_csv(ctx):
    """
    Close signups and send sorted .csv of attendees to user
    Calls fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
    Requires ADMIN role
    """
    pass


@globals.bot.command()
@commands.has_role(globals.adminRole)
@in_mainChannels()
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


@globals.bot.command()
@commands.dm_only()
async def prof(ctx, *, intent=None):
    """
    $prof (no argument) to edit profession, $prof ? to show profession
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
    Toggles lottery opt in/out status
    """
    member = ctx.author
    ID = member.id
    entry = db.get_entry(ID)

    if not entry:
        await request_entry(member)
    else:
        lotto = 1 - entry[7]
        lotto_in_out = 'in to' if lotto else 'out of'
        msg = f'You have opted ' + lotto_in_out + ' the lottery.\n'
        db.update_lotto(ID, lotto)
        await ctx.send('```' + msg + '```')


# @globals.bot.event
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
#     else:
#         logging.error(str(error))
#         errmsg += 'Unknown error.\n'
#
#     errmsg += "$help [command] for specific info. $help for generic info"
#     await ctx.send(errmsg)
