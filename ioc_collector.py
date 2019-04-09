import json
import base64
import requests

from requests.auth import HTTPBasicAuth
from datetime import datetime

from OTXv2 import OTXv2
from OTXv2 import IndicatorTypes


class IOCCollector():

    def __init__(self, otx_key, otx_users):
        self.otx = OTXv2(otx_key)
        self.users = otx_users

    def get_user_iocs(self, user):
        iocs = [ioc['indicator'] for ioc in \
                self.otx.get_all_indicators(author_name=user, indicator_types=[IndicatorTypes.DOMAIN, IndicatorTypes.HOSTNAME])]
        return iocs

    def get_all_iocs(self):
        iocs = []
        for user in self.users:
            iocs.extend(self.get_user_iocs(user))
        return sorted(list(set(iocs)))


class GitHubUpdater():

    def __init__(self):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
        self.ioc_collector = IOCCollector(self.cfg["otx_key"], self.cfg["otx_users"])

    def _get_current_sha(self):
        r = requests.get(self.cfg["github_update_path"])
        if r.status_code == 200:
            print(f"Got old SHA: {r.json()['sha']}")
            return str(r.json()["sha"])
        return None

    def update_iocs(self):
        iocs = self.ioc_collector.get_all_iocs()
        print(f"Got {len(iocs)} IOCs from OTX")
        iocs_b64 = base64.b64encode("\n".join(self.ioc_collector.get_all_iocs()).encode()).decode()

        headers = {'Authorization': f"token {self.cfg['github_key']}"}
        payload = {"message": f"IOCs updated on {datetime.now()}",
                   "content": iocs_b64,
                   "sha": self._get_current_sha()}
        r = requests.put(self.cfg["github_update_path"], data=json.dumps(payload),
                         headers = headers)
        print(r.json())


if __name__ == "__main__":
    gh = GitHubUpdater()
    gh.update_iocs()
