import os
import time
import requests
import schedule
from datetime import datetime
from flask import Flask
import threading

# Create a dummy web server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Silver Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Telegram configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8355694996:AAE5aAFeeA1kFYiQIIe0coD_JdQQ3d6jROA')
CHAT_ID = os.environ.get('CHAT_ID', '375372594')

def get_chart_image():
    """Get TradingView chart image using their snapshot API"""
    # TradingView chart snapshot URL
    # This uses TradingView's chart image service
    chart_url = "https://s3.tradingview.com/snapshots/u/UcE8xWpZ.png"
    
    # Alternative: Use a chart generation service or API
    # For now, we'll use a placeholder approach with TradingView widget
    
    # Generate chart URL with parameters
    symbol = "TVC:SILVER"
    interval = "1"
    
    # Using TradingView's advanced chart widget image
    widget_url = f"https://www.tradingview.com/x/{symbol}/"
    
    try:
        # Fetch the chart image
        response = requests.get(widget_url, timeout=10)
        
        if response.status_code == 200:
            image_path = '/tmp/silver_chart.png'
            with open(image_path, 'wb') as f:
                f.write(response.content)
            return image_path
        else:
            print(f"Failed to fetch chart: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error fetching chart: {e}")
        return None

def send_to_telegram(image_path=None, message=None):
    """Send image or message to Telegram chat"""
    
    if image_path and os.path.exists(image_path):
        # Send photo
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        try:
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': CHAT_ID,
                    'caption': f'📊 Silver (XAG/USD) - 1 Min Chart\n🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    print("Chart sent successfully!")
                    return True
                else:
                    print(f"Error sending to Telegram: {response.text}")
                    return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    elif message:
        # Send text message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            data = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

def get_silver_price():
    """Get current silver price from an API"""
    try:
        # Using Yahoo Finance API
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return price
        return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def job():
    """Main job to send chart update"""
    print(f"Running job at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get silver price
    price = get_silver_price()
    
    if price:
        message = f"""The silver price right now is: ${price:.2f}

🔗 <a href="https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=1">View Live Chart</a>
"""
        send_to_telegram(message=message)
    else:
        # Fallback message
        message = f"""📊 Silver Chart Update
🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🔗 View chart: https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=1
"""
        send_to_telegram(message=message)

def main():
    """Main function to run the bot"""
    print("Silver Chart Bot Started!")
    print(f"Will post updates every 3 minutes to chat ID: {CHAT_ID}")
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("Flask web server started for Render")
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Send startup message
    send_to_telegram(message="🤖 Silver Bot is now active! Updates every 3 minutes.")
    
    # Run immediately on start
    job()
    
    # Schedule to run every 3 minutes
    schedule.every(3).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
