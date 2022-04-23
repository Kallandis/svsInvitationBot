# upon $thumb invocation, waits 60s for the user to react with a thumbs up
# use this format for checking "maybe" reacts
# use this format for when people react with a role that is not their previously used role
#   possible issue: this is not well suited for long-term waiting; would break if the bot ever turns off. Better to
#   write to a file?
import discord
from discord.ext import commands
import db
import globals
import datetime
import asyncio
from professionMenuView import ProfessionMenuView


async def request_entry(member: discord.Member, event_reaction=False):
    """
    Prompt unregistered user to provide data entry for SQL database.
    Called when user reacts to event for the first time, or uses DM command $lotto before being added to DB
    """

    if member.dm_channel is None:
        await member.create_dm()
    dmChannel = member.dm_channel

    if event_reaction:
        cont = "Your event reaction has been removed because you are not in the database.\n" \
               "After entering your profession, you may react to the event again.\n"
    else:
        cont = "You do not have an existing entry in the database. Please enter profession.\n"
    cont += "Menu will disappear in 5 minutes."

    msg = await dmChannel.send(content=cont)
    view = ProfessionMenuView(msg, 'class', first_entry=True)
    await msg.edit(view=view)


async def ack_change(member: discord.Member, show_change=None):

    # async sleep until next write
    nextWrite = db.sql_write.next_iteration.replace(tzinfo=None)
    now = datetime.datetime.utcnow()
    timeUntilNextWrite = (nextWrite - now).total_seconds()

    if member.dm_channel is None:
        await member.create_dm()

    async with member.dm_channel.typing():
        await asyncio.sleep(timeUntilNextWrite + 1)

    entry = db.get_entry(member.id)

    clas = entry[1]
    unit = entry[2]
    level = str(entry[3])
    items = entry[4]
    status = entry[5]
    lottery = entry[6]

    msg = ''
    eventStatus = ''
    eventTitle, eventTime, message_id = db.get_event()
    if message_id:
        eventInfo = eventTitle + ' @ ' + eventTime
        eventStatus = f'You are marked as **{status}** for {eventInfo}\n'

    # get this from db.format_profession()?
    profession = f'You are registered as CLASS: **{clas}**, UNIT: **{unit}**, LEVEL: **{level}**, ITEMS: **{items}**.\n'

    lotto_in_out = '**in** to' if lottery else '**out** of'
    lotto = f'You have opted ' + lotto_in_out + ' the lottery.\n'
    helpString = f'$prof to change profession. $prof ? to show profession. $lottery to toggle lottery participation'

    # default case: show everything
    if show_change is None:
        if message_id:
            msg += eventStatus
        msg += profession + lotto
    elif show_change == 'status':
        if message_id:
            msg += eventStatus
    elif show_change == 'lotto':
        msg += lotto

    msg += helpString
    await member.dm_channel.send(msg)


async def confirm_maybe(member: discord.member):
    pass


@globals.bot.command(usage='EDIT: $prof, SHOW: $prof ?')
@commands.dm_only()
async def prof(ctx, *, arg=None):
    """
    $prof to update profession, $prof ? to check profession
    """

    member = ctx.author
    ID = member.id

    intentDict = {None: "edit", "?": "show"}
    intent = intentDict.get(arg, None)
    if intent is None:
        msg = "USAGE: $prof to edit profession, $prof ? to show profession"
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
        clas = entry[1]
        unit = entry[2]
        level = str(entry[3])
        items = entry[4]
        # TODO: introduce db.format_profession() to print this out nicely in an embed
        msg = f'You are registered as CLASS: **{clas}**, UNIT: **{unit}**, LEVEL: **{level}**, ITEMS: **{items}**.\n'
        await ctx.send(msg)


# @globals.bot.command(usage="[PROFESSION] {CLASS}{UNIT}{LEVEL}")
# @commands.dm_only()
# async def prof(ctx, arg):
#     """
#     $prof to update profession, $prof ? to check profession
#     CLASS: {MM, CE}
#     UNIT: {A, F, N} (skip if CEM)
#     MM levels: {0T, 3T, 5T, 10, E}
#     CE levels: {2, 3, 3X, 3XE, M}
#     EXAMPLES: MMA3T, CEN3XE
#     """
#     member = ctx.author
#     ID = member.id
#
#     entry = db.get_entry(ID)
#
#     if not entry:
#         success = await request_entry(member, arg)
#     else:
#         prof_array = db.parse_profession(arg)
#         if prof_array:
#             success = db.update_profession(ID, prof_array)
#         else:
#             success = False
#
#     if not success:
#         msg = "ERROR: Could not parse profession\n"
#         profPrompt = "CLASS: {MM, CE}\n" \
#                      "UNIT: {A, F, N} (skip if CEM)\n" \
#                      "MM levels: {0T, 3T, 5T, 10, E}\n" \
#                      "CE levels: {2, 3, 3X, 3XE, M}\n" \
#                      "EXAMPLES: MMA3T, CEN3XE\n"
#         msg += profPrompt
#         await ctx.send(msg)
#         return
#     else:
#         await ack_change(member, show_change='profession')


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
        lottery = 1 - entry[6]
        db.update_lotto(ID, lottery)
        await ack_change(member, show_change='lotto')
