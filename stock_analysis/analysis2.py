#!/usr/bin/env python3
"""
Wave Theory Stock Analysis Script
Generates investment recommendations based on Wave Theory and technical indicators
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_price_data():
    """Load price data from CSV"""
    if not os.path.exists('daily_prices.csv'):
        print("Warning: daily_prices.csv not found. Creating sample data...")
        return create_sample_data()
    
    df = pd.read_csv('daily_prices.csv', dtype={'ticker': str})
    df['ticker'] = df['ticker'].apply(lambda x: str(x).zfill(6))
    df['date'] = pd.to_datetime(df['date'])
    return df

def create_sample_data():
    """Create sample data for demonstration"""
    np.random.seed(42)
    tickers = ['005930', '000660', '035720', '051910', '035420', '068270', '207940', '005380', '006400', '105560']
    names = ['삼성전자', 'SK하이닉스', '카카오', 'LG화학', 'NAVER', '셀트리온', '삼성바이오로직스', '현대차', '삼성SDI', 'KB금융']
    
    data = []
    base_date = datetime.now() - timedelta(days=365*2)
    
    for ticker, name in zip(tickers, names):
        price = np.random.uniform(10000, 100000)
        for i in range(500):
            date = base_date + timedelta(days=i)
            price = price * (1 + np.random.uniform(-0.03, 0.03))
            volume = np.random.randint(1000000, 10000000)
            data.append({
                'ticker': ticker,
                'name': name,
                'date': date.strftime('%Y-%m-%d'),
                'close': price,
                'volume': volume
            })
    
    df = pd.DataFrame(data)
    df.to_csv('daily_prices.csv', index=False)
    return df

def calculate_wave_stage(prices):
    """Simplified Wave Theory calculation"""
    if len(prices) < 60:
        return 'Unknown', 0.5
    
    ma20 = prices.rolling(20).mean().iloc[-1]
    ma60 = prices.rolling(60).mean().iloc[-1]
    current = prices.iloc[-1]
    
    # Determine trend
    if current > ma20 > ma60:
        wave = 'Wave 1-2 (상승 초기)'
        score = 0.9
    elif current > ma20 and ma20 < ma60:
        wave = 'Wave 3 (상승 중기)'
        score = 0.85
    elif current < ma20 and ma20 > ma60:
        wave = 'Wave 4 (조정)'
        score = 0.6
    else:
        wave = 'Wave 5 (하락)'
        score = 0.3
    
    return wave, score

def calculate_supply_demand(volumes, prices):
    """Calculate supply/demand stage"""
    if len(volumes) < 20:
        return 'Unknown', 0.5
    
    recent_vol = volumes.iloc[-5:].mean()
    avg_vol = volumes.iloc[-20:].mean()
    price_chg = (prices.iloc[-1] / prices.iloc[-20] - 1) * 100
    
    if recent_vol > avg_vol * 1.2 and price_chg > 0:
        return '수요 증가', 0.9
    elif recent_vol > avg_vol * 1.2 and price_chg < 0:
        return '공급 과잉', 0.3
    elif recent_vol < avg_vol * 0.8:
        return '관망세', 0.5
    else:
        return '균형', 0.7

def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return 0.5  # Default neutral score
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Avoid division by zero
    loss = loss.replace(0, 0.0001)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = rsi.iloc[-1]
    
    # Convert RSI to score (0-1)
    # RSI 30-70: normal (0.5-0.7)
    # RSI >70: overbought (0.3-0.5)
    # RSI <30: oversold (0.8-1.0, good buy opportunity)
    if current_rsi < 30:
        score = 0.9
    elif current_rsi < 40:
        score = 0.8
    elif current_rsi > 70:
        score = 0.4
    elif current_rsi > 60:
        score = 0.6
    else:
        score = 0.7
    
    return score

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    if len(prices) < slow + signal:
        return 0.5  # Default neutral score
    
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    
    # Positive MACD crossover = bullish
    # Negative MACD crossover = bearish
    if current_macd > current_signal and current_macd > 0:
        score = 0.9  # Strong buy signal
    elif current_macd > current_signal:
        score = 0.7  # Buy signal
    elif current_macd < current_signal and current_macd < 0:
        score = 0.3  # Strong sell signal
    else:
        score = 0.5  # Neutral
    
    return score

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands position"""
    if len(prices) < period:
        return 0.5  # Default neutral score
    
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    current_price = prices.iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    
    # Price position within bands
    # Near lower band = oversold = good buy
    # Near upper band = overbought = caution
    band_width = current_upper - current_lower
    if band_width == 0:
        return 0.5
        
    position = (current_price - current_lower) / band_width
    
    # Convert position to score
    if position < 0.2:
        score = 0.9  # Very oversold, excellent buy
    elif position < 0.4:
        score = 0.8  # Oversold, good buy
    elif position > 0.8:
        score = 0.4  # Overbought, caution
    elif position > 0.6:
        score = 0.6  # Approaching overbought
    else:
        score = 0.7  # Normal range
    
    return score

def calculate_technical_indicators(prices):
    """Calculate RSI, MACD, Bollinger Bands, and other technical indicators"""
    scores = []
    
    # RSI Score
    rsi_score = calculate_rsi(prices)
    scores.append(rsi_score)
    
    # MACD Score  
    macd_score = calculate_macd(prices)
    scores.append(macd_score)
    
    # Bollinger Bands Score
    bb_score = calculate_bollinger_bands(prices)
    scores.append(bb_score)
    
    # Simple momentum (keep for additional confirmation)
    if len(prices) >= 20:
        momentum = (prices.iloc[-1] / prices.iloc[-20] - 1) * 100
        if momentum > 5:
            scores.append(0.8)
        elif momentum > 0:
            scores.append(0.6)
        else:
            scores.append(0.4)
    
    # Volatility (keep for risk assessment)
    if len(prices) >= 20:
        volatility = prices.iloc[-20:].std() / prices.iloc[-20:].mean()
        if volatility < 0.05:
            scores.append(0.7)
        else:
            scores.append(0.5)
    
    return np.mean(scores) if scores else 0.5

def assign_grade(score):
    """Assign investment grade based on score"""
    if score >= 0.8:
        return 'S'
    elif score >= 0.7:
        return 'A'
    elif score >= 0.6:
        return 'B'
    elif score >= 0.5:
        return 'C'
    else:
        return 'D'

def analyze_stocks():
    """Main analysis function"""
    print("Loading price data...")
    df = load_price_data()
    
    print("Analyzing stocks...")
    results = []
    
    for ticker in df['ticker'].unique():
        stock_data = df[df['ticker'] == ticker].sort_values('date')
        
        if len(stock_data) < 60:
            continue
        
        ticker_code = stock_data['ticker'].iloc[0]
        name = stock_data['name'].iloc[0]
        prices = stock_data['close']
        volumes = stock_data['volume']
        
        # Calculate metrics
        wave_stage, wave_score = calculate_wave_stage(prices)
        sd_stage, sd_score = calculate_supply_demand(volumes, prices)
        tech_score = calculate_technical_indicators(prices)
        
        # Calculate 20-day price change
        price_20d_ago = prices.iloc[-20] if len(prices) >= 20 else prices.iloc[0]
        price_change_20d = (prices.iloc[-1] - price_20d_ago) / price_20d_ago
        
        # Final score
        final_score = (wave_score * 0.4 + sd_score * 0.3 + tech_score * 0.3)
        grade = assign_grade(final_score)
        
        results.append({
            'ticker': ticker_code,
            'name': name,
            'current_price': prices.iloc[-1],
            'wave_stage': wave_stage,
            'supply_demand_stage': sd_stage,
            'final_investment_score': final_score,
            'investment_grade': grade,
            'price_change_20d': price_change_20d,
            'institutional_trend': 'N/A',
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('final_investment_score', ascending=False)
    results_df.to_csv('wave_transition_analysis_results.csv', index=False)
    
    print(f"\nAnalysis complete! {len(results)} stocks analyzed.")
    print(f"Results saved to wave_transition_analysis_results.csv")
    print(f"\nTop 5 Recommendations:")
    print(results_df[['name', 'ticker', 'investment_grade', 'final_investment_score']].head())

if __name__ == '__main__':
    analyze_stocks()
