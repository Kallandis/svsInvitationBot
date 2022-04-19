#   table USERS
# cursor.execute("""CREATE TABLE USERS (
#         discord_ID INTEGER NOT NULL PRIMARY KEY,
#         class TEXT,
#         unit TEXT,
#         level INTEGER,
#         status TEXT,
#         tokens INTEGER,
#         lottery INTEGER
#         );
#     """)
import globals
from discord.ext.tasks import loop
import sqlite3 as sql3


@loop(seconds=15, reconnect=True)
async def sql_write():
    with sql3.connect('userHistory.db') as conn:
        cur = conn.cursor()
        for entry in globals.sqlEntries:
            try:
                cur.execute(entry[0], entry[1])
            except:
                pass

    globals.sqlEntries = []


def add_entry(entry: tuple):
    """
    param [tuple] entry: INT, STRING, STRING, INT, STRING, INT, INT
    Status and Tokens default to 0
    Lottery default to 1
    Profession must be provided by User
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, status, tokens, lottery) values(?, ?, ?, ?, ?, ?, ?)"
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


def get_entry(conn, discord_id: int):
    """
    Returns entry assoc with unique discord ID. If no entry exists, returns empty list
    """
    user = conn.execute("SELECT FROM USERS WHERE DISCORD_ID = ?", discord_id)
    return list(user)


def update_tokens(conn, discord_id, delete_tokens=False, tokens=0):
    """
    param [int] discord_id: unique identifier of User invoking command
    param [bool] delete_tokens: if True, reset tokens to 0
    param [int] tokens: number of tokens to add
    """

    sql = "UPDATE USERS SET TOKENS = ? WHERE DISCORD_ID = ?"
    if delete_tokens:
        entry = [0, discord_id]
        # conn.execute(sql, entry)
    else:
        old_tokens = conn.execute("SELECT TOKENS FROM USERS WHERE DISCORD_ID = ?", discord_id)
        new_tokens = old_tokens + tokens
        entry = [new_tokens, discord_id]
        # conn.execute("UPDATE USERS SET TOKENS = ? WHERE DISCORD_ID = ?", [new_tokens, discord_id])

    globals.sqlEntries.append([sql, entry])


def update_profession(discord_id, prof: str):
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message, checked in main.py
    """
    # get class (MM, CE)
    prof = prof.upper()
    clas = prof[0:2]
    prof = prof[2:]

    # get unit (A, N, F)
    if 'A' in prof:
        unit = 'A'
        prof = prof.replace('A', '')
    elif 'N' in prof:
        unit = 'N'
        prof = prof.replace('N', '')
    else:
        unit = 'F'
        prof = prof.replace('F', '')

    # get level
    # CE: (2 (or nothing), 3, 3X, 3XE, M)
    # MM: (0 (no T), 3T, 5T, 10, E)
    ceLevelDict = {
        "2":    0,
        "3":    1,
        "3X":   2,
        "3XE":  3,
        "M":    4
    }
    mmLevelDict = {
        "0T":   0,
        "3T":   1,
        "5T":   2,
        "10":   3,
        "E":    4
    }
    if clas == "CE":
        level = ceLevelDict.get(prof, "0")
    else:
        level = mmLevelDict.get(prof, "0")

    sql = "UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ? WHERE DISCORD_ID = ?"
    entry = [clas, unit, level, discord_id]
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


def update_lotto(discord_id, lotto: int):
    sql = "UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?"
    entry = [lotto, discord_id]
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


def update_status(discord_id, status: str):
    sql = "UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?"
    entry = [status, discord_id]
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


# this one can just run immediately rather than go into write-loop
def reset_status(conn):
    sql = "UPDATE USERS SET STATUS = NO"

    # write-loop should only be active while event is open for signup
    sql_write.cancel()
    with conn:
        conn.execute(sql)


def all_of_category(conn, category: str, value):
    """
    return a list of all user tuples that satisfy a condition
    """
    # all (ID, prof, tokens) of status
    if category == 'status':
        users = conn.execute("SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE STATUS = ?", value)

    # all (ID, prof, tokens) of class
    elif category == "class":
        users = conn.execute("SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE CLASS = ?", value)

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        users = conn.execute("SELECT DISCORD_ID FROM USERS WHERE STATUS = YES AND LOTTERY = ?", value)

    else:
        return None

    return list(users)    # list of user tuples


def dump_db(conn):
    with open('dump.sql', 'w') as file:
        for line in conn.iterdump():
            file.write(line + '\n')
