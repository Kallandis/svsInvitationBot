import discord
from typing import Union, Optional
import aiosqlite

import logging

from . import globals


async def add_entry(values: Union[list, tuple]) -> None:
    """
    param [list] entry: INT, STRING, INT, STRING, STRING, STRING, STRING, STRING, INT
    Status defaults to 0
    Lottery defaults to 1
    Profession must be provided by User via calls of ProfessionMenuView()
    """
    sql = "INSERT INTO USERS (discord_ID, class, level, unit, march_size, alliance, mm_traps, skins, status, lottery) "\
          "values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
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
    async with aiosqlite.connect('eventInfo.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql)
            entry = await cursor.fetchone()

    return entry


def profession_dicts() -> tuple:
    # return a tuple of dictionaries to be used for formatting database info into human-readable text
    unitDict = {'A': 'Army', 'F': 'Air Force', 'N': 'Navy'}
    ceLevelDict = {0: "2", 1: "3", 2: "3X", 3: "3XE"}
    mmLevelDict = {0: "0T", 1: "3T", 2: "5T", 3: "10", 4: "E"}
    mmTrapsDict = {'Corrosive Mucus': 'CM', 'Supermagnetic Field': 'SF', 'Electro Missiles': 'EM', '': ''}

    return unitDict, ceLevelDict, mmLevelDict, mmTrapsDict


def info_embed(entry: Union[list, tuple], descr='', first_entry=False) -> discord.Embed:
    # extract values from entry
    clas, level, unit, march_size, alliance, mm_traps, skins, status, lottery = entry[1:]

    # format values for display
    unitDict, ceLevelDict, mmLevelDict, _ = profession_dicts()

    units = [unitDict[char] for char in unit]
    # need to escape the ">" quote char
    march_size = ('\\' + march_size) if '<' in march_size or '>' in march_size else march_size
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
    alliance_args = {'name': 'Alliance', 'value': alliance}
    traps_args = {'name': 'Traps', 'value': traps}
    skins_args = {'name': 'Skins', 'value': skins}
    lottery_args = {'name': 'Lottery', 'value': lottery}
    whitespace_args = {'name': '\u200b', 'value': '\u200b'}     # used to make an empty field for alignment

    if not first_entry:
        if globals.eventChannel:
            # if there is an active event, put the event and the user's status in the description field of the embed
            # eventInfo = eventTitle + ' @ ' + eventTime
            descr += f'You are **{status}** for {globals.eventInfo}\n' \
                     f'[Event Message]({globals.eventMessage.jump_url})'
        else:
            descr += 'There is no event open for signups.'
    else:
        # to avoid confusion, don't tell them their status (which is "NO") if they just tried to sign up
        if globals.eventChannel:
            descr += f'[Event Message]({globals.eventMessage.jump_url})'
        else:
            descr += 'There is no event open for signups.'

    embed = discord.Embed(title='Database Info', description=descr, color=discord.Color.dark_red())

    # add fields to the embed for various entry parameters
    # there are a maximum of 3 fields in a row, stretched to fill a fixed width. Add whitespace fields for alignment
    # row 1: Class, Level, Unit(s)
    embed.add_field(**class_args)
    embed.add_field(**level_args)
    embed.add_field(**unit_args)

    # row 2-3: MarchSize, Alliance, Trap(s), Skin(s), Lottery
    embed.add_field(**march_args)
    embed.add_field(**alliance_args)
    count = 0
    for argDict in [traps_args, skins_args]:
        if argDict['value']:    # if traps or skins is not empty
            embed.add_field(**argDict)
            count += 1

    # lottery
    embed.add_field(**lottery_args)

    # add whitespace fields to align 3rd row with 2nd row, if 3rd row has skins & lottery
    # this happens if the entry has a value for both traps and skins
    if count == 2:
        embed.add_field(**whitespace_args)

    # set thumbnail image
    if globals.LOGO_URL:
        embed.set_thumbnail(url=globals.LOGO_URL)

    # DM command information
    _ = globals.COMMAND_PREFIX
    # embed.set_footer(text=f"{_}info <change/show>   |   {_}lottery   |   {_}help")
    embed.set_footer(text=f"{_}info <change/show>,   {_}lottery,   {_}help")
    embed.timestamp = discord.utils.utcnow()

    # return file, embed
    return embed


async def update_profession(discord_id: discord.Member.id, prof_array: list) -> None:
    """
    updates an existing database entry indexed by "discord_id" to new profession data
    """

    sql = "UPDATE USERS SET CLASS = ?, LEVEL = ?, UNIT = ?, MARCH_SIZE = ?, ALLIANCE = ?, " \
          "MM_TRAPS = ?, SKINS = ? WHERE DISCORD_ID = ?"
    values = [*prof_array, discord_id]

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


async def update_lotto(discord_id: discord.Member.id, lotto: int) -> None:
    sql = "UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?"
    values = [lotto, discord_id]

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
        logging.error('update_status called when globals.eventMessage was \'None\'')
        return

    sql = "UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?"
    values = [status, discord_id]

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            await conn.commit()


# this one can just run immediately rather than go into write-loop
async def reset_status() -> None:
    sql = "UPDATE USERS SET STATUS = ?"
    val = ["NO"]

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, val)
            await conn.commit()


async def all_of_category(category: str, value: Union[str, int], guild=None, status='YES',
                          display_name=False) -> Optional[list[tuple]]:
    """
    return a list of all user tuples that satisfy a condition
    """
    # all (ID, prof) of class
    if category == "class":
        sql = "SELECT DISCORD_ID, CLASS, LEVEL, UNIT, MARCH_SIZE, ALLIANCE, MM_TRAPS, SKINS " \
              "FROM USERS WHERE "
        if status in ['YES', 'MAYBE', 'NO']:
            sql += "STATUS = ? AND CLASS = ?"
            values = [status, value]
        elif status == '*':
            sql += "CLASS = ?"
            values = [value]
        else:
            logging.info(f'ERROR: status "{status}" not recognized.')
            return

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = ? AND LOTTERY = ?"
        values = [status, value]

    # just used for checking maybes. Could be used for repopulating embed name fields if bot restarts.
    elif category == 'status':
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = ?"
        values = [value]

    else:
        logging.info(f'ERROR: category "{category}" not recognized.')
        return

    async with aiosqlite.connect('userHistory.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, values)
            entries = await cursor.fetchall()

    def strip_emoji(name):
        # encode into ascii, ignoring unknown chars, then decode back into ascii
        try:
            byteName = name.encode('ascii', 'ignore')
            name = byteName.decode('ascii').strip()
            if name == '':
                # if the user's name is entirely non-ascii characters, it will become an empty string
                name = 'ERROR_NAME'
        except UnicodeEncodeError:
            # if the user's name cannot be encoded into ascii
            name = 'ERROR_ENCODE'

        return name

    def display_name_entries(entries):
        new_entries = []
        for entry in entries:

            # Get the member object from main 1508 guild to get their display name
            # Filter by globals.CSV_ROLE_NAME
            member = guild.get_member(entry[0])
            if member is None:
                continue

            if globals.CSV_ROLE_NAME not in [r.name for r in member.roles]:
                # only add names to the list if they have the designated role
                continue

            member_name = member.display_name if member is not None else 'NOT_FOUND'
            # make a new entry with the member's display name, stripped of emojis
            new_entry = (
                strip_emoji(member_name),
                *entry[1:]
            )
            # add the modified entry with display_name to display_name_entries
            new_entries.append(new_entry)

        return new_entries

    if display_name:
        if not guild:
            logging.error('Failed to provide guild object for display names.')
        return display_name_entries(entries)

    else:
        return entries


async def dump_db(filename: str) -> discord.File:
    with open(filename, 'w') as file:
        # with sql3.connect('userHistory.db') as conn:
        async with aiosqlite.connect('userHistory.db') as conn:
            async for line in conn.iterdump():
                file.write(line + '\n')

    return discord.File(filename)
