#!/bin/bash
# relaunch.sh - Glomeriato onDev Deployment

# 1. Physical Folder Setup
mkdir -p backups/intelligence backups/transactions scripts
sudo chown -R $USER:$USER backups scripts
chmod +x scripts/backup_manager.sh

echo "🚀 Deploying to onDev branch..."

# 2. Branching & Commitment
git checkout -b onDev 2>/dev/null || git checkout onDev
git add .
git commit -m "V0.1 Dev: Implemented 1-10 descending numbered backup rotation"

# 3. Launch
docker compose --profile official up -d --build bot_official glomeriato_dashboard

# 4. Trigger the first rotation
echo "💾 Initializing first numbered rotation..."
sleep 3
docker exec bot_official bash /app/scripts/backup_manager.sh

echo "✅ Deployment Successful. View your latest backup at ./backups/intelligence/backup_1_*"
