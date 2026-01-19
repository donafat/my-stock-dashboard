import os
import requests
from bs4 import BeautifulSoup
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

# === 2. 날씨 가져오는 함수 (봇 차단 회피 기능 추가) ===
def get_weather(location):
    url = f"https://search.naver.com/search.naver?query={location} 날씨"
    # [중요] GitHub 서버가 아니라 일반 크롬 브라우저인 척 속이는 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5) # 5초 안에 응답 없으면 포기
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 날씨 HTML 구조 파싱
        temp = soup.find('div', {'class': 'temperature_text'}).text.strip().replace('현재 온도', '').replace('°', '')
        status = soup.find('span', {'class': 'weather_before_text'}).text.strip()
        # 어제보다.. 부분은 구조가 복잡할 수 있어 제외하거나 예외처리
        return f"- {location}: {temp}°C ({status})"
    except Exception as e:
        print(f"날씨 오류 ({location}): {e}") # 로그에 에러 원인 출력
        return f"- {location}: 날씨 정보 불러오기 실패"

# === 3. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 4. 메인 실행 로직 ===
if __name__ == "__main__":
    # (1) 날씨 정보 수집
    print("날씨 정보 수집 중...")
    bot_message = "📈 [맷투자 모닝 브리핑]\n"
    current_time = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")
    bot_message += f"📅 {current_time}\n------------------\n"
    
    bot_message += "🌤 **오늘의 날씨**\n"
    bot_message += get_weather("성동구") + "\n"
    bot_message += get_weather("대치동") + "\n"
    bot_message += "------------------\n"

    # (2) 주식 정보 수집
    print("주식 정보 수집 중...")
    bot_message += "📊 **미국 주식 현황**\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # 서버에서는 .info가 막히는 경우가 많아 .history 사용이 훨씬 안정적임
            hist = stock.history(period="2d") # 2일치 데이터를 가져옴
            
            if len(hist) >= 1:
                # 최신 종가 가져오기
                close_price = hist['Close'].iloc[-1]
                
                # 전일 대비 등락률 계산 (데이터가 2일치 이상일 때만)
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
        
        # [중요] 너무 빨리 요청하면 차단당하므로 0.5초 쉬기
        time.sleep(0.5)

    # (3) 텔레그램 전송
    send_telegram_message(bot_message)
    print("전송 완료")
