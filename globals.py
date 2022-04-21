bot = None
mainChannel = None
guild = None
sqlEntries = []   # insert, update
adminRole = 'evan'
triggeredFromBotRemove = False  # I need this because message.remove_reaction() triggers on_raw_reaction_remove(), sending an extra ACK
