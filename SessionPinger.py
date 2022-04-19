import json
import time
from datetime import datetime, timedelta
from typing import Dict

import pytz
from discord import Guild, Role, TextChannel, Embed, Color
from discord.ext import tasks

from database import Database


class SessionPinger:
    def __init__(self, guild: Guild):
        self.guild = guild

    async def get_session_times(self) -> Dict[str, int]:
        session_times = {}

        db = Database()
        campaigns = await db.list_campaigns()

        for campaign in campaigns.values():
            session_time = campaign['session'] if 'session' in campaign else None
            role_id = int(campaign['role']) if 'role' in campaign else None

            if session_time is not None and role_id is not None:
                role = self.guild.get_role(role_id)
                if role is not None:
                    session_times[session_time] = role_id

        return session_times

    @tasks.loop(seconds=30)
    async def perform_loop(self):
        times = await self.get_session_times()
        current = pytz.timezone('Europe/Berlin').localize(datetime.now().replace(second=0, microsecond=0))

        for time_string, role_id in times.items():
            session_time = pytz.timezone('Europe/London').localize(datetime.strptime(time_string, '%Y-%m-%d %I:%M%p'))

            if current + timedelta(hours=1) == session_time:
                channel: TextChannel = self.guild.get_channel(883055887642677268)
                if channel is not None:
                    await channel.send(content='<@&{}>'.format(role_id), embed=Embed(
                        title='Session Reminder',
                        colour=Color.orange(),
                        description='The session starts in 1 hour, at <t:{0}> (<t:{0}:R>)'.format(int(time.mktime(session_time.replace(tzinfo=pytz.timezone('Europe/London')).timetuple())))
                    ))

    async def stop(self):
        self.perform_loop.cancel()
