import sqlite3 as sql3

conn = sql3.connect('userHistory.db')

conn.execute("""CREATE TABLE USERS (
        discord_ID INTEGER NOT NULL PRIMARY KEY,
        class TEXT,
        unit TEXT,
        level INTEGER,
        status INTEGER,
        tokens INTEGER,
        lottery INTEGER
        );
    """)
