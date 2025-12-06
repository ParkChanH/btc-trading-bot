#!/bin/bash
# Automated Stock Data Update Script

cd /Users/parkch/Documents/주식/stock_analysis
source venv/bin/activate

echo "[$(date)] Starting data collection..."
python3 create_complete_daily_prices.py >> logs/data_collection.log 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date)] Data collection completed successfully"
else
    echo "[$(date)] ERROR: Data collection failed" >&2
    exit 1
fi
