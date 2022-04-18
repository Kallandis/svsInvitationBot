#   table USERS
# cursor.execute("""CREATE TABLE USERS (
#         discord_ID INTEGER NOT NULL PRIMARY KEY,
#         role TEXT,
#         status INTEGER,
#         tokens INTEGER
#         );
#     """)


def add_entry(conn, entry):
    """
    param [tuple] entry: INT, STRING, INT, INT
    Status and Tokens default to 0
    Role must be provided by User
    """
    sql = "INSERT INTO USERS (discord_ID, role, status, tokens) values(?, ?, ?)"
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


def update_role(conn, discord_id, new_role):
    """
    param [str] new_role: one of ~10 role designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    """
    conn.execute("UPDATE USERS SET ROLE = ? WHERE DISCORD_ID = ?", [new_role, discord_id])


def update_status(conn, discord_id, status):
    statusDict = {'NO': 0, 'YES': 1, 'MAYBE': 2}
    status = statusDict[status]
    conn.execute("UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?", [status, discord_id])


def all_of_status(conn, status):
    statusDict = {'NO': 0, 'YES': 1, 'MAYBE': 2}
    status = statusDict[status]
    users = conn.execute("SELECT DISCORD_ID, ROLE, TOKENS FROM USERS WHERE STATUS = ?", status)
    return users    # sqlite3 cursor object (iterator)


def dump_db(conn):
    with open('dump.sql', 'w') as file:
        for line in conn.iterdump():
            file.write(line + '\n')
