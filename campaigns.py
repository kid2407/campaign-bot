from typing import Tuple, Dict

from discord import Embed, Color, Member
from discord.ext.commands import Context

from database import Database


class Campaigns:
    def __init__(self, ctx: Context, db: Database):
        self.ctx = ctx
        self.db = db

    async def message(self, text: str, message_type: str) -> None:
        embed = Embed()
        if message_type == 'INFO':
            embed.title = 'Info'
            embed.colour = Color.blue()
        elif message_type == 'WARN':
            embed.title = 'Warning'
            embed.colour = Color.orange()
        elif message_type == 'ERROR':
            embed.title = 'Error'
            embed.colour = Color.red()

        embed.description = text

        await self.ctx.send(embed=embed)

    async def help(self):
        """Your average help command"""
        help_embed = Embed()
        help_embed.colour = Color.purple()
        help_embed.title = 'Managing Campaigns - Help'
        help_embed.description = 'The following sub-commands are available:'

        help_embed.add_field(name='help', value='Displays this help', inline=False)
        help_embed.add_field(name='list', value='Lists all campaigns', inline=False)
        help_embed.add_field(name='details <campaign-id>', value='Display a detailed overview about one campaign', inline=False)
        help_embed.add_field(name='add <name> [description]', value='Add a new campaign', inline=False)
        help_embed.add_field(name='delete <campaign-name> <campaign-id>', value='Deletes a campaign. This cannot be undone!', inline=False)

        await self.ctx.send(embed=help_embed)

    async def list_campaigns(self) -> None:
        """Prints a list of all currently active campaigns"""
        campaign_list = await self.db.list_campaigns()
        out = Embed()
        out.colour = Color.blue()
        out.title = 'List of campaigns'

        if len(campaign_list) == 0:
            out.description = 'No campaigns found'
        else:
            for campaign in campaign_list.values():
                out.add_field(name=campaign.get('name'), value=campaign.get('description'), inline=False)

        await self.ctx.send(embed=out)

    async def campaign_details(self, args: Tuple) -> None:
        """Show the details of all campaigns, that match the given identifier"""
        if len(args) == 0:
            await self.message(text='You have to specify a campaign to show details for!', message_type='WARN')
        else:
            details = await self.db.campaign_details(args[0])

            if not details:
                await self.message(text='Could not find the campaign you specified', message_type='WARN')
            else:
                for campaign in details:
                    embed = Embed()
                    embed.title = 'Campaign Information - ' + campaign['name']
                    embed.colour = Color.blue()
                    embed.add_field(name='Campaign-ID', value=campaign['id'])
                    embed.add_field(name='Name', value=campaign['name'])
                    embed.add_field(name='Description', value=campaign['description'])

                    dm = self.ctx.guild.get_member(campaign['creator_id'])
                    embed.add_field(name='DM', value=dm.name if dm else 'Unknown User')

                    await self.ctx.send(embed=embed)
                if len(details) == 0:
                    await self.message(text='Could not find the campaign you are looking for', message_type='WARN')

    async def add_campaign(self, creator: Member, args: Tuple) -> None:
        """Add a new campaign to the database"""
        if len(args) == 0:
            await self.message(text='You have to specify a name for the campaign!', message_type='WARN')
        else:
            name = args[0]
            if len(args) > 1:
                description = args[1]
            else:
                description = '*(no description)*'
            campaign_id = await self.db.add_campaign(name, creator.id, description)
            await self.message(text='Created campaign with ID {}'.format(campaign_id), message_type='INFO')

    async def delete_campaign(self, requester: Member, args: Tuple):
        """Deletes a campaign from the database. This cannot be undone!"""
        if len(args) == 0:
            await self.message(text='You need to specify a campaign and its ID to delete it!', message_type='WARN')
        elif len(args) == 1:
            await self.message(text='You need to also specify the campaign-id to delete this campaign!', message_type='WARN')
        else:
            campaigns = await self.db.campaign_details(identifier=args[1])
            if len(campaigns) == 0:
                await self.message(text='You specified an invalid campaign!', message_type='WARN')
            elif len(campaigns) > 1:
                await self.message(text='Multiple campaigns that match found. Please specify only one campaign', message_type='WARN')
            else:
                campaign: Dict = campaigns[0]
                if campaign['name'].lower() != args[0].lower():
                    await self.message(text='The campaign name and id do not match!', message_type='WARN')
                elif campaign['creator_id'] != requester.id:
                    await self.message(text='You are not the owner of the campaign!', message_type='WARN')
                else:
                    await self.db.delete_campaign(str(campaign['id']))
                    await self.message(text='Deleted campaign "{}" successfully.'.format(campaign['name']), message_type='INFO')
