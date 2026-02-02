import os
import time
import requests
import pytz
import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta

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
    # [수정] 링크 미리보기 끄기 (disable_web_page_preview=True) -> 메시지 깔끔하게
    data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': 'true'}
    
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
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://wttr.in/{location_eng}?format=j1&lang=ko"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                weather_today = data['weather'][0]['hourly']
                
                am_data = weather_today[3] # 09:00
                pm_data = weather_today[6] # 18:00
                
                result = f"📍 *{location_eng}* ({location_kor})\n"
                result += f" - 기온: {am_data['tempC']}°C / {pm_data['tempC']}°C\n"
                result += f" - 상태: {pm_data['lang_ko'][0]['value']}\n"
                
                link = f"https://search.naver.com/search.naver?query={location_kor}+날씨"
                result += f" 👉 [🔎 상세 날씨 보기]({link})"
                return result
            else:
                time.sleep(1)
        except:
            time.sleep(1)
    return f"📍 {location_eng}: 정보 없음"

# =========================================================
# 3. 시장 주요 지표 (안전장치 포함)
# =========================================================
def get_market_indices():
    msg = "🌎 *글로벌 시장 지표*\n"
    
    # 한국/환율 (네이버 우선 -> 야후 백업)
    items = [["💵 환율", "USD/KRW", "KRW=X"], ["🇰🇷 코스피", "KS11", "^KS11"]]
    
    end_date = datetime.now(pytz.timezone('Asia/Seoul'))
    start_date = end_date - timedelta(days=7)
    
    for name, naver_code, yahoo_code in items:
        price = 0
        change_str = ""
        success = False
        
        # 1. 네이버 시도
        try:
            df = fdr.DataReader(naver_code, start_date, end_date)
            if not df.empty:
                price = df['Close'].iloc[-1]
                if len(df) >= 2:
                    prev = df['Close'].iloc[-2]
                    pct = ((price - prev) / prev) * 100
                    icon = "🔺" if pct > 0 else "💙" if pct < 0 else "➖"
                    change_str = f"({pct:+.2f}%) {icon}"
                success = True
        except: pass
            
        # 2. 야후 시도
        if not success:
            try:
                stock = yf.Ticker(yahoo_code)
                hist = stock.history(period="5d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if len(hist) >= 2:
                        prev = hist['Close'].iloc[-2]
                        pct = ((price - prev) / prev) * 100
                        icon = "🔺" if pct > 0 else "💙" if pct < 0 else "➖"
                        change_str = f"({pct:+.2f}%) {icon}"
                    success = True
            except: pass

        if success:
            fmt = "{:,.2f}원" if "환율" in name else "{:,.0f}"
            msg += f"- {name}: {fmt.format(price)} {change_str}\n"
        else:
            msg += f"- {name}: 확인 불가\n"

    # 미국 지표 (야후)
    us_indices = {"🇺🇸 S&P500": "^GSPC", "💻 나스닥": "^IXIC", "😱 공포지수(VIX)": "^VIX"}
    for name, ticker in us_indices.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                change_str = ""
                if len(hist) >= 2:
                    prev = hist['Close'].iloc[-2]
                    change = ((price - prev) / prev) * 100
                    
                    # VIX는 반대로 해석 (오르면 공포)
                    if "VIX" in name:
                        icon = "🔥" if change > 5 else "😌" if change < -5 else " "
                    else:
                        icon = "🔺" if change > 0 else "💙" if change < 0 else "➖"
                    change_str = f"({change:+.2f}%) {icon}"
                msg += f"- {name}: {price:,.2f} {change_str}\n"
        except:
            msg += f"- {name}: 확인 불가\n"
            
    return msg + "------------------\n"

# =========================================================
# 4. CNN 공포/탐욕 지수 (수정됨: 실패 시 메시지 표시)
# =========================================================
def get_fear_and_greed_index():
    # 헤더를 좀 더 진짜 브라우저처럼 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            score = int(data['fear_and_greed']['score'])
            rating = data['fear_and_greed']['rating']
            
            rating_kor = {
                "extreme fear": "극도의 공포 🥶", "fear": "공포 😨",
                "neutral": "중립 😐", "greed": "탐욕 🤑", "extreme greed": "극도의 탐욕 🔥"
            }
            return score, rating_kor.get(rating, rating)
    except Exception as e:
        print(f"CNN 접속 에러: {e}")
        
    return None, None

# =========================================================
# 5. 주식 뉴스 및 일정
# =========================================================
def get_stock_news_and_events(ticker):
    try:
        stock = yf.Ticker(ticker)
        info_msg = ""
        news_list = stock.news
        if news_list:
            title = news_list[0].get('title', '제목 없음')
            title = title.replace('[', '(').replace(']', ')')
            info_msg += f"  📰 {title}\n"

        cal = stock.calendar
        if cal and 'Earnings Date' in cal:
            earnings_dates = cal['Earnings Date']
            if earnings_dates:
                next_earnings = earnings_dates[0].strftime("%Y-%m-%d")
                info_msg += f"  📢 실적발표: {next_earnings}\n"
        return info_msg
    except: return ""

# =========================================================
# 6. 원자재 시세
# =========================================================
def get_commodity_price():
    commodities = {'금(Gold)': 'GC=F', '은(Silver)': 'SI=F', '구리(Copper)': 'HG=F'}
    report = "⛏️ *[원자재 주요 시세]*\n"
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7) 
    
    for name, ticker in commodities.items():
        try:
            df = fdr.DataReader(ticker, start_date, end_date)
            if not df.empty:
                curr = df['Close'].iloc[-1]
                if len(df) >= 2:
                    prev = df['Close'].iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    emoji = "🔺" if pct > 0 else "💙" if pct < 0 else "➖"
                    report += f"- {name}: ${curr:,.2f} ({emoji} {pct:.2f}%)\n"
                else:
                    report += f"- {name}: ${curr:,.2f}\n"
            else:
                report += f"- {name}: 데이터 없음\n"
        except:
            report += f"- {name}: 정보 없음\n"
    return report + "------------------\n"

# =========================================================
# [최종] 메인 실행 로직
# =========================================================
if __name__ == "__main__":
    print("🚀 봇 실행 시작...")
    
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    current_time_str = now.strftime("%Y-%m-%d %H:%M")
    is_evening_mode = now.hour >= 14
    
    title = "🌙 *[미국주식 프리장 체크]*" if is_evening_mode else "📈 *[맷투자 모닝 브리핑]*"
    bot_message = f"{title}\n📅 {current_time_str}\n------------------\n"
    
    # 1. 날씨
    try:
        print("1. 날씨 수집 중...")
        bot_message += "🌤 *오늘의 날씨*\n"
        bot_message += get_weather_forecast("Seongdong-gu", "성동구") + "\n"
        bot_message += get_weather_forecast("Gangnam-gu", "대치동") + "\n"
        bot_message += "------------------\n"
    except: pass

    # 2. 시장 지표
    print("2. 시장 지표 수집 중...")
    bot_message += get_market_indices()
    
    # 3. 공포지수 (수정됨: 실패해도 메시지 표시)
    print("3. 공포지수 수집 중...")
    score, rating = get_fear_and_greed_index()
    if score:
        bot_message += f"😨 *CNN 공포/탐욕 지수*\n점수: *{score}* / 상태: *{rating}*\n"
    else:
        # 실패 시 메시지 출력
        bot_message += f"😨 *CNN 공포/탐욕 지수*: ⚠️ 수집 실패\n"
    
    # 링크는 성공/실패 상관없이 항상 표시
    bot_message += "[👉 CNN 웹사이트 바로가기](https://edition.cnn.com/markets/fear-and-greed)\n------------------\n"
    
    # 4. 원자재
    print("4. 원자재 수집 중...")
    bot_message += get_commodity_price()

    # 5. 개별 주식
    print("5. 주식 수집 중...")
    tickers = ["SWKS","NVDA","GOOGL","AMZN","TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO","NFLX","IONQ","PLTR","ETN", "TSM", "MU", "AXON","META","BTC-USD", "ETH-USD"]
    news_watch_list = ["SWKS","NVDA","GOOGL","AMZN","TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO","NFLX","IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]
    
    bot_message += "🔥 *프리장 현황*\n" if is_evening_mode else "📊 *종가 현황*\n"
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            curr = None
            prev = None
            
            # [저녁 모드: 프리장] fast_info를 사용하여 실시간 가격 확보
            if is_evening_mode:
                try:
                    # fast_info는 지연 없이 최신가(프리마켓 포함)를 가져옴
                    curr = stock.fast_info['last_price']
                    prev = stock.fast_info['previous_close']
                except:
                    # 실패 시 기존 방식(history)으로 백업
                    pass

            # [데이터가 없거나 아침 모드] 기존 history 방식 사용
            if curr is None:
                # 프리장일 때는 prepost=True, 아닐 때는 일반 데이터
                hist = stock.history(period="1d" if is_evening_mode else "2d", 
                                   interval="1m" if is_evening_mode else "1d",
                                   prepost=True)
                
                if not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    if is_evening_mode:
                        # 프리장일 때 전일 종가는 info에서 가져오거나 history 첫 값
                        prev = stock.info.get('previousClose', hist['Close'].iloc[0])
                    else:
                        # 아침(종가)일 때 전일 종가는 2일치 중 앞의 것
                        prev = hist['Close'].iloc[-2] if len(hist) >= 2 else curr

            # [결과 메시지 생성]
            if curr is not None and prev is not None:
                # 0으로 나누기 방지
                if prev > 0:
                    pct = ((curr - prev) / prev) * 100
                else:
                    pct = 0.0
                
                emoji = "🔺" if pct > 0 else "💙" if pct < 0 else "➖"
                
                bot_message += f"{emoji} *{ticker}*: ${curr:.2f} ({pct:+.2f}%)\n"
                
                if ticker in news_watch_list:
                    bot_message += get_stock_news_and_events(ticker)
            else:
                bot_message += f"⚠️ {ticker}: 데이터 없음\n"
            
            time.sleep(0.2)
            
        except Exception as e:
            print(f"[{ticker}] 에러: {e}")
            bot_message += f"⚠️ {ticker}: 조회 실패\n"

    print("\n--- 전송될 메시지 ---")
    print(bot_message)
    send_telegram(bot_message)
