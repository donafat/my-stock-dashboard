import os
import time
import requests
import pytz
import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta  # <--- 여기에 timedelta를 추가했습니다!

# =========================================================
# 1. 텔레그램 전송 함수
# =========================================================
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ [오류] 텔레그램 설정(TOKEN/CHAT_ID)을 찾을 수 없습니다.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공!")
        else:
            print(f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 전송 중 에러: {e}")

# =========================================================
# 2. 날씨 정보 함수
# =========================================================
def get_weather_forecast(location_eng, location_kor):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://wttr.in/{location_eng}?format=j1&lang=ko"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                weather_today = data['weather'][0]['hourly']
                
                # 시간대별 예보 (오전 9시, 오후 6시)
                am_data = weather_today[3] 
                pm_data = weather_today[6] 
                
                result = f"📍 *{location_eng}* ({location_kor})\n"
                result += f" - 기온: {am_data['tempC']}°C / {pm_data['tempC']}°C\n"
                result += f" - 상태: {pm_data['lang_ko'][0]['value']}\n"
                return result
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
            
    return f"📍 {location_eng}: 정보 없음"

# =========================================================
# 3. 시장 주요 지표
# =========================================================
def get_market_indices():
    msg = ""
    indices = {
        "💵 환율": "KRW=X",
        "🇰🇷 코스피": "^KS11",
        "🇺🇸 S&P500": "^GSPC",
        "💻 나스닥": "^IXIC",
        "😱 공포지수": "^VIX"
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
            
    return msg + "------------------\n"

# =========================================================
# 4. CNN 공포/탐욕 지수
# =========================================================
def get_fear_and_greed_index():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        fng_value = int(data['fear_and_greed']['score'])
        fng_rating = data['fear_and_greed']['rating']
        
        rating_kor = {
            "extreme fear": "극도의 공포 🥶", "fear": "공포 😨",
            "neutral": "중립 😐", "greed": "탐욕 🤑", "extreme greed": "극도의 탐욕 🔥"
        }
        return fng_value, rating_kor.get(fng_rating, fng_rating)
    except:
        return None, None

# =========================================================
# 5. 주식 뉴스 및 일정
# =========================================================
def get_stock_news_and_events(ticker):
    try:
        stock = yf.Ticker(ticker)
        info_msg = ""
        
        # 뉴스
        news_list = stock.news
        if news_list:
            title = news_list[0].get('title', '제목 없음')
            info_msg += f"  📰 {title}\n"

        # 실적발표
        cal = stock.calendar
        if cal and 'Earnings Date' in cal:
            earnings_dates = cal['Earnings Date']
            if earnings_dates:
                next_earnings = earnings_dates[0].strftime("%Y-%m-%d")
                info_msg += f"  📢 실적발표: {next_earnings}\n"
        
        return info_msg
    except:
        return ""

# =========================================================
# 6. 원자재 시세 (금, 은, 구리)
# =========================================================
def get_commodity_price():
    commodities = {
        '금 (Gold)': 'GC=F',
        '은 (Silver)': 'SI=F',
        '구리 (Copper)': 'HG=F'
    }
    
    report = "⛏️ *[원자재 주요 시세]*\n"
    
    # [수정됨] pytz.timedelta -> timedelta 로 변경
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7) 
    
    for name, ticker in commodities.items():
        try:
            df = fdr.DataReader(ticker, start_date, end_date)
            
            if not df.empty:
                last_close = df['Close'].iloc[-1]
                
                if len(df) >= 2:
                    prev_close = df['Close'].iloc[-2]
                    change = last_close - prev_close
                    pct_change = (change / prev_close) * 100
                    
                    emoji = "🔺" if change > 0 else "💙" if change < 0 else "➖"
                    report += f"- {name}: ${last_close:,.2f} ({emoji} {pct_change:.2f}%)\n"
                else:
                    report += f"- {name}: ${last_close:,.2f}\n"
            else:
                report += f"- {name}: 데이터 없음\n"
                
        except Exception:
            report += f"- {name}: 정보 없음\n"
            
    return report + "------------------\n"

# =========================================================
# [최종] 메인 실행 로직
# =========================================================
if __name__ == "__main__":
    print("🚀 봇 실행 시작 (데이터 수집 중...)")
    
    # 1. 시간 설정
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    current_time_str = now.strftime("%Y-%m-%d %H:%M")
    is_evening_mode = now.hour >= 14
    
    title = "🌙 *[미국주식 프리장 체크]*" if is_evening_mode else "📈 *[맷투자 모닝 브리핑]*"
    bot_message = f"{title}\n📅 {current_time_str}\n------------------\n"
    
    # 2. 날씨
    try:
        print("1. 날씨 수집 중...")
        bot_message += "🌤 *오늘의 날씨*\n"
        bot_message += get_weather_forecast("Seongdong-gu", "성동구") + "\n"
        bot_message += get_weather_forecast("Gangnam-gu", "대치동") + "\n"
        bot_message += "------------------\n"
    except Exception as e:
        print(f"날씨 에러: {e}")

    # 3. 시장 지표
    print("2. 시장 지표 수집 중...")
    bot_message += get_market_indices()
    
    # 4. 공포탐욕지수
    print("3. 공포지수 수집 중...")
    fng_score, fng_rating = get_fear_and_greed_index()
    if fng_score:
        bot_message += f"😨 *CNN 공포/탐욕 지수*\n점수: *{fng_score}* / 상태: *{fng_rating}*\n------------------\n"
    
    # 5. 원자재
    print("4. 원자재 시세 수집 중...")
    bot_message += get_commodity_price()

    # 6. 개별 주식
    print("5. 주식 정보 수집 중...")
    tickers = ["SWKS","NVDA","GOOGL","AMZN","TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO","NFLX","IONQ","PLTR","ETN", "TSM", "MU", "AXON","META","BTC-USD", "ETH-USD"]
    news_watch_list = ["SWKS","NVDA","GOOGL","AMZN","TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO","NFLX","IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]
    
    bot_message += "🔥 *프리장 현황*\n" if is_evening_mode else "📊 *종가 현황*\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            if is_evening_mode:
                hist = stock.history(period="1d", interval="1m", prepost=True)
            else:
                hist = stock.history(period="2d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[0] if is_evening_mode else (hist['Close'].iloc[-2] if len(hist) >= 2 else current_price)
                
                change = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                emoji = "🔺" if change > 0 else "💙" if change < 0 else "➖"
                
                bot_message += f"{emoji} *{ticker}*: ${current_price:.2f} ({change:+.2f}%)\n"
                
                if ticker in news_watch_list:
                    bot_message += get_stock_news_and_events(ticker)
            else:
                bot_message += f"⚠️ {ticker}: 데이터 없음\n"
            time.sleep(0.2)
        except:
            bot_message += f"⚠️ {ticker}: 조회 실패\n"

    # 7. 최종 전송
    print("\n--- 전송될 메시지 ---")
    print(bot_message)
    print("--------------------")
    send_telegram(bot_message)
