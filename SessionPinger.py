from datetime import datetime, timedelta
from typing import Dict, List

import pytz
from discord import Guild, TextChannel, Embed, Color
from discord.ext import tasks

from database import Database


class SessionPinger:
    def __init__(self, guild: Guild):
        self.guild = guild

    async def get_session_times(self) -> List[Dict]:
        session_times = []

        db = Database()
        campaigns = await db.list_campaigns()

        for campaign in campaigns.values():
            session_time = str(campaign['session']) if 'session' in campaign else None
            role_id = int(campaign['role']) if 'role' in campaign else None
            channel_id = int(campaign['channel']) if 'channel' in campaign else None

            if session_time is not None and role_id is not None and channel_id is not None:
                role = self.guild.get_role(role_id)
                channel = self.guild.get_channel(channel_id)
                if role is not None and channel is not None:
                    session_times.append({'time': session_time, 'role': role_id, 'channel': channel_id, 'extra-notification': campaign['extra-notification'] if 'extra-notification' in campaign else 'false'})

        return session_times

    @tasks.loop(minutes=1)
    async def perform_loop(self):
        session_times = await self.get_session_times()
        current = pytz.timezone('Europe/Berlin').localize(datetime.now().replace(second=0, microsecond=0))

        for session_data in session_times:
            session_time = pytz.timezone('Europe/Berlin').localize(datetime.strptime(session_data['time'], '%Y-%m-%d %I:%M%p'))

            if current + timedelta(hours=1) == session_time:
                channel: TextChannel = self.guild.get_channel(session_data['channel'])
                if channel is not None:
                    await channel.send(content='<@&{}>'.format(session_data['role']), embed=Embed(
                        title='Session Reminder',
                        colour=Color.orange(),
                        description='The session starts in 1 hour, at <t:{0}> (<t:{0}:R>)'.format(int(session_time.replace(tzinfo=pytz.timezone('utc')).timestamp()))
                    ))

            if session_data['extra-notification'] == 'true':
                today_morning = pytz.timezone('Europe/Berlin').localize(datetime.now().replace(second=0, microsecond=0, minute=0, hour=9))

                if today_morning == current and current.date() == session_time.date():
                    channel: TextChannel = self.guild.get_channel(session_data['channel'])
                    if channel is not None:
                        await channel.send(content='<@&{}>'.format(session_data['role']), embed=Embed(
                            title='Session Reminder',
                            colour=Color.orange(),
                            description='Today is game day! The session is at <t:{0}> (<t:{0}:R>)'.format(int(session_time.replace(tzinfo=pytz.timezone('utc')).timestamp()))
                        ))

    async def stop(self):
        self.perform_loop.cancel()
