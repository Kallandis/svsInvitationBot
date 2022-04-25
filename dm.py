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


async def request_entry(member: discord.Member, event_attempt=False):
    """
    Prompt unregistered user to provide data entry for SQL database.
    Called when user reacts to event for the first time, or uses DM command $lotto before being added to DB
    """

    if member.dm_channel is None:
        await member.create_dm()
    dmChannel = member.dm_channel

    if event_attempt:
        cont = "Your event reaction has been removed because you are not in the database.\n" \
               "After entering your profession, you may react to the event again.\n"
    else:
        cont = "You do not have an existing entry in the database. Please enter profession.\n"
    cont += "Menu will disappear in 5 minutes."

    msg = await dmChannel.send(content=cont)
    view = ProfessionMenuView(msg, 'class', first_entry=True)
    await msg.edit(view=view)


async def confirm_maybe(member: discord.member):
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
        args = {'file': file, 'embed': embed} if file else {'embed': embed}
        await ctx.send(**args)


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
