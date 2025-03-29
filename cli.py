#!/usr/bin/env python3

import os
import subprocess
import json
import yaml
import typer
import time
from pathlib import Path
import sys

# === Project Structure ===
REPO_ROOT = Path(__file__).resolve().parent
PULUMI_DIR = REPO_ROOT / "pulumi"
ANSIBLE_DIR = REPO_ROOT / "ansible"
INVENTORY_FILE = ANSIBLE_DIR / "inventory.ini"  # 🔥 moved here

sys.path.insert(0, str(PULUMI_DIR))
app = typer.Typer(help="Pulumi LXC Deployment CLI")

# === Defaults ===
DEFAULTS = {
    "params_file": PULUMI_DIR / "vm_params.yaml",
    "stack": "willdafoe/dev",
    "ansible_playbook": ANSIBLE_DIR / "site.yml",
    "ansible_user": "root"
}


# === Helpers ===

def load_params(path: Path):
    with open(path) as f:
        return yaml.safe_load(f) if path.suffix in [".yaml", ".yml"] else json.load(f)


def write_inventory(ip: str, user: str, path: Path = INVENTORY_FILE):
    content = f"[container]\n{ip} ansible_user={user} ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n"
    path.write_text(content)
    typer.echo(f"✅ Wrote inventory to {path}")


def wait_for_ip(stack: str, retries: int = 6, delay: int = 5) -> str:
    for attempt in range(retries):
        typer.echo(f"⏳ Waiting for container IP (attempt {attempt + 1}/{retries})...")
        result = subprocess.run(
            ["pulumi", "stack", "output", "ip_address", "--stack", stack],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        ip = result.stdout.decode().strip()
        if ip and ip.lower() != "null":
            typer.echo(f"🌐 Detected IP: {ip}")
            return ip
        time.sleep(delay)
    typer.secho("❌ Failed to detect IP address from Pulumi outputs in time.", fg=typer.colors.RED)
    raise typer.Exit(1)


# === Commands ===

@app.command()
def generate(params_file: Path = DEFAULTS["params_file"]):
    """Generate Pulumi __main__.py from a params YAML/JSON file."""
    params = load_params(params_file)
    net0 = f"name=eth0,bridge={params['bridge']},ip=dhcp"
    main_path = PULUMI_DIR / "__main__.py"

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
    main_path.write_text(content)
    typer.echo(f"✅ Wrote {main_path.relative_to(REPO_ROOT)}")


@app.command()
def deploy(
    stack: str = DEFAULTS["stack"],
    params_file: Path = DEFAULTS["params_file"],
    run_ansible: bool = typer.Option(False, "--run-ansible", help="Run Ansible after deployment"),
):
    """Run Pulumi deployment and optionally run Ansible."""
    generate(params_file=params_file)
    typer.echo(f"🚀 Deploying stack {stack}")
    subprocess.run(["pulumi", "up", "--stack", stack, "--yes"], cwd=PULUMI_DIR, check=True)

    if run_ansible:
        ip = wait_for_ip(stack)
        write_inventory(ip, DEFAULTS["ansible_user"])
        subprocess.run(["ansible-playbook", "-i", str(INVENTORY_FILE), str(DEFAULTS["ansible_playbook"])], check=True)


@app.command()
def destroy(stack: str = DEFAULTS["stack"]):
    """Destroy the Pulumi stack."""
    typer.confirm(f"Destroy stack {stack}?", abort=True)
    subprocess.run(["pulumi", "destroy", "--stack", stack, "--yes"], cwd=PULUMI_DIR, check=True)


@app.command()
def outputs(stack: str = DEFAULTS["stack"]):
    """Show Pulumi outputs for the given stack."""
    subprocess.run(["pulumi", "stack", "output", "--stack", stack], cwd=PULUMI_DIR)


# === Entry Point ===

if __name__ == "__main__":
    app()
