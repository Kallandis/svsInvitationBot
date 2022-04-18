import sqlite3 as sql3
import os

if os.path.exists("userHistory.db"):
    os.remove("userHistory.db")

conn = sql3.connect('userHistory.db')

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
