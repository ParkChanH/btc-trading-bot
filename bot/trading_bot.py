"""
BTC Trading Bot - GitHub Actions 기반 24/7 자동매매
"""

import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv
    # 프로젝트 루트에서 .env 파일 찾기
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✅ .env 파일 로드됨: {env_path}")
    else:
        # 루트에 없으면 현재 디렉토리에서 찾기
        load_dotenv(override=True)
        print("⚠️  .env 파일을 찾지 못했습니다. 환경 변수만 사용합니다.")
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다. 환경 변수만 사용합니다.")

# ============== 설정 ==============
class Config:
    # 업비트 API (실거래 시 필요)
    UPBIT_ACCESS_KEY = os.environ.get('UPBIT_ACCESS_KEY', '') or os.getenv('UPBIT_ACCESS_KEY', '')
    UPBIT_SECRET_KEY = os.environ.get('UPBIT_SECRET_KEY', '') or os.getenv('UPBIT_SECRET_KEY', '')
    
    # DeepSeek AI API (분석용)
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '') or os.getenv('DEEPSEEK_API_KEY', '')
    
    # 텔레그램 알림 (선택)
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '') or os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '') or os.getenv('TELEGRAM_CHAT_ID', '')
    
    # 거래 설정 (기본값: LIVE 모드)
    TRADING_MODE = os.environ.get('TRADING_MODE', 'LIVE') or os.getenv('TRADING_MODE', 'LIVE')  # SIMULATION or LIVE
    MAX_INVESTMENT_PER_TRADE = int(os.environ.get('MAX_INVESTMENT_PER_TRADE', '100000') or os.getenv('MAX_INVESTMENT_PER_TRADE', '100000'))
    STOP_LOSS_PCT = float(os.environ.get('STOP_LOSS_PCT', '-3.0') or os.getenv('STOP_LOSS_PCT', '-3.0'))
    TAKE_PROFIT_PCT = float(os.environ.get('TAKE_PROFIT_PCT', '5.0') or os.getenv('TAKE_PROFIT_PCT', '5.0'))
    
    # 분석 대상 코인
    TARGET_COINS = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-SOL', 'KRW-DOGE']


# ============== 데이터 저장소 (GitHub에 저장) ==============
class DataStore:
    """GitHub 저장소에 데이터를 JSON으로 저장"""
    
    DATA_DIR = Path(__file__).parent.parent / 'data'
    
    @classmethod
    def ensure_dir(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def load(cls, filename: str) -> dict:
        cls.ensure_dir()
        filepath = cls.DATA_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save(cls, filename: str, data: dict):
        cls.ensure_dir()
        filepath = cls.DATA_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    @classmethod
    def get_portfolio(cls) -> dict:
        return cls.load('portfolio.json')
    
    @classmethod
    def save_portfolio(cls, portfolio: dict):
        cls.save('portfolio.json', portfolio)
    
    @classmethod
    def get_trade_history(cls) -> list:
        data = cls.load('trade_history.json')
        return data.get('trades', [])
    
    @classmethod
    def add_trade(cls, trade: dict):
        data = cls.load('trade_history.json')
        trades = data.get('trades', [])
        trades.append(trade)
        # 최근 100개만 유지
        trades = trades[-100:]
        cls.save('trade_history.json', {'trades': trades})
    
    @classmethod
    def get_signals(cls) -> list:
        data = cls.load('signals.json')
        return data.get('signals', [])
    
    @classmethod
    def save_signals(cls, signals: list):
        cls.save('signals.json', {'signals': signals, 'updated_at': datetime.now(timezone.utc).isoformat()})


# ============== 업비트 API ==============
class UpbitAPI:
    """업비트 API 래퍼"""
    
    BASE_URL = 'https://api.upbit.com/v1'
    
    @staticmethod
    def get_current_price(ticker: str) -> float:
        """현재가 조회"""
        try:
            url = f"{UpbitAPI.BASE_URL}/ticker?markets={ticker}"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data and len(data) > 0:
                return data[0]['trade_price']
        except Exception as e:
            print(f"[ERROR] 현재가 조회 실패 ({ticker}): {e}")
        return 0
    
    @staticmethod
    def get_ohlcv(ticker: str, interval: str = 'day', count: int = 30) -> list:
        """OHLCV 데이터 조회"""
        try:
            if interval == 'day':
                url = f"{UpbitAPI.BASE_URL}/candles/days?market={ticker}&count={count}"
            elif interval == 'minute60':
                url = f"{UpbitAPI.BASE_URL}/candles/minutes/60?market={ticker}&count={count}"
            else:
                url = f"{UpbitAPI.BASE_URL}/candles/minutes/15?market={ticker}&count={count}"
            
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            print(f"[ERROR] OHLCV 조회 실패 ({ticker}): {e}")
        return []
    
    @staticmethod
    def get_all_prices(tickers: list) -> dict:
        """여러 코인 현재가 한번에 조회"""
        try:
            if not tickers:
                return {}
            markets = ','.join(tickers)
            url = f"{UpbitAPI.BASE_URL}/ticker?markets={markets}"
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, list):
                return {item['market']: item for item in data}
            elif isinstance(data, dict):
                return {data.get('market', ''): data}
            return {}
        except Exception as e:
            print(f"[ERROR] 가격 조회 실패: {e}")
        return {}


# ============== AI 분석 (DeepSeek) ==============
class AIAnalyzer:
    """DeepSeek AI를 이용한 시장 분석"""
    
    @staticmethod
    def analyze(ticker: str, ohlcv_data: list) -> dict:
        """코인 분석"""
        if not Config.DEEPSEEK_API_KEY:
            # API 키 없으면 간단한 기술적 분석
            return AIAnalyzer.simple_analysis(ticker, ohlcv_data)
        
        try:
            # 최근 7일 데이터 요약
            recent = ohlcv_data[:7] if len(ohlcv_data) >= 7 else ohlcv_data
            price_summary = []
            for candle in recent:
                price_summary.append({
                    'date': candle.get('candle_date_time_kst', '')[:10],
                    'open': candle.get('opening_price'),
                    'high': candle.get('high_price'),
                    'low': candle.get('low_price'),
                    'close': candle.get('trade_price'),
                    'volume': candle.get('candle_acc_trade_volume')
                })
            
            prompt = f"""당신은 암호화폐 트레이딩 전문가입니다.
다음 {ticker} 데이터를 분석하고 매매 신호를 JSON으로 응답하세요.

최근 가격 데이터:
{json.dumps(price_summary, indent=2)}

다음 형식으로만 응답:
{{
    "signal": "매수" 또는 "매도" 또는 "관망",
    "confidence": 0-100 사이 숫자,
    "reason": "분석 이유 (한 문장)",
    "entry_price": 추천 진입가,
    "stop_loss": 손절가,
    "take_profit": 익절가
}}"""

            response = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers={
                    'Authorization': f'Bearer {Config.DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.3
                },
                timeout=30
            )
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            print(f"[ERROR] AI 분석 실패 ({ticker}): {e}")
        
        return AIAnalyzer.simple_analysis(ticker, ohlcv_data)
    
    @staticmethod
    def simple_analysis(ticker: str, ohlcv_data: list) -> dict:
        """간단한 기술적 분석 (AI 없이)"""
        if not ohlcv_data or len(ohlcv_data) < 5:
            return {'signal': '관망', 'confidence': 30, 'reason': '데이터 부족'}
        
        current_price = ohlcv_data[0]['trade_price']
        
        # 5일 이동평균
        ma5 = sum(c['trade_price'] for c in ohlcv_data[:5]) / 5
        
        # 20일 이동평균 (데이터 있으면)
        ma20 = sum(c['trade_price'] for c in ohlcv_data[:20]) / min(20, len(ohlcv_data))
        
        # RSI 간단 계산
        gains = []
        losses = []
        for i in range(min(14, len(ohlcv_data)-1)):
            diff = ohlcv_data[i]['trade_price'] - ohlcv_data[i+1]['trade_price']
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0.0001
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        
        # 신호 결정
        signal = '관망'
        confidence = 50
        reason = ''
        
        if current_price > ma5 > ma20 and rsi < 70:
            signal = '매수'
            confidence = min(80, 50 + int((current_price - ma20) / ma20 * 100))
            reason = f'상승 추세, RSI {rsi:.1f}'
        elif current_price < ma5 < ma20 and rsi > 30:
            signal = '매도'
            confidence = min(80, 50 + int((ma20 - current_price) / ma20 * 100))
            reason = f'하락 추세, RSI {rsi:.1f}'
        elif rsi < 30:
            signal = '매수'
            confidence = 65
            reason = f'과매도 구간, RSI {rsi:.1f}'
        elif rsi > 70:
            signal = '매도'
            confidence = 65
            reason = f'과매수 구간, RSI {rsi:.1f}'
        else:
            reason = f'중립 구간, RSI {rsi:.1f}'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'entry_price': current_price,
            'stop_loss': current_price * (1 + Config.STOP_LOSS_PCT / 100),
            'take_profit': current_price * (1 + Config.TAKE_PROFIT_PCT / 100)
        }


# ============== 알림 ==============
class Notifier:
    """텔레그램 알림"""
    
    @staticmethod
    def send(message: str):
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            print(f"[알림] {message}")
            return
        
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }, timeout=10)
        except Exception as e:
            print(f"[ERROR] 텔레그램 발송 실패: {e}")


# ============== 트레이딩 엔진 ==============
class TradingEngine:
    """메인 트레이딩 로직"""
    
    def __init__(self):
        self.portfolio = DataStore.get_portfolio()
        if not self.portfolio:
            if Config.TRADING_MODE == 'LIVE':
                # LIVE 모드: 실제 잔고 가져오기
                try:
                    import pyupbit
                    if Config.UPBIT_ACCESS_KEY and Config.UPBIT_SECRET_KEY:
                        upbit = pyupbit.Upbit(Config.UPBIT_ACCESS_KEY, Config.UPBIT_SECRET_KEY)
                        krw_balance = upbit.get_balance('KRW')
                        initial_capital = float(krw_balance) if krw_balance else 0
                        print(f"💰 실제 잔고: {initial_capital:,.0f}원")
                    else:
                        print("⚠️  업비트 API 키가 없습니다. 시뮬레이션 모드로 전환합니다.")
                        Config.TRADING_MODE = 'SIMULATION'
                        initial_capital = 1000000
                except Exception as e:
                    print(f"⚠️  잔고 조회 실패: {e}. 시뮬레이션 모드로 전환합니다.")
                    Config.TRADING_MODE = 'SIMULATION'
                    initial_capital = 1000000
            else:
                # SIMULATION 모드
                initial_capital = 1000000
            
            self.portfolio = {
                'cash': initial_capital,
                'positions': {},
                'initial_capital': initial_capital
            }
    
    def run(self):
        """메인 실행"""
        print(f"\n{'='*50}")
        print(f"🤖 BTC Trading Bot 실행")
        print(f"⏰ 시간: {datetime.now(timezone.utc).isoformat()}")
        print(f"📊 모드: {Config.TRADING_MODE}")
        print(f"{'='*50}\n")
        
        signals = []
        
        # 1. 각 코인 분석
        for ticker in Config.TARGET_COINS:
            print(f"\n📈 {ticker} 분석 중...")
            
            # 가격 데이터 가져오기
            ohlcv = UpbitAPI.get_ohlcv(ticker, 'day', 30)
            if not ohlcv:
                print(f"  ❌ 데이터 없음")
                continue
            
            current_price = ohlcv[0]['trade_price']
            change_24h = ohlcv[0].get('change_rate', 0) * 100
            
            # AI 분석
            analysis = AIAnalyzer.analyze(ticker, ohlcv)
            
            signal_data = {
                'ticker': ticker,
                'name': ticker.replace('KRW-', ''),
                'current_price': current_price,
                'change_24h': change_24h,
                'signal': analysis.get('signal', '관망'),
                'confidence': analysis.get('confidence', 50),
                'reason': analysis.get('reason', ''),
                'entry_price': analysis.get('entry_price', current_price),
                'stop_loss': analysis.get('stop_loss', current_price * 0.97),
                'take_profit': analysis.get('take_profit', current_price * 1.05),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            signals.append(signal_data)
            
            print(f"  💰 현재가: {current_price:,.0f}원")
            print(f"  📊 신호: {signal_data['signal']} ({signal_data['confidence']}%)")
            print(f"  📝 이유: {signal_data['reason']}")
            
            # 2. 매매 실행 (신뢰도 70% 이상)
            if signal_data['confidence'] >= 70:
                self.execute_signal(signal_data)
        
        # 3. 보유 포지션 체크 (손절/익절)
        self.check_positions()
        
        # 4. 결과 저장
        DataStore.save_signals(signals)
        DataStore.save_portfolio(self.portfolio)
        
        # 5. 요약 출력
        self.print_summary()
        
        return signals
    
    def execute_signal(self, signal: dict):
        """매매 신호 실행"""
        ticker = signal['ticker']
        
        if signal['signal'] == '매수':
            # 이미 보유 중이면 스킵
            if ticker in self.portfolio.get('positions', {}):
                print(f"  ⏭️ {ticker} 이미 보유 중")
                return
            
            # 투자금 계산
            invest_amount = min(Config.MAX_INVESTMENT_PER_TRADE, self.portfolio['cash'] * 0.2)
            if invest_amount < 10000:
                print(f"  ⚠️ 현금 부족")
                return
            
            quantity = invest_amount / signal['current_price']
            
            if Config.TRADING_MODE == 'SIMULATION':
                # 시뮬레이션 매수
                self.portfolio['cash'] -= invest_amount
                self.portfolio['positions'][ticker] = {
                    'quantity': quantity,
                    'avg_price': signal['current_price'],
                    'invested': invest_amount,
                    'entry_time': datetime.now(timezone.utc).isoformat(),
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit']
                }
                
                trade = {
                    'action': 'BUY',
                    'ticker': ticker,
                    'price': signal['current_price'],
                    'quantity': quantity,
                    'amount': invest_amount,
                    'confidence': signal['confidence'],
                    'reason': signal['reason'],
                    'time': datetime.now(timezone.utc).isoformat(),
                    'mode': 'SIMULATION'
                }
                DataStore.add_trade(trade)
                
                msg = f"🟢 [시뮬레이션] 매수 | {ticker}\n💰 {invest_amount:,.0f}원 @ {signal['current_price']:,.0f}원"
                print(f"  {msg}")
                Notifier.send(msg)
            
            elif Config.TRADING_MODE == 'LIVE':
                # 실제 거래 매수
                try:
                    import pyupbit
                    if not Config.UPBIT_ACCESS_KEY or not Config.UPBIT_SECRET_KEY:
                        print(f"  ❌ 업비트 API 키가 없습니다. 거래를 건너뜁니다.")
                        return
                    
                    upbit = pyupbit.Upbit(Config.UPBIT_ACCESS_KEY, Config.UPBIT_SECRET_KEY)
                    result = upbit.buy_market_order(ticker, invest_amount)
                    
                    if result and 'uuid' in result:
                        # 실제 거래 성공
                        order_info = upbit.get_order(result['uuid'])
                        if order_info:
                            executed_price = order_info.get('price', signal['current_price'])
                            executed_volume = order_info.get('executed_volume', quantity)
                            
                            self.portfolio['cash'] -= invest_amount
                            self.portfolio['positions'][ticker] = {
                                'quantity': float(executed_volume),
                                'avg_price': float(executed_price),
                                'invested': invest_amount,
                                'entry_time': datetime.now(timezone.utc).isoformat(),
                                'stop_loss': signal['stop_loss'],
                                'take_profit': signal['take_profit'],
                                'order_uuid': result['uuid']
                            }
                            
                            trade = {
                                'action': 'BUY',
                                'ticker': ticker,
                                'price': float(executed_price),
                                'quantity': float(executed_volume),
                                'amount': invest_amount,
                                'confidence': signal['confidence'],
                                'reason': signal['reason'],
                                'time': datetime.now(timezone.utc).isoformat(),
                                'mode': 'LIVE',
                                'order_uuid': result['uuid']
                            }
                            DataStore.add_trade(trade)
                            
                            msg = f"🟢 [실거래] 매수 | {ticker}\n💰 {invest_amount:,.0f}원 @ {executed_price:,.0f}원"
                            print(f"  {msg}")
                            Notifier.send(msg)
                    else:
                        print(f"  ❌ 매수 주문 실패: {result}")
                        
                except Exception as e:
                    print(f"  ❌ 실거래 매수 오류: {e}")
                    Notifier.send(f"❌ 매수 실패 | {ticker}\n오류: {str(e)}")
        
        elif signal['signal'] == '매도':
            # 보유 중이 아니면 스킵
            if ticker not in self.portfolio.get('positions', {}):
                print(f"  ⏭️ {ticker} 미보유")
                return
            
            pos = self.portfolio['positions'][ticker]
            sell_amount = pos['quantity'] * signal['current_price']
            profit = sell_amount - pos['invested']
            profit_pct = (profit / pos['invested']) * 100
            
            if Config.TRADING_MODE == 'SIMULATION':
                self.portfolio['cash'] += sell_amount
                del self.portfolio['positions'][ticker]
                
                trade = {
                    'action': 'SELL',
                    'ticker': ticker,
                    'price': signal['current_price'],
                    'quantity': pos['quantity'],
                    'amount': sell_amount,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'confidence': signal['confidence'],
                    'reason': signal['reason'],
                    'time': datetime.now(timezone.utc).isoformat(),
                    'mode': 'SIMULATION'
                }
                DataStore.add_trade(trade)
                
                emoji = "🔴" if profit < 0 else "🟢"
                msg = f"{emoji} [시뮬레이션] 매도 | {ticker}\n💰 {sell_amount:,.0f}원 ({profit_pct:+.2f}%)"
                print(f"  {msg}")
                Notifier.send(msg)
            
            elif Config.TRADING_MODE == 'LIVE':
                # 실제 거래 매도
                try:
                    import pyupbit
                    if not Config.UPBIT_ACCESS_KEY or not Config.UPBIT_SECRET_KEY:
                        print(f"  ❌ 업비트 API 키가 없습니다. 거래를 건너뜁니다.")
                        return
                    
                    upbit = pyupbit.Upbit(Config.UPBIT_ACCESS_KEY, Config.UPBIT_SECRET_KEY)
                    result = upbit.sell_market_order(ticker, pos['quantity'])
                    
                    if result and 'uuid' in result:
                        # 실제 거래 성공
                        order_info = upbit.get_order(result['uuid'])
                        if order_info:
                            executed_price = order_info.get('price', signal['current_price'])
                            executed_volume = order_info.get('executed_volume', pos['quantity'])
                            actual_sell_amount = float(executed_price) * float(executed_volume)
                            actual_profit = actual_sell_amount - pos['invested']
                            actual_profit_pct = (actual_profit / pos['invested']) * 100
                            
                            self.portfolio['cash'] += actual_sell_amount
                            del self.portfolio['positions'][ticker]
                            
                            trade = {
                                'action': 'SELL',
                                'ticker': ticker,
                                'price': float(executed_price),
                                'quantity': float(executed_volume),
                                'amount': actual_sell_amount,
                                'profit': actual_profit,
                                'profit_pct': actual_profit_pct,
                                'confidence': signal['confidence'],
                                'reason': signal['reason'],
                                'time': datetime.now(timezone.utc).isoformat(),
                                'mode': 'LIVE',
                                'order_uuid': result['uuid']
                            }
                            DataStore.add_trade(trade)
                            
                            emoji = "🔴" if actual_profit < 0 else "🟢"
                            msg = f"{emoji} [실거래] 매도 | {ticker}\n💰 {actual_sell_amount:,.0f}원 ({actual_profit_pct:+.2f}%)"
                            print(f"  {msg}")
                            Notifier.send(msg)
                    else:
                        print(f"  ❌ 매도 주문 실패: {result}")
                        
                except Exception as e:
                    print(f"  ❌ 실거래 매도 오류: {e}")
                    Notifier.send(f"❌ 매도 실패 | {ticker}\n오류: {str(e)}")
    
    def check_positions(self):
        """보유 포지션 손절/익절 체크"""
        print(f"\n📋 포지션 체크...")
        
        positions = self.portfolio.get('positions', {})
        if not positions:
            print("  보유 포지션 없음")
            return
        
        prices = UpbitAPI.get_all_prices(list(positions.keys()))
        
        for ticker, pos in list(positions.items()):
            if ticker not in prices:
                print(f"  ⚠️ {ticker}: 가격 정보 없음")
                continue
            
            price_data = prices[ticker]
            if isinstance(price_data, dict):
                current_price = price_data.get('trade_price', 0)
            else:
                current_price = float(price_data) if price_data else 0
            
            if current_price == 0:
                print(f"  ⚠️ {ticker}: 가격 조회 실패")
                continue
            profit_pct = ((current_price - pos['avg_price']) / pos['avg_price']) * 100
            
            print(f"  {ticker}: {profit_pct:+.2f}%")
            
            # 손절
            if profit_pct <= Config.STOP_LOSS_PCT:
                print(f"  🛑 손절 실행!")
                self.execute_signal({
                    'ticker': ticker,
                    'signal': '매도',
                    'current_price': current_price,
                    'confidence': 100,
                    'reason': f'손절 ({profit_pct:.2f}%)'
                })
            
            # 익절
            elif profit_pct >= Config.TAKE_PROFIT_PCT:
                print(f"  🎯 익절 실행!")
                self.execute_signal({
                    'ticker': ticker,
                    'signal': '매도',
                    'current_price': current_price,
                    'confidence': 100,
                    'reason': f'익절 ({profit_pct:.2f}%)'
                })
    
    def print_summary(self):
        """요약 출력"""
        print(f"\n{'='*50}")
        print("📊 포트폴리오 요약")
        print(f"{'='*50}")
        
        # 현재 평가액 계산
        total_value = self.portfolio['cash']
        positions = self.portfolio.get('positions', {})
        
        if positions:
            prices = UpbitAPI.get_all_prices(list(positions.keys()))
            for ticker, pos in positions.items():
                if ticker in prices:
                    total_value += pos['quantity'] * prices[ticker]['trade_price']
        
        profit = total_value - self.portfolio['initial_capital']
        profit_pct = (profit / self.portfolio['initial_capital']) * 100
        
        print(f"💵 현금: {self.portfolio['cash']:,.0f}원")
        print(f"📈 총 평가: {total_value:,.0f}원")
        print(f"💰 수익: {profit:+,.0f}원 ({profit_pct:+.2f}%)")
        print(f"📦 보유 종목: {len(positions)}개")
        
        for ticker, pos in positions.items():
            print(f"   - {ticker}: {pos['quantity']:.4f}개")
        
        print(f"{'='*50}\n")


# ============== 메인 ==============
if __name__ == '__main__':
    engine = TradingEngine()
    engine.run()

