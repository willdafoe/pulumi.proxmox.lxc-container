import pulumi
from pulumi import Output
from pulumi.dynamic import ResourceProvider, Resource, CreateResult, DiffResult, UpdateResult
from proxmox_api import ProxmoxAPI
import time


class LXCProvider(ResourceProvider):
    def create(self, props):
        api = ProxmoxAPI(
            host=props["host"],
            user=props["user"],
            token_id=props["token_id"],
            token_secret=props["token_secret"],
            node=props["node"]
        )

        # Assign VMID
        if "vmid" in props and props["vmid"] is not None:
            vmid = int(float(props["vmid"]))
        else:
            vmid = api.get_next_vmid(starting_from=200)
            props["vmid"] = vmid

        # Normalize numeric values
        params = props["params"].copy()
        for key in ["memory", "cores", "swap"]:
            if key in params:
                try:
                    params[key] = int(float(params[key]))
                except (ValueError, TypeError):
                    raise Exception(f"Param '{key}' must be castable to int, got: {params[key]}")

        pulumi.log.info(f"Creating LXC container {vmid} on node {props['node']}")
        api.create_lxc(vmid, params)

        pulumi.log.info(f"Starting LXC container {vmid}...")
        api.start_lxc(vmid)

        # Extract static IP from net0 config
        net0 = params.get("net0", "")
        ip_address = None
        if "ip=" in net0:
            try:
                ip_address = net0.split("ip=")[1].split(",")[0].strip()
                pulumi.log.info(f"Static IP extracted from net0: {ip_address}")
            except Exception as e:
                pulumi.log.warn(f"Failed to extract static IP from net0: {e}")

        props["hostname"] = params.get("hostname", f"lxc-{vmid}")
        props["ip_address"] = ip_address
        props["status"] = "running"

        return CreateResult(id_=f"{props['node']}-{vmid}", outs=props)

    def delete(self, id, props):
        api = ProxmoxAPI(
            host=props["host"],
            user=props["user"],
            token_id=props["token_id"],
            token_secret=props["token_secret"],
            node=props["node"]
        )

        vmid = int(float(props["vmid"]))
        pulumi.log.info(f"Preparing to delete LXC container {vmid} on node {props['node']}")

        try:
            status = api.get_lxc_status(vmid).get("data", {})
            if status.get("status") == "running":
                pulumi.log.info(f"Stopping LXC container {vmid} before deletion...")
                api.stop_lxc(vmid)

                for _ in range(30):
                    time.sleep(1)
                    try:
                        current = api.get_lxc_status(vmid).get("data", {})
                        if current.get("status") != "running":
                            pulumi.log.info(f"LXC container {vmid} has stopped.")
                            break
                    except Exception as e:
                        pulumi.log.warn(f"Polling shutdown failed: {e}")
                else:
                    raise Exception(f"LXC container {vmid} did not stop within timeout.")
        except Exception as e:
            pulumi.log.warn(f"Failed to check or stop container {vmid} before deletion: {e}")

        pulumi.log.info(f"Deleting LXC container {vmid}")
        api.delete_lxc(vmid)

    def diff(self, id, olds, news):
        replaces = []
        for key in ["vmid", "host", "user", "token_id", "token_secret", "node"]:
            if olds.get(key) != news.get(key):
                replaces.append(key)
        if olds.get("params") != news.get("params"):
            replaces.append("params")
        return DiffResult(changes=bool(replaces), replaces=replaces)

    def update(self, id, olds, news):
        pulumi.log.warn("Update not supported. Replacing container.")
        return UpdateResult(outs=news)


class LXCContainer(Resource):
    def __init__(self, name, vmid, host, user, token_id, token_secret, node, params, opts=None):
        args = {
            "vmid": vmid,
            "host": host,
            "user": user,
            "token_id": token_id,
            "token_secret": token_secret,
            "node": node,
            "params": params,
        }

        super().__init__(LXCProvider(), name, args, opts)

        self.vmid = self.get_output("vmid")
        self.hostname = self.get_output("hostname")
        self.node = self.get_output("node")
        self.ip_address = self.get_output("ip_address")

    def get_output(self, name):
        return getattr(self, name, Output.from_input(None))
