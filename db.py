#   table USERS
# cursor.execute("""CREATE TABLE USERS (
#         discord_ID INTEGER NOT NULL PRIMARY KEY,
#         class TEXT,
#         unit TEXT,
#         level INTEGER,
#         status INTEGER,
#         tokens INTEGER,
#         lottery INTEGER
#         );
#     """)


def add_entry(conn, entry: tuple):
    """
    param [tuple] entry: INT, STRING, STRING, INT, INT, INT, INT
    Status and Tokens default to 0
    Lottery default to 1
    Profession must be provided by User
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, status, tokens, lottery) values(?, ?, ?, ?, ?, ?, ?)"
    conn.execute(sql, entry)


def update_tokens(conn, discord_id, delete_tokens=False, tokens=0):
    """
    param [int] discord_id: unique identifier of User invoking command
    param [bool] delete_tokens: if True, reset tokens to 0
    param [int] tokens: number of tokens to add
    """

    if delete_tokens:
        conn.execute("UPDATE USERS SET TOKENS = ? WHERE DISCORD_ID = ?", [0, discord_id])
    else:
        old_tokens = conn.execute("SELECT TOKENS FROM USERS WHERE DISCORD_ID = ?", discord_id)
        new_tokens = old_tokens + tokens
        conn.execute("UPDATE USERS SET TOKENS = ? WHERE DISCORD_ID = ?", [new_tokens, discord_id])


def update_profession(conn, discord_id, prof: str):
    """
    param [str] new_profession: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
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

    conn.execute("UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ? WHERE DISCORD_ID = ?",
                 (clas, unit, level, discord_id))


def update_lotto(conn, discord_id, lotto: int):
    conn.execute("UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?", [lotto, discord_id])


def update_status(conn, discord_id, status: str):
    statusDict = {'NO': 0, 'YES': 1, 'MAYBE': 2}
    status = statusDict[status]
    conn.execute("UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?", [status, discord_id])


def all_of_category(conn, category: str, value):
    """
    return all users that satisfy a certain criterion
    returns a sqlite3 cursor object (iterator) which parses as a list of tuples
    """
    if category == 'status':
        statusDict = {'NO': 0, 'YES': 1, 'MAYBE': 2}
        status = statusDict[value]
        users = conn.execute("SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE STATUS = ?", status)
    elif category == "class":
        users = conn.execute("SELECT DISCORD_ID, CLASS, UNIT, LEVEL, TOKENS FROM USERS WHERE CLASS = ?", value)
    else:
        return None

    return users    # sqlite3 cursor object (iterator)


def dump_db(conn):
    with open('dump.sql', 'w') as file:
        for line in conn.iterdump():
            file.write(line + '\n')
