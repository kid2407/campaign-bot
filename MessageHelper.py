from datetime import datetime
from typing import Any, Dict

from discord import Embed, Color
from discord.ext.commands import Context

import ActionType
import MessageTypes
from MessageTypes import INFO, WARN, ERROR


class MessageHelper:

    @staticmethod
    def log(action_type: ActionType, data: Dict) -> None:

        if action_type == ActionType.CAMPAIGN_ADD:
            message = ActionType.CAMPAIGN_ADD.format(data['name'], data['id'], data['user'])
        elif action_type == ActionType.CAMPAIGN_DELETE:
            message = ActionType.CAMPAIGN_DELETE.format(data['name'], data['id'])
        elif action_type == ActionType.CAMPAIGN_DESCRIPTION:
            message = ActionType.CAMPAIGN_DESCRIPTION.format(data['name'], data['id'], data['description'])
        elif action_type == ActionType.CAMPAIGN_SESSION:
            message = ActionType.CAMPAIGN_SESSION.format(data['name'], data['id'], data['date'])
        elif action_type == ActionType.CAMPAIGN_ROLE:
            message = ActionType.CAMPAIGN_ROLE.format(data['name'], data['id'], data['role'])
        else:
            message = '(empty message)'

        print('[{}] {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message))

    @staticmethod
    async def message(context: Context, text: str, message_type: MessageTypes) -> None:
        embed = Embed()
        if message_type == INFO:
            embed.title = 'Info'
            embed.colour = Color.blue()
        elif message_type == WARN:
            embed.title = 'Warning'
            embed.colour = Color.orange()
        elif message_type == ERROR:
            embed.title = 'Error'
            embed.colour = Color.red()

        embed.description = text

        await context.send(embed=embed)
