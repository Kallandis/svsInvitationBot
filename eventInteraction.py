import discord
from requestEntry import request_entry
import globals
import db


class EventButtonsView(discord.ui.View):

    __slots__ = ('parent_message', 'last_status')

    def __init__(self, parent_message: discord.Message):
        super().__init__(timeout=None)
        self.parent_message = parent_message
        self.last_status = None

    @discord.ui.button(label='YES', style=discord.ButtonStyle.green, custom_id='persistent_view:yes')
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'YES'
        success = await handle_interaction(self.last_status, status, interaction, self.parent_message)
        if success:
            self.last_status = status

    @discord.ui.button(label='MAYBE', style=discord.ButtonStyle.gray, custom_id='persistent_view:maybe')
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'MAYBE'
        success = await handle_interaction(self.last_status, status, interaction, self.parent_message)
        if success:
            self.last_status = status

    @discord.ui.button(label='NO', style=discord.ButtonStyle.red, custom_id='persistent_view:no')
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'NO'
        success = await handle_interaction(self.last_status, status, interaction, self.parent_message)
        if success:
            self.last_status = status


async def handle_interaction(last_status, status, interaction, parent_message):
    if last_status == status:  # don't do anything if they are already in this category
        return False

    user = interaction.user
    entry = db.get_entry(user.id)
    if not entry:
        await request_entry(user, event_attempt=True)
        return False

    # send ephemeral message to eventChannel
    await interaction.response.send_message(f'Registered as **{status}** for {globals.eventInfo}.', ephemeral=True)
    # update the event field, removing user's name from the previous field they were in if it exists
    await update_event_field(parent_message, user.display_name, status, last_status)
    # update the database
    db.update_status(user.id, status)

    if last_status is None:  # this is their first response to event
        if status != 'NO':   # only DM them if their response is YES or MAYBE
            entry = list(entry)
            entry[6] = status
            await dm_to_user(user, entry=entry)

    else:   # if this is not their first response to event, DM them with change-string instead of full embed
        await dm_to_user(user, new_status=status, last_status=last_status)

    return True


# do I need to worry about people pressing buttons near-simultaneously? ideally calls to this should be queued to
# avoid reader-writer problem. ask in discord?
async def update_event_field(message: discord.Message, name: str, status: str, remove_status: str):
    embed = message.embeds[0]
    fields = embed.fields

    indexDict = {"YES": 0, "MAYBE": 1, "NO": 2}
    fieldIndex = indexDict[status]
    fieldName = fields[fieldIndex].name
    fieldValue = fields[fieldIndex].value
    fieldValues = fieldValue.split('\n')

    # if adding name would not exceed 1024 characters
    if len(fieldValue) + len(name) + 2 < 1024:
        fieldValues.append(name)
        fieldValue = '\n'.join(fieldValues)     # fields hold a string, so make a '\n'-separated string -> column
        embed.set_field_at(fieldIndex, name=fieldName, value=fieldValue)

    # remove from old field
    if remove_status is not None:
        oldFieldIndex = indexDict[remove_status]
        oldFieldName = fields[oldFieldIndex].name
        oldFieldValue = fields[oldFieldIndex].value
        oldFieldValues = oldFieldValue.split('\n')
        oldFieldValues.remove(name)
        oldFieldValue = '\n'.join(oldFieldValues)
        embed.set_field_at(oldFieldIndex, name=oldFieldName, value=oldFieldValue)

    await message.edit(embed=embed)


async def dm_to_user(user, entry=None, new_status=None, last_status=None):
    if user.dm_channel is None:
        await user.create_dm()
    dmChannel = user.dm_channel

    # send user an info embed
    if entry is not None:
        embed = db.info_embed(entry)
        await dmChannel.send(embed=embed)

    # send a small text message to ACK change
    elif new_status is not None:
        await dmChannel.send(f'Your status has been changed from '
                             f'**{last_status}** to **{new_status}** for {globals.eventInfo}')
