# stores bot object and guild information
# bot = None
# guild = None
mainChannels = None   # can't figure out how to access this from My_Help() without making it a global

# stores event information - these are pretty hard to get rid of as they are referenced far away from the bot.
eventInfo = ''
eventMessage = None
eventChannel = None

# confirm maybe loop (asyncio.Task), must be stored so it can be cancelled when event is closed
# maybe_loop = None

# bug reports are sent to a private channel for later review
# bugReportChannel = None


#
#
#
# ---------------- BEGIN user-specific variables ----------------

# only used to remove my private server from the bot's bot.guilds attr
EVAN_GUILD_ID = 964624340295499857    # svsBotTestServer

# IDs of all guild channels that the bot is allowed to create events and listen for commands in
# this is only on the bot's end. You must ensure that the bot has permissions and access to these channels in the server
# it is recommended but not required to ONLY add the bot to the channels in this array, to reduce overhead
MAIN_CHANNEL_ID_LIST = [964654664677212220]  # svsBotTestServer/botchannel
# MAIN_CHANNEL_ID_LIST = [971054349822332948]   # Dragon Babs/bot-testing

# name of the role that allows usage of event-related commands in the mainChannels
# if the bot is to work in multiple servers, all servers must have a role with this name
# adminRole = 'Admin (Yes, be scared)'
ADMIN_ROLE_NAME = 'evan'

# prefix that indicates a command (e.g. $info, $create_event [args])
COMMAND_PREFIX = '~'

# url to the logo to use for embeds. Must be a literal-string (r'URL'). Set this to '', "", or None to not send a
# thumbnail with the embeds
LOGO_URL = r'https://raw.githubusercontent.com/evanm1455/svsInvitationBot/master/logo.png'

# name of the csv file that is made by helpers.build_csv()
CSV_FILENAME = r'svs_entries.csv'

# number of people to select as lottery winners. This should be higher than the intended number of winners, to account
# for no-shows or other cases in which a randomly selected winner should not actually be given a prize.
NUMBER_OF_LOTTO_WINNERS = 40

# how many hours before the scheduled event time should "Maybe's" be reminded of the event
CONFIRM_MAYBE_WARNING_HOURS = 24

# Toggle whether help embeds should be sent to the same channel as $help calls, or to the user's DM
SEND_HELP_TO_DM = True

# Toggle whether error embeds should be sent to the same channel as command calls, or to the user's DM
SEND_ERROR_TO_DM = True

# Channel that $bug should send bug reports to
BUG_REPORT_CHANNEL_ID = 970947508903759902     # svsBotTestServer/bug-reports (Evan's private server)
