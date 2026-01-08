import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. 감시할 종목 리스트 (미국주식 티커) - 여기를 바꾸면 원하는 종목을 볼 수 있어요
tickers = ["NVDA", "AVGO", "LABU", "MSFT", "AAPL"]

def get_stock_data(tickers):
    print("데이터 수집 중...")
    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        # 최신 데이터 가져오기 (오늘과 어제)
        hist = stock.history(period="5d") 
        
        if len(hist) < 2:
            continue
            
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change = ((current_price - prev_close) / prev_close) * 100
        
        # 색상 결정 (상승: 빨강, 하락: 파랑 - 한국식 표기)
        color = "red" if change > 0 else "blue"
        sign = "+" if change > 0 else ""
        
        data.append({
            "name": ticker,
            "price": f"${current_price:.2f}",
            "change": f"{sign}{change:.2f}%",
            "color": color
        })
    return data

def create_html(stock_data):
    # 한국 시간 설정
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    
    # HTML 템플릿 (CSS 포함)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>나만의 주식 대시보드</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f9; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #333; }}
            .update-time {{ text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px; }}
            .stock-item {{ display: flex; justify-content: space-between; padding: 15px; border-bottom: 1px solid #eee; font-size: 1.2em; }}
            .stock-name {{ font-weight: bold; }}
            .red {{ color: #e74c3c; }}
            .blue {{ color: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 Matt-Tuja Dashboard</h1>
            <p class="update-time">최근 업데이트: {now} (KST)</p>
            <div class="stock-list">
    """
    
    for item in stock_data:
        html += f"""
            <div class="stock-item">
                <span class="stock-name">{item['name']}</span>
                <span>{item['price']} <span class="{item['color']}">({item['change']})</span></span>
            </div>
        """
        
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    return html

# 실행 로직
if __name__ == "__main__":
    data = get_stock_data(tickers)
    html_content = create_html(data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("index.html 업데이트 완료!")

# ... (기존 코드들) ...
# print("index.html 업데이트 완료!")  <-- 아마 이 줄이 끝일 겁니다. 그 밑에 추가하세요.

# === [추가할 내용] 텔레그램 발송 실행 ===
# 1. 보낼 메시지 내용을 만듭니다 (간단하게 성공 알림)
bot_message = "🚀 주식 봇 업데이트가 완료되었습니다! (Github Actions)"

# 2. 아까 만든 전송 함수를 실제로 실행합니다
try:
    send_telegram_message(bot_message)
except NameError:
    # 혹시 함수 위치가 꼬였을 경우를 대비해 함수가 없으면 경고
    print("오류: send_telegram_message 함수가 정의되지 않았거나 이름이 다릅니다.")
