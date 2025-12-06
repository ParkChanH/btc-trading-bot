"""
일간 리포트 생성
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def load_json(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print(message)
        return
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")

def generate_report():
    portfolio = load_json('portfolio.json')
    trade_history = load_json('trade_history.json').get('trades', [])
    
    # 오늘 거래만 필터
    today = datetime.now(timezone.utc).date()
    today_trades = [
        t for t in trade_history 
        if datetime.fromisoformat(t['time'].replace('Z', '+00:00')).date() == today
    ]
    
    # 통계 계산
    total_value = portfolio.get('cash', 0)
    positions = portfolio.get('positions', {})
    initial = portfolio.get('initial_capital', 1000000)
    
    # 현재가 조회
    if positions:
        tickers = list(positions.keys())
        markets = ','.join(tickers)
        try:
            resp = requests.get(f"https://api.upbit.com/v1/ticker?markets={markets}", timeout=10)
            prices = {p['market']: p['trade_price'] for p in resp.json()}
            for ticker, pos in positions.items():
                if ticker in prices:
                    total_value += pos['quantity'] * prices[ticker]
        except:
            pass
    
    profit = total_value - initial
    profit_pct = (profit / initial) * 100
    
    # 오늘 수익
    today_profit = sum(t.get('profit', 0) for t in today_trades if t['action'] == 'SELL')
    
    # 승률 계산
    sell_trades = [t for t in trade_history if t['action'] == 'SELL']
    win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
    win_rate = (len(win_trades) / len(sell_trades) * 100) if sell_trades else 0
    
    # 리포트 생성
    report = f"""
📊 <b>일간 트레이딩 리포트</b>
━━━━━━━━━━━━━━━━━━━━

📅 날짜: {today.strftime('%Y-%m-%d')}

💰 <b>포트폴리오</b>
• 총 평가: {total_value:,.0f}원
• 현금: {portfolio.get('cash', 0):,.0f}원
• 보유 종목: {len(positions)}개

📈 <b>수익 현황</b>
• 총 수익: {profit:+,.0f}원 ({profit_pct:+.2f}%)
• 오늘 수익: {today_profit:+,.0f}원

📊 <b>거래 통계</b>
• 오늘 거래: {len(today_trades)}건
• 총 거래: {len(trade_history)}건
• 승률: {win_rate:.1f}%

━━━━━━━━━━━━━━━━━━━━
🤖 BTC Trading Bot
"""
    
    print(report)
    send_telegram(report)

if __name__ == '__main__':
    generate_report()
