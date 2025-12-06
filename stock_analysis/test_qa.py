#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Stock Analysis System
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_portfolio_api():
    """Test portfolio API endpoint"""
    print("\n=== Testing /api/portfolio ===")
    try:
        response = requests.get(f"{BASE_URL}/api/portfolio")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check market indices
        assert 'market_indices' in data, "Missing market_indices"
        assert len(data['market_indices']) > 0, "No market indices returned"
        print(f"✓ Market Indices: {len(data['market_indices'])} indices")
        
        for idx in data['market_indices']:
            assert 'name' in idx and 'price' in idx and 'change_pct' in idx
        print(f"  - Indices: {', '.join([idx['name'] for idx in data['market_indices']])}")
        
        # Check top holdings
        assert 'top_holdings' in data, "Missing top_holdings"
        assert len(data['top_holdings']) > 0, "No holdings returned"
        print(f"✓ Top Holdings: {len(data['top_holdings'])} stocks")
        
        for stock in data['top_holdings']:
            assert 'ticker' in stock and 'name' in stock and 'grade' in stock
            assert stock['grade'] in ['S', 'A', 'B', 'C', 'D']
        
        # Display top 5
        print("\n  Top 5 Recommendations:")
        for i, stock in enumerate(data['top_holdings'][:5], 1):
            print(f"  {i}. [{stock['grade']}] {stock['name']} ({stock['ticker']}) - {stock['price']:,.0f}원")
            print(f"     Wave: {stock['wave']}, SD: {stock['sd_stage']}, Score: {stock['score']:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Portfolio API Test Failed: {e}")
        return False

def test_stock_detail_api():
    """Test stock detail API endpoint"""
    print("\n=== Testing /api/stock/<ticker> ===")
    test_tickers = ['005930', '028260', '066570']
    
    for ticker in test_tickers:
        try:
            response = requests.get(f"{BASE_URL}/api/stock/{ticker}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            
            # Check metrics
            assert 'metrics' in data, "Missing metrics"
            metrics = data['metrics']
            assert 'name' in metrics and 'grade' in metrics and 'score' in metrics
            
            # Check price history
            assert 'price_history' in data, "Missing price_history"
            assert len(data['price_history']) > 0, "No price history"
            
            # Verify OHLCV format
            first_candle = data['price_history'][0]
            required_fields = ['time', 'open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                assert field in first_candle, f"Missing field: {field}"
            
            print(f"✓ {metrics['name']} ({ticker})")
            print(f"  - Grade: {metrics['grade']}, Score: {metrics['score']:.2f}")
            print(f"  - Wave: {metrics['wave_stage']}")
            print(f"  - Price History: {len(data['price_history'])} candles")
            print(f"  - Date Range: {data['price_history'][0]['time']} to {data['price_history'][-1]['time']}")
            
        except Exception as e:
            print(f"✗ Stock Detail API Test Failed for {ticker}: {e}")
            return False
    
    return True

def test_homepage():
    """Test homepage loads"""
    print("\n=== Testing Homepage ===")
    try:
        response = requests.get(BASE_URL)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'ANTIGRAVITY' in response.text, "Missing ANTIGRAVITY header"
        assert 'Market Indices' in response.text, "Missing Market Indices section"
        assert 'AI Recommendations' in response.text, "Missing AI Recommendations section"
        print("✓ Homepage loads successfully")
        print("  - Contains: ANTIGRAVITY header, Market Indices, AI Recommendations")
        return True
    except Exception as e:
        print(f"✗ Homepage Test Failed: {e}")
        return False

def test_data_files():
    """Test that required data files exist"""
    print("\n=== Testing Data Files ===")
    import os
    
    required_files = [
        'daily_prices.csv',
        'wave_transition_analysis_results.csv',
        'recommendation_history.csv',
        'ticker_to_yahoo_map.csv'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✓ {file} ({size:,} bytes)")
        else:
            print(f"✗ {file} - NOT FOUND")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Stock Analysis System - QA Test Suite")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Homepage", test_homepage),
        ("Data Files", test_data_files),
        ("Portfolio API", test_portfolio_api),
        ("Stock Detail API", test_stock_detail_api),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is fully functional.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    exit(main())
