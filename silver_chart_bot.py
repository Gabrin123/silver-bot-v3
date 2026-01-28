import os
import time
import requests
import schedule
from datetime import datetime
from flask import Flask
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Birdeye Solana Scanner Running"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8457965430:AAHERt3c9hX118RcVGLoxu1OZFyePK1c7dI')
CHAT_ID = os.environ.get('CHAT_ID', '-5232036612')
BIRDEYE_API_KEY = os.environ.get('BIRDEYE_API_KEY', 'demo')

last_notification_time = None
notified_coins = []

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': False}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def scan_and_notify():
    global last_notification_time
    
    now = datetime.now()
    if last_notification_time and (now - last_notification_time).seconds < 180:
        logger.info("⏸ Waiting for next notification window")
        return
    
    logger.info("\n" + "="*70)
    logger.info("🔍 BIRDEYE SCAN")
    logger.info("="*70)
    
    try:
        # Get trending tokens from Birdeye
        url = "https://public-api.birdeye.so/defi/tokenlist"
        headers = {"X-API-KEY": BIRDEYE_API_KEY}
        params = {
            "sort_by": "v24hChangePercent",
            "sort_type": "desc",
            "offset": 0,
            "limit": 50
        }
        
        logger.info(f"📡 Calling Birdeye API...")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"❌ Birdeye error: {response.text}")
            return
        
        data = response.json()
        tokens = data.get('data', {}).get('tokens', [])
        
        logger.info(f"✅ Got {len(tokens)} tokens from Birdeye\n")
        
        candidates = []
        
        for i, token in enumerate(tokens[:30]):
            try:
                symbol = token.get('symbol', '')
                address = token.get('address', '')
                
                logger.info(f"{'='*60}")
                logger.info(f"#{i+1}: {symbol}")
                logger.info(f"{'='*60}")
                
                # Skip if already notified
                if address in notified_coins:
                    logger.info(f"⏭ Already notified\n")
                    continue
                
                # Get basic data from Birdeye list
                price = float(token.get('price', 0))
                volume_24h = float(token.get('v24hUSD', 0))
                liquidity = float(token.get('liquidity', 0))
                market_cap = float(token.get('mc', 0))
                price_change_24h = float(token.get('v24hChangePercent', 0))
                
                logger.info(f"BASIC METRICS:")
                logger.info(f"  Price: ${price:.8f}")
                logger.info(f"  Market Cap: ${market_cap:,.2f}")
                logger.info(f"  Liquidity: ${liquidity:,.2f}")
                logger.info(f"  Volume 24h: ${volume_24h:,.2f}")
                logger.info(f"  24h Change: {price_change_24h:.2f}%")
                
                # CHECK 1: Market Cap
                if market_cap < 100000:
                    logger.info(f"❌ REJECTED: Market cap ${market_cap:,.2f} < $100,000\n")
                    continue
                logger.info(f"✓ Market cap OK")
                
                # CHECK 2: Liquidity
                if liquidity < 50000:
                    logger.info(f"❌ REJECTED: Liquidity ${liquidity:,.2f} < $50,000\n")
                    continue
                logger.info(f"✓ Liquidity OK")
                
                # CHECK 3: Volume
                if volume_24h < 20000:
                    logger.info(f"❌ REJECTED: Volume ${volume_24h:,.2f} < $20,000\n")
                    continue
                logger.info(f"✓ Volume OK")
                
                # CHECK 4: Price movement
                if price_change_24h <= 0:
                    logger.info(f"❌ REJECTED: Negative 24h change {price_change_24h:.2f}%\n")
                    continue
                logger.info(f"✓ Positive price movement")
                
                # Get detailed data
                logger.info(f"\n📡 Fetching detailed Birdeye data...")
                detail_url = f"https://public-api.birdeye.so/defi/token_overview"
                detail_params = {"address": address}
                detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=10)
                
                if detail_response.status_code != 200:
                    logger.info(f"⚠ Could not fetch details (status: {detail_response.status_code})\n")
                    continue
                
                detail_data = detail_response.json().get('data', {})
                
                # Holder data
                holder_count = detail_data.get('holder', 0)
                holder_24h_ago = detail_data.get('holder24hAgo', holder_count)
                holder_growth = holder_count - holder_24h_ago
                
                # Buy/Sell data
                buy_24h = float(detail_data.get('buy24h', 0))
                sell_24h = float(detail_data.get('sell24h', 0))
                
                logger.info(f"\nHOLDER METRICS:")
                logger.info(f"  Current holders: {holder_count}")
                logger.info(f"  24h ago: {holder_24h_ago}")
                logger.info(f"  Growth: {holder_growth:+d}")
                
                logger.info(f"\nBUY/SELL PRESSURE:")
                logger.info(f"  Buy 24h: ${buy_24h:,.2f}")
                logger.info(f"  Sell 24h: ${sell_24h:,.2f}")
                
                # CHECK 5: Holder growth
                if holder_growth <= 0:
                    logger.info(f"❌ REJECTED: No holder growth ({holder_growth})\n")
                    continue
                logger.info(f"✓ Holder growth OK (+{holder_growth})")
                
                # CHECK 6: Buy/Sell ratio
                if sell_24h > 0:
                    buy_sell_ratio = buy_24h / sell_24h
                    logger.info(f"  Buy/Sell Ratio: {buy_sell_ratio:.2f}x")
                    
                    if buy_sell_ratio <= 1.0:
                        logger.info(f"❌ REJECTED: More sells than buys (ratio: {buy_sell_ratio:.2f})\n")
                        continue
                    logger.info(f"✓ Buy pressure OK")
                else:
                    buy_sell_ratio = 999
                    logger.info(f"✓ Only buys, no sells")
                
                # ALL CHECKS PASSED!
                logger.info(f"\n✅✅✅ PASSED ALL FILTERS! ✅✅✅\n")
                
                # Get Dexscreener URL
                dex_url = f"https://dexscreener.com/solana/{address}"
                
                candidates.append({
                    'symbol': symbol,
                    'address': address,
                    'price': price,
                    'market_cap': market_cap,
                    'liquidity': liquidity,
                    'volume_24h': volume_24h,
                    'price_change_24h': price_change_24h,
                    'holder_count': holder_count,
                    'holder_growth': holder_growth,
                    'buy_sell_ratio': buy_sell_ratio,
                    'dex_url': dex_url
                })
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}\n")
                continue
        
        # Send best candidate
        if not candidates:
            logger.info("\n" + "="*70)
            logger.info("❌ NO COINS PASSED ALL FILTERS")
            logger.info("="*70 + "\n")
            return
        
        # Sort by buy/sell ratio
        candidates.sort(key=lambda x: x['buy_sell_ratio'], reverse=True)
        best = candidates[0]
        
        logger.info(f"\n" + "="*70)
        logger.info(f"🎯 BEST SIGNAL: {best['symbol']}")
        logger.info(f"   Buy/Sell Ratio: {best['buy_sell_ratio']:.2f}x")
        logger.info(f"   Holder Growth: +{best['holder_growth']}")
        logger.info("="*70)
        
        message = f"""
🚀 <b>HIGH-QUALITY SIGNAL</b>

<b>Token:</b> {best['symbol']}
<b>Price:</b> ${best['price']:.8f}

<b>📊 Performance:</b>
• 24h: +{best['price_change_24h']:.1f}%

<b>💰 Fundamentals:</b>
• Market Cap: ${best['market_cap']:,.0f}
• Liquidity: ${best['liquidity']:,.0f}
• Volume 24h: ${best['volume_24h']:,.0f}

<b>👥 Holder Metrics:</b>
• Total Holders: {best['holder_count']}
• 24h Growth: +{best['holder_growth']} holders

<b>📈 Buy Pressure:</b>
• Buy/Sell Ratio: {best['buy_sell_ratio']:.2f}x
{'• 🔥 Strong buying pressure!' if best['buy_sell_ratio'] > 2 else '• ✅ More buyers than sellers'}

<b>🔗 Chart:</b> {best['dex_url']}

<b>Address:</b> <code>{best['address']}</code>

<i>Reply YES to buy or NO to skip</i>
"""
        
        if send_telegram(message.strip()):
            last_notification_time = now
            notified_coins.append(best['address'])
            
            if len(notified_coins) > 30:
                notified_coins.pop(0)
            
            logger.info("✅ Notification sent!\n")
        
    except Exception as e:
        logger.error(f"❌ Error in scan: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    logger.info("="*70)
    logger.info("BIRDEYE-ONLY SOLANA SCANNER")
    logger.info("Detailed logging enabled for debugging")
    logger.info("="*70 + "\n")
    
    # Start Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("✓ Flask running\n")
    
    time.sleep(2)
    
    send_telegram("🤖 Birdeye Scanner Active!\n\n✅ Filters:\n• MC > $100k\n• Liq > $50k\n• Vol > $20k\n• Holder growth\n• More buys than sells")
    
    # First scan
    scan_and_notify()
    
    # Schedule every 3 minutes
    schedule.every(3).minutes.do(scan_and_notify)
    
    logger.info("✓ Scanner running...\n")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
