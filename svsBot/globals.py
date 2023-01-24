mainChannels = None   # can't figure out how to access this from My_Help() without making it a global

# stores event information - these are pretty hard to get rid of as they are referenced far away from the bot.
eventInfo = ''
eventMessage = None
eventChannel = None

# only used to remove my private server from the bot's bot.guilds attr
EVAN_GUILD_ID = 964624340295499857    # svsBotTestServer

logfile = None

#
#
# ---------------- BEGIN user-specific variables ----------------

# central guild "1508". All other guilds are subsets of this guild; it will be used for pulling member's
# display_name attribute for making the CSV. 
GUILD_ID_1508 = 915761804704104489

# IDs of all guild channels that the bot is allowed to create events and listen for commands in
# this is only on the bot's end. You must ensure that the bot has permissions and access to these channels in the server
# it is recommended but not required to ONLY add the bot to the channels in this array, to reduce overhead
#MAIN_CHANNEL_ID_LIST = [964654664677212220]  # svsBotTestServer/botchannel
MAIN_CHANNEL_ID_LIST = [
        937275649536692294,
        951396183610388491
        ]
    # 1508/svs-registration
    # 1508/el-registration

# name of the role that allows usage of event-related commands in the mainChannels
# if the bot is to work in multiple servers, all servers must have a role with this name
#ADMIN_ROLE_NAME = 'evan'
ADMIN_ROLE_NAME = 'SVS Planner'

# Only add people to CSV if they have this role
CSV_ROLE_NAME = '1508+'

# prefix that indicates a command (e.g. $info, $create_event [args])
COMMAND_PREFIX = '~'
#COMMAND_PREFIX = '!'


# url to the logo to use for embeds. Must be a literal-string (r'URL'). 
# Set this to '', "", or None to not send a thumbnail with the embeds
LOGO_URL = r'https://raw.githubusercontent.com/evanm1455/svsInvitationBot/master/logo1.png'

# name of the csv file containing attendee information
CSV_FILENAME = r'svs_entries.csv'

# name of the csv file containing users that interacted with event
YMN_CSV_FILENAME = r'ymn.csv'

# number of people to select as lottery winners. This should be higher than the intended number of winners, to account
# for no-shows or other cases in which a randomly selected winner should not actually be given a prize.
NUMBER_OF_LOTTO_WINNERS = 40

# how many hours before the scheduled event time should "Maybe's" be reminded of the event
CONFIRM_MAYBE_WARNING_HOURS = 40

# Names longer than this in the event embed will be truncated.
# Maximum of 23
MAX_NAME_LENGTH_IN_EMBED_FIELD = 8

# Toggle whether help embeds should be sent to the same channel as $help calls, or to the user's DM
SEND_HELP_TO_DM = True

# Toggle whether error embeds should be sent to the same channel as command calls, or to the user's DM
SEND_ERROR_TO_DM = True

# Toggle whether bot should delete all commands sent in mainchannels
# Turned off because it requires 2FA on bot owner's account, which I don't want
# but if it's a big deal I'm ok with turning 2FA on
DELETE_MESSAGES = False

# Channel that $bug should send bug reports to
BUG_REPORT_CHANNEL_ID = 970947508903759902  # svsBotTestServer/bug-reports (Evan's private server)

# Channel that backups of the database should be sent to when "~close" is called
DB_BACKUP_CHANNEL_ID = 972960827479031848   # svsBotTestServer/db-backups
