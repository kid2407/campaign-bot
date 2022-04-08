from os import getenv

from discord import Member, Intents
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from campaigns import Campaigns
from database import Database

load_dotenv()

intents: Intents = Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=getenv('PREFIX', '$'), intents=intents)


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))


async def process_command(campaign: Campaigns, sender: Member, args):
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
    else:
        await campaign.message(text='Unknown subcommand. Try `{}campaign help` for a full list of subcommands'.format(bot.command_prefix), message_type='WARN')


@bot.command(name='campaign')
async def campaigns(ctx: Context, *args):
    campaign_handler = Campaigns(ctx, Database())
    if len(args) == 0:
        await campaign_handler.help()
    else:
        await process_command(campaign_handler, ctx.author, args)


bot.run(getenv('BOT_TOKEN'))
