#!/usr/bin/env python3

import os
import argparse
import json
import yaml
from pathlib import Path
import subprocess

DEFAULTS = {
    "hostname": "test-container",
    "ip": "10.1.0.153",
    "cidr": "28",
    "gw": "10.1.0.145",
    "memory": 512,
    "cores": 1,
    "swap": 512,
    "rootfs": "local:8",
    "bridge": "vmbr0",
    "ostemplate": "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst",
    "password": "changeme",
    "stack": "willdafoe/dev",
    "params_file": "vm_params.yaml",
    "ansible_playbook": "playbooks/configure_container.yml"
}


def load_params_from_file(filepath):
    if not Path(filepath).exists():
        return {}
    with open(filepath, "r") as f:
        if filepath.endswith(".json"):
            return json.load(f)
        elif filepath.endswith((".yml", ".yaml")):
            return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format for params file.")


def resolve_param(key, cli_args, env, file_params):
    return getattr(cli_args, key) or env.get(f"VM_{key.upper()}") or file_params.get(key) or DEFAULTS[key]


def write_params_file(filepath, params):
    with open(filepath, "w") as f:
        if filepath.endswith(".json"):
            json.dump(params, f, indent=2)
        else:
            yaml.safe_dump(params, f)
    print(f"✅ Wrote parameters to {filepath}")


def write_main_py(params):
    net0 = f"name=eth0,bridge={params['bridge']},ip={params['ip']}/{params['cidr']},gw={params['gw']}"
    content = f"""import pulumi
from lxc_container import LXCContainer
import os
import yaml
import json

PARAMS_FILE = os.getenv("VM_PARAMS_FILE", "vm_params.yaml")
with open(PARAMS_FILE) as f:
    params = yaml.safe_load(f) if PARAMS_FILE.endswith((".yaml", ".yml")) else json.load(f)

cfg = pulumi.Config("proxmox")

vm_params = {{
    "hostname": params["hostname"],
    "ostemplate": params["ostemplate"],
    "memory": int(params["memory"]),
    "cores": int(params["cores"]),
    "swap": int(params["swap"]),
    "net0": "{net0}",
    "rootfs": params["rootfs"],
    "password": params["password"]
}}

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
"""
    with open("__main__.py", "w") as f:
        f.write(content)
    print("✅ Wrote __main__.py with Pulumi container definition")


def run_pulumi(stack):
    print(f"🚀 Running Pulumi up for stack {stack}")
    subprocess.run(["pulumi", "up", "--stack", stack, "--yes"], check=True)


def extract_ip(stack):
    result = subprocess.run(
        ["pulumi", "stack", "output", "ip_address", "--stack", stack],
        stdout=subprocess.PIPE,
        check=True
    )
    ip = result.stdout.decode().strip()
    print(f"🌐 IP address from Pulumi: {ip}")
    return ip


def write_inventory(ip, user="root"):
    with open("inventory.ini", "w") as f:
        f.write(f"[container]\n{ip} ansible_user={user} ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n")
    print("✅ Wrote inventory.ini")


def run_ansible(playbook):
    print(f"🧪 Running Ansible playbook: {playbook}")
    subprocess.run(["ansible-playbook", "-i", "inventory.ini", playbook], check=True)


def main():
    parser = argparse.ArgumentParser()
    for key in DEFAULTS:
        parser.add_argument(f"--{key}")
    parser.add_argument("--no-deploy", action="store_true")
    parser.add_argument("--run-ansible", action="store_true")
    args = parser.parse_args()

    file_params = load_params_from_file(args.params_file or DEFAULTS["params_file"])
    env = os.environ

    # Merge all param sources
    final = {k: resolve_param(k, args, env, file_params) for k in DEFAULTS}

    # Write files
    write_params_file(final["params_file"], final)
    write_main_py(final)

    # Run Pulumi
    if not args.no_deploy:
        run_pulumi(final["stack"])

    # Run Ansible
    if args.run_ansible:
        ip = extract_ip(final["stack"])
        write_inventory(ip)
        run_ansible(final["ansible_playbook"])


if __name__ == "__main__":
    main()
