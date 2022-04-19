from os import getenv

from discord import Intents, Embed, Color, Game
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from MessageHelper import message
from MessageTypes import WARN
from SessionPinger import SessionPinger
from campaigns import Campaigns
from database import Database
from oneshots import Oneshots

load_dotenv()

intents: Intents = Intents.default()
# noinspection PyUnresolvedReferences,PyDunderSlots
intents.members = True
prefix = getenv('PREFIX', '$')
bot = commands.Bot(command_prefix=prefix, intents=intents, activity=Game('Try {}help for more information.'.format(prefix)))
bot.remove_command('help')


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

    for guild in bot.guilds:
        await SessionPinger(guild).perform_loop.start()


@bot.command(name='help')
async def generic_help(context: Context, *args) -> None:
    if len(args) == 0:
        embed = Embed(title='Help - Overview', description='Type `{}help category` for more info on a category and its subcommands.'.format(bot.command_prefix), colour=Color.blurple())
        embed.add_field(name='campaign', value='Create and manage your campaigns. Restricted to Group Campaign DMs and above.', inline=False)
        embed.add_field(name='oneshot', value='Create and manage your oneshots. Restricted to New DMs and above.', inline=False)

        await context.send(embed=embed)
    else:
        category = args[0].lower()
        if category == 'campaign':
            await Campaigns(context, Database(), bot.command_prefix).help()
        elif category == 'oneshot':
            await Oneshots(context, Database(), bot.command_prefix).help()
        else:
            await message(context=context, text='Unknown category.', message_type=WARN)


@bot.command(name='campaign')
async def campaigns(context: Context, *args):
    await Campaigns(context, Database(), bot.command_prefix).process_commands(context.author, args)


@bot.command(name='oneshot')
async def oneshots(context: Context, *args):
    await Oneshots(context, Database(), bot.command_prefix).process_commands(context.author, args)


bot.run(getenv('BOT_TOKEN'))
