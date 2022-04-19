import sqlite3 as sql3
import os

if os.path.exists("userHistory.db"):
    os.remove("userHistory.db")

with sql3.connect('userHistory.db') as conn:

    conn.execute("""CREATE TABLE USERS (
            discord_ID INTEGER NOT NULL PRIMARY KEY,
            class TEXT,
            unit TEXT,
            level INTEGER,
            status TEXT,
            tokens INTEGER,
            lottery INTEGER
            );
        """)


if os.path.exists("eventInfo.db"):
    os.remove("eventInfo.db")

with sql3.connect('eventInfo.db') as conn:
    conn.execute("""CREATE TABLE EVENT (
            title TEXT,
            time TEXT
            );
        """)
