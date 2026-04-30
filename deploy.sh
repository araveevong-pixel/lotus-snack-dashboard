#!/bin/bash
# LOTUS Snack Dashboard — One-shot deploy
# Run from this folder: bash deploy.sh
set -e

cd "$(dirname "$0")"
echo "=== LOTUS Dashboard Deploy ==="

# Check gh CLI
if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found. Install: brew install gh"
    exit 1
fi

# Check auth
if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Detect github user
GH_USER=$(gh api user -q .login)
REPO_NAME="lotus-snack-dashboard"
REPO="${GH_USER}/${REPO_NAME}"
PAGES_URL="https://${GH_USER}.github.io/${REPO_NAME}/"

echo "→ GitHub user: ${GH_USER}"
echo "→ Target repo: ${REPO}"

# Update brand.json with detected user
python3 -c "
import json
with open('brand.json') as f: b = json.load(f)
b['github_user'] = '${GH_USER}'
b['repo_name'] = '${REPO_NAME}'
with open('brand.json', 'w') as f: json.dump(b, f, ensure_ascii=False, indent=2)
"

# Update README link
sed -i.bak "s|https://[a-z-]*\.github\.io/lotus-snack-dashboard|${PAGES_URL%/}|g" README.md && rm README.md.bak

# Init git if needed
[ -d .git ] || git init -b main

git add -A
git diff --staged --quiet || git commit -m "Deploy LOTUS dashboard via kol-dashboard-generator"

# Create repo if not exists
if ! gh repo view "${REPO}" >/dev/null 2>&1; then
    echo "→ Creating repo ${REPO}..."
    gh repo create "${REPO}" --public --description "LOTUS Snack 2026 KOL Marketing Dashboard"
fi

# Set/update remote
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${REPO}.git"

# Push
echo "→ Pushing files..."
git push -u origin main --force

# Enable Pages
echo "→ Enabling GitHub Pages..."
gh api -X POST "repos/${REPO}/pages" -f "build_type=legacy" -f "source[branch]=main" -f "source[path]=/" 2>/dev/null \
  || gh api -X PUT "repos/${REPO}/pages" -f "build_type=legacy" -f "source[branch]=main" -f "source[path]=/" 2>/dev/null \
  || echo "  (Pages may already be enabled)"

# Trigger workflow
echo "→ Triggering first scrape..."
sleep 3
gh workflow run auto-update.yml --repo "${REPO}" 2>/dev/null || echo "  (workflow runs on cron)"

echo ""
echo "=== Done ==="
echo "Live: ${PAGES_URL}"
echo "Repo: https://github.com/${REPO}"
echo "Wait 1-2 min for first deploy, then visit the live URL."
