import discord


class Dropdown(discord.ui.Select):
    def __init__(self, category, clas=None, units=None):
        self.category = category
        self.clas = clas
        self.units = units
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

        else:
            print("ERROR: Dropdown required parameter 'category' either empty or invalid")
            return

        placeholder = f'Choose your {category}'
        if category == 'unit':
            placeholder += ' (PICK UP TO 3)'
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
        else:
            nextCategory = None

        if nextCategory is not None:
            # dynamically update content with the total selections so far
            await interaction.response.edit_message(content=f'You chose: {choice}',
                                                    view=DropdownView(nextCategory, clas=self.clas, units=self.units))
        else:
            # Remove the selectmenu
            # Tell the user what they selected
            # Write the selection info to DB
            # Ideally, there should be an asyncio.wait_for on this selectMenu, so that the selectMenu does not stay
            # in the channel forever. Display this timer to the user

            level = self.values[0]  # if nextCategory is None, then self.values returns the "level" choice
            msg = f'You have been registered as ' \
                  f'CLASS: **{self.clas}**, UNIT(s): **{self.units}**, LEVEL: **{level}**'
            await interaction.response.edit_message(content=msg, view=None)

            # move db.parse_profession() parsing to here? Not sure how to pass this info to db.parse_profession()
            # if can move this stuff to db.parse_profession(), would be better to parse it there
            unitCharDict = {'Army': 'A', 'Air Force': 'F', 'Navy': 'N'}
            unitChars = [unitCharDict[unit] for unit in self.units]
            prof_array = [self.clas, ''.join(unitChars), ]
            # TODO: write to DB


class DropdownView(discord.ui.View):
    def __init__(self, category, clas=None, units=None):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(category, clas=clas, units=units))
