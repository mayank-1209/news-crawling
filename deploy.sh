#!/bin/bash

set -e


# ==========================
# CONFIGURATION
# ==========================

EC2_USER="mayank"
EC2_IP="13.200.12.231"

REMOTE_DIR="/home/mayank/web-scrapping"

KEY_PATH="$HOME/.ssh/id_ed25519"

ARCHIVE="/tmp/deployment.tar.gz"


# ==========================
# SSH AGENT SETUP
# ==========================

echo "🔑 Starting SSH Agent..."

eval "$(ssh-agent -s)" > /dev/null


if ! ssh-add -l 2>/dev/null | grep -q "id_ed25519"; then
    echo "➕ Adding SSH key..."
    ssh-add "$KEY_PATH"
fi


# ==========================
# CREATE DEPLOYMENT PACKAGE
# ==========================

echo "🚀 Creating deployment package..."

rm -f "$ARCHIVE"


PROJECT_DIR="$(pwd)"


tar \
    --exclude=".git" \
    --exclude=".github" \
    --exclude="myenv" \
    --exclude=".venv" \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude=".pytest_cache" \
    --exclude=".mypy_cache" \
    --exclude=".idea" \
    --exclude=".vscode" \
    --exclude=".env.local" \
    --exclude=".env" \
    --exclude="*.pyc" \
    --exclude="*.pyo" \
    --exclude="*.log" \
    --exclude="deployment.tar.gz" \
    -czf "$ARCHIVE" \
    -C "$PROJECT_DIR" .


echo "✅ Package created:"
ls -lh "$ARCHIVE"



# ==========================
# UPLOAD TO EC2
# ==========================

echo "📤 Uploading package to EC2..."


scp \
    -o StrictHostKeyChecking=no \
    "$ARCHIVE" \
    "$EC2_USER@$EC2_IP:$REMOTE_DIR/deployment.tar.gz"


echo "✅ Upload completed"



# ==========================
# DEPLOY ON SERVER
# ==========================

echo "🐳 Deploying on EC2..."


ssh \
    -o StrictHostKeyChecking=no \
    "$EC2_USER@$EC2_IP" <<EOF


set -e


cd "$REMOTE_DIR"


echo "📦 Extracting deployment package..."

tar -xzf deployment.tar.gz


rm -f deployment.tar.gz



echo "🐳 Restarting Docker containers..."


docker compose down

docker compose up -d --build



echo "🧹 Removing unused Docker images..."

docker image prune -f



echo "✅ Server deployment finished"


EOF



# ==========================
# CLEAN LOCAL FILE
# ==========================

echo "🧹 Cleaning local package..."

rm -f "$ARCHIVE"



echo "🎉 Deployment completed successfully!"