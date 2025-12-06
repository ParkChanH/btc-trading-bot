#!/usr/bin/env python3
"""
Performance Tracking Script
Tracks recommendation performance over time
"""

import pandas as pd
import os
from datetime import datetime

def track_performance():
    """Track and update recommendation performance"""
    
    # Check if analysis results exist
    if not os.path.exists('wave_transition_analysis_results.csv'):
        print("Error: Analysis results not found. Run analysis2.py first.")
        return
    
    # Load current analysis
    current_df = pd.read_csv('wave_transition_analysis_results.csv', dtype={'ticker': str})
    current_df['ticker'] = current_df['ticker'].apply(lambda x: str(x).zfill(6))
    
    # Load or create history
    if os.path.exists('recommendation_history.csv'):
        history_df = pd.read_csv('recommendation_history.csv', dtype={'ticker': str})
        history_df['ticker'] = history_df['ticker'].apply(lambda x: str(x).zfill(6))
    else:
        history_df = pd.DataFrame()
    
    # Add current recommendations to history
    current_df['recommendation_date'] = datetime.now().strftime('%Y-%m-%d')
    
    if history_df.empty:
        history_df = current_df.copy()
    else:
        # Only keep top grades (S, A) in history
        new_recs = current_df[current_df['investment_grade'].isin(['S', 'A'])].copy()
        history_df = pd.concat([history_df, new_recs], ignore_index=True)
    
    # Remove duplicates (keep latest)
    history_df = history_df.drop_duplicates(subset=['ticker'], keep='last')
    
    # Save updated history
    history_df.to_csv('recommendation_history.csv', index=False)
    
    print(f"Performance tracking updated. {len(history_df)} stocks in history.")

if __name__ == '__main__':
    track_performance()
