import pulumi
from pulumi.dynamic import ResourceProvider, Resource, CreateResult, DiffResult, UpdateResult
from proxmox_api import ProxmoxAPI


class LXCProvider(ResourceProvider):
    def create(self, props):
        # Force sanitize numeric values
        params = props["params"].copy()

        for key in ["vmid", "memory", "cores", "swap"]:
            if key in params:
                try:
                    params[key] = int(float(params[key]))
                except (ValueError, TypeError):
                    raise Exception(f"Parameter '{key}' must be castable to integer, got: {params[key]}")

        vmid = int(float(props["vmid"]))

        api = ProxmoxAPI(
            host=props["host"],
            user=props["user"],
            token_id=props["token_id"],
            token_secret=props["token_secret"],
            node=props["node"]
        )

        pulumi.log.info(f"Creating LXC container {vmid} on node {props['node']}")
        api.create_lxc(vmid, params)
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
        pulumi.log.info(f"Deleting LXC container {vmid} from node {props['node']}")
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
        pulumi.log.warn("Updates are not implemented. Container will be replaced if changes are detected.")
        return UpdateResult(outs=news)


class LXCContainer(Resource):
    def __init__(self, name, vmid, host, user, token_id, token_secret, node, params, opts=None):
        super().__init__(LXCProvider(), name, {
            "vmid": vmid,
            "host": host,
            "user": user,
            "token_id": token_id,
            "token_secret": token_secret,
            "node": node,
            "params": params,
        }, opts)
