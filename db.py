import globals
from discord.ext.tasks import loop
import sqlite3 as sql3
import logging


@loop(seconds=15, reconnect=True)
async def sql_write():
    with sql3.connect('userHistory.db') as conn:
        for entry in globals.sqlEntries:
            try:
                conn.execute(entry[0], entry[1])
            except:
                pass

    globals.sqlEntries = []


def add_entry(values: list):
    """
    param [list] entry: INT, STRING, STRING, INT, STRING, INT, INT
    Status and Tokens default to 0
    Lottery default to 1
    Profession must be provided by User
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, status, tokens, lottery) values(?, ?, ?, ?, ?, ?, ?)"
    globals.sqlEntries.append([sql, values])


def get_entry(discord_id: int):
    """
    Returns entry (list) associated with unique discord ID. If no entry exists, returns False
    """
    sql = "SELECT FROM USERS WHERE DISCORD_ID = ?"
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


def update_tokens(discord_id, delete_tokens=False, tokens=0):
    """
    param [int] discord_id: unique identifier of User invoking command
    param [bool] delete_tokens: if True, reset tokens to 0
    param [int] tokens: number of tokens to add
    """

    update_sql = "UPDATE USERS SET TOKENS = ? WHERE DISCORD_ID = ?"
    if delete_tokens:
        values = [0, discord_id]
        # conn.execute(sql, entry)
    else:
        with sql3.connect('userHistory.db') as conn:
            sql = "SELECT TOKENS FROM USERS WHERE DISCORD_ID = ?"
            old_tokens = list(conn.execute(sql, [discord_id]))[0]
        new_tokens = old_tokens + tokens
        values = [new_tokens, discord_id]

    globals.sqlEntries.append([update_sql, values])


def parse_profession(prof: str):
    """
    Takes user-input profession-string
    Parses and returns (CLASS, UNIT, LEVEL) according to rules
    If fail to parse, return False
    """
    # get class (MM, CE)
    prof = prof.upper()
    clas = prof[0:2]
    prof = prof[2:]
    # make sure clas is MM or CE
    if clas not in ["MM", "CE"]:
        logging.error('Failed to parse Class from input')
        return False

    # get unit (A, N, F)
    if 'A' in prof:
        unit = 'A'
        prof = prof.replace('A', '')
    elif 'N' in prof:
        unit = 'N'
        prof = prof.replace('N', '')
    elif 'F' in prof:
        unit = 'F'
        prof = prof.replace('F', '')
    elif 'M' in prof:
        unit = 'M'
    else:
        logging.error('Failed to parse unit from input')
        return False

    # get level
    # CE: (2 (or nothing), 3, 3X, 3XE, M)
    # MM: (0 (no T), 3T, 5T, 10, E)
    ceLevelDict = {
        "2": 0,
        "3": 1,
        "3X": 2,
        "3XE": 3,
        "M": 4
    }
    mmLevelDict = {
        "0T": 0,
        "3T": 1,
        "5T": 2,
        "10": 3,
        "E": 4
    }
    if clas == "CE":
        level = ceLevelDict.get(prof, None)
    else:
        level = mmLevelDict.get(prof, None)

    if level is None:
        logging.error('Failed to parse level from input')
        return False

    return [clas, unit, level]


def update_profession(discord_id, prof_array: list):
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message
    """

    sql = "UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ? WHERE DISCORD_ID = ?"
    entry = prof_array.append(discord_id)
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])
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

    with sql3.connect('userHistory.db') as conn:
        conn.execute(sql)


def all_of_category(category: str, value):
    """
    return a list of all user tuples that satisfy a condition
    """

    conn = sql3.connect('userHistory.db')
    # all (ID, prof, tokens) of status
    if category == 'status':
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE STATUS = ?"
        users = conn.execute(sql, [value])

    # all (ID, prof, tokens) of class
    elif category == "class":
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE CLASS = ?"
        users = conn.execute(sql, [value])

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = YES AND LOTTERY = ?"
        users = conn.execute(sql, value)

    else:
        return None

    conn.close()
    return list(users)    # list of user tuples


def dump_db():
    with open('dump.sql', 'w') as file:
        with sql3.connect('userHistory.db') as conn:
            for line in conn.iterdump():
                file.write(line + '\n')
