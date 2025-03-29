import requests
import urllib3
# Suppress only the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxAPI:
    def __init__(self, host, user, token_id, token_secret, node):
        self.host = host
        self.user = user
        self.token_id = token_id
        self.token_secret = token_secret
        self.node = node
        self.base_url = f"https://{host}:8006/api2/json"
        self.auth_header = {
            "Authorization": f"PVEAPIToken={user}!{token_id}={token_secret}"
        }

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_header)
        res = requests.request(method, url, headers=headers, verify=False, **kwargs)
        res.raise_for_status()
        return res.json()

    def get_next_vmid(self, starting_from=200):
        used = self._request("get", "/cluster/resources")["data"]
        used_vmids = {int(vm["vmid"]) for vm in used if vm["type"] in ["lxc", "qemu"] and "vmid" in vm}
        while starting_from in used_vmids:
            starting_from += 1
        return starting_from

    def create_lxc(self, vmid, params):
        data = {**params, "vmid": vmid}
        return self._request("post", f"/nodes/{self.node}/lxc", data=data)

    def start_lxc(self, vmid):
        return self._request("post", f"/nodes/{self.node}/lxc/{vmid}/status/start")

    def stop_lxc(self, vmid):
        return self._request("post", f"/nodes/{self.node}/lxc/{vmid}/status/stop")

    def delete_lxc(self, vmid):
        return self._request("delete", f"/nodes/{self.node}/lxc/{vmid}")

    def is_lxc_stopped(self, vmid):
        try:
            status = self._request("get", f"/nodes/{self.node}/lxc/{vmid}/status/current")
            return status["data"]["status"] == "stopped"
        except Exception:
            return False
