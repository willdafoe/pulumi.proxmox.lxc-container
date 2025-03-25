import pulumi
from lxc_container import LXCContainer

lxc = LXCContainer(
    "test-container",
    vmid=103,
    node="proxmox-node-name",
    params={
        "hostname": "test123",
        "ostemplate": "local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz",
        "memory": 512,
        "swap": 512,
        "cores": 1,
        "rootfs": "local:8",
        "net0": "name=eth0,bridge=vmbr0,ip=dhcp,ip6=auto",
        "password": "changeme"
    }
)
