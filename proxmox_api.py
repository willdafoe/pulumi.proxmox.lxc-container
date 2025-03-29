import re
import requests
import urllib3

# Suppress unverified TLS warnings from self-signed Proxmox certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxmoxAPI:
    def __init__(self, host, user, token_id, token_secret, node):
        self.host = re.sub(r":\d+$", "", host)
        self.user = user
        self.token_id = token_id
        self.token_secret = token_secret
        self.node = node

        self.base_url = f"https://{self.host}:8006/api2/json"
        self.auth_header = {
            "Authorization": f"PVEAPIToken={self.user}!{self.token_id}={self.token_secret}"
        }

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_header)

        try:
            res = requests.request(method, url, headers=headers, verify=False, **kwargs)
            if not res.ok:
                raise RuntimeError(f"Proxmox API error {res.status_code}: {res.text}")
            return res.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Proxmox API request failed: {e}")

    def create_lxc(self, vmid, params):
        path = f"/nodes/{self.node}/lxc"
        data = {**params, "vmid": vmid}
        return self._request("post", path, data=data)

    def delete_lxc(self, vmid):
        path = f"/nodes/{self.node}/lxc/{vmid}"
        return self._request("delete", path)

    def list_lxc(self):
        return self._request("get", f"/nodes/{self.node}/lxc")

    def get_lxc_status(self, vmid):
        return self._request("get", f"/nodes/{self.node}/lxc/{vmid}/status/current")

    def start_lxc(self, vmid):
        return self._request("post", f"/nodes/{self.node}/lxc/{vmid}/status/start")

    def stop_lxc(self, vmid):
        return self._request("post", f"/nodes/{self.node}/lxc/{vmid}/status/stop")

    def list_templates(self):
        path = f"/nodes/{self.node}/storage/local/content"
        result = self._request("get", path)
        return [item for item in result.get("data", []) if item["content"] == "vztmpl"]
    
    def get_next_vmid(self, starting_from=200):
        res = self._request("get", "/cluster/nextid")
        nextid = int(res.get("data", starting_from))
        return max(nextid, starting_from)
