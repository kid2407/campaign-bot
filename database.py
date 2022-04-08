import json
from os import getenv
from os.path import exists
from typing import Dict, Union, List


class Database:
    def __init__(self) -> None:
        self.filepath = getenv('DB_FILE', 'db.json')
        self.data = {}

        if not exists(self.filepath):
            with open(self.filepath, 'w') as db_file:
                json.dump({"last_campaign_id": 0}, db_file)
                db_file.close()
        self.load_data()

    def load_data(self) -> None:
        with open(self.filepath, 'r') as db_file:
            self.data = json.load(db_file)

    def save_data(self) -> None:
        with open(self.filepath, 'w+') as db_file:
            json.dump(self.data, db_file, indent=4)

    async def list_campaigns(self) -> Dict:
        return self.data.get('campaigns', {})

    async def add_campaign(self, name: str, creator_id: int, description: str) -> int:
        if 'campaigns' not in self.data:
            self.data['campaigns'] = {}
        new_campaign = {
            'id': self.data['last_campaign_id'] + 1,
            'name': name,
            'description': description,
            'creator_id': creator_id
        }
        self.data['campaigns'][new_campaign['id']] = new_campaign
        self.data['last_campaign_id'] += 1
        self.save_data()
        return new_campaign['id']

    async def campaign_details(self, identifier: str) -> Union[List[Dict], bool]:
        campaign_ids = []
        if identifier.isdigit():
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

    async def delete_campaign(self, campaign_id: str) -> None:
        del self.data['campaigns'][campaign_id]
        self.save_data()