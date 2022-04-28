import globals
import discord
from discord.ext.tasks import loop
import sqlite3 as sql3
from typing import Union, Optional

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


def add_entry(values: Union[list, tuple]) -> None:
    """
    param [list] entry: INT, STRING, STRING, INT, STRING, STRING, STRING, INT
    Status defaults to 0
    Lottery defaults to 1
    Profession must be provided by User via calls of ProfessionMenuView()
    """
    sql = "INSERT INTO USERS (discord_ID, class, unit, level, mm_traps, skins, status, lottery) " \
          "values(?, ?, ?, ?, ?, ?, ?, ?)"
    globals.sqlEntries.append([sql, values])


def get_entry(discord_id: int) -> Optional[tuple]:
    """
    Returns entry (list) associated with unique discord ID. If no entry exists, returns None
    """
    sql = "SELECT * FROM USERS WHERE DISCORD_ID = ?"
    values = [discord_id]
    with sql3.connect('userHistory.db') as conn:
        entry = list(conn.execute(sql, values))

    if not entry:
        return None
    else:
        return entry[0]


def update_event(title: str, time: str, message_id: discord.Message.id, channel_id: discord.TextChannel.id) -> None:
    sql = "UPDATE EVENT SET TITLE = ?, TIME = ?, MESSAGE_ID = ?, CHANNEL_ID = ?"
    values = [title, time, message_id, channel_id]
    with sql3.connect('eventInfo.db') as conn:
        conn.execute(sql, values)


def get_event() -> tuple[str, str, int, int]:
    sql = "SELECT * FROM EVENT"
    with sql3.connect('eventInfo.db') as conn:
        eventTitle, eventTime, message_id, channel_id = list(conn.execute(sql))[0]
    return eventTitle, eventTime, message_id, channel_id


def profession_dicts() -> tuple:
    # return a tuple of dictionaries to be used for formatting database info into human-readable text
    unitDict = {'A': 'Army', 'F': 'Air Force', 'N': 'Navy'}
    ceLevelDict = {0: "2", 1: "3", 2: "3X", 3: "3XE"}
    mmLevelDict = {0: "0T", 1: "3T", 2: "5T", 3: "10", 4: "E"}
    mmTrapsDict = {'Corrosive Mucus': 'CM', 'Supermagnetic Field': 'SF', 'Electro Missiles': 'EM'}

    return unitDict, ceLevelDict, mmLevelDict, mmTrapsDict


def info_embed(entry: Union[list, tuple], descr='') -> discord.Embed:
    # extract values from entry
    clas, unit, level, mm_traps, skins, status, lottery = entry[1:]

    # format values for display
    unitDict, ceLevelDict, mmLevelDict, _ = profession_dicts()

    units = [unitDict[char] for char in unit]
    level = ceLevelDict[level] if clas == 'CE' else mmLevelDict[level]
    traps = mm_traps.split(', ')
    skins = skins.split(', ')
    lottery = 'YES' if lottery == 1 else 'NO'

    # fields accept a string, so build a '\n'-separated string from lists
    units = '\n'.join(units)
    traps = '\n'.join(traps)
    skins = '\n'.join(skins)

    unitTitle = 'Unit' if '\n' not in units else 'Units'
    trapsTitle = 'Trap' if '\n' not in traps else 'Traps'
    skinsTitle = 'Skin' if '\n' not in skins else 'Skins'

    # initialize arg dictionaries to be used in field creation
    class_args = {'name': 'Class', 'value': clas}
    unit_args = {'name': unitTitle, 'value': units}
    level_args = {'name': 'Level', 'value': level}
    traps_args = {'name': trapsTitle, 'value': traps}
    skins_args = {'name': skinsTitle, 'value': skins}
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
    # row 1: Class, Unit(s), Level
    embed.add_field(**class_args)
    embed.add_field(**unit_args)
    embed.add_field(**level_args)

    # row 2: Trap(s), Skin(s), lottery
    count = 0
    for argDict in [traps_args, skins_args]:
        if argDict['value']:
            embed.add_field(**argDict)
            count += 1

    # lottery
    embed.add_field(**lottery_args)

    # add whitespace fields to align with first row
    if count > 0:
        for i in range(2 - count):
            embed.add_field(**whitespace_args)

    # # row 3: Lottery
    # embed.add_field(**lottery_args)

    # set thumbnail image
    if globals.logoURL:
        embed.set_thumbnail(url=globals.logoURL)

    # DM command information
    _ = globals.commandPrefix
    embed.set_footer(text=f"{_}prof to edit profession  |  {_}prof ? to show profession  |  "
                          f"{_}lottery to toggle lottery participation")

    # return file, embed
    return embed


def update_profession(discord_id: discord.Member.id, prof_array: list) -> None:
    """
    param [str] prof: one of ~10 Profession designations ( MM1/2/3 , CE3/X/N - A/F/N , CEM )
    formatting instructions to be given in private message
    Should only be called if prof_array is not None
    """

    sql = "UPDATE USERS SET CLASS = ?, UNIT = ?, LEVEL = ?, MM_TRAPS = ?, SKINS = ? WHERE DISCORD_ID = ?"
    values = [*prof_array, discord_id]
    globals.sqlEntries.append([sql, values])


def update_lotto(discord_id: discord.Member.id, lotto: int) -> None:
    sql = "UPDATE USERS SET LOTTERY = ? WHERE DISCORD_ID = ?"
    entry = [lotto, discord_id]
    # conn.execute(sql, entry)
    globals.sqlEntries.append([sql, entry])


def update_status(discord_id: discord.Member.id, status: str) -> None:
    """
    Called by on_raw_reaction_add() to update status when a member reacts to the event embed
    """
    eventTitle, eventTime, message_id, channel_id = get_event()
    if not message_id:
        return

    sql = "UPDATE USERS SET STATUS = ? WHERE DISCORD_ID = ?"
    entry = [status, discord_id]
    globals.sqlEntries.append([sql, entry])


# TODO
async def confirm_maybe(member: discord.Member):
    """
    When it is X hours before the event, remind "MAYBE" users that they are registered as Maybe.
    """

    # make this an embed and include a link to the event message.
    content = f'This is a reminder that you are registered as **MAYBE** for {globals.eventInfo}\n' \
              f'If you would like to change your status, go to {globals.eventChannel.name}.'
    pass


# this one can just run immediately rather than go into write-loop
def reset_status() -> None:
    sql = "UPDATE USERS SET STATUS = ?"
    val = "NO"
    globals.sqlEntries = []
    with sql3.connect('userHistory.db') as conn:
        conn.execute(sql, [val])


def all_attending_of_category(category: str, value: Union[str, int], display_name=True) -> Optional[list[tuple]]:
    """
    return a list of all user tuples that satisfy a condition
    """

    conn = sql3.connect('userHistory.db')

    # all (ID, prof) of class
    if category == "class":
        sql = "SELECT DISCORD_ID, CLASS, UNIT, LEVEL, MM_TRAPS, SKINS FROM USERS WHERE STATUS = ? AND CLASS = ?"
        users = conn.execute(sql, ['YES', value])

    # all ID attending event who have opted in to lotto
    elif category == "lotto":
        sql = "SELECT DISCORD_ID FROM USERS WHERE STATUS = ? AND LOTTERY = ?"
        users = conn.execute(sql, ['YES', value])

    else:
        conn.close()
        return None

    users = list(users)
    conn.close()

    if display_name:
        # convert discord ID to display names
        # I tested and this is slightly faster than using a map
        newUsers = []
        for entry in users:
            newUsers.append((globals.guild.get_member(entry[0]).display_name, *entry[1:]))
        users = newUsers

    return users    # list of user tuples


def dump_db(filename: str) -> discord.File:
    with open(filename, 'w') as file:
        with sql3.connect('userHistory.db') as conn:
            for line in conn.iterdump():
                file.write(line + '\n')

    return discord.File(filename)
