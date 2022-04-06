from os import getenv

from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from campaigns import Campaigns

load_dotenv()

bot = commands.Bot(command_prefix=getenv('PREFIX', '$'))


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))


async def process_command(campaign: Campaigns, args):
    if args[0] == 'list':
        await campaign.list_campaigns(args)
    else:
        await campaign.ctx.send('Unknown subcommand. Try `{}campaigns help` for a full list of subcommands'.format(bot.command_prefix))


@bot.command()
async def campaigns(ctx: Context, *args):
    campaign = Campaigns(ctx)
    if len(args) == 0:
        await campaign.help()
    else:
        await process_command(campaign, args)


bot.run(getenv('BOT_TOKEN'))
