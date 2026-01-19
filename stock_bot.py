import os
import requests
import yfinance as yf
from datetime import datetime
import pytz
import time

# === 1. 텔레그램 전송 함수 (Markdown 적용) ===
def send_telegram_message(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        # [중요] 링크 기능을 위해 parse_mode='Markdown' 추가
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={
                'chat_id': chat_id, 
                'text': msg, 
                'parse_mode': 'Markdown',
                'disable_web_page_preview': 'true' # 링크 미리보기 끄기 (깔끔하게)
            })
        except:
            pass 

# === 2. 날씨 정보 함수 ===
def get_weather_forecast(location_eng, location_kor):
    """
    location_eng: wttr.in 검색용 (예: Seongdong-gu)
    location_kor: 네이버/케이웨더 링크용 (예: 성동구)
    """
    try:
        url = f"https://wttr.in/{location_eng}?format=j1&lang=ko"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather_today = data['weather'][0]['hourly']
            
            am_data = weather_today[3] # 09:00
            pm_data = weather_today[5] # 15:00
            
            rain_timeline = []
            check_indices = [2, 3, 4, 5, 6, 7] 
            
            for idx in check_indices:
                hour_data = weather_today[idx]
                rain_prob = int(hour_data['chanceofrain'])
                time_str = int(hour_data['time']) // 100 
                if rain_prob >= 30:
                    rain_timeline.append(f"{time_str}시({rain_prob}%)")
            
            # 기본 텍스트 정보
            result = f"📍 *{location_eng}* ({location_kor})\n"
            result += f" - 오전: {am_data['tempC']}°C, {am_data['lang_ko'][0]['value']}\n"
            result += f" - 오후: {pm_data['tempC']}°C, {pm_data['lang_ko'][0]['value']}\n"
            
            if rain_timeline:
                result += f" ☔ 비 예보: {', '.join(rain_timeline)}\n"
            else:
                result += " ✨ 비 예보 없음\n"
            
            # [추가] 상세 날씨 바로가기 링크 (네이버 날씨가 가장 URL 접근이 정확함)
            # 케이웨더는 URL에 지역코드가 필요해 자동화가 어려우므로, 
            # 케이웨더 데이터를 사용하는 네이버 날씨 링크를 제공합니다.
            link = f"https://search.naver.com/search.naver?query={location_kor}+날씨"
            result += f" 👉 [🔎 {location_kor} 상세 날씨/미세먼지 보기]({link})"
            
            return result
        else:
            return f"📍 {location_eng}: 정보 없음"
    except:
        return f"📍 {location_eng}: 연결 실패"

# === 3. 시장 주요 지표 ===
def get_market_indices():
    msg = ""
    indices = {
        "💵 환율 (USD/KRW)": "KRW=X",
        "🇰🇷 코스피 (KOSPI)": "^KS11",
        "🇺🇸 S&P 500": "^GSPC",
        "💻 나스닥 (NASDAQ)": "^IXIC",
        "😱 공포지수 (VIX)": "^VIX"
    }
    
    msg += "🌎 *글로벌 시장 지표*\n"
    for name, ticker in indices.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                
                change_str = ""
                if len(hist) >= 2:
                    prev = hist['Close'].iloc[-2]
                    change = ((price - prev) / prev) * 100
                    
                    if "VIX" in name:
                        icon = "🔥" if change > 5 else "😌" if change < -5 else " "
                    else:
                        icon = "🔺" if change > 0 else "💙" if change < 0 else "➖"
                    
                    change_str = f"({change:+.2f}%) {icon}"

                if "환율" in name:
                    msg += f"- {name}: {price:,.2f}원 {change_str}\n"
                else:
                    msg += f"- {name}: {price:,.2f} {change_str}\n"
        except:
            msg += f"- {name}: 확인 불가\n"
        time.sleep(0.3)
    
    return msg + "------------------\n"

# === 4. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 5. 메인 실행 로직 ===
if __name__ == "__main__":
    bot_message = "📈 *[맷투자 모닝 브리핑]*\n"
    current_time = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")
    bot_message += f"📅 {current_time}\n------------------\n"
    
    # (1) 날씨 정보 (한국어 지명 추가)
    print("날씨 정보 수집 중...")
    bot_message += "🌤 *오늘의 날씨*\n"
    bot_message += get_weather_forecast("Seongdong-gu", "성동구") + "\n\n"
    bot_message += get_weather_forecast("Gangnam-gu", "대치동") + "\n"
    bot_message += "------------------\n"

    # (2) 시장 지표
    print("시장 지표 수집 중...")
    bot_message += get_market_indices()

    # (3) 개별 주식 정보
    print("주식 정보 수집 중...")
    bot_message += "📊 *관심 종목 현황*\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) >= 1:
                close_price = hist['Close'].iloc[-1]
                
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    change = ((close_price - prev_close) / prev_close) * 100
                    
                    if change > 0: emoji = "🔺" 
                    elif change < 0: emoji = "💙"
                    else: emoji = "➖"

                    bot_message += f"{emoji} {ticker}: ${close_price:.2f} ({change:+.2f}%)\n"
                else:
                    bot_message += f"➖ {ticker}: ${close_price:.2f}\n"
            else:
                bot_message += f"⚠️ {ticker}: 데이터 없음\n"
                
        except:
            bot_message += f"⚠️ {ticker}: 확인 불가\n"
        
        time.sleep(0.5)

    # (4) 텔레그램
