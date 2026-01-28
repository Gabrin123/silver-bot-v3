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

def send_to_telegram(message=None):
    """Send message to Telegram chat"""
    if message:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            data = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("Message sent successfully!")
                return True
            else:
                print(f"Error sending to Telegram: {response.text}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    return False

def get_silver_price():
    """Get current silver price"""
    print("Fetching silver price...")
    
    # Try Yahoo Finance - most reliable
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"Yahoo Finance status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                meta = result[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                if price:
                    print(f"✓ Silver price fetched successfully: ${price:.2f}")
                    return round(price, 2)
                else:
                    print("Price field not found in response")
            else:
                print("No result in response")
    except Exception as e:
        print(f"Yahoo Finance error: {e}")
    
    # Try alternative source
    try:
        url = "https://api.metals.live/v1/spot/silver"
        response = requests.get(url, timeout=10)
        print(f"Metals.live status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = data[0].get('price')
            if price:
                print(f"✓ Silver price from metals.live: ${price:.2f}")
                return round(price, 2)
    except Exception as e:
        print(f"Metals.live error: {e}")
    
    print("❌ Could not fetch silver price from any source")
    return None

def job():
    """Main job to send chart update"""
    print(f"\n{'='*50}")
    print(f"Running job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # Get silver price
    price = get_silver_price()
    
    if price:
        message = f"The price of Silver is: ${price:.2f}\n\n🔗 <a href='https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=1'>View Live Chart</a>"
        print(f"Sending message with price: ${price:.2f}")
        send_to_telegram(message=message)
    else:
        # Fallback message if price fetch fails
        message = f"📊 Silver Chart Update\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n🔗 <a href='https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=1'>View Live Chart</a>"
        print("Sending fallback message (no price available)")
        send_to_telegram(message=message)
    
    print(f"{'='*50}\n")

def main():
    """Main function to run the bot"""
    print("="*50)
    print("Silver Chart Bot Started!")
    print(f"Chat ID: {CHAT_ID}")
    print(f"Update interval: Every 3 minutes")
    print("="*50)
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✓ Flask web server started")
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Send startup message
    send_to_telegram(message="🤖 Silver Bot is now active! Updates every 3 minutes.")
    
    # Run immediately on start
    job()
    
    # Schedule to run every 60 minutes
    schedule.every(60).minutes.do(job)
    
    print("\n✓ Bot is running. Waiting for scheduled updates...")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
