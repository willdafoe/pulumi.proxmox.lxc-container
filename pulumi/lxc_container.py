import pulumi
from pulumi.dynamic import Resource, ResourceProvider, CreateResult, DiffResult, UpdateResult
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

        vmid = props.get("vmid") or api.get_next_vmid(starting_from=200)
        props["vmid"] = vmid

        # Normalize numeric values
        params = props["params"].copy()
        for key in ["memory", "cores", "swap"]:
            if key in params:
                params[key] = int(float(params[key]))

        pulumi.log.info(f"Creating LXC container {vmid} on node {props['node']}")
        api.create_lxc(vmid, params)

        pulumi.log.info(f"Starting LXC container {vmid}...")
        api.start_lxc(vmid)

        return CreateResult(
            id_=f"{props['node']}-{vmid}",
            outs={
                **props,
                "vmid": vmid,
                "hostname": params.get("hostname"),
                "ip_address": None  # Set post-deploy via Ansible
            }
        )

    def delete(self, id, props):
        api = ProxmoxAPI(
            host=props["host"],
            user=props["user"],
            token_id=props["token_id"],
            token_secret=props["token_secret"],
            node=props["node"]
        )
        vmid = int(props["vmid"])

        # Stop container before deletion
        if not api.is_lxc_stopped(vmid):
            pulumi.log.info(f"Stopping container {vmid} before deletion...")
            api.stop_lxc(vmid)
            for _ in range(30):
                if api.is_lxc_stopped(vmid):
                    break
                time.sleep(2)

        pulumi.log.info(f"Deleting container {vmid}")
        api.delete_lxc(vmid)

    def diff(self, id, olds, news):
        replace_keys = ["vmid", "host", "user", "token_id", "token_secret", "node", "params"]
        changes = [key for key in replace_keys if olds.get(key) != news.get(key)]
        return DiffResult(changes=bool(changes), replaces=changes)

    def update(self, id, olds, news):
        pulumi.log.warn("Updates not supported — container will be replaced.")
        return UpdateResult(outs=news)


class LXCContainer(Resource):
    hostname: pulumi.Output[str]
    ip_address: pulumi.Output[str]
    vmid: pulumi.Output[int]
    node: pulumi.Output[str]

    def __init__(self, name, vmid, host, user, token_id, token_secret, node, params, opts=None):
        super().__init__(LXCProvider(), name, {
            "vmid": vmid,
            "host": host,
            "user": user,
            "token_id": token_id,
            "token_secret": token_secret,
            "node": node,
            "params": params,
            "hostname": params.get("hostname"),
            "ip_address": None,
        }, opts)
