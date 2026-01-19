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

# === 2. [업그레이드] 시간별 비 예보 분석 함수 ===
def get_weather_forecast(location):
    """
    오전(09시), 오후(15시) 날씨와 '비 오는 시간'을 콕 집어 알려줍니다.
    """
    try:
        # format=j1: 상세 데이터를 JSON으로 요청
        url = f"https://wttr.in/{location}?format=j1&lang=ko"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather_today = data['weather'][0]['hourly']
            
            # (1) 대표 시간대 날씨 (오전 9시 / 오후 3시)
            # index 3 = 09:00, index 5 = 15:00
            am_data = weather_today[3]
            pm_data = weather_today[5]
            
            am_temp = am_data['tempC']
            am_desc = am_data['lang_ko'][0]['value']
            pm_temp = pm_data['tempC']
            pm_desc = pm_data['lang_ko'][0]['value']

            # (2) 비 오는 시간 분석 (06시 ~ 21시 사이 스캔)
            # 강수확률(chanceofrain)이 30% 이상인 시간만 찾기
            rain_timeline = []
            check_indices = [2, 3, 4, 5, 6, 7] # 06, 09, 12, 15, 18, 21시
            
            for idx in check_indices:
                hour_data = weather_today[idx]
                rain_prob = int(hour_data['chanceofrain'])
                time_str = int(hour_data['time']) // 100 # 900 -> 9
                
                if rain_prob >= 30: # 기준: 강수확률 30% 이상
                    rain_timeline.append(f"{time_str}시({rain_prob}%)")
            
            # (3) 메시지 조합
            result = f"📍 {location}\n"
            result += f" - 오전(09시): {am_temp}°C, {am_desc}\n"
            result += f" - 오후(15시): {pm_temp}°C, {pm_desc}\n"
            
            if rain_timeline:
                result += f" ☔ 비 예보: {', '.join(rain_timeline)}"
            else:
                result += " ✨ 하루 종일 비 예보 없음"
                
            return result
        else:
            return f"📍 {location}: 정보 없음"
            
    except Exception as e:
        print(f"날씨 에러: {e}")
        return f"📍 {location}: 서버 연결 실패"

# === 3. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 4. 메인 실행 로직 ===
if __name__ == "__main__":
    bot_message = "📈 [맷투자 모닝 브리핑]\n"
    current_time = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")
    bot_message += f"📅 {current_time}\n------------------\n"
    
    # (1) 날씨 정보 수집
    print("날씨 정보 수집 중...")
    bot_message += "🌤 **오늘의 날씨 체크**\n"
    
    # 성동구, 강남구(대치동)
    bot_message += get_weather_forecast("Seongdong-gu") + "\n\n"
    bot_message += get_weather_forecast("Gangnam-gu") + "\n"
    bot_message += "------------------\n"

    # (2) 주식 정보 수집
    print("주식 정보 수집 중...")
    bot_message += "📊 **미국 주식 현황**\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
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
        
        time.sleep(0.5)

    # (3) 텔레그램 전송
    send_telegram_message(bot_message)
    print("전송 완료")
