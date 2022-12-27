import discord
from discord.ext import commands
import traceback
import sys

import logging
from . import globals


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Triggered when an exception is raised while invoking a command.
        """

        if ctx.command:
            errstring = f'{ctx.command} ERROR: {str(error)}'
        else:
            errstring = f'Command not found: {ctx.message.content}'
        logging.info(errstring)
        print(errstring)

        # command has local error handler
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        error = getattr(error, 'original', error)

        # anything in ignored will be ignored
        ignored = (commands.CommandNotFound, )
        if isinstance(error, ignored):
            return

        # generic error handling
        title = f"{ctx.clean_prefix}{ctx.command} Error" if ctx.command else 'Error'

        errmsg = ''
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
            errmsg += "Bot lacks required role to execute this command.\n"
        elif isinstance(error, commands.BotMissingPermissions):
            errmsg += "Bot lacks required permissions to execute this command.\n"
        elif isinstance(error, commands.MissingRole):
            errmsg += "User lacks required role for this command.\n"
        elif isinstance(error, commands.MissingPermissions):
            errmsg += "User lacks required permissions for this command.\n"
        else:
            print(f'Ignoring exception in command {ctx.clean_prefix}{ctx.command}.')
            errmsg += f'Unknown.\nPossible bug, please report with {ctx.clean_prefix}bug.'
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        userInput = '\"' + ctx.message.content + '\"'
        if len(userInput) > 100:
            userInput = userInput[:100] + '...\"'
        if not isinstance(ctx.channel, discord.DMChannel):
            userInput += f'\n\u200b\nin channel: {ctx.channel.mention}'

        # embed = discord.Embed(title=title, description=errmsg)
        embed = discord.Embed(title=title)
        embed.add_field(name='Reason', value=errmsg, inline=False)
        embed.add_field(name='You Typed', value=userInput, inline=False)

        # usage field
        if ctx.command is not None and ctx.command.usage is not None:
            argHints = '<arg> is a mandatory argument\n' \
                       '<arg1/arg2> indicates two possible choices for a mandatory argument\n' \
                       '[arg] is an optional argument\n'
            usage = f'{ctx.clean_prefix}{ctx.command} {ctx.command.usage}\n'
            usage += '\u200b\n' + argHints
            embed.add_field(name='Usage', value=usage, inline=False)

            # Example field
            if 'Example:' in ctx.command.help:
                # if the help-text has "Example:" in it, this grabs the example if it is terminated with '\n'
                example = ctx.command.help.split('Example:')[1].strip().split('\n')[0]
                embed.add_field(name='Example', value=example, inline=False)

        # footer text prompt for $help command, $help
        footerText = f'{ctx.clean_prefix}help {ctx.command} for more info. ' if ctx.command is not None else ''
        footerText += f'{ctx.clean_prefix}help for a list of commands.'
        embed.set_footer(text=footerText)

        if globals.SEND_ERROR_TO_DM:
            # delete the offending command if it was used in a server channel
            if globals.DELETE_MESSAGES and not isinstance(ctx.channel, discord.DMChannel):
                await ctx.message.delete()
            await ctx.author.send(embed=embed)

        else:
            await ctx.send(embed=embed)
