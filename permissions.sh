#!/usr/bin/env bash

set -euo pipefail

# 🔧 CONFIGURATION
PROXMOX_HOST="10.1.0.148"
ROOT_USER="root@pam"
ROOT_PASSWORD="changeme"  # Load from ENV or prompt for security
NEW_USER="cicd@pve"
TOKEN_ID="cicd"
ROLE="PVEVMAdmin"
PERM_PATH="/vms"
REAL_NAME="CI/CD Automation User"

echo "🔐 Authenticating as ${ROOT_USER}..."
AUTH_RESPONSE=$(curl -sk \
  -d "username=${ROOT_USER}&password=${ROOT_PASSWORD}" \
  https://${PROXMOX_HOST}:8006/api2/json/access/ticket)

TICKET=$(echo "$AUTH_RESPONSE" | jq -r '.data.ticket')
CSRF_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.data.CSRFPreventionToken')

AUTH_HEADER=(
  -b "PVEAuthCookie=$TICKET"
  -H "CSRFPreventionToken: $CSRF_TOKEN"
)

# 👤 Create user if not exists
echo "👤 Creating user ${NEW_USER} (if needed)..."
curl -sk "${AUTH_HEADER[@]}" -X POST "https://${PROXMOX_HOST}:8006/api2/json/access/users" \
  -d "userid=${NEW_USER}&enable=1&comment=${REAL_NAME}" || echo "🔁 User may already exist."

# 🔑 Create API token and capture secret
echo "🔑 Creating token ${NEW_USER}!${TOKEN_ID}..."
TOKEN_RESPONSE=$(curl -sk "${AUTH_HEADER[@]}" -X POST \
  "https://${PROXMOX_HOST}:8006/api2/json/access/users/${NEW_USER//\@/%40}/token" \
  -d "tokenid=${TOKEN_ID}&privsep=0" || true)

TOKEN_SECRET=$(echo "$TOKEN_RESPONSE" | jq -r '.data.value // empty')

if [[ -n "$TOKEN_SECRET" ]]; then
  echo -e "\n✅ Token created successfully:"
  echo "Token ID    : ${NEW_USER}!${TOKEN_ID}"
  echo "Token Secret: ${TOKEN_SECRET}"
else
  echo -e "\n⚠️  Token likely already exists. Secret cannot be retrieved again."
  echo "To rotate it, delete and re-create the token."
fi

# 🛡 Assign role
echo "🛡 Assigning role '${ROLE}' to ${NEW_USER} on '${PERM_PATH}'..."
curl -sk "${AUTH_HEADER[@]}" -X PUT \
  "https://${PROXMOX_HOST}:8006/api2/json/access/acl" \
  -d "path=${PERM_PATH}&users=${NEW_USER}&roles=${ROLE}"

echo -e "\n🚀 Done."
