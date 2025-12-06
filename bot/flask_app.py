"""
Flask 웹 대시보드 - 트레이딩 봇 모니터링
Render 배포용
"""

from flask import Flask, render_template, jsonify
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# 템플릿 경로 설정 (Render에서는 절대 경로 사용)
try:
    # btc_analysis/templates가 있으면 사용
    template_path = Path(__file__).parent.parent / 'btc_analysis' / 'templates'
    if template_path.exists():
        app.template_folder = str(template_path)
        app.static_folder = str(template_path)
    else:
        # 없으면 현재 디렉토리에서 찾기
        app.template_folder = None
        app.static_folder = None
except:
    app.template_folder = None
    app.static_folder = None

DATA_DIR = Path(__file__).parent.parent / 'data'

def load_json(filename):
    """JSON 파일 로드"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    """메인 대시보드"""
    try:
        return render_template('index.html')
    except:
        # 템플릿이 없으면 간단한 JSON 응답
        return jsonify({
            'status': 'running',
            'message': 'BTC Trading Bot Dashboard',
            'endpoints': {
                '/api/portfolio': '포트폴리오 정보',
                '/api/signals': '최근 신호',
                '/api/trades': '거래 내역'
            }
        })

@app.route('/api/portfolio')
def get_portfolio():
    """포트폴리오 정보"""
    portfolio = load_json('portfolio.json')
    signals = load_json('signals.json')
    
    # Calculate total value
    total_value = portfolio.get('cash', 0)
    positions = portfolio.get('positions', {})
    
    holdings = []
    for ticker, pos in positions.items():
        current_price = pos.get('avg_price', 0)
        value = pos['quantity'] * current_price
        total_value += value
        profit_pct = ((current_price - pos['avg_price']) / pos['avg_price']) * 100 if pos['avg_price'] > 0 else 0
        
        holdings.append({
            'ticker': ticker,
            'name': ticker.replace('KRW-', ''),
            'price': current_price,
            'quantity': pos['quantity'],
            'return_pct': profit_pct,
            'invested': pos.get('invested', 0)
        })
    
    return jsonify({
        'cash': portfolio.get('cash', 0),
        'total_value': total_value,
        'initial_capital': portfolio.get('initial_capital', 0),
        'profit': total_value - portfolio.get('initial_capital', 0),
        'profit_pct': ((total_value - portfolio.get('initial_capital', 0)) / portfolio.get('initial_capital', 1)) * 100,
        'holdings': holdings,
        'updated_at': portfolio.get('updated_at', datetime.now().isoformat())
    })

@app.route('/api/signals')
def get_signals():
    """최근 신호"""
    signals_data = load_json('signals.json')
    signals = signals_data.get('signals', [])
    
    return jsonify({
        'signals': signals[-10:],  # 최근 10개
        'updated_at': signals_data.get('updated_at', datetime.now().isoformat())
    })

@app.route('/api/trades')
def get_trades():
    """거래 내역"""
    trades_data = load_json('trade_history.json')
    trades = trades_data.get('trades', [])
    
    return jsonify({
        'trades': trades[-20:],  # 최근 20개
        'total': len(trades)
    })

@app.route('/api/status')
def get_status():
    """봇 상태"""
    portfolio = load_json('portfolio.json')
    signals = load_json('signals.json')
    trades = load_json('trade_history.json')
    
    return jsonify({
        'status': 'running',
        'mode': os.getenv('TRADING_MODE', 'LIVE'),
        'portfolio_exists': bool(portfolio),
        'last_signals': signals.get('updated_at'),
        'total_trades': len(trades.get('trades', []))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

