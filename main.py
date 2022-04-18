import discord
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle
import logging
import tokenFile
import globals
import time
import datetime
import sqlite3 as sql3

logging.basicConfig(level=logging.INFO)
intents = discord.Intents(messages=True, members=True, guilds=True)

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

    # components = [ActionRow(Button(label='Yes',
    #                                custom_id='1',
    #                                emoji="✅",
    #                                style=ButtonStyle.green
    #                                ),
    #                         Button(label='Maybe',
    #                                custom_id='2',
    #                                emoji="❔",
    #                                style=ButtonStyle.blurple
    #                                ),
    #                         Button(label='No',
    #                                custom_id='3',
    #                                emoji="✖️",
    #                                style=ButtonStyle.red
    #                                ))
    #               ]

    # await ctx.send(embed=embed, components=components)
    await ctx.send(embed=embed)

    # def _check(i: discord.Interaction, b):
    #     return i.message == msg and i.member == ctx.author

    # interaction, button = await bot.wait_for('button_click')
    # button_id = button.custom_id
    #
    # # This sends the Discord-API that the interaction has been received and is being "processed"
    # await interaction.defer()
    # # if this is not used and you also do not edit the message within 3 seconds as described below,
    # # Discord will indicate that the interaction has failed.
    #
    # # If you use interaction.edit instead of interaction.message.edit, you do not have to defer the interaction,
    # # if your response does not last longer than 3 seconds.
    # await interaction.edit(embed=embed.add_field(name='Choose', value=f'Your Choose was `{button_id}`'),
    #                        components=[components[0].disable_all_buttons()])


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


@bot.command()
async def repeat(ctx, *, arg):
    await ctx.send(arg)


@repeat.error
async def repeat_error(ctx, error):
    await ctx.send('Error with repeat')


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
