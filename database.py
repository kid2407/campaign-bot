import json
from os import getenv
from os.path import exists
from typing import Dict, Union, List, Optional

from discord import Member


class Database:

    # ------------- #
    # General-Stuff #
    # ------------- #

    def __init__(self) -> None:
        self.filepath = getenv('DB_FILE', 'db.json')
        self.data = {}

        if not exists(self.filepath):
            with open(self.filepath, 'w') as db_file:
                json.dump(
                    {
                        "campaigns": {},
                        "last_oneshot_id": 0,
                        "oneshots": {}
                    }, db_file)
                db_file.close()
        self.load_data()

    def load_data(self) -> None:
        with open(self.filepath, 'r') as db_file:
            self.data = json.load(db_file)

    def save_data(self) -> None:
        with open(self.filepath, 'w+') as db_file:
            json.dump(self.data, db_file, indent=4)

    # -------------- #
    # Campaign-Stuff #
    # -------------- #

    async def list_campaigns(self) -> Dict:
        return self.data.get('campaigns', {})

    async def add_campaign(self, name: str, creator_id: int, module: str, description: str, campaign_id: str) -> bool:
        if campaign_id in self.data['campaigns']:
            return False

        new_campaign = {
            'id': campaign_id,
            'name': name,
            'module': module,
            'description': description,
            'creator_id': creator_id
        }
        self.data['campaigns'][campaign_id] = new_campaign
        self.save_data()
        return True

    async def delete_campaign(self, campaign_id: str) -> None:
        del self.data['campaigns'][campaign_id]
        self.save_data()

    async def campaign_details(self, identifier: str) -> Union[List[Dict], bool]:
        campaign_ids = []
        if identifier in self.data['campaigns']:
            campaign_ids = [identifier]
        else:
            for entry in self.data['campaigns'].values():
                if identifier.lower() in entry['name'].lower():
                    campaign_ids.append(str(entry['id']))
        if len(campaign_ids) == 0:
            return False
        else:
            campaign_data = []
            for campaign_id in campaign_ids:
                campaign = self.data['campaigns'].get(campaign_id, None)
                if campaign is not None:
                    campaign_data.append(campaign)
            return campaign_data

    async def update_campaign_description(self, campaign_id: str, description: str) -> None:
        self.data['campaigns'][campaign_id]['description'] = description
        self.save_data()

    async def update_campaign_session_date(self, campaign_id: str, session_string: str) -> bool:
        self.data['campaigns'][campaign_id]['session'] = session_string
        self.save_data()
        return True

    async def update_campaign_role(self, campaign_id: str, role_id: int) -> None:
        self.data['campaigns'][campaign_id]['role'] = role_id
        self.save_data()

    async def campaign_change_channel(self, campaign_id: str, channel: int) -> None:
        self.data['campaigns'][campaign_id]['channel'] = channel
        self.save_data()

    async def update_extra_campaign_notification(self, campaign_id: str, status: str) -> None:
        self.data['campaigns'][campaign_id]['extra-notification'] = status
        self.save_data()

    # ------------- #
    # Oneshot-Stuff #
    # ------------- #

    async def add_oneshot(self, name: str, creator: Member, description: str, time: str, channel: Optional[int], ) -> int:
        oneshot = {
            'id': self.data['last_oneshot_id'] + 1,
            'name': name,
            'description': description,
            'creator_id': creator.id,
            'channel': channel,
            'time': time
        }
        self.data['oneshots'][oneshot['id']] = oneshot
        self.data['last_oneshot_id'] += 1
        self.save_data()
        return oneshot['id']

    async def delete_oneshot(self, oneshot_id: str) -> None:
        del self.data['oneshots'][oneshot_id]
        self.save_data()

    async def list_oneshots(self) -> Dict:
        return self.data['oneshots']

    async def oneshot_details(self, identifier: str) -> Union[List[Dict], bool]:
        oneshot_ids = []
        if identifier in self.data['campaigns']:
            oneshot_ids = [identifier]
        else:
            for entry in self.data['oneshots'].values():
                if identifier.lower() in entry['name'].lower():
                    oneshot_ids.append(str(entry['id']))
        if len(oneshot_ids) == 0:
            return False
        else:
            oneshot_data = []
            for oneshot_id in oneshot_ids:
                oneshot = self.data['oneshots'].get(oneshot_id, None)
                if oneshot is not None:
                    oneshot_data.append(oneshot)
            return oneshot_data

    async def update_oneshot_description(self, oneshot_id: str, description: str) -> bool:
        if oneshot_id not in self.data['oneshots']:
            return False
        self.data['oneshots'][oneshot_id]['description'] = description
        self.save_data()
        return True

    async def oneshot_change_time(self, oneshot_id: str, time: str) -> bool:
        if oneshot_id not in self.data['oneshots']:
            return False
        self.data['oneshots'][oneshot_id]['time'] = time
        self.save_data()
        return True

    async def oneshot_change_channel(self, oneshot_id: str, channel: int) -> bool:
        if oneshot_id not in self.data['oneshots']:
            return False
        self.data['oneshots'][oneshot_id]['channel'] = channel
        self.save_data()
        return True
