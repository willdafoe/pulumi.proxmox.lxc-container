#!/usr/bin/env python3

import subprocess
import sys

if len(sys.argv) != 3:
    print("Usage: clone_stack_config.py <source-stack> <target-stack>")
    sys.exit(1)

src_stack = sys.argv[1]
tgt_stack = sys.argv[2]

# Get config from source
result = subprocess.run(
    ["pulumi", "config", "--stack", src_stack, "--json"],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Failed to read config from stack {src_stack}:\n{result.stderr}")
    sys.exit(1)

import json
config = json.loads(result.stdout)

for key, value in config.items():
    args = ["pulumi", "config", "set", "--stack", tgt_stack]
    if value.get("secret", False):
        args.append("--secret")
    args.extend([key, value["value"]])
    subprocess.run(args)
