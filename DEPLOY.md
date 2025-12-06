# 🚀 배포 가이드

## GitHub Actions 설정

### 1. GitHub 저장소 생성
1. GitHub.com 접속
2. New repository 클릭
3. 저장소 이름 입력 (예: `btc-trading-bot`)
4. 생성

### 2. 로컬에서 푸시
```bash
cd /Users/parkch/Documents/주식

# 원격 저장소 설정 (YOUR_USERNAME과 REPO_NAME을 실제 값으로 변경)
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 또는 새로 추가
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 푸시
git push -u origin main
```

### 3. GitHub Secrets 설정
저장소 → Settings → Secrets and variables → Actions → New repository secret

필수 Secrets:
- `UPBIT_ACCESS_KEY` - 업비트 Access Key
- `UPBIT_SECRET_KEY` - 업비트 Secret Key

선택 Secrets:
- `DEEPSEEK_API_KEY` - AI 분석용
- `TELEGRAM_BOT_TOKEN` - 알림용
- `TELEGRAM_CHAT_ID` - 알림용

### 4. Actions 활성화
1. Actions 탭 클릭
2. "I understand my workflows, go ahead and enable them" 클릭
3. 자동으로 15분마다 실행됨!

---

## Render 배포 설정

### 1. Render 계정 생성
1. https://render.com 접속
2. GitHub로 로그인
3. New → Web Service 클릭

### 2. 저장소 연결
1. GitHub 저장소 선택
2. 설정:
   - **Name**: `btc-trading-dashboard`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd bot && gunicorn flask_app:app --bind 0.0.0.0:$PORT`

### 3. 환경 변수 설정
Render Dashboard → Environment → Add Environment Variable

필수:
- `UPBIT_ACCESS_KEY` = (업비트 Access Key)
- `UPBIT_SECRET_KEY` = (업비트 Secret Key)
- `TRADING_MODE` = `LIVE`

선택:
- `DEEPSEEK_API_KEY` = (DeepSeek API Key)
- `TELEGRAM_BOT_TOKEN` = (텔레그램 봇 토큰)
- `TELEGRAM_CHAT_ID` = (텔레그램 채팅 ID)

### 4. 배포
1. Create Web Service 클릭
2. 배포 완료 대기 (약 2-3분)
3. 제공된 URL로 접속

---

## 로컬 테스트

### .env 파일 생성
```bash
cp .env.example .env
# .env 파일 편집하여 실제 API 키 입력
```

### 실행
```bash
# 트레이딩 봇
cd bot
python trading_bot.py

# 웹 대시보드
python flask_app.py
# http://localhost:5000 접속
```

---

## 문제 해결

### GitHub Actions가 실행 안됨
- Actions 탭에서 활성화 확인
- Secrets 설정 확인
- `.github/workflows/trading-bot.yml` 파일 확인

### Render 배포 실패
- Build Command 확인
- Start Command 확인
- 환경 변수 설정 확인
- 로그 확인 (Render Dashboard → Logs)

### API 키 오류
- .env 파일 확인
- GitHub Secrets 확인
- Render Environment Variables 확인

