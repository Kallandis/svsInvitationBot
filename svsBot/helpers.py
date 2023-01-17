import discord
from discord.ext import commands, tasks
import datetime
import time
import random
import csv
from asyncio import TimeoutError
from typing import Union
import asyncio

from . import db, globals
from . profession_interaction import ProfessionMenuView


def parse_event_input(datestring=None, hour=None, title=None, descr=None):
    """
    Input parser for my_commands.create(), my_commands.edit()
    datestring, hour should be provided together
    Other than that, only one of the args should be given at a time.
    """

    # parse and check the event time
    if datestring is not None and hour is not None:
        # parse YY/MM/DD from command input
        try:
            year, month, day = [int(x) for x in datestring.split('/')]
            if year < 2000:
                year += 2000
            # convert to unix time
            date_time = datetime.datetime(year, month, day, int(hour), 0)
            event_unix_time = int(time.mktime(date_time.timetuple()))

            # get time until event
            timeUntilEvent = event_unix_time - time.time()

        # catch errors from parsing input into datetime object
        except ValueError:
            error = 'Date or hour was invalid.'
            raise commands.CheckFailure(error)

        # event must be at least 10 minutes in the future
        if timeUntilEvent < 10 * 60:
            error = 'Event less than 10 minutes in the future.'
            raise commands.CheckFailure(error)

        # return eventTime for global variable, timeUntilEvent for maybe loop
        eventTimeFmt = f"<t:{event_unix_time}>"
        return eventTimeFmt, timeUntilEvent
        # eventInfo = title + ' @ ' + eventTime

    # check title
    if title is not None:
        # title is limited to 256 chars
        if len(title) > 256:
            error = 'Title over 256 characters.'
            raise commands.CheckFailure(error)
        return title

    # check descr
    if descr is not None:
        # not a technical limitation, but embed can only hold 6000 characters, so can't let this be too long
        if len(descr) > 512:
            error = 'Event description over 512 characters.'
            raise commands.CheckFailure(error)
        return descr

    # return eventTime, timeUntilEvent, eventInfo, title, descr


def build_event_embed(title, descr, cmd_list, old_embed=None):

    # if reusing the old event's description, must avoid adding the firstTimeHint twice
    if 'If this is your first time interacting' not in descr:
        firstTimeHint = '\n\nIf this is your first time interacting with the bot, you will see "This interaction ' \
                        'failed." The bot will send you a DM with instructions.\n\u200b'
        descr += firstTimeHint

    embed = discord.Embed(title=title, description=descr, color=discord.Color.dark_red())

    if old_embed is None:
        embed.add_field(name="YES  [0]", value=">>> \u200b")
        embed.add_field(name="MAYBE  [0]", value=">>> \u200b")
        embed.add_field(name="NO  [0]", value=">>> \u200b")
    else:
        # being called from edit(); add the fields from the old event message
        fields = old_embed.fields
        for field in fields:
            name = field.name
            val = field.value
            embed.add_field(name=name, value=val)

    embed.set_footer(text=', '.join(cmd_list))
    embed.timestamp = discord.utils.utcnow()

    if globals.LOGO_URL:
        embed.set_thumbnail(url=globals.LOGO_URL)

    return embed


# TODO: test this
async def start_confirm_maybe_loop(time_until_event: float,
                                   event_guild: discord.Guild) -> Union[asyncio.Task, None]:
    """
        When it is X hours before the event, remind "MAYBE" users that they are registered as Maybe.
        X = globals.confirmMaybeWarningTimeHours
    """

    # get the time until the reminder should happen
    time_until_reminder = time_until_event - globals.CONFIRM_MAYBE_WARNING_HOURS * 60 * 60

    # "maybes" will only be reminded if it would be at least 2 days in the future
    if time_until_reminder < 2 * 24 * 60 * 60:
        return

    async def send_reminders() -> None:
        # send a reminder embed to all users that are signed up to the event as "MAYBE"

        # build embed
        title = 'Event Reminder'
        descr = f'You are registered as **MAYBE** for {globals.eventInfo}\n' \
                f'If you would like to change your status, go to [Event Message]({globals.eventMessage.jump_url})'
        embed = discord.Embed(title=title, description=descr)

        # send embed to all maybes
        maybeEntries = await db.all_of_category('status', 'MAYBE')
        for entry in maybeEntries:
            user = event_guild.get_member(entry[0])
            await user.send(embed=embed)

    # loop to schedule the reminder for the future
    @tasks.loop(seconds=time_until_reminder, count=2)
    async def confirm_maybe_loop():
        # the loop immediately runs once upon start, so must loop twice, wait until second loop to send reminder
        if confirm_maybe_loop.current_loop > 0:
            await send_reminders()

    # print(type(confirm_maybe_loop))
    # print(dir(confirm_maybe_loop))
    # start the loop
    maybe_loop = confirm_maybe_loop.start()
    # print(type(maybe_loop))
    # print(dir(maybe_loop))
    return maybe_loop

    # return confirm_maybe_loop


async def request_entry(user: Union[discord.Member, discord.User], event_attempt=False) -> None:
    """
    Prompt unregistered user to provide data entry for SQL database.
    Called when user reacts to an event or uses DM command $lotto or $info before being added to DB
    """

    if event_attempt:
        cont = "Your event sign-up has been cancelled because you are not in the database.\n" \
               "After entering your information, you may sign up for the event again.\n"
    else:
        cont = "You do not have an existing entry in the database. Please enter information.\n"
    cont += "Menu will disappear in 5 minutes."

    msg = await user.send(content=cont)
    # DB will be updated following user interaction with ProfessionMenu
    view = ProfessionMenuView(msg, 'class', first_entry=True)
    await msg.edit(view=view)


# to be called in delete_event(), finalize_event()
async def delete_event(user, bot, intent: str) -> None:
    """
    Checks for confirmation with invoking user. If yes:
    Sets eventInfo.db to default value
    Sets everyone's status to "NO"
    Removes interaction buttons from event message
    If intent = 'make_csv', builds a CSV of attending users and DMs it to invoking user
    Empties the sql_write() "buffer"
    """

    try:
        _ = globals.eventMessage.content
    except AttributeError:
        # this should only happen if the event message is manually deleted. In that case, need to escape
        # out of the function early, or all of the below code will error. Reset event vars.

        bot.reset_event_vars()
        await db.update_event('placeholder', 'placeholder', 0, 0)
        # reset everyone's status to "NO"
        await db.reset_status()
        resp = 'Event Message not found. This indicates the event message was manually deleted. ' \
               'Event variables should now be reset.'
        await user.send(resp)
        return

    # prompt the user to send "confirm" in DM to confirm their command
    timeout = 60
    prompt = ''
    if intent == 'delete':
        prompt += f'Type "confirm" within {timeout} seconds to confirm you want to delete the event.'
    elif intent == 'make_csv':
        prompt += f'Type "confirm" within {timeout} seconds ' \
                  f'to confirm you want to close signups and receive a CSV of attendees.\n' \
                  f'Doing this is non-reversible, as it will reset everyone\'s status to \"NO\".'

    cmd = globals.COMMAND_PREFIX + ('delete' if intent == 'delete' else 'close')
    embed = discord.Embed(title=f'{cmd}', description=prompt)
    prompt = await user.send(embed=embed)

    # wait for a response from the user
    try:
        reply = await bot.wait_for('message', timeout=timeout,
                                   check=lambda m: m.channel == user.dm_channel and m.author == user)
    except TimeoutError:
        # if no response, edit the prompt to indicate failure
        edit = f'No response received in {timeout} seconds, event **{intent}** cancelled'
        embed = discord.Embed(title=f'{cmd} Timeout', description=edit)
        await prompt.edit(embed=embed)
        return

    # check if reply was not "confirm"
    if reply.content.lower() != 'confirm':
        edit = f'[Event Message]({globals.eventMessage.jump_url})'
        embed = discord.Embed(title=f'{cmd} Failure', description=edit)
        await prompt.edit(embed=embed)
        return

    # reply was "confirm"
    else:
        title = f'{cmd} Success'
        if intent == 'make_csv':
            eventMessageEdit = '```Sign-ups for this event are closed.```'
            # get the CSV file object

            central_guild = bot.get_guild(globals.GUILD_ID_1508)
            if central_guild is None:
                raise commands.CheckFailure('Failed to acquire 1508 guild.')
            csvFile = await build_csv(central_guild, status='YES', finalize=True)
            description = f'CSV of all users that responded "YES" to {globals.eventInfo}\n' \
                          f'[Event Message]({globals.eventMessage.jump_url})'

            # send a backup of the database to dedicated backup channel
            backupChannel = bot.get_channel(globals.DB_BACKUP_CHANNEL_ID)
            dbFile = discord.File('userHistory.db')
            await backupChannel.send(file=dbFile)
        else:
            # intent = 'delete'
            eventMessageEdit = f'```This event was cancelled with {globals.COMMAND_PREFIX}delete.```'
            description = f'Deleted {globals.eventInfo}\n' \
                          f'[Event Message]({globals.eventMessage.jump_url})'
            csvFile = None

    # remove the EventButtons view, put some text above the event embed indicating it's closed / deleted
    await globals.eventMessage.edit(content=eventMessageEdit, view=None)
    embed = discord.Embed(title=title, description=description)

    # if csvFile is not None, attach it to the message edit
    kwargs = {'embed': embed, 'attachments': [csvFile]} if csvFile else {'embed': embed}
    await prompt.edit(**kwargs)

    # reset event-related variables and confirm maybe loop
    bot.reset_event_vars()

    # globals.eventInfo = ''
    # globals.eventMessage = None
    # globals.eventChannel = None

    # # stop the maybe loop (if it is still running)
    # globals.maybe_loop.cancel()
    # globals.maybe_loop = None

    # reset event database
    await db.update_event('placeholder', 'placeholder', 0, 0)
    # reset everyone's status to "NO"
    await db.reset_status()


async def build_csv(guild: discord.Guild, status: str = 'YES', sorting=True, finalize=False) -> discord.File:
    """
    Parses the user database into CSV subcategories.
    Outputs a formatted, sorted CSV, with unsorted rows at the bottom.

    ARGS:
        guild:      the guild to pull display-names from
        status:     * to get all users in db (that have globals.CSV_ROLE_NAME)
                    YES to get all users who have indicated YES or MAYBE    (yeah, it's confusing)
        finalize:   Indicate that the event has been closed.
                    TRUE --> Triggers lottery, ignores MAYBE-statuses

    NOTE:
        get_csv <all/attending> makes a call with finalize=False
    """

    if finalize:
        # select lotto winners
        lottoEntries = await db.all_of_category('lotto', 1, guild=guild, display_name=True)
        random.shuffle(lottoEntries)
        lottoWinners = lottoEntries[:globals.NUMBER_OF_LOTTO_WINNERS]

    # get class arrays
    ce = await db.all_of_category('class', 'CE', guild=guild, status=status, display_name=True)
    mm = await db.all_of_category('class', 'MM', guild=guild, status=status, display_name=True)
    if status == 'YES' and sorting:
        sorted_maybe = await db.all_of_category('status', 'maybe', guild, display_name=True)
    else:
        sorted_maybe = []

    # it's really hard to go through all of this messy code and make it reusable for both sorting and non-sorting
    # so instead, I'm just going to tack on some extra logic that handles the non-sorted CSV, and otherwise only change
    # the file-write code (and have to bring parse_entry outside of convert_array)
    # get arrays for unsorted CSV
    if not sorting:
        # get the yes and maybe attendees
        # unsorted_yes = await db.all_of_category('status', 'YES', guild, display_name=True)
        unsorted_yes =  await db.all_of_category('class', 'CE', guild=guild, status='YES', display_name=True)
        unsorted_yes += await db.all_of_category('class', 'MM', guild=guild, status='YES', display_name=True)
        unsorted_maybe =  await db.all_of_category('class', 'CE', guild=guild, status='MAYBE', display_name=True)
        unsorted_maybe += await db.all_of_category('class', 'MM', guild=guild, status='MAYBE', display_name=True)
        if status == '*':
            # if called with "all", also get the no's to complete the set
            unsorted_no = await db.all_of_category('class', 'CE', guild=guild, status='NO', display_name=True)
            unsorted_no += await db.all_of_category('class', 'MM', guild=guild, status='NO', display_name=True)
        else:
            unsorted_no = []

    # name, class, level, unit, march_size, traps, skins
    nameIndex = 0
    classIndex = 1
    levelIndex = 2
    unitIndex = 3
    marchIndex = 4
    allianceIndex = 5
    trapsIndex = 6
    skinsIndex = 7

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

    allianceDict = {'508S': 0, '508N': 1, '508W': 2, '508E': 3}

    def sort_alliance(entry):
        alliance = entry[allianceIndex]
        return allianceDict[alliance]

    # entries with more than one unit type
    multiUnitArrays = [
        filter(lambda x: len(x[unitIndex]) > 1, ce),
        filter(lambda x: len(x[unitIndex]) > 1, mm)
    ]

    #
    # sort each array in multiUnitArrays by number of units, then by level, then by march size, then by alliance
    # must first sort by alliance
    multiUnitArrays = [sorted(subArray, key=sort_alliance) for subArray in multiUnitArrays]
    # then march size
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

    #
    # sort the unit arrays by level, then by march size, then by alliance
    # must first sort by alliance
    unitArrays = [sorted(subArray, key=sort_alliance) for subArray in unitArrays]
    # then march size
    unitArrays = [sorted(subArray, key=sort_march, reverse=True) for subArray in unitArrays]
    # then level
    unitArrays = [sorted(subArray, key=lambda x: x[levelIndex], reverse=True) for subArray in unitArrays]

    #
    # finally, sort the maybes by class then level
    if sorted_maybe:
        sorted_maybe = sorted(sorted_maybe, key=lambda x: x[levelIndex], reverse=True)
        sorted_maybe = sorted(sorted_maybe, key=lambda x: x[classIndex])

    #
    # also going to do some brief sorting of the "unsorted" entries, just for convenience
    if not sorting:
        if status == 'YES':
            # if "attending" -> status = "YES", then just work with YES/MAYBE entries
            unsorted_yes = sorted(unsorted_yes, key=lambda x: x[levelIndex], reverse=True)
            unsorted_yes = sorted(unsorted_yes, key=lambda x: x[classIndex])
            unsorted_maybe = sorted(unsorted_maybe, key=lambda x: x[levelIndex], reverse=True)
            unsorted_maybe = sorted(unsorted_maybe, key=lambda x: x[classIndex])
        else:
            # if "all" -> status = "*", then combine all entries into one big column
            unsorted_all = [*unsorted_yes, *unsorted_maybe, *unsorted_no]
            for x in unsorted_all:
                print(x)
            unsorted_all = sorted(unsorted_all, key=lambda x: x[classIndex])

    #
    #
    # CONVERT DATA TO HUMAN READABLE TEXT
    # convert level to text, replace commas with spaces, convert traps to acronym, remove traps from CE

    # get conversion dicts
    _, ceLevelDict, mmLevelDict, mmTrapsDict = db.profession_dicts()

    # parse an individual user-entry into csv-readable format
    def parse_entry(entry_: tuple, cls: str):
        # remove the traps entry from CE
        if cls == 'CE':
            newEntry = (
                *entry_[:levelIndex],
                ceLevelDict[entry_[levelIndex]],
                entry_[unitIndex],
                entry_[marchIndex],
                entry_[allianceIndex],
                entry_[skinsIndex].replace(', ', ' ')
            )
        else:
            # for MM, put the traps entry at the end so it does not conflict with CE entries in same col
            newEntry = (
                *entry_[:levelIndex],
                mmLevelDict[entry_[levelIndex]],
                entry_[unitIndex],
                entry_[marchIndex],
                entry_[allianceIndex],
                entry_[skinsIndex].replace(', ', ' '),
                ' '.join(map(mmTrapsDict.get, entry_[trapsIndex].split(', '))),
            )
        return newEntry

    # fxn to convert the big arrays
    def convert_array(array: list):

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

    #
    # convert/parse the arrays
    multiUnitArrays = convert_array(multiUnitArrays)
    unitArrays = convert_array(unitArrays)

    if sorted_maybe:
        # this should only happen if there are maybe entries, status was "attending", and sorting=True
        sorted_maybe = [parse_entry(entry_, entry_[classIndex]) for entry_ in sorted_maybe]

    if not sorting:
        if status == 'YES':
            unsorted_yes = [parse_entry(entry_, entry_[classIndex]) for entry_ in unsorted_yes]
            unsorted_maybe = [parse_entry(entry_, entry_[classIndex]) for entry_ in unsorted_maybe]
        else:
            unsorted_all = [parse_entry(entry_, entry_[classIndex]) for entry_ in unsorted_all]

    #
    #
    # SORTING AND FORMATTING (skip this section for unsorted)
    # begin formatting arrays so that things can be displayed properly, side-by-side, etc

    # make same-length parallel columns of CE and MM multi-unit entries (make them have same number of rows, so they
    # can be displayed side-by-side in CSV)
    diff = len(multiUnitArrays[1]) - len(multiUnitArrays[0])
    # add rows to the shorter subArray between ceMultiUnits and mmMultiUnits
    if diff > 0:
        multiUnitArrays[0].extend([('', '', '', '', '', '')] * diff)
    elif diff < 0:
        multiUnitArrays[1].extend([('', '', '', '', '', '', '')] * (-1 * diff))

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

    # make number of rows the same
    ceMax = max(map(len, ceSingles))
    mmMax = max(map(len, mmSingles))
    for i in range(3):
        if len(ceSingles[i]) < ceMax:
            ceSingles[i].extend([('', '', '', '', '', '', '')] * (ceMax - len(ceSingles[i])))
        if len(mmSingles[i]) < mmMax:
            mmSingles[i].extend([('', '', '', '', '', '', '', '')] * (mmMax - len(mmSingles[i])))

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
    with open(globals.CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        ceColTitles = ['Name', 'Class', 'Level', 'Units', 'March Size', 'Alliance', 'Skins']
        mmColTitles = [*ceColTitles, 'Traps']

        if sorting:
            # Make the sorted CSV as requested by get_csv, close

            ceRowLength = 7
            mmRowLength = 8
            # write the multi-unit entries as parallel columns of CE and MM
            writer.writerow(['CE multi units', *[''] * (ceRowLength - 1), '', '', 'MM multi units', *[''] * 16,
                             'Sorted by number of units then level then march size then alliance'])
            writer.writerow([*ceColTitles, '', '', *mmColTitles])
            writer.writerows(combinedMultiArray)

            # whitespace
            writer.writerows([''] * 8)

            # write the single-unit entries as parallel columns of A, N, F, in groupings of class, ordered by level
            ceColTitles[3] = 'Unit'
            mmColTitles[3] = 'Unit'

            # first do CE entries
            writer.writerow(['CE single units', *[''] * 25, 'Grouped by unit type - sorted by level then march size then alliance'])
            writer.writerow([*ceColTitles, '', '', *ceColTitles, '', '', *ceColTitles])
            writer.writerows(combined_ceSingles)

            # whitespace
            writer.writerows([''] * 5)

            # do again for MM
            writer.writerow(['MM single units', *[''] * 25, 'Grouped by unit type - sorted by level then march size then alliance'])
            writer.writerow([*mmColTitles, '', *mmColTitles, '', *mmColTitles])
            writer.writerows(combined_mmSingles)

            # whitespace
            writer.writerows([''] * 5)

            if sorted_maybe:
                # finally write the sorted_maybe entries here
                writer.writerow(['Maybes'])
                writer.writerow(mmColTitles)
                writer.writerows(sorted_maybe)

            if finalize:
                # whitespace
                writer.writerows([''] * 5)

                # lotto winners
                writer.writerow([f'Lottery Winners ({globals.NUMBER_OF_LOTTO_WINNERS})'])
                writer.writerows(lottoWinners)

        else:
            # make an unsorted CSV as requested by get_raw_csv
            if status == '*':
                writer.writerow('All DB entries')
                writer.writerow(mmColTitles)
                writer.writerow(unsorted_all)

            else:
                # first put the YES entries
                writer.writerow('Event Attendees')
                writer.writerow(mmColTitles)
                writer.writerow(unsorted_yes)

                # whitespace
                writer.writerows([''] * 5)

                # then the MAYBE entries
                writer.writerows(mmColTitles)
                writer.writerows(unsorted_maybe)

    eventCSV = discord.File(globals.CSV_FILENAME)
    return eventCSV
