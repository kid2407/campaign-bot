from os import getenv

from discord import Member, Intents, Embed, Color
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from MessageHelper import message
from MessageTypes import WARN
from campaigns import Campaigns
from database import Database

load_dotenv()

intents: Intents = Intents.default()
# noinspection PyUnresolvedReferences,PyDunderSlots
intents.members = True
bot = commands.Bot(command_prefix=getenv('PREFIX', '$'), intents=intents)
bot.remove_command('help')


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))


@bot.command(name='help')
async def generic_help(context: Context, *args) -> None:
    if len(args) == 0:
        embed = Embed(title='Help - Overview', description='Type `{}help category` for more info on a category and its subcommands.'.format(bot.command_prefix), colour=Color.blurple())
        embed.add_field(name='campaign', value='Create and manage your campaigns. Restricted to Group Campaign DMs and above.', inline=False)
        embed.add_field(name='oneshot', value='Create and manage your oneshots. Restricted to New DMs and above.', inline=False)

        await context.send(embed=embed)
    else:
        category = args[0]
        if category == 'campaign':
            await Campaigns(context, Database()).help()
        else:
            await message(context=context, text='Unknown category.', message_type=WARN)


async def process_campaign_commands(campaign: Campaigns, sender: Member, args):
    if len(args) == 0:
        subcommand = 'help'
    else:
        subcommand = args[0]

    if subcommand == 'help':
        await campaign.help()
    elif subcommand == 'list':
        await campaign.list_campaigns()
    elif subcommand == 'add':
        await campaign.add_campaign(sender, args[1:])
    elif subcommand == 'details':
        await campaign.campaign_details(args[1:])
    elif subcommand == 'delete':
        await campaign.delete_campaign(sender, args[1:])
    elif subcommand == 'description':
        await campaign.update_description(sender, args[1:])
    else:
        await message(campaign.context, text='Unknown subcommand. Try `{}campaign help` for a full list of subcommands'.format(bot.command_prefix), message_type='WARN')


@bot.command(name='campaign')
async def campaigns(context: Context, *args):
    campaign_handler = Campaigns(context, Database())
    if len(args) == 0:
        await campaign_handler.help()
    else:
        await process_campaign_commands(campaign_handler, context.author, args)


bot.run(getenv('BOT_TOKEN'))
