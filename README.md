# 🤖 BTC Trading Bot

GitHub Actions를 이용한 24/7 무료 자동 트레이딩 봇

## 🚀 특징

- ✅ **완전 무료** - GitHub Actions 무료 티어 사용
- ✅ **24/7 운영** - 15분마다 자동 실행
- ✅ **LIVE 모드** - 실제 거래 지원 (기본값)
- ✅ **AI 분석** - DeepSeek AI 또는 기술적 분석
- ✅ **텔레그램 알림** - 실시간 매매 알림
- ✅ **웹 대시보드** - Render로 배포 가능

## 📁 구조

```
btc-trading-bot/
├── .github/
│   └── workflows/
│       └── trading-bot.yml    # GitHub Actions 설정
├── bot/
│   ├── trading_bot.py         # 메인 트레이딩 봇
│   ├── flask_app.py          # 웹 대시보드 (Render용)
│   └── daily_report.py       # 일간 리포트
├── data/
│   ├── portfolio.json         # 포트폴리오 상태
│   ├── trade_history.json    # 거래 내역
│   └── signals.json          # AI 신호
├── requirements.txt
├── render.yaml                # Render 배포 설정
├── .env.example              # 환경 변수 예시
└── README.md
```

## ⚙️ 설정 방법

### 1단계: GitHub Secrets 설정

Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 필수 | 설명 |
|------------|------|------|
| `UPBIT_ACCESS_KEY` | ✅ | 업비트 API 키 (실거래용) |
| `UPBIT_SECRET_KEY` | ✅ | 업비트 시크릿 키 (실거래용) |
| `DEEPSEEK_API_KEY` | ❌ | DeepSeek AI 키 (AI 분석용) |
| `TELEGRAM_BOT_TOKEN` | ❌ | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | ❌ | 텔레그램 채팅 ID |

> ⚠️ **중요**: LIVE 모드에서는 업비트 API 키가 필수입니다!

### 2단계: Actions 활성화

1. 저장소의 Actions 탭 클릭
2. "I understand my workflows, go ahead and enable them" 클릭
3. 자동으로 15분마다 실행됨!

### 3단계: 수동 실행 (테스트)

1. Actions 탭 → 🤖 BTC Trading Bot
2. "Run workflow" 클릭
3. 실행 모드 선택 후 실행

## 📊 작동 방식

```
[15분마다]
    │
    ▼
┌─────────────────────┐
│ 1. 가격 데이터 수집  │
│    (BTC, ETH, XRP..)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. AI/기술적 분석   │
│    - RSI           │
│    - 이동평균      │
│    - DeepSeek AI   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. 매매 신호 생성   │
│    신뢰도 70% 이상  │
│    → 자동 매매     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. 포지션 관리      │
│    - 손절: -3%     │
│    - 익절: +5%     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. 결과 저장        │
│    → GitHub에 커밋 │
│    → 텔레그램 알림 │
└─────────────────────┘
```

## 💰 거래 설정 변경

`bot/trading_bot.py`에서 수정:

```python
class Config:
    MAX_INVESTMENT_PER_TRADE = 100000  # 1회 최대 투자금
    STOP_LOSS_PCT = -3.0               # 손절 %
    TAKE_PROFIT_PCT = 5.0              # 익절 %
    
    TARGET_COINS = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-SOL', 'KRW-DOGE']
```

## 🌐 Render 웹 대시보드 배포

### 1. Render 계정 생성
1. https://render.com 접속
2. GitHub로 로그인

### 2. 새 Web Service 생성
1. New → Web Service
2. 저장소 선택: `ParkChanH/btc-trading-bot`
3. 설정:
   - **Name**: `btc-trading-dashboard`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd bot && gunicorn flask_app:app --bind 0.0.0.0:$PORT`

### 3. 환경 변수 설정
Render Dashboard → Environment → Add Environment Variable

- `UPBIT_ACCESS_KEY` = (업비트 Access Key)
- `UPBIT_SECRET_KEY` = (업비트 Secret Key)
- `TRADING_MODE` = `LIVE`

### 4. 배포 완료!
배포 후 제공된 URL로 접속하면 대시보드를 볼 수 있습니다.

## 📱 텔레그램 봇 설정

1. @BotFather 에서 봇 생성 → 토큰 받기
2. 봇에게 메시지 전송
3. `https://api.telegram.org/bot<토큰>/getUpdates` 에서 chat_id 확인
4. GitHub Secrets에 등록

## ⚠️ 주의사항

- **LIVE 모드**가 기본값 (실제 거래 실행)
- GitHub Actions는 월 2,000분 무료 (약 2,880회 실행, 15분 간격 기준)
- 실거래 시 업비트 API 키 필수
- **투자 손실에 대한 책임은 사용자에게 있습니다**

## 📈 성과 확인

- `data/portfolio.json` - 현재 포트폴리오
- `data/trade_history.json` - 모든 거래 내역
- `data/signals.json` - 최근 AI 신호
- Actions 탭 - 실행 로그
- Render 대시보드 - 실시간 모니터링

## 🔧 트러블슈팅

### Actions가 실행 안됨
- Actions 탭에서 활성화 확인
- `.github/workflows/trading-bot.yml` 파일 존재 확인
- Secrets 설정 확인

### 푸시 에러
- Settings → Actions → General
- Workflow permissions → "Read and write permissions" 선택

### API 에러
- Secrets 설정 확인
- API 키 유효성 확인
- 업비트 API 권한 확인 (주문 가능 권한 필요)

## 📄 라이선스

MIT License - 자유롭게 사용하세요!

---

⭐ 도움이 되셨다면 Star를 눌러주세요!

