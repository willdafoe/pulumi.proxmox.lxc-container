import pulumi
from lxc_container import LXCContainer

cfg = pulumi.Config("proxmox")

vm_params = {
    "hostname": "test-container",
    "ostemplate": "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst",
    "memory": int(512),
    "cores": int(1),
    "swap": int(512),
    "net0": "name=eth0,bridge=vmbr0,ip=dhcp,ip6=auto",
    "rootfs": "local:8",
    "password": "changeme"
}

container = LXCContainer(
    "test",
    vmid=int(200),
    host=cfg.require("host"),
    user=cfg.require("user"),
    token_id=cfg.require("token_id"),
    token_secret=cfg.require_secret("token_secret"),
    node=cfg.require("node"),
    params=vm_params
)
