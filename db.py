import globals
import discord
from discord.ext.tasks import loop
import sqlite3 as sql3


# temporary function for testing purposes
@globals.bot.command()
async def print_db(ctx):
    with sql3.connect('userHistory.db') as conn:
        entries = conn.execute("SELECT * FROM USERS")

    for entry in entries:
        print(entry)


@loop(seconds=5, reconnect=True)
async def sql_write():
    with sql3.connect('userHistory.db') as conn:
        for entry in globals.sqlEntries:
            try:
                conn.execute(entry[0], entry[1])
            except:
                print(f'Failed to write entry: {entry}')

    globals.sqlEntries = []


def add_entry(values: list):
    """
    param [list] entry: INT, STRING, STRING, INT, STRING, STRING, STRING, INT
    Status defaults to 0
    Lottery defaults to 1
    Profession must be provided by User via calls of ProfessionMenuView()
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, mm_traps, skins, status, lottery) " \
          "values(?, ?, ?, ?, ?, ?, ?, ?)"
    globals.sqlEntries.append([sql, values])


def get_entry(discord_id: int):
    """
    Returns entry (list) associated with unique discord ID. If no entry exists, returns False
    """
    sql = "SELECT * FROM USERS WHERE DISCORD_ID = ?"
    values = [discord_id]
    with sql3.connect('userHistory.db') as conn:
        user = list(conn.execute(sql, values))

    if not user:
        return False
    else:
        return user[0]


def update_event(title: str, time: str, message_id: int):
    sql = "UPDATE EVENT SET TITLE = ?, TIME = ?, MESSAGE_ID = ?"
    values = [title, time, message_id]
    with sql3.connect('eventInfo.db') as conn:
        conn.execute(sql, values)


def get_event():
    sql = "SELECT * FROM EVENT"
    with sql3.connect('eventInfo.db') as conn:
        eventTitle, eventTime, message_id = list(conn.execute(sql))[0]
    return eventTitle, eventTime, message_id


def info_embed(entry: list, descr=''):
    # extract values from entry
    clas, unit, level, mm_traps, skins, status, lottery = entry[1:]

    # format values for display
    unitDict = {'A': 'Army', 'F': 'Air Force', 'N': 'Navy'}
    ceLevelDict = {0: "2", 1: "3", 2: "3X", 3: "3XE"}
    mmLevelDict = {0: "0T", 1: "3T", 2: "5T", 3: "10", 4: "E"}

    units = [unitDict[char] for char in unit]
    level = ceLevelDict[level] if clas == 'CE' else mmLevelDict[level]
    traps = mm_traps.split(', ')
    skins = skins.split(', ')
    lottery = 'YES' if lottery == 1 else 'NO'

    # fields accept a string, so build a '\n'-separated string from lists
    units = '\n'.join(units)
    traps = '\n'.join(traps)
    skins = '\n'.join(skins)

    unitTitle = 'Unit' if '\n' not in units else 'Units'
    trapsTitle = 'Trap' if '\n' not in traps else 'Traps'
    skinsTitle = 'Skin' if '\n' not in skins else 'Skins'

    # get event info
    eventTitle, eventTime, eventMessageID = get_event()

    # initialize arg dictionaries to be used in field creation
    class_args = {'name': 'Class', 'value': clas}
    unit_args = {'name': unitTitle, 'value': units}
    level_args = {'name': 'Level', 'value': level}
    traps_args = {'name': trapsTitle, 'value': traps}
    skins_args = {'name': skinsTitle, 'value': skins}
    lottery_args = {'name': 'Lottery', 'value': lottery}
    whitespace_args = {'name': '\u200b', 'value': '\u200b'}     # used to make an empty field for alignment

    if eventMessageID:
        # if there is an active event, put the event and the user's status in the description field of the embed
        eventInfo = eventTitle + ' @ ' + eventTime
        descr += f'You are marked as **{status}** for {eventInfo}'
    else:
        descr += '\u200b'
    embed = discord.Embed(title='Database Info', description=descr, color=discord.Color.brand_green())

    # add fields to the embed for various entry parameters
    # there are a maximum of 3 fields in a row, stretched to fill a fixed width. Add whitespace fields for alignment
    # row 1: Class, Unit(s), Level
    embed.add_field(**class_args)
    embed.add_field(**unit_args)
    embed.add_field(**level_args)

    # row 2: Trap(s), Skin(s)
    count = 0
    for argDict in [traps_args, skins_args]:
        if argDict['value']:
            embed.add_field(**argDict)
            count += 1
    # add whitespace fields to align with first row
    if count > 0:
        for i in range(3 - count):
            embed.add_field(**whitespace_args)

    # row 3: Lottery
    embed.add_field(**lottery_args)

    # add a local file "logo.png" from the script directory as a thumbnail
    if globals.logoPath:
        file = discord.File(globals.logoPath, filename=globals.logoPath[-8:])
        embed.set_thumbnail(url='attachment://logo.png')
    else:
        file = None

    # DM command information
    embed.set_footer(text="$prof to edit profession  |  $prof ? to show profession  |  "
                          "$lottery to toggle lottery participation")

    return file, embed


def update_profession(discord_id, prof_array: list):
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message
    Should only be called if prof_array is not None
    """

    sql = "UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ?, MM_TRAPS = ?, SKINS = ? WHERE DISCORD_ID = ?"
    values = [*prof_array, discord_id]
    globals.sqlEntries.append([sql, values])
    return True


def update_lotto(discord_id, lotto: int):
    sql = "UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?"
    entry = [lotto, discord_id]
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


def update_status(discord_id, status: str):
    """
    Called by on_raw_reaction_add() to update status when a member reacts to the event embed
    """
    eventTitle, eventTime, message_id = get_event()
    if not message_id:
        return

    sql = "UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?"
    entry = [status, discord_id]
    globals.sqlEntries.append([sql, entry])


# this one can just run immediately rather than go into write-loop
def reset_status():
    sql = "UPDATE USERS SET STATUS = NO"

    globals.sqlEntries = []
    with sql3.connect('userHistory.db') as conn:
        conn.execute(sql)


def all_of_category(category: str, value):
    """
    return a list of all user tuples that satisfy a condition
    """

    conn = sql3.connect('userHistory.db')
    # all (ID, prof) of status
    if category == 'status':
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, MM_TRAPS, SKINS FROM USERS WHERE STATUS = ?"
        users = list(conn.execute(sql, [value]))

    # all (ID, prof) of class
    elif category == "class":
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, MM_TRAPS, SKINS FROM USERS WHERE CLASS = ?"
        users = list(conn.execute(sql, [value]))

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = YES AND LOTTERY = 1"
        users = list(conn.execute(sql, value))

    else:
        conn.close()
        return None

    conn.close()
    return list(users)    # list of user tuples


def dump_db():
    with open('svs_userHistory_dump.sql', 'w') as file:
        with sql3.connect('userHistory.db') as conn:
            for line in conn.iterdump():
                file.write(line + '\n')
