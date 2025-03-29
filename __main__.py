import pulumi
from lxc_container import LXCContainer
import os
import yaml
import json

# Read from params file (YAML or JSON)
PARAMS_FILE = os.getenv("VM_PARAMS_FILE", "vm_params.yaml")

if PARAMS_FILE.endswith(".json"):
    with open(PARAMS_FILE) as f:
        params = json.load(f)
else:
    with open(PARAMS_FILE) as f:
        params = yaml.safe_load(f)

cfg = pulumi.Config("proxmox")

# Construct net0 with static IP info
net0 = f"name=eth0,bridge={params['bridge']},ip={params['ip']}/{params['cidr']},gw={params['gw']}"

vm_params = {
    "hostname": params["hostname"],
    "ostemplate": params["ostemplate"],
    "memory": int(params["memory"]),
    "cores": int(params["cores"]),
    "swap": int(params["swap"]),
    "net0": net0,
    "rootfs": params["rootfs"],
    "password": params["password"]
}

container = LXCContainer(
    "test",
    vmid=None,
    host=cfg.require("host"),
    user=cfg.require("user"),
    token_id=cfg.require("token_id"),
    token_secret=cfg.require_secret("token_secret"),
    node=cfg.require("node"),
    params=vm_params
)

pulumi.export("vmid", container.vmid)
pulumi.export("hostname", container.hostname)
pulumi.export("node", container.node)
pulumi.export("ip_address", container.ip_address)
