#!/bin/bash
# fresh_start.sh

echo "🚀 Initiating Total Fresh Start Protocol..."

# 1. Wipe Database
echo "🧹 Wiping Database..."
docker exec remastered_db psql -U admin -d remastered_core -c "TRUNCATE TABLE active_positions, intelligence_logs;"

# 2. Hard Restart by Container Name
echo "🔄 Hard Restarting Containers..."
# Stop and Start by container name to be 100% sure
docker restart bot_official
docker restart glomeriato_dashboard

echo "✅ System reset complete. Monitoring logs..."

# 3. Follow logs
docker logs -f bot_official
