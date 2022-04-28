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
# this is only on the bot's end. You must ensure that the bot has permissions and access to these channels in the server
# it is recommended but not required to ONLY add the bot to the channels that it is intended to be active in
mainChannelIDs = [964654664677212220]  # svsBotTestServer/botchannel

# prefix that indicates a command (e.g. $prof, $create_event [args])
commandPrefix = '$'

# name of the role that allows usage of event-related commands in the mainChannel
adminRole = 'evan'

# url to the logo to use for embeds. Must be a literal-string (r'URL'). Set this to '', "", or None to not send a
# thumbnail with the embeds
logoURL = r'https://raw.githubusercontent.com/evanm1455/svsInvitationBot/master/logo.png'

# name of the csv file that is made by $finalize_event()
csvFileName = r'svs_attendees.csv'

# number of people to select as lottery winners. This should be higher than the intended number of winners, to account
# for no-shows or other cases in which a randomly selected winner should not actually be given a prize.
numberOfLottoWinners = 40
