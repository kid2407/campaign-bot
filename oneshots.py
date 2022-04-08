from discord import Member, Color, Embed
from discord.ext.commands import Context

from MessageHelper import message
from MessageTypes import INFO
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
        help_embed.add_field(name='add <name> [description]', value='Add a new oneshot.', inline=False)
        help_embed.add_field(name='delete <oneshot-name> <oneshot-id>', value='Deletes a oneshot. This cannot be undone!', inline=False)
        help_embed.add_field(name='description <oneshot-id> <description>', value='Update the description of a oneshot.', inline=False)
        help_embed.add_field(name='channel <oneshot-id> <channel>', value='Update the channel of a oneshot.', inline=False)
        help_embed.add_field(name='time <oneshot-id> <time>', value='Update the time of a oneshot.', inline=False)

        await self.context.send(embed=help_embed)

    async def add(self, args) -> None:
        # await self.db.add_oneshot()
        await message(context=self.context, text='Successfully added the oneshot {} with id {}.', message_type=INFO)

    async def delete(self, args) -> None:
        # await self.db.delete_oneshot()
        await message(context=self.context, text='Successfully deleted the oneshot {}.', message_type=INFO)

    async def list_oneshots(self) -> None:
        # await self.db.list_oneshots()
        await message(context=self.context, text='List of Oneshots here.', message_type=INFO)

    async def details(self, args) -> None:
        # await self.db.oneshot_details()
        await message(context=self.context, text='Details here', message_type=INFO)

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
            await self.delete(args[1:])
        elif subcommand == 'list':
            await self.list_oneshots()
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
