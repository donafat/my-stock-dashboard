import os
import requests
import yfinance as yf
from datetime import datetime
import pytz

# === 1. 텔레그램 전송 함수 정의 ===
def send_telegram_message(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ 텔레그램 설정이 없습니다.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': msg}
    
    try:
        requests.post(url, data=data)
        print("✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

# === 2. 설정 및 데이터 준비 ===
tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "SOXL"] # 원하는 종목
stock_data = {} # HTML을 만들기 위한 데이터 바구니
bot_message = "📈 [맷투자 모닝 브리핑]\n------------------\n"

print("데이터 수집 시작...")

# === 3. 데이터 수집 및 메시지 작성 ===
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # 데이터 가져오기
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        
        # 계산
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        
        # 이모지 설정
        emoji = "🔺" if change >= 0 else "Vk"
        sign = "+" if change >= 0 else ""
        color = "red" if change >= 0 else "blue" # HTML용 색상
        
        # A. 텔레그램용 메시지 줄 추가
        bot_message += f"{emoji} {ticker}: ${price:.2f} ({sign}{change_pct:.2f}%)\n"
        
        # B. HTML용 데이터 저장 (이게 빠져서 업데이트가 안 된 겁니다!)
        stock_data[ticker] = {
            "price": f"${price:.2f}",
            "change": f"{sign}{change_pct:.2f}%",
            "color": color
        }
        print(f"수집 완료: {ticker}")

    except Exception as e:
        print(f"에러 ({ticker}): {e}")
        bot_message += f"⚠️ {ticker}: 수집 실패\n"
        stock_data[ticker] = {"price": "Error", "change": "0%", "color": "black"}

bot_message += "------------------\n👉 대시보드: https://donaq.github.io/my-stock-dashboard/"

# === 4. 텔레그램 발송 ===
send_telegram_message(bot_message)

# === 5. HTML 파일 생성 (가장 중요한 부분!) ===
# 한국 시간 구하기
KST = pytz.timezone('Asia/Seoul')
update_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>맷투자의 주식 대시보드</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background-color: #f4f4f9; }}
        h1 {{ color: #333; }}
        .card {{ background: white; border-radius: 10px; padding: 15px; margin: 10px auto; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .ticker {{ font-size: 1.2em; font-weight: bold; color: #555; }}
        .price {{ font-size: 1.5em; font-weight: bold; margin: 10px 0; }}
        .time {{ color: #888; font-size: 0.8em; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>🚀 맷투자의 주식 현황</h1>
"""

for ticker, data in stock_data.items():
    html_content += f"""
    <div class="card">
        <div class="ticker">{ticker}</div>
        <div class="price" style="color: {data['color']}">{data['price']}</div>
        <div>변동률: {data['change']}</div>
    </div>
    """

html_content += f"""
    <div class="time">마지막 업데이트 (한국시간): {update_time}</div>
</body>
</html>
"""

# 파일로 저장 (이 코드가 있어야 웹사이트가 바뀝니다)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("index.html 파일 업데이트 완료!")
