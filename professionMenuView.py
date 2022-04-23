import discord
import db


class ProfessionMenu(discord.ui.Select):
    def __init__(self, parent_message, category, clas=None, units=None, level=None, first_entry=None):
        self.parent_message = parent_message
        self.category = category
        self.clas = clas
        self.units = units
        self.first_entry = first_entry
        self.level = level
        max_vals = 1

        # Set the options that will be presented inside the dropdown
        if category == "class":
            options = [
                discord.SelectOption(label='MM'),
                discord.SelectOption(label='CE'),
                discord.SelectOption(label='CANCEL', description='Pick this to cancel changing profession')
            ]

        elif category == "unit":
            options = [
                discord.SelectOption(label='Army'),
                discord.SelectOption(label='Air Force'),
                discord.SelectOption(label='Navy')
            ]
            max_vals = 3

        elif category == "level":
            if self.clas == 'MM':
                options = [
                    discord.SelectOption(label='0T'),
                    discord.SelectOption(label='3T'),
                    discord.SelectOption(label='5T'),
                    discord.SelectOption(label='10'),
                    discord.SelectOption(label='E')
                ]
            elif self.clas == 'CE':
                options = [
                    discord.SelectOption(label='2'),
                    discord.SelectOption(label='3'),
                    discord.SelectOption(label='3X'),
                    discord.SelectOption(label='3XE')
                ]
            else:
                print(f"ERROR: Dropdown optional parameter 'clas': {self.clas} invalid")
                return

        elif category == "items":
            options = [
                discord.SelectOption(label='None'),
                discord.SelectOption(label='Item1'),
                discord.SelectOption(label='Item2')
            ]
            max_vals = 2

        else:
            print("ERROR: Dropdown required parameter 'category' either empty or invalid")
            return

        placeholder = f'Choose your {category}'
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
            nextCategory = "items"
        else:   # category is items
            nextCategory = None

        if nextCategory is not None:
            # edit the interaction message with a new ProfessionMenuView view for the next category
            await interaction.response.edit_message(
                content=f'You chose: {choice}',
                view=ProfessionMenuView(self.parent_message, nextCategory,
                                        clas=self.clas, units=self.units, level=self.level,
                                        first_entry=self.first_entry)
            )
        else:   # the current category is "item"
            # Remove the selectmenu, tell user what they selected, write the info to DB

            formattedProfString = f'**CLASS:** {self.clas}, **UNIT(s)**: {self.units}, **LEVEL**: {self.level}'
            if 'None' not in self.values:
                items = ', '.join(self.values)
                formattedProfString += f', **ITEM(s):** {items}'

            # parse selection info into appropriate form for DB-submission
            unitCharDict = {'Army': 'A', 'Air Force': 'F', 'Navy': 'N'}
            unitChars = [unitCharDict[unit] for unit in self.units.split(', ')]

            ceLevelDict = {"2": 0, "3": 1, "3X": 2, "3XE": 3}
            mmLevelDict = {"0T": 0, "3T": 1, "5T": 2, "10": 3, "E": 4}
            levelNum = ceLevelDict[self.level] if self.clas == 'CE' else mmLevelDict[self.level]

            prof_array = [self.clas, ''.join(unitChars), levelNum]

            # if first-time user does not have an entry in DB (called through dm.request_entry())
            if self.first_entry:
                values = [interaction.user.id, *prof_array, "NO", 0, 1]
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
    def __init__(self, parent_message, category, clas=None, units=None, level=None, first_entry=None):
        super().__init__(timeout=300)
        self.parent_message = parent_message
        self.first_entry = first_entry

        # Adds the dropdown to our view object.
        self.add_item(ProfessionMenu(parent_message, category, clas=clas, units=units, level=level, first_entry=first_entry))

    async def on_timeout(self):
        dm_channel = self.parent_message.channel
        ID = self.parent_message.id
        parent_message = await dm_channel.fetch_message(ID)
        current_content = parent_message.content

        # Check that the message has been edited to the selection completion strings, indicating that the user
        # successfully completed selection. If not, timeout the message.
        if not (current_content.startswith('You are') or current_content.startswith('Your profession')):
            await self.parent_message.edit(content='Profession menu timed out.', view=None)
