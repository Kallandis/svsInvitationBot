import discord
from discord.ext import commands
import globals


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return '%s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping):
        descr = '<arg> is a mandatory argument\n' \
                '<arg1/arg2> indicates two possible choices for a mandatory argument\n' \
                '[arg] is an optional argument\n' \
                '\u200b\n' \
                f'\'{self.context.clean_prefix}help [command]\' for command-specific help\n' \
                '\u200b'

        embed = discord.Embed(title="Commands List", description=descr)
        for cog, commands in mapping.items():
            command_signatures = [self.get_command_signature(c) for c in commands]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", None)
                # cog_name = cog_name_dict.get(cog_name, cog_name)
                if cog_name is not None:
                    embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        if globals.send_help_to_dm:
            # delete the help message if it was sent in a guild
            if not isinstance(self.context.channel, discord.DMChannel):
                await self.context.message.delete()
            # send help embed to user's DM
            await self.context.author.send(embed=embed)

        else:
            # send help embed to the context
            channel = self.get_destination()
            await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=self.get_command_signature(command), description=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        if globals.send_help_to_dm:
            # delete the help message if it was sent in a guild
            if not isinstance(self.context.channel, discord.DMChannel):
                await self.context.message.delete()
            # send help embed to user's DM
            await self.context.author.send(embed=embed)

        else:
            # send help embed to the context
            channel = self.get_destination()
            await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        approved_channels = ', '.join([c.mention for c in globals.mainChannels])
        cog_name_dict = {
            'DM': ['DM - edit your database entry',
                   'Commands to edit or show your database entry info.\n'
                   'Must be used in DM with the bot.'
                   ],
            'Event': [f'Event - manage events (ADMIN)',
                      'Commands to create, edit, and close events in approved server channels.\n'
                      f'Requires role: \'{globals.adminRole}\'\n'
                      f'\u200b\n'
                      f'Approved channel(s): {approved_channels}'
                      ],
            'Misc': [f'Misc - general commands', ''],
            'Help': ['Help', '']
        }
        cog_name = getattr(cog, "qualified_name", None)
        cog_name = cog_name_dict.get(cog_name, None)
        if cog_name is None:
            return

        title = cog_name[0]
        descr = cog_name[1]
        kwargs = {'title': title, 'description': descr} if descr else {'title': title}
        embed = discord.Embed(**kwargs)

        commands = cog.get_commands()
        command_signatures = [self.get_command_signature(c) for c in commands]
        if command_signatures:
            embed.add_field(name='Commands', value='\n'.join(command_signatures))

        if globals.send_help_to_dm:
            # delete the help message if it was sent in a guild
            if not isinstance(self.context.channel, discord.DMChannel):
                await self.context.message.delete()
            # send help embed to user's DM
            await self.context.author.send(embed=embed)

        else:
            # send help embed to the context
            channel = self.get_destination()
            await channel.send(embed=embed)

    async def send_error_message(self, error):
        if error.startswith('No command'):
            cmd = error.replace('\"', '')
            cmd = cmd.split()[-2]
            promptDict = {'dm': 'DM', 'event': 'Event', 'misc': 'Misc'}
            prompt = promptDict.get(cmd, None)
            if prompt is not None:
                error += f'\nDid you mean {globals.commandPrefix}help {prompt}?'

        embed = discord.Embed(title="Error", description=error)

        if globals.send_help_to_dm:
            # delete the help message if it was sent in a guild
            if not isinstance(self.context.channel, discord.DMChannel):
                await self.context.message.delete()
            # send help embed to user's DM
            await self.context.author.send(embed=embed)

        else:
            # send help embed to the context
            channel = self.get_destination()
            await channel.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        _ = globals.commandPrefix
        attrs = {
            'help': f'Lists all commands or gives info on a specific command or category.\n'
                    '\u200b\n'
                    f'Examples:\n'
                    f'{_}help         ->   Shows all commands\n'
                    f'{_}help info    ->   Shows specific help for command "info"\n'
                    f'{_}help Event   ->   Shows info about command category "Event"',
            'usage': '[command]'
        }
        help_command = MyHelp(command_attrs=attrs)
        help_command.cog = self

        bot.help_command = help_command
