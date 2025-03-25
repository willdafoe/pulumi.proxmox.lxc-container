import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ProxmoxAPI:
    def __init__(self):
        self.host = os.getenv("PROXMOX_HOST")
        self.user = os.getenv("PROXMOX_USER")
        self.token_id = os.getenv("PROXMOX_TOKEN_ID")
        self.token_secret = os.getenv("PROXMOX_TOKEN_SECRET")
        self.node = os.getenv("PROXMOX_NODE")
        self.base_url = f"https://{self.host}:8006/api2/json"
        self.auth_header = {
            "Authorization": f"PVEAPIToken={self.user}!{self.token_id}={self.token_secret}"
        }

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_header)
        res = requests.request(method, url, headers=headers, verify=False, **kwargs)
        res.raise_for_status()
        return res.json()

    def create_lxc(self, vmid, params):
        path = f"/nodes/{self.node}/lxc"
        data = {**params, "vmid": vmid}
        return self._request("post", path, data=data)

    def delete_lxc(self, vmid):
        path = f"/nodes/{self.node}/lxc/{vmid}"
        return self._request("delete", path)
