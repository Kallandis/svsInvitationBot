import discord
import db

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ProfessionMenu(discord.ui.Select):

    __slots__ = ('parent_message', 'category', 'clas', 'units', 'level', 'mm_traps', 'first_entry')

    def __init__(self, parent_message, category, clas=None, units=None, level=None, mm_traps=None, first_entry=None):
        self.parent_message = parent_message
        self.category = category
        self.clas = clas
        self.units = units
        self.level = level
        self.mm_traps = mm_traps
        self.first_entry = first_entry
        max_vals = 1

        # Set the options that will be presented inside the dropdown
        if category == "class":
            options = [
                discord.SelectOption(label='MM'),
                discord.SelectOption(label='CE'),
                discord.SelectOption(label='CANCEL', description='Pick this to cancel updating profession')
            ]
            placeholder = f'Select your class'

        elif category == "unit":
            options = [
                discord.SelectOption(label='Army'),
                discord.SelectOption(label='Air Force'),
                discord.SelectOption(label='Navy')
            ]
            max_vals = 3
            placeholder = f'Main unit & others w/ mostly purple, >= 8 perks'

        elif category == "level":
            if self.clas == 'MM':
                options = [
                    discord.SelectOption(label='0T', description='Less than level 3 Weakening Towers'),
                    discord.SelectOption(label='3T', description='Level 3 Weakening Towers'),
                    discord.SelectOption(label='5T', description='Level 4-5 Weakening Towers'),
                    discord.SelectOption(label='10', description='+10 march size'),
                    discord.SelectOption(label='E',  description='Encirclement')
                ]
            elif self.clas == 'CE':
                options = [
                    discord.SelectOption(label='2',   description='Not three hero yet'),
                    discord.SelectOption(label='3',   description='Three hero march'),
                    discord.SelectOption(label='3X',  description='Extra skill slot'),
                    discord.SelectOption(label='3XE', description='Encirclement')
                ]
            else:
                print(f"ERROR: Dropdown optional parameter 'clas': {self.clas} invalid")
                return
            placeholder = f'Select {self.clas} progress (Highest that applies)'

        elif category == "mm_traps":
            options = [
                discord.SelectOption(label='None'),
                discord.SelectOption(label='Corrosive Mucus'),
                discord.SelectOption(label='Supermagnetic Field'),
                discord.SelectOption(label='Electro Missiles')
            ]
            max_vals = 3
            placeholder = f'Select which traps you can build'

        elif category == "skins":
            options = [
                discord.SelectOption(label='None'),
                discord.SelectOption(label='Atlantis'),
                discord.SelectOption(label='Ark')
            ]
            max_vals = 2
            placeholder = f'Select which base skins you own'

        else:
            print("ERROR: Dropdown required parameter 'category' either empty or invalid")
            return

        super().__init__(placeholder=placeholder, min_values=1, max_values=max_vals, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options.

        choice = ', '.join(self.values)
        if choice == 'CANCEL':
            # does this need to interact with invoking fxn update_profession()?
            await interaction.response.edit_message(content='Cancelled updating profession', view=None)
            return

        if self.category == "class":
            self.clas = choice
            nextCategory = "unit"
        elif self.category == "unit":
            self.units = choice
            nextCategory = "level"
        elif self.category == "level":
            self.level = choice
            nextCategory = "mm_traps" if self.clas == "MM" else "skins"
        elif self.category == "mm_traps":
            self.mm_traps = choice
            nextCategory = "skins"
        else:   # self.category == "skins"
            nextCategory = None

        if nextCategory is not None:
            # edit the interaction message with a new ProfessionMenuView view for the next category
            # this cycles until nextCategory is None (when category is "skins")
            await interaction.response.edit_message(
                content=f'You chose: {choice}',
                view=ProfessionMenuView(
                    self.parent_message, nextCategory,
                    clas=self.clas, units=self.units, level=self.level, mm_traps=self.mm_traps,
                    first_entry=self.first_entry
                )
            )
        else:   # the current category is "skins"
            # Remove the selectmenu, tell user what they selected, write the info to DB

            skins = ', '.join(self.values)

            # parse selection info into appropriate form for DB-submission
            # unit(s)
            unitCharDict = {'Army': 'A', 'Air Force': 'F', 'Navy': 'N'}
            unitChars = [unitCharDict[unit] for unit in self.units.split(', ')]

            # level
            ceLevelDict = {"2": 0, "3": 1, "3X": 2, "3XE": 3}
            mmLevelDict = {"0T": 0, "3T": 1, "5T": 2, "10": 3, "E": 4}
            levelNum = ceLevelDict[self.level] if self.clas == 'CE' else mmLevelDict[self.level]

            # mm_traps
            if self.mm_traps is None or 'None' in self.mm_traps:
                # if user selected "None" in the MenuView, set mm_traps to ''
                self.mm_traps = ''

            # skin(s)
            if 'None' in skins:
                # if user selected "None" in the MenuView, set skins to ''
                skins = ''

            prof_array = [self.clas, ''.join(unitChars), levelNum, self.mm_traps, skins]

            # if first-time user does not have an entry in DB, add one (happens when called through dm.request_entry())
            if self.first_entry:
                # set status to "NO", lottery to 1 (default vals)
                entry = [interaction.user.id, *prof_array, "NO", 1]

                db.add_entry(entry)
                embed = db.info_embed(entry, descr='You have been added to the database.\n')

            # else just update the user's profession
            else:
                # need to get old DB entry to send to db.info_embed()
                old_entry = db.get_entry(interaction.user.id)
                status, lottery = old_entry[-2:]
                new_entry = [interaction.user.id, *prof_array, status, lottery]

                embed = db.info_embed(new_entry, descr='Successfully edited profession.\n')
                db.update_profession(interaction.user.id, prof_array)

            # send user's selection as an info-embed, remove the view
            await interaction.response.edit_message(content='', embed=embed, view=None)


class ProfessionMenuView(discord.ui.View):

    __slots__ = ('parent_message', 'category', 'clas', 'units', 'level', 'mm_traps', 'first_entry')

    def __init__(self, parent_message, category, clas=None, units=None, level=None, mm_traps=None, first_entry=None):
        super().__init__(timeout=300)
        self.parent_message = parent_message
        self.first_entry = first_entry

        # Adds the dropdown to our view object.
        self.add_item(ProfessionMenu(parent_message, category, clas=clas, units=units, level=level, mm_traps=mm_traps,
                                     first_entry=first_entry))

    async def on_timeout(self):
        dm_channel = self.parent_message.channel
        ID = self.parent_message.id
        parent_message = await dm_channel.fetch_message(ID)

        # check that the parent message has an embed, indicating that the user successfully completed selection.
        # If not, timeout the message.
        if not parent_message.embeds:
            await self.parent_message.edit(content='Profession menu timed out.', view=None)
