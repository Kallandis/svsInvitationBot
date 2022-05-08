import discord
from discord.ext import commands
import sys

import logging
logger = logging.getLogger(__name__)

import svsBot.my_commands as my_commands
import svsBot.my_help as my_help
import svsBot.db as db
import svsBot.error_handler as error_handler
import svsBot.globals as globals




class Bot(commands.Bot):
    # def __init__(self, command_prefix, intents, description, allowed_mentions, activity):
    #     super().__init__(command_prefix=command_prefix, intents=intents, description=description)
    def __init__(self, kwargs):
        super().__init__(**kwargs)

        # list of guilds minus my private server for testing and bug reports
        self.event_guilds = None

        # list of channels to listen on for event commands
        self.main_channels = []

        # self.eventInfo = ''
        # self.eventMessage = None
        # self.eventChannel = None

        # background loop that sends a reminder to people signed up as "maybe"
        self.maybe_loop = None

        # bug report channel that receives reports from $bug cmd
        self.bug_report_channel = None

    async def setup_hook(self) -> None:
        # add cogs
        await self.add_cog(my_commands.DM(self))
        await self.add_cog(my_commands.Event(self))
        await self.add_cog(my_commands.Misc(self))
        # await self.add_cog(my_help.Help(self))
        await self.add_cog(error_handler.CommandErrorHandler(self))

    async def load_variables(self) -> None:
        # guild-related instance variables

        # guilds
        event_guilds = [guild for guild in self.guilds]
        event_guilds.remove(self.get_guild(globals.EVAN_GUILD_ID))
        self.event_guilds = event_guilds

        # channels
        for id_ in globals.MAIN_CHANNEL_ID_LIST:
            self.main_channels.append(self.get_channel(id_))
        if not all(self.main_channels):
            error = 'Failed to acquire at least one channel.'
            logging.error(error)
            sys.exit(error)
        globals.mainChannels = self.main_channels
        await self.add_cog(my_help.Help(self))

        # bug report channel in my private server "svsBotTestServer"
        self.bug_report_channel = self.get_channel(globals.BUG_REPORT_CHANNEL_ID)
        if self.bug_report_channel is None:
            error = 'Failed to acquire bug report channel'
            # TODO: test this
            # remove the bug command if bug channel failed to acquire
            self.remove_command('bug')
            logging.error(error)

        # event variables
        # if bot is restarted while the event is active, repopulate everything in memory to ensure seamless restart
        eventTitle, eventTime, eventMessageID, eventChannelID = await db.get_event()
        if eventMessageID:
            import time
            # from eventInteraction import EventButtonsView
            # import helpers

            # event variables
            globals.eventInfo = eventTitle + ' @ ' + eventTime
            globals.eventChannel = self.get_channel(eventChannelID)
            globals.eventMessage = await globals.eventChannel.fetch_message(eventMessageID)
            # globals.eventMessage = await self.eventChannel.fetch_message(eventMessageID)

            # self.eventInfo = eventTitle + ' @ ' + eventTime
            # self.eventChannel = self.get_channel(eventChannelID)
            # self.eventMessage = await self.eventChannel.fetch_message(eventMessageID)

            # re-initializes EventButtonsView instance so that buttons still work
            view = event_interaction.EventButtonsView(globals.eventMessage)
            # view = EventButtonsView(globals.eventMessage)
            await globals.eventMessage.edit(view=view)
            # view = EventButtonsView(self.eventMessage)
            # await self.eventMessage.edit(view=view)

            # TODO: test this
            # restart confirm_maybe loop
            # extract unix time of event, convert to time until event, send to fxn
            eventTime = int(eventTime.strip('><t:'))
            timeUntilEvent = eventTime - time.time()
            # confirmMaybeTime = eventTime - globals.CONFIRM_MAYBE_WARNING_HOURS * 60 * 60
            # timeUntilConfirmMaybe = confirmMaybeTime - time.time()

            maybe_loop = await helpers.start_confirm_maybe_loop(timeUntilEvent, globals.eventMessage.guild)
            # maybe_loop = await helpers.start_confirm_maybe_loop(timeUntilConfirmMaybe, self.eventMessage.guild)
            self.maybe_loop = maybe_loop

    async def on_ready(self):
        print(f'{self.user.name} connected!')
        print(f'discord.py version = {discord.__version__}')
        print()

        await self.load_variables()

        for guild in self.event_guilds:
            print('Connected to guild: ' + guild.name)
            adminRoleInGuild = list(filter(lambda r: r.name == globals.ADMIN_ROLE_NAME, guild.roles))
            if not adminRoleInGuild:
                print(f'ALERT: Guild "{guild.name}" does not have a role named "{globals.ADMIN_ROLE_NAME}". Events '
                      f'cannot be created in this guild.')

        for channel in self.main_channels:
            print('Listening on channel: ' + channel.guild.name + '/' + channel.name)

        if self.bug_report_channel:
            print('Sending bugs to channel: ' + self.bug_report_channel.guild.name + '/' + self.bug_report_channel.name)

        if globals.eventMessage:
            print(f'Reacquired existing event in channel: '
                  f'{globals.eventChannel.guild.name}/{globals.eventChannel.name}')

    def reset_event_vars(self) -> None:
        globals.eventInfo = ''
        globals.eventMessage = None
        globals.eventChannel = None

        # self.eventInfo = ''
        # self.eventMessage = None
        # self.eventChannel = None

        if self.maybe_loop is not None:
            self.maybe_loop.cancel()
            self.maybe_loop = None
