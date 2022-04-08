from discord import Embed, Color
from discord.ext.commands import Context

import MessageTypes
from MessageTypes import INFO, WARN, ERROR


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
