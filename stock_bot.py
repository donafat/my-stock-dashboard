import os
import requests
from bs4 import BeautifulSoup  # <--- 이 줄이 꼭 있어야 합니다!
import yfinance as yf
from datetime import datetime
import pytz

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

# === [새로 추가된 코드] 날씨 가져오는 함수 ===
def get_weather(location):
    url = f"https://search.naver.com/search.naver?query={location} 날씨"
    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        temp = soup.find('div', {'class': 'temperature_text'}).text.strip().replace('현재 온도', '')
        status = soup.find('span', {'class': 'weather_before_text'}).text.strip()
        return f"{location}: {temp} ({status})"
    except:
        return f"{location}: 날씨 정보 오류"

# === 2. 주식 종목 설정 ===
tickers = ["SWKS","NVDA", "TSLA", "AAPL", "MSFT", "SOXL", "LABU", "TQQQ", "RETL","FNGU", "ETHT", "AVGO", "AMZN", "NFLX", "GOOGL", "IONQ","PLTR","ETN", "TSM", "MU", "AXON","META"]

# === 3. 데이터 수집 시작 ===
bot_message = "📈 [맷투자 모닝 브리핑]\n------------------\n"

# === [새로 추가된 코드] 날씨 정보 먼저 넣기 ===
bot_message += "🌤 **오늘의 날씨**\n"
bot_message += get_weather("성동구") + "\n"
bot_message += get_weather("대치동") + "\n"
bot_message += "------------------\n"

print("데이터 수집 중...")

for ticker in tickers:
    try:
        # 데이터 가져오기
        stock = yf.Ticker(ticker)
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        
        # 변동률 계산
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        
        # 이모지와 색상 결정
        emoji = "🔺" if change >= 0 else "Vk"
        sign = "+" if change >= 0 else ""
        color = "red" if change >= 0 else "blue"
        
        # 1) 텔레그램 메시지에 추가
        bot_message += f"{emoji} {ticker}: ${price:.2f} ({sign}{change_pct:.2f}%)\n"
        
        # 2) HTML 데이터에 저장 (이게 되어야 웹사이트가 바뀝니다!)
        stock_data[ticker] = {
            "price": f"${price:.2f}",
            "change": f"{sign}{change_pct:.2f}%",
            "color": color
        }
        
    except Exception as e:
        print(f"Error {ticker}: {e}")
        bot_message += f"⚠️ {ticker}: 확인 불가\n"

bot_message += "------------------\n👉 대시보드: https://donaq.github.io/my-stock-dashboard/"

# === 4. 텔레그램 전송 ===
send_telegram_message(bot_message)
print("텔레그램 전송 완료")

# === 5. HTML 파일 생성 (여기가 웹사이트 만드는 부분입니다!) ===
kst = pytz.timezone('Asia/Seoul')
now_str = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S (KST)")

html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식 대시보드</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 20px; background: #f0f2f5; }}
        .card {{ background: white; padding: 20px; margin: 10px auto; max-width: 400px; border-radius: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .name {{ font-size: 1.2em; font-weight: bold; color: #333; }}
        .price {{ font-size: 2em; margin: 10px 0; font-weight: bold; }}
        .update {{ margin-top: 30px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>🚀 오늘의 주식 현황</h1>
"""

for ticker, data in stock_data.items():
    html += f"""
    <div class="card">
        <div class="name">{ticker}</div>
        <div class="price" style="color: {data['color']}">{data['price']}</div>
        <div>{data['change']}</div>
    </div>
    """

html += f"""
    <div class="update">최근 업데이트: {now_str}</div>
</body>
</html>
"""

# 파일을 덮어씁니다
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html 업데이트 완료: {now_str}")
