import discord

import logging
import json

from . import db
from . import globals


class ProfessionMenu(discord.ui.Select):

    __slots__ = ('parent_message', 'category',
                 'class_', 'level', 'units', 'march_size', 'alliance', 'mm_traps', 'first_entry')

    def __init__(self, parent_message, category,
                 class_=None, level=None, units=None, march_size=None, alliance=None, mm_traps=None, first_entry=None):
        self.parent_message = parent_message
        self.category = category
        self.class_ = class_
        self.level = level
        self.units = units
        self.march_size = march_size
        self.alliance = alliance
        self.mm_traps = mm_traps
        self.first_entry = first_entry

        self.category_title = ''
        self.options_ = []
        self.max_vals = 1

        # Set the options that will be presented inside the dropdown
        self.parse_options_from_json(self.category)
        super().__init__(placeholder=self.category_title, min_values=1, max_values=self.max_vals, options=self.options_)

        # if category == "class":
        #     options = [
        #         discord.SelectOption(label='MM'),
        #         discord.SelectOption(label='CE'),
        #         discord.SelectOption(label='CANCEL', description='Pick this to cancel updating info.')
        #     ]
        #     # placeholder = f'Select your class'
        #     placeholder = 'Class'
        #
        # elif category == "level":
        #     if self.class_ == 'MM':
        #         options = [
        #             discord.SelectOption(label='0T', description='Less than level 3 Weakening Towers'),
        #             discord.SelectOption(label='3T', description='Level 3 Weakening Towers'),
        #             discord.SelectOption(label='5T', description='Level 4-5 Weakening Towers'),
        #             discord.SelectOption(label='10', description='+10 march size'),
        #             discord.SelectOption(label='E',  description='Encirclement')
        #         ]
        #     elif self.class_ == 'CE':
        #         options = [
        #             discord.SelectOption(label='2',   description='Not three hero yet'),
        #             discord.SelectOption(label='3',   description='Three hero march'),
        #             discord.SelectOption(label='3X',  description='Extra skill slot'),
        #             discord.SelectOption(label='3XE', description='Encirclement')
        #         ]
        #     else:
        #         logging.error(f"Dropdown optional parameter 'class_': {self.class_} invalid")
        #         return
        #     placeholder = f'{self.class_} Progress'
        #
        # elif category == "unit":
        #     options = [
        #         discord.SelectOption(label='Army'),
        #         discord.SelectOption(label='Air Force'),
        #         discord.SelectOption(label='Navy')
        #     ]
        #     max_vals = 3
        #     placeholder = 'Unit(s)'
        #
        # elif category == 'march size':
        #     options = [
        #         discord.SelectOption(label='< 160'),
        #         discord.SelectOption(label='160-170'),
        #         discord.SelectOption(label='170-180'),
        #         discord.SelectOption(label='180-190'),
        #         discord.SelectOption(label='190-200'),
        #         discord.SelectOption(label='200-210'),
        #         discord.SelectOption(label='210-220'),
        #         discord.SelectOption(label='> 220')
        #     ]
        #     # placeholder = 'Best base march size (no skin / buffs)'
        #     placeholder = 'March size'
        #
        # elif category == 'alliance':
        #     options = [
        #         discord.SelectOption(label='508S'),
        #         discord.SelectOption(label='508N'),
        #         discord.SelectOption(label='508W'),
        #         discord.SelectOption(label='508E')
        #     ]
        #     # placeholder = 'Select your alliance'
        #     placeholder = 'Alliance'
        #
        # elif category == "mm_traps":
        #     options = [
        #         discord.SelectOption(label='None'),
        #         discord.SelectOption(label='Corrosive Mucus'),
        #         discord.SelectOption(label='Supermagnetic Field'),
        #         discord.SelectOption(label='Electro Missiles')
        #     ]
        #     max_vals = 3
        #     # placeholder = f'Select which traps you can build'
        #     placeholder = 'Trap(s)'
        #
        # elif category == "skins":
        #     options = [
        #         discord.SelectOption(label='None'),
        #         discord.SelectOption(label='Popstar-30d'),
        #         discord.SelectOption(label='Void Matrix'),
        #     ]
        #     max_vals = len(options)
        #     # placeholder = f'Select which base skins you own'
        #     placeholder = 'Skin(s)'
        #
        # else:
        #     logging.error("ERROR: Dropdown required parameter 'category' either empty or invalid")
        #     return

        # super().__init__(placeholder=self.placeholder, min_values=1, max_values=self.max_vals, options=self.options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options.

        choice = ', '.join(self.values)

        if self.category == "class":
            if choice == 'CANCEL':
                await interaction.response.edit_message(content='Cancelled updating info', view=None)
                return
            self.class_ = choice
            nextCategory = "level"
        elif self.category == "level":
            self.level = choice
            nextCategory = 'units'
        elif self.category == "units":
            self.units = choice
            nextCategory = "march_size"
        elif self.category == "march_size":
            self.march_size = choice
            nextCategory = 'alliance'
        elif self.category == 'alliance':
            self.alliance = choice
            nextCategory = "mm_traps" if self.class_ == "MM" else "skins"
        elif self.category == "mm_traps":
            self.mm_traps = choice
            nextCategory = "skins"
        elif self.category == "skins":
            nextCategory = None
        else:  # should never be reached
            nextCategory = 'error'

        # set the prompt that will be shown above the next select menu
        # nextCategoryPromptDict = {
        #     'level': f'Select {self.class_} progress (Highest that applies)',
        #     'unit': 'Select strongest unit type (regardless of equipment/perks). **Only** choose a second (or third) '
        #             'unit type if you have 4 purple equipment **AND** 8 perks on that march.',
        #     'march size': 'Select base march size on your **BEST** march. Do not include Acadia buff or '
        #                   'Hyperion/Poetic/Romantic.',
        #     'alliance': 'Select the alliance you will be in at the time of the event.',
        #     'mm_traps': 'Select which traps you can build.',
        #     'skins':    'Select which base skins you currently own.'
        # }
        # nextCategoryPrompt = nextCategoryPromptDict.get(nextCategory, None)

        if nextCategory is not None:
            nextCategoryPrompt = self.get_next_category_prompt_from_json(nextCategory)
            # edit the interaction message with a new ProfessionMenuView view for the next category
            # this cycles until nextCategory is None (when category is "skins")
            await interaction.response.edit_message(
                content=nextCategoryPrompt,
                view=ProfessionMenuView(
                    self.parent_message, nextCategory,
                    class_=self.class_, level=self.level, units=self.units, march_size=self.march_size,
                    alliance=self.alliance, mm_traps=self.mm_traps, first_entry=self.first_entry
                )
            )
        else:
            # the current category is "skins"
            # Remove the selectmenu, tell user what they selected, write the info to DB

            skins = ', '.join(self.values)

            # parse selection info into appropriate form for DB-submission
            # unit(s)
            # unitAbbrevDict = db.get_profession_abbreviation_dict('units')
            # unitChars = [unitAbbrevDict[unit] for unit in self.units.split(', ')]

            # mm_traps
            if self.mm_traps is None or 'None' in self.mm_traps:
                self.mm_traps = ''

            # skin(s)
            if 'None' in skins:
                skins = ''

            # prof_array = [self.class_, self.level, ''.join(unitChars), self.march_size, self.alliance, self.mm_traps, skins]
            prof_array = [self.class_, self.level, self.units, self.march_size, self.alliance, self.mm_traps, skins]

            # if first-time user does not have an entry in DB, add one
            if self.first_entry:
                # set status to "NO", lottery to 1 (default vals)
                entry = [interaction.user.id, *prof_array, "NO", 1, 0]

                await db.add_entry(entry)
                embed = db.info_embed(entry,
                                      descr='You have been added to the database.\n'
                                            'Your event sign-up was not registered.\n'
                                            f'Please **sign up** for the event again.\n'
                                            '\u200b\n',
                                      first_entry=True
                                      )

            # else just update the user's profession
            else:
                # still need to get old DB entry to send to db.info_embed()
                old_entry = await db.get_entry(interaction.user.id)
                status, lottery = old_entry[db.STATUS_IND], old_entry[db.LOTTERY_IND]
                new_entry = [interaction.user.id, *prof_array, status, lottery]

                embed = db.info_embed(new_entry, descr='Successfully edited database entry.\n\u200b\n')
                await db.update_profession(interaction.user.id, prof_array)

            # send user's selection as an info-embed, remove the view
            await interaction.response.edit_message(content='', embed=embed, view=None)

    def parse_options_from_json(self, category):
        with open(globals.PROFESSION_INFO_JSON, 'r') as f:
            obj = json.load(f)
        if category == 'level':
            category = 'ce_level' if self.class_ == 'CE' else 'mm_level'

        dat = obj[category]

        # Create the select options
        if 'descriptions' in dat:
            options = []
            for option, description in zip(dat['options'], dat['descriptions']):
                options.append(discord.SelectOption(label=option, description=description))
        else:
            options = [discord.SelectOption(label=option) for option in dat['options']]
        if category == 'class':
            skip_option = discord.SelectOption(label='CANCEL', description='Pick this to cancel updating info.')
            options.append(skip_option)
        self.options_ = options

        # set additional parameters
        self.category_title = dat['category_title']
        if dat['select_multiple']:
            self.max_vals = len(options)

    def get_next_category_prompt_from_json(self, next_category):
        with open(globals.PROFESSION_INFO_JSON, 'r') as f:
            obj = json.load(f)
        if next_category == 'level':
            next_category = 'ce_level' if self.class_ == 'CE' else 'mm_level'

        dat = obj[next_category]
        return dat['prompt']


class ProfessionMenuView(discord.ui.View):

    __slots__ = ('parent_message', 'category',
                 'class_', 'level', 'units', 'march_size', 'alliance', 'mm_traps', 'first_entry')

    def __init__(self, parent_message, category,
                 class_=None, level=None, units=None, march_size=None, alliance=None, mm_traps=None, first_entry=None):
        super().__init__(timeout=300)
        self.parent_message = parent_message
        self.first_entry = first_entry

        # Adds the dropdown to our view object.
        self.add_item(ProfessionMenu(
            parent_message, category,
            class_=class_, level=level, units=units, march_size=march_size, alliance=alliance, mm_traps=mm_traps,
            first_entry=first_entry)
        )

    async def on_timeout(self):
        # have to re-fetch parent message to get its current state
        dm_channel = self.parent_message.channel
        ID = self.parent_message.id
        parent_message = await dm_channel.fetch_message(ID)

        # check that the parent message has an embed, indicating that the user successfully completed selection.
        # If not, timeout the message.
        if not parent_message.embeds:
            await self.parent_message.edit(content='Selection menu timed out.', view=None)
