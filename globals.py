bot = None
mainChannel = None
guild = None
sqlEntries = []   # insert, update

# need this because message.remove_reaction() triggers on_raw_reaction_remove(), sending an extra ACK.. disgusting
triggeredFromBotRemove = False

#
# BEGIN user-specific variables

# ID of the guild the bot is to operate in
guildID = 964624340295499857    # svsBotTestServer

# ID of the channel that the bot is to use for event-management
mainChannelID = 964654664677212220  # svsBotTestServer/botchannel

# name of the role that allows usage of event-related commands in the mainChannel
adminRole = 'evan'

# path to the locally-stored logo picture. Must be a literal-string (r'PATH'). set this to None or '' to not send pic
logoPath = r'C:\Users\evanm\Desktop\Coding\discord_bots\invitationBot\logo.png'
