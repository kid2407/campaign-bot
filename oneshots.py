import re
import time
from datetime import datetime
from os import getenv
from time import mktime
from typing import Dict, Tuple

import pytz
from discord import Color, Embed, Guild, Member
from discord.ext.commands import Context

from MessageHelper import message
from MessageTypes import INFO, WARN, ERROR
from database import Database


class Oneshots:
    FREE_COMMANDS = ['help', 'list', 'details']
    GATED_COMMANDS = ['add', 'delete', 'description', 'channel', 'time']

    def __init__(self, context: Context, db: Database, prefix: str) -> None:
        self.context = context
        self.db = db
        self.prefix = prefix
        role_string = getenv('ONESHOT_ROLES')
        self.GATED_ROLES = list(map(int, role_string.split(','))) if role_string is not None else []

    async def help(self) -> None:
        """Help for Oneshot related commands"""
        help_embed = Embed(colour=Color.dark_gold(), title='Managing Oneshots - Help', description='The following sub-commands are available:')

        help_embed.add_field(name='help', value='Displays this help.', inline=False)
        help_embed.add_field(name='list', value='Lists all oneshots.', inline=False)
        help_embed.add_field(name='details <oneshot-id|oneshot-name>', value='Display a detailed overview about one oneshot. If multiple are found, all matches will be shown.', inline=False)
        help_embed.add_field(name='add <name> <description> <date> [channel]', value='Add a new oneshot. Use the format \'YYYY-MM-DD hour:minute[am/pm]\' (e.g. {}) for the date and time. Mention the channel or type down it\'s name.'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')), inline=False)
        help_embed.add_field(name='delete <oneshot-name> <oneshot-id>', value='Deletes a oneshot. This cannot be undone!', inline=False)
        help_embed.add_field(name='description <oneshot-id> <description>', value='Update the description of a oneshot.', inline=False)
        help_embed.add_field(name='channel <oneshot-id> <channel>', value='Update the channel of a oneshot.', inline=False)
        help_embed.add_field(name='time <oneshot-id> <time>', value='Update the time of a oneshot.', inline=False)

        await self.context.send(embed=help_embed)

    async def add(self, args) -> None:
        arg_count = len(args)
        if arg_count < 3:
            await message(context=self.context, text='A date is required!', message_type=WARN)
            return
        elif arg_count < 2:
            await message(context=self.context, text='A description is required!', message_type=WARN)
            return
        elif arg_count < 1:
            await message(context=self.context, text='A name is required!', message_type=WARN)
            return

        name = args[0]
        description = args[1]
        start_time = args[2]
        channel = None

        if arg_count == 4:
            result = re.search(r'\d+', args[3])
            if result:
                channel = int(result.group())
            else:
                guild: Guild = self.context.guild
                if guild:
                    for text_channel in guild.text_channels:
                        if text_channel.name == args[3]:
                            channel = text_channel.id
                            break
            if channel is None:
                await message(context=self.context, text='Invalid Channel ID or name!', message_type=WARN)
                return

        oneshot_id = await self.db.add_oneshot(name=name, creator=self.context.author, description=description, time=start_time, channel=channel)
        await message(context=self.context, text='Successfully added the oneshot "{}" with ID {}.'.format(name, oneshot_id), message_type=INFO)

    async def delete(self, args, requester: Member) -> None:
        """Deletes an oneshot from the database. This cannot be undone!"""
        if len(args) == 0:
            await message(context=self.context, text='You need to specify the oneshots name or its ID to delete it!', message_type=WARN)
            return

        oneshots = await self.db.oneshot_details(identifier=args[0])
        if len(oneshots) != 1:
            if len(oneshots) == 0:
                await message(context=self.context, text='Could not find the oneshot you specified!', message_type=WARN)
                return
            await message(context=self.context, text='Multiple oneshots that match found. Please specify only one oneshot.', message_type=WARN)
            return

        oneshot: Dict = oneshots[0]
        if oneshot['creator_id'] != requester.id:
            await message(context=self.context, text='You are not the owner of the oneshot!', message_type=WARN)
        else:
            await self.db.delete_oneshot(str(oneshot['id']))
            await message(context=self.context, text='Deleted oneshot "{}" successfully.'.format(oneshot['name']), message_type=INFO)

    async def show_list(self) -> None:
        oneshots = await self.db.list_oneshots()
        out = Embed(colour=Color.blue(), title='List of oneshots', description='No oneshots found.' if len(oneshots) == 0 else '')

        for oneshot in oneshots.values():
            out.add_field(name=oneshot.get('name'), value=oneshot.get('description'), inline=False)

        await self.context.send(embed=out)

    async def details(self, args) -> None:
        """Show the details of all oneshots, that match the given identifier"""
        if len(args) == 0:
            await message(context=self.context, text='You have to specify a oneshot to show details for!', message_type=WARN)
            return

        details = await self.db.oneshot_details(args[0])

        if not details or len(details) == 0:
            await message(context=self.context, text='Could not find the oneshot you specified.', message_type=WARN)
            return

        for oneshot in details:
            embed = Embed(title='Oneshot Information - ' + oneshot['name'], colour=Color.blue())
            embed.add_field(name='ID', value=oneshot['id'])
            embed.add_field(name='Name', value=oneshot['name'])
            embed.add_field(name='Description', value=oneshot['description'])
            embed.add_field(name='Date/Time', value='<t:{0}> (<t:{0}:R>)'.format(int(mktime(datetime.strptime(oneshot['time'], '%Y-%m-%d %I:%M%p').timetuple()))))
            if oneshot['channel'] is not None:
                embed.add_field(name='Channel', value='<#{}>'.format(oneshot['channel']))

            dm = self.context.guild.get_member(oneshot['creator_id'])
            embed.add_field(name='DM', value='<@{}>'.format(dm.id) if dm else 'Unknown User')

            await self.context.send(embed=embed)

    async def description(self, args) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await message(context=self.context, text='Please specify a valid oneshot-ID.', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='Please specify a new description.', message_type=WARN)
                return

        oneshot_id = args[0]
        description = args[1]

        success = await self.db.update_oneshot_description(oneshot_id, description)
        if success:
            await message(context=self.context, text='Description updated', message_type=INFO)
        else:
            await message(context=self.context, text='Failed to update description: Invalid oneshot-ID.', message_type=ERROR)

    async def change_time(self, args) -> None:  # Time format: date = datetime.strptime(date_str, '%Y-%m-%d %I%p'), e.g. 2022-04-08 4:30pm
        if len(args) < 2:
            if len(args) == 0:
                await message(context=self.context, text='Please specify a valid oneshot-ID.', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='Please specify a new time.', message_type=WARN)
                return

        oneshot_id = args[0]
        time_string = args[1]

        try:
            time.strptime(time_string, '%Y-%m-%d %I:%M%p')
            time_valid = True
        except ValueError:
            time_valid = False

        if not time_valid:
            await message(context=self.context, text='The time you specified is incorrectly formatted. Please use the format "YYYY-MM-DD hour:minute[am/pm]" (e.g. {})'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')), message_type=ERROR)
            return

        success = await self.db.oneshot_change_time(oneshot_id, time_string)
        if success:
            await message(context=self.context, text='Successfully changed the time to <t:{0}>.'.format(int(mktime(datetime.strptime(time_string, '%Y-%m-%d %I:%M%p').timetuple()))), message_type=INFO)
        else:
            await message(context=self.context, text='Failed to update session time: Invalid oneshot-ID.', message_type=ERROR)

    async def change_channel(self, args) -> None:
        if len(args) < 2:
            if len(args) == 0:
                await message(context=self.context, text='Please specify a valid oneshot-ID.', message_type=WARN)
                return
            if len(args) == 1:
                await message(context=self.context, text='Please specify a new channel.', message_type=WARN)
                return

        oneshot_id = args[0]
        channel_string = args[1]

        channel = None
        result = re.search(r'\d+', channel_string)

        guild: Guild = self.context.guild
        if not guild:
            await message(context=self.context, text='Error fetching the channel list. Please try again later.', message_type=ERROR)
            return

        if result:
            channel = int(result.group())
            if guild.get_channel(channel) is None:
                await message(context=self.context, text='Invalid Channel ID!', message_type=WARN)
                return
        else:
            for text_channel in guild.text_channels:
                if text_channel.name == channel_string:
                    channel = text_channel.id
                    break
        if channel is None:
            await message(context=self.context, text='Invalid Channel ID or name!', message_type=WARN)
            return

        await self.db.oneshot_change_channel(oneshot_id, channel)
        await message(context=self.context, text='Successfully changed the channel to {}.', message_type=INFO)

    async def process_commands(self, sender: Member, args: Tuple) -> None:
        if len(args) == 0:
            subcommand = 'help'
        else:
            subcommand = args[0]

        if not await self.check_permissions_for_command(sender, subcommand):
            await message(context=self.context, text='You do not have the required role to use this command!', message_type=WARN)
            return

        if subcommand == 'help':
            await self.help()
        elif subcommand == 'add':
            await self.add(args[1:])
        elif subcommand == 'delete':
            await self.delete(args[1:], sender)
        elif subcommand == 'list':
            await self.show_list()
        elif subcommand == 'details':
            await self.details(args[1:])
        elif subcommand == 'description':
            await self.description(args[1:])
        elif subcommand == 'time':
            await self.change_time(args[1:])
        elif subcommand == 'channel':
            await self.change_channel(args[1:])
        else:
            await message(self.context, text='Unknown subcommand. Try `{}campaign help` for a full list of subcommands'.format(self.prefix), message_type='WARN')

    async def check_permissions_for_command(self, requester: Member, command: str) -> bool:
        if command in self.FREE_COMMANDS:
            return True

        if command in self.GATED_COMMANDS:
            role_ids = list(map(lambda role: role.id, requester.roles))
            return not set(role_ids).isdisjoint(self.GATED_ROLES)

        return False
