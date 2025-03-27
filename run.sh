pulumi stack rm --yes --force --stack willdafoe/test && \
pulumi stack init willdafoe/dev && \
pulumi config set proxmox:host 10.1.0.148 --stack willdafoe/dev && \
pulumi config set proxmox:user cicd@pve --stack willdafoe/dev && \
pulumi config set proxmox:token_id cicd --stack willdafoe/dev && \
pulumi config set --secret proxmox:token_secret 2d397a27-9f5e-46b6-b46b-9b41a7f01e58 && \
pulumi config set proxmox:node hades
