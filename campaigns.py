import time
from datetime import datetime
from itertools import islice
from os import getenv
from time import mktime
from typing import Tuple, Dict

import pytz
from discord import Embed, Color, Member
from discord.ext.commands import Context

from MessageHelper import message
from MessageTypes import INFO, WARN, ERROR
from database import Database


class Campaigns:
    FREE_COMMANDS = ['help', 'list', 'details']
    GATED_COMMANDS = ['add', 'delete', 'description', 'session']
    PAGE_SIZE = 10

    def __init__(self, context: Context, db: Database, prefix: str):
        self.context = context
        self.db = db
        self.prefix = prefix
        role_string = getenv('CAMPAIGN_ROLES')
        self.GATED_ROLES = list(map(int, role_string.split(','))) if role_string is not None else []

    async def help(self):
        """Your average help command"""
        help_embed = Embed(colour=Color.purple(), title='Managing Campaigns - Help', description='The following sub-commands are available:')
        help_embed.colour = Color.purple()

        help_embed.add_field(name='help', value='Displays this help.', inline=False)
        help_embed.add_field(name='list', value='Lists all campaigns.', inline=False)
        help_embed.add_field(name='details <campaign-id|campaign-name>', value='Display a detailed overview about one campaign. If multiple are found, all matches will be shown.', inline=False)
        help_embed.add_field(name='add <name> <module> <description> <campaign-id>', value='Add a new campaign.', inline=False)
        help_embed.add_field(name='delete <campaign-name> <campaign-id>', value='Deletes a campaign. This cannot be undone!', inline=False)
        help_embed.add_field(name='description <campaign-id> <description>', value='Update the description of a campaign.', inline=False)
        help_embed.add_field(name='session <campaign-id> <date>', value='Update the date of the next session. Requires to use the format \'YYYY-MM-DD hour:minute[am/pm]\' (e.g. {}) for the date and time.'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')), inline=False)

        await self.context.send(embed=help_embed)

    async def show_list(self, args: Tuple) -> None:
        """Prints a list of all currently active campaigns"""
        campaign_list = await self.db.list_campaigns()
        if len(campaign_list) == 0:
            out = Embed(colour=Color.blue(), title='List of campaigns', description='No campaigns found.')
        else:
            if len(args) > 0:
                try:
                    offset = int(args[0])
                except ValueError:
                    await message(context=self.context, text='The offset you provided is not a number.', message_type=WARN)
                    return
            else:
                offset = 0

            if offset >= len(campaign_list):
                await message(context=self.context, text='You specified an offset greater than the total number of campaigns.', message_type=WARN)
                return

            short_campaign_list = dict(islice(campaign_list.items(), offset, min(offset + self.PAGE_SIZE, len(campaign_list))))

            out = Embed(colour=Color.blue(), title='List of campaigns (showing {}-{} of {})'.format(offset + 1, min(offset + 1 + self.PAGE_SIZE, len(campaign_list)), len(campaign_list)), description='')

            for campaign in short_campaign_list.values():
                out.add_field(name=campaign.get('name'), value='*Module*: {}\n*Description*: {}'.format(campaign['module'], campaign['description']), inline=False)

        await self.context.send(embed=out)

    async def details(self, args: Tuple) -> None:
        """Show the details of all campaigns, that match the given identifier"""
        if len(args) == 0:
            await message(context=self.context, text='You have to specify a campaign to show details for!', message_type=WARN)
            return

        details = await self.db.campaign_details(args[0])

        if not details or len(details) == 0:
            await message(context=self.context, text='Could not find the campaign you specified.', message_type=WARN)
            return

        for campaign in details:
            embed = Embed(title='Campaign Information - ' + campaign['name'], colour=Color.blue())
            embed.add_field(name='Campaign-ID', value=campaign['id'])
            embed.add_field(name='Name', value=campaign['name'])
            embed.add_field(name='Module', value=campaign['module'])

            dm = self.context.guild.get_member(campaign['creator_id'])
            embed.add_field(name='DM', value='<@{}>'.format(dm.id) if dm else 'Unknown User')
            embed.add_field(name='Description', value=campaign['description'])

            embed.add_field(name='Next Session', value='<t:{0}>\n\n<t:{0}:R>'.format(int(mktime(datetime.strptime(campaign['session'], '%Y-%m-%d %I:%M%p').timetuple()))) if 'session' in campaign and len(campaign['session']) > 0 else 'TBA')

            await self.context.send(embed=embed)

    async def add(self, creator: Member, args: Tuple) -> None:
        """Add a new campaign to the database"""
        if len(args) < 4:
            if len(args) == 0:
                await message(context=self.context, text='Please specify a name for the campaign.', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='Please specify which module this is from (Use "Homebrew" if not applicable)', message_type=WARN)
                return
            if len(args) == 2:
                await message(context=self.context, text='Please specify a description for the campaign.', message_type=WARN)
                return
            if len(args) == 3:
                await message(context=self.context, text='Please specify a campaign-ID (usually the group number).', message_type=WARN)
                return
        name = args[0]
        module = args[1]
        description = args[2]
        campaign_id = args[3]

        success = await self.db.add_campaign(name, creator.id, module, description, campaign_id)
        if success:
            await message(context=self.context, text='Created campaign "{}" with ID {}.'.format(name, campaign_id), message_type=INFO)
        else:
            await message(context=self.context, text='Failed to create campaign: Campaign with the ID {} already exists!'.format(campaign_id), message_type=ERROR)

    async def delete(self, requester: Member, args: Tuple) -> None:
        """Deletes a campaign from the database. This cannot be undone!"""
        if len(args) < 2:
            if len(args) == 1:
                await message(context=self.context, text='You need to also specify the campaign-id to delete this campaign!', message_type=WARN)
                return
            await message(context=self.context, text='You need to specify a campaign and its ID to delete it!', message_type=WARN)
            return

        campaigns = await self.db.campaign_details(identifier=args[1])
        if len(campaigns) != 1:
            if len(campaigns) == 0:
                await message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign: Dict = campaigns[0]
        if campaign['name'].lower() != args[0].lower():
            await message(context=self.context, text='The campaign name and id do not match!', message_type=WARN)
        elif campaign['creator_id'] != requester.id:
            await message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
        else:
            await self.db.delete_campaign(str(campaign['id']))
            await message(context=self.context, text='Deleted campaign "{}" successfully.'.format(campaign['name']), message_type=INFO)

    async def update_description(self, requester: Member, args: Tuple) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await message(context=self.context, text='You have to specify a campaign!', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='You have to specify a description!', message_type=WARN)
                return

        campaign_id = args[0]
        description = args[1]
        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if len(campaigns) != 1:
            if len(campaigns) == 0:
                await message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        await self.db.update_campaign_description(str(campaign['id']), description)
        await message(context=self.context, text='Description for campaign {} has been updated.'.format(campaign['name']), message_type=INFO)

    async def update_session_date(self, requester: Member, args: Tuple) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await message(context=self.context, text='You have to specify a campaign!', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='You have to specify a session date!', message_type=WARN)
                return

        campaign_id = args[0]
        session_string = args[1]
        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if len(campaigns) != 1:
            if len(campaigns) == 0:
                await message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        try:
            time.strptime(session_string, '%Y-%m-%d %I:%M%p')
            time_valid = True
        except ValueError:
            time_valid = False

        if not time_valid:
            await message(context=self.context, text='The time you specified is incorrectly formatted. Please use the format "YYYY-MM-DD hour:minute[am/pm]" (e.g. {})'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')), message_type=ERROR)
            return

        success = await self.db.update_campaign_session_date(str(campaign['id']), session_string)
        if success:
            await message(context=self.context, text='Successfully changed the session time to <t:{0}>.'.format(int(mktime(datetime.strptime(session_string, '%Y-%m-%d %I:%M%p').timetuple()))), message_type=INFO)
        else:
            await message(context=self.context, text='Failed to update session time: An unknown error occurred.', message_type=ERROR)

    async def process_commands(self, sender: Member, args) -> None:
        if len(args) == 0:
            subcommand = 'help'
        else:
            subcommand = args[0]

        if not await self.check_permissions_for_command(sender, subcommand):
            await message(context=self.context, text='You do not have the required role to use this command!', message_type=WARN)
            return

        if subcommand == 'help':
            await self.help()
        elif subcommand == 'list':
            await self.show_list(args[1:])
        elif subcommand == 'add':
            await self.add(sender, args[1:])
        elif subcommand == 'details':
            await self.details(args[1:])
        elif subcommand == 'delete':
            await self.delete(sender, args[1:])
        elif subcommand == 'description':
            await self.update_description(sender, args[1:])
        elif subcommand == 'session':
            await self.update_session_date(sender, args[1:])
        else:
            await message(self.context, text='Unknown subcommand. Try `{}campaign help` for a full list of subcommands'.format(self.prefix), message_type='WARN')

    async def check_permissions_for_command(self, requester: Member, command: str) -> bool:
        if command in self.FREE_COMMANDS:
            return True

        if command in self.GATED_COMMANDS:
            role_ids = list(map(lambda role: role.id, requester.roles))
            return not set(role_ids).isdisjoint(self.GATED_ROLES)

        return False
