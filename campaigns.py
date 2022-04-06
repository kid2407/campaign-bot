from discord import Embed, Color
from discord.ext.commands import Context


class Campaigns:

    def __init__(self, ctx: Context):
        self.ctx = ctx

    async def help(self):
        help_embed = Embed()
        help_embed.colour = Color.purple()
        help_embed.title = 'Managing Campaigns - Help'
        help_embed.description = 'The following sub-commands are available:'

        help_embed.add_field(name='help', value='Displays this help', inline=False)
        help_embed.add_field(name='list', value='Lists all campaigns', inline=False)
        help_embed.add_field(name='add <name> [description]', value='Add a new campaign', inline=False)
        help_embed.add_field(name='delete <name> <campaign-id>', value='Deletes a campaign. This cannot be undone!', inline=False)

        await self.ctx.send(embed=help_embed)

    async def list_campaigns(self, args):
        """Prints a list of all currently active campaigns"""
        await self.ctx.send('Called subcommand of `campaign`')
