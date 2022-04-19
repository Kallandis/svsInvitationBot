# upon $thumb invocation, waits 60s for the user to react with a thumbs up
# use this format for checking "maybe" reacts
# use this format for when people react with a role that is not their previously used role
#   possible issue: this is not well suited for long-term waiting; would break if the bot ever turns off. Better to
#   write to a file?
import discord
import sqlite3 as sql3
import db
import globals


async def request_entry(member: discord.member):
    # prompt member to provide data entry for SQL
    # if they do not respond in 1 hr, initialize entry with status "NO"

    # return something indicating if user responded to prompt, or if it was set to NO automatically
    return success


async def ack_status(conn, member: discord.member, event_info: str):
    with conn:
        entry = db.get_entry(conn, member.id)

    clas = entry[1]
    unit = entry[2]
    level = str(entry[3])
    status = entry[4]
    lottery = entry[6]

    msg = f'You have been marked as **{status}** for {event_info}\n' \
          f'You are registered as CLASS: **{clas}**, UNIT: **{unit}**, LEVEL: **{level}**.'

    msg += f'You have opted ' + 'into' if lottery else 'out of' + ' the lottery.'
    msg += f'$prof [PROFESSION] to change profession. $lottery to toggle lottery participation'

    await member.create_dm()
    await member.dm_channel().send(msg)


async def confirm_maybe(conn, member: discord.member):
    pass


@globals.bot.command()
async def prof(ctx, arg):
    """
    $prof [PROFESSION] {CLASS}{UNIT}{LEVEL}
    EXAMPLES: MMA3T, CEN3XE
    MM levels: {0T, 3T, 5T, 10, E}
    CE levels: {2, 3, 3X, 3XE, M}
    """
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        return









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