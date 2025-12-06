#!/bin/bash
# Automated Analysis Script

cd /Users/parkch/Documents/주식/stock_analysis
source venv/bin/activate

echo "[$(date)] Starting analysis..."
python3 analysis2.py >> logs/analysis.log 2>&1

if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: Analysis failed" >&2
    exit 1
fi

echo "[$(date)] Updating performance tracking..."
python3 track_performance.py >> logs/performance.log 2>&1

echo "[$(date)] Running backtesting..."
python3 backtesting.py >> logs/backtesting.log 2>&1

echo "[$(date)] Analysis pipeline completed successfully"
