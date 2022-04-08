import re
from datetime import datetime
from time import mktime
from typing import Dict

import pytz
from discord import Color, Embed, Guild, Member
from discord.ext.commands import Context

from MessageHelper import message
from MessageTypes import INFO, WARN
from database import Database


class Oneshots:
    def __init__(self, context: Context, db: Database, prefix: str) -> None:
        self.context = context
        self.db = db
        self.prefix = prefix

    async def help(self) -> None:
        """Help for Oneshot related commands"""
        help_embed = Embed(colour=Color.dark_gold(), title='Managing Oneshots - Help', description='The following sub-commands are available:')

        help_embed.add_field(name='help', value='Displays this help.', inline=False)
        help_embed.add_field(name='list', value='Lists all oneshots.', inline=False)
        help_embed.add_field(name='details <oneshot-id|oneshot-name>', value='Display a detailed overview about one oneshot. If multiple are found, all matches will be shown.', inline=False)
        help_embed.add_field(name='add <name> <description> <date> [channel]', value='Add a new oneshot. Use the format \'YYYY-MM-DD hour:minute[am/pm]\' (e.g. {}) for the date. Mention the channel or type down it\'s name.'.format(datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %I:%M%p')), inline=False)
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
        await message(context=self.context, text='Successfully added the oneshot "{}" with id {}.'.format(name, oneshot_id), message_type=INFO)

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

        if not details:
            await message(context=self.context, text='Could not find the oneshot you specified.', message_type=WARN)
        else:
            if len(details) == 0:
                await message(context=self.context, text='Could not find the oneshot you are looking for.', message_type=WARN)
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
        # await self.db.update_oneshot_description()
        await message(context=self.context, text='Description updated', message_type=INFO)

    async def change_time(self, args) -> None:  # Time format: date = datetime.strptime(date_str, '%Y-%m-%d %I%p'), e.g. 2022-04-08 4:30pm
        # await self.db.oneshot_change_time()
        await message(context=self.context, text='Successfully changed the time to {}.', message_type=INFO)

    async def change_channel(self, args) -> None:
        # await self.db.oneshot_change_channel()
        await message(context=self.context, text='Successfully changed the channel to {}.', message_type=INFO)

    async def process_commands(self, args) -> None:
        if len(args) == 0:
            subcommand = 'help'
        else:
            subcommand = args[0]

        if subcommand == 'help':
            await self.help()
        elif subcommand == 'add':
            await self.add(args[1:])
        elif subcommand == 'delete':
            await self.delete(args[1:], self.context.author)
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
