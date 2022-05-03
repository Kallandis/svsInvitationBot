import discord
from discord.ext import commands, tasks
import globals
import db
import time
import datetime

from eventInteraction import EventButtonsView
from professionInteraction import ProfessionMenuView
import helpers

import logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.ERROR)


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx) -> bool:
        if ctx.channel.id not in globals.mainChannelIDs:
            raise commands.CheckFailure('Command used outside of allowed channels.')
        if ctx.author not in globals.adminRole.members:
            raise commands.MissingRole(f'User does not have required role \"{globals.adminRole.name}\".')
        if globals.eventChannel is not None:
            # special cases for $create
            if ctx.command.name == 'create':
                if ctx.channel != globals.eventChannel:
                    raise commands.CheckFailure(f'An event is already active in {globals.eventChannel.mention}. Only '
                                                f'one event may be active at a time.')
                elif ctx.channel == globals.eventChannel:
                    raise commands.CheckFailure(f'An event is already active in this channel. {ctx.clean_prefix}delete '
                                                f'to delete the active event.')

            # other commands just need to be in the active event channel if it exists
            else:
                if globals.eventChannel is None:
                    raise commands.CheckFailure('No active event.')
                elif ctx.channel != globals.eventChannel:
                    raise commands.CheckFailure(f'Must use command in {globals.eventChannel.mention}.')

        return True

    @commands.command(help='Creates event at time (PST, 24hr format).\n'
                           'Must be used in a valid server channel when there is not an active event.\n'
                           'Requires ADMIN.\n'
                           '\u200b\n'
                           'If <title> or <description> are not one word, they must be enclosed in \"\"\n'
                           f'Example: {globals.commandPrefix}create 22/7/3 15 \"My Event\" \"This is an event\"',
                      usage='<yy/mm/dd> <hh> <\"title\"> <\"description\">')
    @commands.max_concurrency(1)
    async def create(self, ctx, datestring, hour: int, title, descr):
        """
        Creates event with title and description for specified date and time in PST
        Can only be used in a valid server channel, when there is not currently an active event
        Requires ADMIN Role
        """

        # parse YY/MM/DD from command input
        try:
            year, month, day = [int(x) for x in datestring.split('/')]
            if year < 2000:
                year += 2000
            # convert to unix time
            date_time = datetime.datetime(year, month, day, hour, 0)
            unix_time = int(time.mktime(date_time.timetuple()))

            # get time until event
            td = datetime.timedelta(seconds=unix_time - time.time())
            td = td.total_seconds()
            td -= (globals.confirmMaybeWarningTimeHours * 60 * 60)

        except ValueError:
            error = 'Date or time entered incorrectly.'
            logger.error(error)
            raise commands.CheckFailure(error)

        if len(title) > 256:
            error = 'Title over 256 characters.'
            logger.error(error)
            raise commands.CheckFailure(error)

        if len(descr) > 512:
            # not a technical limitation, but embed can only hold 6000 characters, so can't let this be too long
            error = 'Description over 512 characters.'
            logger.error(error)
            raise commands.CheckFailure(error)

        # TODO: make sure this actually calls confirm_maybe() only once
        # confirm maybe will only be called if it is at least 2 days in the future
        if td > 60 * 60 * 24 * 2:
            @tasks.loop(seconds=td, count=2)
            async def confirm_maybe_loop():
                # the loop immediately runs once upon start, so wait until the second loop
                if confirm_maybe_loop.current_loop > 0:
                    await helpers.confirm_maybe()
            confirm_maybe_loop.start()

        # build title and dynamic timestamp for embed
        # title = "SvS Event"
        eventTime = f"<t:{unix_time}>"

        # and then format them up a bit
        eventInfo = title + ' @ ' + eventTime
        description = '@ ' + eventTime + '\n\n'
        # descr += "It's an SvS Event"
        description += descr
        descr += '\n\u200b'

        # create embed and add fields
        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_red())
        embed.add_field(name="YES  [0]", value=">>> \u200b")
        embed.add_field(name="MAYBE  [0]", value=">>> \u200b")
        embed.add_field(name="NO  [0]", value=">>> \u200b")

        # create footer and timestamp
        cmdList = [ctx.clean_prefix + cmd.name for cmd in self.get_commands()]
        embed.set_footer(text=', '.join(cmdList))
        embed.timestamp = discord.utils.utcnow()

        # get the file to be sent with the event embed
        if globals.logoURL:
            embed.set_thumbnail(url=globals.logoURL)

        # send event embed
        eventMessage = await ctx.send(embed=embed)

        # add the view to event embed. Updating of status, database, and embed fields will be handled in
        # eventInteraction.py through user interactions with the buttons.
        view = EventButtonsView(eventMessage)
        # await eventMessage.edit(embed=embed, view=view, attachments=attachments)
        await eventMessage.edit(embed=embed, view=view)

        # set globals to reduce DB accessing
        globals.eventInfo = eventInfo
        globals.eventMessage = eventMessage
        globals.eventChannel = ctx.channel

        # store event data in eventInfo.db
        await db.update_event(title, eventTime, eventMessage.id, ctx.channel.id)

    @commands.command(usage="TODO")
    @commands.max_concurrency(1)
    async def edit(self, ctx, *, arg):
        """
        Edit the existing event
        Does not change the status of current attendees
        """

        pass

    @commands.command(help='Closes event sign-ups and DMs the user a formatted CSV of attendees.\nMust be used in the same channel as an active event.\nRequires ADMIN.')
    @commands.max_concurrency(1)
    async def finalize(self, ctx):
        """
        Close signups and send sorted .csv of attendees to user
        Calls fxn to build the teams for the upcoming event. Should not be re-used as it consumes tokens.
        Requires ADMIN role
        """

        await helpers.delete_event(ctx.author, intent='make_csv')

    @commands.command(help='Closes event sign-ups and resets database to prepare for new event.\nMust be used in the same channel as an active event.\nRequires ADMIN.')
    @commands.max_concurrency(1)
    async def delete(self, ctx):
        """
        Resets eventInfo.db to default value
        Resets everyone's status to "NO"
        """

        await helpers.delete_event(ctx.author, intent='delete')


class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='Change or show your profession data.\n'
                           f'Example: {globals.commandPrefix}prof change',
                      usage='<change/show>')
    @commands.dm_only()
    async def prof(self, ctx, intent: str) -> None:
        """
        $prof (no argument) to edit profession, $prof ? to show profession

        If the user is not in the database, prompts user to provide a database entry

        Else, sends the user either a ProfessionMenuView view object to change their profession, or an info embed made with
        db.info_embed() to show their database information
        """

        member = ctx.author
        ID = member.id

        # intentDict = {None: "edit", "?": "show"}
        # intent = intentDict.get(intent, None)
        if intent is None:
            msg = "```USAGE:\n$prof to edit profession\n$prof ? to show profession```"
            await ctx.send(msg)
            return
        intent = intent.lower()
        if intent not in ['change', 'show']:
            raise commands.CheckFailure(f'Argument must be either \"change\" or \"show\"')

        entry = await db.get_entry(ID)
        if not entry:   # check if user has been registered in DB. if not, register them
            await helpers.request_entry(member)

        elif intent == "change":
            msg = await ctx.send(content="Enter profession. Menu will disappear in 5 minutes.")
            view = ProfessionMenuView(msg, 'class')
            await msg.edit(view=view)

        elif intent == "show":
            embed = db.info_embed(entry)
            await ctx.send(embed=embed)

    @commands.command(help='Toggles lottery opt in/out.')
    @commands.dm_only()
    async def lottery(self, ctx) -> None:
        """
        Toggles lottery opt in/out
        """
        member = ctx.author
        ID = member.id
        entry = await db.get_entry(ID)

        if not entry:
            await helpers.request_entry(member)
        else:
            lotto = 1 - entry[-1]
            lotto_in_out = 'in to' if lotto else 'out of'
            msg = f'You have opted ' + lotto_in_out + ' the lottery\n'
            await db.update_lotto(ID, lotto)
            await ctx.send(msg)


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='Sends the user a dump of the SQL database.\n'
                           'Requires ADMIN.')
    @commands.has_role(globals.adminRole)
    @commands.max_concurrency(1)
    async def download_db(self, ctx):
        """
        Sends dump of SQL database to user
        Requires ADMIN role
        """

        if ctx.author.dm_channel is None:
            await ctx.author.create_dm()
        dmChannel = ctx.author.dm_channel

        dump = await db.dump_db('svs_userHistory_dump.sql')
        await dmChannel.send("dump of userHistory.db database", file=dump)


@globals.bot.event
async def on_command_error(ctx, error):
    logger.error(f'{ctx.command} ERROR: {str(error)}')
    print(str(error))

    # command has local error handler
    if hasattr(ctx.command, 'on_error'):
        return

    # generic error handling
    errmsg = f"{ctx.clean_prefix}{ctx.command} ERROR: "
    if isinstance(error, commands.CheckFailure):
        errmsg += str(error) + '\n'
    elif isinstance(error, commands.MissingRequiredArgument):
        errmsg += "Missing argument.\n"
    elif isinstance(error, commands.TooManyArguments):
        errmsg += "Too many arguments.\n"
    elif isinstance(error, commands.BadArgument):
        errmsg += f'Parameter \"{str(error).split()[-1][1:-2]}\" was invalid.\n'
    elif isinstance(error, commands.NoPrivateMessage):
        errmsg += "Command does not work in DM.\n"
    elif isinstance(error, commands.PrivateMessageOnly):
        errmsg += "Command only works in DM.\n"
    elif isinstance(error, commands.BotMissingRole):
        errmsg += "Bot lacks required role for this command.\n"
    elif isinstance(error, commands.BotMissingPermissions):
        errmsg += "Bot lacks required permissions for this command.\n"
    elif isinstance(error, commands.MissingRole):
        errmsg += "User lacks required role for this command.\n"
    elif isinstance(error, commands.MissingPermissions):
        errmsg += "User lacks required permissions for this command.\n"
    elif isinstance(error, commands.CommandNotFound):
        errmsg += "Command does not exist.\n"
    else:
        errmsg += f'Error not handled.\n'
        # should probably do a bit more here but idk
        print(f'Ignoring exception in command {globals.commandPrefix}{ctx.command}.')

    # errmsg += f"$help {ctx.command} for specific info. $help for list of commands."
    errmsg += f'Usage: {globals.commandPrefix}{ctx.command} {ctx.command.usage}'
    await ctx.send(f'```{errmsg}```')
