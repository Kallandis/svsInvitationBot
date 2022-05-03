import discord
import helpers
import globals
import db

import logging
logger = logging.getLogger(__name__)

import asyncio
lock = asyncio.Lock()


class EventButtonsView(discord.ui.View):

    __slots__ = ('parent_message', 'last_statuses')

    def __init__(self, parent_message: discord.Message):
        super().__init__(timeout=None)
        self.parent_message = parent_message
        self.last_statuses = {}

    @discord.ui.button(label='YES', style=discord.ButtonStyle.success, custom_id='persistent_view:yes')
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'YES'

        # have to make this mutex to avoid r/w problem with editing event message's embed fields
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

    @discord.ui.button(label='MAYBE', style=discord.ButtonStyle.secondary, custom_id='persistent_view:maybe')
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'MAYBE'
        async with lock:
            last_status = self.last_statuses.get(interaction.user.id, None)
            output = await handle_interaction(last_status, status, interaction, self.parent_message)
        if output == 'request_entry':
            await helpers.request_entry(interaction.user, event_attempt=True)
        elif output == 'success':
            self.last_statuses[interaction.user.id] = status

    @discord.ui.button(label='NO', style=discord.ButtonStyle.danger, custom_id='persistent_view:no')
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = 'NO'
        async with lock:
            last_status = self.last_statuses.get(interaction.user.id, None)
            output = await handle_interaction(last_status, status, interaction, self.parent_message)
        if output == 'request_entry':
            await helpers.request_entry(interaction.user, event_attempt=True)
        elif output == 'success':
            self.last_statuses[interaction.user.id] = status

    # # buttons for finalizing and deleting event
    # @discord.ui.button(label='SUBMIT', style=discord.ButtonStyle.success, custom_id='persistent_view:finalize', row=2)
    # async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     user = interaction.user
    #     if globals.adminRole in [role.name for role in user.roles]:
    #         await helpers.delete_event(user, intent='make_csv')
    #
    # @discord.ui.button(label='DELETE', style=discord.ButtonStyle.danger, custom_id='persistent_view:delete', row=2)
    # async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     user = interaction.user
    #     if globals.adminRole in [role.name for role in user.roles]:
    #         await helpers.delete_event(user, intent='delete')


async def handle_interaction(last_status, status, interaction, parent_message) -> str:
    if last_status == status:  # don't do anything if they are already in this category
        return 'ignore'

    user = interaction.user
    entry = await db.get_entry(user.id)
    if not entry:
        # await helpers.request_entry(user, event_attempt=True)
        # moved request_entry() to the event button to minimize time spent in 'lock'
        return 'request_entry'

    # send ephemeral message to eventChannel
    await interaction.response.send_message(f'Registered as **{status}** for {globals.eventInfo}.', ephemeral=True)
    # update the event field, removing user's name from the previous field they were in if it exists
    await update_event_field(parent_message, user.display_name, status, remove_status=last_status)
    # update the database
    await db.update_status(user.id, status)

    if last_status is None:  # this is their first response to event

        if status != 'NO':   # only DM them if their response is YES or MAYBE
            entry = list(entry)
            entry[-2] = status
            await dm_to_user(user, entry=entry)

    else:
        # if this is not their first response to event, DM them with change-string instead of full embed
        await dm_to_user(user, new_status=status, last_status=last_status)

    return 'success'


async def update_event_field(message: discord.Message, name: str, status: str, remove_status=None) -> None:
    # updates the embed fields to show all attendees.
    # first remove/add vals, then resolve empty/new fields to avoid indexing errors
    embed = message.embeds[0]
    fields = embed.fields
    titles = [field.name[:field.name.index('[')].strip() if '[' in field.name else field.name for field in fields]

    maybeIndex = titles.index('MAYBE')
    noIndex = titles.index('NO')
    rangeDict = {
        'YES':   [0, maybeIndex],
        'MAYBE': [maybeIndex, noIndex],
        'NO':    [noIndex, len(titles)]
    }

    def update_fields(field_range: list[int], name, status, add=True):
        # start all fields with a quote block, whitespace char to turn '>>> ' into a quote block even if field is empty
        fieldPrefix = '>>> \u200b'

        if len(name) > 10:
            # truncate names to 10 letters
            name = name[:8] + '..'

        # get the sum of all of the field-vals associated with "status". Add or remove name from that sum
        statusNames = ''
        for i in range(*field_range):
            # get all field-values associated with status without their prefixes (raw status name data)
            statusNames += fields[i].value.replace(fieldPrefix, '')

        if add:
            statusNames += f'{name}\n'
        else:
            statusNames = statusNames.replace(f'{name}\n', '')

        statusCount = statusNames.count('\n')   # number of names is equal to number of '\n' in string

        fieldVals = []
        # loop through the string of '\n'-separated names, building a field-value string ~1024 chars at a time
        while len(fieldPrefix + statusNames) > 1024:
            # get the first 1019 chars to accommodate the leading '> \u200b' which takes 3 chars
            temp = statusNames[:(1024 - len(fieldPrefix))]
            # reverse the string to get the index of the last '\n', which denotes the last complete name
            lastNewlineInd = -1 * temp[::-1].index('\n')
            # add a field-value string to the list, to be made into a field later
            fieldVals.append(fieldPrefix + temp[:lastNewlineInd])
            # slice out the remaining names for future loops
            # statusNames = statusNames[lastNewlineInd:]
            statusNames = temp[lastNewlineInd:] + statusNames[(1024 - len(fieldPrefix)):]

        if statusNames:
            # add the last (0, 1024 - len(fieldPrefix)] chars as a field-value
            fieldVals.append(fieldPrefix + statusNames)

        elif len(fieldVals) < (field_range[1] - field_range[0]):
            # if a field with only one entry had its value removed, the above if would not be entered.
            # add a placeholder field-value
            fieldVals.append(fieldPrefix)

        for addInd in range(*field_range):
            # for each field associated with status, set its value to one of the field-val strings
            title = (status + f'  [{statusCount}]') if addInd == field_range[0] else '\u200b'
            embed.set_field_at(addInd, name=title, value=fieldVals.pop(0))

        if fieldVals:
            # reached when number of field-val strings != num of fields associated with status
            # only happens if the most recent entry caused the old field-val to overflow to a new field

            # add a field to the embed to hold the new entry
            # docs say "insert field before a specified index. I hope that it doesn't actually do that...
            embed.insert_field_at(field_range[1], name='\u200b', value=fieldVals.pop())

    # remove name
    if remove_status is not None:
        # this can cause an overflow-field to have no names. Could technically remove the field, but it isn't worth
        # the hassle to deal with something that is not a real issue (realistically, only 'YES' will have overflow, and
        # the incoming flux of names should be positive on average). The case where the only entry gets removed is
        # handled without error, in update_fields(), but the empty field will remain with '>>> \u200b' as its fieldValue
        remRange = rangeDict[remove_status]
        update_fields(remRange, name, remove_status, add=False)

    # add name
    addRange = rangeDict[status]
    update_fields(addRange, name, status, add=True)

    await message.edit(embed=embed)


async def dm_to_user(user, entry=None, new_status=None, last_status=None) -> None:

    # send user an info embed
    if entry is not None:
        embed = db.info_embed(entry)
        await user.send(embed=embed)

    # send a small text message to ACK change
    elif new_status is not None:
        await user.send(f'Your status has been changed from '
                        f'**{last_status}** to **{new_status}** for {globals.eventInfo}')
