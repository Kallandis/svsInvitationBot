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


async def request_entry(member: discord.Member, prof_string=None, status="NO"):
    """
    Prompt member to provide data entry for SQL database.
    To be called when member attempts to do update a value, but they are not yet in the database
    Returns False if entry fails, True if succeeds. This allows the function that invokes request_entry() to print out
        an error message if input was unsuccessful.
    """
    # prompt member to provide data entry for SQL
    # if they do not respond in 1 hr, initialize entry with status "NO", empty profession, 0 tokens, opt-in lotto

    if member.dm_channel is None:
        await member.create_dm()
    dmChannel = member.dm_channel

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
        # TODO: do a timestring: "You have until <TIME> to reply"
        msg += "You have 5 minutes to reply."
        await dmChannel.send(msg)

        def check(m):
            return m.channel == dmChannel and m.author == member

        try:
            reply = await globals.bot.wait_for('message', timeout=300, check=check)
        except asyncio.TimeoutError:
            # TODO: should edit message to indicate that time is up and they can no longer reply
            reply = None

        if reply is None:
            # user failed to reply in time.
            success = False
        else:
            prof_array = db.parse_profession(reply.content)
            if not prof_array:
                success = False
            else:
                entry = [member.id, *prof_array, status, 0, 1]
                db.add_entry(entry)
                success = True
                await ack_change(member)

    # return something indicating if user responded to prompt, or if it was set to NO automatically
    return success


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
    status = entry[4]
    lottery = entry[6]

    msg = ''
    eventStatus = ''
    eventTitle, eventTime, message_id = db.get_event()
    if message_id:
        eventInfo = eventTitle + ' @ ' + eventTime
        eventStatus = f'You are marked as **{status}** for {eventInfo}\n'

    profession = f'You are registered as CLASS: **{clas}**, UNIT: **{unit}**, LEVEL: **{level}**.\n'

    lotto_in_out = '**in** to' if lottery else '**out** of'
    lotto = f'You have opted ' + lotto_in_out + ' the lottery.\n'
    helpString = f'$prof [PROFESSION] to change profession. $lottery to toggle lottery participation'

    # default case: show everything
    if show_change is None:
        if message_id:
            msg += eventStatus
        msg += profession + lotto
    elif show_change == 'status':
        if message_id:
            msg += eventStatus
    elif show_change == 'profession':
        msg += profession
    elif show_change == 'lotto':
        msg += lotto

    msg += helpString
    await member.dm_channel.send(msg)


async def confirm_maybe(member: discord.member):
    pass


@globals.bot.command(usage="[PROFESSION] {CLASS}{UNIT}{LEVEL}")
@commands.dm_only()
async def prof(ctx, arg):
    """
    $prof to update profession, $prof ? to check profession
    CLASS: {MM, CE}
    UNIT: {A, F, N} (skip if CEM)
    MM levels: {0T, 3T, 5T, 10, E}
    CE levels: {2, 3, 3X, 3XE, M}
    EXAMPLES: MMA3T, CEN3XE
    """
    member = ctx.author
    ID = member.id

    entry = db.get_entry(ID)

    if not entry:
        success = await request_entry(member, arg)
    else:
        prof_array = db.parse_profession(arg)
        if prof_array:
            success = db.update_profession(ID, prof_array)
        else:
            success = False

    if not success:
        msg = "ERROR: Could not parse profession\n"
        profPrompt = "CLASS: {MM, CE}\n" \
                     "UNIT: {A, F, N} (skip if CEM)\n" \
                     "MM levels: {0T, 3T, 5T, 10, E}\n" \
                     "CE levels: {2, 3, 3X, 3XE, M}\n" \
                     "EXAMPLES: MMA3T, CEN3XE\n"
        msg += profPrompt
        await ctx.send(msg)
        return
    else:
        await ack_change(member, show_change='profession')


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
