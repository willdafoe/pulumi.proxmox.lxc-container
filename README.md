# 🐍 Pulumi Proxmox LXC (Python Runtime)

Manage LXC containers on a Proxmox VE host using Pulumi, with full support for static IP assignment, dynamic configuration, and flexible bootstrapping.

---

## 🚀 Features

- 🔒 Auth via API Token
- ⚙️ Create/Start/Stop/Delete LXC containers
- 📡 Static IP support with Pulumi outputs
- 🔁 Auto-assign or specify VMID
- 📥 Accept container params via:
  - CLI arguments
  - Environment variables
  - YAML or JSON config files
- 📤 Pulumi exports: `vmid`, `hostname`, `node`, `ip_address`

---

## 📦 Requirements

- 🧠 Proxmox VE host with API access and API token
- 🐍 Python 3.8+
- 🧰 Pulumi CLI
- 🔑 Proxmox user with appropriate permissions (see role setup in `ansible/`)

---

## 🔐 Pulumi Config Setup

```bash
pulumi config set proxmox:host 10.1.0.148
pulumi config set proxmox:user cicd@pve
pulumi config set proxmox:token_id cicd
pulumi config set --secret proxmox:token_secret your-token-secret
pulumi config set proxmox:node hades
```

🧠 Usage Options

🔨 1. Run Bootstrap Script (Preferred)
```bash
./bootstrap.py --hostname redis01 --ip 10.1.0.123 --gw 10.1.0.1 --stack organization/stackname
```
Or use env vars:
```bash
export VM_HOSTNAME=redis01
export VM_IP=10.1.0.123
./bootstrap.py
```
Or use a YAML config:
```bash
# vm_params.yaml
hostname: redis01
ip: 10.1.0.123
cidr: 24
gw: 10.1.0.1
memory: 1024
cores: 2
rootfs: local:8
./bootstrap.py --params-file vm_params.yaml
```
This script will:

* Generate __main__.py
* Write vm_params.yaml
* Deploy using pulumi up

🧱 2. Manual Deployment
```bash
make install     # installs Python deps
make up          # runs `pulumi up`
make destroy     # destroys the container
```

📁 Project Structure

File / Dir	Description
```bash
lxc_container.py	Dynamic Pulumi provider for LXC
proxmox_api.py	    Token-based Proxmox API wrapper
__main__.py	        Loads dynamic config from vm_params.yaml
bootstrap.py	    Bootstraps the project from CLI/env/file
vm_params.yaml	    Generated container config
```
💡 Optional Stack File: Pulumi.dev.yaml

```bash
config:
  proxmox:host: 10.1.0.148
  proxmox:user: cicd@pve
  proxmox:token_id: cicd
  proxmox:node: proxmox-node
  proxmox:token_secret:
    secure: <your-base64-encrypted-secret>
```
🧼 Clean Up
```
make destroy
```
🧪 Coming Soon?

* VM support via qemu
* Container snapshotting
* Pre/post deployment hooks (e.g. run Ansible after deploy)
* Built for controlled chaos in your homelab.

LXC: Lean, Clean, Container Machine. 🐧