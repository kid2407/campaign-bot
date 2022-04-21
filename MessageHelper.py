from datetime import datetime
from typing import Any

from discord import Embed, Color
from discord.ext.commands import Context

import ActionType
import MessageTypes
from MessageTypes import INFO, WARN, ERROR


class MessageHelper:

    @staticmethod
    def log(action_type: ActionType, data: Any) -> None:
        message = '(empty message)'

        if action_type == ActionType.CAMPAIGN_ADD:
            message = ActionType.CAMPAIGN_ADD.format(data['id'])

        print('[{}] {}'.format(datetime.now().strftime('%Y-%m/%d %H:%M:%S'), data['id']))

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
