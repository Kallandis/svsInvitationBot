import discord
from professionInteraction import ProfessionMenuView


async def request_entry(member: discord.Member, event_attempt=False):
    """
    Prompt unregistered user to provide data entry for SQL database.
    Called when user reacts to an event or uses DM command $lotto or $prof before being added to DB
    """

    if member.dm_channel is None:
        await member.create_dm()
    dmChannel = member.dm_channel

    if event_attempt:
        cont = "Your event registration because you are not in the database.\n" \
               "After entering your profession, you may register for the event again.\n"
    else:
        cont = "You do not have an existing entry in the database. Please enter profession.\n"
    cont += "Menu will disappear in 5 minutes."

    msg = await dmChannel.send(content=cont)
    # DB will be updated following user interaction with ProfessionMenu
    view = ProfessionMenuView(msg, 'class', first_entry=True)
    await msg.edit(view=view)
