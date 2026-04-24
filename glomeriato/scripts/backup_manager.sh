#!/bin/bash
# scripts/backup_manager.sh - Robust 10-cycle Rotation

BASE_DIR="/app/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)

echo "🔄 Rotating Numbered Backups (Limit: 10) at $TIMESTAMP..."

rotate_logic() {
    local folder=$1
    mkdir -p "$BASE_DIR/$folder"
    
    # 1. Remove the oldest backup (10)
    rm -f "$BASE_DIR/$folder/backup_10_"* 2>/dev/null
    
    # 2. Shift 1-9 to 2-10 with robust matching
    for i in {9..1}; do
        # Use a wildcard to find any file starting with backup_i_
        local old_file=$(ls "$BASE_DIR/$folder/backup_${i}_"* 2>/dev/null | head -n 1)
        if [ -f "$old_file" ]; then
            # Extract only the timestamp part (everything after the second underscore)
            local old_ts=$(basename "$old_file" | cut -d'_' -f3-)
            mv "$old_file" "$BASE_DIR/$folder/backup_$(($i + 1))_$old_ts"
        fi
    done
}

# Intelligence Logs
rotate_logic "intelligence"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "COPY (SELECT * FROM intelligence_logs) TO STDOUT WITH CSV HEADER" > "$BASE_DIR/intelligence/backup_1_$TIMESTAMP.csv"

# Transaction History
rotate_logic "transactions"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "COPY (SELECT * FROM transaction_history) TO STDOUT WITH CSV HEADER" > "$BASE_DIR/transactions/backup_1_$TIMESTAMP.csv"

# Market Summaries
rotate_logic "summaries"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "COPY (SELECT * FROM market_summaries) TO STDOUT WITH CSV HEADER" > "$BASE_DIR/summaries/backup_1_$TIMESTAMP.csv"

echo "✅ Backup Cycle Complete."
