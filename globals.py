bot = None
mainChannel = None
guild = None
sqlEntries = []     # exhausted in db.sql_write() loop
eventInfo = ''
eventMessageID = 0
eventChannel = None

#
#
#
# ---------------- BEGIN user-specific variables ----------------

# ID of the guild the bot is to operate in
guildID = 964624340295499857    # svsBotTestServer

# IDs of all guild channels that the bot is allowed to create events and interpret messages in
mainChannelIDs = [964654664677212220]  # svsBotTestServer/botchannel

# name of the role that allows usage of event-related commands in the mainChannel
adminRole = 'evan'

# path to the locally-stored logo picture. Must be a literal-string (r'PATH'). set this to '' or "" to not send
# a thumbnail with the info-embeds sent in DMs
logoPath = r'C:\Users\evanm\Desktop\Coding\discord_bots\invitationBot\transparent_logo.png'
