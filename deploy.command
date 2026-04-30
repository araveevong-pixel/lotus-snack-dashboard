#!/bin/bash
# LOTUS Dashboard — Deploy v2 (no gh CLI required, uses git + curl)
set -e

cd "$(dirname "$0")"
echo "=== LOTUS Dashboard Deploy v2 ==="

# Read token from existing jele-soda-dashboard repo
TOKEN_LINE=$(grep -E "ghp_|github_pat_" ../.git/config 2>/dev/null | head -1)
if [ -z "$TOKEN_LINE" ]; then
    echo "ERROR: ไม่เจอ GitHub token ใน ../.git/config"
    exit 1
fi

TOKEN=$(echo "$TOKEN_LINE" | grep -oE "(ghp_|github_pat_)[A-Za-z0-9_]+")
echo "→ Token detected: ${TOKEN:0:10}..."

# Get authenticated user
API_USER=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user | grep '"login"' | head -1 | sed 's/.*: "\(.*\)",/\1/')
if [ -z "$API_USER" ]; then
    echo "ERROR: API call failed — token หมดอายุ?"
    exit 1
fi
echo "→ Authenticated as: $API_USER"

REPO_NAME="lotus-snack-dashboard"
PAGES_URL="https://${API_USER}.github.io/${REPO_NAME}/"

# Update brand.json
python3 -c "
import json
with open('brand.json') as f: b = json.load(f)
b['github_user'] = '$API_USER'
b['repo_name'] = '$REPO_NAME'
with open('brand.json', 'w') as f: json.dump(b, f, ensure_ascii=False, indent=2)
"

# Create repo via API
echo "→ Creating repo..."
curl -s -X POST -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO_NAME\",\"public\":true,\"description\":\"LOTUS Snack 2026 KOL Marketing Dashboard\"}" \
    > /tmp/repo_resp.json

if grep -q '"name"' /tmp/repo_resp.json; then
    echo "  ✓ Repo created"
elif grep -q "already exists" /tmp/repo_resp.json; then
    echo "  ✓ Repo already exists"
fi

# Init + commit + push
[ -d .git ] || git init -b main
git config user.email "${API_USER}@users.noreply.github.com"
git config user.name "$API_USER"
git add -A
git diff --staged --quiet || git commit -m "Deploy LOTUS dashboard"
git remote remove origin 2>/dev/null || true
git remote add origin "https://${API_USER}:${TOKEN}@github.com/${API_USER}/${REPO_NAME}.git"

echo "→ Pushing..."
git push -u origin main --force

# Enable Pages
echo "→ Enabling Pages..."
curl -s -X POST -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${API_USER}/${REPO_NAME}/pages" \
    -d '{"source":{"branch":"main","path":"/"}}' > /dev/null
echo "  ✓ Pages enabled"

# Trigger workflow
echo "→ Triggering scrape..."
sleep 3
curl -s -X POST -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${API_USER}/${REPO_NAME}/actions/workflows/auto-update.yml/dispatches" \
    -d '{"ref":"main"}' > /dev/null
echo "  ✓ Workflow dispatched"

echo ""
echo "==================================================="
echo "  ✅ DEPLOY SUCCESS"
echo "==================================================="
echo "  Live:    ${PAGES_URL}"
echo "  Repo:    https://github.com/${API_USER}/${REPO_NAME}"
echo "  Actions: https://github.com/${API_USER}/${REPO_NAME}/actions"
echo "==================================================="
echo "  รอ 1-2 นาทีให้ Pages deploy"
echo ""
