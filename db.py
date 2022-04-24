import globals
import discord
from discord.ext.tasks import loop
import sqlite3 as sql3
import logging


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
    Status and Tokens default to 0
    Lottery default to 1
    Profession must be provided by User
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


def info_embed(entry: list, show=None):
    # extract values from entry
    clas, unit, level, mm_traps, skins, status, lottery = entry[1:]

    # format values for display
    unitDict = {'A': 'Army', 'F': 'Air Force', 'N': 'Navy'}
    ceLevelDict = {0: "2", 1: "3", 2: "3X", 3: "3XE"}
    mmLevelDict = {0: "0T", 1: "3T", 2: "5T", 3: "10", 4: "E"}

    units = [unitDict[char] for char in unit]
    level = ceLevelDict[level] if clas == 'CE' else mmLevelDict[level]
    mm_traps = mm_traps.split(', ')
    skins = skins.split(', ')
    lottery = 'YES' if lottery == 1 else 'NO'

    # fields accept a string, so build a '\n'-separated string from lists
    units = '\n'.join(units)
    mm_traps = '\n'.join(mm_traps)
    skins = '\n'.join(skins)

    unitTitle = 'Unit' if '\n' not in units else 'Units'
    mm_trapsTitle = 'Trap' if '\n' not in mm_traps else 'Traps'
    skinTitle = 'Skin' if '\n' not in skins else 'Skins'

    # get event info
    eventTitle, eventTime, eventMessageID = get_event()

    # make embed object, to be added to and returned
    # embed = discord.Embed(title='Database Info', description='abcedasdad')

    if show is None:    # show all info
        title = 'Database Info'
        if eventMessageID:
            eventInfo = eventTitle + ' @ ' + eventTime
            descr = f'You are marked as **{status}** for {eventInfo}'
        else:
            descr = '\u200b'
        embed = discord.Embed(title=title, description=descr, color=discord.Color.brand_green())
        # maximum of 3 fields in a row
        embed.add_field(name='Class', value=clas)
        embed.add_field(name=unitTitle, value=units)
        embed.add_field(name='Level', value=level)
        embed.add_field(name=mm_trapsTitle, value=mm_traps)
        embed.add_field(name=skinTitle, value=skins)
        embed.add_field(name='\u200b', value='\u200b')  # placeholder to align with above 3 fields
        embed.add_field(name='Lottery', value=lottery, inline=False)


    # add a local file as logo
    file = discord.File(r'C:\Users\evanm\Pictures\logo.png', filename='logo.png')
    embed.set_thumbnail(url='attachment://logo.png')
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
