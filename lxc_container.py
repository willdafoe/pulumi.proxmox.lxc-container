import pulumi
from pulumi.dynamic import ResourceProvider, Resource, CreateResult, DiffResult, UpdateResult
from proxmox_api import ProxmoxAPI


class LXCProvider(ResourceProvider):
    def create(self, props):
        api = ProxmoxAPI(
            host=props["host"],
            user=props["user"],
            token_id=props["token_id"],
            token_secret=props["token_secret"],
            node=props["node"]
        )

        # Auto-assign vmid if not provided
        if "vmid" in props and props["vmid"] is not None:
            vmid = int(float(props["vmid"]))
        else:
            vmid = api.get_next_vmid(starting_from=200)
            props["vmid"] = vmid

        # Normalize numeric params
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
