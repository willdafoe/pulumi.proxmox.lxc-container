import pulumi
from pulumi.dynamic import Resource, ResourceProvider, CreateResult, DiffResult, UpdateResult, DeleteResult
from proxmox_api import ProxmoxAPI


class LXCProvider(ResourceProvider):
    def create(self, inputs):
        api = ProxmoxAPI()
        vmid = inputs["vmid"]
        node = inputs["node"]
        params = inputs["params"]

        pulumi.log.info(f"Creating LXC container {vmid} on node {node}...")

        api.create_lxc(vmid, params)

        return CreateResult(id_=f"{node}-{vmid}", outs=inputs)

    def delete(self, id, props):
        api = ProxmoxAPI()
        vmid = props["vmid"]
        node = props["node"]

        pulumi.log.info(f"Deleting LXC container {vmid} from node {node}...")

        api.delete_lxc(vmid)

    def diff(self, id, olds, news):
        replaces = []

        if olds["vmid"] != news["vmid"]:
            replaces.append("vmid")

        if olds["node"] != news["node"]:
            replaces.append("node")

        # Optionally: deep compare 'params' and mark replacements
        if olds["params"] != news["params"]:
            replaces.append("params")

        return DiffResult(changes=bool(replaces), replaces=replaces)

    def update(self, id, olds, news):
        # In production, implement patch logic here
        pulumi.log.warn("Update not implemented; replacing container...")
        return UpdateResult(outs=news)


class LXCContainer(Resource):
    def __init__(self, name: str, vmid: int, node: str, params: dict, opts: pulumi.ResourceOptions = None):
        super().__init__(LXCProvider(), name, {
            "vmid": vmid,
            "node": node,
            "params": params
        }, opts)
