import globals
import discord
from discord.ext.tasks import loop
from typing import Union, Optional

# import asqlite
import aiosqlite

import logging
logger = logging.getLogger(__name__)


@loop(seconds=5, reconnect=True)
async def sql_write():
    with sql3.connect('userHistory.db') as conn:
        for entry in globals.sqlEntries:
            try:
                conn.execute(entry[0], entry[1])
            except:
                print(f'Failed to write entry: {entry}')

    globals.sqlEntries = []


async def add_entry(values: Union[list, tuple]) -> None:
    """
    param [list] entry: INT, STRING, INT, STRING, STRING, STRING, STRING, STRING, INT
    Status defaults to 0
    Lottery defaults to 1
    Profession must be provided by User via calls of ProfessionMenuView()
    """
    sql = "INSERT INTO USERS (discord_ID, class, level, unit, march_size, mm_traps, skins, status, lottery) " \
          "values(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


async def get_entry(discord_id: int) -> Optional[tuple]:
    """
    Returns entry (list) associated with unique discord ID. If no entry exists, returns None
    """
    sql = "SELECT * FROM USERS WHERE DISCORD_ID = ?"
    val = [discord_id]
    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, val)
            entry = await cursor.fetchone()

    if not entry:
        return None
    else:
        return entry


async def update_event(title: str, time: str, message_id: discord.Message.id, channel_id: discord.TextChannel.id) -> None:
    sql = "UPDATE EVENT SET TITLE = ?, TIME = ?, MESSAGE_ID = ?, CHANNEL_ID = ?"
    values = [title, time, message_id, channel_id]
    async with aiosqlite.connect('eventInfo.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


async def get_event() -> tuple[str, str, int, int]:
    sql = "SELECT * FROM EVENT"
    # with sql3.connect('eventInfo.db') as conn:
    #     eventTitle, eventTime, message_id, channel_id = list(conn.execute(sql))[0]

    async with aiosqlite.connect('eventInfo.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql)
            entry = await cursor.fetchone()

    return entry
    # return eventTitle, eventTime, message_id, channel_id


def profession_dicts() -> tuple:
    # return a tuple of dictionaries to be used for formatting database info into human-readable text
    unitDict = {'A': 'Army', 'F': 'Air Force', 'N': 'Navy'}
    ceLevelDict = {0: "2", 1: "3", 2: "3X", 3: "3XE"}
    mmLevelDict = {0: "0T", 1: "3T", 2: "5T", 3: "10", 4: "E"}
    mmTrapsDict = {'Corrosive Mucus': 'CM', 'Supermagnetic Field': 'SF', 'Electro Missiles': 'EM'}

    return unitDict, ceLevelDict, mmLevelDict, mmTrapsDict


def info_embed(entry: Union[list, tuple], descr='') -> discord.Embed:
    # extract values from entry
    # clas, unit, level, mm_traps, skins, status, lottery = entry[1:]
    clas, level, unit, march_size, mm_traps, skins, status, lottery = entry[1:]

    # format values for display
    unitDict, ceLevelDict, mmLevelDict, _ = profession_dicts()

    units = [unitDict[char] for char in unit]
    march_size = '\\' + march_size if '<' or '>' in march_size else march_size  # need to escape the ">" quote char
    level = ceLevelDict[level] if clas == 'CE' else mmLevelDict[level]
    traps = mm_traps.split(', ')
    skins = skins.split(', ')
    lottery = 'YES' if lottery == 1 else 'NO'

    # fields accept a string, so build a '\n'-separated string from lists
    units = '\n'.join(units)
    traps = '\n'.join(traps)
    skins = '\n'.join(skins)

    unitTitle = 'Unit' if '\n' not in units else 'Units'
    # trapsTitle = 'Trap' if '\n' not in traps else 'Traps'
    # skinsTitle = 'Skin' if '\n' not in skins else 'Skins'

    # initialize arg dictionaries to be used in field creation
    class_args = {'name': 'Class', 'value': clas}
    level_args = {'name': 'Level', 'value': level}
    unit_args = {'name': unitTitle, 'value': units}
    march_args = {'name': 'March Size', 'value': march_size}
    traps_args = {'name': 'Traps', 'value': traps}
    skins_args = {'name': 'Skins', 'value': skins}
    lottery_args = {'name': 'Lottery', 'value': lottery}
    whitespace_args = {'name': '\u200b', 'value': '\u200b'}     # used to make an empty field for alignment

    if globals.eventChannel:
        # if there is an active event, put the event and the user's status in the description field of the embed
        # eventInfo = eventTitle + ' @ ' + eventTime
        descr += f'You are **{status}** for {globals.eventInfo}\n' \
                 f'[Event Message]({globals.eventMessage.jump_url})'
    else:
        descr += 'There is no event open for signups.'
    embed = discord.Embed(title='Database Info', description=descr, color=discord.Color.dark_red())

    # add fields to the embed for various entry parameters
    # there are a maximum of 3 fields in a row, stretched to fill a fixed width. Add whitespace fields for alignment
    # row 1: Class, Level, Unit(s)
    embed.add_field(**class_args)
    embed.add_field(**level_args)
    embed.add_field(**unit_args)

    # row 2: MarchSize, Trap(s), Skin(s), lottery
    embed.add_field(**march_args)
    count = 0
    for argDict in [traps_args, skins_args]:
        if argDict['value']:    # if traps, skins is not empty
            embed.add_field(**argDict)
            count += 1

    # lottery
    embed.add_field(**lottery_args)

    # add whitespace fields to align with first row, if 2nd row only contains MarchSize & lottery
    if count == 0:
        embed.add_field(**whitespace_args)

    # set thumbnail image
    if globals.logoURL:
        embed.set_thumbnail(url=globals.logoURL)

    # DM command information
    _ = globals.commandPrefix
    embed.set_footer(text=f"{_}prof to edit profession  |  {_}prof ? to show profession  |  "
                          f"{_}lottery to toggle lottery participation")

    # return file, embed
    return embed


async def update_profession(discord_id: discord.Member.id, prof_array: list) -> None:
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message
    Should only be called if prof_array is not None
    """

    sql = "UPDATE USERS SET CLASS = ?, LEVEL = ?, UNIT = ?, MARCH_SIZE = ?, " \
          "MM_TRAPS = ?, SKINS = ? WHERE DISCORD_ID = ?"
    values = [*prof_array, discord_id]
    # globals.sqlEntries.append([sql, values])

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


async def update_lotto(discord_id: discord.Member.id, lotto: int) -> None:
    sql = "UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?"
    values = [lotto, discord_id]
    # conn.execute(sql, entry)
    # globals.sqlEntries.append([sql, values])

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


async def update_status(discord_id: discord.Member.id, status: str) -> None:
    """
    Called by on_raw_reaction_add() to update status when a member reacts to the event embed
    """
    # shouldn't need to check on event status as they can only update if there is an active event. But do it anyways
    if globals.eventMessage is None:
        return

    sql = "UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?"
    values = [status, discord_id]
    # globals.sqlEntries.append([sql, entry])

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


# this one can just run immediately rather than go into write-loop
async def reset_status() -> None:
    sql = "UPDATE USERS SET STATUS = ?"
    val = ["NO"]
    # globals.sqlEntries = []
    # with sql3.connect('userHistory.db') as conn:
    #     conn.execute(sql, [val])
    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, [val])
            await conn.commit()


async def all_attending_of_category(category: str, value: Union[str, int], display_name=True) -> Optional[list[tuple]]:
    """
    return a list of all user tuples that satisfy a condition
    """

    # conn = sql3.connect('userHistory.db')

    # all (ID, prof) of class
    if category == "class":
        sql = "SELECT DISCORD_ID, CLASS, LEVEL, UNIT, MARCH_SIZE, MM_TRAPS, SKINS " \
              "FROM USERS WHERE STATUS = ? AND CLASS = ?"
        values = ['YES', value]
        # users = conn.execute(sql, ['YES', value])

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = ? AND LOTTERY = ?"
        values = ['YES', value]
        # users = conn.execute(sql, ['YES', value])

    # just used for checking maybes. Could be used for repopulating embed name fields if bot restarts.
    elif category == 'status':
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = ?"
        values = [value]
        # users = conn.execute(sql, [value])

    else:
        logger.error(f"CATEGORY: {category} NOT RECOGNIZED")
        return

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, *values)
            entries = await cursor.fetchall()

    # entries = list(entries)

    if display_name:
        entries = [(globals.guild.get_member(entry[0]).display_name, *entry[1:]) for entry in entries]

    # if display_name:
    #     # convert discord ID to display names
    #     # I tested and this is slightly faster than using a map
    #     newUsers = []
    #     for entry in entries:
    #         newUsers.append((globals.guild.get_member(entry[0]).display_name, *entry[1:]))
    #     users = newUsers

    return entries    # list of user tuples


async def dump_db(filename: str) -> discord.File:
    with open(filename, 'w') as file:
        # with sql3.connect('userHistory.db') as conn:
        async with aiosqlite.connect('userHistory.db') as conn:
            async for line in conn.iterdump():
                file.write(line + '\n')

    return discord.File(filename)
