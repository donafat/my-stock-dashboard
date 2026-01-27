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
            requests.post(url, data={
                'chat_id': chat_id, 
                'text': msg, 
                'parse_mode': 'Markdown',
                'disable_web_page_preview': 'true'
            })
        except Exception as e:
            print(f"전송 실패: {e}")

# === 2. 날씨 정보 함수 ===
def get_weather_forecast(location_eng, location_kor):
    try:
        url = f"https://wttr.in/{location_eng}?format=j1&lang=ko"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather_today = data['weather'][0]['hourly']
            
            # 현재 시간대에 맞는 예보 가져오기 (오전/오후 단순화)
            am_data = weather_today[3] # 09:00
            pm_data = weather_today[6] # 18:00
            
            result = f"📍 *{location_eng}* ({location_kor})\n"
            result += f" - 오전/오후 기온: {am_data['tempC']}°C / {pm_data['tempC']}°C\n"
            result += f" - 상태: {pm_data['lang_ko'][0]['value']}\n"
            
            link = f"https://search.naver.com/search.naver?query={location_kor}+날씨"
            result += f" 👉 [🔎 상세 날씨 보기]({link})"
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
        "🇰🇷 코스피": "^KS11",
        "🇺🇸 S&P 500": "^GSPC",
        "💻 나스닥": "^IXIC",
        "😱 공포지수": "^VIX"
    }
    
    msg += "🌎 *글로벌 시장 지표*\n"
    for name, ticker in indices.items():
        try:
            # 시장 지표는 하루 단위 변화가 중요하므로 5일치 일별 데이터 사용
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

# === 4. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 5. 메인 실행 로직 ===
if __name__ == "__main__":
    # 한국 시간 가져오기
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    current_time_str = now.strftime("%Y-%m-%d %H:%M")
    
    # 오후 2시 이후면 '저녁 프리장 체크' 모드, 아니면 '아침 브리핑' 모드
    is_evening_mode = now.hour >= 14 
    
    if is_evening_mode:
        title = "🌙 *[미국주식 프리장 체크]*"
    else:
        title = "📈 *[맷투자 모닝 브리핑]*"

    bot_message = f"{title}\n📅 {current_time_str}\n------------------\n"
    
    # (1) 날씨 (아침에만 자세히, 저녁엔 생략하거나 간단히 - 여기선 아침에만 표시로 설정)
    if not is_evening_mode:
        print("날씨 정보 수집 중...")
        bot_message += "🌤 *오늘의 날씨*\n"
        bot_message += get_weather_forecast("Seongdong-gu", "성동구") + "\n"
        bot_message += get_weather_forecast("Gangnam-gu", "대치동") + "\n"
        bot_message += "------------------\n"

    # (2) 시장 지표 (지수는 아침/저녁 모두 확인)
    print("시장 지표 수집 중...")
    bot_message += get_market_indices()

    # (3) 개별 주식 정보 (핵심 수정 부분)
    print("주식 정보 수집 중...")
    if is_evening_mode:
        bot_message += "🔥 *프리장(Pre-market) 현황*\n"
    else:
        bot_message += "📊 *종가(Close) 현황*\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # [중요] 프리장 데이터를 위해 prepost=True, 최근 흐름을 위해 interval='1m' 사용
            # 저녁(프리장)엔 1분봉으로 최신가 조회, 아침엔 일봉으로 마감가 조회
            if is_evening_mode:
                # 최근 1일치 1분봉 (프리장 포함)
                hist = stock.history(period="1d", interval="1m", prepost=True)
            else:
                # 최근 2일치 일봉 (정규장 마감 기준)
                hist = stock.history(period="2d")
            
            if not hist.empty:
                # 가장 최근 가격 (프리장 현재가 or 어제 종가)
                current_price = hist['Close'].iloc[-1]
                
                # 변동률 계산을 위한 기준가 설정
                # 프리장 모드일 땐: '전일 정규장 종가' 기준 (yfinance info 활용)
                # 아침 모드일 땐: '그 전날 종가' 기준
                
                prev_close = 0
                if is_evening_mode:
                    # info에서 전일 종가 가져오기 (가끔 실패할 수 있어 예외처리)
                    try:
                        prev_close = stock.info.get('previousClose', hist['Close'].iloc[0])
                    except:
                        prev_close = hist['Close'].iloc[0] # 실패 시 시가로 대체
                else:
                    if len(hist) >= 2:
                        prev_close = hist['Close'].iloc[-2]
                    else:
                        prev_close = current_price # 비교 불가 시 0% 처리

                # 변동률 계산
                if prev_close > 0:
                    change = ((current_price - prev_close) / prev_close) * 100
                else:
                    change = 0.0

                # 이모지 처리
                if change > 0: emoji = "🔺" 
                elif change < 0: emoji = "💙"
                else: emoji = "➖"

                bot_message += f"{emoji} {ticker}: ${current_price:.2f} ({change:+.2f}%)\n"
            else:
                bot_message += f"⚠️ {ticker}: 데이터 없음\n"
                
        except Exception as e:
            # print(e) # 디버깅용
            bot_message += f"⚠️ {ticker}: 확인 불가\n"
        
        # API 호출 제한 방지 딜레이
        time.sleep(0.2)
######### CNN 공포탐욕지수 추가 ##############
    def get_fear_and_greed_index():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 데이터 구조에서 최신 값 추출
        fng_value = int(data['fear_and_greed']['score'])
        fng_rating = data['fear_and_greed']['rating']
        
        # 등급 한글 변환 (선택 사항)
        rating_kor = {
            "extreme fear": "극도의 공포 🥶",
            "fear": "공포 😨",
            "neutral": "중립 😐",
            "greed": "탐욕 🤑",
            "extreme greed": "극도의 탐욕 🔥"
        }
        
        rating_display = rating_kor.get(fng_rating, fng_rating)
        
        return fng_value, rating_display
        
    except Exception as e:
        print(f"Error fetching F&G Index: {e}")
        return None, None
################ CNN공포탐욕지수 추가 끝#####################
    # (4) 텔레그램 전송
    send_telegram_message(bot_message)
    print("전송 완료")
