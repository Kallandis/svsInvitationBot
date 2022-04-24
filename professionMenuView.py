import discord
import db


class ProfessionMenu(discord.ui.Select):
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
                discord.SelectOption(label='CANCEL', description='Pick this to cancel changing profession')
            ]
            placeholder = f'Choose your {category}'

        elif category == "unit":
            options = [
                discord.SelectOption(label='Army'),
                discord.SelectOption(label='Air Force'),
                discord.SelectOption(label='Navy')
            ]
            max_vals = 3
            placeholder = f'Choose your {category}(s)'

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
            placeholder = f'Choose your progress in the {self.clas} class tree (Pick highest that applies)'

        elif category == "mm_traps":
            options = [
                discord.SelectOption(label='None'),
                discord.SelectOption(label='Corrosive Mucus'),
                discord.SelectOption(label='Supermagnetic Field'),
                discord.SelectOption(label='Electro Missiles')
            ]
            max_vals = 3
            placeholder = f'Which of these traps can you build'

        elif category == "skins":
            options = [
                discord.SelectOption(label='None'),
                discord.SelectOption(label='Atlantis'),
                discord.SelectOption(label='Ark')
            ]
            max_vals = 2
            placeholder = f'Which of these base skins do you have'

        else:
            print("ERROR: Dropdown required parameter 'category' either empty or invalid")
            return

        if max_vals > 1:
            placeholder += f' (PICK UP TO {max_vals})'

        placeholder += '...'
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
            nextCategory = "mm_trap" if self.clas == "MM" else "skins"
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

            formattedProfString = f'**CLASS**: {self.clas}, **UNIT(s)**: {self.units}, **LEVEL**: {self.level}'

            skins = self.values
            # parse selection info into appropriate form for DB-submission
            # unit(s)
            unitCharDict = {'Army': 'A', 'Air Force': 'F', 'Navy': 'N'}
            unitChars = [unitCharDict[unit] for unit in self.units.split(', ')]

            # level
            ceLevelDict = {"2": 0, "3": 1, "3X": 2, "3XE": 3}
            mmLevelDict = {"0T": 0, "3T": 1, "5T": 2, "10": 3, "E": 4}
            levelNum = ceLevelDict[self.level] if self.clas == 'CE' else mmLevelDict[self.level]

            # mm_traps
            if 'None' in self.mm_traps.split(', ') or self.mm_traps is None:
                self.mm_traps = ''
            else:
                formattedProfString += f', **TRAP(s)**: {self.mm_traps}'

            # skin(s)
            if 'None' in skins:
                skins = ''
            else:
                skins = ', '.join(skins)
                formattedProfString += f', **SKIN(s)**: {skins}'

            prof_array = [self.clas, ''.join(unitChars), levelNum, self.mm_traps, skins]

            # if first-time user does not have an entry in DB (when called through dm.request_entry())
            if self.first_entry:
                values = [interaction.user.id, *prof_array, "NO", 1]
                db.add_entry(values)
                msg = 'You are now registered in the database with profession:\n'

            # else just update the profession
            else:
                db.update_profession(interaction.user.id, prof_array)
                msg = 'Your profession has been updated to:\n'

            # send user's selection, remove the view
            msg += formattedProfString
            await interaction.response.edit_message(content=msg, view=None)


class ProfessionMenuView(discord.ui.View):
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
        current_content = parent_message.content

        # Check that the message has been edited to the selection completion strings, indicating that the user
        # successfully completed selection. If not, timeout the message.
        if not (current_content.startswith('You are') or current_content.startswith('Your profession')):
            await self.parent_message.edit(content='Profession menu timed out.', view=None)
