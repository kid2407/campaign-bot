import re
import time
from datetime import datetime
from itertools import islice
from os import getenv
from time import mktime
from typing import Tuple, Dict, Union

import pytz
from discord import Embed, Color, Member, Guild, Role
from discord.ext.commands import Context

import ActionType
from MessageHelper import MessageHelper
from MessageTypes import INFO, WARN, ERROR
from database import Database


class Campaigns:
    FREE_COMMANDS = ['help', 'list', 'details']
    GATED_COMMANDS = ['add', 'delete', 'description', 'session', 'role', 'channel']
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
        help_embed.add_field(name='list [offset]', value='Lists all campaigns, up to a maximum of {} per page. To see more campaigns use an offset, e.g. `{}campaign list 10`'.format(self.PAGE_SIZE, self.prefix), inline=False)
        help_embed.add_field(name='details <campaign-id|campaign-name>', value='Display a detailed overview about one campaign. If multiple are found, all matches will be shown.', inline=False)
        help_embed.add_field(name='add <name> <module> <description> <campaign-id>', value='Add a new campaign.', inline=False)
        help_embed.add_field(name='delete <campaign-name> <campaign-id>', value='Deletes a campaign. This cannot be undone!', inline=False)
        help_embed.add_field(name='description <campaign-id> <description>', value='Update the description of a campaign.', inline=False)
        help_embed.add_field(name='session <campaign-id> <date>',
                             value='Update the date of the next session. Requires to use the format \'YYYY-MM-DD hour:minute[am/pm]\' (e.g. {}) for the date and time.'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')),
                             inline=False)
        help_embed.add_field(name='role <campaign-id> <role-id|role-name>', value='Update the role to be pinged for sessions.', inline=False)
        help_embed.add_field(name='channel <campaign-id> <channel-id|channel-name>', value='Update the channel to to receive notifications for sessions.', inline=False)

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
                    await MessageHelper.message(context=self.context, text='The offset you provided is not a number.', message_type=WARN)
                    return
            else:
                offset = 0

            if offset >= len(campaign_list):
                await MessageHelper.message(context=self.context, text='You specified an offset greater than the total number of campaigns.', message_type=WARN)
                return

            short_campaign_list = dict(islice(campaign_list.items(), offset, min(offset + self.PAGE_SIZE, len(campaign_list))))

            out = Embed(colour=Color.blue(), title='List of campaigns (showing {}-{} of {})'.format(offset + 1, min(offset + 1 + self.PAGE_SIZE, len(campaign_list)), len(campaign_list)), description='')

            for campaign in short_campaign_list.values():
                out.add_field(name=campaign.get('name'), value='*Module*: {}\n*Description*: {}'.format(campaign['module'], campaign['description']), inline=False)

        await self.context.send(embed=out)

    async def details(self, args: Tuple) -> None:
        """Show the details of all campaigns, that match the given identifier"""
        if len(args) == 0:
            await MessageHelper.message(context=self.context, text='You have to specify a campaign to show details for!', message_type=WARN)
            return

        details = await self.db.campaign_details(args[0])

        if not details or len(details) == 0:
            await MessageHelper.message(context=self.context, text='Could not find the campaign you specified.', message_type=WARN)
            return

        for campaign in details:
            embed = Embed(title='Campaign Information - ' + campaign['name'], colour=Color.blue())
            embed.add_field(name='Campaign-ID', value=campaign['id'])
            embed.add_field(name='Name', value=campaign['name'])
            embed.add_field(name='Module', value=campaign['module'])

            dm = self.context.guild.get_member(campaign['creator_id'])
            embed.add_field(name='DM', value='<@{}>'.format(dm.id) if dm else 'Unknown User')
            embed.add_field(name='Description', value=campaign['description'])

            embed.add_field(name='Next Session', value='<t:{0}>\n\n<t:{0}:R>'.format(int(mktime(datetime.strptime(campaign['session'], '%Y-%m-%d %I:%M%p').replace(tzinfo=pytz.timezone('Europe/London')).timetuple()))) if 'session' in campaign and len(
                campaign['session']) > 0 else 'TBA')

            await self.context.send(embed=embed)

    async def add(self, creator: Member, args: Tuple) -> None:
        """Add a new campaign to the database"""
        if len(args) < 4:
            if len(args) == 0:
                await MessageHelper.message(context=self.context, text='Please specify a name for the campaign.', message_type=WARN)
                return
            if len(args) == 1:
                await MessageHelper.message(context=self.context, text='Please specify which module this is from (Use "Homebrew" if not applicable)', message_type=WARN)
                return
            if len(args) == 2:
                await MessageHelper.message(context=self.context, text='Please specify a description for the campaign.', message_type=WARN)
                return
            if len(args) == 3:
                await MessageHelper.message(context=self.context, text='Please specify a campaign-ID (usually the group number).', message_type=WARN)
                return
        name = args[0]
        module = args[1]
        description = args[2]
        campaign_id = args[3]

        success = await self.db.add_campaign(name, creator.id, module, description, campaign_id)
        if success:
            MessageHelper.log(ActionType.CAMPAIGN_ADD, {'name': name, 'id': campaign_id, 'user': creator.display_name})
            await MessageHelper.message(context=self.context, text='Created campaign "{}" with ID {}.'.format(name, campaign_id), message_type=INFO)
        else:
            await MessageHelper.message(context=self.context, text='Failed to create campaign: Campaign with the ID {} already exists!'.format(campaign_id), message_type=ERROR)

    async def delete(self, requester: Member, args: Tuple) -> None:
        """Deletes a campaign from the database. This cannot be undone!"""
        if len(args) < 2:
            if len(args) == 1:
                await MessageHelper.message(context=self.context, text='You need to also specify the campaign-id to delete this campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='You need to specify a campaign and its ID to delete it!', message_type=WARN)
            return

        campaigns = await self.db.campaign_details(identifier=args[1])
        if not campaigns or len(campaigns) != 1:
            if not campaigns or len(campaigns) == 0:
                await MessageHelper.message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign: Dict = campaigns[0]
        if campaign['name'].lower() != args[0].lower():
            await MessageHelper.message(context=self.context, text='The campaign name and id do not match!', message_type=WARN)
        elif campaign['creator_id'] != requester.id:
            await MessageHelper.message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
        else:
            await self.db.delete_campaign(str(campaign['id']))
            MessageHelper.log(ActionType.CAMPAIGN_DELETE, {'name': campaign['name'], 'id': campaign['id'], 'user': requester.display_name})
            await MessageHelper.message(context=self.context, text='Deleted campaign "{}" successfully.'.format(campaign['name']), message_type=INFO)

    async def update_description(self, requester: Member, args: Tuple) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await MessageHelper.message(context=self.context, text='You have to specify a campaign!', message_type=WARN)
                return
            if len(args) == 1:
                await MessageHelper.message(context=self.context, text='You have to specify a description!', message_type=WARN)
                return

        campaign_id = args[0]
        description = args[1]
        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if not campaigns or len(campaigns) != 1:
            if not campaigns or len(campaigns) == 0:
                await MessageHelper.message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await MessageHelper.message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        await self.db.update_campaign_description(str(campaign['id']), description)
        MessageHelper.log(ActionType.CAMPAIGN_DESCRIPTION, {'name': campaign['name'], 'id': campaign['id'], 'description': description})
        await MessageHelper.message(context=self.context, text='Description for campaign {} has been updated.'.format(campaign['name']), message_type=INFO)

    async def update_session_date(self, requester: Member, args: Tuple) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await MessageHelper.message(context=self.context, text='You have to specify a campaign!', message_type=WARN)
                return
            if len(args) == 1:
                await MessageHelper.message(context=self.context, text='You have to specify a session date!', message_type=WARN)
                return

        campaign_id = args[0]
        session_string = args[1]
        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if not campaigns or len(campaigns) != 1:
            if not campaigns or len(campaigns) == 0:
                await MessageHelper.message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await MessageHelper.message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        try:
            time.strptime(session_string, '%Y-%m-%d %I:%M%p')
            time_valid = True
        except ValueError:
            time_valid = False

        if not time_valid:
            await MessageHelper.message(context=self.context,
                                        text='The time you specified is incorrectly formatted. Please use the format "YYYY-MM-DD hour:minute[am/pm]" (e.g. {})'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')),
                                        message_type=ERROR)
            return

        success = await self.db.update_campaign_session_date(str(campaign['id']), session_string)
        if success:
            MessageHelper.log(ActionType.CAMPAIGN_SESSION, {'name': campaign['name'], 'id': campaign['id'], 'date': session_string})
            await MessageHelper.message(context=self.context,
                                        text='Successfully changed the session time to <t:{0}>.'.format(int(mktime(datetime.strptime(session_string, '%Y-%m-%d %I:%M%p').replace(tzinfo=pytz.timezone('Europe/London')).timetuple()))),
                                        message_type=INFO)
        else:
            await MessageHelper.message(context=self.context, text='Failed to update session time: An unknown error occurred.', message_type=ERROR)

    async def update_notification_role(self, requester: Member, args: Tuple) -> None:
        if len(args) < 1:
            await MessageHelper.message(context=self.context, text='You have to specify a campaign!', message_type=WARN)
            return

        campaign_id = args[0]
        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if not campaigns or len(campaigns) != 1:
            if not campaigns or len(campaigns) == 0:
                await MessageHelper.message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await MessageHelper.message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        guild: Guild = self.context.guild

        if len(args) > 1:
            role = args[1]

            role_object = None
            filtered_role = ''.join(filter(str.isdigit, role))
            if len(role) == len(filtered_role):
                role_object: Union[Role, None] = guild.get_role(int(role))
            else:
                for single_role in guild.roles:
                    if single_role.name.lower() == role.lower():
                        role_object = single_role
                        break

            if role_object is None:
                await MessageHelper.message(context=self.context, text='You specified an invalid role!', message_type=WARN)
                return

            await self.db.update_campaign_role(campaign_id, role_object.id)
            MessageHelper.log(ActionType.CAMPAIGN_ROLE, {'name': campaign['name'], 'id': campaign['id'], 'role': role_object.name})
            await MessageHelper.message(context=self.context, text='Updated campaign role successfully.', message_type=INFO)
        else:
            role_object = guild.get_role(int(campaign['role'])) if 'role' in campaign else None
            await MessageHelper.message(context=self.context,
                                        text='The current role to ping is "{}" with the ID `{}`.'.format(role_object.name if role_object is not None else '(empty)', role_object.id if role_object is not None else '(empty)'),
                                        message_type=INFO)

    async def change_channel(self, requester: Member, args: Tuple) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await MessageHelper.message(context=self.context, text='Please specify a valid campaign-ID.', message_type=WARN)
                return
            if len(args) == 1:
                await MessageHelper.message(context=self.context, text='Please specify a new channel.', message_type=WARN)
                return

        campaign_id = args[0]
        channel_string = args[1]

        campaigns = await self.db.campaign_details(identifier=campaign_id)
        if not campaigns or len(campaigns) != 1:
            if not campaigns or len(campaigns) == 0:
                await MessageHelper.message(context=self.context, text='You specified an invalid campaign!', message_type=WARN)
                return
            await MessageHelper.message(context=self.context, text='Multiple campaigns that match found. Please specify only one campaign.', message_type=WARN)
            return

        campaign = campaigns[0]
        if campaign['creator_id'] != requester.id:
            await MessageHelper.message(context=self.context, text='You are not the owner of the campaign!', message_type=WARN)
            return

        channel = None
        result = re.search(r'\d+', channel_string)

        guild: Guild = self.context.guild
        if not guild:
            await MessageHelper.message(context=self.context, text='Error fetching the channel list. Please try again later.', message_type=ERROR)
            return

        if result:
            channel = int(result.group())
            if guild.get_channel(channel) is None:
                await MessageHelper.message(context=self.context, text='Invalid Channel ID!', message_type=WARN)
                return
        else:
            for text_channel in guild.text_channels:
                if text_channel.name == channel_string:
                    channel = text_channel.id
                    break
        if channel is None:
            await MessageHelper.message(context=self.context, text='Invalid Channel ID or name!', message_type=WARN)
            return

        await self.db.campaign_change_channel(campaign_id, channel)
        MessageHelper.log(ActionType.CAMPAIGN_CHANNEL, {'id': campaign_id, 'name': (await self.db.campaign_details(campaign_id))[0]['name'], 'channel': channel})
        await MessageHelper.message(context=self.context, text='Successfully changed the channel to <#{}>.'.format(channel), message_type=INFO)

    async def process_commands(self, sender: Member, args) -> None:
        if len(args) == 0:
            subcommand = 'help'
        else:
            subcommand = args[0]

        has_permission = await self.check_permissions_for_command(sender, subcommand)

        if has_permission is None:
            subcommand = ''
        elif not has_permission:
            await MessageHelper.message(context=self.context, text='You do not have the required role to use this command!', message_type=WARN)
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
        elif subcommand == 'role':
            await self.update_notification_role(sender, args[1:])
        elif subcommand == 'channel':
            await self.change_channel(sender, args[1:])
        else:
            await MessageHelper.message(self.context, text='Unknown subcommand. Try `{}campaign help` for a full list of subcommands'.format(self.prefix), message_type='WARN')

    async def check_permissions_for_command(self, requester: Member, command: str) -> Union[bool, None]:
        if command in self.FREE_COMMANDS:
            return True

        if command in self.GATED_COMMANDS:
            role_ids = list(map(lambda role: role.id, requester.roles))
            return not set(role_ids).isdisjoint(self.GATED_ROLES)

        return None
