# stores bot object and guild information
bot = None
guild = None
mainChannels = []

# stores event information
eventInfo = ''
eventMessage = None
eventChannel = None

# needed for sending bug reports to my private server
bugReportChannel = None
bugReportChannelID = 970947508903759902
#
#
#
# ---------------- BEGIN user-specific variables ----------------

# ID of the guild the bot is to operate in
# guildID = 964624340295499857    # svsBotTestServer
guildID = 865787393529085993      # Dragon Babs

# IDs of all guild channels that the bot is allowed to create events and listen for commands in
# this is only on the bot's end. You must ensure that the bot has permissions and access to these channels in the server
# it is recommended but not required to ONLY add the bot to the channels in this array, to reduce overhead
# mainChannelIDs = [964654664677212220]  # svsBotTestServer/botchannel
mainChannelIDs = [971054349822332948]   # Dragon Babs/bot-testing

# name of the role that allows usage of event-related commands in the mainChannel
adminRole = 'Admin (Yes, be scared)'
# adminRole = 'evan'

# prefix that indicates a command (e.g. $info, $create_event [args])
commandPrefix = '~'

# url to the logo to use for embeds. Must be a literal-string (r'URL'). Set this to '', "", or None to not send a
# thumbnail with the embeds
logoURL = r'https://raw.githubusercontent.com/evanm1455/svsInvitationBot/master/logo.png'

# name of the csv file that is made by helpers.build_csv()
csvFileName = r'svs_entries.csv'

# number of people to select as lottery winners. This should be higher than the intended number of winners, to account
# for no-shows or other cases in which a randomly selected winner should not actually be given a prize.
# numberOfLottoWinners = 40
numberOfLottoWinners = 10

# how many hours before the scheduled event time should "Maybe's" be reminded of the event
confirmMaybeWarningTimeHours = 24

# Toggle whether help embeds should be sent to the same channel as $help calls, or to the user's DM
send_help_to_dm = True

# Toggle whether error embeds should be sent to the same channel as command calls, or to the user's DM
send_error_to_dm = True
