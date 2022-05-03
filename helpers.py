import discord
import random
import csv
from asyncio import TimeoutError
from typing import Union
import asyncio

import db
import globals
from professionInteraction import ProfessionMenuView


async def confirm_maybe() -> None:
    """
    When it is X hours before the event, remind "MAYBE" users that they are registered as Maybe.
    X = globals.confirmMaybeWarningTimeHours
    """
    title = 'Event Reminder'
    descr = f'You are registered as **MAYBE** for {globals.eventInfo}\n' \
            f'If you would like to change your status, go to [Event Message]({globals.eventMessage.jump_url})'
    embed = discord.Embed(title=title, description=descr)

    # send embed to all maybes
    maybeEntries = await db.all_attending_of_category('status', 'MAYBE', display_name=False)
    for entry in maybeEntries:
        user = globals.guild.get_member(entry[0])
        await user.send(embed=embed)


async def request_entry(user: Union[discord.Member, discord.User], event_attempt=False) -> None:
    """
    Prompt unregistered user to provide data entry for SQL database.
    Called when user reacts to an event or uses DM command $lotto or $prof before being added to DB
    """

    if event_attempt:
        cont = "Your event registration because you are not in the database.\n" \
               "After entering your profession, you may register for the event again.\n"
    else:
        cont = "You do not have an existing entry in the database. Please enter profession.\n"
    cont += "Menu will disappear in 5 minutes."

    msg = await user.send(content=cont)
    # DB will be updated following user interaction with ProfessionMenu
    view = ProfessionMenuView(msg, 'class', first_entry=True)
    await msg.edit(view=view)


# to be called in delete_event(), finalize_event()
async def delete_event(user: discord.Member, intent: str) -> None:
    """
    Checks for confirmation with invoking user. If yes:
    Sets eventInfo.db to default value
    Sets everyone's status to "NO"
    Removes interaction buttons from event message
    If intent = 'make_csv', builds a CSV of attending users and DMs it to invoking user
    Empties the sql_write() "buffer"
    """

    if user.dm_channel is None:
        await user.create_dm()
    dmChannel = user.dm_channel

    # prompt the user to send "confirm" in dmChannel to confirm their command
    timeout = 60
    prompt = ''
    if intent == 'delete':
        prompt += f'Type "confirm" within {timeout} seconds to confirm you want to delete the event.'
    elif intent == 'make_csv':
        prompt += f'Type "confirm" within {timeout} seconds ' \
                  f'to confirm you want to close signups and receive a CSV of attendees. Doing this is ' \
                  f'non-reversible, as it will reset everyone\'s status to \"NO\".'

    cmd = globals.commandPrefix + ('delete_event' if intent == 'delete' else 'finalize_event')
    embed = discord.Embed(title=f'{cmd}', description=prompt)
    prompt = await dmChannel.send(embed=embed)

    # wait for a response from the user
    try:
        reply = await globals.bot.wait_for('message', timeout=timeout,
                                           check=lambda m: m.channel == dmChannel and m.author == user)
    except TimeoutError:
        edit = f'No response received in {timeout} seconds, event **{intent}** cancelled'
        embed = discord.Embed(title=f'{cmd} Timeout', description=edit)
        # await prompt.edit(content=edit)
        await prompt.edit(embed=embed)
        return

    # check if reply was not "confirm"
    if reply.content.lower() != 'confirm':
        edit = f'[Event Message]({globals.eventMessage.jump_url})'
        embed = discord.Embed(title=f'{cmd} Failure', description=edit)
        await prompt.edit(embed=embed)
        return

    else:
        # reply was "confirm"
        title = f'{cmd} Success'
        if intent == 'make_csv':
            eventMessageEdit = '```Sign-ups for this event are closed.```'
            # get the CSV file object
            csvFile = build_csv(globals.csvFileName)
            description = f'CSV of all that responded "YES" to {globals.eventInfo}\n' \
                          f'[Event Message]({globals.eventMessage.jump_url})'
        else:
            # intent = 'delete'
            eventMessageEdit = f'```This event was deleted with {globals.commandPrefix}delete_event.```'
            description = f'Deleted {globals.eventInfo}\n' \
                          f'[Event Message]({globals.eventMessage.jump_url})'
            csvFile = None

    # remove the EventButtons view, put some text above the event embed indicating it's closed / deleted
    await globals.eventMessage.edit(content=eventMessageEdit, view=None)
    embed = discord.Embed(title=title, description=description)
    # if csvFile is not None, attach it to the message edit
    kwargs = {'embed': embed, 'attachments': [csvFile]} if csvFile else {'embed': embed}
    await prompt.edit(**kwargs)

    # reset global vars
    globals.eventInfo = ''
    globals.eventMessage = None
    globals.eventChannel = None

    # reset database
    await db.update_event('placeholder', 'placeholder', 0, 0)
    await db.reset_status()


async def build_csv(filename: str) -> discord.File:
    """
    parses the user database into csv subcategories
    """

    # select lotto winners
    lottoEntries = await db.all_attending_of_category('lotto', 1)
    random.shuffle(lottoEntries)
    lottoWinners = lottoEntries[:globals.numberOfLottoWinners]
    # get just the name
    # lottoWinners = [winner[0] for winner in lottoWinners]

    # get class arrays
    ce = await db.all_attending_of_category('class', 'CE')
    mm = await db.all_attending_of_category('class', 'MM')
    # name, class, level, unit, march_size, traps, skins
    nameIndex = 0
    classIndex = 1
    levelIndex = 2
    unitIndex = 3
    marchIndex = 4
    trapsIndex = 5
    skinsIndex = 6

    # to be used as a key for sorting by march size
    def sort_march(entry):
        msize = entry[marchIndex]
        # msize takes the forms {< 160, 160-170, ... , 210-220, > 220}
        if '<' in msize or '>' in msize:
            # strip the < or >
            msize = int(msize.strip('>< '))
        else:
            # take the bottom of the range and add 5 to represent median and avoid equality with smallest edge case
            msize = int(msize.split('-')[0]) + 5
        return msize

    # entries with more than one unit type
    multiUnitArrays = [
        filter(lambda x: len(x[unitIndex]) > 1, ce),
        filter(lambda x: len(x[unitIndex]) > 1, mm)
    ]

    # sort each array in multiUnitArrays by number of units, then by level, then by march size
    # must first sort by march size
    multiUnitArrays = [sorted(subArray, key=sort_march, reverse=True) for subArray in multiUnitArrays]
    # then level
    multiUnitArrays = [sorted(subArray, key=lambda x: x[levelIndex], reverse=True) for subArray in multiUnitArrays]
    # then final sort by number of units
    multiUnitArrays = [sorted(subArray, key=lambda x: len(x[unitIndex]), reverse=True) for subArray in multiUnitArrays]

    #
    # split the single-unit entries of each class into 3 arrays, one for each unit type
    unitArrays = [
        filter(lambda x: x[unitIndex] == 'A', ce),
        filter(lambda x: x[unitIndex] == 'N', ce),
        filter(lambda x: x[unitIndex] == 'F', ce),
        filter(lambda x: x[unitIndex] == 'A', mm),
        filter(lambda x: x[unitIndex] == 'N', mm),
        filter(lambda x: x[unitIndex] == 'F', mm)
    ]

    # sort the unit arrays by level, then by march size
    # must first sort by march size
    unitArrays = [sorted(subArray, key=sort_march, reverse=True) for subArray in unitArrays]
    # then level
    unitArrays = [sorted(subArray, key=lambda x: x[levelIndex], reverse=True) for subArray in unitArrays]

    #
    # convert data into human-readable text
    # convert level to text, replace commas with spaces, convert traps to acronym, remove traps from CE

    # get conversion dicts
    _, ceLevelDict, mmLevelDict, mmTrapsDict = db.profession_dicts()

    # fxn to convert the big arrays
    def convert_array(array: list):

        def parse_entry(entry_: tuple, cls: str):
            # remove the traps entry from CE
            if cls == 'CE':
                newEntry = (
                    *entry_[:levelIndex],
                    ceLevelDict[entry_[levelIndex]],
                    entry_[unitIndex],
                    entry_[marchIndex],
                    entry_[skinsIndex].replace(', ', ' ')
                )
            else:
                # for MM, put the traps entry at the end so it does not conflict with CE entries in same col
                newEntry = (
                    *entry_[:levelIndex],
                    mmLevelDict[entry_[levelIndex]],
                    entry_[unitIndex],
                    entry_[marchIndex],
                    entry_[skinsIndex].replace(', ', ' '),
                    ' '.join(map(mmTrapsDict.get, entry_[trapsIndex].split(', '))),
                )
            return newEntry

        for i in range(len(array)):
            if len(array[i]) == 0:
                # skip sub-array if there are no entries of this type
                # e.g. nobody signed up as 'A', no multi-unit entries of class 'mm', etc
                continue
            class_ = array[i][0][classIndex]
            for j in range(len(array[i])):
                entry = array[i][j]
                entry = parse_entry(entry, class_)
                array[i][j] = entry

        return array

    # convert/parse the arrays
    multiUnitArrays = convert_array(multiUnitArrays)
    unitArrays = convert_array(unitArrays)

    #
    # begin moving arrays around for parallel displays

    # make same-length parallel columns of CE and MM multi-unit entries
    diff = len(multiUnitArrays[0]) - len(multiUnitArrays[1])
    if diff > 0:
        multiUnitArrays[1].extend([('', '', '', '', '', '')] * diff)
    elif diff < 0:
        multiUnitArrays[0].extend([('', '', '', '', '')] * (-1 * diff))

    combinedMultiArray = []
    for i in range(len(multiUnitArrays[0])):
        # combine tuples from CE, MM into one long tuple for CSV row write
        combinedEntry = multiUnitArrays[0][i] + ('', '',) + multiUnitArrays[1][i]
        combinedMultiArray.append(combinedEntry)

    #
    # make same-length parallel columns of A, N, F, grouped by class, sorted by level

    # split in to class groupings
    ceSingles = unitArrays[0:3]
    mmSingles = unitArrays[3:]

    # make lengths the same
    ceMax = max(map(len, ceSingles))
    mmMax = max(map(len, mmSingles))
    for i in range(3):
        if len(ceSingles[i]) < ceMax:
            ceSingles[i].extend([('', '', '', '', '')] * (ceMax - len(ceSingles[i])))
        if len(mmSingles[i]) < mmMax:
            mmSingles[i].extend([('', '', '', '', '', '')] * (mmMax - len(mmSingles[i])))

    # combine tuples from CE {A, N, F}, MM {A, N, F} into one long tuple for CSV row write
    combined_ceSingles = []
    combined_mmSingles = []
    for i in range(ceMax):
        combinedEntry = ceSingles[0][i] + ('', '',) + ceSingles[1][i] + ('', '',) + ceSingles[2][i]
        combined_ceSingles.append(combinedEntry)
    for i in range(mmMax):
        combinedEntry = mmSingles[0][i] + ('',) + mmSingles[1][i] + ('',) + mmSingles[2][i]
        combined_mmSingles.append(combinedEntry)

    # multi-unit should be separate from the rest, just write those in one column
    # single-unit should be one column for each unit type, grouped within column by class, ordered by level
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        colTitles = ['Name', 'Class', 'Level', 'Units', 'March Size', 'Skins']
        ceRowLength = 6
        mmRowLength = 7
        # write the multi-unit entries as parallel columns of CE and MM
        writer.writerow(['CE multi units', *[''] * (ceRowLength - 1), '', '', 'MM multi units', *[''] * 11,
                         'Sorted by number of units followed by level'])
        writer.writerow([*colTitles, '', '', *colTitles, 'Traps'])
        writer.writerows(combinedMultiArray)

        # whitespace
        writer.writerows([''] * 5)

        # write the single-unit entries as parallel columns of A, N, F, in groupings of class, ordered by level
        colTitles[3] = 'Unit'

        # first do CE entries
        writer.writerow(['CE single units', *[''] * 20, 'Grouped by unit type - sorted by level'])
        writer.writerow([*colTitles, '', '', *colTitles, '', '', *colTitles])
        writer.writerows(combined_ceSingles)

        # whitespace
        writer.writerows([''] * 5)

        # do again for MM
        writer.writerow(['MM single units'])
        writer.writerow([*colTitles, 'Traps', '', *colTitles, 'Traps', '', *colTitles, 'Traps'])
        writer.writerows(combined_mmSingles)

        # whitespace
        writer.writerows([''] * 5)

        # lotto winners
        writer.writerow(['Lottery Winners'])
        writer.writerows(lottoWinners)

    eventCSV = discord.File(filename)
    return eventCSV


