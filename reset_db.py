#!/home/pi/python_projects/svs_bot/.venv/bin/python3

import aiosqlite
import os
import asyncio

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def reset_db():

    # User database
    if os.path.exists("userHistory.db"):
        os.remove("userHistory.db")

    # with sql3.connect('userHistory.db') as conn:
    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""CREATE TABLE USERS (
                    discord_ID INTEGER NOT NULL PRIMARY KEY,
                    class TEXT,
                    level INTEGER,
                    unit TEXT,
                    march_size TEXT,
                    alliance TEXT,
                    mm_traps TEXT,
                    skins TEXT,
                    status TEXT,
                    lottery INTEGER
                    );
                """)
            await conn.commit()

    # Event database
    if os.path.exists("eventInfo.db"):
        os.remove("eventInfo.db")

    # with sql3.connect('eventInfo.db') as conn:
    async with aiosqlite.connect('eventInfo.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""CREATE TABLE EVENT (
                    title TEXT,
                    time TEXT,
                    message_ID INT,
                    channel_ID INT
                    );
                """)
            await cursor.execute("INSERT INTO EVENT (title, time, message_ID, channel_ID) values ('placeholder', 'placeholder', 0, 0)")
            await conn.commit()


if __name__ == "__main__":
    confirm_reset = input("Are you sure you want to reset the database? Type CONFIRM to confirm.\n")
    if confirm_reset.lower() == "confirm":
        asyncio.run(reset_db())
