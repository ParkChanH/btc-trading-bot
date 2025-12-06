#!/usr/bin/env python3
"""
Simple Backtesting System
Tests strategy performance on historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def calculate_backtesting_metrics():
    """Calculate simple backtesting metrics from recommendation history"""
    
    try:
        # Load recommendation history
        if pd.io.common.file_exists('recommendation_history.csv'):
            history_df = pd.read_csv('recommendation_history.csv', dtype={'ticker': str})
        else:
            print("No recommendation history found yet.")
            return None
        
        # Load current analysis for price comparison
        current_df = pd.read_csv('wave_transition_analysis_results.csv', dtype={'ticker': str})
        current_df['ticker'] = current_df['ticker'].apply(lambda x: str(x).zfill(6))
        history_df['ticker'] = history_df['ticker'].apply(lambda x: str(x).zfill(6))
        
        results = []
        
        for _, hist_row in history_df.iterrows():
            ticker = hist_row['ticker']
            rec_price = float(hist_row['current_price'])
            rec_date = hist_row.get('recommendation_date', hist_row.get('analysis_date', 'Unknown'))
            grade = hist_row['investment_grade']
            
            # Find current price
            current_row = current_df[current_df['ticker'] == ticker]
            if not current_row.empty:
                current_price = float(current_row.iloc[0]['current_price'])
                
                # Calculate return
                return_pct = ((current_price - rec_price) / rec_price) * 100
                
                results.append({
                    'ticker': ticker,
                    'name': hist_row['name'],
                    'grade': grade,
                    'rec_price': rec_price,
                    'current_price': current_price,
                    'return_pct': return_pct,
                    'rec_date': rec_date
                })
        
        if not results:
            print("No backtesting data available.")
            return None
        
        results_df = pd.DataFrame(results)
        
        # Calculate metrics
        total_trades = len(results_df)
        wins = len(results_df[results_df['return_pct'] > 0])
        losses = len(results_df[results_df['return_pct'] <= 0])
        
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_return = results_df['return_pct'].mean()
        max_return = results_df['return_pct'].max()
        min_return = results_df['return_pct'].min()
        
        # Calculate by grade
        s_grade = results_df[results_df['grade'] == 'S']
        a_grade = results_df[results_df['grade'] == 'A']
        
        metrics = {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'max_return': round(max_return, 2),
            'min_return': round(min_return, 2),
            's_grade_avg_return': round(s_grade['return_pct'].mean(), 2) if len(s_grade) > 0 else 0,
            'a_grade_avg_return': round(a_grade['return_pct'].mean(), 2) if len(a_grade) > 0 else 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
       
        # Save results
        with open('backtesting_results.json', 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        print("\n=== Backtesting Results ===")
        print(f"Total Recommendations: {total_trades}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average Return: {avg_return:+.2f}%")
        print(f"Best Return: {max_return:+.2f}%")
        print(f"Worst Return: {min_return:+.2f}%")
        print(f"\nBy Grade:")
        print(f"  S Grade Avg Return: {metrics['s_grade_avg_return']:+.2f}%")
        print(f"  A Grade Avg Return: {metrics['a_grade_avg_return']:+.2f}%")
        print(f"\nResults saved to backtesting_results.json")
        
        return metrics
        
    except Exception as e:
        print(f"Error in backtesting: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    calculate_backtesting_metrics()
