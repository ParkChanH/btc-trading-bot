#!/usr/bin/env python3
"""
Data Collection Script for Korean Stocks
Fetches historical price data from Yahoo Finance
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Top 50 KOSPI stocks by market cap (manually curated for reliability)
KOREAN_STOCKS = {
    # Top 15 (기존)
    '005930': ('삼성전자', '005930.KS'),
    '000660': ('SK하이닉스', '000660.KS'),
    '005380': ('현대차', '005380.KS'),
    '051910': ('LG화학', '051910.KS'),
    '006400': ('삼성SDI', '006400.KS'),
    '035720': ('카카오', '035720.KS'),
    '035420': ('NAVER', '035420.KS'),
    '068270': ('셀트리온', '068270.KS'),
    '207940': ('삼성바이오로직스', '207940.KS'),
    '105560': ('KB금융', '105560.KS'),
    '012330': ('현대모비스', '012330.KS'),
    '055550': ('신한지주', '055550.KS'),
    '028260': ('삼성물산', '028260.KS'),
    '066570': ('LG전자', '066570.KS'),
    '003670': ('포스코퓨처엠', '003670.KS'),
    # Top 16-50 (추가)
    '000270': ('기아', '000270.KS'),
    '003550': ('LG', '003550.KS'),
    '096770': ('SK이노베이션', '096770.KS'),
    '034730': ('SK', '034730.KS'),
    '009150': ('삼성전기', '009150.KS'),
    '017670': ('SK텔레콤', '017670.KS'),
    '033780': ('KT&G', '033780.KS'),
    '000810': ('삼성화재', '000810.KS'),
    '005490': ('POSCO홀딩스', '005490.KS'),
    '032830': ('삼성생명', '032830.KS'),
    '086790': ('하나금융지주', '086790.KS'),
    '005830': ('DB손해보험', '005830.KS'),
    '323410': ('카카오뱅크', '323410.KS'),
    '018260': ('삼성에스디에스', '018260.KS'),
    '000100': ('유한양행', '000100.KS'),
    '015760': ('한국전력', '015760.KS'),
    '009540': ('HD한국조선해양', '009540.KS'),
    '010130': ('고려아연', '010130.KS'),
    '011170': ('롯데케미칼', '011170.KS'),
    '010950': ('S-Oil', '010950.KS'),
    '047810': ('한국항공우주', '047810.KS'),
    '011200': ('HMM', '011200.KS'),
    '024110': ('기업은행', '024110.KS'),
    '090430': ('아모레퍼시픽', '090430.KS'),
    '078930': ('GS', '078930.KS')}

def get_top_kospi_stocks(count=None):
    """Get a curated list of top KOSPI stocks."""
    print(f"Using a curated list of {len(KOREAN_STOCKS)} KOSPI stocks.")
    stocks = []
    for ticker, (name, yahoo_ticker) in KOREAN_STOCKS.items():
        stocks.append((ticker, name, yahoo_ticker))
    
    if count and count < len(stocks):
        stocks = stocks[:count]
        print(f"Limiting to top {count} stocks from the curated list.")

    print(f"✓ Found {len(stocks)} stocks")
    return stocks

def fetch_stock_data(ticker, yahoo_ticker, name, period='2y'):
    """Fetch historical data for a single stock"""
    try:
        stock = yf.Ticker(yahoo_ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            print(f"No data for {name} ({ticker})")
            return pd.DataFrame()
        
        hist = hist.reset_index()
        hist['ticker'] = ticker
        hist['name'] = name
        hist['date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        
        # Rename columns
        hist = hist.rename(columns={
            'Close': 'close',
            'Volume': 'volume',
            'Open': 'open',
            'High': 'high',
            'Low': 'low'
        })
        
        return hist[['ticker', 'name', 'date', 'close', 'volume', 'open', 'high', 'low']]
    
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return pd.DataFrame()

def collect_all_data():
    """Collect data for all stocks"""
    print("Fetching historical price data for Korean stocks...")
    print(f"This will fetch data for {len(KOREAN_STOCKS)} stocks (expanded from 15)")
    
    all_data = []
    
    for ticker, (name, yahoo_ticker) in tqdm(KOREAN_STOCKS.items()):
        df = fetch_stock_data(ticker, yahoo_ticker, name)
        if not df.empty:
            all_data.append(df)
        time.sleep(0.5)  # Rate limiting
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = final_df.sort_values(['ticker', 'date'])
        final_df.to_csv('daily_prices.csv', index=False)
        
        print(f"\n✓ Successfully collected {len(final_df)} price records")
        print(f"✓ Data saved to daily_prices.csv")
        print(f"✓ Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        
        # Save ticker mapping
        mapping_df = pd.DataFrame([
            {'ticker': ticker, 'yahoo_ticker': yahoo_ticker}
            for ticker, (_, yahoo_ticker) in KOREAN_STOCKS.items()
        ])
        mapping_df.to_csv('ticker_to_yahoo_map.csv', index=False)
        print(f"✓ Ticker mapping saved to ticker_to_yahoo_map.csv")
    else:
        print("× No data collected")

if __name__ == '__main__':
    collect_all_data()
