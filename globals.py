bot = None
guild = None
mainChannels = []

eventInfo = ''
# eventMessageID = 0
eventMessage = None
eventChannel = None

sqlEntries = []     # exhausted in db.sql_write() loop

#
#
#
# ---------------- BEGIN user-specific variables ----------------

# ID of the guild the bot is to operate in
guildID = 964624340295499857    # svsBotTestServer

# IDs of all guild channels that the bot is allowed to create events and listen for commands in
mainChannelIDs = [964654664677212220]  # svsBotTestServer/botchannel

# prefix that indicates a command (e.g. $prof, $create_event [args])
commandPrefix = '$'

# name of the role that allows usage of event-related commands in the mainChannel
adminRole = 'evan'

# url to the logo to use for embeds. Must be a literal-string (r'URL'). Set this to '', "", or None to not send a
# thumbnail with the embeds
logoURL = r'https://raw.githubusercontent.com/evanm1455/svsInvitationBot/master/transparent_logo.png'
