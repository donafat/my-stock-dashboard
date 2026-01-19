import os
import requests
import yfinance as yf
from datetime import datetime
import pytz
import time

# === 1. 텔레그램 전송 함수 ===
def send_telegram_message(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={'chat_id': chat_id, 'text': msg})
        except:
            pass 

# === 2. 날씨 가져오는 함수 (wttr.in 서비스 사용) ===
def get_weather(location):
    """
    네이버 대신 봇 차단이 없는 wttr.in 날씨 서비스를 사용합니다.
    location: 지역명 (예: Seoul, Seongdong-gu)
    """
    try:
        # format=3: "지역: 날씨이모티콘 온도" 형태로 간략하게 받기
        # lang=ko: 한국어로 결과 받기
        url = f"https://wttr.in/{location}?format=%l:+%c+%t&lang=ko"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"{location}: 정보 없음"
    except Exception as e:
        return f"{location}: 날씨 서버 연결 실패"

# === 3. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 4. 메인 실행 로직 ===
if __name__ == "__main__":
    bot_message = "📈 [맷투자 모닝 브리핑]\n"
    current_time = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")
    bot_message += f"📅 {current_time}\n------------------\n"
    
    # (1) 날씨 정보 수집 (차단 방지를 위해 지역명을 명확하게 변경 추천)
    print("날씨 정보 수집 중...")
    bot_message += "🌤 **오늘의 날씨**\n"
    # wttr.in은 '구' 단위까지가 정확합니다.
    bot_message += get_weather("Seongdong-gu") + "\n" 
    bot_message += get_weather("Gangnam-gu") + " (대치동 인근)\n"
    bot_message += "------------------\n"

    # (2) 주식 정보 수집
    print("주식 정보 수집 중...")
    bot_message += "📊 **미국 주식 현황**\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # 서버에서 안정적인 history 함수 사용
            hist = stock.history(period="2d")
            
            if len(hist) >= 1:
                close_price = hist['Close'].iloc[-1]
                
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    change = ((close_price - prev_close) / prev_close) * 100
                    emoji = "🔺" if change > 0 else "Vk" if change < 0 else "➖"
                    bot_message += f"{emoji} {ticker}: ${close_price:.2f} ({change:+.2f}%)\n"
                else:
                    bot_message += f"➖ {ticker}: ${close_price:.2f}\n"
            else:
                bot_message += f"⚠️ {ticker}: 데이터 없음\n"
                
        except Exception as e:
            print(f"{ticker} 에러: {e}")
            bot_message += f"⚠️ {ticker}: 확인 불가\n"
        
        time.sleep(0.5) # 차단 방지 대기

    # (3) 텔레그램 전송
    send_telegram_message(bot_message)
    print("전송 완료")
