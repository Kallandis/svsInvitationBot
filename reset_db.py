import sqlite3 as sql3
import os

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def reset_db():

    # User database
    if os.path.exists("userHistory.db"):
        os.remove("userHistory.db")

    with sql3.connect('userHistory.db') as conn:

        conn.execute("""CREATE TABLE USERS (
                discord_ID INTEGER NOT NULL PRIMARY KEY,
                class TEXT,
                unit TEXT,
                level INTEGER,
                mm_traps TEXT,
                skins TEXT,
                status TEXT,
                lottery INTEGER
                );
            """)

    # Event database
    if os.path.exists("eventInfo.db"):
        os.remove("eventInfo.db")

    with sql3.connect('eventInfo.db') as conn:
        conn.execute("""CREATE TABLE EVENT (
                title TEXT,
                time TEXT,
                message_ID INT,
                channel_ID INT
                );
            """)
        conn.execute("INSERT INTO EVENT (title, time, message_ID, channel_ID) values ('placeholder', 'placeholder', 0, 0)")


if __name__ == "__main__":
    confirm_reset = input("Are you sure you want to reset the database? Type CONFIRM to confirm.\n")
    if confirm_reset == "CONFIRM":
        reset_db()
