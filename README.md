🐍 Pulumi Proxmox LXC (Python Runtime)

Manage LXC containers on a Proxmox VE host using Pulumi, with full support for static IP assignment, dynamic configuration, and flexible bootstrapping.

🚀 Features

🔒 API Token authentication (no passwords!)
⚙️ Create, Start, Stop, Delete LXC containers
📡 Static IP and DHCP support via net0
🔁 Auto-assign or manually specify VMID
🧠 Intelligent IP wait + retry before Ansible
🛠 Accept VM configuration via:
✅ CLI arguments
✅ Environment variables
✅ YAML/JSON config files
📤 Pulumi exports: vmid, hostname, node, ip_address
🧪 Optional Ansible integration post-deploy
🧹 Automatic inventory file generation
📦 Requirements

🧠 Proxmox VE host with API token access
🐍 Python 3.8+
🧰 Pulumi CLI
🔐 Proxmox user + token with permissions (see ansible/ role)
🔐 Pulumi Config Setup

pulumi config set proxmox:host 10.1.0.148
pulumi config set proxmox:user cicd@pve
pulumi config set proxmox:token_id cicd
pulumi config set --secret proxmox:token_secret your-token-secret
pulumi config set proxmox:node hades
🧠 Usage Options

🔨 1. Use the Typer CLI (Recommended)
Generate, deploy, and run Ansible in one shot:

./cli.py deploy --run-ansible
Or customize it:

./cli.py deploy --params-file pulumi/vm_params.yaml
Update outputs or destroy:

./cli.py outputs
./cli.py destroy
📦 Example vm_params.yaml
hostname: redis01
ip: 10.1.0.123
cidr: 24
gw: 10.1.0.1
memory: 1024
cores: 2
swap: 512
rootfs: local:8
ostemplate: local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst
bridge: vmbr0
password: changeme
🧱 2. Manual Makefile Deployment
make install     # install Python + Pulumi deps
make up          # run Pulumi deployment
make destroy     # nuke it from orbit
📁 Project Structure

File / Dir	Description
pulumi/__main__.py	Dynamically generated deployment script
pulumi/lxc_container.py	Dynamic Pulumi provider for LXC
pulumi/proxmox_api.py	Token-authenticated API client
pulumi/bootstrap.py	Generate config + deploy Pulumi stack
pulumi/cli.py	Typer-based CLI for full control
pulumi/vm_params.yaml	Input file for container settings
ansible/site.yml	Post-deploy configuration (e.g. UniFi)
ansible/roles/	Ansible roles (e.g. unifi.controller)
ansible/inventory.ini	Dynamically written by CLI
💡 Optional Stack File: Pulumi.dev.yaml

config:
  proxmox:host: 10.1.0.148
  proxmox:user: cicd@pve
  proxmox:token_id: cicd
  proxmox:node: hades
  proxmox:token_secret:
    secure: <your-encrypted-token>
🧼 Clean Up

./cli.py destroy
pulumi stack rm willdafoe/dev
🧪 Coming Soon?

🔄 LXC snapshotting support
💣 Chaos testing hooks
☁️ QEMU VM support
🔗 Pre/Post hook automation
🧭 GUI frontend for multi-container orchestration
LXC: Lean, Clean, Container Machine. 🐧
Proxmox + Pulumi + Python = Pure Power.