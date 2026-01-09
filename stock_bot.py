import pandas as pd
from datetime import datetime
import pytz
import os
import requests
import yfinance as yf

def send_telegram_message(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ 텔레그램 설정(토큰/ID)이 없습니다.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': msg}
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ 텔레그램 전송 완료")
        else:
            print(f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        
# 1. 감시할 종목 리스트 (미국주식 티커) - 여기를 바꾸면 원하는 종목을 볼 수 있어요
# 1. 감시할 종목 리스트 (원하는 종목으로 바꾸세요)
tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "SOXL"]

# 2. 텔레그램 메시지 시작 부분 만들기
bot_message = "📈 [맷투자 모닝 브리핑]\n------------------\n"

# HTML 생성을 위한 데이터 저장소
stock_data = {}

print("데이터 수집을 시작합니다...")

# 3. 반복문 시작 (주가 가져오기 + 메시지 만들기)
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # 최신 데이터 가져오기 (fast_info가 빠르고 오류가 적습니다)
        price = stock.fast_info['last_price'] 
        prev_close = stock.fast_info['previous_close']
        
        # 변동률 계산
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        
        # 이모지 결정 (오르면 빨강/상승, 내리면 파랑/하락)
        emoji = "🔺" if change >= 0 else "Vk"
        sign = "+" if change >= 0 else ""
        
        # 4. [중요] 텔레그램 메시지에 한 줄 추가하기
        # 예: 🔺 NVDA: $120.50 (+1.2%)
        line = f"{emoji} {ticker}: ${price:.2f} ({sign}{change_pct:.2f}%)\n"
        bot_message += line
        
        print(f"수집 성공: {ticker}")

    except Exception as e:
        print(f"에러 발생 ({ticker}): {e}")
        bot_message += f"⚠️ {ticker}: 데이터 수집 실패\n"

# 5. HTML 파일 업데이트 (기존 코드 유지)
# ... (HTML 만드는 코드가 있다면 여기에 그대로 둡니다) ...

bot_message += "------------------\n👉 대시보드 확인: https://donaq.github.io/my-stock-dashboard/"

# 6. 최종 메시지 전송
print("텔레그램 전송 중...")
send_telegram_message(bot_message)
