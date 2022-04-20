# upon $thumb invocation, waits 60s for the user to react with a thumbs up
# use this format for checking "maybe" reacts
# use this format for when people react with a role that is not their previously used role
#   possible issue: this is not well suited for long-term waiting; would break if the bot ever turns off. Better to
#   write to a file?
import discord
from discord.ext import commands
import sqlite3 as sql3
import db
import globals
import datetime
import asyncio


async def request_entry(member: discord.Member, prof_string=None, status="NO"):
    """
    Prompt member to provide data entry for SQL database.
    To be called when member attempts to do update a value, but they are not yet in the database
    Returns False if entry fails, True if succeeds
    """
    # prompt member to provide data entry for SQL
    # if they do not respond in 1 hr, initialize entry with status "NO", empty profession, 0 tokens, opt-in lotto

    await member.create_dm()
    dmChannel = member.dm_channel()

    # if prof_string provided through $prof
    if prof_string is not None:
        # parse prof_string with db.parse_profession()
        prof_array = db.parse_profession(prof_string)
        if not prof_array:
            success = False
        else:
            entry = [member.id, *prof_array, status, 0, 1]
            db.add_entry(entry)
            success = True
            await ack_change(member)

    # default case (no profession string given)
    # happens when user reacts to event or uses $lotto
    else:
        profPrompt = "CLASS: {MM, CE}\n" \
                     "UNIT: {A, F, N} (skip if CEM)\n" \
                     "MM levels: {0T, 3T, 5T, 10, E}\n" \
                     "CE levels: {2, 3, 3X, 3XE, M}\n" \
                     "EXAMPLES: MMA3T, CEN3XE\n"

        msg = "You do not have an existing entry in the database. Please enter Profession with following format: "
        msg += profPrompt
        msg += "You have 5 minutes to reply."
        await dmChannel.send(msg)

        def check(m):
            return m.channel == dmChannel and m.author == member

        try:
            reply = await globals.bot.wait_for('message', timeout=300, check=check)
        except asyncio.TimeoutError:
            reply = None

        if reply is None:
            # user failed to reply in time.
            success = False
        else:
            prof_array = db.parse_profession(reply)
            if not prof_array:
                success = False
            else:
                entry = [member.id, *prof_array, status, 0, 1]
                db.add_entry(entry)
                success = True
                await ack_change(member)

    # return something indicating if user responded to prompt, or if it was set to NO automatically
    return success


async def ack_change(member: discord.Member):

    # async sleep until next write
    nextWrite = db.sql_write.next_iteration
    timeUntilNextWrite = (nextWrite - datetime.datetime.now()).total_seconds()

    await member.create_dm()
    async with member.dm_channel.typing():
        await asyncio.sleep(timeUntilNextWrite + 3)

    with sql3.connect('userHistory.db') as conn:
        entry = db.get_entry(conn, member.id)

    clas = entry[1]
    unit = entry[2]
    level = str(entry[3])
    status = entry[4]
    lottery = entry[6]

    msg = ''
    eventTitle, eventTime = db.get_event()
    if eventTitle != 'placeholder':
        eventInfo = eventTitle + ' @ ' + eventTime
        msg += f'You are marked as **{status}** for {eventInfo}\n'

    msg += f'You are registered as CLASS: **{clas}**, UNIT: **{unit}**, LEVEL: **{level}**.\n'

    msg += f'You have opted ' + '**in** to' if lottery else '**out** of' + ' the lottery.\n'
    msg += f'$prof [PROFESSION] to change profession. $lottery to toggle lottery participation'

    await member.dm_channel().send(msg)


async def confirm_maybe(conn, member: discord.member):
    pass


@globals.bot.command(usage="[PROFESSION] {CLASS}{UNIT}{LEVEL}")
@commands.dm_only()
async def prof(ctx, arg):
    """
    CLASS: {MM, CE}
    UNIT: {A, F, N} (skip if CEM)
    MM levels: {0T, 3T, 5T, 10, E}
    CE levels: {2, 3, 3X, 3XE, M}
    EXAMPLES: MMA3T, CEN3XE
    """
    member = ctx.author
    ID = member.id

    with sql3.connect('userHistory.db') as conn:
        entry = db.get_entry(conn, ID)

    if not entry:
        success = await request_entry(member, arg)
    else:
        # TODO: Handle arg-parsing in db.update_profession(). return True if successful, False otherwise
        success = db.update_profession(ID, arg)

    if not success:
        await ctx.send(f"ERROR: Could not parse profession")
        return
    else:
        await ack_change(member)


@globals.bot.command()
@commands.dm_only()
async def toggle_lotto(ctx):
    """
    Toggles lottery opt in/out status
    """
    member = ctx.author
    ID = member.id
    with sql3.connect('userHistory.db') as conn:
        entry = db.get_entry(conn, ID)

    if not entry:
        success = await request_entry(member)
    else:
        lottery = 1 - entry[6]
        db.update_lotto(ID, lottery)
        await ack_change(member)


# @client.event
# async def on_message(message):
#     if message.content.startswith('$thumb'):
#         channel = message.channel
#         await channel.send('Send me that 👍 reaction, mate')
#
#         def check(reaction, user):
#             return user == message.author and str(reaction.emoji) == '👍'
#
#         try:
#             reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
#         except asyncio.TimeoutError:
#             await channel.send('👎')
#         else:
#             await channel.send('👍')