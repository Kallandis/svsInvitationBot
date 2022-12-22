import discord
import asyncio

lock = asyncio.Lock()

import logging

from . import helpers, globals, db

fieldPrefix = '>>> \u200b'  # quote block and whitespace char


class EventButtonsView(discord.ui.View):
    __slots__ = ('parent_message', 'last_statuses')

    def __init__(self, parent_message: discord.Message):
        super().__init__(timeout=None)
        self.parent_message = parent_message
        self.last_statuses = {}

    @discord.ui.button(label='YES', style=discord.ButtonStyle.success, custom_id='persistent_view:yes')
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'YES'
        self.check_in_field_before_restart(interaction)
        await self.process_click(interaction, status)

    @discord.ui.button(label='MAYBE', style=discord.ButtonStyle.secondary, custom_id='persistent_view:maybe')
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'MAYBE'
        self.check_in_field_before_restart(interaction)
        await self.process_click(interaction, status)

    @discord.ui.button(label='NO', style=discord.ButtonStyle.danger, custom_id='persistent_view:no')
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'NO'
        self.check_in_field_before_restart(interaction)
        await self.process_click(interaction, status)

    def check_in_field_before_restart(self, interaction):
        # if the last status of user is None, checks to make sure the bot has not restarted and thus lost their last
        # status. Does this by checking the raw field values to see if the user's name is in there. If so, sets the
        # user's last status to the correct value.
        if self.last_statuses.get(interaction.user.id, None) is None:
            # get the embed
            emb = self.parent_message.embeds[0]
            fields = emb.fields
            for i in range(len(fields)):
                # check each field for user's truncated name
                name = interaction.user.display_name[:globals.MAX_NAME_LENGTH_IN_EMBED_FIELD]
                if name in fields[i].value:
                    # if name is found, iterate backwards to get the 'category' of field that it is in (yes, maybe, no)
                    while True:
                        # strip [124] field count to get title
                        fieldType = fields[i].name.split()[0]
                        if fieldType in ['YES', 'MAYBE', 'NO']:
                            self.last_statuses[interaction.user.id] = fieldType
                            break
                        else:
                            i -= 1
                    break

    async def process_click(self, interaction, status):
        async with lock:
            # get the last status of the user, defaults to None
            last_status = self.last_statuses.get(interaction.user.id, None)
            # handle interaction
            output = await handle_interaction(last_status, status, interaction, self.parent_message)
        if output == 'request_entry':
            # handle_intxn returns 'request_entry' when user does not have a database entry
            # must keep this separate to reduce time spent in 'lock'
            await helpers.request_entry(interaction.user, event_attempt=True)
        elif output == 'success':
            # if field was updated, add/edit key-value pair of discordID-status, to be used if status is changed
            self.last_statuses[interaction.user.id] = status


async def handle_interaction(last_status, status, interaction, parent_message) -> str:
    if last_status == status:  # don't do anything if they are already in this category
        return 'ignore'

    user = interaction.user
    entry = await db.get_entry(user.id)
    if not entry:
        # await helpers.request_entry(user, event_attempt=True)
        # moved request_entry() to the event button to minimize time spent in 'lock'
        return 'request_entry'

    # add the user's name to the selected field, and remove it from the last field if applicable
    await update_event_field(parent_message, user.display_name, status, remove_status=last_status)
    # update the database
    await db.update_status(user.id, status)
    # send ephemeral message to eventChannel
    await interaction.response.send_message(f'Registered as **{status}** for {globals.eventInfo}.', ephemeral=True)

    if last_status is None:  # this is their first response to event
        if status != 'NO':  # only DM them if their response is YES or MAYBE
            entry = list(entry)
            entry[-2] = status
            embed = db.info_embed(entry)
            await user.send(embed=embed)
    else:
        # if this is not their first response to event, DM them with change-string instead of full embed
        await user.send(f'Your status has been changed from '
                        f'**{last_status}** to **{status}** for {globals.eventInfo}')

    return 'success'


async def update_event_field(message: discord.Message, name: str, status: str, remove_status=None) -> None:
    """
    Updates the embed fields with attendee names.
    First remove names, then add, then resolve empty/new fields to avoid indexing errors.

    Each field has 1024 char limit (use 1000 for safety). The embed has 6000 char limit.
    """
    embed = message.embeds[0]

    # truncate names to 8 letters
    name = name[:globals.MAX_NAME_LENGTH_IN_EMBED_FIELD]

    if remove_status is not None:
        edit_field_values(embed, name, remove_status, operation='remove')

    edit_field_values(embed, name, status, operation='add')

    await message.edit(embed=embed)


def get_field_indices_of_status(fields, status: str) -> list[int]:
    titles = [field.name.split()[0] for field in fields]
    maybeIndex = titles.index('MAYBE')
    noIndex = titles.index('NO')
    rangeDict = {
        'YES': [0, maybeIndex],
        'MAYBE': [maybeIndex, noIndex],
        'NO': [noIndex, len(titles)]
    }
    return rangeDict[status]


def get_names_list_from_field_value(field_value: str) -> list[str]:
    """
    Parse field-value string into a list of names.
    Each name ends with "\n", but sometimes discord strips the trailing "\n".
    """
    field_value = field_value[len(fieldPrefix):]
    names = field_value.split('\n')
    if names[-1] == '':
        names = names[:-1]
    return names


def edit_field_values(embed, name, status, operation: str):
    """
    Parses the field-value strings into lists for ease of manipulation.
    """
    logging.debug(f'\nSTATUS: {status}, OPERATION: {operation}')
    fields = embed.fields
    status_range = get_field_indices_of_status(fields, status)
    names = []
    for i in range(*status_range):
        fieldVal = fields[i].value
        names.extend(get_names_list_from_field_value(fieldVal))

    if operation == 'remove':
        try:
            names.remove(name)
        except ValueError:
            # if user changed display name after joining event, their old name cannot be removed
            # there will be a duplicate entry in the embed, but everything else will work fine
            logging.error(f'NAME: {name} not found in STATUS: {status}. User may have changed display name.')
            return
    else:
        names.append(name)

    # Build the field-value strings
    # Each field must start with fieldPrefix. Maximum field length is 1024 chars
    fieldVals = []
    fieldVal = fieldPrefix
    while names:
        fieldVal += names.pop(0) + '\n'
        if len(fieldVal) > 1000:
            # names are capped at globals.MAX_NAME_LENGTH_IN_EMBED_FIELD chars, +1 for '\n'
            # so len(fieldVal) in this block is in [1001, 1001 + MAX_NAME_LENGTH]
            fieldVals.append(fieldVal)
            fieldVal = fieldPrefix

    if fieldVal != fieldPrefix:
        # Need to append the names after exiting while loop
        fieldVals.append(fieldVal)

    if fieldVal == fieldPrefix and operation == 'remove':
        # This happens if a field with only one name had its name removed.
        # Losing a field messes with the field indices. Easier to keep an empty placeholder field.
        # Note that the first condition could be true after an "add" operation, without the same issue.
        fieldVals.append(fieldVal)

    # edit the fields
    for ind in range(*status_range):
        fieldVal = fieldVals.pop(0)
        numberOfNames = fieldVal.count('\n')
        title = (status + f'  [{numberOfNames}]') if ind == status_range[0] else '\u200b'
        embed.set_field_at(ind, name=title, value=fieldVal)

    if fieldVals:
        # Happens if an "add" operation caused overflow, so we need a new field
        if len(fieldVals) > 1:
            logging.error('More than 1 fieldVal remaining at end.')
        embed.insert_field_at(status_range[1], name='\u200b', value=fieldVals.pop())
