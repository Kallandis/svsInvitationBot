import globals
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
    param [list] entry: INT, STRING, STRING, INT, STRING, STRING, INT
    Status and Tokens default to 0
    Lottery default to 1
    Profession must be provided by User
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, items, status, lottery) values(?, ?, ?, ?, ?, ?, ?)"
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


def update_profession(discord_id, prof_array: list):
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message
    Should only be called if prof_array is not None
    """

    sql = "UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ?, ITEMS = ? WHERE DISCORD_ID = ?"
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
    # all (ID, prof, tokens) of status
    if category == 'status':
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, ITEMS FROM USERS WHERE STATUS = ?"
        users = list(conn.execute(sql, [value]))

    # all (ID, prof) of class
    elif category == "class":
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, ITEMS FROM USERS WHERE CLASS = ?"
        users = list(conn.execute(sql, [value]))

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = YES AND LOTTERY = ?"
        users = list(conn.execute(sql, value))

    else:
        return None

    conn.close()
    return list(users)    # list of user tuples


def dump_db():
    with open('svs_userHistory_dump.sql', 'w') as file:
        with sql3.connect('userHistory.db') as conn:
            for line in conn.iterdump():
                file.write(line + '\n')
