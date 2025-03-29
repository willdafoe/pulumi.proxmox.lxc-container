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
    "params_file": "vm_params.yaml"
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


def main():
    parser = argparse.ArgumentParser()
    for key in DEFAULTS:
        parser.add_argument(f"--{key}")
    parser.add_argument("--no-deploy", action="store_true")
    args = parser.parse_args()

    file_params = load_params_from_file(args.params_file or DEFAULTS["params_file"])
    env = os.environ

    # Merge values
    final = {k: resolve_param(k, args, env, file_params) for k in DEFAULTS}

    # Write merged params to file for __main__.py to use
    params_file = args.params_file or DEFAULTS["params_file"]
    write_params_file(params_file, final)

    if not args.no_deploy:
        print(f"🚀 Running: pulumi up --stack {final['stack']} --yes")
        subprocess.run(["pulumi", "up", "--stack", final["stack"], "--yes"], check=True)


if __name__ == "__main__":
    main()